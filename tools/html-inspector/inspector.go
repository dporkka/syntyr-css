package main

import (
	"encoding/json"
	"fmt"
	"io"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"github.com/andybalholm/cascadia"
)

type part struct {
	Tag     string   `json:"tag"`
	Classes []string `json:"classes"`
}
type slot struct {
	part
	Name       string `json:"name"`
	Optional   bool   `json:"optional"`
	Repeatable bool   `json:"repeatable"`
}
type recipe struct {
	ID    string `json:"id"`
	Root  part   `json:"root"`
	Slots []slot `json:"slots"`
}
type catalog struct {
	SchemaVersion int    `json:"schema_version"`
	SourceVersion string `json:"source_version"`
	Components    []struct {
		Name    string   `json:"name"`
		Classes []string `json:"classes"`
	} `json:"components"`
	Recipes []recipe `json:"recipes"`
}

type SlotReport struct {
	Name   string `json:"name"`
	Count  int    `json:"count"`
	Status string `json:"status"`
}
type RecipeReport struct {
	ID    string       `json:"id"`
	Slots []SlotReport `json:"slots"`
}
type Element struct {
	Tag        string         `json:"tag"`
	Classes    []string       `json:"classes"`
	Components []string       `json:"components"`
	Recipes    []RecipeReport `json:"recipes"`
}
type Report struct {
	SchemaVersion int       `json:"schema_version"`
	SourceVersion string    `json:"source_version"`
	Selector      string    `json:"selector"`
	Elements      []Element `json:"elements"`
}

func loadCatalog(r io.Reader) (catalog, error) {
	var c catalog
	d := json.NewDecoder(r)
	if err := d.Decode(&c); err != nil {
		return c, err
	}
	var extra any
	if err := d.Decode(&extra); err != io.EOF {
		return c, fmt.Errorf("catalog must contain exactly one JSON object")
	}
	if c.SchemaVersion != 1 || c.SourceVersion == "" || c.Components == nil || c.Recipes == nil {
		return c, fmt.Errorf("expected version 1 component catalog with source version, components and recipes")
	}
	for _, r := range c.Recipes {
		if r.ID == "" || r.Root.Tag == "" || len(r.Root.Classes) == 0 {
			return c, fmt.Errorf("invalid recipe root: %q", r.ID)
		}
		for _, s := range r.Slots {
			if s.Name == "" || s.Tag == "" || len(s.Classes) == 0 {
				return c, fmt.Errorf("invalid slot in recipe %q", r.ID)
			}
		}
	}
	return c, nil
}

func matches(s *goquery.Selection, p part) bool {
	if goquery.NodeName(s) != p.Tag {
		return false
	}
	for _, c := range p.Classes {
		if !s.HasClass(c) {
			return false
		}
	}
	return true
}

func inert(s *goquery.Selection) bool {
	return goquery.NodeName(s) == "template" || s.ParentsFiltered("template").Length() > 0
}

func recipeReport(root *goquery.Selection, r recipe) RecipeReport {
	out := RecipeReport{ID: r.ID, Slots: []SlotReport{}}
	for _, slot := range r.Slots {
		count := 0
		root.Find("*").Each(func(_ int, candidate *goquery.Selection) {
			if inert(candidate) || !matches(candidate, slot.part) {
				return
			}
			// A nested instance of the same recipe owns its own slots.
			for p := candidate.Parent(); p.Length() > 0 && p.Get(0) != root.Get(0); p = p.Parent() {
				if matches(p, r.Root) {
					return
				}
			}
			if !matches(candidate, r.Root) {
				count++
			}
		})
		status := "ok"
		if count == 0 && !slot.Optional {
			status = "missing"
		}
		if count > 1 && !slot.Repeatable {
			status = "multiple"
		}
		out.Slots = append(out.Slots, SlotReport{Name: slot.Name, Count: count, Status: status})
	}
	return out
}

func inspect(r io.Reader, c catalog, selector string) (Report, error) {
	out := Report{SchemaVersion: 1, SourceVersion: c.SourceVersion, Selector: selector, Elements: []Element{}}
	query := selector
	if query == "" {
		query = "[class]"
	}
	matcher, err := cascadia.Compile(query)
	if err != nil {
		return out, fmt.Errorf("invalid selector: %w", err)
	}
	doc, err := goquery.NewDocumentFromReader(r)
	if err != nil {
		return out, err
	}
	doc.FindMatcher(matcher).Each(func(_ int, s *goquery.Selection) {
		if inert(s) {
			return
		}
		raw, _ := s.Attr("class")
		e := Element{Tag: goquery.NodeName(s), Classes: []string{}, Components: []string{}, Recipes: []RecipeReport{}}
		seen := map[string]bool{}
		for _, class := range strings.Fields(raw) {
			if strings.HasPrefix(class, "syn-") && !seen[class] {
				e.Classes = append(e.Classes, class)
				seen[class] = true
			}
		}
		if selector == "" && len(e.Classes) == 0 {
			return
		}
		for _, comp := range c.Components {
			for _, class := range comp.Classes {
				if seen[class] {
					e.Components = append(e.Components, comp.Name)
					break
				}
			}
		}
		for _, recipe := range c.Recipes {
			if matches(s, recipe.Root) {
				e.Recipes = append(e.Recipes, recipeReport(s, recipe))
			}
		}
		out.Elements = append(out.Elements, e)
	})
	return out, nil
}
