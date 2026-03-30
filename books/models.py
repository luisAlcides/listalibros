from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Book(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('READING', 'Leyendo'),
        ('COMPLETED', 'Terminado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    total_pages = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    cover_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def pages_read(self):
        # Return the highest end_page from sessions, or 0 if no sessions
        return self.readingsession_set.aggregate(max_page=models.Max('end_page'))['max_page'] or 0

    @property
    def progress_percentage(self):
        if self.total_pages == 0:
            return 0
        return min(100, int((self.pages_read / self.total_pages) * 100))

    @property
    def pages_remaining(self):
        return max(0, self.total_pages - self.pages_read)

    @property
    def total_time_read(self):
        raw = self.readingsession_set.aggregate(total=models.Sum('duration_minutes'))['total']
        if raw is None:
            minutes = Decimal('0')
        else:
            minutes = Decimal(str(raw))
        if minutes == 0:
            return '0m'

        def fmt_mins(m):
            m = m.normalize()
            if m == m.to_integral():
                return str(int(m))
            return format(m, 'f').rstrip('0').rstrip('.')

        hours = int(minutes // 60)
        mins = minutes % 60
        if hours > 0:
            return f'{hours}h {fmt_mins(mins)}m'
        return f'{fmt_mins(mins)}m'

class ReadingSession(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    end_page = models.IntegerField(help_text="Página hasta la que llegaste")
    duration_minutes = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text='Tiempo leído en minutos (admite decimales, p. ej. 12,5)',
    )
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.book.title} - Pág {self.end_page} - {self.date}"
