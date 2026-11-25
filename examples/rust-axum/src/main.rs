//! A deliberately small, read-only SaaS dashboard. No Syntyr Rust crate,
//! runtime JavaScript, CSS compiler, external asset host, or data store.
use askama::Template;
use axum::{
    extract::Query,
    http::{header, StatusCode},
    response::{Html, IntoResponse, Response},
    routing::get,
    Router,
};
use serde::Deserialize;

const CORE_CSS: &str = include_str!("../../../dist/syntyr.core.css");

#[derive(Debug, Deserialize, Default)]
struct Search {
    q: Option<String>,
}

#[derive(Clone)]
struct Project {
    name: &'static str,
    owner: &'static str,
    status: &'static str,
}

const PROJECTS: [Project; 4] = [
    Project {
        name: "Customer portal",
        owner: "Morgan",
        status: "Active",
    },
    Project {
        name: "Billing",
        owner: "Avery",
        status: "Planning",
    },
    Project {
        name: "Operations",
        owner: "Taylor",
        status: "Active",
    },
    Project {
        name: "Reporting",
        owner: "Jordan",
        status: "Review",
    },
];

#[derive(Template)]
#[template(path = "dashboard.html")]
struct Dashboard {
    query: String,
    has_error: bool,
    error: &'static str,
    projects: Vec<Project>,
    result_count: usize,
}

fn build_dashboard(raw: Option<&str>) -> (StatusCode, Dashboard) {
    let query = raw.unwrap_or_default().trim().to_owned();
    // Limit Unicode scalar values rather than UTF-8 bytes for a predictable UX.
    let invalid = query.chars().count() > 40;
    let projects: Vec<_> = if invalid {
        Vec::new()
    } else {
        PROJECTS
            .iter()
            .filter(|project| {
                query.is_empty()
                    || project.name.to_lowercase().contains(&query.to_lowercase())
                    || project.owner.to_lowercase().contains(&query.to_lowercase())
            })
            .cloned()
            .collect()
    };
    let result_count = projects.len();
    (
        if invalid {
            StatusCode::UNPROCESSABLE_ENTITY
        } else {
            StatusCode::OK
        },
        Dashboard {
            query,
            has_error: invalid,
            error: if invalid {
                "Search must be 40 characters or fewer."
            } else {
                ""
            },
            projects,
            result_count,
        },
    )
}

async fn index(Query(search): Query<Search>) -> Response {
    let (status, template) = build_dashboard(search.q.as_deref());
    match template.render() {
        Ok(body) => (status, Html(body)).into_response(),
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    }
}

async fn css() -> impl IntoResponse {
    (
        [
            (header::CONTENT_TYPE, "text/css; charset=utf-8"),
            (header::CACHE_CONTROL, "public, max-age=3600"),
        ],
        CORE_CSS,
    )
}

fn router() -> Router {
    Router::new()
        .route("/", get(index))
        .route("/assets/syntyr.core.css", get(css))
}

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(3000);
    let listener = tokio::net::TcpListener::bind(("127.0.0.1", port)).await?;
    println!("Syntyr Askama/Axum starter: http://127.0.0.1:{port}");
    axum::serve(listener, router()).await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_search_lists_all_projects() {
        let (status, dashboard) = build_dashboard(None);
        assert_eq!(status, StatusCode::OK);
        assert_eq!(dashboard.result_count, 4);
    }

    #[test]
    fn searches_trim_and_match_case_insensitively() {
        let (status, dashboard) = build_dashboard(Some("  mOrGaN "));
        assert_eq!(status, StatusCode::OK);
        assert_eq!(dashboard.result_count, 1);
        assert_eq!(dashboard.projects[0].name, "Customer portal");
    }

    #[test]
    fn overlong_search_returns_validation_error() {
        let (status, dashboard) = build_dashboard(Some(&"é".repeat(41)));
        assert_eq!(status, StatusCode::UNPROCESSABLE_ENTITY);
        assert!(dashboard.has_error);
        let html = dashboard.render().unwrap();
        assert!(html.contains("aria-invalid=\"true\""));
        assert!(html.contains("id=\"search-error\""));
    }

    #[test]
    fn askama_html_escapes_untrusted_search_input() {
        let (_, dashboard) = build_dashboard(Some("<script>alert(1)</script>"));
        let html = dashboard.render().unwrap();
        assert!(!html.contains("<script>"));
        assert!(
            html.contains("script") && html.contains("&"),
            "untrusted input should be HTML-escaped"
        );
    }

    #[test]
    fn unknown_query_renders_accessible_empty_state() {
        let (_, dashboard) = build_dashboard(Some("no such project"));
        assert_eq!(dashboard.result_count, 0);
        let html = dashboard.render().unwrap();
        assert!(html.contains("No matching projects"));
        assert!(html.contains("<caption>"));
    }

    #[test]
    fn embedded_syntyr_has_root_scope() {
        assert!(CORE_CSS.contains(".syn-root"));
        assert!(CORE_CSS.contains(".syn-button"));
    }
}
