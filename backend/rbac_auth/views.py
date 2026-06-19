#from django.shortcuts import render ненадо,просто НЕТ

# Create your views here. -Cheers Django now let`s ROCK!
from .models import Record
from .models import RolePermission, CustomRole, AppPermission
from django.utils.dateparse import parse_date
from .models import AuditLog
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .services import calculate_effective_permissions
from .permissions import HasMatrixPermission
from rbac_auth.models import CustomUser

class LoginView(APIView):
    #Рут для входа в систему POST /api/auth/login/
    # Тут рут для незалогиненых будет,ибо это и есть логин
    permission_classes = [] 

    def post(self, request):
        #получаем от юзера все что нужно
        username = request.data.get('username')
        password = request.data.get('password')

        # сверяет пароли сам джанго по бд
        user = authenticate(username=username, password=password) #вся сложная криптография на плечи спецов
        #механизм таков: запрос в бд по юзернейму,находим пароль в базе и сравниваем с присланным который хешируем


        if user is not None:
            # Не буду повторяться в десятый раз: Б А Н
            if user.is_blocked:
                return Response(
                    {"error": "Ваш аккаунт заблокирован суперадмином!"}, 
                    status=status.HTTP_403_FORBIDDEN #вот кстати корректная обработка ошибок подъехала
                )
            
            # Если всё ок берем существующий или создаем новый токен для пользака
            token, created = Token.objects.get_or_create(user=user) #вручную,к счастью,писать не пришлось слава Богу
            
            # фронту верну ответ с токеном и статусом 200-> сомнительно,но окей
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        
        return Response(
            {"error": "Неверный логин или пароль"}, #или в ином случае вас не существует!
            status=status.HTTP_400_BAD_REQUEST 
        )


class MeView(APIView):
    #Рут получения инфы о себе и своих прав GET /api/auth/me/

    # сюда проход только с токеном
    
    def get(self, request):
        user = request.user
        
        effective_permissions = calculate_effective_permissions(user)
        
        return Response({
            "id": user.id,
            "username": user.username,
            "is_blocked": user.is_blocked,
            "permissions": effective_permissions  # Передаем весь твой словарь с allow/deny!
        }, status=status.HTTP_200_OK)
    

