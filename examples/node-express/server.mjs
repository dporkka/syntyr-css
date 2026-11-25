import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Resolve the installed, versioned package asset. No Syntyr middleware or
// JavaScript is necessary; the host backend owns its HTTP/static asset policy.
const cssFile = fileURLToPath(import.meta.resolve("@syntyr/css/core.css"));
const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const app = express();

app.disable("x-powered-by");
app.set("views", path.join(__dirname, "views"));
app.set("view engine", "ejs");
app.use("/css", express.static(path.dirname(cssFile), {
  maxAge: "1h",
  index: false,
  fallthrough: false,
}));

const accounts = ["Northside Media", "Metro Displays", "Regional Screens"];
app.get("/", (_request, response) => response.redirect(302, "/search"));
app.get("/search", (request, response) => {
  const query = typeof request.query.q === "string" ? request.query.q.slice(0, 120) : "";
  const matches = accounts.filter((name) => name.toLowerCase().includes(query.toLowerCase()));
  response.render("index", { query, matches });
});
