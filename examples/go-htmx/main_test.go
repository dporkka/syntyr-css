package main

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func exercise(t *testing.T, h http.Handler, url string, hx bool) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(http.MethodGet, url, nil)
	if hx {
		req.Header.Set("HX-Request", "true")
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func TestFullDocumentSupportsNativeGETAndEscapesUserInput(t *testing.T) {
	h := newHandler("../../dist", false)
	rec := exercise(t, h, "/contacts?q=%3Cscript%3E", false)
	if rec.Code != http.StatusOK {
		t.Fatalf("status: %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), "<!doctype html>") {
		t.Error("missing full document")
	}
	if !strings.Contains(rec.Body.String(), "method=\"get\"") {
		t.Error("native GET form missing")
	}
	if strings.Contains(rec.Body.String(), "<script>") {
		t.Error("unsafe reflected query")
	}
	if !strings.Contains(rec.Body.String(), "&lt;script&gt;") {
		t.Error("escaped query not preserved")
	}
	if strings.Contains(rec.Body.String(), "htmx.min.js") {
		t.Error("optional HTMX loaded by default")
	}
}

func TestHTMXReturnsOnlyFragmentAndVariesByRequestHeader(t *testing.T) {
	h := newHandler("../../dist", false)
	rec := exercise(t, h, "/contacts?q=ada", true)
	if rec.Code != http.StatusOK {
		t.Fatalf("status: %d", rec.Code)
	}
	if strings.Contains(rec.Body.String(), "<!doctype html>") {
		t.Error("HTMX response was a full page")
	}
	if !strings.Contains(rec.Body.String(), "Ada") {
		t.Error("query did not filter contacts")
	}
	if strings.Contains(rec.Body.String(), "Grace") {
		t.Error("query returned unrelated contacts")
	}
	if rec.Header().Get("Vary") != "HX-Request, HX-History-Restore-Request" {
		t.Error("missing Vary: HX-Request, HX-History-Restore-Request")
	}
	if got := rec.Header().Get("Content-Type"); !strings.HasPrefix(got, "text/html") {
		t.Errorf("content type: %s", got)
	}
}

func TestHTMXHistoryRestoreReturnsCompleteDocument(t *testing.T) {
	h := newHandler("../../dist", false)
	req := httptest.NewRequest(http.MethodGet, "/contacts?q=ada", nil)
	req.Header.Set("HX-Request", "true")
	req.Header.Set("HX-History-Restore-Request", "true")
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("history restore status: %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), "<!doctype html>") {
		t.Errorf("history restore must return a full document: %s", rec.Body.String())
	}
	if !strings.Contains(rec.Body.String(), "method=\"get\"") {
		t.Error("history restore lost the native search form")
	}
	if !strings.Contains(rec.Body.String(), "Ada Lovelace") {
		t.Error("history restore lost filtered results")
	}
}

func TestDefaultRouteAndCSSAreServed(t *testing.T) {
	h := newHandler("../../dist", false)
	if rec := exercise(t, h, "/", false); rec.Code != http.StatusOK {
		t.Errorf("home status: %d", rec.Code)
	}
	req := httptest.NewRequest(http.MethodGet, "/assets/syntyr.core.css", nil)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("stylesheet status: %d", rec.Code)
	}
	content, _ := io.ReadAll(rec.Body)
	if !strings.Contains(string(content), "--syn-") {
		t.Error("wrong stylesheet served")
	}
}

func TestRejectsMutatingRequests(t *testing.T) {
	h := newHandler("../../dist", false)
	req := httptest.NewRequest(http.MethodPost, "/contacts", strings.NewReader("q=abc"))
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusMethodNotAllowed {
		t.Errorf("status: %d", rec.Code)
	}
	if rec.Header().Get("Allow") != http.MethodGet {
		t.Error("missing Allow header")
	}
}

func TestResultStatusUsesAccurateSingularAndPlural(t *testing.T) {
	h := newHandler("../../dist", false)
	singular := exercise(t, h, "/contacts?q=Ada", true)
	plural := exercise(t, h, "/contacts", true)
	if !strings.Contains(singular.Body.String(), "1 contact found.") {
		t.Errorf("singular status: %s", singular.Body.String())
	}
	if !strings.Contains(plural.Body.String(), "4 contacts found.") {
		t.Errorf("plural status: %s", plural.Body.String())
	}
}

func TestOptionalHTMXScriptIsExplicit(t *testing.T) {
	h := newHandler("../../dist", true)
	rec := exercise(t, h, "/contacts", false)
	if !strings.Contains(rec.Body.String(), "/vendor/htmx.min.js") {
		t.Error("HTMX script was not enabled")
	}
	if !strings.Contains(rec.Body.String(), "hx-get=\"/contacts\"") {
		t.Error("enhancement attributes missing")
	}
}
