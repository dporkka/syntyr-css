import { useState } from "preact/hooks";

export function App() {
  const [count, setCount] = useState(0);
  return (
    <main class="syn-root" data-syn-theme="studio" style={{ padding: "2rem" }}>
      <section class="syn-panel" aria-labelledby="preact-title">
        <span class="syn-badge">Preact / JSX</span>
        <h1 class="syn-heading" id="preact-title">Operations</h1>
        <p>Native JSX, Syntyr classes, no React wrapper or Syntyr JavaScript.</p>
        <label class="syn-label" for="preact-project">Project</label>
        <input class="syn-input" id="preact-project" name="project" placeholder="Project name" />
        <button class="syn-button syn-button--primary" type="button"
          onClick={() => setCount((current) => current + 1)}>
          Count: {count}
        </button>
      </section>
    </main>
  );
}
