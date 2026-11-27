package main

import (
	"strings"
	"testing"
)

func TestSourcePatchDistinguishesIdenticalButtonsAndPreservesBytes(t *testing.T) {
	source := "<!-- café -->\r\n<button class='syn-button  syn-button--primary' title=\"syn-button--primary\">One</button>\r\n<button class='syn-button  syn-button--primary'>Two</button>"
	c, r := variantFixture(t, source)
	plan, err := previewVariant([]byte(source), c, "button", r.DocumentSHA256, r.Elements[1].ElementID, "syn-button--primary", "syn-button--outline")
	if err != nil {
		t.Fatal(err)
	}
	patch, err := sourcePatch([]byte(source), plan, "syn-button--primary", "syn-button--outline")
	if err != nil {
		t.Fatal(err)
	}
	want := strings.LastIndex(source, "syn-button--primary")
	if patch.StartByte != want || patch.EndByte != want+len("syn-button--primary") {
		t.Fatalf("%+v", patch)
	}
	got := source[:patch.StartByte] + patch.Replacement + source[patch.EndByte:]
	if got != source[:want]+"syn-button--outline"+source[want+len("syn-button--primary"):] {
		t.Fatal(got)
	}
}

func TestSourcePatchRejectsEncodedClassAndDuplicateAttribute(t *testing.T) {
	for _, source := range []string{
		`<button class="syn-button syn-button&#45;&#45;primary">One</button>`,
		`<button class="syn-button syn-button--primary" CLASS="other">One</button>`,
	} {
		c, r := variantFixture(t, source)
		plan, err := previewVariant([]byte(source), c, "button", r.DocumentSHA256, r.Elements[0].ElementID, "syn-button--primary", "syn-button--outline")
		if err != nil {
			t.Fatal(err)
		}
		if _, err := sourcePatch([]byte(source), plan, "syn-button--primary", "syn-button--outline"); err == nil {
			t.Fatal("accepted ambiguous source", source)
		}
	}
}

func TestSourcePatchDoesNotEditScriptOrComments(t *testing.T) {
	source := `<script>const x='<button class="syn-button syn-button--primary">';</script><!-- <button class="syn-button syn-button--primary"> --><button class="syn-button syn-button--primary">Actual</button>`
	c, r := variantFixture(t, source)
	plan, err := previewVariant([]byte(source), c, "button", r.DocumentSHA256, r.Elements[0].ElementID, "syn-button--primary", "syn-button--outline")
	if err != nil {
		t.Fatal(err)
	}
	patch, err := sourcePatch([]byte(source), plan, "syn-button--primary", "syn-button--outline")
	if err != nil || patch.StartByte != strings.LastIndex(source, "syn-button--primary") {
		t.Fatalf("%+v %v", patch, err)
	}
}
