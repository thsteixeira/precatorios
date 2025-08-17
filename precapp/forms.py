from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Precatorio, Cliente, Alvara, Requerimento, Fase, FaseHonorariosContratuais


class BrazilianDateInput(forms.DateInput):
    """
    Custom DateInput widget for Brazilian date format (dd/mm/yyyy)
    """
    input_type = 'text'
    
    def __init__(self, attrs=None, format=None):
        default_attrs = {
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa',
            'pattern': r'\d{2}/\d{2}/\d{4}',
            'title': 'Digite a data no formato dd/mm/aaaa (ex: 31/12/2023)',
            'maxlength': '10',
        }
        if attrs:
            default_attrs.update(attrs)
        
        # Use Brazilian date format
        if format is None:
            format = '%d/%m/%Y'
            
        super().__init__(attrs=default_attrs, format=format)


def validate_cnj(value):
    """
    Validates CNJ number format: NNNNNNN-DD.AAAA.J.TR.OOOO
    """
    # Remove any spaces
    cnj = value.replace(' ', '')
    
    # CNJ pattern: 7digits-2digits.4digits.1digit.2digits.4digits
    cnj_pattern = r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$'
    
    if not re.match(cnj_pattern, cnj):
        raise ValidationError(
            'CNJ deve estar no formato: NNNNNNN-DD.AAAA.J.TR.OOOO (exemplo: 1234567-89.2023.8.26.0100)',
            code='invalid_cnj'
        )
    
    # Extract parts for additional validation
    # Split the CNJ correctly: NNNNNNN-DD.AAAA.J.TR.OOOO
    # First, split by the first dot to separate the sequential part from the rest
    first_dot_pos = cnj.find('.')
    sequential_part = cnj[:first_dot_pos]  # NNNNNNN-DD
    rest_parts = cnj[first_dot_pos+1:].split('.')  # [AAAA, J, TR, OOOO]
    
    if len(rest_parts) != 4:
        raise ValidationError('Formato CNJ inválido', code='invalid_cnj')
    
    # Validate year (should be reasonable)
    year = int(rest_parts[0])  # AAAA
    if year < 1988 or year > 2050:  # Constitution year to future
        raise ValidationError(
            'Ano do CNJ deve estar entre 1988 e 2050',
            code='invalid_year'
        )
    
    # Validate judicial segment (J field)
    segment = int(rest_parts[1])  # J
    valid_segments = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    if segment not in valid_segments:
        raise ValidationError(
            'Segmento do judiciário (J) deve ser um dígito de 1 a 9',
            code='invalid_segment'
        )
    
    return value

def validate_currency(value):
    """
    Validates currency values to ensure they are positive
    """
    if value is not None and value < 0:
        raise ValidationError(
            'O valor deve ser positivo.',
            code='negative_value'
        )
    return value


