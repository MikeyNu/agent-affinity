'use strict';
// Read-only Affinity execute_script payload. Logs JSON for MCP and Script Studio.
// Do not execute with Node. Run in the app after reading the SDK preamble.
const { Document } = require('/document.js');

const current = Document.current;
if (!current) {
  console.log(JSON.stringify({ status: 'no_document', current: null }));
} else {
  const selected = current.selection.nodes.toArray();
  console.log(JSON.stringify({
    status: 'read_only_inspection',
    name: current.name || null,
    sessionUuid: current.sessionUuid,
    dpi: current.dpi,
    spreadCount: current.spreads.length,
    selectedCount: selected.length,
    selectedTypes: selected.slice(0, 16).map(node =>
      node[Symbol.toStringTag] || 'unknown'
    )
  }));
}
