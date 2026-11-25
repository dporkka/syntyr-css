import "@syntyr/css/core.css";
import { render } from "solid-js/web";
import { App } from "./App";

const root = document.getElementById("app");
if (!root) throw new Error("Missing #app");
render(() => <App />, root);
