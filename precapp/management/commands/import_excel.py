"""
Django management command to import data from Pasta1.xlsx
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal, InvalidOperation
from datetime import datetime
import pandas as pd
import os
from precapp.models import Precatorio, Cliente, Alvara, Requerimento, Fase, FaseHonorariosContratuais, TipoDiligencia, Tipo, PedidoRequerimento


class Command(BaseCommand):
    help = 'Import data from Pasta1.xlsx file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='precapp/sheets/2014.xlsx',
            help='Path to Excel file to import'
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default=None,
            help='Specific sheet name to import (imports all sheets if not specified)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
    
    def handle(self, *args, **options):
        file_path = options['file']
        sheet_name = options['sheet']
        dry_run = options['dry_run']
        
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no data will be saved'))
        
        # Create main phases before importing data
        if not dry_run:
            self.create_main_phases()
            self.create_tipos_diligencia()
            self.create_tipos_precatorio()
            self.create_tipos_pedido_requerimento()
        
        try:
            self.import_excel_data(file_path, sheet_name, dry_run)
        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')
    
    def create_main_phases(self):
        """Create main phases for Requerimento and Alvará"""
        
        # Fases Principais para Requerimento
        requerimento_phases = [
            {
                'nome': 'Organizar Documentos',
                'descricao': 'Fase inicial para organização dos documentos necessários',
                'cor': '#FFC107',  # Amarelo - indicando preparação
                'ativa': True,
                'ordem': 1
            },
            {
                'nome': 'Protocolado',
                'descricao': 'Requerimento protocolado e em análise',
                'cor': '#17A2B8',  # Azul - indicando em andamento
                'ativa': True,
                'ordem': 2
            },
            {
                'nome': 'Deferido',
                'descricao': 'Requerimento deferido e aprovado',
                'cor': '#28A745',  # Verde - indicando sucesso
                'ativa': True,
                'ordem': 3
            },
            {
                'nome': 'Indeferido',
                'descricao': 'Requerimento indeferido e negado',
                'cor': '#DC3545',  # Vermelho - indicando negativa
                'ativa': True,
                'ordem': 4
            }
        ]
        
        # Fases Principais para Alvará
        alvara_phases = [
            {
                'nome': 'Aguardando Depósito Judicial',
                'descricao': 'Aguardando o depósito dos valores pelo tribunal',
                'cor': '#FFC107',  # Amarelo - aguardando
                'ativa': True,
                'ordem': 1
            },
            {
                'nome': 'Crédito Depositado Judicialmente',
                'descricao': 'Valores depositados pelo tribunal',
                'cor': '#17A2B8',  # Azul - em processamento
                'ativa': True,
                'ordem': 2
            },
            {
                'nome': 'Aguardando Atualização pela Contadoria',
                'descricao': 'Aguardando atualização dos valores pela contadoria',
                'cor': '#6F42C1',  # Roxo - processamento interno
                'ativa': True,
                'ordem': 3
            },
            {
                'nome': 'Recebido Pelo Cliente',
                'descricao': 'Valores recebidos pelo cliente final',
                'cor': '#28A745',  # Verde - concluído
                'ativa': True,
                'ordem': 4
            }
        ]
        
        # Fases Principais para Honorários
        honorarios_phases = [
            {
                'nome': 'Aguardando Depósito Judicial',
                'descricao': 'Aguardando o depósito dos honorários pelo tribunal',
                'cor': '#FFC107',  # Amarelo - aguardando
                'ativa': True,
                'ordem': 1
            },
            {
                'nome': 'Cobrar Cliente',
                'descricao': 'Iniciar cobrança dos honorários do cliente',
                'cor': '#FF6B35',  # Laranja - ação necessária
                'ativa': True,
                'ordem': 2
            },
            {
                'nome': 'Quitado parcialmente',
                'descricao': 'Honorários quitados parcialmente pelo cliente',
                'cor': '#17A2B8',  # Azul - parcialmente concluído
                'ativa': True,
                'ordem': 3
            },
            {
                'nome': 'Quitado integralmente',
                'descricao': 'Honorários quitados integralmente pelo cliente',
                'cor': '#28A745',  # Verde - totalmente concluído
                'ativa': True,
                'ordem': 4
            }
        ]
        
        # Create Requerimento phases
        created_req = 0
        for phase_data in requerimento_phases:
            fase, created = Fase.objects.get_or_create(
                nome=phase_data['nome'],
                tipo='requerimento',
                defaults={
                    'descricao': phase_data['descricao'],
                    'cor': phase_data['cor'],
                    'ativa': phase_data['ativa'],
                    'ordem': phase_data['ordem']
                }
            )
            if created:
                created_req += 1
                self.stdout.write(f'✓ Created Requerimento phase: {fase.nome} (ordem: {fase.ordem})')
        
        # Create Alvará phases
        created_alv = 0
        for phase_data in alvara_phases:
            fase, created = Fase.objects.get_or_create(
                nome=phase_data['nome'],
                tipo='alvara',
                defaults={
                    'descricao': phase_data['descricao'],
                    'cor': phase_data['cor'],
                    'ativa': phase_data['ativa'],
                    'ordem': phase_data['ordem']
                }
            )
            if created:
                created_alv += 1
                self.stdout.write(f'✓ Created Alvará phase: {fase.nome} (ordem: {fase.ordem})')
        
        # Create Honorários phases
        created_hon = 0
        for phase_data in honorarios_phases:
            fase, created = FaseHonorariosContratuais.objects.get_or_create(
                nome=phase_data['nome'],
                defaults={
                    'descricao': phase_data['descricao'],
                    'cor': phase_data['cor'],
                    'ativa': phase_data['ativa'],
                    'ordem': phase_data['ordem']
                }
            )
            if created:
                created_hon += 1
                self.stdout.write(f'✓ Created Honorários phase: {fase.nome} (ordem: {fase.ordem})')
        
        if created_req > 0 or created_alv > 0 or created_hon > 0:
            self.stdout.write(f'\n=== PHASES CREATED ===')
            self.stdout.write(f'Requerimento phases: {created_req}')
            self.stdout.write(f'Alvará phases: {created_alv}')
            self.stdout.write(f'Honorários phases: {created_hon}')
        else:
            self.stdout.write('All main phases already exist')
        
        self.stdout.write('')
    
    def create_tipos_diligencia(self):
        """Create default diligencia types"""
        
        diligencia_types = [
            {
                'nome': 'Propor repactuação',
                'descricao': 'Propor uma nova pactuação ou renegociação dos termos',
                'cor': '#007bff',  # Azul - padrão
                'ordem': 1
            },
            {
                'nome': 'Solicitar RG',
                'descricao': 'Solicitar documento de identidade (RG) do cliente',
                'cor': '#28a745',  # Verde
                'ordem': 2
            },
            {
                'nome': 'Solicitar contrato',
                'descricao': 'Solicitar contrato ou documentação contratual',
                'cor': '#ffc107',  # Amarelo
                'ordem': 3
            },
            {
                'nome': 'Cobrar honorários',
                'descricao': 'Realizar cobrança de honorários devidos',
                'cor': '#fd7e14',  # Laranja
                'ordem': 4
            },
            {
                'nome': 'Executar honorários',
                'descricao': 'Executar judicialmente os honorários em aberto',
                'cor': '#dc3545',  # Vermelho
                'ordem': 5
            }
        ]
        
        created_count = 0
        for tipo_data in diligencia_types:
            tipo, created = TipoDiligencia.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults={
                    'descricao': tipo_data['descricao'],
                    'cor': tipo_data['cor'],
                    'ordem': tipo_data['ordem']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'✓ Created TipoDiligencia: {tipo.nome} (ordem: {tipo.ordem})')
        
        if created_count > 0:
            self.stdout.write(f'\n=== TIPOS DE DILIGÊNCIA CREATED ===')
            self.stdout.write(f'Created {created_count} new diligencia types')
        else:
            self.stdout.write('All diligencia types already exist')
        
        self.stdout.write('')
    
    def create_tipos_precatorio(self):
        """Create default tipos de precatorio"""
        
        tipos_precatorio = [
            {
                'nome': 'Descompressão',
                'descricao': 'Precatórios originados de processos de descompressão salarial',
                'cor': '#007bff',  # Azul
                'ordem': 1
            },
            {
                'nome': 'URV',
                'descricao': 'Precatórios relacionados à Unidade Real de Valor',
                'cor': '#28a745',  # Verde
                'ordem': 2
            },
            {
                'nome': 'Reclassificação',
                'descricao': 'Precatórios originados de processos de reclassificação funcional',
                'cor': '#ffc107',  # Amarelo
                'ordem': 3
            }
        ]
        
        created_count = 0
        for tipo_data in tipos_precatorio:
            tipo, created = Tipo.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults={
                    'descricao': tipo_data['descricao'],
                    'cor': tipo_data['cor'],
                    'ordem': tipo_data['ordem'],
                    'ativa': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'✓ Created Tipo de Precatório: {tipo.nome} (ordem: {tipo.ordem})')
        
        if created_count > 0:
            self.stdout.write(f'\n=== TIPOS DE PRECATÓRIO CREATED ===')
            self.stdout.write(f'Created {created_count} new tipos de precatorio')
        else:
            self.stdout.write('All tipos de precatorio already exist')
        
        self.stdout.write('')
    
    def create_tipos_pedido_requerimento(self):
        """Create default tipos de pedido requerimento"""
        
        tipos_pedido_requerimento = [
            {
                'nome': 'Prioridade por idade',
                'descricao': 'Requerimento para prioridade de tramitação por idade (acima de 60 anos)',
                'cor': '#6f42c1',  # Roxo
                'ordem': 1
            },
            {
                'nome': 'Prioridade por doença',
                'descricao': 'Requerimento para prioridade de tramitação por doença grave',
                'cor': '#e83e8c',  # Rosa
                'ordem': 2
            },
            {
                'nome': 'Acordo no Principal',
                'descricao': 'Requerimento de acordo sobre o valor principal do precatório',
                'cor': '#007bff',  # Azul
                'ordem': 3
            },
            {
                'nome': 'Acordo nos Hon. Sucumbenciais',
                'descricao': 'Requerimento de acordo sobre os honorários sucumbenciais',
                'cor': '#28a745',  # Verde
                'ordem': 4
            },
            {
                'nome': 'Acordo nos Hon. Contratuais',
                'descricao': 'Requerimento de acordo sobre os honorários contratuais',
                'cor': '#ffc107',  # Amarelo
                'ordem': 5
            },
            {
                'nome': 'Impugnação aos cálculos',
                'descricao': 'Requerimento de impugnação aos cálculos apresentados',
                'cor': '#fd7e14',  # Laranja
                'ordem': 6
            },
            {
                'nome': 'Repartição de honorários',
                'descricao': 'Requerimento para repartição de honorários entre advogados',
                'cor': '#dc3545',  # Vermelho
                'ordem': 7
            }
        ]
        
        created_count = 0
        for tipo_data in tipos_pedido_requerimento:
            tipo, created = PedidoRequerimento.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults={
                    'descricao': tipo_data['descricao'],
                    'cor': tipo_data['cor'],
                    'ordem': tipo_data['ordem'],
                    'ativo': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'✓ Created Tipo de Pedido Requerimento: {tipo.nome} (ordem: {tipo.ordem})')
        
        if created_count > 0:
            self.stdout.write(f'\n=== TIPOS DE PEDIDO REQUERIMENTO CREATED ===')
            self.stdout.write(f'Created {created_count} new tipos de pedido requerimento')
        else:
            self.stdout.write('All tipos de pedido requerimento already exist')
        
        self.stdout.write('')
    
    def import_excel_data(self, file_path, sheet_name, dry_run):
        """Main import logic"""
        # Read Excel file
        excel_file = pd.ExcelFile(file_path)
        sheets_to_process = [sheet_name] if sheet_name else excel_file.sheet_names
        
        self.stdout.write(f'Found sheets: {excel_file.sheet_names}')
        
        total_imported = {
            'precatorios': 0,
            'clientes': 0,
            'requerimentos': 0
        }
        
        for sheet in sheets_to_process:
            self.stdout.write(f'\n=== Processing sheet: {sheet} ===')
            
            # Read with header row detection
            df = pd.read_excel(file_path, sheet_name=sheet, header=1)  # Headers are in row 1 (0-indexed)
            
            # Clean up column names - adjusted for new structure after first column deletion
            df.columns = [
                'cnj', 'cnj_origem', 'orcamento', 'nome', 'cpf', 'nascimento', 'valor_face'
            ]
            
            # Remove any completely empty rows
            df = df.dropna(how='all')
            
            # Display sheet info
            self.stdout.write(f'Shape after cleaning: {df.shape} (rows x columns)')
            self.stdout.write(f'Columns: {list(df.columns)}')
            self.stdout.write(f'Sample data:')
            self.stdout.write(str(df.head(2)))
            
            if not dry_run and not df.empty:
                with transaction.atomic():
                    imported = self.process_precatorios_2014_format(df)
                    for key, value in imported.items():
                        total_imported[key] += value
            elif dry_run:
                self.stdout.write(f'\n📊 DRY RUN - Would process {len(df)} rows')
                self.stdout.write('Sample records that would be created (Precatórios + Clientes only):')
                for idx, row in df.head(3).iterrows():
                    self.stdout.write(f'  Precatório: {row["cnj"]} | Cliente: {row["nome"]} | CPF: {row["cpf"]} | Valor: {row["valor_face"]}')
                self.stdout.write('Note: Alvarás will NOT be created during import')
        
        # Summary
        self.stdout.write(f'\n=== IMPORT SUMMARY ===')
        for model, count in total_imported.items():
            self.stdout.write(f'{model.capitalize()}: {count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data was actually imported'))
        else:
            self.stdout.write(self.style.SUCCESS('Import completed successfully!'))
    
    def process_precatorios_2014_format(self, df):
        """Process data in the specific 2014 format from the Excel file"""
        imported = {
            'precatorios': 0,
            'clientes': 0,
            'requerimentos': 0
        }
        
        for index, row in df.iterrows():
            try:
                # Create or get precatorio
                precatorio = self.create_precatorio_from_row(row)
                if precatorio:
                    imported['precatorios'] += 1
                
                # Create or get cliente
                cliente = self.create_cliente_from_row(row)
                if cliente:
                    imported['clientes'] += 1
                
                # Link cliente to precatorio
                if precatorio and cliente:
                    precatorio.clientes.add(cliente)
                    
                    # Skip Alvará creation as requested
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error processing row {index}: {str(e)}')
                )
                continue
        
        return imported
    
    def create_precatorio_from_row(self, row):
        """Create precatorio from Excel row"""
        cnj = str(row['cnj']).strip() if pd.notna(row['cnj']) else None
        if not cnj:
            return None
        
        # Derive origem from cnj_origem (second column in the new structure)
        cnj_origem = str(row['cnj_origem']).strip() if pd.notna(row['cnj_origem']) else None
        origem = cnj_origem if cnj_origem else 'Importado da planilha'
        
        # Set up defaults
        defaults = {
            'orcamento': int(row['orcamento']) if pd.notna(row['orcamento']) else 2014,
            'origem': origem,
            'valor_de_face': float(row['valor_face']) if pd.notna(row['valor_face']) else 0.0,
            'ultima_atualizacao': float(row['valor_face']) if pd.notna(row['valor_face']) else 0.0,
            'percentual_contratuais_assinado': 0.0,
            'percentual_contratuais_apartado': 0.0,
            'percentual_sucumbenciais': 0.0,
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        }
        
        # Only set data_ultima_atualizacao if there's a date column in the sheet
        # For now, we don't set it since the current sheet doesn't have this data
        
        precatorio, created = Precatorio.objects.get_or_create(
            cnj=cnj,
            defaults=defaults
        )
        
        if created:
            self.stdout.write(f'✓ Created precatório: {cnj} (Valor: R$ {defaults["valor_de_face"]:,.2f})')
        
        return precatorio
    
    def create_cliente_from_row(self, row):
        """Create cliente from Excel row"""
        cpf = str(row['cpf']).replace('.', '').replace('-', '').replace('/', '').strip() if pd.notna(row['cpf']) else None
        nome = str(row['nome']).strip() if pd.notna(row['nome']) else None
        
        if not cpf or not nome:
            return None
        
        # Handle birth date
        nascimento = datetime(1980, 1, 1).date()  # Default
        if pd.notna(row['nascimento']):
            try:
                if isinstance(row['nascimento'], datetime):
                    nascimento = row['nascimento'].date()
                elif isinstance(row['nascimento'], str):
                    nascimento = datetime.strptime(row['nascimento'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        
        defaults = {
            'nome': nome,
            'nascimento': nascimento,
            'prioridade': False  # Can be updated later based on other criteria
        }
        
        cliente, created = Cliente.objects.get_or_create(
            cpf=cpf,
            defaults=defaults
        )
        
        if created:
            self.stdout.write(f'✓ Created cliente: {nome} (CPF: {cpf})')
        
        return cliente
    
    # NOTE: create_alvara_from_row method removed - Alvarás are no longer created during import
    
    def process_sheet_data(self, df, sheet_name):
        """Process data from a single sheet"""
        imported = {
            'precatorios': 0,
            'clientes': 0,
            'alvaras': 0,
            'requerimentos': 0
        }
        
        # Try to identify the data structure based on column names
        columns = [col.lower().strip() for col in df.columns]
        
        # Common column name mappings
        column_mappings = {
            # Precatorio fields
            'cnj': ['cnj', 'numero_cnj', 'processo'],
            'origem': ['origem', 'tribunal', 'vara'],
            'orcamento': ['orcamento', 'ano', 'exercicio'],
            'valor_face': ['valor_face', 'valor_de_face', 'valor_principal', 'valor'],
            'ultima_atualizacao': ['ultima_atualizacao', 'valor_atual', 'valor_atualizado'],
            'data_atualizacao': ['data_atualizacao', 'data_ultima_atualizacao', 'data'],
            
            # Payment status fields
            'credito_principal': ['credito_principal', 'status_principal', 'principal_status'],
            'honorarios_contratuais_status': ['honorarios_contratuais_status', 'status_contratuais', 'contratuais_status'],
            'honorarios_sucumbenciais_status': ['honorarios_sucumbenciais_status', 'status_sucumbenciais', 'sucumbenciais_status'],
            'quitado': ['quitado', 'pago', 'status_pagamento'],  # For backward compatibility
            
            # Cliente fields  
            'nome': ['nome', 'cliente', 'beneficiario'],
            'cpf': ['cpf', 'documento'],
            'nascimento': ['nascimento', 'data_nascimento', 'dt_nascimento'],
            'prioridade': ['prioridade', 'prioritario'],
            
            # Alvara fields
            'tipo_alvara': ['tipo', 'tipo_alvara', 'modalidade'],
            'honorarios_contratuais': ['honorarios_contratuais', 'honorarios', 'hon_contratuais'],
            'honorarios_sucumbenciais': ['honorarios_sucumbenciais', 'hon_sucumbenciais'],
            'fase': ['fase', 'situacao', 'status'],
            
            # Requerimento fields
            'pedido': ['pedido', 'tipo_pedido', 'requerimento'],
            'desagio': ['desagio', 'desconto', 'deságio']
        }
        
        # Identify which type of data this sheet contains
        data_type = self.identify_data_type(columns, column_mappings)
        self.stdout.write(f'Detected data type: {data_type}')
        
        if data_type == 'mixed' or data_type == 'precatorio_with_details':
            # Process as complete precatorio data with clients and alvaras/requerimentos
            imported = self.import_complete_data(df, column_mappings)
        elif data_type == 'precatorios':
            imported['precatorios'] = self.import_precatorios(df, column_mappings)
        elif data_type == 'clientes':
            imported['clientes'] = self.import_clientes(df, column_mappings)
        elif data_type == 'alvaras':
            imported['alvaras'] = self.import_alvaras(df, column_mappings)
        elif data_type == 'requerimentos':
            imported['requerimentos'] = self.import_requerimentos(df, column_mappings)
        
        return imported
    
    def identify_data_type(self, columns, mappings):
        """Identify what type of data the sheet contains"""
        has_cnj = any(self.find_column(columns, mappings['cnj']))
        has_nome = any(self.find_column(columns, mappings['nome']))
        has_cpf = any(self.find_column(columns, mappings['cpf']))
        has_tipo_alvara = any(self.find_column(columns, mappings['tipo_alvara']))
        has_pedido = any(self.find_column(columns, mappings['pedido']))
        
        if has_cnj and has_nome and (has_tipo_alvara or has_pedido):
            return 'mixed'  # Complete data with precatorio + client + alvara/requerimento
        elif has_cnj:
            return 'precatorios'
        elif has_cpf and not has_cnj:
            return 'clientes'
        elif has_tipo_alvara:
            return 'alvaras'
        elif has_pedido:
            return 'requerimentos'
        else:
            return 'unknown'
    
    def find_column(self, columns, possible_names):
        """Find a column that matches any of the possible names"""
        for col in columns:
            if any(name in col for name in possible_names):
                return col
        return None
    
    def get_column_value(self, row, columns, mappings, key):
        """Get value from row using column mappings"""
        column_name = self.find_column(columns, mappings[key])
        if column_name and column_name in row.index:
            value = row[column_name]
            if pd.isna(value):
                return None
            return value
        return None
    
    def import_complete_data(self, df, mappings):
        """Import complete data (precatorios with clients and alvaras/requerimentos)"""
        imported = {'precatorios': 0, 'clientes': 0, 'requerimentos': 0}
        columns = [col.lower().strip() for col in df.columns]
        
        for index, row in df.iterrows():
            try:
                # Import precatorio
                precatorio = self.create_or_update_precatorio(row, columns, mappings)
                if precatorio:
                    imported['precatorios'] += 1
                
                # Import cliente
                cliente = self.create_or_update_cliente(row, columns, mappings)
                if cliente:
                    imported['clientes'] += 1
                
                # Link cliente to precatorio
                if precatorio and cliente:
                    precatorio.clientes.add(cliente)
                
                # Import alvara or requerimento (Alvarás disabled)
                has_pedido = self.get_column_value(row, columns, mappings, 'pedido')
                
                if has_pedido and precatorio and cliente:
                    requerimento = self.create_requerimento(row, columns, mappings, precatorio, cliente)
                    if requerimento:
                        imported['requerimentos'] += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error processing row {index}: {str(e)}')
                )
                continue
        
        return imported
    
    def create_or_update_precatorio(self, row, columns, mappings):
        """Create or update precatorio from row data"""
        cnj = self.get_column_value(row, columns, mappings, 'cnj')
        if not cnj:
            return None
        
        # Clean CNJ format
        cnj = str(cnj).strip()
        
        defaults = {}
        
        # Get other fields
        if origem := self.get_column_value(row, columns, mappings, 'origem'):
            defaults['origem'] = str(origem)
        
        if orcamento := self.get_column_value(row, columns, mappings, 'orcamento'):
            try:
                defaults['orcamento'] = int(orcamento)
            except (ValueError, TypeError):
                pass
        
        if valor_face := self.get_column_value(row, columns, mappings, 'valor_face'):
            try:
                defaults['valor_de_face'] = float(valor_face)
                defaults['ultima_atualizacao'] = float(valor_face)  # Default to same value
            except (ValueError, TypeError):
                pass
        
        if ultima_atualizacao := self.get_column_value(row, columns, mappings, 'ultima_atualizacao'):
            try:
                defaults['ultima_atualizacao'] = float(ultima_atualizacao)
            except (ValueError, TypeError):
                pass
        
        if data_atualizacao := self.get_column_value(row, columns, mappings, 'data_atualizacao'):
            try:
                if isinstance(data_atualizacao, datetime):
                    defaults['data_ultima_atualizacao'] = data_atualizacao.date()
                elif isinstance(data_atualizacao, str):
                    defaults['data_ultima_atualizacao'] = datetime.strptime(data_atualizacao, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        
        # Handle payment status fields (new approach)
        # Check for specific payment status columns
        if credito_principal_status := self.get_column_value(row, columns, mappings, 'credito_principal'):
            status_value = str(credito_principal_status).lower().strip()
            if status_value in ['pendente', 'parcial', 'quitado', 'vendido']:
                defaults['credito_principal'] = status_value
            elif status_value in ['pendente de pagamento']:
                defaults['credito_principal'] = 'pendente'
            elif status_value in ['quitado parcialmente']:
                defaults['credito_principal'] = 'parcial'
            elif status_value in ['quitado integralmente']:
                defaults['credito_principal'] = 'quitado'
        
        if honorarios_contratuais_status := self.get_column_value(row, columns, mappings, 'honorarios_contratuais_status'):
            status_value = str(honorarios_contratuais_status).lower().strip()
            if status_value in ['pendente', 'parcial', 'quitado', 'vendido']:
                defaults['honorarios_contratuais'] = status_value
            elif status_value in ['pendente de pagamento']:
                defaults['honorarios_contratuais'] = 'pendente'
            elif status_value in ['quitado parcialmente']:
                defaults['honorarios_contratuais'] = 'parcial'
            elif status_value in ['quitado integralmente']:
                defaults['honorarios_contratuais'] = 'quitado'
        
        if honorarios_sucumbenciais_status := self.get_column_value(row, columns, mappings, 'honorarios_sucumbenciais_status'):
            status_value = str(honorarios_sucumbenciais_status).lower().strip()
            if status_value in ['pendente', 'parcial', 'quitado', 'vendido']:
                defaults['honorarios_sucumbenciais'] = status_value
            elif status_value in ['pendente de pagamento']:
                defaults['honorarios_sucumbenciais'] = 'pendente'
            elif status_value in ['quitado parcialmente']:
                defaults['honorarios_sucumbenciais'] = 'parcial'
            elif status_value in ['quitado integralmente']:
                defaults['honorarios_sucumbenciais'] = 'quitado'
        
        # Backward compatibility: if old 'quitado' field exists, map it to all three status fields
        if quitado_status := self.get_column_value(row, columns, mappings, 'quitado'):
            if isinstance(quitado_status, bool):
                status = 'quitado' if quitado_status else 'pendente'
            else:
                quitado_str = str(quitado_status).lower().strip()
                status = 'quitado' if quitado_str in ['true', '1', 'sim', 'quitado', 'pago'] else 'pendente'
            
            # Only set if not already set by specific status columns
            if 'credito_principal' not in defaults:
                defaults['credito_principal'] = status
            if 'honorarios_contratuais' not in defaults:
                defaults['honorarios_contratuais'] = status  
            if 'honorarios_sucumbenciais' not in defaults:
                defaults['honorarios_sucumbenciais'] = status
        
        # Set default values for required fields
        if 'orcamento' not in defaults:
            defaults['orcamento'] = 2024
        if 'origem' not in defaults:
            defaults['origem'] = 'Importado da planilha'
        if 'valor_de_face' not in defaults:
            defaults['valor_de_face'] = 0.0
        if 'ultima_atualizacao' not in defaults:
            defaults['ultima_atualizacao'] = defaults['valor_de_face']
        if 'data_ultima_atualizacao' not in defaults:
            defaults['data_ultima_atualizacao'] = datetime.now().date()
        
        # Set default percentages and payment statuses
        defaults.update({
            'percentual_contratuais_assinado': 0.0,
            'percentual_contratuais_apartado': 0.0,
            'percentual_sucumbenciais': 0.0,
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        })
        
        precatorio, created = Precatorio.objects.get_or_create(
            cnj=cnj,
            defaults=defaults
        )
        
        if created:
            self.stdout.write(f'Created precatorio: {cnj}')
        
        return precatorio
    
    def create_or_update_cliente(self, row, columns, mappings):
        """Create or update cliente from row data"""
        cpf = self.get_column_value(row, columns, mappings, 'cpf')
        nome = self.get_column_value(row, columns, mappings, 'nome')
        
        if not cpf or not nome:
            return None
        
        # Clean CPF (remove formatting)
        cpf = str(cpf).replace('.', '').replace('-', '').replace('/', '').strip()
        
        defaults = {
            'nome': str(nome).strip(),
            'nascimento': datetime(1980, 1, 1).date(),  # Default birth date
            'prioridade': False
        }
        
        # Get birth date
        if nascimento := self.get_column_value(row, columns, mappings, 'nascimento'):
            try:
                if isinstance(nascimento, datetime):
                    defaults['nascimento'] = nascimento.date()
                elif isinstance(nascimento, str):
                    defaults['nascimento'] = datetime.strptime(nascimento, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        
        # Get priority
        if prioridade := self.get_column_value(row, columns, mappings, 'prioridade'):
            defaults['prioridade'] = bool(prioridade)
        
        cliente, created = Cliente.objects.get_or_create(
            cpf=cpf,
            defaults=defaults
        )
        
        if created:
            self.stdout.write(f'Created cliente: {nome} ({cpf})')
        
        return cliente
    
    def create_alvara(self, row, columns, mappings, precatorio, cliente):
        """Create alvara from row data"""
        tipo = self.get_column_value(row, columns, mappings, 'tipo_alvara')
        if not tipo:
            tipo = 'comum'
        
        # Get default fase
        fase = Fase.objects.filter(tipo__in=['alvara', 'ambos'], ativa=True).first()
        if not fase:
            # Create a default fase
            fase = Fase.objects.create(
                nome='Importado',
                tipo='alvara',
                cor='#007BFF',
                ativa=True
            )
        
        defaults = {
            'precatorio': precatorio,
            'cliente': cliente,
            'tipo': str(tipo).lower(),
            'fase': fase,
            'valor_principal': 0.0,
            'honorarios_contratuais': 0.0,
            'honorarios_sucumbenciais': 0.0
        }
        
        # Get values
        if valor_principal := self.get_column_value(row, columns, mappings, 'valor_face'):
            try:
                defaults['valor_principal'] = float(valor_principal)
            except (ValueError, TypeError):
                pass
        
        if hon_contratuais := self.get_column_value(row, columns, mappings, 'honorarios_contratuais'):
            try:
                defaults['honorarios_contratuais'] = float(hon_contratuais)
            except (ValueError, TypeError):
                pass
        
        if hon_sucumbenciais := self.get_column_value(row, columns, mappings, 'honorarios_sucumbenciais'):
            try:
                defaults['honorarios_sucumbenciais'] = float(hon_sucumbenciais)
            except (ValueError, TypeError):
                pass
        
        alvara = Alvara.objects.create(**defaults)
        self.stdout.write(f'Created alvara for {cliente.nome}')
        
        return alvara
    
    def create_requerimento(self, row, columns, mappings, precatorio, cliente):
        """Create requerimento from row data"""
        pedido = self.get_column_value(row, columns, mappings, 'pedido')
        if not pedido:
            pedido = 'outros'
        
        # Get default fase
        fase = Fase.objects.filter(tipo__in=['requerimento', 'ambos'], ativa=True).first()
        if not fase:
            # Create a default fase
            fase = Fase.objects.create(
                nome='Em Andamento',
                tipo='requerimento',
                cor='#28A745',
                ativa=True
            )
        
        defaults = {
            'precatorio': precatorio,
            'cliente': cliente,
            'pedido': str(pedido).lower(),
            'fase': fase,
            'valor': 0.0,
            'desagio': 0.0
        }
        
        # Get values
        if valor := self.get_column_value(row, columns, mappings, 'valor_face'):
            try:
                defaults['valor'] = float(valor)
            except (ValueError, TypeError):
                pass
        
        if desagio := self.get_column_value(row, columns, mappings, 'desagio'):
            try:
                defaults['desagio'] = float(desagio)
            except (ValueError, TypeError):
                pass
        
        requerimento = Requerimento.objects.create(**defaults)
        self.stdout.write(f'Created requerimento for {cliente.nome}')
        
        return requerimento
    
    def import_precatorios(self, df, mappings):
        """Import only precatorio data"""
        count = 0
        columns = [col.lower().strip() for col in df.columns]
        
        for index, row in df.iterrows():
            try:
                precatorio = self.create_or_update_precatorio(row, columns, mappings)
                if precatorio:
                    count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error importing precatorio at row {index}: {str(e)}')
                )
        
        return count
    
    def import_clientes(self, df, mappings):
        """Import only cliente data"""
        count = 0
        columns = [col.lower().strip() for col in df.columns]
        
        for index, row in df.iterrows():
            try:
                cliente = self.create_or_update_cliente(row, columns, mappings)
                if cliente:
                    count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error importing cliente at row {index}: {str(e)}')
                )
        
        return count
    
    def import_alvaras(self, df, mappings):
        """Import alvara data (requires existing precatorios and clientes)"""
        # This would need additional logic to link to existing precatorios/clientes
        return 0
    
    def import_requerimentos(self, df, mappings):
        """Import requerimento data (requires existing precatorios and clientes)"""  
        # This would need additional logic to link to existing precatorios/clientes
        return 0
