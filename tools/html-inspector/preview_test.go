package main

import (
	"strings"
	"testing"
)

const variantCatalog = `{"schema_version":1,"source_version":"test","components":[{"name":"Button","classes":["syn-button","syn-button--primary","syn-button--outline"]}],"recipes":[]}`

func variantFixture(t *testing.T, html string) (catalog, Report) {
	t.Helper()
	c, err := loadCatalog(strings.NewReader(variantCatalog))
	if err != nil {
		t.Fatal(err)
	}
	r, err := inspect(strings.NewReader(html), c, "button")
	if err != nil {
		t.Fatal(err)
	}
	return c, r
}

func TestPreviewOnlyChangesRequestedModifier(t *testing.T) {
	html := `<button class="local syn-button  syn-button--primary">Save</button><button class="syn-button syn-button--primary">Other</button>`
	c, r := variantFixture(t, html)
	plan, err := previewVariant([]byte(html), c, "button", r.DocumentSHA256, r.Elements[0].ElementID, "syn-button--primary", "syn-button--outline")
	if err != nil {
		t.Fatal(err)
	}
	if plan.Before != "local syn-button  syn-button--primary" || plan.After != "local syn-button  syn-button--outline" || plan.ElementID != r.Elements[0].ElementID || !plan.PreviewOnly {
		t.Fatalf("%+v", plan)
	}
}

func TestPreviewRejectsStaleOrWrongTarget(t *testing.T) {
	html := `<button class="syn-button syn-button--primary">Save</button>`
	c, r := variantFixture(t, html)
	for _, tc := range []struct{ html, selector, id string }{
		{html + " ", "button", r.Elements[0].ElementID},
		{html, "div", r.Elements[0].ElementID},
		{html, "button", "unknown"},
	} {
		if _, err := previewVariant([]byte(tc.html), c, tc.selector, r.DocumentSHA256, tc.id, "syn-button--primary", "syn-button--outline"); err == nil {
			t.Fatalf("accepted %+v", tc)
		}
	}
}

func TestPreviewRejectsUnsafeOrAmbiguousClassChanges(t *testing.T) {
	for _, classes := range []string{"syn-button syn-button--primary syn-button--outline", "syn-button syn-button--primary syn-button--primary", "syn-button--primary", "syn-button syn-button--primary {{ dynamic }}"} {
		html := `<button class="` + classes + `">Save</button>`
		c, r := variantFixture(t, html)
		if _, err := previewVariant([]byte(html), c, "button", r.DocumentSHA256, r.Elements[0].ElementID, "syn-button--primary", "syn-button--outline"); err == nil {
			t.Fatalf("accepted %s", classes)
		}
	}
	html := `<button class="syn-button syn-button--primary">Save</button>`
	c, r := variantFixture(t, html)
	if _, err := previewVariant([]byte(html), c, "button", r.DocumentSHA256, r.Elements[0].ElementID, "syn-button--primary", "syn-button--unknown"); err == nil {
		t.Fatal("unknown variant accepted")
	}
}

func TestPreviewUsesEffectiveHTML5ClassAttribute(t *testing.T) {
	html := `<button class="syn-button syn-button--primary" class="other">Save</button>`
	c, r := variantFixture(t, html)
	plan, err := previewVariant([]byte(html), c, "button", r.DocumentSHA256, r.Elements[0].ElementID, "syn-button--primary", "syn-button--outline")
	if err != nil || plan.Before != "syn-button syn-button--primary" || !plan.PreviewOnly {
		t.Fatalf("%+v %v", plan, err)
	}
}
