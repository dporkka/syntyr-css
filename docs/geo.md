# Syntyr Geo — renderer-neutral geospatial interface styles

**Status:** experimental and unreleased. The MIT-licensed `syntyr.geo.css` module styles geospatial application **chrome**: map workspaces, filters, layers, marker hit targets, selected states, clusters, legends, callouts, scale bars and attribution. No JavaScript, tiles, mapping SDK, fonts, or network assets are included in Syntyr Geo. Load `syntyr.core.css` first.

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.geo.css">
```

Or, in a package-manager application consuming the **unpublished** alpha.5 candidate, import `@syntyr/css/geo.css`. The `syntyr.all.css` bundle already contains Geo; **do not load both**. Neither `syntyr.core.css` nor `syntyr.viz.css` includes it.

**[Open the synthetic, offline Geo demo](../examples/geo.html)**. It is a Schematic illustration, **Not to scale**, with fictional records, no tile provider or API keys, and disabled zoom controls. It is not a map renderer.

### Optional Python standard-library operations demo (repository source)

The [runnable Geo operations server](https://github.com/dporkka/syntyr-css/blob/main/examples/geo_operations_server.py) illustrates **actual server-owned GET filtering and selection** without JavaScript or additional CSS APIs. From a repository checkout run:

```sh
python3 examples/geo_operations_server.py --port 8765
```

Open `http://127.0.0.1:8765/`. It composes the existing `syntyr.core.css`, `syntyr.recipes.css` and `syntyr.geo.css` files into a responsive inventory search, accessible results/inspector, and fictional map schematic. Map coordinates are **illustrative pixel percentages**, not geographic coordinates. The Python file is a **source-only reference** and is not included in the distributable release ZIP. The server binds to localhost and contains fictional in-memory records; it has no credentials, accounts, tenant isolation, authorization, persistence or booking capability. Never expose this sample on a public interface as a production service.

### District drill-down and selection: interaction contract

The optional server example uses **real, browser-native GET navigation** for a small fictional district facet. The new `district` select and district links share search, status and format filters. District counts are computed after those other filters but before choosing a district, so the number on each link represents the results it would show. There is no JavaScript filtering or hidden application state.

| User action | Native UI and URL state | What the server must guarantee |
| --- | --- | --- |
| Apply filters | Labeled `search` input and `select` controls, `method="get"` | Filter the **list and the schematic markers** from the same result set, recompute summary/counts and prevent stale selected records |
| Browse a district | Named `nav` of ordinary links with one `aria-current="page"` | Retain search, status and format; reset selection before choosing the first visible item |
| Select a map marker or an asset | Link with preserved filters and `selected=ID#selection` | Inspect only an asset that belongs to the currently filtered district; never reveal an out-of-scope record |
| Find a map marker from a record | `#map-marker-ID` points to a real named anchor | Preserve a keyboard-reachable target even with JavaScript disabled; do **not** pretend to center a real map camera |
| No matching records | Plain-text status with no markers or inspector | Clear stale selection and display an actionable filter-reset path |

This contract is **read-only demonstration behavior**, not tenant authorization. The district names and percentages are fictional, not geographic boundaries. A production application must validate parameters and permissions at the data-access layer, rather than treating filtered HTML or the marker list as an access-control boundary. Do not use the diagram's percentage coordinates to simulate real GIS geography.

Maintainers can optionally verify Chromium/Firefox native GET interaction, district navigation, 320px reflow, enlarged text, RTL markers and forced colors with `node tests/geo_operations_server_browser.cjs` after installing Playwright **outside** the Syntyr runtime. The script starts and shuts down the localhost Python server automatically. This does not replace manual screen-reader or real browser-zoom review.

## The boundary: cartographic behavior is an application concern

**Syntyr does not** calculate geographic coordinates, distances, bearings, geodesics, clustering, projections, antimeridian handling, routing or point-in-polygon queries. It cannot fetch or display basemap data, style vector tiles, perform hit testing, handle map keyboard navigation, or ensure geospatial measurement accuracy. Supply your own GIS data, map engine, and attribution. Syntyr only styles HTML around the actual map.

