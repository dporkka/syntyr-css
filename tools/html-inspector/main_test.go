package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestCLIWithCanonicalCatalog(t *testing.T) {
	var out, stderr bytes.Buffer
	err := run([]string{"--catalog", "../../metadata/components.json", "--selector", ".syn-app-shell", "../../examples/operations-console.html"}, &out, &stderr)
	if err != nil {
		t.Fatal(err)
	}
	var report Report
	if err = json.Unmarshal(out.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if len(report.Elements) != 1 || len(report.Elements[0].Recipes) != 1 || report.Elements[0].Recipes[0].ID != "app-shell" {
		t.Fatalf("%+v", report)
	}
	for _, s := range report.Elements[0].Recipes[0].Slots {
		if s.Status != "ok" {
			t.Fatalf("%+v", s)
		}
	}
}

func TestCLIReportsMissingSlotWithoutFailing(t *testing.T) {
	dir := t.TempDir()
	file := filepath.Join(dir, "fragment.html")
	if err := os.WriteFile(file, []byte(`<div class="syn-app-shell"></div>`), 0600); err != nil {
		t.Fatal(err)
	}
	var out, stderr bytes.Buffer
	if err := run([]string{"--catalog", "../../metadata/components.json", file}, &out, &stderr); err != nil {
		t.Fatal(err)
	}
	var report Report
	if err := json.Unmarshal(out.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if report.Elements[0].Recipes[0].Slots[0].Status != "missing" {
		t.Fatalf("%+v", report)
	}
}

func TestCLIRejectsOversizedHTML(t *testing.T) {
	file := filepath.Join(t.TempDir(), "large.html")
	if err := os.WriteFile(file, make([]byte, maxInputBytes+1), 0600); err != nil {
		t.Fatal(err)
	}
	var out, stderr bytes.Buffer
	if err := run([]string{"--catalog", "../../metadata/components.json", file}, &out, &stderr); err == nil || out.Len() != 0 {
		t.Fatal("oversized HTML accepted")
	}
}

func TestCLIPreviewLeavesSourceUnchanged(t *testing.T) {
	html := `<button class="syn-button syn-button--primary">Save</button>`
	path := filepath.Join(t.TempDir(), "source.html")
	if err := os.WriteFile(path, []byte(html), 0600); err != nil {
		t.Fatal(err)
	}
	var out, stderr bytes.Buffer
	args := []string{"--catalog", "../../metadata/components.json", "--selector", "button"}
	if err := run(append(append([]string{}, args...), path), &out, &stderr); err != nil {
		t.Fatal(err)
	}
	var r Report
	if err := json.Unmarshal(out.Bytes(), &r); err != nil {
		t.Fatal(err)
	}
	out.Reset()
	args = append(args, "--document-sha256", r.DocumentSHA256, "--element-id", r.Elements[0].ElementID, "--preview-from", "syn-button--primary", "--preview-to", "syn-button--outline", path)
	if err := run(args, &out, &stderr); err != nil {
		t.Fatal(err)
	}
	var p VariantPreview
	if err := json.Unmarshal(out.Bytes(), &p); err != nil {
		t.Fatal(err)
	}
	if p.After != "syn-button syn-button--outline" || !p.PreviewOnly {
		t.Fatalf("%+v", p)
	}
	actual, err := os.ReadFile(path)
	if err != nil || string(actual) != html {
		t.Fatal("source modified")
	}
}
func TestCLIStrictRecipesReportsViolationsAndFails(t *testing.T) {
	file := filepath.Join(t.TempDir(), "fragment.html")
	if err := os.WriteFile(file, []byte(`<div class="syn-app-shell"></div>`), 0600); err != nil {
		t.Fatal(err)
	}
	var out, stderr bytes.Buffer
	err := run([]string{"--catalog", "../../metadata/components.json", "--strict-recipes", file}, &out, &stderr)
	if err == nil {
		t.Fatal("strict mode accepted missing slots")
	}
	var report Report
	if err := json.Unmarshal(out.Bytes(), &report); err != nil {
		t.Fatalf("strict mode must emit JSON: %v", err)
	}
	if len(report.Elements) != 1 || report.Elements[0].Recipes[0].Slots[0].Status != "missing" {
		t.Fatalf("%+v", report)
	}
}
func TestCLIStrictRecipesAcceptsValidRecipe(t *testing.T) {
	var out, stderr bytes.Buffer
	if err := run([]string{"--catalog", "../../metadata/components.json", "--strict-recipes", "../../examples/operations-console.html"}, &out, &stderr); err != nil {
		t.Fatal(err)
	}
}

func TestCLIStrictRecipesRejectsTruncatedReport(t *testing.T) {
	var out, stderr bytes.Buffer
	err := run([]string{"--catalog", "../../metadata/components.json", "--strict-recipes", "--limit", "1", "../../examples/operations-console.html"}, &out, &stderr)
	if err == nil || out.Len() != 0 {
		t.Fatal("strict validation must reject output truncation")
	}
}

func TestCLIStrictRecipesRejectsPreviewModes(t *testing.T) {
	for _, args := range [][]string{
		{"--strict-recipes", "--preview-from", "syn-button--primary", "-"},
		{"--strict-recipes", "--verify-patches", "[]", "-"},
	} {
		var out, stderr bytes.Buffer
		err := runWithInput(args, bytes.NewBufferString("<button></button>"), &out, &stderr)
		if err == nil || !strings.Contains(err.Error(), "strict recipe validation") || out.Len() != 0 {
			t.Fatalf("expected strict flag conflict, got %v", err)
		}
	}
}
