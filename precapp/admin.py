from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import (
    Precatorio, Cliente, Alvara, Requerimento, Fase, Tipo,
    FaseHonorariosContratuais, FaseHonorariosSucumbenciais, TipoDiligencia, Diligencias, PedidoRequerimento,
    ContaBancaria, Recebimentos
)
from .forms import CustomFileWidget

# Custom admin configurations

class ClienteInline(admin.TabularInline):
    """Inline for managing clientes within precatorio admin"""
    model = Precatorio.clientes.through
    extra = 1
    verbose_name = "Cliente Vinculado"
    verbose_name_plural = "Clientes Vinculados"


class AlvaraInline(admin.TabularInline):
    """Inline for managing alvaras within precatorio admin"""
    model = Alvara
    extra = 0
    fields = ('cliente', 'valor_principal', 'tipo', 'fase', 'fase_honorarios_contratuais', 'fase_honorarios_sucumbenciais', 'fase_alterada_por')
    readonly_fields = ('fase_alterada_por', 'fase_honorarios_alterada_por', 'fase_honorarios_sucumbenciais_alterada_por')


class RequerimentoInline(admin.TabularInline):
    """Inline for managing requerimentos within precatorio admin"""
    model = Requerimento
    extra = 0
    fields = ('cliente', 'pedido', 'valor', 'desagio', 'fase', 'fase_alterada_por')
    readonly_fields = ('fase_alterada_por',)


class DiligenciasInline(admin.TabularInline):
    """Inline for managing diligencias within cliente admin"""
    model = Diligencias
    extra = 0
    fields = ('tipo', 'data_final', 'urgencia', 'responsavel', 'concluida', 'descricao')
    readonly_fields = ('data_criacao',)


class RecebimentosInline(admin.TabularInline):
    """Inline for managing payments within alvara admin"""
    model = Recebimentos
    extra = 0
    fields = ('numero_documento', 'data', 'conta_bancaria', 'valor', 'tipo', 'criado_por')
    readonly_fields = ('criado_por',)


