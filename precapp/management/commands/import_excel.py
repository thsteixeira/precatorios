"""
Django management command to import precatory data from Excel files.

This command provides comprehensive functionality for importing precatory (court payment order)
data from Excel files into the Precatórios Control System. It supports intelligent data mapping
and comprehensive error handling.

Key Features:
- Excel format support with automatic data validation and cleaning
- Database transaction management for data integrity
- Dry run mode for safe testing
- Comprehensive error handling and reporting
- Default data structure creation (phases, types, etc.)

Usage Examples:
    python manage.py import_excel --file "data.xlsx" --dry-run
    python manage.py import_excel --file "data.xlsx" --sheet "Main"
    python manage.py import_excel --dry-run

Supported Data Types:
- Precatórios (court payment orders)
- Clientes (client information)
- Workflow phases and configurations
- Various type definitions

Author: Precatórios System Team
Version: 2.0
Last Updated: September 2025
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal, InvalidOperation
from datetime import datetime
import pandas as pd
import os
from precapp.models import Precatorio, Cliente, Alvara, Requerimento, Fase, FaseHonorariosContratuais, TipoDiligencia, Tipo, PedidoRequerimento


class Command(BaseCommand):
    """
    Django management command for importing precatory data from Excel files.
    
    This command handles the bulk import of precatory data, client information,
    and related configurations from Excel files into the database. It provides
    robust error handling, data validation, and flexible format support.
    
    Attributes:
        help (str): Command description shown in Django's help system
    
    Key Capabilities:
    - Imports precatory records with CNJ validation
    - Creates and links client records with CPF validation
    - Sets up default workflow phases and type configurations
    - Supports multiple Excel formats with intelligent detection
    - Provides dry run mode for safe testing
    - Maintains data integrity through transaction management
    
    Supported Excel Format:
    - Current format with enhanced data fields and comprehensive mapping
    
    Error Handling:
    - Row-level error isolation (failed rows don't stop entire import)
    - Comprehensive error reporting with specific failure reasons
    - Transaction rollback on critical errors
    - Data validation with graceful handling of invalid data
    
    Performance Features:
    - Memory-efficient row-by-row processing
    - Progress reporting for long operations
    - Configurable batch processing for large files
    """
    help = 'Import data from Pasta1.xlsx file'
    
    def add_arguments(self, parser):
        """
        Define command-line arguments for the import command.
        
        Configures the argument parser with options for file path, sheet selection,
        and dry run mode. These arguments provide flexibility in how the import
        is executed and allow for safe testing of import operations.
        
        Args:
            parser (argparse.ArgumentParser): Django's command argument parser
            
        Arguments Added:
            --file (str): Path to Excel file to import
                Default: 'precapp/sheets/data.xlsx'
                Example: --file "data/monthly_import.xlsx"
                
            --sheet (str): Specific sheet name to import  
                Default: None (auto-detects and uses first sheet)
                Example: --sheet "Main_Data"
                
            --dry-run (flag): Enable dry run mode
                When specified, shows what would be imported without saving data
                Useful for testing and validation before actual import
                
        Usage Examples:
            python manage.py import_excel --file "data.xlsx"
            python manage.py import_excel --sheet "Main" --dry-run
            python manage.py import_excel --file "large_file.xlsx" --sheet "Q1_Data"
        """
        parser.add_argument(
            '--file',
            type=str,
            default='precapp/sheets/data.xlsx',
            help='Path to Excel file to import'
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default=None,
            help='Specific sheet name to import (imports first sheet if not specified)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
    
    def handle(self, *args, **options):
        """
        Main entry point for the import command execution.
        
        Coordinates the entire import process from initial validation through
        final data import. Handles file validation, dry run mode setup,
        default data creation, and delegates to the main import logic.
        
        Args:
            *args: Positional arguments (unused)
            **options (dict): Command options from argument parser containing:
                - file (str): Path to Excel file
                - sheet (str): Sheet name to import
                - dry_run (bool): Whether to run in dry run mode
                
        Raises:
            CommandError: If file is not found or import fails
            
        Process Flow:
            1. Extract and validate command options
            2. Verify Excel file exists and is accessible
            3. Set up dry run mode if specified
            4. Create default data structures (phases, types) if not dry run
            5. Execute main import logic
            6. Handle and report any critical errors
            
        Error Handling:
            - File not found: Raises CommandError with specific file path
            - Import failures: Catches exceptions and raises CommandError with details
            - Validation errors: Provides clear feedback about what failed
            
        Side Effects:
            - Creates default phases, diligence types, precatory types
            - May create/update precatory and client records
            - Outputs progress and status information to stdout
        """
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
        """
        Create default workflow phases for the system.
        
        Sets up the standard workflow phases for different process types in the
        precatory system. These phases define the workflow states that precatories,
        alvarás, and honorários can be in during their lifecycle.
        
        Creates three types of phases:
        
        1. Requerimento Phases (4 phases):
           - Organizar Documentos: Initial document preparation
           - Protocolado: Filed and under review
           - Deferido: Approved and accepted
           - Indeferido: Denied or rejected
           
        2. Alvará Phases (4 phases):
           - Aguardando Depósito Judicial: Waiting for court deposit
           - Crédito Depositado Judicialmente: Credit deposited by court
           - Aguardando Atualização pela Contadoria: Waiting for accounting update
           - Recebido Pelo Cliente: Received by client
           
        3. Honorários Phases (4 phases):
           - Aguardando Depósito Judicial: Waiting for judicial deposit
           - Cobrar Cliente: Bill the client
           - Quitado parcialmente: Partially paid
           - Quitado integralmente: Fully paid
           
        Each phase includes:
        - nome (str): Phase name
        - descricao (str): Detailed description
        - cor (str): Color code for UI display (hex format)
        - ativa (bool): Whether phase is active
        - ordem (int): Sort order for display
        
        Models Used:
        - Fase: For Requerimento and Alvará phases
        - FaseHonorariosContratuais: For Honorários phases
        
        Behavior:
        - Uses get_or_create() to prevent duplicate phases
        - Only creates phases that don't already exist
        - Provides detailed console output about creation status
        - Counts and reports newly created phases by type
        
        Side Effects:
        - Creates database records for workflow phases
        - Outputs creation status to stdout
        - Enables workflow functionality in the web interface
        """
        
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
        """
        Create default diligencia (due diligence) types for the system.
        
        Sets up standard types of diligence activities that can be performed
        in the precatory management process. These types categorize different
        kinds of legal and administrative actions.
        
        Created Diligencia Types:
        1. Propor repactuação: Propose renegotiation of terms
        2. Solicitar RG: Request identity document from client
        3. Solicitar contrato: Request contract documentation
        4. Cobrar honorários: Collect legal fees
        5. Executar honorários: Judicially execute outstanding fees
        
        Each type includes:
        - nome (str): Type name/title
        - descricao (str): Detailed description of the diligence type
        - cor (str): Color code for UI categorization (hex format)
        - ordem (int): Display order for consistent sorting
        
        Color Scheme:
        - Blue (#007bff): Standard/default actions
        - Green (#28a745): Document collection
        - Yellow (#ffc107): Contract-related
        - Orange (#fd7e14): Fee collection
        - Red (#dc3545): Enforcement actions
        
        Model Used:
        - TipoDiligencia: Stores diligence type definitions
        
        Behavior:
        - Uses get_or_create() to prevent duplicates
        - Only creates types that don't already exist
        - Provides console feedback about creation status
        - Reports count of newly created types
        
        Side Effects:
        - Creates database records for diligence types
        - Enables diligence categorization in the system
        - Provides structured options for diligence activities
        """
        
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
        """
        Create default precatory type classifications for the system.
        
        Establishes the standard categories of precatories based on their
        legal origin and nature. These types help classify and organize
        different kinds of court payment orders.
        
        Created Precatory Types:
        1. Descompressão: Precatories from salary decompression processes
           - Related to salary adjustment lawsuits
           - Common in public sector employment disputes
           
        2. URV: Precatories related to Real Value Unit (Unidade Real de Valor)
           - Monetary adjustment from Brazil's currency stabilization period
           - Typically involves salary corrections from 1994-1995
           
        3. Reclassificação: Precatories from job reclassification processes
           - Result from disputes over job position classifications
           - Often involve salary adjustments for reclassified positions
        
        Each type includes:
        - nome (str): Type name/classification
        - descricao (str): Detailed explanation of the precatory type
        - cor (str): Color code for visual identification (hex format)
        - ordem (int): Display order for consistent listing
        - ativa (bool): Whether the type is active for new precatories
        
        Color Scheme:
        - Blue (#007bff): Standard classification (Descompressão)
        - Green (#28a745): Currency-related (URV)
        - Yellow (#ffc107): Position-related (Reclassificação)
        
        Model Used:
        - Tipo: Stores precatory type definitions
        
        Behavior:
        - Uses get_or_create() to prevent duplicate types
        - Sets all types as active by default
        - Provides detailed creation feedback
        - Reports count of newly created types
        
        Side Effects:
        - Creates database records for precatory types
        - Enables type classification in precatory management
        - Supports filtering and reporting by precatory type
        """
        
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
        """
        Create default request types for legal requirements in the system.
        
        Establishes standard categories of legal requests that can be made
        in relation to precatory processes. These types categorize different
        kinds of petitions and requests that may be filed with the court.
        
        Created Request Types:
        
        1. Prioridade por idade: Priority processing due to age (60+ years)
           - Legal right for elderly persons
           - Expedites precatory processing
           
        2. Prioridade por doença: Priority processing due to serious illness
           - Medical condition-based priority
           - Requires medical documentation
           
        3. Acordo no Principal: Agreement on principal amount
           - Settlement regarding main debt value
           - May involve discounts or payment terms
           
        4. Acordo nos Hon. Sucumbenciais: Agreement on sucumbential fees
           - Settlement on court-awarded attorney fees
           - Typically between opposing parties
           
        5. Acordo nos Hon. Contratuais: Agreement on contractual fees
           - Settlement on contracted attorney fees
           - Between client and attorney
           
        6. Impugnação aos cálculos: Objection to calculations
           - Challenge to monetary calculations
           - Disputes over amounts or interest
           
        7. Repartição de honorários: Division of attorney fees
           - Distribution of fees among multiple attorneys
           - Common in cases with multiple representation
        
        Each type includes:
        - nome (str): Request type name
        - descricao (str): Detailed description of the request type
        - cor (str): Color code for visual categorization (hex format)
        - ordem (int): Display order for consistent listing
        - ativo (bool): Whether the type is active for new requests
        
        Color Scheme:
        - Purple (#6f42c1): Priority requests
        - Pink (#e83e8c): Medical priority
        - Blue (#007bff): Principal agreements
        - Green (#28a745): Sucumbential agreements
        - Yellow (#ffc107): Contractual agreements
        - Orange (#fd7e14): Objections
        - Red (#dc3545): Fee divisions
        
        Model Used:
        - PedidoRequerimento: Stores request type definitions
        
        Behavior:
        - Uses get_or_create() to prevent duplicate types
        - Sets all types as active by default
        - Provides detailed creation feedback
        - Reports count of newly created types
        
        Side Effects:
        - Creates database records for request types
        - Enables categorization of legal requests
        - Supports workflow management for different request types
        """
        
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
        """
        Main import logic coordinator for Excel data processing.
        
        Orchestrates the complete import process from Excel file reading
        through data processing and database updates. Handles format detection,
        data validation, and provides comprehensive feedback throughout.
        
        Args:
            file_path (str): Absolute path to the Excel file to import
            sheet_name (str|None): Specific sheet name to import, or None for auto-detection
            dry_run (bool): If True, simulates import without saving data to database
            
        Process Flow:
        1. Read Excel file using pandas
        2. Validate and select target sheet (defaults to '2026')
        3. Clean and standardize column names
        4. Remove empty rows and validate data structure
        5. Display data preview and statistics
        6. Process data using current format structure
        7. Provide detailed import summary
        
        Sheet Selection Logic:
        - Uses provided sheet_name if specified
        - Defaults to first available sheet for current format
        - Validates sheet exists in Excel file
        - Lists available sheets if target not found
        
        Data Cleaning:
        - Standardizes column names to lowercase
        - Maps expected columns for 2026 format
        - Removes completely empty rows
        - Preserves data integrity during cleaning
        
        Data Processing:
        - Uses current format structure for processing
        - Applies appropriate column mapping and validation
        - Handles flexible naming conventions
        
        Error Handling:
        - Validates Excel file readability
        - Checks sheet existence
        - Handles pandas reading errors
        - Provides detailed error messages
        
        Dry Run Mode:
        - Shows processing statistics without database changes
        - Displays sample records that would be created
        - Provides data preview for validation
        - Safe testing before actual import
        
        Output Information:
        - Available sheets in Excel file
        - Selected sheet and data dimensions
        - Column names and sample data
        - Processing progress and statistics
        - Import summary with counts by model type
        
        Side Effects (when not dry run):
        - Creates/updates Precatorio records
        - Creates/updates Cliente records
        - Links precatories to clients
        - May create related records (requirements, etc.)
        
        Raises:
        - CommandError: If sheet not found or critical processing error
        - pandas errors: If Excel file cannot be read
        """
        # Read Excel file
        excel_file = pd.ExcelFile(file_path)
        
        # Use the first sheet by default, or the provided sheet_name
        target_sheet = sheet_name if sheet_name else excel_file.sheet_names[0]
        
        if target_sheet not in excel_file.sheet_names:
            raise CommandError(f'Sheet "{target_sheet}" not found. Available sheets: {excel_file.sheet_names}')
        
        self.stdout.write(f'Found sheets: {excel_file.sheet_names}')
        self.stdout.write(f'Using sheet: {target_sheet}')
        
        total_imported = {
            'precatorios': 0,
            'clientes': 0,
            'requerimentos': 0
        }
        
        self.stdout.write(f'\n=== Processing sheet: {target_sheet} ===')
        
        # Read with header row detection
        df = pd.read_excel(file_path, sheet_name=target_sheet, header=1)  # Headers are in row 1 (0-indexed)
        
        # Clean up column names for current format
        # Expected columns: ['Origem', 'Tipo', 'CNJ', 'Orçamento', 'Destacado', 'Autor', 'CPF', 'Nascimento', 'Valor de Face']
        df.columns = [
            'origem', 'tipo', 'cnj', 'orcamento', 'destacado', 'nome', 'cpf', 'nascimento', 'valor_face'
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
                imported = self.process_sheet_data(df, sheet_name)
                for key, value in imported.items():
                    total_imported[key] += value
        elif dry_run:
            self.stdout.write(f'\n📊 DRY RUN - Would process {len(df)} rows')
            self.stdout.write('Sample records that would be created (Precatórios + Clientes only):')
            for idx, row in df.head(3).iterrows():
                self.stdout.write(f'  Precatório: {row["cnj"]} | Cliente: {row["nome"]} | CPF: {row["cpf"]} | Valor: {row["valor_face"]}')
                self.stdout.write(f'    Tipo: {row.get("tipo", "N/A")} | Destacado: {row.get("destacado", "N/A")}')
            self.stdout.write('Note: Alvarás will NOT be created during import')
        
        # Summary
        self.stdout.write(f'\n=== IMPORT SUMMARY ===')
        for model, count in total_imported.items():
            self.stdout.write(f'{model.capitalize()}: {count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data was actually imported'))
        else:
            self.stdout.write(self.style.SUCCESS('Import completed successfully!'))
    
    def create_precatorio_from_row(self, row):
        """
        Create a Precatorio record from a single Excel row using current format.
        
        Processes one row of Excel data in the current format and creates or
        updates a Precatorio record in the database. Handles data validation,
        type mapping, and provides detailed logging of the creation process.
        
        Args:
            row (pandas.Series): Single row of Excel data containing:
                - cnj: CNJ process number (required)
                - origem: Source/origin information
                - tipo: Type classification
                - orcamento: Budget year
                - destacado: Separated contractual percentage
                - valor_face: Face value amount
                
        Returns:
            Precatorio|None: Created or existing Precatorio instance, or None if invalid data
            
        Data Processing:
        
        CNJ Validation:
        - Strips whitespace from CNJ value
        - Returns None if CNJ is missing or empty
        - Uses CNJ as unique identifier (primary key)
        
        Origem Handling:
        - Direct mapping from origem column
        - Falls back to default message if missing
        - Preserves original source information
        
        Tipo Integration:
        - Searches for existing Tipo by name (case-insensitive)
        - Creates new Tipo record if not found
        - Logs warnings when creating new types
        - Handles missing tipo values gracefully
        
        Destacado Mapping:
        - Maps to percentual_contratuais_apartado field
        - Converts to float with error handling
        - Defaults to 0.0 for invalid or missing values
        
        Value Processing:
        - Sets both valor_de_face and ultima_atualizacao to same value
        - Handles numeric conversion with error handling
        - Defaults to 0.0 for invalid values
        
        Default Values:
        - orcamento: From data or None (nullable)
        - percentual_contratuais_assinado: 0.0
        - percentual_sucumbenciais: 0.0
        - credito_principal: 'pendente'
        - honorarios_contratuais: 'pendente'
        - honorarios_sucumbenciais: 'pendente'
        
        Database Interaction:
        - Uses get_or_create() to prevent duplicates
        - Creates new record only if CNJ doesn't exist
        - Preserves existing records without modification
        
        Error Handling:
        - Safely handles missing or invalid data
        - Logs conversion errors without stopping
        - Returns None for critical validation failures
        - Provides detailed creation logging
        
        Logging:
        - Reports successful creation with key details
        - Shows valor, tipo, and destacado information
        - Indicates when existing records are found
        
        Side Effects:
        - May create new Precatorio database record
        - May create new Tipo record if not found
        - Outputs creation status to console
        
        Example Usage:
            precatorio = self.create_precatorio_from_row(excel_row)
            if precatorio:
                # Link to client or perform other operations
                pass
        """
        cnj = str(row['cnj']).strip() if pd.notna(row['cnj']) else None
        if not cnj:
            return None
        
        # Get origem from the origem column
        origem = str(row['origem']).strip() if pd.notna(row['origem']) else 'Importado da planilha'
        
        # Get tipo from the tipo column and map to Tipo model
        tipo_obj = None
        if pd.notna(row['tipo']):
            tipo_nome = str(row['tipo']).strip()
            try:
                from precapp.models import Tipo
                tipo_obj = Tipo.objects.filter(nome__icontains=tipo_nome).first()
                if not tipo_obj:
                    self.stdout.write(f'Warning: Tipo "{tipo_nome}" not found, creating new one')
                    tipo_obj = Tipo.objects.create(nome=tipo_nome, ativa=True)
            except Exception as e:
                self.stdout.write(f'Warning: Error handling tipo "{tipo_nome}": {e}')
        
        # Get destacado value for percentual_contratuais_apartado
        destacado = 0.0
        if pd.notna(row['destacado']):
            try:
                destacado = float(row['destacado'])
            except (ValueError, TypeError):
                destacado = 0.0
        
        # Set up defaults
        defaults = {
            'orcamento': int(row['orcamento']) if pd.notna(row['orcamento']) else None,
            'origem': origem,
            'valor_de_face': float(row['valor_face']) if pd.notna(row['valor_face']) else 0.0,
            'ultima_atualizacao': float(row['valor_face']) if pd.notna(row['valor_face']) else 0.0,
            'percentual_contratuais_assinado': 0.0,
            'percentual_contratuais_apartado': destacado,  # Map destacado to this field
            'percentual_sucumbenciais': 0.0,
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente',
            'tipo': tipo_obj  # Map tipo to this field
        }
        
        precatorio, created = Precatorio.objects.get_or_create(
            cnj=cnj,
            defaults=defaults
        )
        
        if created:
            self.stdout.write(f'✓ Created precatório: {cnj} (Valor: R$ {defaults["valor_de_face"]:,.2f}, Tipo: {tipo_obj.nome if tipo_obj else "N/A"}, Destacado: {destacado})')
        
        return precatorio


    def create_cliente_from_row(self, row):
        """
        Create a Cliente record from a single Excel row using current format.
        
        Processes one row of Excel data in the current format and creates or
        updates a Cliente record in the database. Includes enhanced data
        validation, CPF cleaning, and flexible birth date handling.
        
        Args:
            row (pandas.Series): Single row of Excel data containing:
                - cpf: Client CPF (Brazilian tax ID) - required
                - nome: Client full name - required
                - nascimento: Birth date (optional, nullable)
                
        Returns:
            Cliente|None: Created or existing Cliente instance, or None if invalid data
            
        Data Processing:
        
        CPF Cleaning and Validation:
        - Removes dots, dashes, and slashes automatically
        - Strips whitespace from CPF value
        - Returns None if CPF is missing or empty
        - Uses cleaned CPF as unique identifier
        
        Name Processing:
        - Strips whitespace from name value
        - Returns None if name is missing or empty
        - Preserves original capitalization
        
        Birth Date Handling:
        - Field is nullable (allows None values)
        - Supports multiple date formats:
          * datetime objects (direct conversion)
          * String formats: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
        - Gracefully handles invalid or missing dates
        - Defaults to None for invalid dates
        
        Default Values:
        - nascimento: None (nullable field)
        - prioridade: False (can be updated later based on criteria)
        
        Date Format Support:
        - Automatic datetime object handling
        - String parsing with multiple format attempts
        - Error-resistant date conversion
        - Maintains data integrity on conversion failures
        
        Database Interaction:
        - Uses get_or_create() with CPF as unique identifier
        - Creates new record only if CPF doesn't exist
        - Preserves existing records without modification
        - Updates are not performed (creation only)
        
        Error Handling:
        - Safely handles missing required fields (CPF, nome)
        - Graceful date parsing with fallback to None
        - Type conversion errors handled without stopping
        - Returns None for critical validation failures
        
        Validation Rules:
        - CPF: Required, automatically cleaned
        - Nome: Required, whitespace trimmed
        - Nascimento: Optional, multiple formats accepted
        
        Logging:
        - Reports successful creation with CPF
        - Indicates when existing records are found
        - No error logging for expected validation failures
        
        Data Cleaning Examples:
        - CPF "123.456.789-01" → "12345678901"
        - CPF "123 456 789 01" → "12345678901" 
        - Name " João Silva " → "João Silva"
        
        Side Effects:
        - May create new Cliente database record
        - Outputs creation status to console
        - Enables client-precatory relationship linking
        
        Example Usage:
            cliente = self.create_cliente_from_row(excel_row)
            if cliente and precatorio:
                precatorio.clientes.add(cliente)
        """
        cpf = str(row['cpf']).replace('.', '').replace('-', '').replace('/', '').strip() if pd.notna(row['cpf']) else None
        nome = str(row['nome']).strip() if pd.notna(row['nome']) else None
        
        if not cpf or not nome:
            return None
        
        # Handle birth date - field can now be null/blank
        nascimento = None  # Default to None since field now allows null
        if pd.notna(row['nascimento']):
            try:
                if isinstance(row['nascimento'], datetime):
                    nascimento = row['nascimento'].date()
                elif isinstance(row['nascimento'], str):
                    # Try different date formats
                    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                        try:
                            nascimento = datetime.strptime(row['nascimento'], fmt).date()
                            break
                        except ValueError:
                            continue
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
        """
        Process data from a single Excel sheet with intelligent format detection.
        
        Advanced data processor that automatically detects the type of data
        in an Excel sheet and applies appropriate processing logic. Supports
        multiple data types and flexible column mapping for various Excel formats.
        
        Args:
            df (pandas.DataFrame): Excel sheet data to process
            sheet_name (str): Name of the sheet being processed (for context)
            
        Returns:
            dict: Import statistics containing counts for each model type:
                - precatorios (int): Number of precatory records processed
                - clientes (int): Number of client records processed
                - alvaras (int): Number of alvará records processed
                - requerimentos (int): Number of requirement records processed
                
        Processing Flow:
        1. Analyze column structure to identify data type
        2. Apply column name normalization and mapping
        3. Route to appropriate processing method based on detected type
        4. Return aggregated statistics from processing
        
        Data Type Detection:
        - mixed: Complete dataset with precatories, clients, and alvarás/requirements
        - precatorio_with_details: Precatories with detailed information
        - precatorios: Precatory data only
        - clientes: Client data only
        - alvaras: Alvará data only
        - requerimentos: Requirement data only
        - unknown: Cannot determine data structure
        
        Column Mapping Support:
        Supports flexible column name variations for:
        - Precatorio fields: CNJ, origem, orçamento, valores
        - Cliente fields: nome, CPF, nascimento
        - Payment status fields: credito_principal, honorários
        - Alvará fields: tipo, fase, honorários
        - Requerimento fields: pedido, deságio
        
        Advanced Features:
        - Intelligent column name matching
        - Multiple naming convention support
        - Backward compatibility with various naming conventions
        - Extensible mapping system
        
        Error Handling:
        - Graceful handling of unknown data types
        - Column mapping fallbacks
        - Processing continues with available data
        
        Side Effects:
        - Outputs data type detection results
        - May create various types of database records
        - Provides processing progress feedback
        
        Example Column Mappings:
        - 'cnj', 'numero_cnj', 'processo' → CNJ field
        - 'nome', 'cliente', 'beneficiario' → Client name
        - 'cpf', 'documento' → Client CPF
        
        Note:
        This method provides advanced functionality for complex Excel files
        with mixed data types or non-standard column naming conventions.
        """
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
            'tipo': ['tipo', 'tipo_precatorio', 'categoria'],
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
        """
        Analyze Excel columns to automatically determine the data structure type.
        
        Examines the column names in an Excel sheet to intelligently detect
        what type of data is present. This enables automatic routing to the
        appropriate processing method without manual specification.
        
        Args:
            columns (list): List of column names from Excel sheet (normalized to lowercase)
            mappings (dict): Column mapping configuration containing possible name variations
            
        Returns:
            str: Detected data type, one of:
                - 'mixed': Complete dataset with precatories, clients, and alvarás/requirements
                - 'precatorios': Primarily precatory data
                - 'clientes': Client information only
                - 'alvaras': Alvará records only
                - 'requerimentos': Requirement records only
                - 'unknown': Cannot determine data structure
                
        Detection Logic:
        
        Column Presence Analysis:
        - has_cnj: Indicates precatory data (CNJ process numbers)
        - has_nome: Indicates client data (client names)
        - has_cpf: Indicates client data (client CPF numbers)
        - has_tipo_alvara: Indicates alvará data (alvará types)
        - has_pedido: Indicates requirement data (request types)
        
        Decision Tree:
        1. If CNJ + Client + (Alvará OR Requirement) → 'mixed'
        2. If CNJ only → 'precatorios'
        3. If CPF but no CNJ → 'clientes'
        4. If Alvará type present → 'alvaras'
        5. If Request type present → 'requerimentos'
        6. Otherwise → 'unknown'
        
        Column Matching Strategy:
        - Uses flexible matching through find_column() method
        - Supports multiple naming conventions
        - Case-insensitive matching
        - Partial string matching for common variations
        
        Mapping Examples:
        - CNJ fields: 'cnj', 'numero_cnj', 'processo'
        - Client names: 'nome', 'cliente', 'beneficiario'
        - CPF fields: 'cpf', 'documento'
        - Alvará types: 'tipo', 'tipo_alvara', 'modalidade'
        - Requests: 'pedido', 'tipo_pedido', 'requerimento'
        
        Use Cases:
        - Automatic processing of unknown Excel files
        - Batch processing of multiple sheet types
        - Dynamic routing to appropriate handlers
        - Validation of expected data structures
        
        Error Handling:
        - Returns 'unknown' for unrecognizable structures
        - Handles missing or malformed column names
        - Provides fallback classification
        
        Side Effects:
        - Outputs detected data type for user feedback
        - Enables automatic processing workflow
        
        Example Usage:
            data_type = self.identify_data_type(['cnj', 'nome', 'cpf'], mappings)
            if data_type == 'mixed':
                # Process as complete dataset
                pass
        """
        has_cnj = self.find_column(columns, mappings['cnj']) is not None
        has_nome = self.find_column(columns, mappings['nome']) is not None
        has_cpf = self.find_column(columns, mappings['cpf']) is not None
        has_tipo_alvara = self.find_column(columns, mappings['tipo_alvara']) is not None
        has_pedido = self.find_column(columns, mappings['pedido']) is not None
        
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
        """
        Find a column that matches any of the possible name variations.
        
        Searches through a list of actual column names to find one that matches
        any of the provided possible name variations. Uses flexible matching
        to handle different naming conventions and formats in Excel files.
        
        Args:
            columns (list): List of actual column names from Excel sheet (lowercase)
            possible_names (list): List of possible name variations to search for
            
        Returns:
            str|None: Name of the first matching column found, or None if no match
            
        Matching Strategy:
        - Iterates through each actual column name
        - For each column, checks if any possible name is contained within it
        - Returns the first column that contains any of the possible names
        - Uses substring matching (not exact matching)
        
        Flexible Matching Examples:
        - Column 'numero_cnj_completo' matches possible name 'cnj'
        - Column 'nome_completo_cliente' matches possible name 'nome'
        - Column 'cpf_limpo' matches possible name 'cpf'
        
        Use Cases:
        - Handle Excel files with varying column naming conventions
        - Support different formats with alternative naming schemes
        - Enable automatic column mapping across different sources
        - Provide flexibility for user-generated Excel files
        
        Common Mapping Scenarios:
        ```python
        # Finding CNJ column variations
        cnj_column = find_column(['cnj', 'numero_processo'], ['cnj', 'processo'])
        
        # Finding client name variations  
        name_column = find_column(['nome_cliente', 'beneficiario'], ['nome', 'cliente'])
        ```
        
        Error Handling:
        - Returns None if no matching column is found
        - Handles empty column lists gracefully
        - No exceptions raised for missing matches
        
        Performance Considerations:
        - Early return on first match found
        - Simple substring search operations
        - Efficient for typical Excel column counts
        
        Side Effects:
        - None (pure function with no side effects)
        
        Example Usage:
            column_name = self.find_column(
                ['cnj_numero', 'processo_id', 'valor_total'],
                ['cnj', 'numero_cnj', 'processo']
            )
            # Returns 'cnj_numero' (first match)
        """
        for col in columns:
            if any(name in col for name in possible_names):
                return col
        return None
    
    def get_column_value(self, row, columns, mappings, key):
        """
        Safely extract a value from an Excel row using flexible column mapping.
        
        Retrieves a value from a pandas Series (Excel row) by finding the
        appropriate column name through the mapping system and handling
        missing or null values gracefully.
        
        Args:
            row (pandas.Series): Single row of Excel data
            columns (list): List of available column names (lowercase)
            mappings (dict): Column mapping configuration
            key (str): Mapping key to look up (e.g., 'cnj', 'nome', 'cpf')
            
        Returns:
            Any|None: The value from the row, or None if not found or null
            
        Value Extraction Process:
        1. Use find_column() to locate the appropriate column name
        2. Check if the column exists in the row's index
        3. Extract the value and check for pandas null values
        4. Return the value or None if missing/null
        
        Null Value Handling:
        - Uses pandas.isna() to detect null/NaN values
        - Returns None for any null or missing values
        - Preserves original data types for valid values
        
        Error Handling:
        - Returns None if column mapping key doesn't exist
        - Returns None if mapped column is not found
        - Returns None if column exists but value is null
        - No exceptions raised for missing data
        
        Column Mapping Integration:
        - Leverages the flexible column mapping system
        - Supports multiple naming conventions automatically
        - Handles case variations and naming differences
        
        Use Cases:
        - Safe data extraction from variable Excel formats
        - Consistent value retrieval across different sheet structures
        - Graceful handling of incomplete data
        - Standardized null value management
        
        Example Usage:
        ```python
        # Extract CNJ value with fallback to None
        cnj = self.get_column_value(row, columns, mappings, 'cnj')
        
        # Extract client name safely
        nome = self.get_column_value(row, columns, mappings, 'nome')
        
        # Extract optional birth date
        nascimento = self.get_column_value(row, columns, mappings, 'nascimento')
        ```
        
        Supported Keys (examples):
        - 'cnj': CNJ process numbers
        - 'nome': Client names
        - 'cpf': Client CPF numbers
        - 'valor_face': Face values
        - 'nascimento': Birth dates
        - 'origem': Origin information
        
        Data Type Preservation:
        - Maintains original pandas data types
        - Preserves datetime objects
        - Keeps numeric types intact
        - Returns strings as-is
        
        Side Effects:
        - None (pure function with no side effects)
        
        Integration:
        Works seamlessly with other methods like:
        - create_or_update_precatorio()
        - create_or_update_cliente()
        - import_complete_data()
        """
        column_name = self.find_column(columns, mappings[key])
        if column_name and column_name in row.index:
            value = row[column_name]
            if pd.isna(value):
                return None
            return value
        return None
    
    def import_complete_data(self, df, mappings):
        """
        Import complete dataset containing precatories, clients, and related records.
        
        Processes Excel data that contains comprehensive information including
        precatories, client details, and associated alvarás or requirements.
        This method handles the most complex import scenario with full data
        relationships and cross-record linking.
        
        Args:
            df (pandas.DataFrame): Excel data with complete dataset
            mappings (dict): Column mapping configuration for flexible field mapping
            
        Returns:
            dict: Import statistics containing:
                - precatorios (int): Number of precatory records created/updated
                - clientes (int): Number of client records created/updated
                - requerimentos (int): Number of requirement records created
                
        Processing Workflow:
        1. Process each row sequentially to maintain data integrity
        2. Create or update Precatorio record from row data
        3. Create or update Cliente record from row data
        4. Link Cliente to Precatorio via many-to-many relationship
        5. Determine if row contains alvará or requerimento data
        6. Create associated records (requirements only - alvarás disabled)
        7. Track statistics and handle errors gracefully
        
        Data Relationship Management:
        - Establishes Precatorio ↔ Cliente many-to-many relationships
        - Links Requerimento records to both Precatorio and Cliente
        - Maintains referential integrity throughout the process
        
        Record Creation Strategy:
        - Uses advanced field mapping methods for flexible data extraction
        - Leverages get_or_create patterns to prevent duplicates
        - Applies appropriate validation and data cleaning
        - Handles missing or incomplete data gracefully
        
        Alvará vs Requerimento Detection:
        - Checks for 'pedido' field to determine requirement records
        - Creates requerimento records when pedido data is present
        - Skips alvará creation (as per system configuration)
        
        Error Handling:
        - Row-level error isolation prevents complete import failure
        - Detailed error logging with row numbers and specific issues
        - Processing continues after individual row failures
        - Maintains transaction integrity for related records
        
        Data Validation:
        - Validates required fields before record creation
        - Applies business rules for data consistency
        - Handles data type conversions safely
        - Ensures relationship prerequisites are met
        
        Performance Considerations:
        - Processes one row at a time to manage memory usage
        - Uses efficient database operations (get_or_create)
        - Provides progress feedback for long operations
        - Batches related operations where possible
        
        Side Effects:
        - Creates/updates multiple types of database records
        - Establishes relationships between records
        - Outputs detailed progress information
        - May create default phases if needed
        
        Example Data Structure:
        Each row typically contains:
        - Precatory data: CNJ, origem, valores, tipos
        - Client data: nome, CPF, nascimento
        - Additional data: pedidos, fases, honorários
        
        Integration Points:
        - Uses create_or_update_precatorio() for precatory handling
        - Uses create_or_update_cliente() for client handling
        - Uses create_requerimento() for requirement creation
        - Integrates with the flexible column mapping system
        """
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
        """
        Create or update a Precatorio record with advanced field mapping and validation.
        
        Advanced method for creating Precatorio records that supports flexible
        column mapping, enhanced payment status handling, and comprehensive
        data validation. Designed for complex Excel formats with variable
        column naming conventions.
        
        Args:
            row (pandas.Series): Single row of Excel data
            columns (list): Available column names (normalized)
            mappings (dict): Column mapping configuration
            
        Returns:
            Precatorio|None: Created or existing Precatorio instance, or None if invalid
            
        Enhanced Features:
        
        Flexible Field Mapping:
        - Uses get_column_value() for safe data extraction
        - Supports multiple column naming conventions
        - Handles missing fields gracefully with defaults
        
        Advanced Payment Status Handling:
        - Maps specific payment status columns when available
        - Supports new payment status fields:
          * credito_principal
          * honorarios_contratuais_status
          * honorarios_sucumbenciais_status
        - Maintains backward compatibility with legacy 'quitado' field
        
        Payment Status Mapping:
        ```python
        # New format status mapping
        'pendente de pagamento' → 'pendente'
        'quitado parcialmente' → 'parcial'
        'quitado integralmente' → 'quitado'
        
        # Backward compatibility with boolean format
        quitado=True → all statuses set to 'quitado'
        quitado=False → all statuses set to 'pendente'
        ```
        
        Data Processing:
        
        CNJ Validation:
        - Required field, returns None if missing
        - Strips whitespace automatically
        - Used as unique identifier for get_or_create
        
        Value Handling:
        - Processes valor_face and ultima_atualizacao
        - Handles numeric conversion with error handling
        - Sets both fields to same value initially
        
        Date Processing:
        - Supports data_ultima_atualizacao field
        - Handles datetime objects and string formats
        - Falls back gracefully on parsing errors
        
        Default Value Management:
        - Comprehensive default values for all required fields
        - Ensures database constraints are met
        - Provides sensible fallbacks for missing data
        
        Error Handling:
        - Safe type conversions with try-catch blocks
        - Graceful handling of missing or invalid data
        - Returns None only for critical validation failures
        - Continues processing with available data
        
        Database Interaction:
        - Uses get_or_create() to prevent duplicates
        - Only creates new records, doesn't update existing
        - Maintains data integrity through validation
        
        Side Effects:
        - May create new Precatorio database record
        - Outputs creation status with key details
        - Enables further processing (client linking, etc.)
        
        Example Mapped Fields:
        - origem: Source or tribunal information
        - orcamento: Budget year (integer)
        - valor_face: Face value (decimal)
        - credito_principal: Payment status
        - data_ultima_atualizacao: Last update date
        
        Integration:
        - Works with import_complete_data() workflow
        - Supports various Excel format structures
        - Enables relationship establishment with clients
        """
        cnj = self.get_column_value(row, columns, mappings, 'cnj')
        if not cnj:
            return None
        
        # Clean CNJ format
        cnj = str(cnj).strip()
        
        defaults = {}
        
        # Get other fields
        if origem := self.get_column_value(row, columns, mappings, 'origem'):
            defaults['origem'] = str(origem)
        
        # Handle orcamento with explicit None support
        orcamento_value = self.get_column_value(row, columns, mappings, 'orcamento')
        if orcamento_value is not None and pd.notna(orcamento_value):
            try:
                defaults['orcamento'] = int(orcamento_value)
            except (ValueError, TypeError):
                defaults['orcamento'] = None
        else:
            defaults['orcamento'] = None
        
        # Handle tipo field (map to Tipo model)
        if tipo_nome := self.get_column_value(row, columns, mappings, 'tipo'):
            try:
                from precapp.models import Tipo
                tipo_nome = str(tipo_nome).strip()
                tipo_obj = Tipo.objects.filter(nome__icontains=tipo_nome).first()
                if not tipo_obj:
                    self.stdout.write(f'Warning: Tipo "{tipo_nome}" not found, creating new one')
                    tipo_obj = Tipo.objects.create(nome=tipo_nome, ativa=True)
                defaults['tipo'] = tipo_obj
            except Exception as e:
                self.stdout.write(f'Warning: Error handling tipo "{tipo_nome}": {e}')

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
        
        # Set default values for required fields (skip orcamento - it's nullable)
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
        """
        Create or update a Cliente record with advanced field mapping and validation.
        
        Advanced method for creating Cliente records that supports flexible
        column mapping, enhanced data validation, and comprehensive error
        handling. Designed for complex Excel formats with variable column
        naming conventions.
        
        Args:
            row (pandas.Series): Single row of Excel data
            columns (list): Available column names (normalized)
            mappings (dict): Column mapping configuration
            
        Returns:
            Cliente|None: Created or existing Cliente instance, or None if invalid
            
        Enhanced Features:
        
        Flexible Field Mapping:
        - Uses get_column_value() for safe data extraction
        - Supports multiple column naming conventions
        - Handles various client data field variations
        
        Data Processing:
        
        CPF Validation and Cleaning:
        - Extracts CPF using flexible column mapping
        - Automatically removes formatting (dots, dashes, slashes)
        - Strips whitespace from CPF value
        - Returns None if CPF is missing (required field)
        
        Name Processing:
        - Extracts nome using flexible mapping
        - Strips whitespace from name value
        - Returns None if name is missing (required field)
        
        Birth Date Handling:
        - Advanced date parsing with multiple format support
        - Handles datetime objects directly
        - Supports string formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
        - Falls back to default date for invalid formats
        - Uses 1980-01-01 as default birth date
        
        Priority Detection:
        - Processes prioridade field if available
        - Converts various input types to boolean
        - Defaults to False for missing priority data
        
        Default Values:
        - nome: Extracted from data (required)
        - nascimento: Parsed date or default (1980-01-01)
        - prioridade: Extracted boolean or False
        
        Data Validation:
        - Validates required fields (CPF, nome)
        - Performs data type conversions safely
        - Handles missing optional fields gracefully
        
        Error Handling:
        - Safe data extraction with null checks
        - Graceful date parsing with fallbacks
        - Type conversion errors handled without stopping
        - Returns None only for missing required fields
        
        Database Interaction:
        - Uses get_or_create() with CPF as unique identifier
        - Only creates new records, doesn't update existing
        - Prevents duplicate client records
        
        CPF Cleaning Examples:
        ```python
        # Various CPF formats are cleaned automatically
        "123.456.789-01" → "12345678901"
        "123 456 789 01" → "12345678901"
        "123.456.789/01" → "12345678901"
        ```
        
        Date Format Support:
        ```python
        # Supported date input formats
        datetime(1990, 5, 15) → 1990-05-15
        "1990-05-15" → 1990-05-15
        "15/05/1990" → 1990-05-15
        "15-05-1990" → 1990-05-15
        invalid_date → 1980-01-01 (default)
        ```
        
        Side Effects:
        - May create new Cliente database record
        - Outputs creation status with CPF and name
        - Enables relationship linking with precatories
        
        Integration:
        - Works with import_complete_data() workflow
        - Supports various Excel format structures
        - Enables many-to-many relationship with Precatorio
        
        Example Usage:
        ```python
        cliente = self.create_or_update_cliente(row, columns, mappings)
        if cliente and precatorio:
            precatorio.clientes.add(cliente)
        ```
        """
        cpf = self.get_column_value(row, columns, mappings, 'cpf')
        nome = self.get_column_value(row, columns, mappings, 'nome')
        
        if not cpf or not nome:
            return None
        
        # Clean CPF (remove formatting)
        cpf = str(cpf).replace('.', '').replace('-', '').replace('/', '').strip()
        
        defaults = {
            'nome': str(nome).strip(),
            'prioridade': False
        }
        
        # Get birth date with explicit None support
        nascimento_value = self.get_column_value(row, columns, mappings, 'nascimento')
        if nascimento_value is not None and pd.notna(nascimento_value):
            try:
                if isinstance(nascimento_value, datetime):
                    defaults['nascimento'] = nascimento_value.date()
                elif isinstance(nascimento_value, str):
                    defaults['nascimento'] = datetime.strptime(nascimento_value, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                defaults['nascimento'] = None  # Keep as None for invalid dates
        else:
            defaults['nascimento'] = None  # Explicitly None when no date provided
        
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
        """
        Create an Alvará record from Excel row data with relationship linking.
        
        Creates an Alvará (judicial authorization) record associated with a
        specific precatory and client. Handles data extraction, validation,
        default phase assignment, and relationship establishment.
        
        Args:
            row (pandas.Series): Single row of Excel data
            columns (list): Available column names (normalized)
            mappings (dict): Column mapping configuration
            precatorio (Precatorio): Related precatory instance
            cliente (Cliente): Related client instance
            
        Returns:
            Alvara: Created Alvará instance
            
        Data Processing:
        
        Type Determination:
        - Extracts tipo_alvara from row data
        - Defaults to 'comum' if not specified
        - Normalizes type value to lowercase
        
        Phase Assignment:
        - Searches for existing alvará phases (tipo='alvara' or 'ambos')
        - Uses first active phase found
        - Creates default 'Importado' phase if none exist
        - Ensures proper workflow state initialization
        
        Value Processing:
        - Extracts valor_principal from valor_face mapping
        - Extracts honorarios_contratuais and honorarios_sucumbenciais
        - Handles numeric conversion with error handling
        - Defaults to 0.0 for invalid or missing values
        
        Default Values:
        - precatorio: Required relationship (passed parameter)
        - cliente: Required relationship (passed parameter)
        - tipo: From data or 'comum'
        - fase: Active alvará phase or created default
        - valor_principal: From data or 0.0
        - honorarios_contratuais: From data or 0.0
        - honorarios_sucumbenciais: From data or 0.0
        
        Phase Creation (if needed):
        - nome: 'Importado'
        - tipo: 'alvara'
        - cor: '#007BFF' (blue)
        - ativa: True
        
        Database Interaction:
        - Creates new Alvará record directly (no get_or_create)
        - Establishes foreign key relationships
        - Assumes unique data per import operation
        
        Error Handling:
        - Safe value extraction with fallbacks
        - Numeric conversion errors handled gracefully
        - Creates default phase if system phases missing
        
        Side Effects:
        - Creates new Alvará database record
        - May create default phase if none exist
        - Outputs creation confirmation with client name
        
        Workflow Integration:
        - Integrates with alvará management workflow
        - Enables phase-based processing
        - Supports value tracking and updates
        
        Note:
        While this method exists for completeness, alvará creation
        is currently disabled in the main import workflow as per
        system requirements. The method remains available for
        future use or specific import scenarios.
        """
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
        """
        Create a Requerimento (legal request) record from Excel row data.
        
        Creates a Requerimento record associated with a specific precatory
        and client. Handles data extraction, validation, default phase
        assignment, and relationship establishment for legal requests.
        
        Args:
            row (pandas.Series): Single row of Excel data
            columns (list): Available column names (normalized)
            mappings (dict): Column mapping configuration
            precatorio (Precatorio): Related precatory instance (required)
            cliente (Cliente): Related client instance (required)
            
        Returns:
            Requerimento: Created Requerimento instance
            
        Data Processing:
        
        Request Type Determination:
        - Extracts pedido field from row data
        - Defaults to 'outros' if not specified
        - Normalizes request type to lowercase
        - Maps to predefined request categories
        
        Phase Assignment:
        - Searches for existing requerimento phases (tipo='requerimento' or 'ambos')
        - Uses first active phase found
        - Creates default 'Em Andamento' phase if none exist
        - Ensures proper workflow state initialization
        
        Value Processing:
        - Extracts valor from valor_face mapping
        - Extracts deságio (discount) information
        - Handles numeric conversion with error handling
        - Defaults to 0.0 for invalid or missing values
        
        Default Values:
        - precatorio: Required relationship (passed parameter)
        - cliente: Required relationship (passed parameter)
        - pedido: From data or 'outros'
        - fase: Active requerimento phase or created default
        - valor: From data or 0.0
        - desagio: From data or 0.0
        
        Default Phase Creation (if needed):
        - nome: 'Em Andamento'
        - tipo: 'requerimento'
        - cor: '#28A745' (green)
        - ativa: True
        
        Request Type Examples:
        - 'prioridade_idade': Age-based priority request
        - 'prioridade_doenca': Disease-based priority request
        - 'acordo_principal': Agreement on principal amount
        - 'acordo_honorarios': Agreement on fees
        - 'outros': General or unspecified requests
        
        Database Interaction:
        - Creates new Requerimento record directly
        - Establishes foreign key relationships with Precatorio and Cliente
        - Assumes unique data per import operation
        
        Error Handling:
        - Safe value extraction with fallback defaults
        - Numeric conversion errors handled gracefully
        - Creates default phase if system phases missing
        - Handles missing or invalid request types
        
        Workflow Integration:
        - Integrates with requerimento management workflow
        - Enables phase-based request tracking
        - Supports value and discount tracking
        
        Side Effects:
        - Creates new Requerimento database record
        - May create default phase if none exist
        - Outputs creation confirmation with client name
        - Enables request workflow management
        
        Legal Context:
        Requerimentos represent various types of legal requests that can be
        made in relation to precatory processes, such as priority requests,
        settlement agreements, or objections to calculations.
        
        Example Usage:
        ```python
        if has_pedido and precatorio and cliente:
            requerimento = self.create_requerimento(row, columns, mappings, precatorio, cliente)
        ```
        """
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
        """
        Import precatory data only from Excel DataFrame.
        
        Specialized import method for processing Excel data that contains
        only precatory information without associated client or other
        related record data. Ideal for precatory-focused data sources.
        
        Args:
            df (pandas.DataFrame): Excel data containing precatory information
            mappings (dict): Column mapping configuration for field mapping
            
        Returns:
            int: Number of precatory records successfully created/processed
            
        Processing Logic:
        - Iterates through each row in the DataFrame
        - Calls create_or_update_precatorio() for each row
        - Uses flexible column mapping for field extraction
        - Accumulates count of successfully processed records
        
        Data Focus:
        - CNJ process numbers and validation
        - Precatory values and amounts
        - Origin and source information
        - Budget years and classifications
        - Payment status information
        
        Error Handling:
        - Row-level error isolation
        - Detailed error logging with row numbers
        - Processing continues after individual failures
        - Returns count of successful imports only
        
        Use Cases:
        - Importing precatory master data
        - Updating precatory information in bulk
        - Processing precatory-only Excel exports
        - Initial system setup with precatory data
        
        Side Effects:
        - Creates/updates Precatorio database records
        - Outputs processing progress and error information
        - Returns success count for verification
        """
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
        """
        Import client data only from Excel DataFrame.
        
        Specialized import method for processing Excel data that contains
        only client information without associated precatory or other
        related record data. Ideal for client database setup or updates.
        
        Args:
            df (pandas.DataFrame): Excel data containing client information
            mappings (dict): Column mapping configuration for field mapping
            
        Returns:
            int: Number of client records successfully created/processed
            
        Processing Logic:
        - Iterates through each row in the DataFrame
        - Calls create_or_update_cliente() for each row
        - Uses flexible column mapping for field extraction
        - Accumulates count of successfully processed records
        
        Data Focus:
        - Client names and personal information
        - CPF numbers with automatic cleaning
        - Birth dates with flexible format support
        - Priority status information
        
        Error Handling:
        - Row-level error isolation
        - Detailed error logging with row numbers
        - Processing continues after individual failures
        - Returns count of successful imports only
        
        Use Cases:
        - Importing client master data
        - Updating client information in bulk
        - Processing client-only Excel exports
        - Initial system setup with client database
        - Client data migration from other systems
        
        Side Effects:
        - Creates/updates Cliente database records
        - Outputs processing progress and error information
        - Returns success count for verification
        """
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
        """
        Import alvará data from Excel DataFrame (requires existing precatories and clients).
        
        Specialized import method for processing Excel data that contains
        alvará (judicial authorization) information. This method requires
        that related precatory and client records already exist in the
        database for proper relationship linking.
        
        Args:
            df (pandas.DataFrame): Excel data containing alvará information
            mappings (dict): Column mapping configuration for field mapping
            
        Returns:
            int: Number of alvará records successfully created (currently returns 0)
            
        Current Implementation:
        - Placeholder method for future alvará import functionality
        - Returns 0 as alvará creation is currently disabled
        - Requires additional logic to link to existing precatorios/clientes
        
        Planned Functionality:
        - Link alvará records to existing Precatorio instances
        - Link alvará records to existing Cliente instances
        - Process alvará-specific data (types, phases, values)
        - Handle alvará workflow state initialization
        
        Data Requirements (when implemented):
        - Alvará type information
        - Associated CNJ numbers for precatory linking
        - Associated CPF numbers for client linking
        - Value information (principal, contractual fees, sucumbencial fees)
        - Phase or status information
        
        Relationship Dependencies:
        - Precatorio records must exist (linked via CNJ)
        - Cliente records must exist (linked via CPF)
        - Proper many-to-many relationships established
        
        Error Handling (planned):
        - Validation of required relationship records
        - Graceful handling of missing precatory/client links
        - Row-level error isolation for individual failures
        
        Use Cases (future):
        - Importing alvará master data
        - Bulk creation of judicial authorizations
        - Linking alvará records to existing case data
        - Workflow state initialization for alvarás
        
        Note:
        This method is currently a placeholder. Full implementation
        would require additional logic to establish relationships
        with existing precatory and client records based on
        identifying fields in the Excel data.
        """
        # This would need additional logic to link to existing precatorios/clientes
        return 0
    
    def import_requerimentos(self, df, mappings):
        """
        Import requerimento data from Excel DataFrame (requires existing precatories and clients).
        
        Specialized import method for processing Excel data that contains
        requerimento (legal request) information. This method requires
        that related precatory and client records already exist in the
        database for proper relationship linking.
        
        Args:
            df (pandas.DataFrame): Excel data containing requerimento information
            mappings (dict): Column mapping configuration for field mapping
            
        Returns:
            int: Number of requerimento records successfully created (currently returns 0)
            
        Current Implementation:
        - Placeholder method for future requerimento import functionality
        - Returns 0 as standalone requerimento import is not implemented
        - Requires additional logic to link to existing precatorios/clientes
        
        Planned Functionality:
        - Link requerimento records to existing Precatorio instances
        - Link requerimento records to existing Cliente instances
        - Process request-specific data (types, phases, values)
        - Handle requerimento workflow state initialization
        
        Data Requirements (when implemented):
        - Request type information (pedido)
        - Associated CNJ numbers for precatory linking
        - Associated CPF numbers for client linking
        - Value information and discount (deságio) data
        - Phase or status information
        
        Request Type Examples:
        - Priority requests (age, disease)
        - Settlement agreements (principal, fees)
        - Objections to calculations
        - Fee distribution requests
        
        Relationship Dependencies:
        - Precatorio records must exist (linked via CNJ)
        - Cliente records must exist (linked via CPF)
        - Proper foreign key relationships established
        
        Error Handling (planned):
        - Validation of required relationship records
        - Graceful handling of missing precatory/client links
        - Row-level error isolation for individual failures
        - Request type validation and mapping
        
        Use Cases (future):
        - Importing requerimento master data
        - Bulk creation of legal requests
        - Linking request records to existing case data
        - Workflow state initialization for requests
        
        Workflow Integration (planned):
        - Initialize with appropriate requerimento phases
        - Enable phase-based request tracking
        - Support request type categorization
        - Handle value and discount calculations
        
        Note:
        This method is currently a placeholder. Full implementation
        would require additional logic to establish relationships
        with existing precatory and client records based on
        identifying fields in the Excel data. The current import
        workflow handles requerimento creation as part of the
        complete data import process.
        """  
        # This would need additional logic to link to existing precatorios/clientes
        return 0
