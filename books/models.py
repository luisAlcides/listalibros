from django.db import models
from django.utils import timezone

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
        return self.readingsession_set.aggregate(total=models.Sum('pages_read'))['total'] or 0

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
        minutes = self.readingsession_set.aggregate(total=models.Sum('duration_minutes'))['total'] or 0
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

class ReadingSession(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    pages_read = models.IntegerField(help_text="Páginas leídas en esta sesión")
    duration_minutes = models.IntegerField(default=0, help_text="Tiempo leído en minutos")
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.book.title} - {self.pages_read} págs - {self.date}"
