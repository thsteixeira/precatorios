from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime

# Create your models here.
class Precatorio(models.Model):
    cnj = models.CharField(max_length=200, primary_key=True)
    data_oficio = models.DateField()
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
    ultima_atualizacao = models.FloatField()
    data_ultima_atualizacao = models.DateField()
    percentual_contratuais_assinado = models.FloatField()
    percentual_contratuais_apartado = models.FloatField()
    percentual_sucumbenciais = models.FloatField()
    prioridade_deferida = models.BooleanField()
    acordo_deferido = models.BooleanField()
    clientes = models.ManyToManyField('Cliente', related_name='precatorios')

    def __str__(self):
        return f"{self.cnj} - {self.origem}"

    class Meta:
        verbose_name = "Precatório"
        verbose_name_plural = "Precatórios"
        ordering = ['-data_oficio']


class Cliente(models.Model):
    cpf = models.CharField(max_length=11, primary_key=True)
    nome = models.CharField(max_length=400)
    nascimento = models.DateField()
    prioridade = models.BooleanField()

    def __str__(self):
        return f"{self.nome} - {self.cpf}"


class Alvara(models.Model):
    precatorio = models.ForeignKey(Precatorio, on_delete=models.CASCADE, to_field='cnj')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, to_field='cpf')
    valor_principal = models.FloatField()
    honorarios_contratuais = models.FloatField()
    honorarios_sucumbenciais = models.FloatField()
    tipo = models.CharField(max_length=100)
    fase = models.CharField(max_length=100)

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
    fase = models.CharField(max_length=100)

    def __str__(self):
        return f"Requerimento - {self.pedido} - {self.cliente.nome}"
    
    # Removed list/set logic since only one choice is allowed
    
    class Meta:
        verbose_name = "Requerimento"
        verbose_name_plural = "Requerimentos"