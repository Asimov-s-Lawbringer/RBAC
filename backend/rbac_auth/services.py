from .models import RolePermission, CustomRole


def merge_access(current, new):
    """FR-24: явный deny всегда побеждает allow при конфликте."""
    if new == 'deny' or current == 'deny':
        return 'deny'
    if new == 'allow' or current == 'allow':
        return 'allow'
    return new or current


#Главная функия собирающая все права пользователя
def calculate_effective_permissions(user):

    # В бане - значит нет прав,впрочем,как и всегда
    if user.is_blocked or not user.is_active:
        return {}

    # Сюда итоговые права,словарик
    effective_perms = {}

    # Берем все роли пользака сейчас
    user_roles = user.roles.all() #кстати объект Квери Сета за авторством Джанго,читай набросок запроса SQL в БД
    #"ягодки" т.е запросы пойдут в цикле ниже

    # Теперь идем к его родителям 
    for start_role in user_roles:
        role_chain = []
        current_role = start_role
        
        # Идем перебирая родителей по аналогии с clean() кстати. Идем снизу!
        while current_role is not None:
            role_chain.append(current_role)
            current_role = current_role.parent
            
        #Смотрим на ситуацию "под другим углом" хехе, ну то есть от Древнейшего родителя к младшему сыну 
        role_chain.reverse()

        # Берем роль каждую,для каждой смотрим разрешения
        for role in role_chain:
            # Достаем все правила для конкретной роли из Матрицы РольxРазрешение см. в fixtures для наглядного вида кстати
            rules = RolePermission.objects.filter(role=role).select_related('permission', 'permission__section') #иннер джоин 
            #смортим RolePermission и AppPermission и AppSection
            
            for rule in rules:
                perm_key = rule.permission.codename
                effective_perms[perm_key] = merge_access(
                    effective_perms.get(perm_key),
                    rule.access_type,
                )

    return effective_perms

#P.s сколько запросов делает Функция в бд?  user.roles.all() и его цикл, RolePermission.objects.filter() тут для каждой роли по запросу в цикле