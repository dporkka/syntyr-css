"use client";
import { useState } from "react";
import { Button } from "@syntyr/react";

export function Counter() {
  const [count, setCount] = useState(0);
  return (
    <Button variant="primary" onClick={() => setCount((n) => n + 1)}>
      Increment {count}
    </Button>
  );
}
