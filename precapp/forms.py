from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Precatorio, Cliente, Alvara, Requerimento, Fase


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
        help_text='Valor em reais (R$). Ex: 50000.00',
        validators=[validate_currency],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '50000.00',
            'title': 'Digite o valor em reais (use . para separar decimais)'
        })
    )
    
    ultima_atualizacao = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Última Atualização Monetária',
        help_text='Valor atualizado em reais (R$). Ex: 75000.00',
        validators=[validate_currency],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '75000.00',
            'title': 'Digite o valor atualizado em reais (use . para separar decimais)'
        })
    )
    
    percentual_contratuais_assinado = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label='% Honorários Contratuais (Assinado)',
        help_text='Percentual entre 0% e 30%. Ex: 20.00',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '30',
            'placeholder': '20.00',
            'title': 'Digite o percentual (0 a 30%)'
        })
    )
    
    percentual_contratuais_apartado = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label='% Honorários Contratuais (Apartado)',
        help_text='Percentual entre 0% e 30%. Ex: 15.00',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '30',
            'placeholder': '15.00',
            'title': 'Digite o percentual (0 a 30%)'
        })
    )
    
    percentual_sucumbenciais = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label='% Honorários Sucumbenciais',
        help_text='Percentual entre 0% e 30%. Ex: 10.00',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '30',
            'placeholder': '10.00',
            'title': 'Digite o percentual (0 a 30%)'
        })
    )
    
    class Meta:
        model = Precatorio
        fields = [
            "cnj",
            "data_oficio",
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
            'data_oficio': BrazilianDateInput(),
            'orcamento': forms.NumberInput(attrs={
                'type': 'number', 
                'class': 'form-control',
                'min': '1988',
                'max': '2050',
                'placeholder': '2023',
                'title': 'Digite apenas o ano (formato: YYYY)'
            }),
            'ultima_atualizacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Digite as informações sobre a última atualização...'}),
            'data_ultima_atualizacao': BrazilianDateInput(),
            'quitado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prioridade_deferida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'acordo_deferido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        labels = {
            'data_oficio': 'Data do Ofício',
            'orcamento': 'Ano do Orçamento',
            'quitado': 'Quitado',
            'data_ultima_atualizacao': 'Data da Última Atualização',
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
        help_text='Formato: 000.000.000-00 (obrigatório)',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
            'title': 'CPF no formato: 000.000.000-00'
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
        help_text='Formato: 000.000.000-00 (obrigatório)',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
            'title': 'CPF no formato: 000.000.000-00'
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


class AlvaraForm(forms.ModelForm):
    precatorio_cnj = forms.CharField(
        max_length=25,
        label='CNJ do Precatório',
        help_text='Digite o CNJ do precatório. Formato: NNNNNNN-DD.AAAA.J.TR.OOOO',
        validators=[validate_cnj],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234567-89.2023.8.26.0100',
            'pattern': r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}',
            'title': 'CNJ no formato: NNNNNNN-DD.AAAA.J.TR.OOOO'
        })
    )
    
    cliente_cpf = forms.CharField(
        max_length=14,
        label='CPF do Cliente',
        help_text='Digite o CPF do cliente. Formato: 000.000.000-00',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
            'title': 'CPF no formato: 000.000.000-00'
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
        queryset=Fase.objects.filter(ativa=True),
        empty_label='Selecione a fase',
        label='Fase',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    valor_principal = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Valor Principal',
        help_text='Valor em reais (R$). Ex: 50000.00',
        validators=[validate_currency],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '50000.00',
            'title': 'Digite o valor em reais (use . para separar decimais)'
        })
    )
    
    honorarios_contratuais = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        label='Honorários Contratuais',
        help_text='Valor em reais (R$). Ex: 10000.00',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '10000.00',
            'title': 'Digite o valor em reais (use . para separar decimais)'
        })
    )
    
    honorarios_sucumbenciais = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        label='Honorários Sucumbenciais',
        help_text='Valor em reais (R$). Ex: 5000.00',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '5000.00',
            'title': 'Digite o valor em reais (use . para separar decimais)'
        })
    )
    
    def clean_precatorio_cnj(self):
        """Validate that the CNJ corresponds to an existing precatorio"""
        cnj = self.cleaned_data.get('precatorio_cnj')
        if cnj:
            try:
                from .models import Precatorio
                precatorio = Precatorio.objects.get(cnj=cnj)
                return cnj
            except Precatorio.DoesNotExist:
                raise forms.ValidationError(f'Não foi encontrado um precatório com o CNJ "{cnj}". Verifique se o número está correto.')
        return cnj
    
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

    class Meta:
        model = Alvara
        fields = ["tipo", "fase", "valor_principal", "honorarios_contratuais", "honorarios_sucumbenciais"]
        labels = {
            'precatorio': 'Precatório',
            'cliente': 'Cliente',
            'tipo': 'Tipo',
            'fase': 'Fase',
            'valor_principal': 'Valor Principal',
            'honorarios_contratuais': 'Honorários Contratuais',
            'honorarios_sucumbenciais': 'Honorários Sucumbenciais',
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
        help_text='Digite o CPF do cliente para vincular ao precatório. Formato: 000.000.000-00',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
            'title': 'CPF no formato: 000.000.000-00'
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
        help_text='Digite o CPF do cliente. Formato: 000.000.000-00',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
            'title': 'CPF no formato: 000.000.000-00'
        })
    )
    
    valor = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Valor',
        help_text='Valor em reais (R$). Ex: 50000.00',
        validators=[validate_currency],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '50000.00',
            'title': 'Digite o valor em reais (use . para separar decimais)'
        })
    )
    
    desagio = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label='Deságio (%)',
        help_text='Percentual de deságio. Ex: 15.50',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '100',
            'placeholder': '15.50',
            'title': 'Digite o percentual de deságio (0 a 100%)'
        })
    )
    
    fase = forms.ModelChoiceField(
        queryset=Fase.objects.filter(ativa=True),
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
            'fase': 'Fase',
        }