@admin.register(Precatorio)
class PrecatorioAdmin(admin.ModelAdmin):
    """Admin configuration for Precatorio model"""
    
    list_display = (
        'cnj', 'orcamento', 'origem_short', 'credito_principal_display', 
        'honorarios_contratuais_display', 'honorarios_sucumbenciais_display', 
        'valor_de_face_formatted', 'tipo_colored', 'has_pdf', 'clientes_count', 'alvaras_count', 'requerimentos_count'
    )
    list_filter = (
        'orcamento', 'credito_principal', 'honorarios_contratuais', 
        'honorarios_sucumbenciais', 'tipo'
    )
    search_fields = ('cnj', 'origem', 'clientes__nome', 'clientes__cpf')
    ordering = ('-orcamento', 'cnj')
    
    fieldsets = (
        ('Identificação', {
            'fields': ('cnj', 'orcamento', 'origem', 'tipo')
        }),
        ('Status de Pagamento', {
            'fields': ('credito_principal', 'honorarios_contratuais', 'honorarios_sucumbenciais'),
            'classes': ('collapse',)
        }),
        ('Valores', {
            'fields': ('valor_de_face', 'ultima_atualizacao', 'data_ultima_atualizacao'),
            'classes': ('collapse',)
        }),
        ('Percentuais', {
            'fields': ('percentual_contratuais_assinado', 'percentual_contratuais_apartado', 'percentual_sucumbenciais'),
            'classes': ('collapse',),
            'description': 'Percentual apartado é preenchido automaticamente pela coluna "Destacado" durante importação'
        }),
        ('Documentos e Observações', {
            'fields': ('observacao', 'integra_precatorio'),
            'classes': ('collapse',),
            'description': 'Observações gerais e documentos relacionados ao precatório'
        }),
        ('Relacionamentos', {
            'fields': ('clientes',),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('clientes',)
    inlines = [AlvaraInline, RequerimentoInline]
    
    # Custom widget configuration for textarea fields
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form to use custom file widget for existing objects"""
        form = super().get_form(request, obj, **kwargs)
        
        # Use custom file widget for editing existing precatorios
        if obj and obj.pk and obj.cnj:
            form.base_fields['integra_precatorio'].widget = CustomFileWidget(
                attrs={'class': 'form-control', 'accept': '.pdf'},
                precatorio_cnj=obj.cnj
            )
        
        return form
    
    # Custom methods for display
    def origem_short(self, obj):
        return obj.origem[:50] + '...' if len(obj.origem) > 50 else obj.origem
    origem_short.short_description = 'Origem'
    
    def valor_de_face_formatted(self, obj):
        return f'R$ {obj.valor_de_face:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    valor_de_face_formatted.short_description = 'Valor de Face'
    
    def tipo_colored(self, obj):
        if obj.tipo:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.tipo.cor, obj.tipo.nome
            )
        return '-'
    tipo_colored.short_description = 'Tipo'
    
    def clientes_count(self, obj):
        count = obj.clientes.count()
        return format_html('<span style="color: blue;">{}</span>', count)
    clientes_count.short_description = 'Clientes'
    
    def alvaras_count(self, obj):
        count = obj.alvara_set.count()
        return format_html('<span style="color: green;">{}</span>', count)
    alvaras_count.short_description = 'Alvarás'
    
    def requerimentos_count(self, obj):
        count = obj.requerimento_set.count()
        return format_html('<span style="color: orange;">{}</span>', count)
    requerimentos_count.short_description = 'Requerimentos'
    
    def credito_principal_display(self, obj):
        """Display status with updated labels"""
        return obj.get_credito_principal_display()
    credito_principal_display.short_description = 'Crédito Principal'
    
    def honorarios_contratuais_display(self, obj):
        """Display status with updated labels"""
        return obj.get_honorarios_contratuais_display()
    honorarios_contratuais_display.short_description = 'Hon. Contratuais'
    
    def honorarios_sucumbenciais_display(self, obj):
        """Display status with updated labels"""
        return obj.get_honorarios_sucumbenciais_display()
    honorarios_sucumbenciais_display.short_description = 'Hon. Sucumbenciais'
    
    def has_pdf(self, obj):
        """Display PDF status"""
        if obj.integra_precatorio:
            return format_html('<span style="color: green;" title="PDF disponível">📄</span>')
        return format_html('<span style="color: #ccc;" title="Sem PDF">📄</span>')
    has_pdf.short_description = 'PDF'


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Admin configuration for Cliente model"""
    
    list_display = ('cpf', 'nome', 'nascimento', 'idade', 'prioridade', 'falecido_status', 'has_observacao', 'precatorios_count', 'diligencias_count')
    list_filter = ('prioridade', 'falecido', 'nascimento')
    search_fields = ('cpf', 'nome')
    ordering = ('nome',)
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('cpf', 'nome', 'nascimento', 'prioridade', 'falecido')
        }),
        ('Observações', {
            'fields': ('observacao',),
            'classes': ('collapse',),
            'description': 'Observações gerais sobre o cliente'
        }),
    )
    
    inlines = [DiligenciasInline]
    
    # Custom widget configuration for textarea fields
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }
    
    def idade(self, obj):
        """Calculate and display client age from birth date."""
        if obj.nascimento is not None:
            from datetime import date
            today = date.today()
            age = today.year - obj.nascimento.year - ((today.month, today.day) < (obj.nascimento.month, obj.nascimento.day))
            return f'{age} anos'
        return '-'
    idade.short_description = 'Idade'
    
    def falecido_status(self, obj):
        """Display deceased status with visual indicators"""
        if obj.falecido is True:
            return format_html('<span style="color: red;" title="Cliente falecido">✝️ Sim</span>')
        elif obj.falecido is False:
            return format_html('<span style="color: green;" title="Cliente vivo">✓ Não</span>')
        else:
            return format_html('<span style="color: #ccc;" title="Status não informado">❓ N/I</span>')
    falecido_status.short_description = 'Falecido(a)'
    
    def has_observacao(self, obj):
        """Display if client has observations"""
        if obj.observacao and obj.observacao.strip():
            return format_html('<span style="color: blue;" title="Cliente tem observações">💬</span>')
        return format_html('<span style="color: #ccc;" title="Sem observações">💬</span>')
    has_observacao.short_description = 'Obs'
    
    def precatorios_count(self, obj):
        count = obj.precatorios.count()
        return format_html('<span style="color: blue;">{}</span>', count)
    precatorios_count.short_description = 'Precatórios'
    
    def diligencias_count(self, obj):
        count = obj.diligencias.count()
        pendentes = obj.diligencias.filter(concluida=False).count()
        if pendentes > 0:
            return format_html('<span style="color: red;">{} ({})</span>', count, f'{pendentes} pendentes')
        return format_html('<span style="color: green;">{}</span>', count)
    diligencias_count.short_description = 'Diligências'


