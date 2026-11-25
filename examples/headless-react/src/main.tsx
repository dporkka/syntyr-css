import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "../../../dist/syntyr.core.css";
import "../../../dist/syntyr.recipes.css";
import "../../../integrations/headless/interactions.css";
import "./workspace-reflow.css";

const host = document.getElementById("root");
if (!host) throw new Error("Missing React host");
createRoot(host).render(<StrictMode><App /></StrictMode>);
