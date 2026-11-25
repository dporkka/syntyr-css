package main

import (
	"embed"
	"flag"
	"html/template"
	"log"
	"net/http"
	"os"
	"strings"
)

//go:embed templates/*.html
var views embed.FS

var templates = template.Must(template.ParseFS(views, "templates/*.html"))

type contact struct {
	Name    string
	Company string
	Email   string
}

type pageData struct {
	Query       string
	Contacts    []contact
	HTMXEnabled bool
}

var contacts = []contact{
	{"Ada Lovelace", "Analytical Works", "ada@example.test"},
	{"Grace Hopper", "Compiler Labs", "grace@example.test"},
	{"Katherine Johnson", "Orbital Systems", "katherine@example.test"},
	{"Margaret Hamilton", "Flight Software", "margaret@example.test"},
}

func results(query string) []contact {
	query = strings.ToLower(strings.TrimSpace(query))
	found := make([]contact, 0, len(contacts))
	for _, person := range contacts {
		if query == "" || strings.Contains(strings.ToLower(person.Name+" "+person.Company+" "+person.Email), query) {
			found = append(found, person)
		}
	}
	return found
}

// newHandler owns the complete server. Syntyr contributes CSS, not application state.
func newHandler(distDir string, enableHTMX bool) http.Handler {
	mux := http.NewServeMux()
	mux.Handle("/assets/", http.StripPrefix("/assets/", http.FileServer(http.Dir(distDir))))
	if enableHTMX {
		mux.HandleFunc("/vendor/htmx.min.js", func(w http.ResponseWriter, r *http.Request) {
			if r.Method != http.MethodGet && r.Method != http.MethodHead {
				w.Header().Set("Allow", "GET, HEAD")
				http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
				return
			}
			http.ServeFile(w, r, "vendor/htmx.min.js")
		})
	}
	render := func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", http.MethodGet)
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if r.URL.Path != "/" && r.URL.Path != "/contacts" {
			http.NotFound(w, r)
			return
		}
		// HTML fragments and full pages share a URL but must not share cache entries.
		w.Header().Set("Vary", "HX-Request, HX-History-Restore-Request")
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		query := strings.TrimSpace(r.URL.Query().Get("q"))
		// Avoid rendering arbitrarily long untrusted queries.
		if len([]rune(query)) > 128 {
			query = string([]rune(query)[:128])
		}
		data := pageData{Query: query, Contacts: results(query), HTMXEnabled: enableHTMX}
		name := "page"
		if r.URL.Path == "/contacts" && r.Header.Get("HX-Request") == "true" && r.Header.Get("HX-History-Restore-Request") != "true" {
			name = "results"
		}
		if err := templates.ExecuteTemplate(w, name, data); err != nil {
			log.Printf("render: %v", err)
		}
	}
	mux.HandleFunc("/", render)
	return mux
}

func main() {
	addr := flag.String("addr", "127.0.0.1:8766", "listen address")
	enableHTMX := flag.Bool("htmx", false, "enable local vendored HTMX (vendor/htmx.min.js)")
	flag.Parse()
	if *enableHTMX {
		if _, err := os.Stat("vendor/htmx.min.js"); err != nil {
			log.Fatalf("-htmx requires a locally supplied vendor/htmx.min.js: %v", err)
		}
	}
	log.Printf("Syntyr Go demo at http://%s/contacts (HTMX enabled: %v)", *addr, *enableHTMX)
	log.Fatal(http.ListenAndServe(*addr, newHandler("../../dist", *enableHTMX)))
}
