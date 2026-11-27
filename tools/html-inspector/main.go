package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
)

const maxInputBytes = 8 << 20

var errRecipeViolations = errors.New("recipe slot violations found")

func run(args []string, stdout, stderr io.Writer) error {
	return runWithInput(args, os.Stdin, stdout, stderr)
}

func runWithInput(args []string, stdin io.Reader, stdout, stderr io.Writer) error {
	fs := flag.NewFlagSet("syntyr-html-inspect", flag.ContinueOnError)
	fs.SetOutput(stderr)
	catalogPath := fs.String("catalog", "metadata/components.json", "path to Syntyr component catalog")
	strict := fs.Bool("strict-recipes", false, "fail on reported recipe slot violations after emitting JSON")
	selector := fs.String("selector", "", "CSS selector (default: elements with syn-* classes)")
	limit := fs.Int("limit", 0, "maximum returned elements; zero means unlimited")
	from := fs.String("preview-from", "", "original curated modifier class")
	to := fs.String("preview-to", "", "replacement curated modifier class")
	digest := fs.String("document-sha256", "", "digest from inspection")
	id := fs.String("element-id", "", "element ID from inspection")
	patch := fs.Bool("source-patch", false, "include an exact verified source byte patch in variant preview")
	verify := fs.String("verify-patches", "", "JSON array of bounded source patch operations for combined DOM proof")
	fs.Usage = func() {
		fmt.Fprintln(stderr, "Usage: syntyr-html-inspect [--catalog FILE] [--selector CSS] [--strict-recipes] HTML_FILE|-")
		fs.PrintDefaults()
	}
	if err := fs.Parse(args); err != nil {
		return err
	}
	if fs.NArg() != 1 {
		return fmt.Errorf("expected one local HTML file")
	}
	if *strict && (*limit != 0 || *patch || *from != "" || *to != "" || *digest != "" || *id != "" || *verify != "") {
		return fmt.Errorf("strict recipe validation requires unlimited inspection, not preview or verification")
	}
	if *limit < 0 {
		return fmt.Errorf("limit must be nonnegative")
	}
	cfile, err := os.Open(*catalogPath)
	if err != nil {
		return err
	}
	defer cfile.Close()
	c, err := loadCatalog(cfile)
	if err != nil {
		return fmt.Errorf("catalog: %w", err)
	}
	var input io.Reader = stdin
	if fs.Arg(0) != "-" {
		f, err := os.Open(fs.Arg(0))
		if err != nil {
			return err
		}
		defer f.Close()
		input = f
	}
	data, err := io.ReadAll(io.LimitReader(input, maxInputBytes+1))
	if err != nil {
		return err
	}
	if len(data) > maxInputBytes {
		return fmt.Errorf("HTML exceeds 8 MiB input limit")
	}
	enc := json.NewEncoder(stdout)
	enc.SetIndent("", "  ")
	if *verify != "" {
		if *patch || *from != "" || *to != "" || *id != "" || *selector != "" || *limit != 0 || len(*verify) > 16384 {
			return fmt.Errorf("invalid combined verification flags")
		}
		var ops []CombinedOperation
		decoder := json.NewDecoder(bytes.NewBufferString(*verify))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&ops); err != nil {
			return err
		}
		var extra any
		if err := decoder.Decode(&extra); err != io.EOF {
			return fmt.Errorf("unexpected extra verification data")
		}
		result, err := verifyCombined(data, c, *digest, ops)
		if err != nil {
			return err
		}
		return enc.Encode(map[string]any{"schema_version": 1, "source_version": c.SourceVersion, "document_sha256": *digest, "result_sha256": result, "combined_dom_verified": true})
	}
	if *patch || *from != "" || *to != "" || *digest != "" || *id != "" {
		if *limit != 0 {
			return fmt.Errorf("limit is not applicable to preview")
		}
		plan, err := previewVariant(data, c, *selector, *digest, *id, *from, *to)
		if err != nil {
			return err
		}
		if *patch {
			p, err := sourcePatch(data, plan, *from, *to)
			if err != nil {
				return err
			}
			plan.SourcePatch = &p
		}
		return enc.Encode(plan)
	}
	report, err := inspectLimited(bytes.NewReader(data), c, *selector, *limit)
	if err != nil {
		return err
	}
	if err := enc.Encode(report); err != nil {
		return err
	}
	if *strict {
		for _, element := range report.Elements {
			for _, recipe := range element.Recipes {
				for _, slot := range recipe.Slots {
					if slot.Status != "ok" {
						return errRecipeViolations
					}
				}
			}
		}
	}
	return nil
}
func main() {
	if err := run(os.Args[1:], os.Stdout, os.Stderr); err != nil {
		if err == flag.ErrHelp {
			return
		}
		fmt.Fprintln(os.Stderr, err)
		if errors.Is(err, errRecipeViolations) {
			os.Exit(1)
		}
		os.Exit(2)
	}
}