class PrecatorioForm(forms.ModelForm):
    cnj = forms.CharField(
        max_length=25,
        label='CNJ',
        help_text='Formato: NNNNNNN-DD.AAAA.J.TR.OOOO (ex: 1234567-89.2023.8.26.0100)',
        validators=[validate_cnj],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234567-89.2023.8.26.0100',
            'pattern': r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}',
            'title': 'CNJ no formato: NNNNNNN-DD.AAAA.J.TR.OOOO'
        })
    )
    
    origem = forms.CharField(
        max_length=25,
        label='CNJ de Origem',
        help_text='Formato: NNNNNNN-DD.AAAA.J.TR.OOOO (ex: 9876543-21.2022.8.26.0001)',
        validators=[validate_cnj],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '9876543-21.2022.8.26.0001',
            'pattern': r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}',
            'title': 'CNJ de origem no formato: NNNNNNN-DD.AAAA.J.TR.OOOO'
        })
    )
    
    valor_de_face = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Valor de Face',
        help_text='Valor em reais (R$). Ex: 50.000,00',
        validators=[validate_currency],
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-currency',
            'placeholder': '50.000,00',
            'title': 'Digite o valor em reais (formato brasileiro: 50.000,00)'
        })
    )
    
    ultima_atualizacao = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,  # Made optional
        label='Última Atualização Monetária',
        help_text='Valor atualizado em reais (R$). Ex: 75.000,00 (Opcional)',
        validators=[validate_currency],
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-currency',
            'placeholder': '75.000,00',
            'title': 'Digite o valor atualizado em reais (formato brasileiro: 75.000,00)'
        })
    )
    
    percentual_contratuais_assinado = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label='% Honorários Contratuais (Assinado)',
        help_text='Percentual entre 0% e 30%. Ex: 20,00',
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-number',
            'placeholder': '20,00',
            'title': 'Digite o percentual (0 a 30%) - formato brasileiro: 20,00'
        })
    )
    
    percentual_contratuais_apartado = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label='% Honorários Contratuais (Apartado)',
        help_text='Percentual entre 0% e 30%. Ex: 15,00',
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-number',
            'placeholder': '15,00',
            'title': 'Digite o percentual (0 a 30%) - formato brasileiro: 15,00'
        })
    )
    
    percentual_sucumbenciais = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label='% Honorários Sucumbenciais',
        help_text='Percentual entre 0% e 30%. Ex: 10,00',
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-number',
            'placeholder': '10,00',
            'title': 'Digite o percentual (0 a 30%) - formato brasileiro: 10,00'
        })
    )
    
    class Meta:
        model = Precatorio
        fields = [
            "cnj",
            "orcamento",
            "origem",
            "quitado",
            "valor_de_face",
            "ultima_atualizacao",
            "data_ultima_atualizacao",
            "percentual_contratuais_assinado",
            "percentual_contratuais_apartado",
            "percentual_sucumbenciais",
            "prioridade_deferida",
            "acordo_deferido",
        ]
        
        widgets = {
            'orcamento': forms.NumberInput(attrs={
                'type': 'number', 
                'class': 'form-control',
                'min': '1988',
                'max': '2050',
                'placeholder': '2023',
                'title': 'Digite apenas o ano (formato: YYYY)'
            }),
            'data_ultima_atualizacao': BrazilianDateInput(attrs={'required': False}),
            'quitado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prioridade_deferida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'acordo_deferido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        labels = {
            'orcamento': 'Ano do Orçamento',
            'quitado': 'Quitado',
            'data_ultima_atualizacao': 'Data da Última Atualização (Opcional)',
            'prioridade_deferida': 'Prioridade Deferida',
            'acordo_deferido': 'Acordo Deferido',
        }

    def clean_percentual_contratuais_assinado(self):
        percentual = self.cleaned_data.get('percentual_contratuais_assinado')
        if percentual is not None:
            if percentual < 0 or percentual > 30:
                raise forms.ValidationError('O percentual deve estar entre 0% e 30%.')
        return percentual
    
    def clean_percentual_contratuais_apartado(self):
        percentual = self.cleaned_data.get('percentual_contratuais_apartado')
        if percentual is not None:
            if percentual < 0 or percentual > 30:
                raise forms.ValidationError('O percentual deve estar entre 0% e 30%.')
        return percentual
    
    def clean_percentual_sucumbenciais(self):
        percentual = self.cleaned_data.get('percentual_sucumbenciais')
        if percentual is not None:
            if percentual < 0 or percentual > 30:
                raise forms.ValidationError('O percentual deve estar entre 0% e 30%.')
        return percentual


class ClienteForm(forms.ModelForm):
    cpf = forms.CharField(
        max_length=14,
        label='CPF',
        help_text='Formato: 000.000.000-00 ou 00000000000 (obrigatório)',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00 ou 00000000000',
            'pattern': r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})',
            'title': 'CPF no formato: 000.000.000-00 ou 00000000000'
        })
    )
    
    precatorio_cnj = forms.CharField(
        max_length=25,
        label='CNJ do Precatório',
        help_text='Digite o CNJ do precatório para vincular ao cliente (opcional). Formato: NNNNNNN-DD.AAAA.J.TR.OOOO',
        required=False,
        validators=[validate_cnj],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234567-89.2023.8.26.0100',
            'pattern': r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}',
            'title': 'CNJ no formato: NNNNNNN-DD.AAAA.J.TR.OOOO'
        })
    )
    
    def clean_cpf(self):
        """
        Clean CPF field by removing formatting (dots and dashes) and validate it's not empty
        """
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove dots and dashes, keep only numbers
            cpf_numbers = ''.join(filter(str.isdigit, cpf))
            if len(cpf_numbers) != 11:
                raise forms.ValidationError('CPF deve ter exatamente 11 dígitos.')
            if cpf_numbers == '00000000000':
                raise forms.ValidationError('CPF inválido.')
            return cpf_numbers
        else:
            raise forms.ValidationError('CPF é obrigatório.')
    
    def clean_precatorio_cnj(self):
        """
        Validate that the CNJ corresponds to an existing precatorio
        """
        cnj = self.cleaned_data.get('precatorio_cnj')
        if cnj:
            try:
                from .models import Precatorio
                precatorio = Precatorio.objects.get(cnj=cnj)
                return cnj
            except Precatorio.DoesNotExist:
                raise forms.ValidationError(f'Não foi encontrado um precatório com o CNJ "{cnj}". Verifique se o número está correto.')
        return cnj

    class Meta:
        model = Cliente
        fields = ["cpf", "nome", "nascimento", "prioridade"]
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome completo do cliente'
            }),
            'nascimento': BrazilianDateInput(),
            'prioridade': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'nome': 'Nome Completo',
            'nascimento': 'Data de Nascimento',
            'prioridade': 'Cliente com Prioridade Legal',
        }


