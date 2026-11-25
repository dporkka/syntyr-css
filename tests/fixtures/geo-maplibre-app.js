// Developer-only application wiring, not a Syntyr CSS component or public API.
// All sites here are synthetic. In a real app the server must provide only
// authorized, tenant-scoped records; client-side filtering IS NOT access control.
(() => {
  "use strict";
  const sites = [
    { id: "site-a", name: "Site A", status: "active", coordinates: [-73.9, 40.7] },
    { id: "site-b", name: "Site B", status: "maintenance", coordinates: [-73.95, 40.77] },
    { id: "site-c", name: "Site C", status: "active", coordinates: [-73.85, 40.73] },
  ];
  const map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      sources: {},
      layers: [{ id: "offline-background", type: "background", paint: { "background-color": "#c6dee2" } }],
    },
    center: sites[0].coordinates,
    zoom: 8,
    attributionControl: false, // Offline empty style, no external tile data.
    cooperativeGestures: true,
    fadeDuration: 0,
  });
  const markers = new Map();
  const links = new Map();
  const rows = new Map();
  const statusInput = document.querySelector("#site-status");
  const searchInput = document.querySelector("#site-search");
  const siteCount = document.querySelector("#site-count");
  const detailName = document.querySelector("#site-selected-name");
  const detailStatus = document.querySelector("#site-selected-status");
  const detailCoordinates = document.querySelector("#site-selected-coordinates");
  const announcement = document.querySelector("#site-selection-announcement");
  let visible = sites;
  let selectedId = null;

  function setCurrent(id) {
    const site = visible.find(item => item.id === id);
    if (!site) return false;
    selectedId = site.id;
    for (const [key, marker] of markers) {
      const current = key === id;
      marker.getElement().dataset.synSelected = String(current);
      if (current) marker.getElement().setAttribute("aria-current", "location");
      else marker.getElement().removeAttribute("aria-current");
      if (current) links.get(key).setAttribute("aria-current", "location");
      else links.get(key).removeAttribute("aria-current");
    }
    detailName.textContent = site.name;
    detailStatus.textContent = site.status === "active" ? "Active" : "Maintenance";
    detailCoordinates.textContent = site.coordinates.join(", ") + " (synthetic)";
    announcement.textContent = site.name + " selected";
    // The renderer, never Syntyr CSS, owns the geographic camera position.
    map.jumpTo({ center: site.coordinates });
    return true;
  }

  function filterSites() {
    const query = searchInput.value.trim().toLocaleLowerCase();
    const status = statusInput.value;
    visible = sites.filter(site =>
      (status === "all" || site.status === status) &&
      (!query || (site.name + " " + site.status).toLocaleLowerCase().includes(query))
    );
    for (const site of sites) {
      const shown = visible.includes(site);
      rows.get(site.id).hidden = !shown;
      // Avoid remounting a marker on every keystroke (which would drop focus).
      const marker = markers.get(site.id);
      if (shown && !marker.getElement().isConnected) marker.addTo(map);
      else if (!shown && marker.getElement().isConnected) marker.remove();
    }
    siteCount.textContent = visible.length === 1
      ? "1 fictional site in the list" : visible.length + " fictional sites in the list";
    if (visible.length === 0) {
      selectedId = null;
      detailName.textContent = "No matching sites";
      detailStatus.textContent = "—";
      detailCoordinates.textContent = "—";
      announcement.textContent = "No matching sites. Change the search or status filter.";
      for (const link of links.values()) link.removeAttribute("aria-current");
      for (const marker of markers.values()) {
        marker.getElement().removeAttribute("aria-current");
        marker.getElement().dataset.synSelected = "false";
      }
      return;
    }
    setCurrent(visible.some(site => site.id === selectedId) ? selectedId : visible[0].id);
  }

  for (const site of sites) {
    const row = document.querySelector('[data-site-id="' + site.id + '"]');
    // Progressive enhancement: the static list is readable, but has no
    // false detail navigation if the map application fails to initialize.
    const label = row.querySelector('[data-site-label="' + site.id + '"]');
    const link = document.createElement("a");
    link.href = "#site-details";
    link.dataset.siteLink = site.id;
    link.textContent = label.textContent;
    label.replaceWith(link);
    rows.set(site.id, row);
    links.set(site.id, link);
    link.addEventListener("click", () => { setCurrent(site.id); });
    const markerButton = document.createElement("button");
    markerButton.type = "button";
    markerButton.className = "syn-geo-marker";
    markerButton.dataset.siteId = site.id;
    markerButton.dataset.synGeoKind = site.status === "maintenance" ? "zone" : "site";
    markerButton.setAttribute("aria-label", "Inspect " + site.name);
    markerButton.addEventListener("click", () => setCurrent(site.id));
    // These are genuine longitude/latitude values in a synthetic map fixture,
    // not CSS percentages used by Syntyr's static schematic.
    markers.set(site.id, new maplibregl.Marker({ element: markerButton, anchor: "center" })
      .setLngLat(site.coordinates));
  }
  searchInput.addEventListener("input", filterSites);
  statusInput.addEventListener("change", filterSites);
  const zoom = document.querySelector("#geo-zoom");
  zoom.addEventListener("click", () => map.zoomIn({ duration: 0 }));
  // Controls remain disabled if the renderer bundle never initializes.
  searchInput.disabled = false;
  statusInput.disabled = false;
  zoom.disabled = false;
  filterSites();

  // Test inspection only. This fixture is not a production application.
  window.__geoMap = map;
  window.__geoFixture = { markers, getSelected: () => selectedId, selectSite: setCurrent };
})();
