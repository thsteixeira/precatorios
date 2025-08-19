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
        ordering = ['tipo', 'nome']
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
        ordering = ['nome']

class Precatorio(models.Model):
    cnj = models.CharField(max_length=200, primary_key=True)
    orcamento = models.IntegerField(
        validators=[
            MinValueValidator(1988),
            MaxValueValidator(2050)
        ],
        help_text="Ano do orçamento (formato: YYYY)"
    )
    origem = models.CharField(max_length=200)
    quitado = models.BooleanField()
    valor_de_face = models.FloatField()
    ultima_atualizacao = models.FloatField(null=True, blank=True)
    data_ultima_atualizacao = models.DateField(null=True, blank=True)
    percentual_contratuais_assinado = models.FloatField(null=True, blank=True)
    percentual_contratuais_apartado = models.FloatField(null=True, blank=True)
    percentual_sucumbenciais = models.FloatField(null=True, blank=True)
    acordo_deferido = models.BooleanField()
    clientes = models.ManyToManyField('Cliente', related_name='precatorios')

    def __str__(self):
        return f"{self.cnj} - {self.origem}"

    class Meta:
        verbose_name = "Precatório"
        verbose_name_plural = "Precatórios"
        ordering = ['cnj']  # Changed from data_oficio to cnj


class Cliente(models.Model):
    cpf = models.CharField(max_length=11, primary_key=True)
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