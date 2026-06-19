import { api } from './api.js';
import { requireAuth } from './auth.js';
import { $, renderLoading, renderEmpty, renderError, statusLabel } from './utils.js';

if (!requireAuth()) {}

const STATUS_BADGE = {
  active: 'badge--active',
  blocked: 'badge--blocked',
  inactive: 'badge--inactive',
};

const tableContainer = $('#users-table-container');
const searchInput = $('#search-input');
const paginationEl = $('#pagination');

let page = 1;

function renderTable(users) {
  tableContainer.innerHTML = `
    <table class="data-table data-table--clickable">
      <thead>
        <tr>
          <th>ФИО</th>
          <th>Логин</th>
          <th>Роли</th>
          <th>Статус</th>
        </tr>
      </thead>
      <tbody>
        ${users.map((u) => `
          <tr onclick="location.href='user.html#${u.id}'">
            <td>${u.fullName}</td>
            <td>${u.login}</td>
            <td>${u.roleNames.length
              ? u.roleNames.map((n) => `<span class="role-chip">${n}</span>`).join(' ')
              : '—'}</td>
            <td><span class="badge ${STATUS_BADGE[u.status]}">${statusLabel(u.status)}</span></td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

function renderPagination(meta) {
  if (!meta || meta.total === 0) {
    paginationEl.innerHTML = '';
    return;
  }
  paginationEl.innerHTML = `
    <span>${meta.total} пользователей</span>
    <div class="pagination__controls">
      <button class="btn btn--secondary btn--sm" id="prev-page" ${page <= 1 ? 'disabled' : ''}>←</button>
      <button class="btn btn--secondary btn--sm" id="next-page" ${page >= meta.pages ? 'disabled' : ''}>→</button>
    </div>`;
  $('#prev-page')?.addEventListener('click', () => { page--; loadUsers(); });
  $('#next-page')?.addEventListener('click', () => { page++; loadUsers(); });
}

async function loadUsers() {
  renderLoading(tableContainer);
  try {
    const res = await api.getUsers({ page, limit: 10, search: searchInput.value.trim() });
    if (res.meta.total === 0) {
      renderEmpty(tableContainer, 'Пользователей нет', '');
    } else {
      renderTable(res.data);
    }
    renderPagination(res.meta);
  } catch (err) {
    renderError(tableContainer, err.message);
  }
}

searchInput.addEventListener('input', () => { page = 1; loadUsers(); });
loadUsers();
