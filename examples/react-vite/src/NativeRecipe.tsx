/** Copy-owned TSX recipe: plain semantic HTML and Syntyr CSS, no adapter. */
export function NativeRecipe({
  count,
  onIncrement,
}: {
  count: number;
  onIncrement: () => void;
}) {
  return (
    <section className="syn-panel" aria-labelledby="react-title">
      <span className="syn-badge">React / TSX</span>
      <h1 className="syn-heading" id="react-title">Operations</h1>
      <p>Native TSX styled by Syntyr CSS; React owns the counter behavior.</p>
      <label className="syn-label" htmlFor="react-project">Project</label>
      <input className="syn-input" id="react-project" name="project" placeholder="Project name" />
      <button className="syn-button syn-button--primary" type="button" onClick={onIncrement}>
        Count: {count}
      </button>
    </section>
  );
}
