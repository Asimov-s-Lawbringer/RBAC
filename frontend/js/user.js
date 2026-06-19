import { api } from './api.js';
import { requireAuth, getSession } from './auth.js';
import { renderLoading, renderError, statusLabel } from './utils.js';

if (!requireAuth()) {}

const container = document.getElementById('user-page-container');

function getUserId() {
  return Number(window.location.hash.replace('#', ''));
}

async function init() {
  const userId = getUserId();
  if (!userId) {
    renderError(container, 'Не указан пользователь');
    return;
  }

  renderLoading(container);

  try {
    const { data: user } = await api.getUser(userId);
    const session = getSession();
    let rights = [];

    if (session?.userId === userId) {
      const res = await api.getMyPermissions();
      rights = res.data;
    }

    const rolesHtml = user.roleNames.length
      ? user.roleNames.map((n) => `<span class="role-chip">${n}</span>`).join('')
      : '<span class="role-chips__empty">Нет ролей</span>';

    const rightsHtml = rights.length
      ? rights.map((r) => `
          <div class="effective-card">
            <div class="effective-card__name">${r.name}</div>
            <span class="effective-card__status effective-card__status--${r.allowed ? 'allowed' : 'denied'}">
              ${r.allowed ? 'разрешено' : 'запрещено'}
            </span>
          </div>`).join('')
      : '<p style="color:#64748b">Эффективные права доступны для своего профиля</p>';

    container.innerHTML = `
      <div class="user-page">
        <div class="user-page__left">
          <h1 class="user-page__title">Пользователь · ${user.fullName}</h1>
          <div class="user-field">
            <span class="user-field__label">Статус</span>
            <p>${statusLabel(user.status)}</p>
          </div>
          <div class="user-field">
            <span class="user-field__label">Назначенные роли</span>
            <div class="role-chips">${rolesHtml}</div>
          </div>
        </div>
        <div class="user-page__right card">
          <h2 class="user-page__section-title">Эффективные права</h2>
          <div class="effective-cards">${rightsHtml}</div>
        </div>
      </div>`;
  } catch (err) {
    renderError(container, err.message);
  }
}

init();
