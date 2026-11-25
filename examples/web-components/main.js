import "./status-toggle.js";

document.addEventListener("syn-demo-native-status-change", (event) => {
  const output = document.querySelector("#native-event-output");
  if (output) output.textContent =
    `${event.detail.service}: ${event.detail.online ? "online" : "offline"}`;
});
