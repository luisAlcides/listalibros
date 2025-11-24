from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Book, ReadingSession, Category
from .forms import BookForm, ReadingSessionForm, CategoryForm

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
    books = Book.objects.filter(user=request.user).select_related('category').order_by('category__name', '-updated_at')

    if status_filter:
        books = books.filter(status=status_filter)

    # Calculate statistics
    total_books = Book.objects.filter(user=request.user).count()
    completed_books = Book.objects.filter(user=request.user, status='COMPLETED').count()
    reading_books = Book.objects.filter(user=request.user, status='READING').count()

    context = {
        'books': books,
        'current_filter': status_filter,
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