class RecordListView(APIView):
    def get_permissions(self): #тут и далее в методах работает перехват запроса и проверка с помощью метода проверки роли
        if self.request.method == 'GET': #ориентируясь на характер запроса
            return [HasMatrixPermission('view_records')] #вызываем метод проверки с определенным действием, тут - для просмотра
        return [HasMatrixPermission('create_records')]#тут для создания записей,целая цепочка внутри!

    def get(self, request):
        # берем все записи из модельки записей
        records = Record.objects.all()
        
        # Из джанго масивов,да в Джейсон благодатный
        data = []
        for r in records:
            data.append({
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        title = request.data.get('title')
        content = request.data.get('content')
        
        if not title or not content:
            return Response({"error": "Заголовок и содержимое обязательны!"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Бум- создали запись
        new_record = Record.objects.create(title=title, content=content)
        
        return Response({
            "id": new_record.id,
            "message": "Запись успешно сохранена в БД!"
        }, status=status.HTTP_201_CREATED)
    

class AuditLogListView(APIView):
    #Рут для просмотра и фильтрации логов GET /api/admin/audit-logs/
    # пускаем только тех у кого есть право 'view_audit'
    def get_permissions(self):
        return [HasMatrixPermission('view_audit')]

    def get(self, request):
        # 1 подготовка к SQL запросу склеиваем джоинами- и опять получаем один запрос побольше,вместо многих маленьких
        #сразу знаем в логах имя юзера из за JOIN-а 
        queryset = AuditLog.objects.all().select_related('user')

        # 2 читаем Query запрос,по ним ориентируемся
        filter_result = request.query_params.get('result')       # allow или deny
        filter_user = request.query_params.get('user_id')        # ID конкретного пользователя
        date_from = request.query_params.get('date_from')        # Дата "С" (ГГГГ-ММ-ДД)
        date_to = request.query_params.get('date_to')            # Дата "По" (ГГГГ-ММ-ДД)

        # Если фронтенд передал фильтр по результату — фильтруем
        if filter_result:
            queryset = queryset.filter(result=filter_result)

        # Если выбран конкретный пользователь — фильтруем по нему
        if filter_user:
            queryset = queryset.filter(user_id=filter_user)

        # Фильтр по диапазону дат
        if date_from:
            queryset = queryset.filter(created_at__date__gte=parse_date(date_from))
        if date_to:
            queryset = queryset.filter(created_at__date__lte=parse_date(date_to))

        # готовим ответ обратно
        logs_data = []
        for log in queryset:
            logs_data.append({
                "id": log.id,
                "username": log.username_snapshot,  # тут важно - читаем записанное имя юзера,пусть тот даже удален
                "action": log.action_codename,
                "result": log.result,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") 
            })

        return Response(logs_data, status=status.HTTP_200_OK)


class MatrixView(APIView):
    #Рут для работы с интерактивной матрицей прав GET — прочесть сетку POST — сохранить изменения кнопочкой
    def get_permissions(self):#хитроумный перехват
        if self.request.method == 'GET':
            return [HasMatrixPermission('view_matrix')]
        return [HasMatrixPermission('save_matrix')]

    def get(self, request):
        # Выкладываем всю матрицу из бд опять применяя шаблон SQL запроса + Джоин,один запрос побольше вместо сотни маленьких
        rules = RolePermission.objects.all().select_related('role', 'permission')
        
        matrix_data = []
        for rule in rules:
            matrix_data.append({
                "id": rule.id,
                "role_id": rule.role_id,
                "permission_id": rule.permission_id,
                "grant": rule.access_type  # 'allow' или 'deny'
            })
        return Response(matrix_data, status=status.HTTP_200_OK)

    def post(self, request):
        # Когда админ нажимает кнопку сохранить, фронтенд присылает массив изменений по идее:
        # [{"role_id": 2, "permission_id": 3, "grant": "allow"}, и т.д]
        changes = request.data.get('changes', []) #извлекаем массив изменений

        for change in changes:# проходимся по ним
            role_id = change.get('role_id')
            permission_id = change.get('permission_id')
            grant = change.get('grant') # 'allow', 'deny' или 'none'

            if grant in ['allow', 'deny']:
                # Чуть магии Джанго update_or_create сама ищет запись в бдшке-модельке
                # Найдет - обновит существующую,не найдет грубо говоря создаст 
                RolePermission.objects.update_or_create(
                    role_id=role_id,
                    permission_id=permission_id,
                    defaults={'access_type': grant}
                )
            elif grant in ['none', 'inherit']:
                # Админ убрал галочку,тогда мы удаляем запись
                RolePermission.objects.filter(role_id=role_id, permission_id=permission_id).delete()
                #функция рассчета должна пойти искать права у родителей роли,если есть конечно.. ну родители в смысле

        return Response({"message": "Матрица прав успешно сохранена!"}, status=status.HTTP_200_OK)

class AdminUserListView(APIView):

    #Рут для Экрана Пользователей (GET /api/admin/users/)
    def get_permissions(self):
        return [HasMatrixPermission('manage_roles')]

    def get(self, request, pk=None):
        # Если в URL передан ID (например, /api/admin/users/5/)
        # То админ открыл карточку конкретного юзера или нажал "Проверить доступ"
        if pk is not None:
            try:
                user = CustomUser.objects.prefetch_related('roles').get(pk=pk)
                user_roles = [role.name for role in user.roles.all()]
                
                return Response({
                    "id": user.id,
                    "username": user.username,
                    "is_blocked": user.is_blocked,
                    "roles": user_roles,
                    # рассчитали права конкретного человека
                    "effective_permissions": calculate_effective_permissions(user)
                }, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Если ID нет (просто /api/admin/users/) -  То просто легкий список всех
        users = CustomUser.objects.all().prefetch_related('roles')
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "is_blocked": user.is_blocked,
                "roles": [role.name for role in user.roles.all()],
            })
        return Response(users_data, status=status.HTTP_200_OK)
