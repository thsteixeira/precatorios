from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from precapp.models import Cliente

class Command(BaseCommand):
    help = 'Update priority status for clients over 60 years old'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--age-limit',
            type=int,
            default=60,
            help='Age limit for priority (default: 60 years)',
        )
    
    def handle(self, *args, **options):
        age_limit = options['age_limit']
        
        # Calculate date for the age limit (e.g., 60 years ago)
        cutoff_date = date.today() - timedelta(days=age_limit*365.25)
        
        # Find clients born before this date (older than age_limit)
        clients_over_age = Cliente.objects.filter(
            nascimento__lt=cutoff_date,
            prioridade=False  # Only update those not already prioritized
        )
        
        count = clients_over_age.count()
        
        if options['dry_run']:
            self.stdout.write(f"DRY RUN: Would update {count} clients over {age_limit} years old to priority status")
            if count > 0:
                self.stdout.write("\nClients that would be updated:")
                for client in clients_over_age[:10]:  # Show first 10
                    age = (date.today() - client.nascimento).days // 365
                    self.stdout.write(f"  - {client.nome} (CPF: {client.cpf}, Age: {age} years)")
                if count > 10:
                    self.stdout.write(f"  ... and {count - 10} more clients")
            else:
                self.stdout.write("No clients found that need priority update.")
        else:
            if count > 0:
                updated = clients_over_age.update(prioridade=True)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {updated} clients over {age_limit} years old to priority status')
                )
                
                # Show some examples of updated clients
                updated_clients = Cliente.objects.filter(
                    nascimento__lt=cutoff_date,
                    prioridade=True
                )[:5]
                
                self.stdout.write("\nSome updated clients:")
                for client in updated_clients:
                    age = (date.today() - client.nascimento).days // 365
                    self.stdout.write(f"  - {client.nome} (CPF: {client.cpf}, Age: {age} years)")
            else:
                self.stdout.write(
                    self.style.WARNING('No clients found that need priority update.')
                )
