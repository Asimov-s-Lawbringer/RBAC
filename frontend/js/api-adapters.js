const LABELS = {
  'records:view': 'Просмотр записей',
  'records:create': 'Создание записей',
  'records:delete': 'Удаление записей',
  'audit:view': 'Просмотр журнала',
  'roles:manage': 'Управление ролями',
};

function label(section, action) {
  return LABELS[`${section}:${action}`] || `${section}:${action}`;
}

export function matrixFromApi(apiRows, apiRoles) {
  const roles = apiRoles.map((r) => ({
    id: r.id,
    name: r.name,
    parentId: r.parent_id ?? null,
  }));

  const roleByName = Object.fromEntries(roles.map((r) => [r.name, r]));

  const permissions = apiRows.map((row) => ({
    id: row.permission_id,
    section: row.section,
    action: row.action,
    name: label(row.section, row.action),
  }));

  const bindings = [];

  for (const row of apiRows) {
    for (const [roleName, accessType] of Object.entries(row.roles_assigned || {})) {
      const role = roleByName[roleName];
      if (!role) continue;
      bindings.push({
        roleId: role.id,
        permissionId: row.permission_id,
        grant: accessType,
      });
    }
  }

  // наследование для отображения 🕒 (только визуал, в БД не пишется)
  for (const perm of permissions) {
    for (const role of roles) {
      if (bindings.some((b) => b.roleId === role.id && b.permissionId === perm.id)) continue;
      if (!role.parentId) continue;
      const parentAllow = bindings.find(
        (b) => b.roleId === role.parentId && b.permissionId === perm.id && b.grant === 'allow'
      );
      if (parentAllow) {
        bindings.push({ roleId: role.id, permissionId: perm.id, grant: 'inherit' });
      }
    }
  }

  return { permissions, roles, bindings };
}

export function matrixToApi(permissions, roles, bindings) {
  return permissions.map((perm) => {
    const roles_assigned = {};
    for (const role of roles) {
      const grant = bindings.find(
        (b) => b.roleId === role.id && b.permissionId === perm.id
      )?.grant;
      if (grant === 'allow' || grant === 'deny') {
        roles_assigned[role.name] = grant;
      }
    }
    return {
      permission_id: perm.id,
      section: perm.section,
      action: perm.action,
      roles_assigned,
    };
  });
}

export function auditFromApi(rows) {
  return rows.map((row) => ({
    time: row.created_at,
    subject: row.username ?? row.username_snapshot ?? '—',
    action: row.action ?? row.action_codename ?? '—',
    result: row.result,
  }));
}

export function effectiveFromNested(nested) {
  const list = [];
  for (const [section, actions] of Object.entries(nested || {})) {
    if (!actions || typeof actions !== 'object') continue;
    for (const [action, allowed] of Object.entries(actions)) {
      list.push({
        name: label(section, action),
        allowed: Boolean(allowed),
      });
    }
  }
  return list;
}

export function usersFromApi(rows) {
  return rows.map((u) => ({
    id: u.id,
    login: u.username,
    fullName: [u.first_name, u.last_name].filter(Boolean).join(' ') || u.username,
    status: u.is_blocked ? 'blocked' : u.is_active ? 'active' : 'inactive',
    roleNames: (u.roles || []).map((r) => (typeof r === 'object' ? r.name : r)),
  }));
}