@admin.register(Alvara)
class AlvaraAdmin(admin.ModelAdmin):
    """Admin configuration for Alvara model"""
    
    list_display = (
        'id', 'precatorio', 'cliente_nome', 'tipo', 'valor_principal_formatted', 
        'fase_colored', 'fase_honorarios_contratuais_colored', 'fase_honorarios_sucumbenciais_colored', 'total_valor'
    )
    list_filter = ('tipo', 'fase', 'fase_honorarios_contratuais', 'fase_honorarios_sucumbenciais')
    search_fields = ('precatorio__cnj', 'cliente__nome', 'cliente__cpf', 'tipo')
    
    fieldsets = (
        ('Relacionamentos', {
            'fields': ('precatorio', 'cliente')
        }),
        ('Valores', {
            'fields': ('valor_principal', 'honorarios_contratuais', 'honorarios_sucumbenciais')
        }),
        ('Classificação e Status', {
            'fields': ('tipo', 'fase', 'fase_honorarios_contratuais', 'fase_honorarios_sucumbenciais')
        }),
        ('Auditoria de Alterações', {
            'fields': (
                ('fase_ultima_alteracao', 'fase_alterada_por'),
                ('fase_honorarios_ultima_alteracao', 'fase_honorarios_alterada_por'),
                ('fase_honorarios_sucumbenciais_ultima_alteracao', 'fase_honorarios_sucumbenciais_alterada_por')
            ),
            'classes': ('collapse',),
            'description': 'Informações de rastreamento das últimas alterações nas fases'
        }),
    )
    
    autocomplete_fields = ['precatorio', 'cliente']
    readonly_fields = ('fase_ultima_alteracao', 'fase_alterada_por', 'fase_honorarios_ultima_alteracao', 'fase_honorarios_alterada_por', 'fase_honorarios_sucumbenciais_ultima_alteracao', 'fase_honorarios_sucumbenciais_alterada_por')
    inlines = [RecebimentosInline]
    
    def cliente_nome(self, obj):
        return obj.cliente.nome
    cliente_nome.short_description = 'Cliente'
    
    def valor_principal_formatted(self, obj):
        return f'R$ {obj.valor_principal:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    valor_principal_formatted.short_description = 'Valor Principal'
    
    def fase_colored(self, obj):
        if obj.fase:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.fase.cor, obj.fase.nome
            )
        return '-'
    fase_colored.short_description = 'Fase'
    
    def fase_honorarios_contratuais_colored(self, obj):
        if obj.fase_honorarios_contratuais:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.fase_honorarios_contratuais.cor, obj.fase_honorarios_contratuais.nome
            )
        return '-'
    fase_honorarios_contratuais_colored.short_description = 'Fase Hon. Contratuais'
    
    def fase_honorarios_sucumbenciais_colored(self, obj):
        if obj.fase_honorarios_sucumbenciais:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.fase_honorarios_sucumbenciais.cor, obj.fase_honorarios_sucumbenciais.nome
            )
        return '-'
    fase_honorarios_sucumbenciais_colored.short_description = 'Fase Hon. Sucumbenciais'
    
    def total_valor(self, obj):
        total = obj.valor_principal + (obj.honorarios_contratuais or 0) + (obj.honorarios_sucumbenciais or 0)
        return f'R$ {total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    total_valor.short_description = 'Valor Total'
    
    def fase_ultima_alteracao_display(self, obj):
        """Display formatted fase last modification info"""
        if obj.fase_ultima_alteracao:
            from django.utils.timezone import localtime
            local_time = localtime(obj.fase_ultima_alteracao)
            return format_html(
                '<span style="color: #666;">{}<br><small>por: {}</small></span>',
                local_time.strftime('%d/%m/%Y %H:%M'),
                obj.fase_alterada_por or 'Sistema'
            )
        return '-'
    fase_ultima_alteracao_display.short_description = 'Última Alt. Fase'
    
    def fase_honorarios_ultima_alteracao_display(self, obj):
        """Display formatted fase honorarios last modification info"""
        if obj.fase_honorarios_ultima_alteracao:
            from django.utils.timezone import localtime
            local_time = localtime(obj.fase_honorarios_ultima_alteracao)
            return format_html(
                '<span style="color: #666;">{}<br><small>por: {}</small></span>',
                local_time.strftime('%d/%m/%Y %H:%M'),
                obj.fase_honorarios_alterada_por or 'Sistema'
            )
        return '-'
    fase_honorarios_ultima_alteracao_display.short_description = 'Última Alt. Hon. Contratuais'
    
    def fase_honorarios_sucumbenciais_ultima_alteracao_display(self, obj):
        """Display formatted fase honorarios sucumbenciais last modification info"""
        if obj.fase_honorarios_sucumbenciais_ultima_alteracao:
            from django.utils.timezone import localtime
            local_time = localtime(obj.fase_honorarios_sucumbenciais_ultima_alteracao)
            return format_html(
                '<span style="color: #666;">{}<br><small>por: {}</small></span>',
                local_time.strftime('%d/%m/%Y %H:%M'),
                obj.fase_honorarios_sucumbenciais_alterada_por or 'Sistema'
            )
        return '-'
    fase_honorarios_sucumbenciais_ultima_alteracao_display.short_description = 'Última Alt. Hon. Sucumbenciais'


