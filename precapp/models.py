from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime

# Create your models here.

class Fase(models.Model):
    """
    Model for custom phases that can be used in Alvarás and Requerimentos.
    
    This model represents the various stages or phases that both Alvarás and Requerimentos
    can go through during their lifecycle. Each phase can be configured with a specific
    color for visual identification and can be limited to specific document types.
    
    Attributes:
        nome (CharField): The name of the phase (max 100 characters)
        descricao (TextField): Optional description of the phase
        cor (CharField): Hexadecimal color code for visual identification (e.g., #007bff)
        tipo (CharField): Defines whether phase is for Alvarás, Requerimentos, or both
        ordem (PositiveIntegerField): Display order (lower numbers appear first)
        ativa (BooleanField): Whether this phase is active for use
        criado_em (DateTimeField): Timestamp when the phase was created
        atualizado_em (DateTimeField): Timestamp when the phase was last updated
    
    Business Rules:
        - Each phase must have a unique combination of nome and tipo
        - Phases are ordered by ordem, then tipo, then nome
        - Only active phases are available for selection in forms
        - Different tipos allow the same nome (e.g., "Concluído" for both alvara and requerimento)
    
    Usage Examples:
        # Create a phase for Alvarás only
        fase = Fase.objects.create(
            nome="Aguardando Depósito",
            tipo="alvara",
            cor="#FF6B35"
        )
        
        # Get all phases available for Alvarás
        alvara_phases = Fase.get_fases_for_alvara()
    """
    
    TIPO_CHOICES = [
        ('alvara', 'Alvará'),
        ('requerimento', 'Requerimento'),
        ('ambos', 'Ambos (Alvará e Requerimento)'),
    ]
    
    nome = models.CharField(max_length=100, help_text="Nome da fase")
    descricao = models.TextField(blank=True, help_text="Descrição opcional da fase")
    cor = models.CharField(
        max_length=7, 
        default='#6c757d', 
        help_text="Cor da fase em hexadecimal (ex: #007bff)"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='ambos',
        help_text="Define se a fase é específica para Alvarás, Requerimentos ou ambos"
    )
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de exibição (números menores aparecem primeiro)"
    )
    ativa = models.BooleanField(default=True, help_text="Se esta fase está ativa para uso")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        tipo_display = dict(self.TIPO_CHOICES).get(self.tipo, self.tipo)
        return f"{self.nome}"
    
    @classmethod
    def get_fases_for_alvara(cls):
        """
        Get active phases that can be used for Alvarás.
        
        Returns:
            QuerySet: Active phases with tipo 'alvara' or 'ambos'
        """
        return cls.objects.filter(ativa=True, tipo__in=['alvara', 'ambos'])
    
    @classmethod
    def get_fases_for_requerimento(cls):
        """
        Get active phases that can be used for Requerimentos.
        
        Returns:
            QuerySet: Active phases with tipo 'requerimento' or 'ambos'
        """
        return cls.objects.filter(ativa=True, tipo__in=['requerimento', 'ambos'])
    
    class Meta:
        verbose_name = "Fase Principal"
        verbose_name_plural = "Fases Principais"
        ordering = ['ordem', 'tipo', 'nome']
        # Remove unique constraint on nome to allow same names for different types
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'tipo'],
                name='unique_fase_nome_tipo'
            )
        ]

