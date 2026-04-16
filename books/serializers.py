from django.db.models import Max
from rest_framework import serializers

from .models import Book, Category, ReadingSession


def refresh_book_status(book):
    max_page = book.readingsession_set.aggregate(m=Max('end_page'))['m'] or 0
    if max_page >= book.total_pages:
        book.status = 'COMPLETED'
    elif max_page > 0:
        book.status = 'READING'
    else:
        book.status = 'PENDING'
    book.save(update_fields=['status', 'updated_at'])


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class ReadingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingSession
        fields = ['id', 'book', 'end_page', 'duration_minutes', 'date', 'notes']
        read_only_fields = ['id', 'book']

    def validate(self, attrs):
        book = self.context.get('book') or self.instance.book
        end_page = attrs.get('end_page', self.instance.end_page if self.instance else None)
        if end_page is not None and end_page > book.total_pages:
            raise serializers.ValidationError(
                {'end_page': f'No puede ser mayor al total de páginas ({book.total_pages}).'}
            )
        return attrs

    def create(self, validated_data):
        book = self.context['book']
        session = ReadingSession.objects.create(book=book, **validated_data)
        refresh_book_status(book)
        return session

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        refresh_book_status(instance.book)
        return instance


class BookSerializer(serializers.ModelSerializer):
    pages_read = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    pages_remaining = serializers.IntegerField(read_only=True)
    total_time_read = serializers.CharField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'total_pages',
            'status',
            'category',
            'category_name',
            'cover_url',
            'created_at',
            'updated_at',
            'pages_read',
            'progress_percentage',
            'pages_remaining',
            'total_time_read',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_total_pages(self, value):
        if value < 0:
            raise serializers.ValidationError('Debe ser mayor o igual a 0.')
        return value
