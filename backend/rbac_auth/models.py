from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError


# P.s id у всех моделей есть по дефолту встроенные
# Поля стандартного Django Юзера->->->|
# |->->-> username: Уникальное имя пользователя.password: Хэш пароля | first_name: Имя пользователя | last_name: Фамилия пользователя | email: Электронная почта | is_staff: Логическое значение (True/False), определяющее доступ к панели администратора | is_active: Логическое значение (активен ли аккаунт). Используется вместо физического удаления пользователя | is_superuser: Логическое значение (является ли пользователь суперпользователем со всеми правами) | last_login: Дата и время последнего входа в систему.date_joined: Дата и время создания учетной записи.


# 1 Юзеры (FR-1: Статусы и блокировка)

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



# 2 Роли (FR-3, FR-4: Иерархия, Системность)

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
    # Помнить про django-mptt/treebeard
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

    def clean(self):
        super().clean()
        # Сделал проверку на рекурсию в ролях, ещё одна победа я считаю!
        if self.parent:
            current = self.parent
            while current is not None:
                if current.id == self.id:
                    raise ValidationError(f"Ошибка: Обнаружен цикл! Роль '{self.name}' не может быть предком самой себе.")
                current = current.parent

    #Поведение самой таблицы,не её поля
    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    #Для принта 
    def __str__(self):
        return self.name

    #Удаление с проверкой на системность, Админ не может самоуничтожится
    def delete(self, *args, **kwargs):
        if self.is_system:
            raise PermissionError("Критическая ошибка: Нельзя удалить системную роль!")
        super().delete(*args, **kwargs)
    #добавление с проверкой на рекурсию в родителях
    def save(self, *args, **kwargs):
        self.full_clean()  
        super().save(*args, **kwargs)



#Декоратор сигналов, читай слушатель событий. Events если угодно как в Ноде
@receiver(pre_delete, sender=CustomRole)
def protect_system_roles(sender, instance, **kwargs):
    if instance.is_system:
        raise PermissionError("Критическая ошибка: Нельзя удалить системную роль через QuerySet!")



# 3 Каталог Разделов

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



# 4 Каталог Действий (FR-5)

class AppPermission(models.Model):
    section = models.ForeignKey(
        AppSection,  #Удалили раздел == удалили действия в нем
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
        constraints = [ #Ограничения- НЕ может быть у нас одного и того же действия в одном и том же разделе..
            models.UniqueConstraint(fields=['section', 'codename'], name='unique_section_action')
        ]

    #Финтифлюшка чисто для красивого вывода: Позывной раздела и действие через двоеточие
    def __str__(self): 
        return f"{self.section.slug}:{self.codename}"



# 5 Матрица прав Роль_x_Действие (Явные ALLOW / DENY)

class RolePermission(models.Model):
    #Список вариантов для админки
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
        constraints = [ #Уникальная связка Роль+Действие = Разрешить/Запретить, низя сделать и allow и deny одному и тому же посту
            models.UniqueConstraint(fields=['role', 'permission'], name='unique_role_permission')
        ]



# 6 Логи Аудита (FR-13, FR-14, FR-15)

class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True) #Тут специально id создаем сами, хотя он и есть в Моедлях по дефолту,нам же нужен BigInt
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_logs',
        verbose_name="Пользователь",
        db_index=True # Мгновенный поиск (читы),по сути индексация базы данных  
        # Если серьезно то строится полноценное Дерево с поиском по сложности O(logN) Чтобы найти запись среди миллиона базе потребуется всего около 20 операций вместо 1 000 000.
        # Из минусов- замедляется Insert-ы и удаления
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

# 7 Чуть не забыл,конечно же - записи пользаков 
class Record(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок записи")
    content = models.TextField(verbose_name="Содержимое записи")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    def __str__(self):
        return self.title
