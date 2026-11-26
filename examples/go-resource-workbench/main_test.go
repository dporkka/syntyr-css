package main

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

func request(t *testing.T, path string) (int, string) {
	t.Helper()
	recorder := httptest.NewRecorder()
	newHandler("../../dist").ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, path, nil))
	return recorder.Code, recorder.Body.String()
}

func TestFilteredResourcesAndQueryPreservation(t *testing.T) {
	code, body := request(t, "/resources?q=harbor&status=review")
	if code != http.StatusOK {
		t.Fatalf("code = %d", code)
	}
	if !strings.Contains(body, "Harbor East") || strings.Contains(body, "Civic Center") {
		t.Fatal("server search/status did not constrain visible records")
	}
	if !strings.Contains(body, `value="harbor"`) || !strings.Contains(body, `value="review" selected`) {
		t.Fatal("query state not restored in GET form")
	}
	if !strings.Contains(body, "1 result") {
		t.Fatal("truthful result count missing")
	}
	if !strings.Contains(body, "/resources?") || !strings.Contains(body, "id=RS-204") || !strings.Contains(body, "q=harbor") {
		t.Fatal("record links missing")
	}
}

func TestNoResultsWithFilter(t *testing.T) {
	code, body := request(t, "/resources?q=nonexistent&status=active")
	if code != http.StatusOK || !strings.Contains(body, "No matching resources") || strings.Contains(body, "Preview all 0") {
		t.Fatal("empty search must show helpful real zero-results state")
	}
}

func TestInspectorTracksOnlyVisibleFilteredRecord(t *testing.T) {
	code, body := request(t, "/resources?q=harbor&status=review&id=RS-204")
	if code != http.StatusOK || !strings.Contains(body, "<h3>Selected record: Harbor East</h3>") {
		t.Fatal("visible record not shown in inspector")
	}
	_, body = request(t, "/resources?q=harbor&status=active&id=RS-204")
	if strings.Contains(body, "Selected record:") {
		t.Fatal("inspector leaked record that was excluded by current filter")
	}
}

func TestColumnSettingsAndSorting(t *testing.T) {
	code, body := request(t, "/resources?columns_present=1&columns=owner&sort=name")
	if code != http.StatusOK {
		t.Fatalf("code = %d", code)
	}
	if !strings.Contains(body, `<th scope="col">Owner</th>`) || strings.Contains(body, `<th scope="col">Region</th>`) {
		t.Fatal("host did not honor declared column settings")
	}
	a, b := strings.Index(body, "Civic Center"), strings.Index(body, "Harbor East")
	if a < 0 || b < 0 || a > b {
		t.Fatal("name sort failed")
	}
}

func TestBulkPreviewCheckedIdsMustMatchFilter(t *testing.T) {
	params := url.Values{"ids": {"RS-204", "RS-088"}, "q": {"harbor"}, "status": {"review"}}
	code, body := request(t, "/preview?"+params.Encode())
	if code != http.StatusOK || !strings.Contains(body, "<p>1 selected.</p>") ||
		!strings.Contains(body, "<li>RS-204 — Harbor East (review)</li>") ||
		strings.Contains(body, "<li>RS-088 — Civic Center (active)</li>") {
		t.Fatal("checked-selection preview must intersect the active search results")
	}
	if !strings.Contains(body, "Preview only") {
		t.Fatal("must distinguish preview from mutation")
	}
}

func TestMatchingScopeComputedOnServer(t *testing.T) {
	code, body := request(t, "/preview?scope=matching&status=review")
	if code != http.StatusOK || !strings.Contains(body, "matching search") ||
		!strings.Contains(body, "<p>2 selected.</p>") ||
		!strings.Contains(body, "<li>RS-204 — Harbor East (review)</li>") ||
		!strings.Contains(body, "<li>RS-144 — Riverside Digital (review)</li>") ||
		strings.Contains(body, "<li>RS-088 — Civic Center (active)</li>") {
		t.Fatal("matching-scope preview must use server-filtered results")
	}
	_, body = request(t, "/preview?status=review")
	if !strings.Contains(body, "No resources selected") {
		t.Fatal("empty selection must not implicitly become select-all")
	}
}

func TestRejectUnknownIDsAndBadScopes(t *testing.T) {
	for _, path := range []string{"/preview?ids=missing", "/preview?scope=everything", "/preview?ids=RS-204&ids=missing"} {
		code, _ := request(t, path)
		if code != http.StatusBadRequest {
			t.Fatalf("%s: code = %d", path, code)
		}
	}
}

func TestRejectMutationAndEscapeSearchText(t *testing.T) {
	recorder := httptest.NewRecorder()
	newHandler("../../dist").ServeHTTP(recorder, httptest.NewRequest(http.MethodPost, "/resources", nil))
	if recorder.Code != http.StatusMethodNotAllowed {
		t.Fatalf("POST code = %d", recorder.Code)
	}
	code, body := request(t, "/resources?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E")
	if code != http.StatusOK || strings.Contains(body, "<script>alert(1)</script>") || !strings.Contains(body, "&lt;script&gt;") {
		t.Fatal("untrusted search query not escaped")
	}
}

