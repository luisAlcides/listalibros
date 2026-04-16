from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Book, Category, ReadingSession
from .serializers import BookSerializer, CategorySerializer, ReadingSessionSerializer, refresh_book_status


def api_usage_guide(request):
    """GET /api/ — Resumen de uso de la API (misma base que el resto de rutas)."""

    def abs_url(suffix):
        return request.build_absolute_uri(f'/api/{suffix.lstrip("/")}')

    payload = {
        'titulo': 'BookTracker API',
        'descripcion': (
            'Misma base URL que el resto de endpoints: todo bajo /api/. '
            'Requiere usuario autenticado salvo la obtención de token.'
        ),
        'autenticacion': {
            'token': {
                'pasos': [
                    'POST a la URL "obtener_token" con username y password (JSON o formulario).',
                    'Guarda el valor de "token" en el cliente.',
                    'En cada petición envía el encabezado Authorization: Token <token>.',
                ],
                'obtener_token': {
                    'url': abs_url('auth/token/'),
                    'metodo': 'POST',
                    'cuerpo_json_ejemplo': {'username': 'tu_usuario', 'password': 'tu_contraseña'},
                },
            },
            'alternativas': [
                'Sesión (cookies) si ya iniciaste sesión en el navegador.',
                'Basic Auth (Authorization: Basic …) con usuario y contraseña.',
            ],
        },
        'cors': (
            'Si llamas desde un navegador en otro dominio, configura CORS_ALLOWED_ORIGINS '
            'o CORS_ALLOW_ALL_ORIGINS en el servidor (ver settings).'
        ),
        'recursos': [
            {
                'nombre': 'Categorías',
                'url': abs_url('categories/'),
                'metodos': ['GET', 'POST'],
                'detalle': abs_url('categories/{id}/'),
                'detalle_metodos': ['GET', 'PUT', 'PATCH', 'DELETE'],
            },
            {
                'nombre': 'Libros (del usuario autenticado)',
                'url': abs_url('books/'),
                'metodos': ['GET', 'POST'],
                'query': {'status': 'PENDING | READING | COMPLETED', 'q': 'búsqueda en título o autor'},
                'crear_json_ejemplo': {
                    'title': 'Título',
                    'author': 'Autor',
                    'total_pages': 300,
                    'status': 'PENDING',
                    'category': 1,
                    'cover_url': 'https://…',
                },
                'detalle': abs_url('books/{id}/'),
                'detalle_metodos': ['GET', 'PUT', 'PATCH', 'DELETE'],
            },
            {
                'nombre': 'Sesiones de lectura de un libro',
                'url': abs_url('books/{id}/sessions/'),
                'metodos': ['GET', 'POST'],
                'crear_json_ejemplo': {
                    'end_page': 120,
                    'duration_minutes': '30',
                    'date': '2026-04-15',
                    'notes': '',
                },
            },
            {
                'nombre': 'Sesión (por id)',
                'url': abs_url('sessions/{id}/'),
                'metodos': ['GET', 'PUT', 'PATCH', 'DELETE'],
            },
        ],
        'ejemplo_powershell': (
            '$r = Invoke-RestMethod -Uri "'
            + abs_url('auth/token/')
            + '" -Method Post -Body (@{ username="..."; password="..." } | ConvertTo-Json) '
            '-ContentType "application/json"; '
            '$h = @{ Authorization = "Token $($r.token)" }; '
            'Invoke-RestMethod -Uri "'
            + abs_url('books/')
            + '" -Headers $h'
        ),
        'script_repo': 'scripts/add-book-from-outside.ps1',
    }
    return JsonResponse(payload, json_dumps_params={'ensure_ascii': False, 'indent': 2})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer

    def get_queryset(self):
        qs = (
            Book.objects.filter(user=self.request.user)
            .select_related('category')
            .order_by('category__name', '-updated_at')
        )
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        q = self.request.query_params.get('q', '').strip()
        if q:
            from django.db.models import Q

            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q))
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'])
    def sessions(self, request, pk=None):
        book = self.get_object()
        if request.method == 'GET':
            sessions = book.readingsession_set.all().order_by('-date', '-id')
            return Response(ReadingSessionSerializer(sessions, many=True).data)
        serializer = ReadingSessionSerializer(data=request.data, context={'book': book})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        book.refresh_from_db()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReadingSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingSessionSerializer
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return ReadingSession.objects.filter(book__user=self.request.user).select_related('book')

    def perform_destroy(self, instance):
        book = instance.book
        super().perform_destroy(instance)
        refresh_book_status(book)