@admin.register(Requerimento)
class RequerimentoAdmin(admin.ModelAdmin):
    """Admin configuration for Requerimento model"""
    
    list_display = (
        'id', 'precatorio', 'cliente_nome', 'pedido_colored', 
        'valor_formatted', 'desagio_formatted', 'fase_colored'
    )
    list_filter = ('pedido', 'fase')
    search_fields = ('precatorio__cnj', 'cliente__nome', 'cliente__cpf', 'pedido')
    
    fieldsets = (
        ('Relacionamentos', {
            'fields': ('precatorio', 'cliente')
        }),
        ('Detalhes do Requerimento', {
            'fields': ('pedido', 'valor', 'desagio', 'fase')
        }),
        ('Auditoria de Alterações', {
            'fields': (
                ('fase_ultima_alteracao', 'fase_alterada_por'),
            ),
            'classes': ('collapse',),
            'description': 'Informações de rastreamento das últimas alterações na fase'
        }),
    )
    
    autocomplete_fields = ['precatorio', 'cliente']
    readonly_fields = ('fase_ultima_alteracao', 'fase_alterada_por')
    
    def cliente_nome(self, obj):
        return obj.cliente.nome
    cliente_nome.short_description = 'Cliente'
    
    def pedido_colored(self, obj):
        if obj.pedido:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.pedido.cor, obj.pedido.nome
            )
        return '-'
    pedido_colored.short_description = 'Pedido'
    
    def valor_formatted(self, obj):
        return f'R$ {obj.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    valor_formatted.short_description = 'Valor'
    
    def desagio_formatted(self, obj):
        return f'{obj.desagio}%'
    desagio_formatted.short_description = 'Deságio'
    
    def fase_colored(self, obj):
        if obj.fase:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.fase.cor, obj.fase.nome
            )
        return '-'
    fase_colored.short_description = 'Fase'
    
    def fase_ultima_alteracao_display(self, obj):
        """Display formatted fase last modification info"""
        if obj.fase_ultima_alteracao:
            from django.utils.timezone import localtime
            local_time = localtime(obj.fase_ultima_alteracao)
            return format_html(
                '<span style="color: #666;">{}<br><small>por: {}</small></span>',
                local_time.strftime('%d/%m/%Y %H:%M'),
                obj.fase_alterada_por or 'Sistema'
            )
        return '-'
    fase_ultima_alteracao_display.short_description = 'Última Alt. Fase'


