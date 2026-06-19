/**
 * Каталог ролей и прав из backend/fixtures/init_data.json
 * (отдельных эндпоинтов для справочников пока нет)
 */
const ROLES_CATALOG = [
  { id: 1, name: 'Пользователь', parentId: null },
  { id: 2, name: 'Менеджер', parentId: 1 },
  { id: 3, name: 'Аудитор', parentId: null },
  { id: 4, name: 'Администратор', parentId: null },
];

const PERMISSIONS_CATALOG = [
  { id: 1, codename: 'view_records', name: 'Просмотр записей' },
  { id: 2, codename: 'create_records', name: 'Создание записей' },
  { id: 3, codename: 'delete_records', name: 'Удаление записей' },
  { id: 4, codename: 'view_audit', name: 'Просмотр журнала логов' },
  { id: 5, codename: 'export_audit', name: 'Экспорт логов' },
  { id: 6, codename: 'manage_roles', name: 'Управление ролями' },
  { id: 7, codename: 'view_matrix', name: 'Просмотр матрицы прав' },
  { id: 8, codename: 'save_matrix', name: 'Сохранение матрицы' },
];

export const CODENAME_LABELS = Object.fromEntries(
  PERMISSIONS_CATALOG.map((p) => [p.codename, p.name])
);

const ACCESS_LABELS = {
  allow: 'разрешено',
  deny: 'запрещено',
  none: 'нет',
};

/** Плоский словарь прав из GET /auth/me/ или GET /admin/users/:id/ */
export function permissionsDict(me) {
  return me?.permissions ?? me?.effective_permissions ?? {};
}

export function codenameLabel(codename) {
  return CODENAME_LABELS[codename] || codename;
}

function grantAt(bindings, roleId, permissionId) {
  return bindings.find((b) => b.roleId === roleId && b.permissionId === permissionId)?.grant ?? 'none';
}

function addInheritDisplay(roles, permissions, bindings) {
  for (const perm of permissions) {
    for (const role of roles) {
      const existing = bindings.find(
        (b) => b.roleId === role.id && b.permissionId === perm.id
      );
      if (existing) continue;
      if (!role.parentId) continue;
      const parentAllow = bindings.find(
        (b) =>
          b.roleId === role.parentId &&
          b.permissionId === perm.id &&
          b.grant === 'allow'
      );
      if (parentAllow) {
        bindings.push({ roleId: role.id, permissionId: perm.id, grant: 'inherit' });
      }
    }
  }
}

/** GET /admin/matrix/ → плоский список { role_id, permission_id, grant } */
export function matrixFromApi(apiRules) {
  const roles = ROLES_CATALOG.map((r) => ({ ...r }));
  const permissions = PERMISSIONS_CATALOG.map((p) => ({ id: p.id, name: p.name }));

  const bindings = (apiRules || []).map((rule) => ({
    roleId: rule.role_id,
    permissionId: rule.permission_id,
    grant: rule.grant,
  }));

  addInheritDisplay(roles, permissions, bindings);
  return { permissions, roles, bindings };
}

/** POST /admin/matrix/ → { changes: [{ role_id, permission_id, grant }] } */
export function matrixChangesToApi(roles, permissions, savedBindings, bindings) {
  const changes = [];

  for (const perm of permissions) {
    for (const role of roles) {
      const saved = grantAt(savedBindings, role.id, perm.id);
      const current = grantAt(bindings, role.id, perm.id);

      const savedVal = saved === 'inherit' ? 'none' : saved;
      const currentVal = current === 'inherit' ? 'none' : current;

      if (savedVal === currentVal) continue;

      changes.push({
        role_id: role.id,
        permission_id: perm.id,
        grant: currentVal === 'none' ? 'none' : currentVal,
      });
    }
  }

  return { changes };
}

export function auditFromApi(rows) {
  return rows.map((row) => {
    const action = row.action ?? row.action_codename ?? '—';
    return {
      time: row.created_at,
      subject: row.username ?? row.username_snapshot ?? '—',
      action: codenameLabel(action),
      result: row.result,
    };
  });
}

/** GET /auth/me/ или GET /admin/users/:id/ → список для карточки (allow / deny / none) */
export function effectiveFromMe(me) {
  const perms = permissionsDict(me);
  return Object.entries(perms).map(([codename, accessType]) => ({
    name: codenameLabel(codename),
    codename,
    accessType,
    label: ACCESS_LABELS[accessType] || accessType,
  }));
}

export function meToUser(me) {
  return {
    id: me.id,
    login: me.username,
    fullName: me.username,
    status: me.is_blocked ? 'blocked' : 'active',
    roleNames: [],
  };
}

function userStatus(u) {
  if (u.is_blocked) return 'blocked';
  if (u.is_active === false) return 'inactive';
  return 'active';
}

export function usersFromApi(rows) {
  return rows.map((u) => ({
    id: u.id,
    login: u.username,
    fullName: [u.first_name, u.last_name].filter(Boolean).join(' ') || u.username,
    status: userStatus(u),
    roleNames: (u.roles || []).map((r) => (typeof r === 'object' ? r.name : r)),
  }));
}
