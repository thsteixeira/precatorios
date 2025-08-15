from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Create a default admin user for testing'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Username for the admin user')
        parser.add_argument('--password', type=str, default='admin123', help='Password for the admin user')
        parser.add_argument('--email', type=str, default='admin@precatorios.com', help='Email for the admin user')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'Usuário "{username}" já existe!')
                )
                return

            # Create the superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='Administrador',
                last_name='Sistema'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Superusuário "{username}" criado com sucesso!')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Username: {username}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Password: {password}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Email: {email}')
            )
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao criar usuário: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro inesperado: {e}')
            )