func TestThemePersistsAcrossFilteredViewsAndPreview(t *testing.T) {
	code, body := request(t, "/resources?theme=grid&q=harbor")
	if code != http.StatusOK || !strings.Contains(body, `data-syn-theme="grid"`) ||
		!strings.Contains(body, "theme=grid") {
		t.Fatal("theme should be applied and retained in resource links")
	}
	code, body = request(t, "/preview?scope=matching&theme=noir")
	if code != http.StatusOK || !strings.Contains(body, `data-syn-theme="noir"`) {
		t.Fatal("preview should retain chosen theme")
	}
	code, _ = request(t, "/resources?theme=nonexistent")
	if code != http.StatusBadRequest {
		t.Fatal("unknown theme must fail closed")
	}
}

func TestPaginationUsesBoundedRowsAndPreservesViewState(t *testing.T) {
	code, body := request(t, "/resources?page=2&sort=name&theme=grid&columns_present=1&columns=owner")
	if code != http.StatusOK || !strings.Contains(body, "Page 2 of 2") {
		t.Fatalf("expected second page, code=%d", code)
	}
	if strings.Contains(body, "Airport Loop") || strings.Contains(body, "Civic Center") || !strings.Contains(body, "Transit Hub") {
		t.Fatal("second page must display only second-page resources")
	}
	if !strings.Contains(body, "page=1") || !strings.Contains(body, "sort=name") || !strings.Contains(body, "theme=grid") || !strings.Contains(body, "columns=owner") {
		t.Fatal("pagination must preserve filters, theme and column settings")
	}
	if !strings.Contains(body, "6 results") {
		t.Fatal("total filtered count must not become a page-length count")
	}
}

func TestInvalidPagesFailClosed(t *testing.T) {
	paths := []string{"/resources?page=0", "/resources?page=-1", "/resources?page=nope", "/resources?page=99", "/resources?status=review&page=2", "/preview?page=999&scope=matching"}
	for _, path := range paths {
		code, _ := request(t, path)
		if code != http.StatusBadRequest {
			t.Errorf("%s: code = %d", path, code)
		}
	}
}

func TestCheckedPreviewIsPageScopedButMatchingScopeSpansPages(t *testing.T) {
	code, body := request(t, "/preview?page=2&ids=RS-204")
	if code != http.StatusOK || !strings.Contains(body, "No resources selected") || strings.Contains(body, "<li>RS-204") {
		t.Fatal("checked selection must not include a record from a different page")
	}
	code, body = request(t, "/preview?page=2&ids=RS-088")
	if code != http.StatusOK || !strings.Contains(body, "1 selected") || !strings.Contains(body, "<li>RS-088") {
		t.Fatal("valid checked IDs on the current page should work")
	}
	code, body = request(t, "/preview?page=2&scope=matching")
	if code != http.StatusOK || !strings.Contains(body, "6 selected") || !strings.Contains(body, "page=2") {
		t.Fatal("explicit matching scope should span all filtered pages and retain return page")
	}
}

func TestInspectorHonorsVisiblePage(t *testing.T) {
	_, body := request(t, "/resources?page=2&id=RS-204")
	if strings.Contains(body, "Selected record: Harbor East") {
		t.Fatal("inspector must not reveal record excluded by current page")
	}
	_, body = request(t, "/resources?page=2&id=RS-088")
	if !strings.Contains(body, "Selected record: Civic Center") {
		t.Fatal("inspector must open a visible current-page record")
	}
}

func TestGroupingUsesAllMatchingCountsButOnlyVisibleRows(t *testing.T) {
	code, body := request(t, "/resources?group=status&sort=name&columns_present=1")
	if code != http.StatusOK ||
		!strings.Contains(body, `<th scope="rowgroup" colspan="4">active · 2 on this page · 2 matching in group</th>`) ||
		!strings.Contains(body, "done · 1 on this page · 2 matching in group") ||
		strings.Contains(body, "review ·") {
		t.Fatalf("incorrect grouping or page counts: code=%d", code)
	}
	if strings.Index(body, "Airport Loop") > strings.Index(body, "Civic Center") {
		t.Fatal("the selected sort must be retained within the group")
	}
	_, body = request(t, "/resources?group=status&sort=name&page=2")
	if !strings.Contains(body, "done · 1 on this page · 2 matching in group") ||
		!strings.Contains(body, "review · 2 on this page · 2 matching in group") {
		t.Fatal("a split group must retain its full matching count")
	}
	_, body = request(t, "/resources?group=region&q=North")
	if !strings.Contains(body, "North · 2 on this page · 2 matching in group") ||
		strings.Contains(body, "West ·") {
		t.Fatal("group totals must use only filtered records")
	}
}

func TestGroupingPersistsAcrossPaginationAndSelection(t *testing.T) {
	code, body := request(t, "/resources?group=status&sort=name")
	if code != http.StatusOK ||
		!strings.Contains(body, "group=status&amp;") ||
		!strings.Contains(body, `name="group" value="status"`) {
		t.Fatal("grouping must survive navigation and checked selection")
	}
	_, body = request(t, "/preview?group=status&sort=name&page=2&ids=RS-301")
	if !strings.Contains(body, "No resources selected") {
		t.Fatal("checked selection must use the grouped, paginated result set")
	}
	_, body = request(t, "/preview?group=status&sort=name&page=2&scope=matching")
	if !strings.Contains(body, "6 selected.") {
		t.Fatal("matching preview must still span all grouped pages")
	}
	for _, path := range []string{"/resources?group=owner", "/resources?group=status&group=region", "/preview?scope=matching&group=unknown"} {
		code, _ := request(t, path)
		if code != http.StatusBadRequest {
			t.Errorf("%s: expected 400, got %d", path, code)
		}
	}
}
