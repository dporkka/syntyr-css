package main

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/a-h/templ"
)

func rendered(t *testing.T, component templ.Component) string {
	t.Helper()
	var out bytes.Buffer
	if err := component.Render(context.Background(), &out); err != nil {
		t.Fatal(err)
	}
	return out.String()
}

func TestComposableComponentContract(t *testing.T) {
	html := rendered(t, Page(buildPage("", "").Data))
	for _, part := range []string{`class="syn-root`, `class="syn-field`, `class="syn-input"`, `class="syn-button`, `class="syn-table"`, `scope="col"`, `scope="row"`, `aria-label="Resource pages"`, `method="get"`, `rel="next"`} {
		if !strings.Contains(html, part) {
			t.Errorf("missing %q", part)
		}
	}
	if strings.Contains(html, "<script") {
		t.Fatal("client JS not allowed")
	}
	if !strings.Contains(rendered(t, Table(nil)), "No matching resources") {
		t.Fatal("expected empty state")
	}
}

func TestEscapingAndDescribedError(t *testing.T) {
	html := rendered(t, Field(FieldProps{ID: "resource-query", Name: "q", Label: "<query>", Value: `<img src=x onerror=alert(1)>`, Error: "Bad & input"}))
	for _, part := range []string{`aria-invalid="true"`, `aria-describedby="resource-query-error"`, `id="resource-query-error"`, `data-syn-state="error"`, `&lt;query&gt;`, `&lt;img`, `Bad &amp; input`} {
		if !strings.Contains(html, part) {
			t.Errorf("missing %q", part)
		}
	}
	if strings.Contains(html, `<img src=x`) {
		t.Fatal("unescaped HTML")
	}
	html = rendered(t, Notice(NoticeProps{Message: `<script>attack</script>`, Danger: true}))
	if strings.Contains(html, `<script>`) || !strings.Contains(html, `role="alert"`) {
		t.Fatal("notice not safe")
	}
}

func TestTemplPreventsExecutableLinkProtocols(t *testing.T) {
	html := rendered(t, Pagination(PaginationProps{Page: 2, Total: 2, PrevURL: "javascript:alert(1)"}))
	if strings.Contains(html, `href="javascript:`) {
		t.Fatal("templ emitted executable URL")
	}
}

func TestServerQueryAndPagination(t *testing.T) {
	for _, tt := range []struct {
		query, page string
		status      int
	}{
		{"", "", 200}, {"&", "1", 200}, {strings.Repeat("a", 81), "", 400}, {"", "0", 400}, {"", "x", 400}, {"", "999", 400},
	} {
		data := buildPage(tt.query, tt.page)
		if data.Status != tt.status {
			t.Errorf("%q page=%q: %d", tt.query, tt.page, data.Status)
		}
	}
	html := rendered(t, Page(buildPage("&", "1").Data))
	if !strings.Contains(html, `value="&amp;"`) || !strings.Contains(html, `q=%26`) {
		t.Fatal("missing escaped query or encoded pagination")
	}
	html = rendered(t, Page(buildPage("", "2").Data))
	if !strings.Contains(html, `aria-current="page"`) || !strings.Contains(html, `rel="prev"`) {
		t.Fatal("navigation is not accessible")
	}
}

func TestHTTPBoundaries(t *testing.T) {
	for _, test := range []struct {
		method, path string
		status       int
	}{
		{http.MethodGet, "/", 200}, {http.MethodHead, "/", 200},
		{http.MethodGet, "/missing", 404}, {http.MethodPost, "/", 405},
	} {
		recorder := httptest.NewRecorder()
		newHandler("../../dist").ServeHTTP(recorder, httptest.NewRequest(test.method, test.path, nil))
		if recorder.Code != test.status {
			t.Errorf("%s %s: %d", test.method, test.path, recorder.Code)
		}
		if test.method == http.MethodHead && recorder.Body.Len() != 0 {
			t.Fatal("HEAD returned body")
		}
		if test.method == http.MethodPost && recorder.Header().Get("Allow") != "GET, HEAD" {
			t.Fatal("missing Allow header")
		}
	}
}

func TestRejectedTemplSearchHidesResultsAndPagination(t *testing.T) {
	invalid := "&" + strings.Repeat(" ", 79) + "X"
	result := buildPage(invalid, "")
	if result.Status != 400 {
		t.Fatalf("expected 400, got %d", result.Status)
	}
	html := rendered(t, Page(result.Data))
	for _, missing := range []string{`<table class="syn-table"`, `aria-label="Resource pages"`, `rel="next"`} {
		if strings.Contains(html, missing) {
			t.Errorf("rejected search rendered %q", missing)
		}
	}
	if !strings.Contains(html, `aria-invalid="true"`) {
		t.Fatal("missing linked field validation")
	}
	if valid := rendered(t, Page(buildPage("&", "").Data)); !strings.Contains(valid, `rel="next"`) {
		t.Fatal("valid query lost pagination")
	}
}

func TestMalformedTemplQueryReturns400(t *testing.T) {
	for _, path := range []string{"/?q=CRM&page=%ZZ", "/?q=%ZZ", "/?q=CRM%"} {
		rec := httptest.NewRecorder()
		newHandler("../../dist").ServeHTTP(rec, httptest.NewRequest(http.MethodGet, path, nil))
		if rec.Code != 400 {
			t.Errorf("%s: got %d", path, rec.Code)
		}
	}
}
