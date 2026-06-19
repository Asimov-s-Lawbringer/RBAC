from django.contrib.auth import get_user_model
from django.test import TestCase

from rbac_auth.models import AppPermission, AppSection, CustomRole, RolePermission
from rbac_auth.services import calculate_effective_permissions, merge_access

User = get_user_model()


class MergeAccessTests(TestCase):
    def test_deny_beats_allow(self):
        self.assertEqual(merge_access('allow', 'deny'), 'deny')
        self.assertEqual(merge_access('deny', 'allow'), 'deny')

    def test_allow_when_no_deny(self):
        self.assertEqual(merge_access(None, 'allow'), 'allow')
        self.assertEqual(merge_access('allow', 'allow'), 'allow')


class EffectivePermissionsTests(TestCase):
    def setUp(self):
        section = AppSection.objects.create(slug='records', name='Записи')
        self.delete_perm = AppPermission.objects.create(
            section=section,
            codename='delete_records',
            description='Удаление записей',
        )
        self.parent_role = CustomRole.objects.create(name='Родитель')
        self.child_role = CustomRole.objects.create(name='Потомок', parent=self.parent_role)
        self.other_role = CustomRole.objects.create(name='Другая')

        self.user = User.objects.create_user(username='tester', password='tester')

    def test_inheritance_child_deny_over_parent_allow(self):
        """FR-24: deny у дочерней роли блокирует allow родителя."""
        RolePermission.objects.create(
            role=self.parent_role, permission=self.delete_perm, access_type='allow'
        )
        RolePermission.objects.create(
            role=self.child_role, permission=self.delete_perm, access_type='deny'
        )
        self.user.roles.add(self.child_role)

        perms = calculate_effective_permissions(self.user)
        self.assertEqual(perms['delete_records'], 'deny')

    def test_inheritance_parent_deny_over_child_allow(self):
        """FR-24: deny родителя блокирует allow потомка."""
        RolePermission.objects.create(
            role=self.parent_role, permission=self.delete_perm, access_type='deny'
        )
        RolePermission.objects.create(
            role=self.child_role, permission=self.delete_perm, access_type='allow'
        )
        self.user.roles.add(self.child_role)

        perms = calculate_effective_permissions(self.user)
        self.assertEqual(perms['delete_records'], 'deny')

    def test_multiple_roles_deny_wins(self):
        """FR-24: deny в одной из ролей блокирует allow в другой."""
        RolePermission.objects.create(
            role=self.child_role, permission=self.delete_perm, access_type='allow'
        )
        RolePermission.objects.create(
            role=self.other_role, permission=self.delete_perm, access_type='deny'
        )
        self.user.roles.add(self.child_role, self.other_role)

        perms = calculate_effective_permissions(self.user)
        self.assertEqual(perms['delete_records'], 'deny')