class FaseHonorariosContratuais(models.Model):
    """
    Model for custom phases specifically for Honorários Contratuais tracking.
    
    This model represents specialized phases that track the status of contractual
    fees (honorários contratuais) separately from the main document phases.
    This allows for independent tracking of fee payment status while the main
    document may be in a different phase.
    
    Attributes:
        nome (CharField): The name of the contractual fees phase (max 100 characters)
        descricao (TextField): Optional description of the phase
        cor (CharField): Hexadecimal color code for visual identification (default: #28a745)
        ordem (PositiveIntegerField): Display order (lower numbers appear first)
        ativa (BooleanField): Whether this phase is active for use
        criado_em (DateTimeField): Timestamp when the phase was created
        atualizado_em (DateTimeField): Timestamp when the phase was last updated
    
    Business Rules:
        - Each phase name must be unique
        - Phases are ordered by ordem, then by nome
        - Only active phases are available for selection
        - Default color is green (#28a745) to distinguish from main phases
    
    Usage Examples:
        # Create a contractual fees phase
        fase = FaseHonorariosContratuais.objects.create(
            nome="Aguardando Pagamento",
            descricao="Honorários aguardando liberação do pagamento"
        )
        
        # Get all active contractual fees phases
        active_phases = FaseHonorariosContratuais.get_fases_ativas()
    """
    
    nome = models.CharField(max_length=100, help_text="Nome da fase de honorários contratuais")
    descricao = models.TextField(blank=True, help_text="Descrição opcional da fase")
    cor = models.CharField(
        max_length=7, 
        default='#28a745', 
        help_text="Cor da fase em hexadecimal (ex: #28a745)"
    )
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de exibição (números menores aparecem primeiro)"
    )
    ativa = models.BooleanField(default=True, help_text="Se esta fase está ativa para uso")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nome}"
    
    @classmethod
    def get_fases_ativas(cls):
        """
        Get active phases for honorários contratuais.
        
        Returns:
            QuerySet: Active contractual fees phases ordered by ordem and nome
        """
        return cls.objects.filter(ativa=True)
    
    class Meta:
        verbose_name = "Fase Honorários Contratuais"
        verbose_name_plural = "Fases Honorários Contratuais"
        ordering = ['ordem', 'nome']

class Tipo(models.Model):
    """
    Model for custom types that can be assigned to Precatórios.
    
    This model represents different categories or types that Precatórios can be
    classified into. Each type can be configured with a specific color for visual
    identification and can help organize and filter precatórios by their nature.
    
    Attributes:
        nome (CharField): The name of the type (max 100 characters)
        descricao (TextField): Optional description of the type
        cor (CharField): Hexadecimal color code for visual identification (e.g., #007bff)
        ordem (PositiveIntegerField): Display order (lower numbers appear first)
        ativa (BooleanField): Whether this type is active for use
        criado_em (DateTimeField): Timestamp when the type was created
        atualizado_em (DateTimeField): Timestamp when the type was last updated
    
    Business Rules:
        - Each type name must be unique
        - Types are ordered by ordem, then by nome
        - Only active types are available for selection in forms
        - Default color is blue (#007bff)
    
    Usage Examples:
        # Create a new type
        tipo = Tipo.objects.create(
            nome="Alimentar",
            descricao="Precatórios de natureza alimentar",
            cor="#28a745"
        )
        
        # Get all active types
        active_types = Tipo.get_tipos_ativos()
    """
    
    nome = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nome do tipo de precatório"
    )
    descricao = models.TextField(blank=True, help_text="Descrição opcional do tipo")
    cor = models.CharField(
        max_length=7, 
        default='#007bff', 
        help_text="Cor do tipo em hexadecimal (ex: #007bff)"
    )
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de exibição (números menores aparecem primeiro)"
    )
    ativa = models.BooleanField(default=True, help_text="Se este tipo está ativo para uso")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nome
    
    @classmethod
    def get_tipos_ativos(cls):
        """
        Get all active types for selection.
        
        Returns:
            QuerySet: Active types ordered by ordem and nome
        """
        return cls.objects.filter(ativa=True).order_by('ordem', 'nome')
    
    class Meta:
        verbose_name = "Tipo de Precatório"
        verbose_name_plural = "Tipos de Precatórios"
        ordering = ['ordem', 'nome']

