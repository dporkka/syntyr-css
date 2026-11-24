/* Editor-only ZIP packaging; published sites contain zero JavaScript. */
const encoder = new TextEncoder();
const PERMITTED = /^(?:index\.html|[a-z][a-z0-9-]{0,39}\/index\.html|syntyr\.all\.css|LICENSE|README\.txt|assets\/(?:(?:gallery-[a-z0-9-]+|syntyr-mark)\.svg|custom-[a-f0-9]{64}\.(?:png|jpg|webp)))$/;
const LIMIT = 32 * 1024 * 1024;
export const SITE_ZIP_MAX_ENTRIES = 256;
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}
export function createStoredZip(entries, {maxBytes = LIMIT, maxEntries = 128} = {}) {
  if (!Number.isInteger(maxEntries) || maxEntries < 1 || maxEntries > SITE_ZIP_MAX_ENTRIES ||
      !Array.isArray(entries) || !entries.length || entries.length > maxEntries)
    throw new Error("Invalid ZIP file count");
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1 || maxBytes > 0xffffffff)
    throw new Error("Invalid ZIP size limit");
  const names = new Set();
  const items = [];
  let total = 22;
  for (const entry of entries) {
    if (!entry || typeof entry.name !== "string" || !PERMITTED.test(entry.name))
      throw new Error("Invalid static site file path");
    if (names.has(entry.name)) throw new Error("Duplicate ZIP file name");
    names.add(entry.name);
    const name = encoder.encode(entry.name);
    const data = typeof entry.content === "string" ? encoder.encode(entry.content) :
      entry.content instanceof Uint8Array ? entry.content : null;
    if (!data) throw new Error("Invalid ZIP file content");
    if (data.byteLength > 0xffffffff) throw new Error("ZIP file too large");
    total += 76 + 2 * name.length + data.length;
    if (total > maxBytes) throw new Error("Static site ZIP exceeds size limit");
    items.push({name, data, crc: crc32(data)});
  }
  const output = new Uint8Array(total);
  const view = new DataView(output.buffer);
  let offset = 0;
  const central = [];
  for (const item of items) {
    const start = offset;
    view.setUint32(offset, 0x04034b50, true);
    view.setUint16(offset + 4, 20, true);
    view.setUint16(offset + 6, 0x0800, true);
    view.setUint16(offset + 14, item.crc & 0xffff, true);
    view.setUint16(offset + 16, item.crc >>> 16, true);
    view.setUint32(offset + 18, item.data.length, true);
    view.setUint32(offset + 22, item.data.length, true);
    view.setUint16(offset + 26, item.name.length, true);
    output.set(item.name, offset + 30);
    output.set(item.data, offset + 30 + item.name.length);
    offset += 30 + item.name.length + item.data.length;
    central.push({start, ...item});
  }
  const directoryStart = offset;
  for (const item of central) {
    view.setUint32(offset, 0x02014b50, true);
    view.setUint16(offset + 4, 20, true);
    view.setUint16(offset + 6, 20, true);
    view.setUint16(offset + 8, 0x0800, true);
    view.setUint32(offset + 16, item.crc, true);
    view.setUint32(offset + 20, item.data.length, true);
    view.setUint32(offset + 24, item.data.length, true);
    view.setUint16(offset + 28, item.name.length, true);
    view.setUint32(offset + 42, item.start, true);
    output.set(item.name, offset + 46);
    offset += 46 + item.name.length;
  }
  const directoryLength = offset - directoryStart;
  view.setUint32(offset, 0x06054b50, true);
  view.setUint16(offset + 8, items.length, true);
  view.setUint16(offset + 10, items.length, true);
  view.setUint32(offset + 12, directoryLength, true);
  view.setUint32(offset + 16, directoryStart, true);
  return output;
}
