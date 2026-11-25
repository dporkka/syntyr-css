import { useMemo, useRef, useState } from "react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import * as Toast from "@radix-ui/react-toast";
import {
  Button, ComboBox, Group, Input, Label,
  ListBox, ListBoxItem, Popover, Table, TableHeader, Column, TableBody, Row, Cell,
  type SortDescriptor
} from "react-aria-components";

type Notice = { id: number; title: string; message: string; tone: "success" | "error" };
type Asset = { id: string; asset: string; faces: number };
const assets: Asset[] = [
  { id: "airport", asset: "Airport display", faces: 3 },
  { id: "central", asset: "Central billboard", faces: 12 },
  { id: "transit", asset: "Transit shelter", faces: 7 }
];

export default function App() {
  const nextNotice = useRef(0);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [inventoryQuery, setInventoryQuery] = useState("");
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());
  const [inspectedId, setInspectedId] = useState<string | null>(null);
  const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>({
    column: "asset",
    direction: "ascending"
  });
  // This demonstration contains every asset locally. In a paginated app, never
  // interpret "matching" as all server-side matches without an explicit API scope.
  const matchingAssets = useMemo(() => {
    const query = inventoryQuery.trim().toLocaleLowerCase();
    return assets.filter((item) => item.asset.toLocaleLowerCase().includes(query));
  }, [inventoryQuery]);
  const sortedAssets = useMemo(() => {
    const direction = sortDescriptor.direction === "descending" ? -1 : 1;
    return [...matchingAssets].sort((a, b) => {
      const comparison = sortDescriptor.column === "faces"
        ? a.faces - b.faces
        : a.asset.localeCompare(b.asset);
      return direction * comparison || a.asset.localeCompare(b.asset);
    });
  }, [matchingAssets, sortDescriptor]);
  const inspectedAsset = assets.find((item) => item.id === inspectedId);
  const scopeCount = matchingAssets.length;

  function filterInventory(query: string) {
    setInventoryQuery(query);
    // Clearing on scope changes prevents hidden records remaining selected.
    setSelectedKeys(new Set());
    setInspectedId(null);
  }

  function notify(title: string, message: string, tone: Notice["tone"] = "success") {
    const id = ++nextNotice.current;
    setNotices((current) => [...current.slice(-2), { id, title, message, tone }]);
  }

  return (
    <Toast.Provider swipeDirection="right" duration={5000} label="Notifications">
      <main className="syn-shell" style={{ paddingBlock: "2rem" }}>
        <header>
          <p className="syn-eyebrow">Syntyr / optional headless integrations</p>
          <h1>Accessible interactive controls</h1>
          <p className="syn-lede">
            React Aria handles combobox filtering and focus. Radix handles menu keyboard
            navigation and toast dismissals. Syntyr supplies presentation only.
          </p>
        </header>

        <section className="syn-panel" aria-labelledby="menu-heading">
          <h2 id="menu-heading">Action menu</h2>
          <DropdownMenu.Root>
            <DropdownMenu.Trigger className="syn-button" type="button">
              Campaign actions
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content className="syn-menu-surface" sideOffset={6} align="start">
                <DropdownMenu.Item
                  className="syn-menu-item"
                  onSelect={() => notify("Demo action", "Review selected; no data changed.")}
                >
                  Review campaign
                </DropdownMenu.Item>
                <DropdownMenu.Item
                  className="syn-menu-item"
                  onSelect={() => notify("Demo action", "Duplicate selected; no data changed.")}
                >
                  Duplicate campaign
                </DropdownMenu.Item>
                <DropdownMenu.Separator className="syn-menu-separator" />
                <DropdownMenu.Item className="syn-menu-item" disabled>
                  Archive (unavailable)
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </section>

        <section className="syn-panel" aria-labelledby="combo-heading">
          <h2 id="combo-heading">Searchable format selector</h2>
          <ComboBox className="syn-combobox" name="format">
            <Label className="syn-label">Advertising format</Label>
            <Group className="syn-combobox-field">
              <Input className="syn-input" placeholder="Type a format" />
              <Button className="syn-button" aria-label="Show advertising formats">Show</Button>
            </Group>
            <Popover className="syn-combobox-popover" placement="bottom start">
              <ListBox className="syn-combobox-listbox">
                <ListBoxItem id="static" textValue="Static billboard" className="syn-combobox-option">
                  Static billboard
                </ListBoxItem>
                <ListBoxItem id="digital" textValue="Digital screen" className="syn-combobox-option">
                  Digital screen
                </ListBoxItem>
                <ListBoxItem id="transit" textValue="Transit advertising" className="syn-combobox-option">
                  Transit advertising
                </ListBoxItem>
              </ListBox>
            </Popover>
          </ComboBox>
        </section>

        <section className="syn-panel" aria-labelledby="grid-heading">
          <h2 id="grid-heading">Keyboard-accessible sortable inventory grid</h2>
          <p>
            React Aria provides grid keyboard navigation and sort announcements.
            The application orders this illustrative in-memory dataset; Syntyr
            supplies the existing table presentation.
          </p>
          <div className="syn-filter-bar">
            <label className="syn-filter-field syn-filter-field--query" htmlFor="inventory-filter">
              Filter inventory by asset name
              <input
                id="inventory-filter"
                className="syn-input"
                type="search"
                value={inventoryQuery}
                onChange={(event) => filterInventory(event.target.value)}
                placeholder="Filter the three local records"
              />
            </label>
          </div>
          <div className="syn-bulk-actions">
            <p role="status" aria-label="Inventory selection scope" aria-live="polite">
              {selectedKeys.size} selected · {scopeCount} matching (local data only)
            </p>
            <div className="syn-collection-actions">
              <button
                className="syn-button"
                type="button"
                disabled={scopeCount === 0}
                onClick={() => setSelectedKeys(new Set(matchingAssets.map((item) => item.id)))}
              >
                Select {scopeCount} matching {scopeCount === 1 ? "asset" : "assets"}
              </button>
              <button
                className="syn-button"
                type="button"
                disabled={selectedKeys.size === 0}
                onClick={() => setSelectedKeys(new Set())}
              >
                Clear selection
              </button>
              <button
                className="syn-button"
                type="button"
                disabled={selectedKeys.size === 0}
                onClick={() => notify(
                  "Selection preview",
                  `${selectedKeys.size} asset${selectedKeys.size === 1 ? "" : "s"} selected locally; no data changed.`
                )}
              >
                Preview selection
              </button>
            </div>
          </div>
          <p className="syn-help">
            Click a row or press Space to select. Selection always applies only to the
            current locally loaded results and is cleared when the filter changes.
            No server-side bulk operation is performed.
          </p>
          <div className="syn-table-wrap" role="region" aria-label="Scrollable inventory">
            <Table
              className="syn-table syn-table--striped"
              aria-label="Campaign inventory"
              sortDescriptor={sortDescriptor}
              onSortChange={setSortDescriptor}
              selectionMode="multiple"
              selectionBehavior="toggle"
              selectedKeys={selectedKeys}
              onSelectionChange={(keys) => {
                const visible = new Set(matchingAssets.map((item) => item.id));
                // React Aria's "all" means every currently rendered row, not
                // unseen server records. Resolve it to explicit local IDs.
                const next = keys === "all" ? visible : new Set(Array.from(keys, String));
                setSelectedKeys(new Set([...next].filter((key) => visible.has(key))));
              }}
            >
              <TableHeader>
                <Column id="asset" isRowHeader allowsSorting>
                  <span className="syn-table-sort">Asset</span>
                </Column>
                <Column id="faces" allowsSorting>
                  <span className="syn-table-sort">Faces</span>
                </Column>
                <Column id="details">Details</Column>
              </TableHeader>
              <TableBody items={sortedAssets}>
                {(item) => (
                  <Row id={item.id}>
                    <Cell>{item.asset}</Cell>
                    <Cell>{item.faces}</Cell>
                    <Cell>
                      <Button
                        className="syn-button syn-button--small"
                        onPress={() => setInspectedId(item.id)}
                      >
                        View details for {item.asset}
                      </Button>
                    </Cell>
                  </Row>
                )}
              </TableBody>
            </Table>
          </div>
          {scopeCount === 0 && <p role="status" className="syn-result-state">No matching assets</p>}
          <aside className="syn-panel" role="region" aria-label="Asset details">
            {inspectedAsset ? (
              <>
                <h3>{inspectedAsset.asset}</h3>
                <p>{inspectedAsset.faces} faces</p>
                <p className="syn-help">Read-only local record preview. No backend changes.</p>
              </>
            ) : (
              <p className="syn-muted">Choose View details on a record to inspect it.</p>
            )}
          </aside>
        </section>

        <section className="syn-panel" aria-labelledby="toast-heading">
          <h2 id="toast-heading">Transient notifications</h2>
          <p>Toast messages are intentionally noncritical and can be dismissed.</p>
          <button
            className="syn-button syn-button--primary"
            type="button"
            onClick={() => notify("Demo notification", "This is not a persisted operation.")}
          >
            Show a notification
          </button>
        </section>
      </main>
      {notices.map((item) => (
        <Toast.Root
          key={item.id}
          className="syn-toast"
          data-tone={item.tone}
          open
          duration={5000}
          onOpenChange={(open) => {
            if (!open) setNotices((current) => current.filter((notice) => notice.id !== item.id));
          }}
        >
          <Toast.Title className="syn-toast-title">{item.title}</Toast.Title>
          <Toast.Description className="syn-toast-description">{item.message}</Toast.Description>
          <Toast.Close className="syn-button syn-button--small" aria-label={`Dismiss ${item.title}`}>
            Dismiss
          </Toast.Close>
        </Toast.Root>
      ))}
      <Toast.Viewport className="syn-toast-region" label="Notifications (F8)" />
    </Toast.Provider>
  );
}
