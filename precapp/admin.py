from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import (
    Precatorio, Cliente, Alvara, Requerimento, Fase, Tipo,
    FaseHonorariosContratuais, TipoDiligencia, Diligencias, PedidoRequerimento
)

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
    fields = ('cliente', 'valor_principal', 'tipo', 'fase', 'fase_honorarios_contratuais', 'fase_alterada_por')
    readonly_fields = ('fase_alterada_por', 'fase_honorarios_alterada_por')


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


@admin.register(Precatorio)
class PrecatorioAdmin(admin.ModelAdmin):
    """Admin configuration for Precatorio model"""
    
    list_display = (
        'cnj', 'orcamento', 'origem_short', 'credito_principal_display', 
        'honorarios_contratuais_display', 'honorarios_sucumbenciais_display', 
        'valor_de_face_formatted', 'tipo_colored', 'clientes_count', 'alvaras_count', 'requerimentos_count'
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
        ('Relacionamentos', {
            'fields': ('clientes',),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('clientes',)
    inlines = [AlvaraInline, RequerimentoInline]
    
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


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Admin configuration for Cliente model"""
    
    list_display = ('cpf', 'nome', 'nascimento', 'idade', 'prioridade', 'precatorios_count', 'diligencias_count')
    list_filter = ('prioridade', 'nascimento')
    search_fields = ('cpf', 'nome')
    ordering = ('nome',)
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('cpf', 'nome', 'nascimento', 'prioridade')
        }),
    )
    
    inlines = [DiligenciasInline]
    
    def idade(self, obj):
        if obj.nascimento:
            from datetime import date
            today = date.today()
            age = today.year - obj.nascimento.year - ((today.month, today.day) < (obj.nascimento.month, obj.nascimento.day))
            return f'{age} anos'
        return '-'
    idade.short_description = 'Idade'
    
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
        'fase_colored', 'fase_honorarios_colored', 'total_valor'
    )
    list_filter = ('tipo', 'fase', 'fase_honorarios_contratuais')
    search_fields = ('precatorio__cnj', 'cliente__nome', 'cliente__cpf', 'tipo')
    
    fieldsets = (
        ('Relacionamentos', {
            'fields': ('precatorio', 'cliente')
        }),
        ('Valores', {
            'fields': ('valor_principal', 'honorarios_contratuais', 'honorarios_sucumbenciais')
        }),
        ('Classificação e Status', {
            'fields': ('tipo', 'fase', 'fase_honorarios_contratuais')
        }),
        ('Auditoria de Alterações', {
            'fields': (
                ('fase_ultima_alteracao', 'fase_alterada_por'),
                ('fase_honorarios_ultima_alteracao', 'fase_honorarios_alterada_por')
            ),
            'classes': ('collapse',),
            'description': 'Informações de rastreamento das últimas alterações nas fases'
        }),
    )
    
    autocomplete_fields = ['precatorio', 'cliente']
    readonly_fields = ('fase_ultima_alteracao', 'fase_alterada_por', 'fase_honorarios_ultima_alteracao', 'fase_honorarios_alterada_por')
    
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
    
    def fase_honorarios_colored(self, obj):
        if obj.fase_honorarios_contratuais:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.fase_honorarios_contratuais.cor, obj.fase_honorarios_contratuais.nome
            )
        return '-'
    fase_honorarios_colored.short_description = 'Fase Honorários'
    
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
    fase_honorarios_ultima_alteracao_display.short_description = 'Última Alt. Honorários'


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


# Customize admin site header and title
admin.site.site_header = "Controle de Precatórios - Admin"
admin.site.site_title = "Precatórios Admin"
admin.site.index_title = "Painel Administrativo - Controle de Precatórios"
