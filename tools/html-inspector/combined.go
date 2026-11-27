package main

import (
	"bytes"
	"fmt"
	"sort"

	"github.com/PuerkitoBio/goquery"
	"golang.org/x/net/html"
)

type CombinedOperation struct {
	ElementID string      `json:"element_id"`
	Selector  string      `json:"selector"`
	From      string      `json:"from"`
	To        string      `json:"to"`
	Patch     SourcePatch `json:"patch"`
}

func verifyCombined(data []byte, c catalog, digest string, ops []CombinedOperation) (string, error) {
	if len(data) > maxPatchInput || digest != documentDigest(data) || len(ops) < 1 || len(ops) > 8 {
		return "", fmt.Errorf("invalid combined proof input")
	}
	doc, err := goquery.NewDocumentFromReader(bytes.NewReader(data))
	if err != nil {
		return "", err
	}
	ids := elementIDs(doc)
	nodes := map[string]*html.Node{}
	for node, id := range ids {
		nodes[id] = node
	}
	seen := map[string]bool{}
	patches := make([]SourcePatch, 0, len(ops))
	for _, op := range ops {
		if seen[op.ElementID] {
			return "", fmt.Errorf("duplicate target")
		}
		seen[op.ElementID] = true
		preview, err := previewVariant(data, c, op.Selector, digest, op.ElementID, op.From, op.To)
		if err != nil {
			return "", err
		}
		p := op.Patch
		if p.StartByte < 0 || p.EndByte <= p.StartByte || p.EndByte > len(data) || p.Expected != op.From || p.Replacement != op.To || string(data[p.StartByte:p.EndByte]) != op.From {
			return "", fmt.Errorf("invalid patch precondition")
		}
		node := nodes[op.ElementID]
		if node == nil {
			return "", fmt.Errorf("missing target")
		}
		for i := range node.Attr {
			if node.Attr[i].Key == "class" && node.Attr[i].Namespace == "" {
				node.Attr[i].Val = preview.After
				break
			}
		}
		patches = append(patches, p)
	}
	sort.Slice(patches, func(i, j int) bool { return patches[i].StartByte < patches[j].StartByte })
	for i := 1; i < len(patches); i++ {
		if patches[i-1].EndByte > patches[i].StartByte {
			return "", fmt.Errorf("overlapping patches")
		}
	}
	candidate := bytes.Clone(data)
	for i := len(patches) - 1; i >= 0; i-- {
		p := patches[i]
		next := make([]byte, 0, len(candidate)+len(p.Replacement))
		next = append(next, candidate[:p.StartByte]...)
		next = append(next, p.Replacement...)
		next = append(next, candidate[p.EndByte:]...)
		candidate = next
	}
	actual, err := html.Parse(bytes.NewReader(candidate))
	if err != nil || !sameTree(actual, doc.Get(0)) {
		return "", fmt.Errorf("combined DOM differs from expected mutation")
	}
	return documentDigest(candidate), nil
}