class ClienteSimpleForm(forms.ModelForm):
    """Simplified ClienteForm for use within precatorio details (no precatorio_cnj field)"""
    cpf = forms.CharField(
        max_length=14,
        label='CPF',
        help_text='Formato: 000.000.000-00 ou 00000000000 (obrigatório)',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00 ou 00000000000',
            'pattern': r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})',
            'title': 'CPF no formato: 000.000.000-00 ou 00000000000'
        })
    )
    
    def clean_cpf(self):
        """
        Clean CPF field by removing formatting (dots and dashes) and validate it's not empty
        """
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove dots and dashes, keep only numbers
            cpf_numbers = ''.join(filter(str.isdigit, cpf))
            if len(cpf_numbers) != 11:
                raise forms.ValidationError('CPF deve ter exatamente 11 dígitos.')
            if cpf_numbers == '00000000000':
                raise forms.ValidationError('CPF inválido.')
            # Check if client already exists
            if Cliente.objects.filter(cpf=cpf_numbers).exists():
                raise forms.ValidationError('Já existe um cliente com este CPF.')
            return cpf_numbers
        else:
            raise forms.ValidationError('CPF é obrigatório.')

    class Meta:
        model = Cliente
        fields = ["cpf", "nome", "nascimento", "prioridade"]
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome completo do cliente'
            }),
            'nascimento': BrazilianDateInput(),
            'prioridade': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

        labels = {
            'nome': 'Nome Completo',
            'nascimento': 'Data de Nascimento',
            'prioridade': 'Cliente com Prioridade Legal',
        }


class PrecatorioSearchForm(forms.Form):
    """Form for searching precatorios by CNJ to link to a client"""
    cnj = forms.CharField(
        max_length=25,
        label='CNJ do Precatório',
        help_text='Digite o CNJ do precatório para vincular ao cliente. Formato: NNNNNNN-DD.AAAA.J.TR.OOOO',
        validators=[validate_cnj],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234567-89.2023.8.26.0100',
            'pattern': r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}',
            'title': 'CNJ no formato: NNNNNNN-DD.AAAA.J.TR.OOOO'
        })
    )


class ClienteSearchForm(forms.Form):
    """Form for searching clients by CPF to link to a precatorio"""
    cpf = forms.CharField(
        max_length=14,
        label='CPF do Cliente',
        help_text='Digite o CPF do cliente para vincular ao precatório. Formato: 000.000.000-00 ou 00000000000',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00 ou 00000000000',
            'pattern': r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})',
            'title': 'CPF no formato: 000.000.000-00 ou 00000000000'
        })
    )
    
    def clean_cpf(self):
        """
        Clean CPF field by removing formatting (dots and dashes) and validate it's not empty
        """
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove dots and dashes, keep only numbers
            cpf_numbers = ''.join(filter(str.isdigit, cpf))
            if len(cpf_numbers) != 11:
                raise forms.ValidationError('CPF deve ter exatamente 11 dígitos.')
            if cpf_numbers == '00000000000':
                raise forms.ValidationError('CPF inválido.')
            return cpf_numbers
        else:
            raise forms.ValidationError('CPF é obrigatório.')


