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

export function getToken() {
  return getSession()?.token ?? null;
}

export function requireAuth() {
  if (!getToken()) {
    window.location.replace('login.html');
    return false;
  }
  return true;
}

export function redirectIfAuthenticated() {
  if (getToken()) {
    window.location.replace('matrix.html');
    return true;
  }
  return false;
}

export async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  let json = {};
  try {
    json = await response.json();
  } catch {
    /* пустой ответ */
  }

  if (!response.ok) {
    throw new Error(json.error || json.detail || 'Неверный логин или пароль');
  }

  if (!json.token) {
    throw new Error('Сервер не вернул токен авторизации');
  }

  localStorage.setItem(SESSION_KEY, JSON.stringify({ token: json.token }));

  const meResponse = await fetch(`${API_BASE}/auth/me/`, {
    headers: {
      Accept: 'application/json',
      Authorization: `Token ${json.token}`,
    },
  });

  let me = {};
  try {
    me = await meResponse.json();
  } catch {
    /* пустой ответ */
  }

  if (!meResponse.ok) {
    localStorage.removeItem(SESSION_KEY);
    throw new Error(me.error || me.detail || 'Не удалось получить профиль');
  }

  const session = {
    token: json.token,
    username: me.username,
    fullName: me.username,
    userId: me.id,
  };
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return session;
}

export function logout() {
  localStorage.removeItem(SESSION_KEY);
  window.location.replace('login.html');
}
