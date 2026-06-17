from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

# ==========================================
# 1. ПОЛЬЗОВАТЕЛИ (FR-1: Статусы и блокировка)
# ==========================================
class CustomUser(AbstractUser):
    is_blocked = models.BooleanField(
        default=False, 
        verbose_name="Заблокирован"
    )
    roles = models.ManyToManyField(
        'CustomRole', 
        blank=True, 
        related_name='users',
        verbose_name="Роли пользователя"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


# ==========================================
# 2. РОЛИ (FR-3, FR-4: Иерархия, Системность)
# ==========================================
class CustomRole(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Название роли"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Описание роли"
    )
    # Помните про django-mptt/treebeard, если дерево ролей будет глубоким
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sub_roles',
        verbose_name="Родительская роль"
    )
    is_system = models.BooleanField(
        default=False, 
        verbose_name="Системная роль (нельзя удалить)"
    )

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise PermissionError("Критическая ошибка: Нельзя удалить системную роль!")
        super().delete(*args, **kwargs)

# Сигнал для железной защиты системных ролей от массового удаления через QuerySet
@receiver(pre_delete, sender=CustomRole)
def protect_system_roles(sender, instance, **kwargs):
    if instance.is_system:
        raise PermissionError("Критическая ошибка: Нельзя удалить системную роль через QuerySet!")


# ==========================================
# 3. КАТАЛОГ РАЗДЕЛОВ
# ==========================================
class AppSection(models.Model):
    name = models.CharField(
        max_length=100, 
        verbose_name="Название раздела"
    )
    slug = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Код раздела для фронтенда (slug)"
    )

    class Meta:
        verbose_name = "Раздел приложения"
        verbose_name_plural = "Разделы приложения"

    def __str__(self):
        return self.name


# ==========================================
# 4. КАТАЛОГ ПРАВ (FR-5)
# ==========================================
class AppPermission(models.Model):
    section = models.ForeignKey(
        AppSection, 
        on_delete=models.CASCADE, 
        related_name='permissions',
        verbose_name="Раздел приложения"
    )
    codename = models.CharField(
        max_length=50, 
        verbose_name="Код действия (codename)"
    )
    description = models.TextField(
        verbose_name="Описание права"
    )

    class Meta:
        verbose_name = "Право доступа"
        verbose_name_plural = "Права доступа"
        constraints = [
            models.UniqueConstraint(fields=['section', 'codename'], name='unique_section_action')
        ]

    def __str__(self):
        return f"{self.section.slug}:{self.codename}"


# ==========================================
# 5. МАТРИЦА ПРАВ (Явные ALLOW / DENY)
# ==========================================
class RolePermission(models.Model):
    ACCESS_CHOICES = [
        ('allow', 'Разрешить (ALLOW)'),
        ('deny', 'Запретить (DENY)'),
    ]

    role = models.ForeignKey(
        CustomRole, 
        on_delete=models.CASCADE, 
        related_name='matrix_rules',
        verbose_name="Роли"
    )
    permission = models.ForeignKey(
        AppPermission, 
        on_delete=models.CASCADE, 
        related_name='matrix_rules',
        verbose_name="Право"
    )
    access_type = models.CharField(
        max_length=5, 
        choices=ACCESS_CHOICES, 
        default='allow',
        verbose_name="Тип доступа"
    )

    class Meta:
        verbose_name = "Правило матрицы"
        verbose_name_plural = "Матрица прав"
        constraints = [
            models.UniqueConstraint(fields=['role', 'permission'], name='unique_role_permission')
        ]


# ==========================================
# 6. ЛОГИ АУДИТА (FR-13, FR-14, FR-15)
# ==========================================
class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_logs',
        verbose_name="Пользователь",
        db_index=True # Быстрый поиск по конкретному юзеру
    )
    username_snapshot = models.CharField(
        max_length=150, 
        verbose_name="Слепок имени пользователя"
    )
    action_codename = models.CharField(
        max_length=100, 
        verbose_name="Проверяемое действие"
    )
    result = models.CharField(
        max_length=5, 
        choices=[('allow', 'ALLOW'), ('deny', 'DENY')], 
        verbose_name="Результат проверки",
        db_index=True # Быстрая фильтрация неуспешных попыток (FR-14)
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата и время",
        db_index=True # Быстрый поиск по периодам (FR-15)
    )

    class Meta:
        verbose_name = "Лог аудита"
        verbose_name_plural = "Логи аудита"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Автоматически пишем имя пользователя, если передан объект CustomUser
        if self.user and not self.username_snapshot:
            self.username_snapshot = self.user.username
        super().save(*args, **kwargs)
