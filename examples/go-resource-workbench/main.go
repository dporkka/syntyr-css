package main

import (
	"embed"
	"flag"
	"html/template"
	"log"
	"net"
	"net/http"
	"net/url"
	"sort"
	"strconv"
	"strings"
)

//go:embed templates/*.html
var templateFiles embed.FS
var pageTemplate = template.Must(template.ParseFS(templateFiles, "templates/*.html"))

type resource struct {
	ID, Name, Status, Region, Owner, Updated string
}
type resourceRow struct {
	resource
	DetailURL string
}

// A page may contain a slice of a larger matching group. Keep both scopes.
type resourceGroup struct {
	Label string
	Total int
	Rows  []resourceRow
}

const rowsPerPage = 3

type pageData struct {
	Query, Status, Sort, Theme, Group         string
	ThemeStudio, ThemeGrid, ThemeNoir         bool
	StatusActive, StatusReview, StatusDone    bool
	SortName, SortUpdated                     bool
	ShowOwner, ShowRegion                     bool
	Groups                                    []resourceGroup
	ColumnCount                               int
	Count                                     int
	Page, TotalPages, FirstResult, LastResult int
	HasPrevious, HasNext                      bool
	PreviousURL, NextURL                      string
	Selected                                  *resource
	EditToken                                 string
	AllPreviewURL, ReturnURL                  string
	IsPreview                                 bool
	Chosen                                    []resource
	SelectionScope                            string
	SelectionCount                            int
}

var resources = []resource{
	{"RS-204", "Harbor East", "review", "North", "Operations", "2026-11-17"},
	{"RS-088", "Civic Center", "active", "South", "Finance", "2026-11-10"},
	{"RS-301", "Airport Loop", "active", "North", "Sales", "2026-11-15"},
	{"RS-144", "Riverside Digital", "review", "West", "Operations", "2026-11-13"},
	{"RS-442", "Transit Hub", "done", "West", "Field", "2026-11-03"},
	{"RS-005", "Summit Plaza", "done", "East", "Sales", "2026-11-08"},
}

func limitedQuery(q string) string {
	q = strings.TrimSpace(q)
	chars := []rune(q)
	if len(chars) > 100 {
		return string(chars[:100])
	}
	return q
}
func filterResources(rows []resource, q, status, ordering string) []resource {
	result := make([]resource, 0, len(rows))
	for _, item := range rows {
		searchable := strings.ToLower(item.ID + " " + item.Name + " " + item.Owner + " " + item.Region)
		if status != "" && item.Status != status {
			continue
		}
		if q != "" && !strings.Contains(searchable, strings.ToLower(q)) {
			continue
		}
		result = append(result, item)
	}
	sort.Slice(result, func(i, j int) bool {
		if ordering == "name" {
			return strings.ToLower(result[i].Name) < strings.ToLower(result[j].Name)
		}
		if result[i].Updated == result[j].Updated {
			return result[i].ID < result[j].ID
		}
		return result[i].Updated > result[j].Updated
	})
	return result
}
func validGroup(group string) bool {
	return group == "" || group == "status" || group == "region"
}

func groupLabel(item resource, group string) string {
	switch group {
	case "status":
		return item.Status
	case "region":
		return item.Region
	default:
		return ""
	}
}

// Group before pagination, retaining the original sort order inside each group.
func groupResources(rows []resource, group string) {
	if group != "" {
		sort.SliceStable(rows, func(i, j int) bool {
			return groupLabel(rows[i], group) < groupLabel(rows[j], group)
		})
	}
}

func baseValues(q, status, ordering, group string, showOwner, showRegion bool) url.Values {
	v := url.Values{"columns_present": {"1"}}
	if q != "" {
		v.Set("q", q)
	}
	if status != "" {
		v.Set("status", status)
	}
	if ordering != "" {
		v.Set("sort", ordering)
	}
	if group != "" {
		v.Set("group", group)
	}
	if showOwner {
		v.Add("columns", "owner")
	}
	if showRegion {
		v.Add("columns", "region")
	}
	return v
}
func link(path string, q url.Values) string {
	return path + "?" + q.Encode()
}

