import { requireAuth, logout, hasPermission, getDefaultPage } from './auth.js';
import { setActiveNav, $ } from './utils.js';

const NAV_PERMISSIONS = {
  matrix: 'view_matrix',
  users: 'manage_roles',
  audit: 'view_audit',
};

const PAGE_PERMISSION = {
  matrix: 'view_matrix',
  users: 'manage_roles',
  audit: 'view_audit',
};

function applyNavPermissions() {
  document.querySelectorAll('.app-nav__link[data-page]').forEach((link) => {
    const perm = NAV_PERMISSIONS[link.dataset.page];
    if (perm) link.hidden = !hasPermission(perm);
  });
}

export function initAppShell() {
  if (!requireAuth()) return false;

  const page = document.body.dataset.page;
  const required = PAGE_PERMISSION[page];
  if (required && !hasPermission(required)) {
    window.location.replace(getDefaultPage());
    return false;
  }

  $('#logout-btn')?.addEventListener('click', logout);
  applyNavPermissions();
  setActiveNav();
  return true;
}
