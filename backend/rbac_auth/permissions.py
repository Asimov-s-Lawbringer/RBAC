from rest_framework.permissions import BasePermission
from .services import calculate_effective_permissions
from .models import AuditLog

#Класс проверки прав вместо функции чтобы избежать if elso-в множественных, иначе говоря чайник с функцией.. логирования 
class HasMatrixPermission(BasePermission): #кастомная проверка- наследуемся и пишем хэс пермишн без ошЫбок
    def __init__(self, required_perm=None):
        # передаем какое право нужно для этого рута (к примеру вот 'view_records')
        self.required_perm = required_perm

    def has_permission(self, request, view):
        # Читерство? Бан.Оскорбления? Бан.Без логина? Расстрел,потом Бан
        if not request.user or not request.user.is_authenticated:
            return False

        # Умом? Умом, пользуемся уже написаной функцией и получаем все права пользака
        user_perms = calculate_effective_permissions(request.user)

        # Смотрим есть ли у него такое право и 'allow" ли оно? get вернет none по идее если не найдет ничего
        is_allowed = user_perms.get(self.required_perm) == 'allow'
        result_text = 'allow' if is_allowed else 'deny'

        #Автологи,ее!
        
        AuditLog.objects.create(
            user=request.user,
            action_codename=self.required_perm,
            result=result_text
        )

        # Возвращаем True для допуска или False DRF сам выплюнет ошибку Форбиден, Запрещен Доступ тобишь
        return is_allowed
