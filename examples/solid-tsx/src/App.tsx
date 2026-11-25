import { createSignal } from "solid-js";

export function App() {
  const [count, setCount] = createSignal(0);
  return (
    <main class="syn-root" data-syn-theme="studio" style={{ padding: "2rem" }}>
      <section class="syn-panel" aria-labelledby="solid-title">
        <span class="syn-badge">Solid / TSX</span>
        <h1 class="syn-heading" id="solid-title">Operations</h1>
        <p>Native TSX, Syntyr classes, no React wrapper or Syntyr JavaScript.</p>
        <label class="syn-label" for="solid-project">Project</label>
        <input class="syn-input" id="solid-project" name="project" placeholder="Project name" />
        <button class="syn-button syn-button--primary" type="button"
          onClick={() => setCount((current) => current + 1)}>
          Count: {count()}
        </button>
      </section>
    </main>
  );
}
