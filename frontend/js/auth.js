import { API_BASE } from './api.js';

const SESSION_KEY = 'rbac_session';

export function getSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function requireAuth() {
  if (!getSession()) {
    window.location.replace('login.html');
    return false;
  }
  return true;
}

export function redirectIfAuthenticated() {
  if (getSession()) {
    window.location.replace('matrix.html');
    return true;
  }
  return false;
}

export async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  });

  let json = {};
  try {
    json = await response.json();
  } catch {
    /* пустой ответ */
  }

  if (!response.ok) {
    throw new Error(json.detail || 'Неверный логин или пароль');
  }

  const session = {
    username: json.username,
    fullName: json.full_name || json.username,
    userId: json.id,
  };
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return session;
}

export function logout() {
  localStorage.removeItem(SESSION_KEY);
  window.location.replace('login.html');
}