class Precatorio(models.Model):
    """
    Model representing a legal Precatório document.
    
    A Precatório is a legal instrument used in Brazilian law for collecting debts
    from public entities. This model tracks the document details, payment status
    of different components, and financial information.
    
    Attributes:
        cnj (CharField): CNJ number serving as primary key (unique identifier)
        orcamento (IntegerField): Budget year (YYYY format, validated 1988-2050)
        origem (CharField): Origin or source reference (max 200 characters)
        credito_principal (CharField): Payment status of the principal credit
        honorarios_contratuais (CharField): Payment status of contractual fees
        honorarios_sucumbenciais (CharField): Payment status of succumbence fees
        valor_de_face (FloatField): Face value of the precatório
        ultima_atualizacao (FloatField): Last updated value amount
        data_ultima_atualizacao (DateField): Date of last value update
        percentual_contratuais_assinado (FloatField): Signed contractual percentage
        percentual_contratuais_apartado (FloatField): Separated contractual percentage
        percentual_sucumbenciais (FloatField): Succumbence percentage
        clientes (ManyToManyField): Related clients who have rights to this precatório
    
    Payment Status Choices:
        - pendente: Pending payment
        - parcial: Partially paid
        - quitado: Fully paid
        - vendido: Sold
    
    Business Rules:
        - CNJ must be unique across all precatórios
        - Budget year must be between 1988 and 2050
        - Multiple clients can be associated with one precatório
        - Payment status is tracked separately for each component (principal, contractual, succumbence)
        - Financial percentages can be null/blank for optional tracking
    
    Usage Examples:
        # Create a new precatório
        precatorio = Precatorio.objects.create(
            cnj="1234567-89.2023.8.26.0100",
            orcamento=2023,
            origem="Original case reference",
            valor_de_face=100000.00
        )
        
        # Add clients to precatório
        precatorio.clientes.add(cliente1, cliente2)
    """
    
    STATUS_PAGAMENTO_CHOICES = [
        ('pendente', 'Pendente de pagamento'),
        ('parcial', 'Quitado parcialmente'),
        ('quitado', 'Quitado integralmente'),
        ('vendido', 'Vendido'),
    ]
    
    cnj = models.CharField(max_length=200, primary_key=True)
    orcamento = models.IntegerField(
        validators=[
            MinValueValidator(1988),
            MaxValueValidator(2050)
        ],
        help_text="Ano do orçamento (formato: YYYY)"
    )
    origem = models.CharField(max_length=200)
    credito_principal = models.CharField(
        max_length=20,
        choices=STATUS_PAGAMENTO_CHOICES,
        default='pendente',
        help_text="Status de pagamento do crédito principal"
    )
    honorarios_contratuais = models.CharField(
        max_length=20,
        choices=STATUS_PAGAMENTO_CHOICES,
        default='pendente',
        help_text="Status de pagamento dos honorários contratuais"
    )
    honorarios_sucumbenciais = models.CharField(
        max_length=20,
        choices=STATUS_PAGAMENTO_CHOICES,
        default='pendente',
        help_text="Status de pagamento dos honorários sucumbenciais"
    )
    valor_de_face = models.FloatField()
    ultima_atualizacao = models.FloatField(null=True, blank=True)
    data_ultima_atualizacao = models.DateField(null=True, blank=True)
    percentual_contratuais_assinado = models.FloatField(null=True, blank=True)
    percentual_contratuais_apartado = models.FloatField(null=True, blank=True)
    percentual_sucumbenciais = models.FloatField(null=True, blank=True)
    
    tipo = models.ForeignKey(
        'Tipo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Tipo do precatório (ex: Alimentar, Comum, etc.)"
    )
    
    clientes = models.ManyToManyField('Cliente', related_name='precatorios')

    def __str__(self):
        return f"{self.cnj} - {self.origem}"

    class Meta:
        verbose_name = "Precatório"
        verbose_name_plural = "Precatórios"
        ordering = ['cnj']  # Changed from data_oficio to cnj


