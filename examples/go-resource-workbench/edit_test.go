package main

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"regexp"
	"strings"
	"testing"
)

func getEditor(t *testing.T, h http.Handler) (*http.Cookie, string) {
	t.Helper()
	recorder := httptest.NewRecorder()
	h.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/resources?id=RS-204&theme=grid", nil))
	body := recorder.Body.String()
	if recorder.Code != http.StatusOK || !strings.Contains(body, `method="post" action="/resource/edit"`) {
		t.Fatalf("expected a native edit form on selected record; code=%d", recorder.Code)
	}
	match := regexp.MustCompile(`name="csrf_token" value="([^"]+)"`).FindStringSubmatch(body)
	if len(match) != 2 || match[1] == "" {
		t.Fatal("missing CSRF form token")
	}
	for _, c := range recorder.Result().Cookies() {
		if c.Name == "syn_demo_csrf" {
			if !c.HttpOnly || c.SameSite != http.SameSiteStrictMode {
				t.Fatal("CSRF cookie must be HttpOnly and SameSite Strict")
			}
			return c, match[1]
		}
	}
	t.Fatal("missing CSRF cookie")
	return nil, ""
}

func postEdit(h http.Handler, cookie *http.Cookie, form url.Values) *httptest.ResponseRecorder {
	req := httptest.NewRequest(http.MethodPost, "/resource/edit", strings.NewReader(form.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	if cookie != nil {
		req.AddCookie(cookie)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func TestEditResourceUsesNativePostAndPRG(t *testing.T) {
	h := newHandler("../../dist")
	cookie, token := getEditor(t, h)
	form := url.Values{"id": {"RS-204"}, "owner": {"Studio Ops"}, "status": {"done"}, "theme": {"grid"}, "csrf_token": {token}}
	rec := postEdit(h, cookie, form)
	if rec.Code != http.StatusSeeOther || rec.Header().Get("Location") != "/resources?id=RS-204&theme=grid" {
		t.Fatalf("expected safe post/redirect/get, code=%d location=%q body=%s", rec.Code, rec.Header().Get("Location"), rec.Body.String())
	}
	result := httptest.NewRecorder()
	h.ServeHTTP(result, httptest.NewRequest(http.MethodGet, "/resources?id=RS-204", nil))
	body := result.Body.String()
	if !strings.Contains(body, "Studio Ops") || !strings.Contains(body, "<dd>done</dd>") {
		t.Fatal("edited resource was not saved in local application state")
	}
	if strings.Contains(body, "<script") {
		t.Fatal("native workflow must not inject application JavaScript")
	}
}

func TestEditRequiresValidCSRFCookieAndToken(t *testing.T) {
	h := newHandler("../../dist")
	cookie, token := getEditor(t, h)
	base := url.Values{"id": {"RS-204"}, "owner": {"Changed"}, "status": {"done"}, "csrf_token": {token}}
	if code := postEdit(h, nil, base).Code; code != http.StatusForbidden {
		t.Fatalf("missing cookie: expected 403, got %d", code)
	}
	wrong := *cookie
	wrong.Value = "tampered"
	if code := postEdit(h, &wrong, base).Code; code != http.StatusForbidden {
		t.Fatalf("tampered cookie: expected 403, got %d", code)
	}
	base.Set("csrf_token", "tampered")
	if code := postEdit(h, cookie, base).Code; code != http.StatusForbidden {
		t.Fatalf("tampered form token: expected 403, got %d", code)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/resources?id=RS-204", nil))
	if !strings.Contains(rec.Body.String(), "Operations") || strings.Contains(rec.Body.String(), "<dd>done</dd>") {
		t.Fatal("failed CSRF attempts must not change record")
	}
}

func TestEditRejectsInvalidFieldsAndDoesNotMutate(t *testing.T) {
	h := newHandler("../../dist")
	cookie, token := getEditor(t, h)
	for _, tc := range []struct{ id, owner, status, theme string }{
		{"missing", "New Owner", "done", "studio"},
		{"RS-204", "", "done", "studio"},
		{"RS-204", strings.Repeat("x", 81), "done", "studio"},
		{"RS-204", "New Owner", "deleted", "studio"},
		{"RS-204", "New Owner", "done", "not-a-theme"},
	} {
		rec := postEdit(h, cookie, url.Values{"id": {tc.id}, "owner": {tc.owner}, "status": {tc.status}, "theme": {tc.theme}, "csrf_token": {token}})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("invalid %v: expected 400 got %d", tc, rec.Code)
		}
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/resources?id=RS-204", nil))
	if !strings.Contains(rec.Body.String(), "<dd>Operations</dd>") || !strings.Contains(rec.Body.String(), "<dd>review</dd>") {
		t.Fatal("invalid edits must not change existing record")
	}
}

func TestEditRespectsMethodAndPerHandlerIsolation(t *testing.T) {
	h := newHandler("../../dist")
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/resource/edit", nil))
	if rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("edit GET should be 405, got %d", rec.Code)
	}
	cookie, token := getEditor(t, h)
	postEdit(h, cookie, url.Values{"id": {"RS-204"}, "owner": {"Changed"}, "status": {"active"}, "csrf_token": {token}})
	pristine := httptest.NewRecorder()
	newHandler("../../dist").ServeHTTP(pristine, httptest.NewRequest(http.MethodGet, "/resources?id=RS-204", nil))
	if !strings.Contains(pristine.Body.String(), "<dd>Operations</dd>") {
		t.Fatal("demo state should be isolated per application instance")
	}
}

func TestLocalDemoRejectsNonLoopbackBindAddresses(t *testing.T) {
	for _, tc := range []struct {
		address string
		allowed bool
	}{
		{"127.0.0.1:8767", true},
		{"[::1]:8767", true},
		{"localhost:8767", true},
		{"0.0.0.0:8767", false},
		{":8767", false},
		{"192.168.1.20:8767", false},
		{"example.com:8767", false},
		{"invalid", false},
	} {
		if got := loopbackAddress(tc.address); got != tc.allowed {
			t.Errorf("%s: allowed=%v, want %v", tc.address, got, tc.allowed)
		}
	}
}
