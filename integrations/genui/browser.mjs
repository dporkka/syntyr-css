/** Optional native DOM renderer for the bounded Syntyr GenUI v1 snapshot. */
const MAX_BYTES = 262144, MAX_DEPTH = 12, MAX_NODES = 256, MAX_TEXT = 4000;
const own = (o, k) => Object.hasOwn(o, k);
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const fields = (o, required, optional = []) => object(o) &&
  required.every(k => own(o, k)) && Object.keys(o).every(k => required.includes(k) || optional.includes(k));
export class GenUIError extends Error {}
function require(condition, message) {
  if (!condition) throw new GenUIError(message);
}
function text(v, label = false) {
  require(typeof v === 'string' && [...v].length <= MAX_TEXT &&
    !/[\uD800-\uDFFF\u0000-\u0008\u000B\u000C\u000E-\u001F]/u.test(v), 'Invalid text');
  require(!label || /[^\p{White_Space}\u001c-\u001f]/u.test(v), 'Empty label');
}
function strings(v, max, label = false) {
  require(Array.isArray(v) && v.length > 0 && v.length <= max, 'Invalid string list');
  for (const item of v) text(item, label);
}
const contracts = Object.freeze({
  Panel: [], Stack: [], Grid: [], Heading: ['text','level'], Text: ['text'],
  Badge: ['text'], Metric: ['label','value'], List: ['items'],
  Table: ['caption','columns','rows'], Progress: ['label','value','max'],
  Details: ['summary'], Divider: [],
});
const containers = new Set(['Panel','Stack','Grid','Details']);

// JSON.parse validates grammar first. Walk lexical tokens to reject duplicate
// decoded property names and noninteger number spellings lost by JSON.parse.
function strictParse(source) {
  let value;
  try { value = JSON.parse(source); }
  catch { throw new GenUIError('Invalid JSON'); }
  const stack = [];
  const tokens = /"(?:\\.|[^"\\])*"|[{}\[\],:]|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/g;
  for (const match of source.matchAll(tokens)) {
    const t = match[0], top = stack.at(-1);
    if (t === '{' || t === '[') {
      stack.push(t === '{' ? {keys:new Set(), key:true} : null);
      require(stack.length <= 40, 'JSON depth exceeded');
    } else if (t === '}' || t === ']') stack.pop();
    else if (t === ',' && top) top.key = true;
    else if (t[0] === '"' && top?.key) {
      const key = JSON.parse(t);
      require(!top.keys.has(key), 'Duplicate JSON key');
      top.keys.add(key);
      top.key = false;
    } else if (/^-?\d/.test(t)) {
      require(/^-?\d+$/.test(t), 'Expected integer number');
    }
  }
  return value;
}

export function validateJson(source) {
  require(typeof source === 'string' && source.length <= MAX_BYTES &&
    new TextEncoder().encode(source).length <= MAX_BYTES, 'Invalid document size');
  const spec = strictParse(source);
  require(fields(spec,['version','root']) && spec.version === 1, 'Invalid envelope');
  let budget = MAX_NODES;
  function validate(n, depth) {
    require(depth <= MAX_DEPTH && budget-- > 0, 'Component limit exceeded');
    require(fields(n,['type'],['props','children']) && typeof n.type === 'string' &&
      own(contracts,n.type), 'Unknown component');
    const p = own(n,'props') ? n.props : {};
    require(fields(p,contracts[n.type]), 'Invalid properties');
    switch (n.type) {
      case 'Heading':
        text(p.text); require(Number.isInteger(p.level) && p.level >= 1 && p.level <= 6,'Invalid heading'); break;
      case 'Text': text(p.text); break;
      case 'Badge': text(p.text,true); break;
      case 'Metric': text(p.label,true); text(p.value); break;
      case 'List': strings(p.items,100); break;
      case 'Table':
        text(p.caption,true); strings(p.columns,20,true);
        require(Array.isArray(p.rows) && p.rows.length <= 100,'Invalid rows');
        for (const row of p.rows) {
          strings(row,20); require(row.length === p.columns.length,'Invalid row width');
        }
        break;
      case 'Progress':
        text(p.label,true);
        require(Number.isInteger(p.value) && Number.isInteger(p.max) &&
          p.value >= 0 && p.max > 0 && p.max <= 1000000000 && p.value <= p.max,'Invalid progress'); break;
      case 'Details': text(p.summary,true); break;
    }
    if (containers.has(n.type)) {
      require(Array.isArray(n.children) && n.children.length > 0 && n.children.length <= MAX_NODES,'Invalid children');
      for (const child of n.children) validate(child,depth+1);
    } else require(!own(n,'children'),'Leaf component cannot have children');
  }
  validate(spec.root,1);
  return spec;
}

// Private identity metadata: keys never become DOM attributes.
const identities = new WeakMap();
const mounted = new WeakMap();

