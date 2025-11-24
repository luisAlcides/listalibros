from django import forms
from .models import Book, ReadingSession, Category

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'total_pages', 'status', 'category', 'cover_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'author': forms.TextInput(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'total_pages': forms.NumberInput(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'status': forms.Select(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'category': forms.Select(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'cover_url': forms.URLInput(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500', 'placeholder': 'https://example.com/image.jpg'}),
        }

class ReadingSessionForm(forms.ModelForm):
    class Meta:
        model = ReadingSession
        fields = ['end_page', 'duration_minutes', 'date', 'notes']
        labels = {
            'end_page': '¿Hasta qué página llegaste?',
        }
        widgets = {
            'end_page': forms.NumberInput(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500', 'placeholder': 'Minutos'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500'}),
        }
