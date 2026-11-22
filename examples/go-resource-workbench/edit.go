package main

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
	"unicode"
	"unicode/utf8"
)

const csrfCookieName = "syn_demo_csrf"

type resourceState struct {
	mu   sync.RWMutex
	rows []resource
}

func newResourceState() *resourceState {
	return &resourceState{rows: append([]resource(nil), resources...)}
}

func (s *resourceState) snapshot() []resource {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return append([]resource(nil), s.rows...)
}

func validOwner(value string) bool {
	if value == "" || utf8.RuneCountInString(value) > 80 {
		return false
	}
	for _, char := range value {
		if unicode.IsControl(char) {
			return false
		}
	}
	return true
}

func validStatus(value string) bool {
	return value == "active" || value == "review" || value == "done"
}

func validTheme(value string) bool {
	return value == "" || value == "studio" || value == "grid" || value == "noir"
}

func (s *resourceState) edit(id, owner, status string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	for i := range s.rows {
		if s.rows[i].ID == id {
			s.rows[i].Owner = owner
			s.rows[i].Status = status
			s.rows[i].Updated = time.Now().UTC().Format("2006-01-02")
			return true
		}
	}
	return false
}

func newCSRFSecret() [32]byte {
	var secret [32]byte
	if _, err := rand.Read(secret[:]); err != nil {
		// An app unable to obtain secure randomness must not accept edits.
		panic("unable to create local demo CSRF secret: " + err.Error())
	}
	return secret
}

func signedToken(secret [32]byte, nonce string) string {
	mac := hmac.New(sha256.New, secret[:])
	mac.Write([]byte(nonce))
	return hex.EncodeToString(mac.Sum(nil))
}

// issueFormToken binds an edit form to an HttpOnly, same-site cookie.
// This is *not* an authentication system: the example is localhost-only.
func issueFormToken(w http.ResponseWriter, r *http.Request, secret [32]byte) (string, error) {
	nonce := ""
	if cookie, err := r.Cookie(csrfCookieName); err == nil {
		raw, decErr := hex.DecodeString(cookie.Value)
		if decErr == nil && len(raw) == 32 {
			nonce = cookie.Value
		}
	}
	if nonce == "" {
		bytes := make([]byte, 32)
		if _, err := rand.Read(bytes); err != nil {
			return "", err
		}
		nonce = hex.EncodeToString(bytes)
		http.SetCookie(w, &http.Cookie{
			Name: csrfCookieName, Value: nonce, Path: "/", HttpOnly: true,
			SameSite: http.SameSiteStrictMode, Secure: r.TLS != nil,
		})
	}
	return signedToken(secret, nonce), nil
}

func validateFormToken(r *http.Request, secret [32]byte) bool {
	cookie, err := r.Cookie(csrfCookieName)
	if err != nil {
		return false
	}
	nonce, err := hex.DecodeString(cookie.Value)
	if err != nil || len(nonce) != 32 {
		return false
	}
	provided, err := hex.DecodeString(r.PostFormValue("csrf_token"))
	if err != nil || len(provided) != sha256.Size {
		return false
	}
	expected, _ := hex.DecodeString(signedToken(secret, cookie.Value))
	return hmac.Equal(provided, expected)
}

func singleValue(form url.Values, key string) (string, bool) {
	values, exists := form[key]
	return valueOrEmpty(values), exists && len(values) == 1
}

func valueOrEmpty(values []string) string {
	if len(values) != 1 {
		return ""
	}
	return values[0]
}

func editHandler(state *resourceState, secret [32]byte) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		if r.Method != http.MethodPost {
			w.Header().Set("Allow", http.MethodPost)
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		r.Body = http.MaxBytesReader(w, r.Body, 4096)
		if err := r.ParseForm(); err != nil {
			http.Error(w, "Invalid form", http.StatusBadRequest)
			return
		}
		if !validateFormToken(r, secret) {
			http.Error(w, "Invalid form token", http.StatusForbidden)
			return
		}
		// A form must not select an arbitrary redirect destination.
		id, okID := singleValue(r.PostForm, "id")
		owner, okOwner := singleValue(r.PostForm, "owner")
		status, okStatus := singleValue(r.PostForm, "status")
		theme, okTheme := singleValue(r.PostForm, "theme")
		if !okTheme {
			if _, exists := r.PostForm["theme"]; !exists {
				okTheme = true
				theme = ""
			}
		}
		owner = strings.TrimSpace(owner)
		if !okID || !okOwner || !okStatus || !okTheme || !validOwner(owner) ||
			!validStatus(status) || !validTheme(theme) {
			http.Error(w, "Invalid resource edit", http.StatusBadRequest)
			return
		}
		if !state.edit(id, owner, status) {
			http.Error(w, "Unknown resource ID", http.StatusBadRequest)
			return
		}
		values := url.Values{"id": {id}}
		if theme != "" {
			values.Set("theme", theme)
		}
		http.Redirect(w, r, link("/resources", values), http.StatusSeeOther)
	}
}
