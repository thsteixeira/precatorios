from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime

# Create your models here.

class Fase(models.Model):
    """Model for custom phases that can be used in Alvarás and Requerimentos"""
    
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
        """Get active phases that can be used for Alvarás"""
        return cls.objects.filter(ativa=True, tipo__in=['alvara', 'ambos'])
    
    @classmethod
    def get_fases_for_requerimento(cls):
        """Get active phases that can be used for Requerimentos"""
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
    """Model for custom phases specifically for Honorários Contratuais tracking"""
    
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
        """Get active phases for honorários contratuais"""
        return cls.objects.filter(ativa=True)
    
    class Meta:
        verbose_name = "Fase Honorários Contratuais"
        verbose_name_plural = "Fases Honorários Contratuais"
        ordering = ['ordem', 'nome']

class Precatorio(models.Model):
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
    clientes = models.ManyToManyField('Cliente', related_name='precatorios')

    def __str__(self):
        return f"{self.cnj} - {self.origem}"

    class Meta:
        verbose_name = "Precatório"
        verbose_name_plural = "Precatórios"
        ordering = ['cnj']  # Changed from data_oficio to cnj


class Cliente(models.Model):
    cpf = models.CharField(max_length=18, primary_key=True, help_text="CPF ou CNPJ do cliente")
    nome = models.CharField(max_length=400)
    nascimento = models.DateField()
    prioridade = models.BooleanField()

    def __str__(self):
        return f"{self.nome} - {self.cpf}"
    
    def get_priority_requerimentos(self):
        """Get all priority requerimentos (idade/doença) for this cliente"""
        priority_reqs = []
        
        # Only get requerimentos that actually belong to THIS cliente
        for req in Requerimento.objects.filter(cliente=self):
            if req.pedido in ['prioridade idade', 'prioridade doença']:
                priority_reqs.append(req)
        
        return priority_reqs


class TipoDiligencia(models.Model):
    """Model for customizable diligence types"""
    
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
        """Return only active diligence types"""
        return cls.objects.filter(ativo=True)
    
    class Meta:
        verbose_name = "Tipo de Diligência"
        verbose_name_plural = "Tipos de Diligência"
        ordering = ['ordem', 'nome']


class Diligencias(models.Model):
    """Model for diligences related to clients"""
    
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
        """Check if the diligence is overdue"""
        from django.utils import timezone
        if not self.concluida and self.data_final < timezone.now().date():
            return True
        return False
    
    def days_until_deadline(self):
        """Calculate days until deadline"""
        from django.utils import timezone
        if self.concluida:
            return None
        today = timezone.now().date()
        delta = (self.data_final - today).days
        return delta
    
    def get_urgencia_color(self):
        """Get Bootstrap color class based on urgency level"""
        urgencia_colors = {
            'baixa': 'secondary',
            'media': 'warning',
            'alta': 'danger',
        }
        return urgencia_colors.get(self.urgencia, 'secondary')
    
    @property
    def criado_em(self):
        """Alias for data_criacao to maintain consistency with template"""
        return self.data_criacao
    
    @property  
    def criador(self):
        """Alias for criado_por to maintain consistency with form field"""
        return self.criado_por
    
    class Meta:
        verbose_name = "Diligência"
        verbose_name_plural = "Diligências"
        ordering = ['-data_criacao']


class Alvara(models.Model):
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
        """Validate that the cliente is linked to the precatorio"""
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
        """Override save to call clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.cliente.nome}"
    

class Requerimento(models.Model):
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
        """Validate that the cliente is linked to the precatorio"""
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
        """Override save to call clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Requerimento - {self.pedido} - {self.cliente.nome}"
    
    def get_pedido_abreviado(self):
        """Return abbreviated version of pedido"""
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