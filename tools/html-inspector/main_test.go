package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
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
