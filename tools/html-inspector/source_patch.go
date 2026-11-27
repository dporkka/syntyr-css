package main

import (
	"bytes"
	"fmt"
	"io"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"golang.org/x/net/html"
)

type SourcePatch struct {
	StartByte   int    `json:"start_byte"`
	EndByte     int    `json:"end_byte"`
	Expected    string `json:"expected"`
	Replacement string `json:"replacement"`
}

const maxPatchInput = 80_000
const maxPatchCandidates = 16

// Restrict the lexical mapping to ordinary literal start tags. The HTML5
// tokenizer supplies the raw tag boundary; this scanner never scans text,
// comments or script content. Reject unsupported syntax instead of guessing.
func literalClassRange(raw []byte, before string) (int, int, bool) {
	if len(raw) < 3 || raw[0] != '<' {
		return 0, 0, false
	}
	space := func(b byte) bool { return htmlSpace(rune(b)) }
	delim := func(b byte) bool { return space(b) || strings.ContainsRune("/>=\"'<", rune(b)) }
	i := 1
	for i < len(raw) && !delim(raw[i]) {
		i++
	}
	start, end, count := 0, 0, 0
	for i < len(raw) {
		for i < len(raw) && space(raw[i]) {
			i++
		}
		if i >= len(raw) {
			return 0, 0, false
		}
		if raw[i] == '>' || (raw[i] == '/' && i+1 < len(raw) && raw[i+1] == '>') {
			break
		}
		a := i
		for i < len(raw) && !delim(raw[i]) {
			i++
		}
		if i == a {
			return 0, 0, false
		}
		name := string(raw[a:i])
		for i < len(raw) && space(raw[i]) {
			i++
		}
		vstart, vend := i, i
		hasValue := i < len(raw) && raw[i] == '='
		if hasValue {
			i++
			for i < len(raw) && space(raw[i]) {
				i++
			}
			if i >= len(raw) {
				return 0, 0, false
			}
			if raw[i] == '"' || raw[i] == '\'' {
				quote := raw[i]
				i++
				vstart = i
				for i < len(raw) && raw[i] != quote {
					i++
				}
				if i >= len(raw) {
					return 0, 0, false
				}
				vend = i
				i++
			} else {
				vstart = i
				for i < len(raw) && !space(raw[i]) && raw[i] != '>' {
					if strings.ContainsRune("\"'<=`", rune(raw[i])) {
						return 0, 0, false
					}
					i++
				}
				vend = i
			}
		}
		if strings.EqualFold(name, "class") {
			count++
			if !hasValue || string(raw[vstart:vend]) != before || bytes.ContainsAny(raw[vstart:vend], "&\r\x00") {
				return 0, 0, false
			}
			start, end = vstart, vend
		}
	}
	return start, end, count == 1
}

func tokenRange(value []byte, token string) (int, int, bool) {
	for i := 0; i < len(value); {
		for i < len(value) && htmlSpace(rune(value[i])) {
			i++
		}
		start := i
		for i < len(value) && !htmlSpace(rune(value[i])) {
			i++
		}
		if string(value[start:i]) == token {
			return start, i, true
		}
	}
	return 0, 0, false
}

// Compare actual tree structure without serializing HTML or relying on
// source formatting. Parent/sibling pointers are deliberately not compared.
func sameTree(a, b *html.Node) bool {
	if a == nil || b == nil {
		return a == b
	}
	if a.Type != b.Type || a.Data != b.Data || a.Namespace != b.Namespace ||
		a.DataAtom != b.DataAtom || len(a.Attr) != len(b.Attr) {
		return false
	}
	for i := range a.Attr {
		if a.Attr[i] != b.Attr[i] {
			return false
		}
	}
	x, y := a.FirstChild, b.FirstChild
	for x != nil && y != nil {
		if !sameTree(x, y) {
			return false
		}
		x, y = x.NextSibling, y.NextSibling
	}
	return x == nil && y == nil
}

// Prove a candidate byte edit by comparing its reparsed tree with the tree
// obtained by changing only the selected node's effective class attribute.
func sourcePatch(data []byte, plan VariantPreview, from, to string) (SourcePatch, error) {
	fail := func(msg string) (SourcePatch, error) { return SourcePatch{}, fmt.Errorf("%s", msg) }
	if len(data) > maxPatchInput || plan.DocumentSHA256 != documentDigest(data) {
		return fail("source patch input exceeds limit or digest mismatch")
	}
	doc, err := goquery.NewDocumentFromReader(bytes.NewReader(data))
	if err != nil {
		return SourcePatch{}, err
	}
	ids := elementIDs(doc)
	var target *goquery.Selection
	doc.Find("*").EachWithBreak(func(_ int, s *goquery.Selection) bool {
		if ids[s.Get(0)] == plan.ElementID {
			target = s
			return false
		}
		return true
	})
	if target == nil {
		return fail("target missing")
	}
	tag := goquery.NodeName(target)
	target.SetAttr("class", plan.After)
	expected := doc.Get(0)
	z := html.NewTokenizer(bytes.NewReader(data))
	offset, attempts := 0, 0
	var verified []SourcePatch
	for {
		kind := z.Next()
		if kind == html.ErrorToken {
			if z.Err() != io.EOF {
				return SourcePatch{}, z.Err()
			}
			break
		}
		raw := z.Raw()
		if kind == html.StartTagToken || kind == html.SelfClosingTagToken {
			// Token() can normalize the tokenizer buffer; retain the original bytes.
			original := data[offset : offset+len(raw)]
			tok := z.Token()
			if tok.Data == tag {
				for _, a := range tok.Attr {
					if a.Key != "class" || a.Val != plan.Before {
						continue
					}
					start, end, ok := literalClassRange(original, plan.Before)
					if !ok {
						continue
					}
					lo, hi, ok := tokenRange(original[start:end], from)
					if !ok {
						continue
					}
					lo += offset + start
					hi += offset + start
					attempts++
					if attempts > maxPatchCandidates {
						return fail("too many matching source candidates")
					}
					candidate := make([]byte, 0, len(data)+len(to))
					candidate = append(candidate, data[:lo]...)
					candidate = append(candidate, to...)
					candidate = append(candidate, data[hi:]...)
					actual, err := html.Parse(bytes.NewReader(candidate))
					if err == nil && sameTree(actual, expected) {
						verified = append(verified, SourcePatch{StartByte: lo, EndByte: hi, Expected: from, Replacement: to})
					}
				}
			}
		}
		offset += len(raw)
	}
	if len(verified) != 1 {
		return fail("no unique verified literal source patch; use semantic preview")
	}
	return verified[0], nil
}
