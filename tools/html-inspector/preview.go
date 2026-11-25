package main

import (
	"bytes"
	"fmt"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"github.com/andybalholm/cascadia"
)

type VariantPreview struct {
	SchemaVersion  int    `json:"schema_version"`
	SourceVersion  string `json:"source_version"`
	DocumentSHA256 string `json:"document_sha256"`
	ElementID      string `json:"element_id"`
	Selector       string `json:"selector"`
	Attribute      string `json:"attribute"`
	Before         string `json:"before"`
	After          string `json:"after"`
	PreviewOnly    bool   `json:"preview_only"`
}

func previewVariant(data []byte, c catalog, selector, digest, id, from, to string) (VariantPreview, error) {
	fail := func(message string) (VariantPreview, error) { return VariantPreview{}, fmt.Errorf("%s", message) }
	if len(data) > maxInputBytes {
		return fail("HTML exceeds input limit")
	}
	if digest != documentDigest(data) {
		return fail("document digest mismatch; inspect again")
	}
	if selector == "" || id == "" {
		return fail("explicit selector and element ID required")
	}
	base, modifier, ok := strings.Cut(from, "--")
	otherBase, otherModifier, otherOK := strings.Cut(to, "--")
	if !ok || !otherOK || !strings.HasPrefix(base, "syn-") || modifier == "" || otherModifier == "" || base != otherBase || from == to {
		return fail("expected distinct modifiers in the same Syntyr class family")
	}
	known := false
	for _, comp := range c.Components {
		found := map[string]bool{}
		for _, class := range comp.Classes {
			found[class] = true
		}
		if found[base] && found[from] && found[to] {
			known = true
			break
		}
	}
	if !known {
		return fail("variant pair not in curated component catalog")
	}
	matcher, err := cascadia.Compile(selector)
	if err != nil {
		return fail("invalid selector")
	}
	doc, err := goquery.NewDocumentFromReader(bytes.NewReader(data))
	if err != nil {
		return VariantPreview{}, err
	}
	ids := elementIDs(doc)
	var target *goquery.Selection
	doc.FindMatcher(matcher).EachWithBreak(func(_ int, s *goquery.Selection) bool {
		if !inert(s) && ids[s.Get(0)] == id {
			target = s
			return false
		}
		return true
	})
	if target == nil {
		return fail("element ID does not match selector")
	}
	n := target.Get(0)
	if n.Namespace != "" {
		return fail("only HTML elements supported")
	}
	classAttrs := 0
	for _, attr := range n.Attr {
		if attr.Namespace == "" && attr.Key == "class" {
			classAttrs++
		}
	}
	if classAttrs != 1 {
		return fail("expected exactly one class attribute")
	}
	before, exists := target.Attr("class")
	if !exists || strings.ContainsAny(before, "{}$<>") {
		return fail("expected literal class attribute")
	}
	// Reject duplicate or competing modifiers; preserve all other token text and spacing.
	tokens := strings.FieldsFunc(before, htmlSpace)
	baseCount, fromCount := 0, 0
	for _, token := range tokens {
		if token == base {
			baseCount++
		}
		if token == from {
			fromCount++
		} else if strings.HasPrefix(token, base+"--") {
			return fail("competing modifier already present")
		}
	}
	if baseCount != 1 || fromCount != 1 {
		return fail("expected exactly one base and original modifier")
	}
	// Locate the exact token in the decoded attribute without normalizing whitespace.
	after := before
	for start := 0; start < len(before); {
		for start < len(before) && htmlSpace(rune(before[start])) {
			start++
		}
		end := start
		for end < len(before) && !htmlSpace(rune(before[end])) {
			end++
		}
		if before[start:end] == from {
			after = before[:start] + to + before[end:]
			break
		}
		start = end
	}
	return VariantPreview{SchemaVersion: 1, SourceVersion: c.SourceVersion, DocumentSHA256: digest, ElementID: id, Selector: selector, Attribute: "class", Before: before, After: after, PreviewOnly: true}, nil
}
