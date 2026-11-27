package main

import (
	"strings"
	"testing"
)

func TestCombinedProofRejectsWrongTargetAndAcceptsTwoEdits(t *testing.T) {
	source := `<button class="syn-button syn-button--primary">One</button><button class="syn-button syn-button--primary">Two</button>`
	c, r := variantFixture(t, source)
	ops := []CombinedOperation{}
	for _, e := range r.Elements {
		p, err := previewVariant([]byte(source), c, "button", r.DocumentSHA256, e.ElementID, "syn-button--primary", "syn-button--outline")
		if err != nil {
			t.Fatal(err)
		}
		patch, err := sourcePatch([]byte(source), p, "syn-button--primary", "syn-button--outline")
		if err != nil {
			t.Fatal(err)
		}
		ops = append(ops, CombinedOperation{ElementID: e.ElementID, Selector: "button", From: "syn-button--primary", To: "syn-button--outline", Patch: patch})
	}
	result, err := verifyCombined([]byte(source), c, r.DocumentSHA256, ops)
	if err != nil || result != documentDigest([]byte(strings.ReplaceAll(source, "syn-button--primary", "syn-button--outline"))) {
		t.Fatalf("%s %v", result, err)
	}
	ops[0].Patch, ops[1].Patch = ops[1].Patch, ops[0].Patch
	// Swapping equivalent replacements still produces the intended combined DOM.
	// A single wrong-target patch must fail.
	if _, err := verifyCombined([]byte(source), c, r.DocumentSHA256, ops[:1]); err == nil {
		t.Fatal("wrong target accepted")
	}
	ops[1].Patch = ops[0].Patch
	if _, err := verifyCombined([]byte(source), c, r.DocumentSHA256, ops); err == nil {
		t.Fatal("overlap accepted")
	}
}
