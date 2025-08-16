from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, datetime
from precapp.models import Precatorio, Cliente, Alvara, Requerimento


class Command(BaseCommand):
    help = 'Populate the database with sample data: 5 precatórios, 5 clientes, 5 alvarás, and 5 requerimentos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Requerimento.objects.all().delete()
            Alvara.objects.all().delete()
            Cliente.objects.all().delete()
            Precatorio.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # Sample data
        precatorios_data = [
            {
                'cnj': '1234567-89.2023.8.26.0100',
                'data_oficio': date(2023, 3, 15),
                'orcamento': 2023,
                'origem': '5432109-87.2022.8.26.0001',
                'quitado': False,
                'valor_de_face': 150000.00,
                'ultima_atualizacao': 185000.00,
                'data_ultima_atualizacao': date(2024, 12, 1),
                'percentual_contratuais_assinado': 20.00,
                'percentual_contratuais_apartado': 5.00,
                'percentual_sucumbenciais': 10.00,
                'prioridade_deferida': True,
                'acordo_deferido': False,
            },
            {
                'cnj': '2345678-90.2023.8.26.0200',
                'data_oficio': date(2023, 5, 22),
                'orcamento': 2023,
                'origem': '6543210-98.2022.8.26.0002',
                'quitado': True,
                'valor_de_face': 85000.00,
                'ultima_atualizacao': 98000.00,
                'data_ultima_atualizacao': date(2024, 8, 15),
                'percentual_contratuais_assinado': 15.00,
                'percentual_contratuais_apartado': 0.00,
                'percentual_sucumbenciais': 8.00,
                'prioridade_deferida': False,
                'acordo_deferido': True,
            },
            {
                'cnj': '3456789-01.2024.8.26.0300',
                'data_oficio': date(2024, 1, 10),
                'orcamento': 2024,
                'origem': '7654321-09.2023.8.26.0003',
                'quitado': False,
                'valor_de_face': 220000.00,
                'ultima_atualizacao': 265000.00,
                'data_ultima_atualizacao': date(2024, 11, 30),
                'percentual_contratuais_assinado': 25.00,
                'percentual_contratuais_apartado': 10.00,
                'percentual_sucumbenciais': 12.00,
                'prioridade_deferida': True,
                'acordo_deferido': False,
            },
            {
                'cnj': '4567890-12.2024.8.26.0400',
                'data_oficio': date(2024, 6, 5),
                'orcamento': 2024,
                'origem': '8765432-10.2023.8.26.0004',
                'quitado': False,
                'valor_de_face': 75000.00,
                'ultima_atualizacao': 82000.00,
                'data_ultima_atualizacao': date(2024, 10, 20),
                'percentual_contratuais_assinado': 18.00,
                'percentual_contratuais_apartado': 3.00,
                'percentual_sucumbenciais': 9.00,
                'prioridade_deferida': False,
                'acordo_deferido': True,
            },
            {
                'cnj': '5678901-23.2024.8.26.0500',
                'data_oficio': date(2024, 9, 12),
                'orcamento': 2024,
                'origem': '9876543-21.2023.8.26.0005',
                'quitado': False,
                'valor_de_face': 320000.00,
                'ultima_atualizacao': 385000.00,
                'data_ultima_atualizacao': date(2024, 12, 5),
                'percentual_contratuais_assinado': 30.00,
                'percentual_contratuais_apartado': 15.00,
                'percentual_sucumbenciais': 15.00,
                'prioridade_deferida': True,
                'acordo_deferido': False,
            },
        ]

        clientes_data = [
            {
                'cpf': '12345678901',
                'nome': 'Maria Silva Santos',
                'nascimento': date(1965, 4, 12),
                'prioridade': True,
            },
            {
                'cpf': '23456789012',
                'nome': 'João Pedro Oliveira',
                'nascimento': date(1972, 8, 25),
                'prioridade': False,
            },
            {
                'cpf': '34567890123',
                'nome': 'Ana Carolina Ferreira',
                'nascimento': date(1958, 11, 3),
                'prioridade': True,
            },
            {
                'cpf': '45678901234',
                'nome': 'Carlos Eduardo Lima',
                'nascimento': date(1980, 2, 18),
                'prioridade': False,
            },
            {
                'cpf': '56789012345',
                'nome': 'Fernanda Costa Almeida',
                'nascimento': date(1955, 7, 30),
                'prioridade': True,
            },
        ]

        alvaras_data = [
            {
                'precatorio_cnj': '1234567-89.2023.8.26.0100',
                'cliente_cpf': '12345678901',
                'valor_principal': 120000.00,
                'honorarios_contratuais': 24000.00,
                'honorarios_sucumbenciais': 12000.00,
                'tipo': 'prioridade',
                'fase': 'depósito judicial',
            },
            {
                'precatorio_cnj': '2345678-90.2023.8.26.0200',
                'cliente_cpf': '23456789012',
                'valor_principal': 68000.00,
                'honorarios_contratuais': 10200.00,
                'honorarios_sucumbenciais': 5440.00,
                'tipo': 'acordo',
                'fase': 'recebido pelo cliente',
            },
            {
                'precatorio_cnj': '3456789-01.2024.8.26.0300',
                'cliente_cpf': '34567890123',
                'valor_principal': 180000.00,
                'honorarios_contratuais': 45000.00,
                'honorarios_sucumbenciais': 21600.00,
                'tipo': 'prioridade',
                'fase': 'aguardando depósito',
            },
            {
                'precatorio_cnj': '4567890-12.2024.8.26.0400',
                'cliente_cpf': '45678901234',
                'valor_principal': 60000.00,
                'honorarios_contratuais': 10800.00,
                'honorarios_sucumbenciais': 5400.00,
                'tipo': 'acordo',
                'fase': 'depósito judicial',
            },
            {
                'precatorio_cnj': '5678901-23.2024.8.26.0500',
                'cliente_cpf': '56789012345',
                'valor_principal': 250000.00,
                'honorarios_contratuais': 75000.00,
                'honorarios_sucumbenciais': 37500.00,
                'tipo': 'ordem cronológica',
                'fase': 'aguardando depósito',
            },
        ]

        requerimentos_data = [
            {
                'precatorio_cnj': '1234567-89.2023.8.26.0100',
                'cliente_cpf': '12345678901',
                'valor': 15000.00,
                'desagio': 5.00,
                'pedido': 'prioridade idade',
                'fase': 'análise inicial',
            },
            {
                'precatorio_cnj': '2345678-90.2023.8.26.0200',
                'cliente_cpf': '23456789012',
                'valor': 8000.00,
                'desagio': 12.50,
                'pedido': 'acordo principal',
                'fase': 'deferido',
            },
            {
                'precatorio_cnj': '3456789-01.2024.8.26.0300',
                'cliente_cpf': '34567890123',
                'valor': 22000.00,
                'desagio': 8.00,
                'pedido': 'prioridade doença',
                'fase': 'em andamento',
            },
            {
                'precatorio_cnj': '4567890-12.2024.8.26.0400',
                'cliente_cpf': '45678901234',
                'valor': 6500.00,
                'desagio': 15.00,
                'pedido': 'acordo honorários contratuais',
                'fase': 'análise inicial',
            },
            {
                'precatorio_cnj': '5678901-23.2024.8.26.0500',
                'cliente_cpf': '56789012345',
                'valor': 35000.00,
                'desagio': 10.00,
                'pedido': 'acordo honorários sucumbenciais',
                'fase': 'em andamento',
            },
        ]

        try:
            with transaction.atomic():
                self.stdout.write('Creating precatórios...')
                precatorios_created = []
                for data in precatorios_data:
                    precatorio, created = Precatorio.objects.get_or_create(
                        cnj=data['cnj'],
                        defaults=data
                    )
                    precatorios_created.append(precatorio)
                    if created:
                        self.stdout.write(f'  ✓ Created precatório: {precatorio.cnj}')
                    else:
                        self.stdout.write(f'  ⚠ Precatório already exists: {precatorio.cnj}')

                self.stdout.write('Creating clientes...')
                clientes_created = []
                for data in clientes_data:
                    cliente, created = Cliente.objects.get_or_create(
                        cpf=data['cpf'],
                        defaults=data
                    )
                    clientes_created.append(cliente)
                    if created:
                        self.stdout.write(f'  ✓ Created cliente: {cliente.nome} (CPF: {cliente.cpf})')
                    else:
                        self.stdout.write(f'  ⚠ Cliente already exists: {cliente.nome} (CPF: {cliente.cpf})')

                self.stdout.write('Creating alvarás...')
                for i, data in enumerate(alvaras_data):
                    precatorio = Precatorio.objects.get(cnj=data['precatorio_cnj'])
                    cliente = Cliente.objects.get(cpf=data['cliente_cpf'])
                    
                    alvara_data = {
                        'precatorio': precatorio,
                        'cliente': cliente,
                        'valor_principal': data['valor_principal'],
                        'honorarios_contratuais': data['honorarios_contratuais'],
                        'honorarios_sucumbenciais': data['honorarios_sucumbenciais'],
                        'tipo': data['tipo'],
                        'fase': data['fase'],
                    }
                    
                    alvara, created = Alvara.objects.get_or_create(
                        precatorio=precatorio,
                        cliente=cliente,
                        defaults=alvara_data
                    )
                    
                    if created:
                        self.stdout.write(f'  ✓ Created alvará: {alvara.tipo} for {cliente.nome}')
                    else:
                        self.stdout.write(f'  ⚠ Alvará already exists for {cliente.nome} and precatório {precatorio.cnj}')

                self.stdout.write('Creating requerimentos...')
                for i, data in enumerate(requerimentos_data):
                    precatorio = Precatorio.objects.get(cnj=data['precatorio_cnj'])
                    cliente = Cliente.objects.get(cpf=data['cliente_cpf'])
                    
                    requerimento_data = {
                        'precatorio': precatorio,
                        'cliente': cliente,
                        'valor': data['valor'],
                        'desagio': data['desagio'],
                        'pedido': data['pedido'],
                        'fase': data['fase'],
                    }
                    
                    requerimento, created = Requerimento.objects.get_or_create(
                        precatorio=precatorio,
                        cliente=cliente,
                        pedido=data['pedido'],
                        defaults=requerimento_data
                    )
                    
                    if created:
                        self.stdout.write(f'  ✓ Created requerimento: {requerimento.pedido} for {cliente.nome}')
                    else:
                        self.stdout.write(f'  ⚠ Requerimento already exists: {requerimento.pedido} for {cliente.nome}')

                # Link clientes to precatórios (many-to-many relationship)
                self.stdout.write('Linking clientes to precatórios...')
                for i in range(5):
                    precatorio = precatorios_created[i]
                    cliente = clientes_created[i]
                    precatorio.clientes.add(cliente)
                    self.stdout.write(f'  ✓ Linked {cliente.nome} to {precatorio.cnj}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error populating database: {str(e)}')
            )
            return

        self.stdout.write(self.style.SUCCESS('\n🎉 Database populated successfully!'))
        self.stdout.write(self.style.SUCCESS('📊 Summary:'))
        self.stdout.write(f'   • {Precatorio.objects.count()} Precatórios')
        self.stdout.write(f'   • {Cliente.objects.count()} Clientes')
        self.stdout.write(f'   • {Alvara.objects.count()} Alvarás')
        self.stdout.write(f'   • {Requerimento.objects.count()} Requerimentos')
        
        # Show some quick stats
        total_valor = sum(p.valor_de_face for p in Precatorio.objects.all())
        self.stdout.write(f'   • Total Valor de Face: R$ {total_valor:,.2f}')
        
        quitados = Precatorio.objects.filter(quitado=True).count()
        self.stdout.write(f'   • Precatórios Quitados: {quitados}')
        
        prioridades = Cliente.objects.filter(prioridade=True).count()
        self.stdout.write(f'   • Clientes com Prioridade: {prioridades}')
        
        # Show requerimento stats
        pedidos_prioridade = Requerimento.objects.filter(pedido__contains='prioridade').count()
        self.stdout.write(f'   • Requerimentos de Prioridade: {pedidos_prioridade}')
        
        pedidos_acordo = Requerimento.objects.filter(pedido__contains='acordo').count()
        self.stdout.write(f'   • Requerimentos de Acordo: {pedidos_acordo}')
