import "@syntyr/css/core.css";
import "@syntyr/css/recipes.css";
import type { ReactNode } from "react";
import { SyntyrRoot } from "@syntyr/react";

export const metadata = { title: "Syntyr Next.js adoption fixture" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SyntyrRoot theme="studio" style={{ padding: "2rem" }}>
          {children}
        </SyntyrRoot>
      </body>
    </html>
  );
}
