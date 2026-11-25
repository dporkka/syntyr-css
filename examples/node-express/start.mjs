import { app } from "./server.mjs";

const port = Number(process.env.PORT || 3000);
app.listen(port, "127.0.0.1", () => {
  console.log("Syntyr Express demo on http://127.0.0.1:" + port + "/search");
});
