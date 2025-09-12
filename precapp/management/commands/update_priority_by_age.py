from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from precapp.models import Cliente

class Command(BaseCommand):
    help = 'Update priority status for living clients over 60 years old and remove priority from deceased clients'
    
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
        # Exclude deceased clients from getting priority status
        clients_over_age = Cliente.objects.filter(
            nascimento__lt=cutoff_date,
            prioridade=False,  # Only update those not already prioritized
            falecido=False     # Exclude deceased clients
        )
        
        # Find deceased clients who currently have priority and should lose it
        deceased_with_priority = Cliente.objects.filter(
            prioridade=True,
            falecido=True
        )
        
        count = clients_over_age.count()
        deceased_count = deceased_with_priority.count()
        
        if options['dry_run']:
            self.stdout.write(f"DRY RUN: Would update {count} clients over {age_limit} years old to priority status")
            if deceased_count > 0:
                self.stdout.write(f"DRY RUN: Would remove priority from {deceased_count} deceased clients")
                
            if count > 0:
                self.stdout.write("\nClients that would get priority:")
                for client in clients_over_age[:10]:  # Show first 10
                    age = (date.today() - client.nascimento).days // 365
                    self.stdout.write(f"  - {client.nome} (CPF: {client.cpf}, Age: {age} years)")
                if count > 10:
                    self.stdout.write(f"  ... and {count - 10} more clients")
            
            if deceased_count > 0:
                self.stdout.write("\nDeceased clients that would lose priority:")
                for client in deceased_with_priority[:5]:  # Show first 5
                    self.stdout.write(f"  - {client.nome} (CPF: {client.cpf})")
                if deceased_count > 5:
                    self.stdout.write(f"  ... and {deceased_count - 5} more deceased clients")
                    
            if count == 0 and deceased_count == 0:
                self.stdout.write("No clients found that need priority updates.")
        else:
            updated_to_priority = 0
            removed_from_priority = 0
            
            # Update living clients over age limit to priority
            if count > 0:
                updated_to_priority = clients_over_age.update(prioridade=True)
                
            # Remove priority from deceased clients
            if deceased_count > 0:
                removed_from_priority = deceased_with_priority.update(prioridade=False)
            
            # Display results
            if updated_to_priority > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {updated_to_priority} living clients over {age_limit} years old to priority status')
                )
            
            if removed_from_priority > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully removed priority status from {removed_from_priority} deceased clients')
                )
            
            if updated_to_priority == 0 and removed_from_priority == 0:
                self.stdout.write(
                    self.style.WARNING('No clients found that need priority updates.')
                )
                
            # Show some examples of clients that got priority
            if updated_to_priority > 0:
                updated_clients = Cliente.objects.filter(
                    nascimento__lt=cutoff_date,
                    prioridade=True,
                    falecido=False
                )[:5]
                
                self.stdout.write("\nSome clients who got priority:")
                for client in updated_clients:
                    age = (date.today() - client.nascimento).days // 365
                    self.stdout.write(f"  - {client.nome} (CPF: {client.cpf}, Age: {age} years)")
                    
            # Show some examples of deceased clients who lost priority
            if removed_from_priority > 0:
                self.stdout.write("\nSome deceased clients who lost priority:")
                deceased_clients = Cliente.objects.filter(
                    prioridade=False,
                    falecido=True
                )[:3]
                for client in deceased_clients:
                    self.stdout.write(f"  - {client.nome} (CPF: {client.cpf})")
