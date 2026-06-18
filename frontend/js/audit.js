import { api } from './api.js';
import { requireAuth } from './auth.js';
import { $, renderLoading, renderEmpty, renderError, formatTime } from './utils.js';

if (!requireAuth()) {}

const tableContainer = $('#audit-table-container');
const resultFilter = $('#result-filter');
const paginationEl = $('#pagination');

let page = 1;

function renderTable(entries) {
  tableContainer.innerHTML = `
    <table class="data-table">
      <thead>
        <tr><th>Время</th><th>Пользователь</th><th>Действие</th><th>Результат</th></tr>
      </thead>
      <tbody>
        ${entries.map((e) => `
          <tr>
            <td>${formatTime(e.time)}</td>
            <td>${e.subject}</td>
            <td>${e.action}</td>
            <td>
              <span class="result-badge result-badge--${e.result === 'allow' ? 'allowed' : 'denied'}">
                ${e.result === 'allow' ? 'разрешено' : 'отказано'}
              </span>
            </td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

async function loadAudit() {
  renderLoading(tableContainer);
  const result = resultFilter.value;
  try {
    const res = await api.getAuditLog({
      page,
      limit: 10,
      result: result === 'all' ? '' : result,
    });
    if (res.meta.total === 0) {
      renderEmpty(tableContainer, 'Записей в журнале нет', '');
    } else {
      renderTable(res.data);
    }
    if (res.meta.pages > 1) {
      paginationEl.innerHTML = `
        <button class="btn btn--secondary btn--sm" id="prev" ${page <= 1 ? 'disabled' : ''}>←</button>
        <button class="btn btn--secondary btn--sm" id="next" ${page >= res.meta.pages ? 'disabled' : ''}>→</button>`;
      $('#prev')?.addEventListener('click', () => { page--; loadAudit(); });
      $('#next')?.addEventListener('click', () => { page++; loadAudit(); });
    } else {
      paginationEl.innerHTML = '';
    }
  } catch (err) {
    renderError(tableContainer, err.message);
  }
}

resultFilter.addEventListener('change', () => { page = 1; loadAudit(); });
loadAudit();