class RequerimentoForm(forms.ModelForm):
    cliente_cpf = forms.CharField(
        max_length=14,
        label='CPF do Cliente',
        help_text='Digite o CPF do cliente. Formato: 000.000.000-00 ou 00000000000',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00 ou 00000000000',
            'pattern': r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})',
            'title': 'CPF no formato: 000.000.000-00 ou 00000000000'
        })
    )
    
    valor = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Valor',
        help_text='Valor em reais (R$). Ex: 50.000,00',
        validators=[validate_currency],
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-currency',
            'placeholder': '50.000,00',
            'title': 'Digite o valor em reais (formato brasileiro: 50.000,00)'
        })
    )
    
    desagio = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label='Deságio (%)',
        help_text='Percentual de deságio. Ex: 15,50',
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-number',
            'placeholder': '15,50',
            'title': 'Digite o percentual de deságio (0 a 100%) - formato brasileiro: 15,50'
        })
    )
    
    fase = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        empty_label='Selecione a fase',
        label='Fase',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def clean_cliente_cpf(self):
        """Validate that the CPF corresponds to an existing cliente"""
        cpf = self.cleaned_data.get('cliente_cpf')
        if cpf:
            # Remove dots and dashes, keep only numbers
            cpf_numbers = ''.join(filter(str.isdigit, cpf))
            if len(cpf_numbers) != 11:
                raise forms.ValidationError('CPF deve ter exatamente 11 dígitos.')
            try:
                from .models import Cliente
                cliente = Cliente.objects.get(cpf=cpf_numbers)
                return cpf
            except Cliente.DoesNotExist:
                raise forms.ValidationError(f'Não foi encontrado um cliente com o CPF "{cpf}". Verifique se o número está correto ou cadastre o cliente primeiro.')
        return cpf

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset to only show phases for Requerimento
        from .models import Fase
        self.fields['fase'].queryset = Fase.get_fases_for_requerimento()

    class Meta:
        model = Requerimento
        fields = ["valor", "desagio", "pedido", "fase"]
        
        widgets = {
            'pedido': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        
        labels = {
            'valor': 'Valor',
            'desagio': 'Deságio (%)',
            'pedido': 'Tipo de Pedido',
            'fase': 'Fase Principal',
        }


class AlvaraSimpleForm(forms.ModelForm):
    """Simplified AlvaraForm for use within precatorio details (no precatorio_cnj field)"""
    
    cliente_cpf = forms.CharField(
        max_length=14,
        label='CPF do Cliente',
        help_text='Digite o CPF do cliente. Formato: 000.000.000-00 ou 00000000000',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00 ou 00000000000',
            'pattern': r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})',
            'title': 'CPF no formato: 000.000.000-00 ou 00000000000'
        })
    )
    
    tipo = forms.ChoiceField(
        choices=[
            ('', 'Selecione o tipo'),
            ('ordem cronológica', 'Ordem cronológica'),
            ('prioridade', 'Prioridade'),
            ('acordo', 'Acordo'),
        ],
        label='Tipo',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    fase = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        empty_label='Selecione a fase',
        label='Fase',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    fase_honorarios_contratuais = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        empty_label='Selecione a fase (opcional)',
        label='Fase Honorários Contratuais',
        required=False,
        help_text='Fase específica para acompanhar o status dos honorários contratuais',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    valor_principal = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Valor Principal',
        help_text='Valor em reais (R$). Ex: 50.000,00',
        validators=[validate_currency],
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-currency',
            'placeholder': '50.000,00',
            'title': 'Digite o valor em reais (formato brasileiro: 50.000,00)'
        })
    )
    
    honorarios_contratuais = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        label='Honorários Contratuais',
        help_text='Valor em reais (R$). Ex: 10.000,00',
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-currency',
            'placeholder': '10.000,00',
            'title': 'Digite o valor em reais (formato brasileiro: 10.000,00)'
        })
    )
    
    honorarios_sucumbenciais = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        label='Honorários Sucumbenciais',
        help_text='Valor em reais (R$). Ex: 5.000,00',
        widget=forms.TextInput(attrs={
            'class': 'form-control brazilian-currency',
            'placeholder': '5.000,00',
            'title': 'Digite o valor em reais (formato brasileiro: 5.000,00)'
        })
    )
    
    def clean_cliente_cpf(self):
        """Validate that the CPF corresponds to an existing cliente"""
        cpf = self.cleaned_data.get('cliente_cpf')
        if cpf:
            # Remove dots and dashes, keep only numbers
            cpf_numbers = ''.join(filter(str.isdigit, cpf))
            if len(cpf_numbers) != 11:
                raise forms.ValidationError('CPF deve ter exatamente 11 dígitos.')
            try:
                from .models import Cliente
                cliente = Cliente.objects.get(cpf=cpf_numbers)
                return cpf
            except Cliente.DoesNotExist:
                raise forms.ValidationError(f'Não foi encontrado um cliente com o CPF "{cpf}". Verifique se o número está correto ou cadastre o cliente primeiro.')
        return cpf

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset to only show phases for Alvará
        from .models import Fase, FaseHonorariosContratuais
        self.fields['fase'].queryset = Fase.get_fases_for_alvara()
        self.fields['fase_honorarios_contratuais'].queryset = FaseHonorariosContratuais.get_fases_ativas()

    class Meta:
        model = Alvara
        fields = ["tipo", "fase", "fase_honorarios_contratuais", "valor_principal", "honorarios_contratuais", "honorarios_sucumbenciais"]
        labels = {
            'tipo': 'Tipo',
            'fase': 'Fase Principal',
            'fase_honorarios_contratuais': 'Fase Honorários Contratuais',
            'valor_principal': 'Valor Principal',
            'honorarios_contratuais': 'Honorários Contratuais',
            'honorarios_sucumbenciais': 'Honorários Sucumbenciais',
        }


