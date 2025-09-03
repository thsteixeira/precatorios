"""
Django management command for setting up system customization data.

This command creates default phases, types, and configurations needed for the
precatory management system to function properly. It should be run during
initial system setup or when resetting the system to default configurations.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from precapp.models import Fase, FaseHonorariosContratuais, TipoDiligencia, Tipo, PedidoRequerimento


class Command(BaseCommand):
    """
    Management command for setting up system customization data.
    
    Creates all the default phases, types, and configurations needed for the
    precatory management system. This includes workflow phases, diligence types,
    precatory classifications, and request types.
    
    Usage:
        python manage.py setup_customization
        
    Features:
    - Creates default workflow phases for different process types
    - Sets up standard diligence activity types
    - Establishes precatory classification categories
    - Creates legal request type definitions
    - Uses database transactions for data integrity
    - Prevents duplicate entries with get_or_create logic
    - Provides detailed feedback about creation status
    """
    
    help = 'Set up default phases, types, and configurations for the system'
    
    def handle(self, *args, **options):
        """
        Execute the customization setup process.
        
        Coordinates the creation of all default system data including phases,
        diligence types, precatory types, and request types. Uses database
        transactions to ensure data integrity.
        
        Args:
            *args: Positional arguments (unused)
            **options: Command options (unused)
            
        Process Flow:
            1. Start database transaction
            2. Create main workflow phases
            3. Create diligence types
            4. Create precatory types
            5. Create request types
            6. Commit transaction and report results
            
        Error Handling:
            - Database transaction ensures atomicity
            - Individual creation methods handle duplicates gracefully
            - Detailed error reporting for debugging
            
        Output:
            - Progress messages for each creation step
            - Count of newly created items by category
            - Success confirmation upon completion
        """
        self.stdout.write(self.style.SUCCESS('Setting up system customization...'))
        
        try:
            with transaction.atomic():
                self.create_main_phases()
                self.create_tipos_diligencia()
                self.create_tipos_precatorio()
                self.create_tipos_pedido_requerimento()
                
            self.stdout.write(self.style.SUCCESS('System customization setup completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Setup failed: {str(e)}'))
            raise
    
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
        
        self.stdout.write('\\n=== CREATING MAIN PHASES ===')
        
        # Requerimento phases
        requerimento_phases = [
            {
                'nome': 'Organizar Documentos',
                'descricao': 'Fase inicial para organização dos documentos necessários',
                'cor': '#17a2b8',
                'ativa': True,
                'ordem': 1,
                'tipo': 'requerimento',
            },
            {
                'nome': 'Protocolado',
                'descricao': 'Requerimento protocolado e em análise',
                'cor': '#ffc107',
                'ativa': True,
                'ordem': 2,
                'tipo': 'requerimento',
            },
            {
                'nome': 'Deferido',
                'descricao': 'Requerimento deferido e aprovado',
                'cor': '#28a745',
                'ativa': True,
                'ordem': 3,
                'tipo': 'requerimento',
            },
            {
                'nome': 'Indeferido',
                'descricao': 'Requerimento indeferido e negado',
                'cor': '#dc3545',
                'ativa': True,
                'ordem': 4,
                'tipo': 'requerimento',
            }
        ]
        
        # Alvará phases
        alvara_phases = [
            {
                'nome': 'Aguardando Depósito Judicial',
                'descricao': 'Aguardando o depósito do valor pelo tribunal',
                'cor': "#d9ff00",
                'ativa': True,
                'ordem': 1,
                'tipo': 'alvara',
            },
            {
                'nome': 'Aguardando Atualização pela Contadoria',
                'descricao': 'Aguardando cálculos de atualização pela contadoria',
                'cor': "#ff07ea",
                'ativa': True,
                'ordem': 2,
                'tipo': 'alvara',
            },
            {
                'nome': 'Para manifestar de cálculos',
                'descricao': 'Aguardando manifestação sobre os cálculos',
                'cor': '#fd7e14',
                'ativa': True,
                'ordem': 3,
                'tipo': 'alvara',
            },
            {
                'nome': 'Cálculos impugnados',
                'descricao': 'Cálculos foram impugnados',
                'cor': '#dc3545',
                'ativa': True,
                'ordem': 4,
                'tipo': 'alvara',
            },
            {
                'nome': 'Para informar conta',
                'descricao': 'Solicitado informações de conta bancária',
                'cor': '#20c997',
                'ativa': True,
                'ordem': 5,
                'tipo': 'alvara',
            },
            {
                'nome': 'Contas bancárias informadas',
                'descricao': 'Informações bancárias foram fornecidas',
                'cor': '#6f42c1',
                'ativa': True,
                'ordem': 6,
                'tipo': 'alvara',
            },
            {
                'nome': 'Recebido Pelo Cliente',
                'descricao': 'Valor foi recebido pelo cliente',
                'cor': "#001aff",
                'ativa': True,
                'ordem': 7,
                'tipo': 'alvara',
            }
        ]
        
        created_req = 0
        created_alv = 0
        created_hon = 0
        
        # Create Requerimento phases
        for phase_data in requerimento_phases:
            fase, created = Fase.objects.get_or_create(
                nome=phase_data['nome'],
                tipo=phase_data['tipo'],
                defaults={
                    'descricao': phase_data['descricao'],
                    'cor': phase_data['cor'],
                    'ativa': phase_data['ativa'],
                    'ordem': phase_data['ordem']
                }
            )
            if created:
                created_req += 1
                self.stdout.write(f'✓ Created Requerimento fase: {fase.nome} (ordem: {fase.ordem})')
        
        # Create Alvará phases  
        for phase_data in alvara_phases:
            fase, created = Fase.objects.get_or_create(
                nome=phase_data['nome'],
                tipo=phase_data['tipo'],
                defaults={
                    'descricao': phase_data['descricao'],
                    'cor': phase_data['cor'],
                    'ativa': phase_data['ativa'],
                    'ordem': phase_data['ordem']
                }
            )
            if created:
                created_alv += 1
                self.stdout.write(f'✓ Created Alvará fase: {fase.nome} (ordem: {fase.ordem})')
        
        # Create Honorários phases
        honorarios_phases = [
            {
                'nome': 'Aguardando Depósito Judicial',
                'descricao': 'Aguardando depósito dos honorários pelo tribunal diretamente à HT',
                'cor': "#fffb00",
                'ativa': True,
                'ordem': 1
            },
            {
                'nome': 'Aguardando Pagamento ao Cliente',
                'descricao': 'Aguardando pagamento ao Cliente pelo tribunal',
                'cor': "#ff00dd",
                'ativa': True,
                'ordem': 2
            },
            {
                'nome': 'Cobrar Cliente',
                'descricao': 'Cobrar do cliente o pagamento dos honorários contratuais',
                'cor': '#fd7e14',
                'ativa': True,
                'ordem': 3
            },
            {
                'nome': 'Quitado parcialmente',
                'descricao': 'Honorários contratuais pagos parcialmente',
                'cor': "#ff0707",
                'ativa': True,
                'ordem': 4
            },
            {
                'nome': 'Quitado integralmente',
                'descricao': 'Honorários contratuais pagos integralmente',
                'cor': "#0004ff",
                'ativa': True,
                'ordem': 5
            }
        ]
        
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
                self.stdout.write(f'✓ Created Honorários fase: {fase.nome} (ordem: {fase.ordem})')
        
        # Summary
        if created_req > 0 or created_alv > 0 or created_hon > 0:
            self.stdout.write(f'\\n=== PHASES CREATION SUMMARY ===')
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
        
        self.stdout.write('\\n=== CREATING TIPOS DE DILIGÊNCIA ===')
        
        diligencia_types = [
            {
                'nome': 'Propor repactuação',
                'descricao': 'Propor nova negociação dos termos do acordo',
                'cor': '#007bff',
                'ordem': 1
            },
            {
                'nome': 'Solicitar RG',
                'descricao': 'Solicitar documento de identidade do cliente',
                'cor': '#28a745',
                'ordem': 2
            },
            {
                'nome': 'Solicitar contrato',
                'descricao': 'Solicitar documentação contratual',
                'cor': '#ffc107',
                'ordem': 3
            },
            {
                'nome': 'Cobrar honorários',
                'descricao': 'Realizar cobrança de honorários devidos',
                'cor': '#fd7e14',
                'ordem': 4
            },
            {
                'nome': 'Executar honorários',
                'descricao': 'Executar judicialmente honorários em aberto',
                'cor': '#dc3545',
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
            self.stdout.write(f'\\n=== TIPOS DE DILIGÊNCIA CREATED ===')
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
        
        self.stdout.write('\\n=== CREATING TIPOS DE PRECATÓRIO ===')
        
        tipos_precatorio = [
            {
                'nome': 'Descompressão',
                'descricao': 'Precatórios oriundos de processos de descompressão salarial',
                'cor': '#007bff',
                'ordem': 1,
                'ativa': True
            },
            {
                'nome': 'URV',
                'descricao': 'Precatórios relacionados à Unidade Real de Valor',
                'cor': '#28a745',
                'ordem': 2,
                'ativa': True
            },
            {
                'nome': 'Reclassificação',
                'descricao': 'Precatórios de processos de reclassificação de cargo',
                'cor': '#ffc107',
                'ordem': 3,
                'ativa': True
            },
            {
                'nome': 'Revisão de proventos',
                'descricao': 'Precatórios de processos de revisão de proventos',
                'cor': "#ff0707",
                'ordem': 4,
                'ativa': True
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
                    'ativa': tipo_data['ativa']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'✓ Created Tipo: {tipo.nome} (ordem: {tipo.ordem})')
        
        if created_count > 0:
            self.stdout.write(f'\\n=== TIPOS DE PRECATÓRIO CREATED ===')
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
        
        1. Expedição de Alvará:
           - Request for issuance of judicial authorization
           - Standard procedural request for payment authorization
           
        2. Pedido de Atualização de Valores:
           - Request for value updates and corrections
           - Common for inflation adjustments and interest calculations
           
        3. Execução dos Honorários Contratuais:
           - Request for execution of contractual fees
           - Legal action to collect outstanding attorney fees
           
        4. Cessão de Crédito:
           - Request for credit assignment/transfer
           - Legal procedure to transfer precatory rights
        
        Each type includes:
        - nome (str): Request type name
        - descricao (str): Detailed description of the request
        - cor (str): Color code for UI categorization (hex format)
        - ordem (int): Display order for consistent sorting
        - ativa (bool): Whether the type is active for new requests
        
        Color Scheme:
        - Blue (#007bff): Standard procedural requests
        - Green (#28a745): Financial/value-related requests  
        - Orange (#fd7e14): Fee collection requests
        - Purple (#6f42c1): Transfer/assignment requests
        
        Model Used:
        - PedidoRequerimento: Stores request type definitions
        
        Behavior:
        - Uses get_or_create() to prevent duplicate types
        - Sets all types as active by default
        - Provides detailed creation feedback
        - Reports count of newly created types
        
        Side Effects:
        - Creates database records for request types
        - Enables request categorization in the system
        - Provides structured options for legal requests
        """
        
        self.stdout.write('\\n=== CREATING TIPOS DE PEDIDO REQUERIMENTO ===')
        
        tipos_pedido = [
            {
                'nome': 'Expedição de Alvará',
                'descricao': 'Pedido para expedição de alvará judicial de levantamento',
                'cor': '#007bff',
                'ordem': 1,
                'ativo': True
            },
            {
                'nome': 'Pedido de Atualização de Valores',
                'descricao': 'Solicitação de atualização monetária dos valores',
                'cor': '#28a745',
                'ordem': 2,
                'ativo': True
            },
            {
                'nome': 'Execução dos Honorários Contratuais',
                'descricao': 'Execução judicial dos honorários contratuais devidos',
                'cor': '#fd7e14',
                'ordem': 3,
                'ativo': True
            },
            {
                'nome': 'Cessão de Crédito',
                'descricao': 'Pedido de cessão de direitos creditórios do precatório',
                'cor': '#6f42c1',
                'ordem': 4,
                'ativo': True
            }
        ]
        
        created_count = 0
        
        for tipo_data in tipos_pedido:
            tipo, created = PedidoRequerimento.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults={
                    'descricao': tipo_data['descricao'],
                    'cor': tipo_data['cor'],
                    'ordem': tipo_data['ordem'],
                    'ativo': tipo_data['ativo']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'✓ Created PedidoRequerimento: {tipo.nome} (ordem: {tipo.ordem})')
        
        if created_count > 0:
            self.stdout.write(f'\\n=== TIPOS DE PEDIDO REQUERIMENTO CREATED ===')
            self.stdout.write(f'Created {created_count} new tipos de pedido requerimento')
        else:
            self.stdout.write('All tipos de pedido requerimento already exist')
        
        self.stdout.write('')
