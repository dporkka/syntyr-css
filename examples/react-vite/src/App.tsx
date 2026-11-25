import { useState } from "react";
import { SyntyrRoot } from "@syntyr/react";
import { NativeRecipe } from "./NativeRecipe.js";

export function App() {
  const [value, setValue] = useState(0);
  return (
    <SyntyrRoot theme="studio" style={{ padding: "2rem" }}>
      <main>
        <NativeRecipe count={value} onIncrement={() => setValue((n) => n + 1)} />
      </main>
    </SyntyrRoot>
  );
}