For interactive maps, integrate an engine such as [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) (vector tiles / WebGL), [Leaflet](https://leafletjs.com/reference) (lightweight tiled/DOM maps), or [OpenLayers](https://openlayers.org/) (specialized GIS interactions and projections). They are **application dependencies**, not dependencies of Syntyr. Engine-native attribution and copyright/license requirements still apply; never remove provider credits. A decorative CSS attribution surface cannot replace legally required renderer attribution.

Choose and disclose the projection and coordinate reference system that your data needs (for example WGS 84 longitude/latitude for position inputs); do not assume a visual pixel distance equals a ground distance. Compute scale from the actual renderer viewport, latitude and zoom. Only set `data-syn-measured="true"` on `.syn-geo-scale` when the application has supplied a truthful measured label and bar length. Static examples deliberately say “Not to scale.”

## A map-ready, responsive shell

```html
<section class="syn-root syn-geo-shell" data-syn-theme="studio">
  <div class="syn-geo-workspace">
    <aside class="syn-geo-sidebar" aria-labelledby="locations-title">
      <h2 id="locations-title">Locations</h2>
      <ul class="syn-geo-data-list">
        <li><a href="#location-1">Site M-12 — operational</a></li>
      </ul>
    </aside>

    <div class="syn-geo-viewport" role="region"
         aria-label="Interactive site map; location details are also in the list">
      <div id="site-map" class="syn-geo-map"></div>
      <div class="syn-geo-overlay">
        <!-- Optional app-owned, functional controls and legend go here. -->
      </div>
    </div>
  </div>
</section>
```

The map mount fills the viewport, while `.syn-geo-overlay` lets pointer events pass through to the renderer except on Syntyr controls, legends and other interactive children. The workspace uses a **named container query** (`syn-geo`), so it stacks at narrow *container* sizes, including in a split dashboard. Set `--syn-geo-height`, `--syn-geo-compact-height` and `--syn-geo-sidebar-width` on an ancestor to customize its dimensions.

### Markers: use the renderer to position them

`.syn-geo-marker` styles a 44 × 44 CSS-pixel target with a smaller visible glyph. With MapLibre, provide a real native `button` to `new maplibregl.Marker({ element: button })`, then set the exact `LngLat` using `.setLngLat([longitude, latitude]).addTo(map)`. MapLibre owns the marker's geographic positioning; **do not place engine-managed marker elements inside `.syn-geo-marker-layer`**.

The pure HTML demo instead places links within `.syn-geo-marker-layer`; only those children use `--syn-geo-x` and `--syn-geo-y` for *diagram* coordinates, not GIS coordinates. These CSS percentages are expressly not a geographic coordinate API.

Use `data-syn-geo-kind="route"` for square markers or `"zone"` for rotated-square markers; ordinary sites remain round. `data-syn-selected="true"` and `aria-current="location"` provide a visible selection ring. `.syn-geo-cluster` styles an already-computed cluster count; **Syntyr never computes clustering**. An app must wire marker activation and popups, synchronize selection with the detail panel, and support keyboard navigation.

### Map controls and overlays

- `.syn-geo-controls`, `.syn-geo-control-group`, `.syn-geo-control` style the application's real `button` controls. A displayed control must work: wire zoom/pan to the map SDK, otherwise disable it.
- `.syn-geo-bottom`, `.syn-geo-legend`, `.syn-geo-legend-list`, `.syn-geo-swatch` style legends for points, routes, and zones. Always include text labels; swatch shape must not be the only source of meaning.
- `.syn-geo-callout` styles the body of an engine-positioned popup. Use safe DOM APIs and text nodes for untrusted feature labels instead of passing unsafe strings into HTML.
- `.syn-geo-scale` presents a scale label. A measured bar only appears for `data-syn-measured="true"` and a renderer-provided `--syn-geo-scale-length`.
- `.syn-geo-attribution` is a surface treatment for attribution you supply, not a replacement for engine-provided credits.
- `.syn-geo-layer-list` styles labeled checkboxes; connect state to the renderer's visible layer set. Checking a box alone does not change map data.
- `.syn-geo-data-list` provides a navigable, semantic fallback for locations and map features.

MapLibre and Leaflet already offer their own zoom, scale and attribution controls. Prefer their functional native versions instead of overlaying duplicate, inert Syntyr controls. Avoid covering copyright or the map's navigation affordances.

## Theming and accessibility

All seven Syntyr palettes resolve the nested tokens `--syn-geo-land`, `--syn-geo-water`, `--syn-geo-road`, `--syn-geo-parcel`, `--syn-geo-point`, `--syn-geo-route` and `--syn-geo-zone`, as well as `--syn-geo-floating`. These are UI/documentation defaults, **not** standardized GIS symbology, hazard categories or validated cartographic color scales. In a real map, assign purpose-specific and contrast-checked symbology to rendered geospatial layers.

For screen reader access, keep the meaningful asset list, labels, live states and a real HTML table or equivalent structured alternative **outside** the map canvas. Give every interactive marker an accessible name, make popup actions usable via keyboard, show an explicit focus ring, and announce state changes where appropriate. SVG diagrams used only as illustration may be `aria-hidden="true"` when the same information exists in text. Do not rely on hue alone for status or selection.

Touch targets are at least 44 CSS pixels in the provided controls and markers. Reflow should be audited at 320px and 400% zoom; verify that map overlays do not obscure attribution or details. Forced-colors users get native system-color surfaces and selected-marker outlines. Reduced-motion settings should also be respected by the **map renderer**, including camera transitions and animated geospatial layers.

## Product fit

Geo deliberately stays in its own CSS module rather than bloating core. Use it for OOH asset inventory maps, real-estate site selection, logistics fleet screens, field operations, municipal dashboards, parcel analysis and geospatial intelligence consoles. Any paid Syntyr Pro templates can compose this free MIT foundation while keeping premium implementation, integrations and domain-specific workflows in a separate licensed product.

## Optional real-MapLibre browser smoke (maintainers)

The repository also includes an intentionally **unpublished, developer-only** MapLibre integration fixture and browser harness. It loads locally installed MapLibre, Playwright and esbuild from a separate host application and bundles them for a temporary localhost page with a **synthetic offline map style**, no external tiles, credentials or real asset data. It is not the Syntyr runtime.

The [fixture HTML](https://github.com/dporkka/syntyr-css/blob/main/tests/fixtures/geo-maplibre.html) and [application-owned wiring](https://github.com/dporkka/syntyr-css/blob/main/tests/fixtures/geo-maplibre-app.js) demonstrate the complete **map ↔ list ↔ inspector** contract with three fictional longitude/latitude points:

1. The native list links navigate to a real, focusable details section. MapLibre-owned marker **buttons** expose accessible names; Enter and Space select the same record.
2. The host app updates exactly one selected record in the list, selected-marker ring, inspector and polite status announcement. List selection calls MapLibre `map.jumpTo({center: ...})`, using real `LngLat` positions and the renderer's projection, not `--syn-geo-x` or CSS percentage coordinates.
3. Native status and search controls update both the list and actual MapLibre markers. A hidden/unknown record cannot be selected through the example UI; no-results states clear the inspector and selected markers. Returning to a broader filter keeps the current selection **if it remains visible**.
4. The fixture starts with filters and zoom **disabled** until the app wires their behavior. Without JavaScript, the authored list, initial details and explicit `noscript` explanation remain readable; the list only becomes clickable once the application has wired selection, so it never links inactive sites to unrelated details.
5. Browser checks validate real geographic marker projection, zoom, marker/list keyboard activation, selection and empty-state consistency, 44px targets, mobile container reflow, overlay pointer events, 2×/4× root-font stress, forced colors and reduced motion.

**Authorization boundary:** this is *not* a security implementation. The three fictional points are embedded in test-only JavaScript and are all visible to anyone with the fixture. Client-side filtering and rejecting unknown UI selections do **not** provide authentication, tenant isolation, feature authorization or data privacy. A real OOH/map application must deliver only server-authorized records, enforce per-record and per-tenant permissions at each API or tile endpoint, and verify selection/detail requests server-side. Never load sensitive cross-tenant assets and hope CSS, map layers, or browser filtering hide them. Do not use this synthetic test as evidence that real tenant isolation is working.

**Host-owned design decision:** the fixture uses safe `textContent` updates instead of interpolating record names into `innerHTML`, `map.jumpTo` instead of simulated CSS marker placement, and ordinary browser focus/fragment navigation instead of a custom focus trap. Other applications can use React, HTMX, or plain JavaScript for this orchestration; Syntyr only supplies the optional geospatial presentation styles.

~~~sh
SYNTYR_VENDOR_NODE_MODULES=/path/to/installed/node_modules \
  node tests/geo_maplibre_browser.mjs
~~~

Set `SYNTYR_GEO_CHROMIUM_PATH` if the locally installed Playwright browser revision differs from Playwright's default, or `SYNTYR_GEO_SCREENSHOT_DIR` to save developer-only screenshots. The harness never runs as a Syntyr consumer dependency. Its static fixture and scripts are **not** published on Cloudflare or in the release ZIP.

**Adacavo integration decision:** prefer borrowing Syntyr Geo layout, legend and accessible map-chrome patterns into the existing MapLibre inventory view **without importing an unreleased Syntyr CSS package**. Retain Adacavo's tenant-safe APIs, actual inventory status colors, source clustering, positioning, map controls and map attribution. Reevaluate package-level integration only after Syntyr's CSS is released and proven stable.
