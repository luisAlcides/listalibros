from django.core.management.base import BaseCommand
from books.models import Book, Category

class Command(BaseCommand):
    help = 'Seeds the database with initial books'

    def handle(self, *args, **kwargs):
        # Create categories
        categories = {
            "FINANCE": "Finanzas y Riqueza",
            "PRODUCTIVITY": "Productividad y Eficiencia",
            "MINDSET": "Mentalidad y Estoicismo",
            "STRATEGY": "Estrategia y Poder",
            "BIOGRAPHY": "Biografías y Negocios"
        }
        
        cat_objs = {}
        for key, name in categories.items():
            cat, created = Category.objects.get_or_create(name=name)
            cat_objs[key] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))

        books_data = [
            # Finance
            ("La Psicología del Dinero", "Morgan Housel", "FINANCE", 256),
            ("El hombre más rico de Babilonia", "George S. Clason", "FINANCE", 144),
            ("La vía rápida del millonario", "MJ DeMarco", "FINANCE", 336),
            ("Padre Rico, Padre Pobre", "Robert Kiyosaki", "FINANCE", 336),
            ("El camino simple hacia la riqueza", "JL Collins", "FINANCE", 286),
            ("Te enseñaré a ser rico", "Ramit Sethi", "FINANCE", 352),
            ("El millonario de la puerta de al lado", "Thomas J. Stanley", "FINANCE", 258),
            ("Los secretos de la mente millonaria", "T. Harv Eker", "FINANCE", 224),
            ("Dinero: Domina el juego", "Tony Robbins", "FINANCE", 688),
            ("La bolsa o la vida", "Vicki Robin & Joe Dominguez", "FINANCE", 400),
            ("Un paso por delante de Wall Street", "Peter Lynch", "FINANCE", 304),
            ("El inversor inteligente", "Benjamin Graham", "FINANCE", 640),
            ("El patrón Bitcoin", "Saifedean Ammous", "FINANCE", 304),
            
            # Productivity
            ("Hábitos Atómicos", "James Clear", "PRODUCTIVITY", 320),
            ("Céntrate (Deep Work)", "Cal Newport", "PRODUCTIVITY", 304),
            ("Esencialismo", "Greg McKeown", "PRODUCTIVITY", 272),
            ("El Principio 80/20", "Richard Koch", "PRODUCTIVITY", 336),
            ("Hazlo tan bien que no puedan ignorarte", "Cal Newport", "PRODUCTIVITY", 304),
            ("El poder de los hábitos", "Charles Duhigg", "PRODUCTIVITY", 416),
            ("Organízate con eficacia (GTD)", "David Allen", "PRODUCTIVITY", 352),
            ("Algoritmos para la vida cotidiana", "Brian Christian & Tom Griffiths", "PRODUCTIVITY", 368),
            ("La semana laboral de 4 horas", "Tim Ferriss", "PRODUCTIVITY", 416),

            # Mindset
            ("No me puedes lastimar (Can't Hurt Me)", "David Goggins", "MINDSET", 364),
            ("Meditaciones", "Marco Aurelio", "MINDSET", 256),
            ("El obstáculo es el camino", "Ryan Holiday", "MINDSET", 224),
            ("El ego es el enemigo", "Ryan Holiday", "MINDSET", 256),
            ("Piense y Hágase Rico", "Napoleon Hill", "MINDSET", 238),
            ("El hombre en busca de sentido", "Viktor Frankl", "MINDSET", 160),
            ("Maestría", "Robert Greene", "MINDSET", 352),
            ("Mindset: La actitud del éxito", "Carol Dweck", "MINDSET", 320),
            ("Los seis pilares de la autoestima", "Nathaniel Branden", "MINDSET", 368),

            # Strategy
            ("Rompe la barrera del no", "Chris Voss", "STRATEGY", 288),
            ("Las 48 leyes del poder", "Robert Greene", "STRATEGY", 480),
            ("Cómo ganar amigos e influir sobre las personas", "Dale Carnegie", "STRATEGY", 288),
            ("Influencia", "Robert Cialdini", "STRATEGY", 320),
            ("El arte de la guerra", "Sun Tzu", "STRATEGY", 128),
            ("Conversaciones cruciales", "Kerry Patterson", "STRATEGY", 256),
            ("Jugar para ganar (Skin in the Game)", "Nassim Nicholas Taleb", "STRATEGY", 304),
            ("Antifragil", "Nassim Nicholas Taleb", "STRATEGY", 544),

            # Biography/Business
            ("Principios", "Ray Dalio", "BIOGRAPHY", 592),
            ("Cero a Uno", "Peter Thiel", "BIOGRAPHY", 224),
            ("El Almanaque de Naval Ravikant", "Eric Jorgenson", "BIOGRAPHY", 244),
            ("Pensar rápido, pensar despacio", "Daniel Kahneman", "BIOGRAPHY", 499),
            ("Steve Jobs", "Walter Isaacson", "BIOGRAPHY", 656),
            ("Elon Musk", "Walter Isaacson", "BIOGRAPHY", 688),
            ("Nunca te pares (Shoe Dog)", "Phil Knight", "BIOGRAPHY", 400),
            ("Lo difícil de las cosas difíciles", "Ben Horowitz", "BIOGRAPHY", 304),
            ("De bueno a excelente (Good to Great)", "Jim Collins", "BIOGRAPHY", 320),
            ("Sapiens: De animales a dioses", "Yuval Noah Harari", "BIOGRAPHY", 496),
            ("Economía básica", "Thomas Sowell", "BIOGRAPHY", 704),
        ]

        self.stdout.write('Seeding books...')
        
        for title, author, cat_key, pages in books_data:
            category = cat_objs.get(cat_key)
            if not Book.objects.filter(title=title).exists():
                Book.objects.create(
                    title=title,
                    author=author,
                    category=category,
                    total_pages=pages,
                    status='PENDING'
                )
                self.stdout.write(self.style.SUCCESS(f'Created book: {title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Book already exists: {title}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded books'))
