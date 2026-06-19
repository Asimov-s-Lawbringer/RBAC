import { requireAuth, logout } from './auth.js';
import { setActiveNav, $ } from './utils.js';

export function initAppShell() {
  if (!requireAuth()) return false;

  $('#logout-btn')?.addEventListener('click', logout);
  setActiveNav();
  return true;
}
