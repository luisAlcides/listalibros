from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db import models
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Book, ReadingSession, Category
from .forms import BookForm, ReadingSessionForm, CategoryForm


def _format_reading_minutes(minutes):
    """Format total minutes like Book.total_time_read (m / h m)."""
    if minutes is None:
        m = Decimal('0')
    else:
        m = Decimal(str(minutes))
    if m == 0:
        return '0m'

    def fmt_mins(x):
        x = x.normalize()
        if x == x.to_integral():
            return str(int(x))
        return format(x, 'f').rstrip('0').rstrip('.')

    hours = int(m // 60)
    mins = m % 60
    if hours > 0:
        return f'{hours}h {fmt_mins(mins)}m'
    return f'{fmt_mins(mins)}m'


def _sum_minutes_for_user(user, start_d, end_d):
    total = ReadingSession.objects.filter(
        book__user=user,
        date__gte=start_d,
        date__lte=end_d,
    ).aggregate(t=Sum('duration_minutes'))['t']
    if total is None:
        return Decimal('0')
    return Decimal(str(total))


def _pct_change(current, previous):
    if previous <= 0:
        return None
    return float((current - previous) / previous * 100)


def _signed_delta_display(delta_minutes):
    if delta_minutes == 0:
        return 'sin cambio', 'text-gray-400'
    sign = '+' if delta_minutes > 0 else ''
    label = f'{sign}{_format_reading_minutes(abs(delta_minutes))}'
    if delta_minutes > 0:
        return label, 'text-green-400'
    return label, 'text-red-400'


_MESES = (
    '',
    'enero',
    'febrero',
    'marzo',
    'abril',
    'mayo',
    'junio',
    'julio',
    'agosto',
    'septiembre',
    'octubre',
    'noviembre',
    'diciembre',
)

_MESES_CORTO = (
    '',
    'ene',
    'feb',
    'mar',
    'abr',
    'may',
    'jun',
    'jul',
    'ago',
    'sep',
    'oct',
    'nov',
    'dic',
)


def _month_label_es(d: date) -> str:
    return f'{_MESES[d.month]} {d.year}'.capitalize()


def _date_range_label_es(start: date, end: date) -> str:
    if start == end:
        return f'{start.day} {_MESES_CORTO[start.month]} {start.year}'
    if start.year == end.year and start.month == end.month:
        return f'{start.day}–{end.day} {_MESES_CORTO[end.month]} {end.year}'
    if start.year == end.year:
        return f'{start.day} {_MESES_CORTO[start.month]} – {end.day} {_MESES_CORTO[end.month]} {end.year}'
    return f'{start.day} {_MESES_CORTO[start.month]} {start.year} – {end.day} {_MESES_CORTO[end.month]} {end.year}'


@login_required
def reading_stats(request):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    monday_this = today - timedelta(days=today.weekday())
    sunday_this = monday_this + timedelta(days=6)
    monday_prev = monday_this - timedelta(days=7)
    sunday_prev = monday_this - timedelta(days=1)

    first_this_month = today.replace(day=1)
    _, last_day_m = monthrange(today.year, today.month)
    last_this_month = today.replace(day=last_day_m)

    if first_this_month.month == 1:
        prev_m_year = first_this_month.year - 1
        prev_m_month = 12
    else:
        prev_m_year = first_this_month.year
        prev_m_month = first_this_month.month - 1

    first_prev_month = date(prev_m_year, prev_m_month, 1)
    _, last_prev_m = monthrange(prev_m_year, prev_m_month)
    last_prev_month = date(prev_m_year, prev_m_month, last_prev_m)

    today_m = _sum_minutes_for_user(request.user, today, today)
    yesterday_m = _sum_minutes_for_user(request.user, yesterday, yesterday)
    week_m = _sum_minutes_for_user(request.user, monday_this, sunday_this)
    week_prev_m = _sum_minutes_for_user(request.user, monday_prev, sunday_prev)
    month_m = _sum_minutes_for_user(request.user, first_this_month, last_this_month)
    month_prev_m = _sum_minutes_for_user(request.user, first_prev_month, last_prev_month)

    day_delta = today_m - yesterday_m
    week_delta = week_m - week_prev_m
    month_delta = month_m - month_prev_m

    day_delta_text, day_delta_class = _signed_delta_display(day_delta)
    week_delta_text, week_delta_class = _signed_delta_display(week_delta)
    month_delta_text, month_delta_class = _signed_delta_display(month_delta)

    context = {
        'today_display': _format_reading_minutes(today_m),
        'yesterday_display': _format_reading_minutes(yesterday_m),
        'day_delta_text': day_delta_text,
        'day_delta_class': day_delta_class,
        'day_pct': _pct_change(today_m, yesterday_m),

        'week_current_display': _format_reading_minutes(week_m),
        'week_previous_display': _format_reading_minutes(week_prev_m),
        'week_delta_text': week_delta_text,
        'week_delta_class': week_delta_class,
        'week_pct': _pct_change(week_m, week_prev_m),
        'week_range_label': _date_range_label_es(monday_this, sunday_this),
        'week_prev_range_label': _date_range_label_es(monday_prev, sunday_prev),

        'month_current_display': _format_reading_minutes(month_m),
        'month_previous_display': _format_reading_minutes(month_prev_m),
        'month_delta_text': month_delta_text,
        'month_delta_class': month_delta_class,
        'month_pct': _pct_change(month_m, month_prev_m),
        'month_label': _month_label_es(first_this_month),
        'prev_month_label': _month_label_es(first_prev_month),
    }
    return render(request, 'books/reading_stats.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('book_list')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('book_list')
    else:
        form = UserCreationForm()
    return render(request, 'books/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('book_list')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido {username}!')
                return redirect('book_list')
    else:
        form = AuthenticationForm()
    return render(request, 'books/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada.')
    return redirect('login')

@login_required
def book_list(request):
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q', '')
    
    books = Book.objects.filter(user=request.user).select_related('category').order_by('category__name', '-updated_at')

    if status_filter:
        books = books.filter(status=status_filter)
    
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) | 
            Q(author__icontains=search_query)
        )

    # Calculate statistics
    total_books = Book.objects.filter(user=request.user).count()
    completed_books = Book.objects.filter(user=request.user, status='COMPLETED').count()
    reading_books = Book.objects.filter(user=request.user, status='READING').count()

    context = {
        'books': books,
        'current_filter': status_filter,
        'search_query': search_query,
        'total_books': total_books,
        'completed_books': completed_books,
        'reading_books': reading_books,
    }
    return render(request, 'books/book_list.html', context)

