/* Optional, dependency-free ARIA menu behavior. Importing is inert.
 * Ordinary Syntyr action panels use Tab navigation and need no script. */
const ITEM = '[data-syn-menu-item]';

export function enhanceMenu(menu) {
  if (!menu || !menu.matches?.('[popover][data-syn-menu]')) {
    throw new TypeError('enhanceMenu expects a popover with data-syn-menu');
  }
  // Manual popovers do not dismiss on Escape. The adapter promises Escape
  // dismissal and must reject this mode before applying any ARIA roles.
  if (menu.getAttribute('popover') === 'manual') {
    throw new TypeError('enhanceMenu requires an auto popover');
  }
  if (typeof menu.showPopover !== 'function') return () => {};

  const document = menu.ownerDocument;
  const root = menu.getRootNode();
  const active = () => root.activeElement ?? document.activeElement;
  const oldRole = menu.getAttribute('role');
  const oldItems = new Map();
  const trigger = [...root.querySelectorAll('[popovertarget]')]
    .find((el) => el.getAttribute('popovertarget') === menu.id);
  const triggerAttributes = new Map();
  if (trigger) {
    for (const name of ['aria-haspopup', 'aria-controls', 'aria-expanded']) {
      triggerAttributes.set(name, trigger.getAttribute(name));
    }
    trigger.setAttribute('aria-haspopup', 'menu');
    trigger.setAttribute('aria-controls', menu.id);
    trigger.setAttribute('aria-expanded', String(menu.matches(':popover-open')));
  }
  const enabled = () => [...menu.querySelectorAll(ITEM)].filter((el) =>
    !el.matches(':disabled, [aria-disabled="true"], [hidden]') &&
    !el.closest('[hidden], [inert]') && el.getClientRects().length > 0);
  let typed = '';
  let lastTyped = 0;

  for (const item of menu.querySelectorAll(ITEM)) {
    oldItems.set(item, [item.getAttribute('role'), item.getAttribute('tabindex')]);
    item.setAttribute('role', 'menuitem');
    item.setAttribute('tabindex', '-1');
  }
  menu.setAttribute('role', 'menu');

  function onToggle(event) {
    trigger?.setAttribute('aria-expanded', String(event.newState === 'open'));
    if (event.newState === 'open') {
      typed = '';
      enabled()[0]?.focus();
    } else if (menu.contains(active())) {
      trigger?.focus();
    }
  }
  function onKeyDown(event) {
    if (event.altKey || event.ctrlKey || event.metaKey ||
        event.target.matches('input, textarea, select, [contenteditable="true"]')) return;
    const items = enabled();
    if (!items.length) return;
    const index = items.indexOf(active());
    let next;
    switch (event.key) {
      case 'ArrowDown': next = (index + 1) % items.length; break;
      case 'ArrowUp': next = (index < 0 ? 0 : index + items.length - 1) % items.length; break;
      case 'Home': next = 0; break;
      case 'End': next = items.length - 1; break;
      case 'Tab':
        menu.hidePopover();
        return; // Preserve native sequential focus navigation.
      default:
        if (event.key.length !== 1 || !/\S/u.test(event.key)) return;
        const now = Date.now();
        typed = now - lastTyped > 700 ? event.key : typed + event.key;
        lastTyped = now;
        const candidates = [...items.slice(index + 1), ...items.slice(0, index + 1)];
        const matches = (query) => candidates.find((item) =>
          item.textContent.trim().toLocaleLowerCase().startsWith(query.toLocaleLowerCase()));
        const found = matches(typed) ?? matches(event.key);
        if (found) {
          event.preventDefault();
          found.focus();
        }
        return;
    }
    event.preventDefault();
    items[next]?.focus();
  }
  function onCaptureClick(event) {
    const item = event.target.closest?.(ITEM);
    if (!item || !menu.contains(item)) return;
    // Capture runs before a disabled link's own click listeners. A bubbling
    // handler would run too late to prevent application-side mutations.
    if (item.matches(':disabled, [aria-disabled="true"]')) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }
  function onClick(event) {
    const item = event.target.closest?.(ITEM);
    if (!item || !menu.contains(item)) return;
    // Application handlers may run before this bubbling listener; ordinary
    // enabled actions are application-owned, then the menu is dismissed.
    menu.hidePopover();
  }

  menu.addEventListener('toggle', onToggle);
  menu.addEventListener('keydown', onKeyDown);
  menu.addEventListener('click', onCaptureClick, true);
  menu.addEventListener('click', onClick);
  // If enhancement starts after the popover has opened, no toggle event is
  // replayed. Establish the same initial focus as the normal opening path.
  if (menu.matches(':popover-open')) {
    typed = '';
    enabled()[0]?.focus();
  }
  return () => {
    menu.removeEventListener('toggle', onToggle);
    menu.removeEventListener('keydown', onKeyDown);
    menu.removeEventListener('click', onCaptureClick, true);
    menu.removeEventListener('click', onClick);
    if (trigger) {
      for (const [name, value] of triggerAttributes) {
        if (value === null) trigger.removeAttribute(name);
        else trigger.setAttribute(name, value);
      }
    }
    if (oldRole === null) menu.removeAttribute('role');
    else menu.setAttribute('role', oldRole);
    for (const [item, [role, tabindex]] of oldItems) {
      if (role === null) item.removeAttribute('role');
      else item.setAttribute('role', role);
      if (tabindex === null) item.removeAttribute('tabindex');
      else item.setAttribute('tabindex', tabindex);
    }
  };
}
