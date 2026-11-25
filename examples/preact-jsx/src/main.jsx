import "@syntyr/css/core.css";
import { render } from "preact";
import { App } from "./App.jsx";

const root = document.getElementById("app");
if (!root) throw new Error("Missing #app");
render(<App />, root);
