from django import forms
from .models import Book, ReadingSession, Category


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'total_pages', 'status', 'category', 'cover_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Cien años de soledad'}),
            'author': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Gabriel García Márquez'}),
            'total_pages': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'cover_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://ejemplo.com/portada.jpg'}),
        }


class ReadingSessionForm(forms.ModelForm):
    class Meta:
        model = ReadingSession
        fields = ['end_page', 'duration_minutes', 'date', 'notes']
        labels = {
            'end_page': '¿Hasta qué página llegaste?',
            'duration_minutes': 'Tiempo (minutos)',
            'date': 'Fecha',
            'notes': 'Notas (opcional)',
        }
        widgets = {
            'end_page': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'placeholder': 'Ej: 145'}),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Minutos (admite decimales)',
                'step': 'any',
                'min': '0',
            }),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea', 'placeholder': '¿Qué te pareció esta sesión?'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Ficción, Ensayo, Poesía…'}),
        }
