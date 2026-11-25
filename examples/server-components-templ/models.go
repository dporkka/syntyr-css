package main

import (
	"net/url"
	"strconv"
	"strings"
	"unicode/utf8"
)

// These application-owned inputs mirror the native HTML contract in ../server-components-go.
type FieldProps struct{ ID, Name, Label, Value, Help, Error string }
type NoticeProps struct {
	Message string
	Danger  bool
}
type ButtonProps struct {
	Label           string
	Primary, Submit bool
}
type Record struct{ Title, Description string }
type PaginationProps struct {
	Page, Total      int
	PrevURL, NextURL string
}
type PageData struct {
	ShowResults  bool
	Query        FieldProps
	Notice       NoticeProps
	SearchButton ButtonProps
	Records      []Record
	Pager        PaginationProps
}
type pageResult struct {
	Data   PageData
	Status int
}

var resources = []Record{
	{"Billing", "Invoices & statements"},
	{"CRM", "Accounts & contacts"},
	{"Inventory", "Assets & availability"},
	{"Operations", "Work orders and inspections"},
	{"Proposals", "Contracts and approvals"},
	{"Reporting", "Revenue and campaign summaries"},
}

func buttonClass(primary bool) string {
	if primary {
		return "syn-button syn-button--primary"
	}
	return "syn-button"
}

func paginationLabel(p PaginationProps) string {
	return "Page " + strconv.Itoa(p.Page) + " of " + strconv.Itoa(p.Total)
}

func pageHref(query string, page int) string {
	vals := url.Values{}
	if query != "" {
		vals.Set("q", query)
	}
	if page > 1 {
		vals.Set("page", strconv.Itoa(page))
	}
	if len(vals) == 0 {
		return "/"
	}
	return "/?" + vals.Encode()
}

func buildPage(query, pageText string) pageResult {
	const pageSize = 2
	const maxQueryRunes = 80
	field := FieldProps{ID: "resource-query", Name: "q", Label: "Find a resource", Value: query, Help: "Search titles and descriptions."}
	status := 200
	if utf8.RuneCountInString(field.Value) > maxQueryRunes {
		field.Value = string([]rune(field.Value)[:maxQueryRunes])
		field.Error = "Search must be at most 80 characters."
		status = 400
		return pageResult{Status: status, Data: PageData{
			Query:        field,
			Notice:       NoticeProps{Message: "Correct the search field and try again.", Danger: true},
			SearchButton: ButtonProps{Label: "Search", Primary: true, Submit: true},
		}}
	}
	matches := make([]Record, 0, len(resources))
	needle := strings.ToLower(strings.TrimSpace(field.Value))
	for _, record := range resources {
		if needle == "" || strings.Contains(strings.ToLower(record.Title+" "+record.Description), needle) {
			matches = append(matches, record)
		}
	}
	total := (len(matches) + pageSize - 1) / pageSize
	if total == 0 {
		total = 1
	}
	page := 1
	invalidPage := false
	if pageText != "" {
		parsed, err := strconv.Atoi(pageText)
		invalidPage = err != nil || parsed < 1 || parsed > total
		if !invalidPage {
			page = parsed
		} else {
			status = 400
		}
	}
	start := (page - 1) * pageSize
	end := start + pageSize
	if end > len(matches) {
		end = len(matches)
	}
	pager := PaginationProps{Page: page, Total: total}
	if page > 1 {
		pager.PrevURL = pageHref(field.Value, page-1)
	}
	if page < total {
		pager.NextURL = pageHref(field.Value, page+1)
	}
	alert := NoticeProps{Message: "Filtered on the server. No browser JavaScript required."}
	if invalidPage {
		alert = NoticeProps{Message: "Page number is invalid for these results.", Danger: true}
	}
	return pageResult{Status: status, Data: PageData{
		ShowResults: !invalidPage,
		Query:       field, Notice: alert, SearchButton: ButtonProps{Label: "Search", Primary: true, Submit: true},
		Records: matches[start:end], Pager: pager,
	}}
}