func newHandler(distDir string) http.Handler {
	state := newResourceState()
	secret := newCSRFSecret()
	mux := http.NewServeMux()
	mux.Handle("/assets/", http.StripPrefix("/assets/", http.FileServer(http.Dir(distDir))))
	mux.Handle("/resource/edit", editHandler(state, secret))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" && r.URL.Path != "/resources" && r.URL.Path != "/preview" {
			http.NotFound(w, r)
			return
		}
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", "GET, HEAD")
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		v := r.URL.Query()
		q := limitedQuery(v.Get("q"))
		status := v.Get("status")
		ordering := v.Get("sort")
		group := v.Get("group")
		theme := v.Get("theme")
		if theme == "" {
			theme = "studio"
		}
		if !validGroup(group) || len(v["group"]) > 1 || (status != "" && status != "active" && status != "review" && status != "done") ||
			(ordering != "" && ordering != "updated" && ordering != "name") ||
			(theme != "studio" && theme != "grid" && theme != "noir") {
			http.Error(w, "Invalid filter, sort or grouping value", http.StatusBadRequest)
			return
		}
		showOwner, showRegion := true, true
		if v.Has("columns_present") {
			showOwner, showRegion = false, false
			for _, c := range v["columns"] {
				switch c {
				case "owner":
					showOwner = true
				case "region":
					showRegion = true
				default:
					http.Error(w, "Invalid column", http.StatusBadRequest)
					return
				}
			}
		}
		rows := state.snapshot()
		filtered := filterResources(rows, q, status, ordering)
		groupResources(filtered, group)
		groupTotals := make(map[string]int)
		for _, item := range filtered {
			groupTotals[groupLabel(item, group)]++
		}
		page := 1
		if v.Has("page") {
			var err error
			page, err = strconv.Atoi(v.Get("page"))
			if err != nil || page < 1 {
				http.Error(w, "Invalid page", http.StatusBadRequest)
				return
			}
		}
		totalPages := max(1, (len(filtered)+rowsPerPage-1)/rowsPerPage)
		if page > totalPages {
			http.Error(w, "Page out of range", http.StatusBadRequest)
			return
		}
		first := (page - 1) * rowsPerPage
		last := min(first+rowsPerPage, len(filtered))
		visible := filtered[first:last]
		params := baseValues(q, status, ordering, group, showOwner, showRegion)
		params.Set("theme", theme)
		params.Set("page", strconv.Itoa(page))
		data := pageData{
			Query: q, Status: status, Sort: ordering, Theme: theme, Group: group,
			ThemeStudio: theme == "studio", ThemeGrid: theme == "grid", ThemeNoir: theme == "noir",
			StatusActive: status == "active", StatusReview: status == "review", StatusDone: status == "done",
			SortName: ordering == "name", SortUpdated: ordering != "name",
			ShowOwner: showOwner, ShowRegion: showRegion,
			Count: len(filtered), ColumnCount: 4,
			Page: page, TotalPages: totalPages, FirstResult: first + 1, LastResult: last,
			HasPrevious: page > 1, HasNext: page < totalPages,
			AllPreviewURL: "", ReturnURL: link("/resources", params),
			IsPreview: r.URL.Path == "/preview",
		}
		if showOwner {
			data.ColumnCount++
		}
		if showRegion {
			data.ColumnCount++
		}
		if data.HasPrevious {
			previous := baseValues(q, status, ordering, group, showOwner, showRegion)
			previous.Set("theme", theme)
			previous.Set("page", strconv.Itoa(page-1))
			data.PreviousURL = link("/resources", previous)
		}
		if data.HasNext {
			next := baseValues(q, status, ordering, group, showOwner, showRegion)
			next.Set("theme", theme)
			next.Set("page", strconv.Itoa(page+1))
			data.NextURL = link("/resources", next)
		}
		for _, item := range visible {
			detail := baseValues(q, status, ordering, group, showOwner, showRegion)
			detail.Set("id", item.ID)
			detail.Set("theme", theme)
			detail.Set("page", strconv.Itoa(page))
			label := groupLabel(item, group)
			if len(data.Groups) == 0 || data.Groups[len(data.Groups)-1].Label != label {
				data.Groups = append(data.Groups, resourceGroup{Label: label, Total: groupTotals[label]})
			}
			current := &data.Groups[len(data.Groups)-1]
			current.Rows = append(current.Rows, resourceRow{item, link("/resources", detail)})
			if item.ID == v.Get("id") && r.URL.Path != "/preview" {
				selected := item
				data.Selected = &selected
				if r.Method == http.MethodGet {
					token, err := issueFormToken(w, r, secret)
					if err != nil {
						http.Error(w, "Cannot prepare edit form", http.StatusServiceUnavailable)
						return
					}
					data.EditToken = token
				}
			}
		}
		if len(filtered) > 0 {
			all := baseValues(q, status, ordering, group, showOwner, showRegion)
			all.Set("scope", "matching")
			all.Set("theme", theme)
			all.Set("page", strconv.Itoa(page))
			data.AllPreviewURL = link("/preview", all)
		}
		if data.IsPreview {
			scope := v.Get("scope")
			if scope != "" && scope != "matching" {
				http.Error(w, "Invalid selection scope", http.StatusBadRequest)
				return
			}
			data.SelectionScope = "checked rows"
			if scope == "matching" {
				data.SelectionScope = "matching search"
				data.Chosen = filtered
			} else {
				ids := v["ids"]
				if len(ids) > 32 {
					http.Error(w, "Too many selected IDs", http.StatusBadRequest)
					return
				}
				known := make(map[string]struct{}, len(rows))
				for _, item := range rows {
					known[item.ID] = struct{}{}
				}
				requested := make(map[string]struct{}, len(ids))
				for _, id := range ids {
					if _, ok := known[id]; !ok {
						http.Error(w, "Invalid resource ID", http.StatusBadRequest)
						return
					}
					requested[id] = struct{}{}
				}
				for _, item := range visible {
					if _, ok := requested[item.ID]; ok {
						data.Chosen = append(data.Chosen, item)
					}
				}
			}
			data.SelectionCount = len(data.Chosen)
		}
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		if r.Method == http.MethodHead {
			return
		}
		if err := pageTemplate.ExecuteTemplate(w, "page.html", data); err != nil {
			log.Printf("render resource workbench: %v", err)
		}
	})
	return mux
}

// loopbackAddress keeps the unauthenticated, in-memory edit demo off public interfaces.
func loopbackAddress(addr string) bool {
	host, _, err := net.SplitHostPort(addr)
	if err != nil {
		return false
	}
	if host == "localhost" {
		return true
	}
	ip := net.ParseIP(host)
	return ip != nil && ip.IsLoopback()
}

func main() {
	addr := flag.String("addr", "127.0.0.1:8767", "local listen address")
	dist := flag.String("dist", "../../dist", "path to compiled Syntyr CSS")
	flag.Parse()
	if !loopbackAddress(*addr) {
		log.Fatal("This unauthenticated demo must bind to 127.0.0.1, [::1], or localhost")
	}
	log.Printf("Syntyr resource workbench demo at http://%s/resources", *addr)
	log.Fatal(http.ListenAndServe(*addr, newHandler(*dist)))
}
