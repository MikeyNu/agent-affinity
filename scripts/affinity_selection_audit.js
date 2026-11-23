'use strict';
// Read-only Affinity SDK example for Scripting Studio or MCP execute_script.
// Node can check syntax but cannot execute Affinity-only require('/document.js').
// Official SDK selection APIs: https://www.affinity.studio/help/scripting-tutorial-crop-marks/
const { Document } = require('/document.js');

const doc = Document.current;
if (!doc) {
  console.log(JSON.stringify({ status: 'no_document', selected: 0 }));
} else {
  const selected = doc.selection.nodes.toArray();
  const bounds = [];
  for (const node of selected.slice(0, 24)) {
    const box = node.getSpreadVisibleBox();
    bounds.push({ x: box.x, y: box.y, width: box.width, height: box.height });
  }
  console.log(JSON.stringify({
    status: 'read_only_selection',
    documentSessionUuid: doc.sessionUuid,
    selected: selected.length,
    bounds
  }));
}