class FaseForm(forms.ModelForm):
    """Form for creating and editing custom phases"""
    
    nome = forms.CharField(
        max_length=100,
        label='Nome da Fase',
        help_text='Nome único para identificar a fase',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Aguardando documentos',
            'required': True
        })
    )
    
    descricao = forms.CharField(
        required=False,
        label='Descrição',
        help_text='Descrição opcional da fase',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descreva esta fase (opcional)...'
        })
    )
    
    tipo = forms.ChoiceField(
        choices=[
            ('alvara', 'Alvará'),
            ('requerimento', 'Requerimento'),
            ('ambos', 'Ambos (Alvará e Requerimento)'),
        ],
        initial='ambos',
        label='Tipo de Fase',
        help_text='Define onde esta fase pode ser usada',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    cor = forms.CharField(
        max_length=7,
        label='Cor',
        help_text='Cor para identificar visualmente a fase',
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-control form-control-color',
            'value': '#6c757d',
            'title': 'Escolha uma cor para esta fase'
        })
    )
    
    ativa = forms.BooleanField(
        required=False,
        initial=True,
        label='Fase Ativa',
        help_text='Marque para disponibilizar esta fase para uso',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_nome(self):
        """Validate nome field to ensure uniqueness within the same tipo"""
        nome = self.cleaned_data.get('nome')
        tipo = self.cleaned_data.get('tipo')
        if nome and tipo:
            nome = nome.strip()
            # Check if another fase with the same name and tipo exists (excluding current instance if editing)
            existing_fase = Fase.objects.filter(nome__iexact=nome, tipo=tipo)
            if self.instance.pk:
                existing_fase = existing_fase.exclude(pk=self.instance.pk)
            
            if existing_fase.exists():
                raise forms.ValidationError(f'Já existe uma fase com o nome "{nome}" para o tipo "{dict(Fase.TIPO_CHOICES).get(tipo, tipo)}".')
        return nome
    
    def clean_cor(self):
        """Validate color field format"""
        cor = self.cleaned_data.get('cor')
        if cor:
            # Ensure it's a valid hex color
            if not re.match(r'^#[0-9a-fA-F]{6}$', cor):
                raise forms.ValidationError('Cor deve estar no formato hexadecimal (#RRGGBB)')
        return cor

    class Meta:
        model = Fase
        fields = ['nome', 'descricao', 'tipo', 'cor', 'ativa']


class FaseHonorariosContratuaisForm(forms.ModelForm):
    """Form for creating and editing Fase Honorários Contratuais"""
    
    nome = forms.CharField(
        max_length=100,
        label='Nome da Fase',
        help_text='Nome único para identificar a fase de honorários contratuais',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Aguardando pagamento',
            'required': True
        })
    )
    
    descricao = forms.CharField(
        required=False,
        label='Descrição',
        help_text='Descrição opcional da fase',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descreva esta fase (opcional)...'
        })
    )
    
    cor = forms.CharField(
        max_length=7,
        label='Cor',
        help_text='Cor para identificar visualmente a fase',
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-control form-control-color',
            'value': '#28a745',
            'title': 'Escolha uma cor para esta fase'
        })
    )
    
    ativa = forms.BooleanField(
        required=False,
        initial=True,
        label='Fase Ativa',
        help_text='Marque para disponibilizar esta fase para uso',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_nome(self):
        """Validate nome field to ensure uniqueness"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            # Check if another fase with the same name exists (excluding current instance if editing)
            from .models import FaseHonorariosContratuais
            existing_fase = FaseHonorariosContratuais.objects.filter(nome__iexact=nome)
            if self.instance.pk:
                existing_fase = existing_fase.exclude(pk=self.instance.pk)
            
            if existing_fase.exists():
                raise forms.ValidationError(f'Já existe uma fase de honorários contratuais com o nome "{nome}".')
        return nome
    
    def clean_cor(self):
        """Validate color field format"""
        cor = self.cleaned_data.get('cor')
        if cor:
            # Ensure it's a valid hex color
            if not re.match(r'^#[0-9a-fA-F]{6}$', cor):
                raise forms.ValidationError('Cor deve estar no formato hexadecimal (#RRGGBB)')
        return cor

    class Meta:
        model = FaseHonorariosContratuais
        fields = ['nome', 'descricao', 'cor', 'ativa']

        