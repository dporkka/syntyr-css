# Syntyr + Tailwind CSS v4 (opt-in)

Run against the source-tree CSS package:

```sh
cd examples/tailwind-v4
npm install
npm run build
python3 -m http.server 8000
```

Open http://localhost:8000. The generated dist/app.css is ignored.
Nested themes resolve at runtime; Tailwind processes @theme inline at build time.
Syntyr adds no Tailwind runtime dependency.

Run `npm run check:native-palettes` after installation to compile the optional
mobile palette utilities with Tailwind v4. This validates utility generation,
not NativeWind/Uniwind Metro or native device rendering.