@admin.register(Fase)
class FaseAdmin(admin.ModelAdmin):
    """Admin configuration for Fase model"""
    
    list_display = ('nome', 'tipo_colored', 'cor_preview', 'ordem', 'ativa', 'usage_count', 'criado_em')
    list_filter = ('tipo', 'ativa')
    search_fields = ('nome', 'descricao')
    ordering = ('tipo', 'ordem', 'nome')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'tipo')
        }),
        ('Aparência e Ordenação', {
            'fields': ('cor', 'ordem')
        }),
        ('Status', {
            'fields': ('ativa',)
        }),
    )
    
    def tipo_colored(self, obj):
        colors = {'alvara': '#28a745', 'requerimento': '#007bff', 'ambos': '#6f42c1'}
        color = colors.get(obj.tipo, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, dict(obj.TIPO_CHOICES).get(obj.tipo, obj.tipo)
        )
    tipo_colored.short_description = 'Tipo'
    
    def cor_preview(self, obj):
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor
        )
    cor_preview.short_description = 'Cor'
    
    def usage_count(self, obj):
        alvara_count = obj.alvara_set.count()
        req_count = obj.requerimento_set.count()
        total = alvara_count + req_count
        return format_html('A:{} R:{} <strong>T:{}</strong>', alvara_count, req_count, total)
    usage_count.short_description = 'Uso (A:Alvarás, R:Reqs)'


@admin.register(Tipo)
class TipoAdmin(admin.ModelAdmin):
    """Admin configuration for Tipo model"""
    
    list_display = ('nome', 'cor_preview', 'ordem', 'ativa', 'usage_count', 'criado_em')
    list_filter = ('ativa',)
    search_fields = ('nome', 'descricao')
    ordering = ('ordem', 'nome')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao')
        }),
        ('Aparência e Ordenação', {
            'fields': ('cor', 'ordem')
        }),
        ('Status', {
            'fields': ('ativa',)
        }),
    )
    
    def cor_preview(self, obj):
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor
        )
    cor_preview.short_description = 'Cor'
    
    def usage_count(self, obj):
        count = obj.precatorio_set.count()
        return format_html('<span style="color: blue;">{}</span>', count)
    usage_count.short_description = 'Precatórios'


@admin.register(PedidoRequerimento)
class PedidoRequerimentoAdmin(admin.ModelAdmin):
    """Admin configuration for PedidoRequerimento model"""
    
    list_display = ('nome', 'cor_preview', 'ordem', 'ativo', 'usage_count', 'criado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    ordering = ('ordem', 'nome')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao')
        }),
        ('Aparência e Ordenação', {
            'fields': ('cor', 'ordem')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )
    
    def cor_preview(self, obj):
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor
        )
    cor_preview.short_description = 'Cor'
    
    def usage_count(self, obj):
        count = obj.requerimento_set.count()
        return format_html('<span style="color: blue;">{}</span>', count)
    usage_count.short_description = 'Requerimentos'


@admin.register(FaseHonorariosContratuais)
class FaseHonorariosContratuaisAdmin(admin.ModelAdmin):
    """Admin configuration for FaseHonorariosContratuais model"""
    
    list_display = ('nome', 'cor_preview', 'ordem', 'ativa', 'usage_count', 'criado_em')
    list_filter = ('ativa',)
    search_fields = ('nome', 'descricao')
    ordering = ('ordem', 'nome')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao')
        }),
        ('Aparência e Ordenação', {
            'fields': ('cor', 'ordem')
        }),
        ('Status', {
            'fields': ('ativa',)
        }),
    )
    
    def cor_preview(self, obj):
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor
        )
    cor_preview.short_description = 'Cor'
    
    def usage_count(self, obj):
        count = obj.alvara_set.count()
        return format_html('<span style="color: blue;">{}</span>', count)
    usage_count.short_description = 'Alvarás'