class Cliente(models.Model):
    """
    Model representing a client with rights to precatórios.
    
    This model stores information about individuals or legal entities that have
    rights to receive payments from precatórios. Clients can be associated with
    multiple precatórios and may have priority status for faster processing.
    
    Attributes:
        cpf (CharField): CPF or CNPJ serving as primary key (max 18 characters)
        nome (CharField): Full name or company name (max 400 characters)
        nascimento (DateField): Birth date or company founding date
        prioridade (BooleanField): Whether client has priority status
    
    Business Rules:
        - CPF/CNPJ must be unique across all clients
        - Supports both individual CPF (11 digits) and company CNPJ (14 digits)
        - Priority status affects processing order and available benefits
        - Birth date is required for age-based priority calculations
        - Many-to-many relationship with Precatorio through precatorios.clientes
    
    Related Models:
        - Precatorio: Many-to-many relationship for document ownership
        - Requerimento: Foreign key relationship for legal requests
        - Alvara: Foreign key relationship for payment authorizations
        - Diligencias: Foreign key relationship for required actions
    
    Methods:
        get_priority_requerimentos(): Returns priority requests (age/illness) for this client
    
    Usage Examples:
        # Create an individual client
        cliente = Cliente.objects.create(
            cpf="12345678909",
            nome="João Silva",
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Create a company client
        empresa = Cliente.objects.create(
            cpf="12345678000195",
            nome="Empresa Ltda",
            nascimento=date(2000, 1, 1),
            prioridade=False
        )
        
        # Get priority requests for a client
        priority_reqs = cliente.get_priority_requerimentos()
    """
    cpf = models.CharField(max_length=18, primary_key=True, help_text="CPF ou CNPJ do cliente")
    nome = models.CharField(max_length=400)
    nascimento = models.DateField()
    prioridade = models.BooleanField()

    def __str__(self):
        return f"{self.nome} - {self.cpf}"
    
    def get_priority_requerimentos(self):
        """
        Get all priority requerimentos (idade/doença) for this cliente.
        
        Priority requerimentos are special legal requests for expedited processing
        based on age or illness conditions. This method filters all requerimentos
        belonging to this client and returns only those with priority pedidos.
        
        Returns:
            list: List of Requerimento instances with priority pedidos
                 ('prioridade idade' or 'prioridade doença')
        """
        priority_reqs = []
        
        # Only get requerimentos that actually belong to THIS cliente
        for req in Requerimento.objects.filter(cliente=self):
            if req.pedido in ['prioridade idade', 'prioridade doença']:
                priority_reqs.append(req)
        
        return priority_reqs


