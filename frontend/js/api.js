/**
 * Запросы к Django API. Без mock — нужен запущенный бэкенд.
 */

import {
  matrixFromApi,
  matrixToApi,
  auditFromApi,
  effectiveFromNested,
  usersFromApi,
} from './api-adapters.js';

export const API_BASE = 'http://localhost:8000/api';

async function request(method, path, body) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const csrf = document.cookie.match(/csrftoken=([^;]+)/);
  if (csrf && method !== 'GET') {
    headers['X-CSRFToken'] = decodeURIComponent(csrf[1]);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
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
    throw new Error(json?.detail || json?.message || `Ошибка ${response.status}`);
  }

  return json;
}

function asList(data) {
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return [];
}

function asMeta(data, page, limit) {
  const total = data?.count ?? (Array.isArray(data) ? data.length : 0);
  return { total, page, limit, pages: Math.max(1, Math.ceil(total / limit)) };
}

export const api = {
  async getMatrixView() {
    const [matrixRaw, rolesRaw] = await Promise.all([
      request('GET', '/admin/matrix/'),
      request('GET', '/admin/roles/'),
    ]);
    return matrixFromApi(asList(matrixRaw), asList(rolesRaw));
  },

  async saveMatrixView(permissions, roles, bindings) {
    const payload = matrixToApi(permissions, roles, bindings);
    await request('PUT', '/admin/matrix/', payload);
  },

  async getAuditLog(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const raw = await request('GET', `/admin/audit-logs/${qs ? `?${qs}` : ''}`);
    const page = Number(params.page) || 1;
    const limit = Number(params.limit) || 10;
    return {
      data: auditFromApi(asList(raw)),
      meta: asMeta(raw, page, limit),
    };
  },

  async getUsers(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const raw = await request('GET', `/admin/users/${qs ? `?${qs}` : ''}`);
    const page = Number(params.page) || 1;
    const limit = Number(params.limit) || 10;
    return {
      data: usersFromApi(asList(raw)),
      meta: asMeta(raw, page, limit),
    };
  },

  async getUser(id) {
    const raw = await request('GET', `/admin/users/${id}/`);
    return { data: usersFromApi([raw])[0] };
  },

  async getMyPermissions() {
    const raw = await request('GET', '/v1/users/me/permissions/');
    return { data: effectiveFromNested(raw) };
  },
};