@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user
            book.save()
            messages.success(request, 'Libro agregado exitosamente.')
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/add_book.html', {'form': form})

@login_required
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Libro actualizado exitosamente.')
            return redirect('book_detail', pk=pk)
    else:
        form = BookForm(instance=book)
    
    return render(request, 'books/edit_book.html', {'form': form, 'book': book})

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría agregada.')
            return redirect('add_book')
    else:
        form = CategoryForm()
    return render(request, 'books/add_category.html', {'form': form})

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ReadingSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.book = book
            
            if session.end_page > book.total_pages:
                messages.error(request, f'La página no puede ser mayor al total ({book.total_pages}).')
            else:
                session.save()
                
                # Update book status
                if session.end_page >= book.total_pages:
                    book.status = 'COMPLETED'
                    book.save()
                    messages.success(request, '¡Felicidades! Has terminado el libro.')
                elif book.status == 'PENDING' and session.end_page > 0:
                    book.status = 'READING'
                    book.save()
                    messages.success(request, 'Progreso registrado.')
                else:
                    messages.success(request, 'Progreso registrado.')
                
            return redirect('book_detail', pk=pk)
    else:
        form = ReadingSessionForm()

    sessions = book.readingsession_set.all().order_by('-date', '-id')
    
    context = {
        'book': book,
        'form': form,
        'sessions': sessions
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Libro eliminado.')
        return redirect('book_list')
    return redirect('book_detail', pk=pk)

@login_required
def edit_session(request, pk):
    session = get_object_or_404(ReadingSession, pk=pk)
    book = session.book
    
    # Verify user owns this book
    if book.user != request.user:
        messages.error(request, 'No tienes permiso para editar esta sesión.')
        return redirect('book_list')
    
    if request.method == 'POST':
        form = ReadingSessionForm(request.POST, instance=session)
        if form.is_valid():
            new_session = form.save(commit=False)
            if new_session.end_page > book.total_pages:
                messages.error(request, f'La página no puede ser mayor al total ({book.total_pages}).')
            else:
                new_session.save()
                
                # Recalculate book status based on the latest progress
                max_page = book.readingsession_set.aggregate(max_page=models.Max('end_page'))['max_page'] or 0
                
                if max_page >= book.total_pages:
                    book.status = 'COMPLETED'
                elif max_page > 0:
                    book.status = 'READING'
                else:
                    book.status = 'PENDING'
                book.save()
                
                messages.success(request, 'Sesión actualizada.')
                return redirect('book_detail', pk=book.pk)
    else:
        form = ReadingSessionForm(instance=session)
    
    return render(request, 'books/edit_session.html', {'form': form, 'session': session, 'book': book})

@login_required
def delete_session(request, pk):
    session = get_object_or_404(ReadingSession, pk=pk)
    book = session.book
    
    # Verify user owns this book
    if book.user != request.user:
        messages.error(request, 'No tienes permiso para eliminar esta sesión.')
        return redirect('book_list')
    
    book_pk = book.pk
    if request.method == 'POST':
        session.delete()
        
        # Recalculate status
        book = Book.objects.get(pk=book_pk)
        max_page = book.readingsession_set.aggregate(max_page=models.Max('end_page'))['max_page'] or 0
        
        if max_page >= book.total_pages:
            book.status = 'COMPLETED'
        elif max_page > 0:
            book.status = 'READING'
        else:
            book.status = 'PENDING'
        book.save()
        
        messages.success(request, 'Sesión eliminada.')
    return redirect('book_detail', pk=book_pk)


def manifest(request):
    """Web App Manifest: usa el icono SVG de libro de la app."""
    book_icon = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
        "viewBox='0 0 512 512'%3E%3Crect width='512' height='512' rx='112' "
        "fill='%230b1020'/%3E%3Cpath d='M142 104h173a58 58 0 0 1 58 58v239H181a39 "
        "39 0 0 1-39-39V104Z' fill='%236366f1'/%3E%3Cpath d='M142 104h156a58 58 0 "
        "0 1 58 58v221H181a39 39 0 0 1-39-39V104Z' fill='%238b5cf6'/%3E%3Cpath "
        "d='M176 138h122a34 34 0 0 1 34 34v181H181a39 39 0 0 0-39 39V138h34Z' "
        "fill='%23f8fafc' fill-opacity='.92'/%3E%3Cpath d='M205 205h84M205 256h102M205 "
        "307h67' stroke='%234f46e5' stroke-width='18' stroke-linecap='round'/%3E%3C/svg%3E"
    )
    data = {
        'name': 'BookTracker',
        'short_name': 'BookTracker',
        'description': 'Tu biblioteca personal de libros.',
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#070914',
        'theme_color': '#0b1020',
        'icons': [
            {
                'src': book_icon,
                'sizes': '512x512',
                'type': 'image/svg+xml',
                'purpose': 'any maskable',
            },
            {
                'src': book_icon,
                'sizes': '192x192',
                'type': 'image/svg+xml',
                'purpose': 'any maskable',
            },
        ],
    }
    return JsonResponse(
        data,
        json_dumps_params={'ensure_ascii': False},
        content_type='application/manifest+json; charset=utf-8',
    )
