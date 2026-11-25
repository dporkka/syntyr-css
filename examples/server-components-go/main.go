// An optional, zero-dependency Syntyr server component example.
// Syntyr owns CSS; Go owns rendering, validation, routing and query state.
package main

import (
	"bytes"
	"embed"
	"flag"
	"html/template"
	"log"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"unicode/utf8"
)

//go:embed templates/*.html
var source embed.FS

var views = template.Must(template.ParseFS(source, "templates/*.html"))

type textField struct {
	ID, Name, Label, Value, Help, Error string
}

type notice struct {
	Message string
	Danger  bool
}

type button struct {
	Label           string
	Primary, Submit bool
}

type record struct {
	Title, Description string
}

type pagination struct {
	Page, Total      int
	PrevURL, NextURL string
}

type pageData struct {
	ShowResults  bool
	Query        textField
	Notice       notice
	SearchButton button
	Records      []record
	Pager        pagination
}

var resources = []record{
	{"Billing", "Invoices & statements"},
	{"CRM", "Accounts & contacts"},
	{"Inventory", "Assets & availability"},
	{"Operations", "Work orders and inspections"},
	{"Proposals", "Contracts and approvals"},
	{"Reporting", "Revenue and campaign summaries"},
}

const pageSize = 2
const maxQueryRunes = 80

func pageHref(query string, page int) string {
	values := url.Values{}
	if query != "" {
		values.Set("q", query)
	}
	if page > 1 {
		values.Set("page", strconv.Itoa(page))
	}
	if len(values) == 0 {
		return "/"
	}
	return "/?" + values.Encode()
}

func makePage(query, rawPage string) (pageData, int) {
	data := pageData{
		ShowResults:  true,
		Query:        textField{ID: "resource-query", Name: "q", Label: "Find a resource", Value: query, Help: "Search titles and descriptions."},
		SearchButton: button{Label: "Search", Submit: true, Primary: true},
		Notice:       notice{Message: "Filtered on the server. No browser JavaScript required."},
	}
	status := http.StatusOK
	if utf8.RuneCountInString(query) > maxQueryRunes {
		data.Query.Value = string([]rune(query)[:maxQueryRunes])
		data.Query.Error = "Search must be at most 80 characters."
		status = http.StatusBadRequest
	}
	filtered := make([]record, 0, len(resources))
	needle := strings.ToLower(strings.TrimSpace(data.Query.Value))
	for _, resource := range resources {
		if needle == "" || strings.Contains(strings.ToLower(resource.Title+" "+resource.Description), needle) {
			filtered = append(filtered, resource)
		}
	}
	total := (len(filtered) + pageSize - 1) / pageSize
	if total == 0 {
		total = 1
	}
	page := 1
	if rawPage != "" {
		parsed, err := strconv.Atoi(rawPage)
		if err != nil || parsed < 1 || parsed > total {
			status = http.StatusBadRequest
			data.Notice = notice{Message: "Page number is invalid for these results.", Danger: true}
		} else {
			page = parsed
		}
	}
	if data.Query.Error != "" {
		data.Notice = notice{Message: "Correct the search field and try again.", Danger: true}
		// Invalid input is for error display only; truncated input is never
		// silently treated as a new, valid search with actionable pagination.
		data.ShowResults = false
		return data, status
	}
	start := (page - 1) * pageSize
	end := start + pageSize
	if end > len(filtered) {
		end = len(filtered)
	}
	data.Records = filtered[start:end]
	data.Pager = pagination{Page: page, Total: total}
	if page > 1 {
		data.Pager.PrevURL = pageHref(data.Query.Value, page-1)
	}
	if page < total {
		data.Pager.NextURL = pageHref(data.Query.Value, page+1)
	}
	return data, status
}

func newHandler(distDir string) http.Handler {
	mux := http.NewServeMux()
	mux.Handle("/assets/", http.StripPrefix("/assets/", http.FileServer(http.Dir(distDir))))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		params, err := url.ParseQuery(r.URL.RawQuery)
		if err != nil {
			http.Error(w, "Invalid query encoding", http.StatusBadRequest)
			return
		}
		data, status := makePage(params.Get("q"), params.Get("page"))
		var html bytes.Buffer
		if err := views.ExecuteTemplate(&html, "page", data); err != nil {
			log.Printf("render: %v", err)
			http.Error(w, "Rendering failed", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.WriteHeader(status)
		if r.Method != http.MethodHead {
			_, _ = w.Write(html.Bytes())
		}
	})
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// A shared method gate also covers the static stylesheet route, which
		// the standard library FileServer does not restrict on its own.
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", "GET, HEAD")
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		mux.ServeHTTP(w, r)
	})
}

func main() {
	address := flag.String("addr", "127.0.0.1:8767", "development listen address")
	dist := flag.String("dist", "../../dist", "path to built Syntyr CSS files")
	flag.Parse()
	log.Printf("Syntyr server components at http://%s/", *address)
	log.Fatal(http.ListenAndServe(*address, newHandler(*dist)))
}