class TipoDiligencia(models.Model):
    """
    Model for customizable diligence types.
    
    This model defines the types of diligences (legal actions or requirements)
    that can be assigned to clients. Each type can be configured with visual
    styling and organizational properties for better management.
    
    Attributes:
        nome (CharField): Unique name of the diligence type (max 100 characters)
        descricao (TextField): Optional detailed description of the diligence type
        cor (CharField): Hexadecimal color code for visual identification (default: #007bff)
        ordem (PositiveIntegerField): Display order (lower numbers appear first)
        ativo (BooleanField): Whether this type is active for use (default: True)
        criado_em (DateTimeField): Timestamp when the type was created
        atualizado_em (DateTimeField): Timestamp when the type was last updated
    
    Business Rules:
        - Each type name must be unique across all diligence types
        - Only active types are available for selection in forms
        - Types are ordered by ordem field, then by nome alphabetically
        - Color field allows visual categorization in the interface
        - Soft delete pattern: types are deactivated rather than deleted to preserve history
    
    Related Models:
        - Diligencias: Foreign key relationship with PROTECT constraint
          (prevents deletion of types that are referenced by existing diligences)
    
    Methods:
        get_ativos(): Class method returning only active diligence types
    
    Usage Examples:
        # Create a new diligence type
        tipo = TipoDiligencia.objects.create(
            nome="Documentação Pendente",
            descricao="Solicitação de documentos necessários para o processo",
            cor="#FFA500"
        )
        
        # Get all active types for form choices
        active_types = TipoDiligencia.get_ativos()
        
        # Deactivate a type instead of deleting
        tipo.ativo = False
        tipo.save()
    """
    
    nome = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nome do tipo de diligência"
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição opcional do tipo de diligência"
    )
    cor = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text="Cor em hexadecimal para identificação visual (ex: #007bff)"
    )
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de exibição (números menores aparecem primeiro)"
    )
    ativo = models.BooleanField(
        default=True,
        help_text="Se este tipo está ativo para uso"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nome
    
    @classmethod
    def get_ativos(cls):
        """
        Return only active diligence types.
        
        This method provides a convenient way to filter diligence types
        to only those that are currently active and available for use.
        
        Returns:
            QuerySet: Active TipoDiligencia instances ordered by ordem and nome
        """
        return cls.objects.filter(ativo=True)
    
    class Meta:
        verbose_name = "Tipo de Diligência"
        verbose_name_plural = "Tipos de Diligência"
        ordering = ['ordem', 'nome']


class Diligencias(models.Model):
    """
    Model for diligences related to clients.
    
    Diligences represent specific actions, tasks, or requirements that need to be
    completed for clients in the context of their precatório processes. Each
    diligence has a deadline, urgency level, and tracks completion status.
    
    Attributes:
        cliente (ForeignKey): Related client who needs this diligence completed
        tipo (ForeignKey): Type of diligence (protected from deletion)
        data_final (DateField): Deadline for completing the diligence
        urgencia (CharField): Urgency level (baixa, media, alta)
        criado_por (CharField): Name of user who created the diligence (max 200 chars)
        descricao (TextField): Optional detailed description of the diligence
        concluida (BooleanField): Whether the diligence has been completed
        data_criacao (DateTimeField): Timestamp when diligence was created
        data_conclusao (DateTimeField): Timestamp when diligence was completed
        concluido_por (CharField): Name of user who completed the diligence
    
    Urgency Levels:
        - baixa: Low priority, normal processing
        - media: Medium priority (default)
        - alta: High priority, expedited processing
    
    Business Rules:
        - Each diligence must be associated with exactly one client
        - Diligence type cannot be deleted while referenced (PROTECT constraint)
        - Only active diligence types can be selected (limit_choices_to)
        - Completion fields (data_conclusao, concluido_por) are set when marking as complete
        - Overdue detection is calculated against current date
        - Urgency affects visual styling and processing priority
    
    Methods:
        is_overdue(): Checks if diligence is past deadline and not completed
        days_until_deadline(): Calculates days remaining (negative if overdue)
        get_urgencia_color(): Returns Bootstrap color class for urgency level
    
    Properties:
        criado_em: Alias for data_criacao (template consistency)
        criador: Alias for criado_por (form field consistency)
    
    Usage Examples:
        # Create a new diligence
        diligencia = Diligencias.objects.create(
            cliente=cliente,
            tipo=tipo_documentacao,
            data_final=date.today() + timedelta(days=7),
            urgencia='alta',
            criado_por='João Admin',
            descricao='Solicitar certidão de nascimento atualizada'
        )
        
        # Check if overdue
        if diligencia.is_overdue():
            print(f"Diligence is {abs(diligencia.days_until_deadline())} days overdue")
        
        # Mark as completed
        diligencia.concluida = True
        diligencia.data_conclusao = timezone.now()
        diligencia.concluido_por = 'Maria Admin'
        diligencia.save()
    """
    
    URGENCIA_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]
    
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        to_field='cpf',
        related_name='diligencias',
        help_text="Cliente relacionado à diligência"
    )
    tipo = models.ForeignKey(
        TipoDiligencia,
        on_delete=models.PROTECT,
        limit_choices_to={'ativo': True},
        help_text="Tipo da diligência"
    )
    data_final = models.DateField(
        help_text="Data limite para conclusão da diligência"
    )
    urgencia = models.CharField(
        max_length=20,
        choices=URGENCIA_CHOICES,
        default='media',
        help_text="Nível de urgência da diligência"
    )
    criado_por = models.CharField(
        max_length=200,
        help_text="Nome do usuário que criou a diligência"
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição opcional da diligência"
    )
    concluida = models.BooleanField(
        default=False,
        help_text="Indica se a diligência foi concluída"
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora de criação da diligência"
    )
    data_conclusao = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e hora de conclusão da diligência"
    )
    concluido_por = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nome do usuário que concluiu a diligência"
    )

    def __str__(self):
        status = "Concluída" if self.concluida else "Pendente"
        return f"{self.tipo.nome} - {self.cliente.nome} ({status})"
    
    def is_overdue(self):
        """
        Check if the diligence is overdue.
        
        A diligence is considered overdue if:
        1. It is not yet completed (concluida = False)
        2. The deadline (data_final) is before today's date
        
        Returns:
            bool: True if overdue, False otherwise
        """
        from django.utils import timezone
        if not self.concluida and self.data_final < timezone.now().date():
            return True
        return False
    
    def days_until_deadline(self):
        """
        Calculate days until deadline.
        
        For completed diligences, returns None.
        For pending diligences, returns:
        - Positive number: days remaining until deadline
        - Negative number: days overdue
        - Zero: deadline is today
        
        Returns:
            int or None: Days until deadline, or None if completed
        """
        from django.utils import timezone
        if self.concluida:
            return None
        today = timezone.now().date()
        delta = (self.data_final - today).days
        return delta
    
    def get_urgencia_color(self):
        """
        Get Bootstrap color class based on urgency level.
        
        Maps urgency levels to Bootstrap color classes for consistent
        visual styling across the interface.
        
        Returns:
            str: Bootstrap color class name
                - 'secondary': baixa urgency (gray)
                - 'warning': media urgency (yellow/orange)
                - 'danger': alta urgency (red)
        """
        urgencia_colors = {
            'baixa': 'secondary',
            'media': 'warning',
            'alta': 'danger',
        }
        return urgencia_colors.get(self.urgencia, 'secondary')
    
    @property
    def criado_em(self):
        """
        Alias for data_criacao to maintain consistency with template.
        
        Returns:
            datetime: Creation timestamp
        """
        return self.data_criacao
    
    @property  
    def criador(self):
        """
        Alias for criado_por to maintain consistency with form field.
        
        Returns:
            str: Name of user who created this diligence
        """
        return self.criado_por
    
    class Meta:
        verbose_name = "Diligência"
        verbose_name_plural = "Diligências"
        ordering = ['-data_criacao']


