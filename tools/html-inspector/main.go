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
	fs.Usage = func() {
		fmt.Fprintln(stderr, "Usage: syntyr-html-inspect [--catalog FILE] [--selector CSS] [--strict-recipes] [--limit N] HTML_FILE|-")
		fs.PrintDefaults()
	}
	if err := fs.Parse(args); err != nil {
		return err
	}
	if fs.NArg() != 1 {
		return fmt.Errorf("expected one local HTML file")
	}
	if *strict && *limit != 0 {
		return fmt.Errorf("strict recipe validation requires an unlimited report")
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
	report, err := inspectLimited(bytes.NewReader(data), c, *selector, *limit)
	if err != nil {
		return err
	}
	enc := json.NewEncoder(stdout)
	enc.SetIndent("", "  ")
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
