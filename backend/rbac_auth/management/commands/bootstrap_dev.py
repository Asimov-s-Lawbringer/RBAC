from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from rbac_auth.models import CustomRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей для локальной разработки'

    def handle(self, *args, **options):
        self._ensure_user(
            username='admin',
            password='admin',
            role_names=['Администратор'],
            extra_defaults={'is_staff': True, 'is_superuser': True},
        )
        self._ensure_user(
            username='demo',
            password='demo',
            role_names=['Менеджер', 'Аудитор'],
        )

    def _ensure_user(self, username, password, role_names, extra_defaults=None):
        user, created = User.objects.get_or_create(
            username=username,
            defaults=extra_defaults or {},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан пользователь {username} / {password}'))
        else:
            self.stdout.write(f'Пользователь {username} уже существует')

        for role_name in role_names:
            role = CustomRole.objects.filter(name=role_name).first()
            if not role:
                self.stdout.write(
                    self.style.WARNING(
                        f'Роль «{role_name}» не найдена — сначала выполните loaddata init_data.json'
                    )
                )
                continue
            user.roles.add(role)
            self.stdout.write(self.style.SUCCESS(f'Роль «{role_name}» назначена пользователю {username}'))
