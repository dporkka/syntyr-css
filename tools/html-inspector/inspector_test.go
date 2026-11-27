package main

import (
	"strings"
	"testing"
)

const fixtureCatalog = `{"schema_version":1,"source_version":"test","components":[{"name":"Button","classes":["syn-button","syn-button--primary"]}],"recipes":[{"id":"shell","root":{"tag":"div","classes":["syn-shell"]},"slots":[{"name":"main","tag":"main","classes":["syn-main"],"optional":false,"repeatable":false},{"name":"aside","tag":"aside","classes":["syn-aside"],"optional":true,"repeatable":false}]}]}`

func runInspection(t *testing.T, html, selector string) Report {
	t.Helper()
	c, err := loadCatalog(strings.NewReader(fixtureCatalog))
	if err != nil {
		t.Fatal(err)
	}
	r, err := inspect(strings.NewReader(html), c, selector)
	if err != nil {
		t.Fatal(err)
	}
	return r
}

func TestSelectorAndClassDiscovery(t *testing.T) {
	r := runInspection(t, `<main><button class="syn-button syn-button--primary local">Go</button><button class="local">Skip</button></main>`, "main > button.syn-button")
	if len(r.Elements) != 1 || len(r.Elements[0].Components) != 1 || r.Elements[0].Components[0] != "Button" || len(r.Elements[0].Classes) != 2 {
		t.Fatalf("%+v", r)
	}
}

func TestDefaultInventoryExcludesUnrelatedAndInertMarkup(t *testing.T) {
	r := runInspection(t, `<div class="not-syn-button"></div><template><button class="syn-button"></button></template><button class="syn-button"></button>`, "")
	if len(r.Elements) != 1 {
		t.Fatalf("%+v", r)
	}
}

func TestRequiredSlotsAndNestedRecipeIsolation(t *testing.T) {
	r := runInspection(t, `<div class="syn-shell"><div class="syn-shell"><main class="syn-main"></main></div></div>`, ".syn-shell")
	if len(r.Elements) != 2 {
		t.Fatalf("%+v", r)
	}
	outer, inner := r.Elements[0].Recipes[0], r.Elements[1].Recipes[0]
	if outer.Slots[0].Status != "missing" || inner.Slots[0].Status != "ok" || outer.Slots[1].Status != "ok" {
		t.Fatalf("%+v %+v", outer, inner)
	}
}

func TestNonrepeatableSlot(t *testing.T) {
	r := runInspection(t, `<div class="syn-shell"><main class="syn-main"></main><main class="syn-main"></main></div>`, ".syn-shell")
	if r.Elements[0].Recipes[0].Slots[0].Status != "multiple" {
		t.Fatalf("%+v", r)
	}
}

func TestInvalidSelectorIsAnError(t *testing.T) {
	c, err := loadCatalog(strings.NewReader(fixtureCatalog))
	if err != nil {
		t.Fatal(err)
	}
	if _, err = inspect(strings.NewReader("<div></div>"), c, "["); err == nil {
		t.Fatal("invalid selector accepted")
	}
}

func TestUnsupportedCatalogVersion(t *testing.T) {
	if _, err := loadCatalog(strings.NewReader(`{"schema_version":99}`)); err == nil {
		t.Fatal("unsupported schema accepted")
	}
}

func TestExplicitSelectorCanMatchUnstyledElements(t *testing.T) {
	r := runInspection(t, `<main><p>Text</p><button class="syn-button"></button></main>`, "main > p, main > button")
	if len(r.Elements) != 2 || r.Elements[0].Tag != "p" || len(r.Elements[0].Classes) != 0 {
		t.Fatalf("%+v", r)
	}
}

func TestHTMLClassWhitespace(t *testing.T) {
	r := runInspection(t, `<button class="syn-button&#160;local"></button><button class="syn-button local"></button>`, "button")
	if len(r.Elements) != 2 || len(r.Elements[0].Components) != 0 || len(r.Elements[1].Components) != 1 {
		t.Fatalf("%+v", r)
	}
}

func TestElementIdentityIsIndependentOfSelector(t *testing.T) {
	html := `<main><button class="syn-button">One</button><button class="syn-button">Two</button></main>`
	all := runInspection(t, html, "button")
	one := runInspection(t, html, "button:nth-child(2)")
	if all.DocumentSHA256 == "" || all.DocumentSHA256 != one.DocumentSHA256 ||
		all.Elements[1].ElementID != one.Elements[0].ElementID ||
		all.Elements[0].ElementID == all.Elements[1].ElementID {
		t.Fatalf("%+v %+v", all, one)
	}
}