function buildJson(source, doc, keys = new Map()) {
  const spec = validateJson(source);
  require(keys instanceof Map && keys.size <= MAX_NODES, 'Invalid key map');
  const used = new Set(), visited = new Set();
  for (const [path, key] of keys) {
    require(typeof path === 'string' && path.length <= 128, 'Invalid key path');
    text(key,true);
    require(key.length <= 128 && !used.has(key), 'Duplicate or oversized key');
    used.add(key);
  }
  const el = (tag, cls, content) => {
    const e = doc.createElement(tag);
    if (cls) e.className = cls;
    if (content !== undefined) e.textContent = content;
    return e;
  };
  function render(n, path) {
    const element = renderElement(n,path);
    visited.add(path);
    identities.set(element,{type:n.type,key:keys.get(path)});
    return element;
  }
  function renderElement(n, path) {
    const p = n.props ?? {};
    let e;
    switch (n.type) {
      case 'Panel': case 'Stack': case 'Grid':
        e = el('div', 'syn-' + n.type.toLowerCase());
        e.append(...n.children.map((child,i)=>render(child,path+'/'+i))); return e;
      case 'Details':
        e = el('details'); e.append(el('summary',null,p.summary),...n.children.map((child,i)=>render(child,path+'/'+i))); return e;
      case 'Heading': return el('h'+p.level,'syn-heading',p.text);
      case 'Text': return el('p',null,p.text);
      case 'Badge': return el('span','syn-badge',p.text);
      case 'Metric':
        e = el('dl','syn-stat'); e.append(el('dt','syn-stat-label',p.label),el('dd','syn-stat-value',p.value)); return e;
      case 'List':
        e = el('ul','syn-list'); e.append(...p.items.map(item=>el('li',null,item))); return e;
      case 'Table': {
        e = el('div','syn-table-wrap');
        e.tabIndex=0; e.setAttribute('role','region'); e.setAttribute('aria-label',p.caption);
        const table=el('table','syn-table'), head=el('thead'), tr=el('tr'), body=el('tbody');
        for (const column of p.columns) {
          const th=el('th',null,column); th.scope='col'; tr.append(th);
        }
        head.append(tr);
        for (const row of p.rows) {
          const r=el('tr'); r.append(...row.map(cell=>el('td',null,cell))); body.append(r);
        }
        table.append(el('caption',null,p.caption),head,body); e.append(table); return e;
      }
      case 'Progress': {
        e=el('label',null,p.label+' ');
        const fraction=p.value+'/'+p.max, progress=el('progress',null,fraction);
        progress.max=p.max; progress.value=p.value;
        e.append(progress,' ',el('span',null,fraction)); return e;
      }
      case 'Divider': return el('hr');
    }
  }
  const root=el('div','syn-root');
  root.append(render(spec.root,'root'));
  require([...keys.keys()].every(path=>visited.has(path)), 'Unknown key path');
  return root;
}

/** Construct a detached native subtree; never parse model content as HTML. */
export function renderJson(source, doc = globalThis.document) {
  return buildJson(source,doc);
}

/** Replace only the host-owned container after successful validation/render. */
export function mountJson(container, source) {
  const root = renderJson(source,container.ownerDocument);
  container.replaceChildren(root);
  mounted.set(container,root);
  return root;
}


// Match only compatible generated nodes. Unkeyed nodes have positional identity;
// keyed components may move among siblings but cannot move across parents.
function compatible(oldNode,newNode) {
  if (!oldNode || oldNode.nodeType !== newNode.nodeType ||
      oldNode.nodeName !== newNode.nodeName) return false;
  const old = identities.get(oldNode), next = identities.get(newNode);
  return old?.type === next?.type && old?.key === next?.key;
}

function patchNode(oldNode,newNode) {
  if (oldNode.nodeType === 3) {
    if (oldNode.data !== newNode.data) oldNode.data = newNode.data;
    return;
  }
  const preserveOpen = oldNode.localName === 'details';
  for (const attr of [...oldNode.attributes]) {
    if (!(preserveOpen && attr.name === 'open') && !newNode.hasAttribute(attr.name))
      oldNode.removeAttribute(attr.name);
  }
  for (const attr of newNode.attributes) {
    if (oldNode.getAttribute(attr.name) !== attr.value)
      oldNode.setAttribute(attr.name,attr.value);
  }
  const oldChildren = [...oldNode.childNodes], nextChildren = [...newNode.childNodes];
  const keyed = new Map();
  for (const child of oldChildren) {
    const key = identities.get(child)?.key;
    if (key !== undefined) keyed.set(key,child);
  }
  const retained = new Set();
  const ordered = nextChildren.map((child,index)=>{
    const key = identities.get(child)?.key;
    const candidate = key === undefined ? oldChildren[index] : keyed.get(key);
    if (!retained.has(candidate) && compatible(candidate,child)) {
      retained.add(candidate);
      patchNode(candidate,child);
      return candidate;
    }
    return child;
  });
  // Remove discarded nodes first, then reorder retained nodes with minimal moves.
  for (const child of oldChildren) if (!retained.has(child)) child.remove();
  for (const [index,child] of ordered.entries()) {
    if (oldNode.childNodes[index] !== child)
      oldNode.insertBefore(child,oldNode.childNodes[index] ?? null);
  }
}

/**
 * Reconcile a validated snapshot into a dedicated renderer-owned container.
 * Host-provided keys map component paths (root, root/0, ...) to stable IDs.
 * Unkeyed children are matched by position; key interactive components if
 * their order can change. Never reuse unknown host DOM as a starting tree.
 */
export function reconcileJson(container,source,{keys=new Map()}={}) {
  const next = buildJson(source,container.ownerDocument,keys);
  const previous = mounted.get(container);
  if (!previous || container.childNodes.length !== 1 || container.firstChild !== previous) {
    container.replaceChildren(next);
    mounted.set(container,next);
    return next;
  }
  const active = container.ownerDocument.activeElement;
  const focused = previous.contains(active) ? active : null;
  const scroll = [...previous.querySelectorAll('.syn-table-wrap')]
    .map(node=>[node,node.scrollLeft,node.scrollTop]);
  patchNode(previous,next);
  if (focused && previous.contains(focused) &&
      container.ownerDocument.activeElement !== focused) {
    focused.focus({preventScroll:true});
  }
  for (const [node,x,y] of scroll) if (previous.contains(node)) {
    if (node.scrollLeft !== x) node.scrollLeft = x;
    if (node.scrollTop !== y) node.scrollTop = y;
  }
  return previous;
}