@admin.register(FaseHonorariosSucumbenciais)
class FaseHonorariosSucumbenciaisAdmin(admin.ModelAdmin):
    """Admin configuration for FaseHonorariosSucumbenciais model"""
    
    list_display = ('nome', 'cor_preview', 'ordem', 'ativa', 'usage_count', 'criado_em')
    list_filter = ('ativa',)
    search_fields = ('nome', 'descricao')
    ordering = ('ordem', 'nome')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao')
        }),
        ('Aparência e Ordenação', {
            'fields': ('cor', 'ordem')
        }),
        ('Status', {
            'fields': ('ativa',)
        }),
    )
    
    def cor_preview(self, obj):
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor
        )
    cor_preview.short_description = 'Cor'
    
    def usage_count(self, obj):
        count = obj.alvara_set.count()
        return format_html('<span style="color: blue;">{}</span>', count)
    usage_count.short_description = 'Alvarás'


@admin.register(TipoDiligencia)
class TipoDiligenciaAdmin(admin.ModelAdmin):
    """Admin configuration for TipoDiligencia model"""
    
    list_display = ('nome', 'cor_preview', 'ordem', 'ativo', 'usage_count', 'criado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    ordering = ('ordem', 'nome')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao')
        }),
        ('Aparência e Ordenação', {
            'fields': ('cor', 'ordem')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )
    
    def cor_preview(self, obj):
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor
        )
    cor_preview.short_description = 'Cor'
    
    def usage_count(self, obj):
        count = obj.diligencias_set.count()
        return format_html('<span style="color: blue;">{}</span>', count)
    usage_count.short_description = 'Diligências'


