export function $(selector, parent = document) {
  return parent.querySelector(selector);
}

export function formatTime(value) {
  const normalized = typeof value === 'string' ? value.replace(' ', 'T') : value;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return value ?? '—';
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const STATUS_LABELS = {
  active: 'Активен',
  blocked: 'Заблокирован',
  inactive: 'Деактивирован',
};

export function statusLabel(status) {
  return STATUS_LABELS[status] || status;
}

export function setActiveNav() {
  const page = document.body.dataset.page;
  document.querySelectorAll('.app-nav__link').forEach((link) => {
    link.classList.toggle('app-nav__link--active', link.dataset.page === page);
  });
}

export function renderLoading(container) {
  container.innerHTML = '<div class="state-loading"><div class="state-loading__spinner"></div><p>Загрузка…</p></div>';
}

export function renderEmpty(container, title, subtitle) {
  container.innerHTML = `<div class="state-empty"><p class="state-empty__title">${title}</p>${subtitle ? `<p>${subtitle}</p>` : ''}</div>`;
}

export function renderError(container, message) {
  container.innerHTML = `<div class="state-error"><p class="state-empty__title">Ошибка</p><p>${message}</p></div>`;
}