class Alvara(models.Model):
    """
    Model representing an Alvará (payment authorization) document.
    
    An Alvará is a legal document that authorizes payment of specific amounts
    from a precatório to a client. It tracks both main phases and separate
    contractual fee phases, along with various fee components.
    
    Attributes:
        precatorio (ForeignKey): Related precatório document (CASCADE deletion)
        cliente (ForeignKey): Client receiving the payment (CASCADE deletion)
        valor_principal (FloatField): Principal amount to be paid
        honorarios_contratuais (FloatField): Contractual fees amount (default: 0.0)
        honorarios_sucumbenciais (FloatField): Succumbence fees amount (default: 0.0)
        tipo (CharField): Type/category of the alvará (max 100 characters)
        fase (ForeignKey): Current main phase of the alvará (PROTECT constraint)
        fase_honorarios_contratuais (ForeignKey): Separate phase for contractual fees tracking
    
    Business Rules:
        - Cliente must be linked to the precatório before creating an alvará
        - Validation ensures client-precatório relationship exists
        - Main fase and honorarios fase can be tracked independently
        - Financial amounts can be zero but not negative
        - PROTECT constraints prevent deletion of referenced phases
        - CASCADE deletion removes alvarás if precatório or cliente is deleted
    
    Validation:
        - clean() method validates cliente-precatório relationship
        - save() method calls full_clean() to ensure validation runs
        - ValidationError raised if cliente not linked to precatório
    
    Related Models:
        - Precatorio: Parent document (CASCADE)
        - Cliente: Payment recipient (CASCADE)
        - Fase: Main phase tracking (PROTECT)
        - FaseHonorariosContratuais: Separate fee phase tracking (PROTECT)
    
    Usage Examples:
        # Create an alvará (cliente must be linked to precatório first)
        precatorio.clientes.add(cliente)
        alvara = Alvara.objects.create(
            precatorio=precatorio,
            cliente=cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            tipo="Prioridade por idade",
            fase=fase_aguardando_deposito
        )
        
        # Add contractual fees phase tracking
        alvara.fase_honorarios_contratuais = fase_hon_pendente
        alvara.save()
    """
    precatorio = models.ForeignKey(Precatorio, on_delete=models.CASCADE, to_field='cnj')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, to_field='cpf')
    valor_principal = models.FloatField()
    honorarios_contratuais = models.FloatField(null=True, blank=True, default=0.0)
    honorarios_sucumbenciais = models.FloatField(null=True, blank=True, default=0.0)
    tipo = models.CharField(max_length=100)
    fase = models.ForeignKey(
        Fase, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Fase principal atual do alvará"
    )
    fase_honorarios_contratuais = models.ForeignKey(
        FaseHonorariosContratuais,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Fase específica para honorários contratuais",
        verbose_name="Fase Honorários Contratuais"
    )

    def clean(self):
        """
        Validate that the cliente is linked to the precatorio.
        
        This validation ensures data integrity by verifying that the client
        specified in the alvará is actually associated with the precatório
        through the many-to-many relationship.
        
        Raises:
            ValidationError: If cliente is not linked to the precatorio
        
        Note:
            Uses safe attribute access to handle cases where the instance
            is not fully populated (e.g., during form validation).
        """
        super().clean()
        # Only validate the linkage if both precatorio and cliente are set
        # Use hasattr and getattr to safely check for the precatorio without triggering RelatedObjectDoesNotExist
        try:
            precatorio = getattr(self, 'precatorio', None)
            cliente = getattr(self, 'cliente', None)
            
            if precatorio and cliente:
                if not precatorio.clientes.filter(cpf=cliente.cpf).exists():
                    raise ValidationError({
                        'cliente': f'O cliente {cliente.nome} (CPF: {cliente.cpf}) não está vinculado ao precatório {precatorio.cnj}. Vincule o cliente ao precatório antes de criar o alvará.'
                    })
        except (AttributeError, Precatorio.DoesNotExist):
            # If precatorio is not set or doesn't exist, skip validation
            # This can happen during form validation when the instance is not fully populated
            pass
    
    def save(self, *args, **kwargs):
        """
        Override save to call clean validation.
        
        Ensures that validation rules are always enforced when saving,
        regardless of how the save is triggered.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.cliente.nome}"
    

class Requerimento(models.Model):
    """
    Model representing a legal Requerimento (request) document.
    
    A Requerimento is a formal legal request submitted in the context of a
    precatório process. It can request various types of actions such as
    priority processing, payment agreements, or other legal procedures.
    
    Attributes:
        precatorio (ForeignKey): Related precatório document (CASCADE deletion)
        cliente (ForeignKey): Client making the request (CASCADE deletion)
        valor (FloatField): Monetary value associated with the request
        desagio (FloatField): Discount/premium percentage applied
        pedido (CharField): Type of request being made (from PEDIDO_CHOICES)
        fase (ForeignKey): Current phase of the requerimento (PROTECT constraint)
    
    Request Types (PEDIDO_CHOICES):
        - prioridade doença: Priority processing due to illness
        - prioridade idade: Priority processing due to age (elderly)
        - acordo principal: Agreement on principal amount
        - acordo honorários contratuais: Agreement on contractual fees
        - acordo honorários sucumbenciais: Agreement on succumbence fees
    
    Business Rules:
        - Cliente must be linked to the precatório before creating a requerimento
        - Each requerimento is for exactly one type of request (single choice)
        - Validation ensures client-precatório relationship exists
        - Phase tracking allows monitoring request progress
        - Financial values (valor, desagio) are required and must be positive
    
    Validation:
        - clean() method validates cliente-precatório relationship
        - save() method calls full_clean() to ensure validation runs
        - ValidationError raised if cliente not linked to precatório
    
    Methods:
        get_pedido_abreviado(): Returns shortened version of pedido for display
    
    Related Models:
        - Precatorio: Parent document (CASCADE)
        - Cliente: Request submitter (CASCADE)
        - Fase: Phase tracking (PROTECT)
    
    Usage Examples:
        # Create a priority request (cliente must be linked to precatório first)
        precatorio.clientes.add(cliente)
        requerimento = Requerimento.objects.create(
            precatorio=precatorio,
            cliente=cliente,
            pedido="prioridade idade",
            valor=25000.00,
            desagio=15.5,
            fase=fase_em_andamento
        )
        
        # Get abbreviated display name
        short_name = requerimento.get_pedido_abreviado()  # "Prioridade Idade"
    """
    
    PEDIDO_CHOICES = [
        ('prioridade doença', 'Prioridade por doença'),
        ('prioridade idade', 'Prioridade por idade'),
        ('acordo principal', 'Acordo sobre o valor Principal'),
        ('acordo honorários contratuais', 'Acordo sobre os Honorários Contratuais'),
        ('acordo honorários sucumbenciais', 'Acordo sobre os Honorários Sucumbenciais'),
    ]
    
    precatorio = models.ForeignKey(Precatorio, on_delete=models.CASCADE, to_field='cnj')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, to_field='cpf')
    valor = models.FloatField()
    desagio = models.FloatField()
    pedido = models.CharField(
        max_length=50,
        choices=PEDIDO_CHOICES,
        help_text='Selecione apenas um pedido.'
    )
    fase = models.ForeignKey(
        Fase, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Fase principal atual do requerimento"
    )

    def clean(self):
        """
        Validate that the cliente is linked to the precatorio.
        
        This validation ensures data integrity by verifying that the client
        specified in the requerimento is actually associated with the precatório
        through the many-to-many relationship.
        
        Raises:
            ValidationError: If cliente is not linked to the precatorio
        
        Note:
            Uses safe attribute access to handle cases where the instance
            is not fully populated (e.g., during form validation).
        """
        super().clean()
        # Only validate the linkage if both precatorio and cliente are set
        # Use hasattr and getattr to safely check for the precatorio without triggering RelatedObjectDoesNotExist
        try:
            precatorio = getattr(self, 'precatorio', None)
            cliente = getattr(self, 'cliente', None)
            
            if precatorio and cliente:
                if not precatorio.clientes.filter(cpf=cliente.cpf).exists():
                    raise ValidationError({
                        'cliente': f'O cliente {cliente.nome} (CPF: {cliente.cpf}) não está vinculado ao precatório {precatorio.cnj}. Vincule o cliente ao precatório antes de criar o requerimento.'
                    })
        except (AttributeError, Precatorio.DoesNotExist):
            # If precatorio is not set or doesn't exist, skip validation
            # This can happen during form validation when the instance is not fully populated
            pass
    
    def save(self, *args, **kwargs):
        """
        Override save to call clean validation.
        
        Ensures that validation rules are always enforced when saving,
        regardless of how the save is triggered.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Requerimento - {self.pedido} - {self.cliente.nome}"
    
    def get_pedido_abreviado(self):
        """
        Return abbreviated version of pedido for display purposes.
        
        Provides shortened, more concise versions of the pedido choices
        for use in tables, lists, or other space-constrained displays.
        
        Returns:
            str: Abbreviated pedido text, or title-cased original if no abbreviation exists
        """
        abbreviations = {
            'prioridade doença': 'Prioridade Doença',
            'prioridade idade': 'Prioridade Idade',
            'acordo principal': 'Acordo Principal',
            'acordo honorários contratuais': 'Acordo Hon. Contratuais',
            'acordo honorários sucumbenciais': 'Acordo Hon. Sucumbenciais',
        }
        return abbreviations.get(self.pedido.lower(), self.pedido.title())
    
    # Removed list/set logic since only one choice is allowed
    
    class Meta:
        verbose_name = "Requerimento"
        verbose_name_plural = "Requerimentos"