class AlvaraSimpleForm(forms.ModelForm):
    """Simplified AlvaraForm for use within precatorio details (no precatorio_cnj field)"""
    
    cliente_cpf = forms.CharField(
        max_length=14,
        label='CPF do Cliente',
        help_text='Digite o CPF do cliente. Formato: 000.000.000-00',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
            'title': 'CPF no formato: 000.000.000-00'
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
        queryset=Fase.objects.filter(ativa=True),
        empty_label='Selecione a fase',
        label='Fase',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    valor_principal = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Valor Principal',
        help_text='Valor em reais (R$). Ex: 50000.00',
        validators=[validate_currency],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '50000.00',
            'title': 'Digite o valor em reais (use . para separar decimais)'
        })
    )
    
    honorarios_contratuais = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        label='Honorários Contratuais',
        help_text='Valor em reais (R$). Ex: 10000.00',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '10000.00',
            'title': 'Digite o valor em reais (use . para separar decimais)'
        })
    )
    
    honorarios_sucumbenciais = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        label='Honorários Sucumbenciais',
        help_text='Valor em reais (R$). Ex: 5000.00',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '5000.00',
            'title': 'Digite o valor em reais (use . para separar decimais)'
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

    class Meta:
        model = Alvara
        fields = ["tipo", "fase", "valor_principal", "honorarios_contratuais", "honorarios_sucumbenciais"]
        labels = {
            'tipo': 'Tipo',
            'fase': 'Fase',
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
        """Validate nome field to ensure uniqueness"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            # Check if another fase with the same name exists (excluding current instance if editing)
            existing_fase = Fase.objects.filter(nome__iexact=nome)
            if self.instance.pk:
                existing_fase = existing_fase.exclude(pk=self.instance.pk)
            
            if existing_fase.exists():
                raise forms.ValidationError('Já existe uma fase com este nome.')
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
        fields = ['nome', 'descricao', 'cor', 'ativa']

        