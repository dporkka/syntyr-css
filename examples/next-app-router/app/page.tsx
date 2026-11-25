import { Badge, Card, Input } from "@syntyr/react";
import { Counter } from "./counter";

export default function Page() {
  return (
    <main>
      <Card>
        <Badge>Server Component</Badge>
        <h1 className="syn-heading">Next.js operations</h1>
        <p>Rendered on the server using the standard CSS contract.</p>
        <label className="syn-label" htmlFor="account">Account</label>
        <Input id="account" name="account" placeholder="Account name" />
        <Counter />
      </Card>
    </main>
  );
}
