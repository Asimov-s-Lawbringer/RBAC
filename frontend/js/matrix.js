import { api } from './api.js';
import { $, renderLoading, renderError } from './utils.js';
import { requireAuth, hasPermission } from './auth.js';

if (!requireAuth()) {}

const DISPLAY = {
  allow: { icon: '✓', label: '', className: 'matrix-cell--allow' },
  deny: { icon: '✕', label: 'deny', className: 'matrix-cell--deny' },
  inherit: { icon: '🕒', label: 'насл.', className: 'matrix-cell--inherit' },
  none: { icon: '✕', label: '', className: 'matrix-cell--deny' },
};

const EDIT_CYCLE = ['none', 'allow', 'deny'];

let permissions = [];
let roles = [];
let bindings = [];
let savedBindings = [];

const tableContainer = $('#matrix-table-container');
const saveBtn = $('#save-btn');
const canSave = hasPermission('save_matrix');

function getBinding(roleId, permissionId) {
  return bindings.find((b) => b.roleId === roleId && b.permissionId === permissionId);
}

function cellHtml(grant) {
  const d = DISPLAY[grant] || DISPLAY.none;
  const label = d.label ? `<span class="matrix-cell__label">${d.label}</span>` : '';
  return `<span class="matrix-cell ${d.className}">${d.icon}${label}</span>`;
}

function renderTable() {
  const headers = roles.map((r) => `<th>${r.name.toUpperCase()}</th>`).join('');
  const rows = permissions.map((perm) => {
    const cells = roles.map((role) => {
      const grant = getBinding(role.id, perm.id)?.grant ?? 'none';
      return `<td data-role-id="${role.id}" data-permission-id="${perm.id}">${cellHtml(grant)}</td>`;
    }).join('');
    return `<tr><td>${perm.name}</td>${cells}</tr>`;
  }).join('');

  tableContainer.innerHTML = `
    <table class="matrix-table">
      <thead><tr><th>Право / Роль</th>${headers}</tr></thead>
      <tbody>${rows}</tbody>
    </table>`;

  if (canSave) {
    tableContainer.querySelectorAll('td[data-role-id]').forEach((td) => {
      td.addEventListener('click', onCellClick);
    });
  }
}

function onCellClick(e) {
  const td = e.currentTarget;
  const roleId = Number(td.dataset.roleId);
  const permissionId = Number(td.dataset.permissionId);
  let binding = getBinding(roleId, permissionId);
  const current = binding?.grant ?? 'none';
  const idx = current === 'inherit' ? 0 : EDIT_CYCLE.indexOf(current);
  const next = EDIT_CYCLE[(idx + 1) % EDIT_CYCLE.length];

  if (binding) binding.grant = next;
  else {
    binding = { roleId, permissionId, grant: next };
    bindings.push(binding);
  }

  td.innerHTML = cellHtml(next);
  saveBtn.disabled = !hasMatrixChanges();
}

function hasMatrixChanges() {
  return JSON.stringify(storableBindings(bindings)) !== JSON.stringify(storableBindings(savedBindings));
}

function storableBindings(list) {
  return list
    .filter((b) => b.grant === 'allow' || b.grant === 'deny')
    .map((b) => ({ roleId: b.roleId, permissionId: b.permissionId, grant: b.grant }))
    .sort((a, b) => a.roleId - b.roleId || a.permissionId - b.permissionId);
}

async function loadMatrix() {
  renderLoading(tableContainer);
  saveBtn.hidden = !canSave;
  saveBtn.disabled = true;
  try {
    const view = await api.getMatrixView();
    permissions = view.permissions;
    roles = view.roles;
    bindings = structuredClone(view.bindings);
    savedBindings = structuredClone(view.bindings);
    renderTable();
    saveBtn.disabled = !hasMatrixChanges();
  } catch (err) {
    renderError(tableContainer, err.message);
  }
}

saveBtn.addEventListener('click', async () => {
  if (!canSave) return;
  saveBtn.disabled = true;
  try {
    await api.saveMatrixView(permissions, roles, bindings, savedBindings);
    savedBindings = structuredClone(bindings);
  } catch (err) {
    alert(err.message);
  }
  saveBtn.disabled = !hasMatrixChanges();
});

loadMatrix();