@admin.register(Diligencias)
class DiligenciasAdmin(admin.ModelAdmin):
    """Admin configuration for Diligencias model"""
    
    list_display = (
        'id', 'cliente_nome', 'tipo_colored', 'data_final', 'urgencia_colored', 
        'responsavel_display', 'status_colored', 'days_remaining', 'criado_por', 'data_criacao'
    )
    list_filter = ('urgencia', 'concluida', 'tipo', 'data_final', 'responsavel')
    search_fields = ('cliente__nome', 'cliente__cpf', 'tipo__nome', 'criado_por', 'responsavel__username', 'responsavel__first_name', 'responsavel__last_name', 'descricao')
    date_hierarchy = 'data_criacao'
    
    fieldsets = (
        ('Relacionamentos', {
            'fields': ('cliente', 'tipo')
        }),
        ('Detalhes da Diligência', {
            'fields': ('data_final', 'urgencia', 'responsavel', 'descricao')
        }),
        ('Status e Controle', {
            'fields': ('concluida', 'criado_por'),
            'classes': ('collapse',)
        }),
        ('Conclusão', {
            'fields': ('data_conclusao', 'concluido_por'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('data_criacao',)
    autocomplete_fields = ['cliente']
    
    def cliente_nome(self, obj):
        return obj.cliente.nome
    cliente_nome.short_description = 'Cliente'
    
    def tipo_colored(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.tipo.cor, obj.tipo.nome
        )
    tipo_colored.short_description = 'Tipo'
    
    def urgencia_colored(self, obj):
        colors = {'baixa': '#28a745', 'media': '#ffc107', 'alta': '#dc3545'}
        color = colors.get(obj.urgencia, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.get_urgencia_display()
        )
    urgencia_colored.short_description = 'Urgência'
    
    def responsavel_display(self, obj):
        if obj.responsavel:
            # Show full name if available, otherwise username
            display_name = obj.responsavel.get_full_name() or obj.responsavel.username
            return format_html('<span style="color: #007bff;"><i class="fas fa-user"></i> {}</span>', display_name)
        return format_html('<span style="color: #6c757d;">-</span>')
    responsavel_display.short_description = 'Responsável'
    
    def status_colored(self, obj):
        if obj.concluida:
            return format_html('<span style="color: green;">✓ Concluída</span>')
        elif obj.is_overdue():
            return format_html('<span style="color: red;">⚠ Atrasada</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pendente</span>')
    status_colored.short_description = 'Status'
    
    def days_remaining(self, obj):
        if obj.concluida:
            return '-'
        days = obj.days_until_deadline()
        if days < 0:
            return format_html('<span style="color: red;">{} dias atrasada</span>', abs(days))
        elif days == 0:
            return format_html('<span style="color: orange;">Vence hoje!</span>')
        else:
            return format_html('<span style="color: blue;">{} dias restantes</span>', days)
    days_remaining.short_description = 'Prazo'


@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    """Admin configuration for ContaBancaria model"""
    
    list_display = ('banco', 'tipo_de_conta', 'agencia', 'conta', 'usage_count', 'criado_em')
    list_filter = ('tipo_de_conta', 'banco')
    search_fields = ('banco', 'agencia', 'conta')
    ordering = ('banco', 'agencia', 'conta')
    
    fieldsets = (
        ('Informações Bancárias', {
            'fields': ('banco', 'tipo_de_conta', 'agencia', 'conta')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('criado_em', 'atualizado_em')
    
    def usage_count(self, obj):
        count = obj.recebimentos_set.count()
        if count > 0:
            return format_html('<span style="color: green;">{} recebimentos</span>', count)
        return format_html('<span style="color: #6c757d;">Não utilizada</span>')
    usage_count.short_description = 'Uso'


@admin.register(Recebimentos)
class RecebimentosAdmin(admin.ModelAdmin):
    """Admin configuration for Recebimentos model"""
    
    list_display = (
        'numero_documento', 'alvara_info', 'data', 'conta_bancaria_info', 
        'valor_formatado', 'tipo', 'criado_por', 'criado_em'
    )
    list_filter = ('data', 'tipo', 'conta_bancaria__banco', 'conta_bancaria__tipo_de_conta')
    search_fields = (
        'numero_documento', 'alvara__cliente__nome', 'alvara__precatorio__cnj',
        'conta_bancaria__banco', 'conta_bancaria__agencia', 'conta_bancaria__conta'
    )
    date_hierarchy = 'data'
    ordering = ('-data', '-numero_documento')
    
    fieldsets = (
        ('Informações do Recebimento', {
            'fields': ('numero_documento', 'data', 'valor', 'tipo')
        }),
        ('Relacionamentos', {
            'fields': ('alvara', 'conta_bancaria')
        }),
        ('Auditoria', {
            'fields': ('criado_por', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('criado_por', 'criado_em', 'atualizado_em')
    autocomplete_fields = ['alvara']
    
    def alvara_info(self, obj):
        """Display alvara information with client and precatorio"""
        alvara = obj.alvara
        return format_html(
            '<strong>Alvará #{}</strong><br>'
            '<span style="color: #007bff;">{}</span><br>'
            '<span style="color: #6c757d; font-size: 0.9em;">{}</span>',
            alvara.id,
            alvara.cliente.nome,
            alvara.precatorio.cnj
        )
    alvara_info.short_description = 'Alvará'
    
    def conta_bancaria_info(self, obj):
        """Display bank account information"""
        conta = obj.conta_bancaria
        return format_html(
            '<strong>{}</strong><br>'
            '<span style="color: #6c757d; font-size: 0.9em;">Ag: {} - CC: {}</span><br>'
            '<span style="color: #28a745; font-size: 0.9em;">{}</span>',
            conta.banco,
            conta.agencia,
            conta.conta,
            conta.get_tipo_de_conta_display()
        )
    conta_bancaria_info.short_description = 'Conta Bancária'
    
    def valor_formatado(self, obj):
        """Display formatted currency value"""
        return format_html(
            '<strong style="color: #28a745;">R$ {:,.2f}</strong>',
            obj.valor
        ).replace(',', 'X').replace('.', ',').replace('X', '.')
    valor_formatado.short_description = 'Valor'


# Customize admin site header and title
admin.site.site_header = "Controle de Precatórios - Admin"
admin.site.site_title = "Precatórios Admin"
admin.site.index_title = "Painel Administrativo - Controle de Precatórios"
