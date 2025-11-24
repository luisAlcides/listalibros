from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Book, ReadingSession, Category
from .forms import BookForm, ReadingSessionForm, CategoryForm

def book_list(request):
    status_filter = request.GET.get('status')
    books = Book.objects.select_related('category').all().order_by('category__name', '-updated_at')

    if status_filter:
        books = books.filter(status=status_filter)

    context = {
        'books': books,
        'current_filter': status_filter
    }
    return render(request, 'books/book_list.html', context)

def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Libro agregado exitosamente.')
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/add_book.html', {'form': form})

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

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        form = ReadingSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.book = book
            
            # Basic validation
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
        # Pre-fill with next logical page if possible, or just empty
        form = ReadingSessionForm()

    sessions = book.readingsession_set.all().order_by('-date', '-id')
    
    context = {
        'book': book,
        'form': form,
        'sessions': sessions
    }
    return render(request, 'books/book_detail.html', context)

def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Libro eliminado.')
        return redirect('book_list')
    return redirect('book_detail', pk=pk)
