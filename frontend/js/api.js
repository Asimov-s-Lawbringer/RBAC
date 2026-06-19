/**
 * Запросы к Django API (ветка feat/back-models-filling).
 * Авторизация: Token в заголовке Authorization.
 */

import {
  matrixFromApi,
  matrixChangesToApi,
  auditFromApi,
  effectiveFromMe,
  meToUser,
  usersFromApi,
} from './api-adapters.js';

export const API_BASE = 'http://localhost:8000/api';

const SESSION_KEY = 'rbac_session';

function getToken() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw).token : null;
  } catch {
    return null;
  }
}

async function request(method, path, body) {
  const headers = { Accept: 'application/json' };
  const token = getToken();
  if (token) {
    headers.Authorization = `Token ${token}`;
  }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  let json = null;
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      json = { detail: text };
    }
  }

  if (!response.ok) {
    throw new Error(json?.error || json?.detail || json?.message || `Ошибка ${response.status}`);
  }

  return json;
}

function asList(data) {
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return [];
}

export const api = {
  async getMatrixView() {
    const matrixRaw = await request('GET', '/admin/matrix/');
    return matrixFromApi(asList(matrixRaw));
  },

  async saveMatrixView(permissions, roles, bindings, savedBindings) {
    const payload = matrixChangesToApi(roles, permissions, savedBindings, bindings);
    if (payload.changes.length === 0) return;
    await request('POST', '/admin/matrix/', payload);
  },

  async getAuditLog(params = {}) {
    const qs = new URLSearchParams();
    if (params.result) qs.set('result', params.result);
    if (params.user_id) qs.set('user_id', params.user_id);
    if (params.date_from) qs.set('date_from', params.date_from);
    if (params.date_to) qs.set('date_to', params.date_to);

    const query = qs.toString();
    const raw = await request('GET', `/admin/audit-logs/${query ? `?${query}` : ''}`);
    const all = auditFromApi(asList(raw));

    const page = Number(params.page) || 1;
    const limit = Number(params.limit) || 10;
    const start = (page - 1) * limit;

    return {
      data: all.slice(start, start + limit),
      meta: {
        total: all.length,
        page,
        limit,
        pages: Math.max(1, Math.ceil(all.length / limit)),
      },
    };
  },

  /** Эндпоинта /admin/users/ на бэкенде пока нет */
  async getUsers() {
    return {
      data: [],
      meta: { total: 0, page: 1, limit: 10, pages: 1 },
      unavailable: true,
    };
  },

  async getUser(id) {
    const raw = await request('GET', `/admin/users/${id}/`);
    return { data: usersFromApi([raw])[0] };
  },

  async getMe() {
    const raw = await request('GET', '/auth/me/');
    return {
      data: meToUser(raw),
      permissions: effectiveFromMe(raw),
    };
  },

  async getMyPermissions() {
    const { permissions } = await this.getMe();
    return { data: permissions };
  },
};
