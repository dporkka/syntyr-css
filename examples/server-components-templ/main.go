package main

import (
	"bytes"
	"flag"
	"log"
	"net/http"
	"net/url"
	"path/filepath"
)

// The application, not Syntyr, owns routing, errors, query state and file serving.
func newHandler(distDir string) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/assets/syntyr.core.css", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", "GET, HEAD")
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		w.Header().Set("X-Content-Type-Options", "nosniff")
		http.ServeFile(w, r, filepath.Join(distDir, "syntyr.core.css"))
	})
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", "GET, HEAD")
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		params, err := url.ParseQuery(r.URL.RawQuery)
		if err != nil {
			http.Error(w, "Invalid query encoding", http.StatusBadRequest)
			return
		}
		result := buildPage(params.Get("q"), params.Get("page"))
		var html bytes.Buffer
		if err := Page(result.Data).Render(r.Context(), &html); err != nil {
			log.Printf("render: %v", err)
			http.Error(w, "Rendering failed", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.WriteHeader(result.Status)
		if r.Method != http.MethodHead {
			_, _ = w.Write(html.Bytes())
		}
	})
	return mux
}

func main() {
	addr := flag.String("addr", "127.0.0.1:8769", "local listen address")
	dist := flag.String("dist", "../../dist", "path to built Syntyr CSS")
	flag.Parse()
	log.Printf("Syntyr Go templ server components at http://%s/", *addr)
	log.Fatal(http.ListenAndServe(*addr, newHandler(*dist)))
}
