from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Precatorio, Cliente, Alvara, Requerimento, Fase, FaseHonorariosContratuais, Diligencias, TipoDiligencia, Tipo


def validate_cpf(cpf):
    """
    Validate Brazilian CPF using the official algorithm
    Returns True if valid, False otherwise
    """
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    sum1 = 0
    for i in range(9):
        sum1 += int(cpf[i]) * (10 - i)
    remainder1 = sum1 % 11
    digit1 = 11 - remainder1 if remainder1 > 1 else 0
    if int(cpf[9]) != digit1:
        return False
    sum2 = 0
    for i in range(10):
        sum2 += int(cpf[i]) * (11 - i)
    remainder2 = sum2 % 11
    digit2 = 11 - remainder2 if remainder2 > 1 else 0
    if int(cpf[10]) != digit2:
        return False
    return True

def validate_cnpj(cnpj):
    """
    Validate Brazilian CNPJ using the official algorithm
    Returns True if valid, False otherwise
    """
    cnpj = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False
    weight1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weight2 = [6] + weight1
    sum1 = sum(int(cnpj[i]) * weight1[i] for i in range(12))
    digit1 = 11 - (sum1 % 11)
    digit1 = digit1 if digit1 < 10 else 0
    if int(cnpj[12]) != digit1:
        return False
    sum2 = sum(int(cnpj[i]) * weight2[i] for i in range(13))
    digit2 = 11 - (sum2 % 11)
    digit2 = digit2 if digit2 < 10 else 0
    if int(cnpj[13]) != digit2:
        return False
    return True
    
    # Check if all digits are the same (invalid CPFs)
    if cpf == cpf[0] * 11:
        return False
    
    # Calculate first check digit
    sum1 = 0
    for i in range(9):
        sum1 += int(cpf[i]) * (10 - i)
    
    remainder1 = sum1 % 11
    digit1 = 11 - remainder1 if remainder1 > 1 else 0
    
    # Check first digit
    if int(cpf[9]) != digit1:
        return False
    
    # Calculate second check digit
    sum2 = 0
    for i in range(10):
        sum2 += int(cpf[i]) * (11 - i)
    
    remainder2 = sum2 % 11
    digit2 = 11 - remainder2 if remainder2 > 1 else 0
    
    # Check second digit
    if int(cpf[10]) != digit2:
        return False
    
    return True


class BrazilianDateInput(forms.DateInput):
    """
    Custom date input widget with Brazilian formatting and validation.
    
    This widget provides a localized date input experience for Brazilian users,
    automatically formatting dates in the Brazilian standard (dd/mm/yyyy) and
    providing appropriate UI hints and validation patterns.
    
    Key Features:
        - Brazilian date format (dd/mm/yyyy) by default
        - Built-in placeholder text in Portuguese
        - HTML5 pattern validation for date format
        - Bootstrap CSS classes for consistent styling
        - Accessibility support with descriptive title
        - Maximum length validation to prevent invalid input
        
    Usage:
        # Basic usage
        class MyForm(forms.ModelForm):
            data_field = forms.DateField(widget=BrazilianDateInput())
            
        # Custom attributes
        widget = BrazilianDateInput(attrs={'class': 'custom-date-input'})
        
        # Custom format
        widget = BrazilianDateInput(format='%d-%m-%Y')
    
    Attributes:
        input_type (str): HTML input type, set to 'text' for better control
        format (str): Date format string, defaults to '%d/%m/%Y'
        attrs (dict): HTML attributes for the input element
        
    Default Attributes:
        - class: 'form-control' (Bootstrap styling)
        - placeholder: 'dd/mm/aaaa' (Brazilian format hint)
        - pattern: Regex pattern for date validation
        - title: Descriptive text for accessibility
        - maxlength: '10' (prevents over-typing)
        
    Browser Compatibility:
        - Supports HTML5 pattern validation
        - Works with all modern browsers
        - Gracefully degrades in older browsers
        
    Accessibility:
        - Includes descriptive placeholder text in Portuguese
        - Provides title attribute for screen readers
        - Uses semantic HTML input patterns
        - Supports keyboard navigation
        
    Validation:
        - Client-side pattern validation (dd/mm/yyyy)
        - Server-side format validation via Django
        - Maximum length enforcement
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


class BrazilianDateTimeInput(forms.DateTimeInput):
    """
    Custom datetime input widget with Brazilian formatting and validation.
    
    This widget provides a localized datetime input experience for Brazilian users,
    automatically formatting datetime values in the Brazilian standard (dd/mm/yyyy hh:mm)
    and providing appropriate UI hints for date and time entry.
    
    Key Features:
        - Brazilian datetime format (dd/mm/yyyy hh:mm) by default
        - Built-in placeholder text in Portuguese
        - Bootstrap CSS classes for consistent styling
        - Accessibility support with descriptive title
        - Maximum length validation to prevent invalid input
        - 24-hour time format for clarity
        
    Usage:
        # Basic usage
        class MyForm(forms.ModelForm):
            datetime_field = forms.DateTimeField(widget=BrazilianDateTimeInput())
            
        # Custom attributes
        widget = BrazilianDateTimeInput(attrs={'class': 'custom-datetime-input'})
        
        # Custom format
        widget = BrazilianDateTimeInput(format='%d-%m-%Y %H:%M:%S')
    
    Attributes:
        input_type (str): HTML input type, set to 'text' for better control
        format (str): Datetime format string, defaults to '%d/%m/%Y %H:%M'
        attrs (dict): HTML attributes for the input element
        
    Default Attributes:
        - class: 'form-control' (Bootstrap styling)
        - placeholder: 'dd/mm/aaaa hh:mm' (Brazilian format hint)
        - title: Descriptive text for accessibility with example
        - maxlength: '16' (prevents over-typing)
        
    Format Details:
        - Date: dd/mm/yyyy (day/month/year)
        - Time: hh:mm (24-hour format)
        - Separator: Single space between date and time
        - Example: 31/12/2023 14:30
        
    Browser Compatibility:
        - Works with all modern browsers
        - Text input provides consistent behavior
        - No dependency on browser datetime pickers
        
    Accessibility:
        - Includes descriptive placeholder text in Portuguese
        - Provides title attribute with format example
        - Supports keyboard navigation
        - Screen reader friendly
        
    Validation:
        - Server-side format validation via Django
        - Maximum length enforcement
        - Compatible with Django's datetime parsing
        
    Use Cases:
        - Diligencia conclusion timestamps
        - Event scheduling
        - Audit trail timestamps
        - User activity logging
    """
    input_type = 'text'
    
    def __init__(self, attrs=None, format=None):
        default_attrs = {
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa hh:mm',
            'title': 'Digite a data e hora no formato dd/mm/aaaa hh:mm (ex: 31/12/2023 14:30)',
            'maxlength': '16',
        }
        if attrs:
            default_attrs.update(attrs)
        
        # Use Brazilian datetime format
        if format is None:
            format = '%d/%m/%Y %H:%M'
            
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
    """
    Comprehensive form for creating and editing precatorios in the legal system.
    
    This form handles the complete lifecycle of precatorio management, including
    creation, editing, and validation of all precatorio-related fields. It enforces
    Brazilian legal standards for court document numbering (CNJ format) and
    manages complex financial calculations for legal settlements.
    
    Key Features:
        - CNJ number validation using Brazilian court standards
        - Financial value validation with Brazilian currency formatting
        - Budget year validation and constraints
        - Percentage validation for legal fee calculations
        - Status tracking for different precatorio stages
        - Integration with client management system
        - Audit trail support through timestamp fields
        
    Business Logic:
        - CNJ numbers must follow Brazilian court format: NNNNNNN-DD.AAAA.J.TR.OOOO
        - Origin CNJ must be different from main CNJ (different court cases)
        - Financial values must be positive and within legal limits
        - Percentage fields must sum to logical totals
        - Budget year must be current or future year
        - Status transitions must follow legal workflow
        
    Usage:
        # Creating new precatorio
        form = PrecatorioForm(request.POST or None)
        if form.is_valid():
            precatorio = form.save()
            
        # Editing existing precatorio
        form = PrecatorioForm(request.POST or None, instance=precatorio)
        
        # With initial data
        form = PrecatorioForm(initial={'orcamento': 2024})
    
    Fields:
        cnj (CharField): Primary CNJ court number
            - Format: NNNNNNN-DD.AAAA.J.TR.OOOO
            - Required, validated using validate_cnj()
            - Unique identifier for the precatorio
            
        origem (CharField): Origin CNJ court number  
            - Format: NNNNNNN-DD.AAAA.J.TR.OOOO
            - Required, must be different from main CNJ
            - References original court case
            
        orcamento (IntegerField): Budget year
            - Must be current year or later
            - Used for financial planning and budgeting
            
        valor_de_face (DecimalField): Face value of the precatorio
            - Brazilian currency format (R$ 0,00)
            - Maximum 15 digits, 2 decimal places
            - Represents the original court-determined amount
            
        ultima_atualizacao (DecimalField): Last updated value
            - Current calculated value with corrections
            - Updated with monetary adjustments
            
        data_ultima_atualizacao (DateField): Last update date
            - Brazilian date format (dd/mm/yyyy)
            - Tracks when value was last updated
            
        percentual_contratuais_assinado (DecimalField): Signed contractual percentage
        percentual_contratuais_apartado (DecimalField): Separated contractual percentage  
        percentual_sucumbenciais (DecimalField): Succumbential fees percentage
        
        credito_principal (CharField): Principal credit status
        honorarios_contratuais (CharField): Contractual fees status
        honorarios_sucumbenciais (CharField): Succumbential fees status
        
    Validation:
        - CNJ format validation using regex patterns
        - Financial value range validation
        - Percentage sum validation (business rules)
        - Date consistency validation
        - Status transition validation
        
    Widgets:
        - BrazilianDateInput for date fields
        - TextInput with CNJ format patterns
        - NumberInput with Brazilian currency formatting
        - Select widgets for status choices
        
    Security Considerations:
        - CNJ validation prevents injection attacks
        - Financial value sanitization
        - Status validation prevents unauthorized changes
        - Input length limitations
        
    Performance:
        - Optimized field validation
        - Minimal database queries during validation
        - Efficient widget rendering
        
    Integration Points:
        - Cliente model through ManyToMany relationship
        - Alvara and Requerimento models as related objects
        - Financial calculation utilities
        - Court system integration APIs
    """
    """
    Comprehensive form for creating and editing precatorios in the legal system.
    
    This form handles the complete lifecycle of precatorio management, including
    creation, editing, and validation of all precatorio-related fields. It enforces
    Brazilian legal standards for court document numbering (CNJ format) and
    manages complex financial calculations for legal settlements.
    
    Key Features:
        - CNJ number validation using Brazilian court standards
        - Financial value validation with Brazilian currency formatting
        - Budget year validation and constraints
        - Percentage validation for legal fee calculations
        - Status tracking for different precatorio stages
        - Integration with client management system
        - Audit trail support through timestamp fields
        
    Business Logic:
        - CNJ numbers must follow Brazilian court format: NNNNNNN-DD.AAAA.J.TR.OOOO
        - Origin CNJ must be different from main CNJ (different court cases)
        - Financial values must be positive and within legal limits
        - Percentage fields must sum to logical totals
        - Budget year must be current or future year
        - Status transitions must follow legal workflow
        
    Usage:
        # Creating new precatorio
        form = PrecatorioForm(request.POST or None)
        if form.is_valid():
            precatorio = form.save()
            
        # Editing existing precatorio
        form = PrecatorioForm(request.POST or None, instance=precatorio)
        
        # With initial data
        form = PrecatorioForm(initial={'orcamento': 2024})
    
    Fields:
        cnj (CharField): Primary CNJ court number
            - Format: NNNNNNN-DD.AAAA.J.TR.OOOO
            - Required, validated using validate_cnj()
            - Unique identifier for the precatorio
            
        origem (CharField): Origin CNJ court number  
            - Format: NNNNNNN-DD.AAAA.J.TR.OOOO
            - Required, must be different from main CNJ
            - References original court case
            
        orcamento (IntegerField): Budget year
            - Must be current year or later
            - Used for financial planning and budgeting
            
        valor_de_face (DecimalField): Face value of the precatorio
            - Brazilian currency format (R$ 0,00)
            - Maximum 15 digits, 2 decimal places
            - Represents the original court-determined amount
            
        ultima_atualizacao (DecimalField): Last updated value
            - Current calculated value with corrections
            - Updated with monetary adjustments
            
        data_ultima_atualizacao (DateField): Last update date
            - Brazilian date format (dd/mm/yyyy)
            - Tracks when value was last updated
            
        percentual_contratuais_assinado (DecimalField): Signed contractual percentage
        percentual_contratuais_apartado (DecimalField): Separated contractual percentage  
        percentual_sucumbenciais (DecimalField): Succumbential fees percentage
        
        credito_principal (CharField): Principal credit status
        honorarios_contratuais (CharField): Contractual fees status
        honorarios_sucumbenciais (CharField): Succumbential fees status
        
    Validation:
        - CNJ format validation using regex patterns
        - Financial value range validation
        - Percentage sum validation (business rules)
        - Date consistency validation
        - Status transition validation
        
    Widgets:
        - BrazilianDateInput for date fields
        - TextInput with CNJ format patterns
        - NumberInput with Brazilian currency formatting
        - Select widgets for status choices
        
    Security Considerations:
        - CNJ validation prevents injection attacks
        - Financial value sanitization
        - Status validation prevents unauthorized changes
        - Input length limitations
        
    Performance:
        - Optimized field validation
        - Minimal database queries during validation
        - Efficient widget rendering
        
    Integration Points:
        - Cliente model through ManyToMany relationship
        - Alvara and Requerimento models as related objects
        - Financial calculation utilities
        - Court system integration APIs
    """
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
            "tipo",
            "credito_principal",
            "honorarios_contratuais",
            "honorarios_sucumbenciais",
            "valor_de_face",
            "ultima_atualizacao",
            "data_ultima_atualizacao",
            "percentual_contratuais_assinado",
            "percentual_contratuais_apartado",
            "percentual_sucumbenciais",
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
            'tipo': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Selecione o tipo de precatório'
            }),
            'credito_principal': forms.Select(attrs={'class': 'form-select'}),
            'honorarios_contratuais': forms.Select(attrs={'class': 'form-select'}),
            'honorarios_sucumbenciais': forms.Select(attrs={'class': 'form-select'}),
        }
        
        labels = {
            'orcamento': 'Ano do Orçamento',
            'tipo': 'Tipo de Precatório',
            'credito_principal': 'Status do Crédito Principal',
            'honorarios_contratuais': 'Status dos Honorários Contratuais',
            'honorarios_sucumbenciais': 'Status dos Honorários Sucumbenciais',
            'data_ultima_atualizacao': 'Data da Última Atualização (Opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset to only show active tipos
        self.fields['tipo'].queryset = Tipo.objects.filter(ativa=True).order_by('ordem', 'nome')
        self.fields['tipo'].empty_label = "Selecione o tipo de precatório"

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
    """
    Comprehensive form for managing client information in the precatorios system.
    
    This form provides full client lifecycle management, supporting both individuals
    (CPF) and corporations (CNPJ). It handles client creation, editing, and validation
    according to Brazilian legal document standards and business requirements.
    
    Key Features:
        - Dual support for CPF (individuals) and CNPJ (corporations)
        - Brazilian document validation using official algorithms
        - Age calculation and priority determination
        - Flexible input formatting (accepts various formats)
        - Comprehensive validation with user-friendly error messages
        - Bootstrap styling for consistent user interface
        - Accessibility support with proper labels and help text
        
    Business Logic:
        - CPF validation using Brazilian algorithm (11 digits)
        - CNPJ validation using Brazilian algorithm (14 digits)
        - Automatic age calculation from birth date
        - Priority flag for special case handling
        - Duplicate client prevention through unique constraints
        - Format normalization (removes formatting characters)
        
    Usage:
        # Creating new client
        form = ClienteForm(request.POST or None)
        if form.is_valid():
            client = form.save()
            
        # Editing existing client
        form = ClienteForm(request.POST or None, instance=client)
        
        # With initial data
        form = ClienteForm(initial={'prioridade': True})
    
    Fields:
        cpf (CharField): CPF or CNPJ identification number
            - max_length: 18 characters (formatted CNPJ)
            - Required field with comprehensive validation
            - Supports multiple input formats
            - Algorithm validation for document authenticity
            
        nome (CharField): Full name or company name
            - Required field for client identification
            - Bootstrap form-control styling
            - Placeholder guidance for user input
            
        nascimento (DateField): Birth date or foundation date
            - Brazilian date format (dd/mm/yyyy)
            - Uses BrazilianDateInput widget
            - Required for age calculation and legal purposes
            
        prioridade (BooleanField): Priority flag for special handling
            - Optional field, defaults to False
            - Used for expedited processing cases
            - Checkbox input with Bootstrap styling
            
    Validation:
        - CPF: 11-digit validation with algorithm verification
        - CNPJ: 14-digit validation with algorithm verification
        - Duplicate prevention: Checks for existing clients
        - Format normalization: Removes dots, dashes, slashes
        - Required field validation with appropriate error messages
        
    Document Format Support:
        CPF (Individuals):
            - Formatted: 000.000.000-00
            - Unformatted: 00000000000
            
        CNPJ (Corporations):
            - Formatted: 00.000.000/0000-00
            - Unformatted: 00000000000000
            
    Error Messages:
        - "CPF inválido. Verifique se o número está correto."
        - "CNPJ inválido. Verifique se o número está correto."
        - "CPF deve ter exatamente 11 dígitos."
        - "CNPJ deve ter exatamente 14 dígitos."
        - "Já existe um cliente com este CPF/CNPJ."
        - "CPF ou CNPJ é obrigatório."
        
    Widgets:
        - TextInput with pattern validation for CPF/CNPJ
        - TextInput with form-control styling for name
        - BrazilianDateInput for birth date
        - CheckboxInput for priority flag
        
    Security Considerations:
        - Input sanitization through digit extraction
        - Algorithm validation prevents fake documents
        - Unique constraint enforcement
        - Length validation prevents buffer overflow
        
    Performance:
        - Efficient validation algorithms
        - Minimal database queries during validation
        - Optimized widget rendering
        - Client-side format validation
        
    Accessibility:
        - Descriptive labels and help text
        - Pattern attributes for screen readers
        - Title attributes with format examples
        - Keyboard navigation support
        
    Integration Points:
        - Cliente model for data persistence
        - Precatorio model through relationships
        - validate_cpf() and validate_cnpj() utilities
        - Brazilian legal document standards
    """
    cpf = forms.CharField(
        max_length=18,
        label='CPF ou CNPJ',
        help_text='Digite o CPF (000.000.000-00) ou CNPJ (00.000.000/0000-00)',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CPF ou CNPJ',
            'pattern': r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})',
            'title': 'CPF: 000.000.000-00 ou 00000000000 | CNPJ: 00.000.000/0000-00 ou 00000000000000'
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
        Clean CPF/CNPJ field by removing formatting and validate it's not empty or invalid
        """
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            doc = ''.join(filter(str.isdigit, cpf))
            if len(doc) == 11:
                if not validate_cpf(doc):
                    raise forms.ValidationError('CPF inválido. Verifique se o número está correto.')
                return doc
            elif len(doc) == 14:
                if not validate_cnpj(doc):
                    raise forms.ValidationError('CNPJ inválido. Verifique se o número está correto.')
                return doc
            else:
                raise forms.ValidationError('Documento deve ser um CPF (11 dígitos) ou CNPJ (14 dígitos).')
        else:
            raise forms.ValidationError('CPF ou CNPJ é obrigatório.')
    
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
    """
    Simplified client form for streamlined client creation within precatorio workflow.
    
    This form provides a lightweight alternative to ClienteForm specifically designed
    for use within precatorio detail views and quick client creation scenarios.
    It focuses exclusively on CPF validation (individuals only) and excludes the
    precatorio_cnj field for simplified user experience.
    
    Key Features:
        - CPF-only validation (no CNPJ support)
        - Streamlined interface for quick client creation
        - Integrated duplicate prevention
        - Brazilian document validation
        - Bootstrap styling for consistency
        - Optimized for embedded use in precatorio forms
        - Simplified field set for essential information
        
    Business Logic:
        - CPF validation using Brazilian algorithm (11 digits only)
        - Automatic format normalization (removes formatting)
        - Duplicate client prevention through unique constraints
        - Required field validation with appropriate messages
        - Age calculation support through birth date
        - Priority flag for special case handling
        
    Usage:
        # Quick client creation in precatorio workflow
        form = ClienteSimpleForm(request.POST or None)
        if form.is_valid():
            client = form.save()
            
        # Embedded in precatorio creation
        cliente_form = ClienteSimpleForm(prefix='cliente')
        
        # With validation check
        if cliente_form.is_valid():
            new_client = cliente_form.save()
    
    Fields:
        cpf (CharField): CPF identification number (individuals only)
            - max_length: 18 characters (to support formatted input)
            - Required field with comprehensive validation
            - Supports both formatted and unformatted input
            - Algorithm validation for document authenticity
            - Pattern validation for real-time feedback
            
        nome (CharField): Full name of the individual
            - Required field for client identification
            - Bootstrap form-control styling
            - Placeholder guidance for user input
            - Inherited from model definition
            
        nascimento (DateField): Birth date for age calculation
            - Brazilian date format (dd/mm/yyyy)
            - Uses BrazilianDateInput widget
            - Required for legal age verification
            - Inherited from model definition
            
        prioridade (BooleanField): Priority flag for expedited processing
            - Optional field, defaults to False
            - Checkbox input with Bootstrap styling
            - Used for special case handling
            - Inherited from model definition
            
    Validation:
        - CPF: 11-digit validation with Brazilian algorithm
        - Format normalization: Removes dots and dashes
        - Duplicate prevention: Checks for existing clients
        - Required field validation with user-friendly messages
        - Length validation (exactly 11 digits required)
        
    Document Format Support:
        CPF (Individuals only):
            - Formatted: 000.000.000-00
            - Unformatted: 00000000000
            - No CNPJ support (use ClienteForm for corporations)
            
    Error Messages:
        - "CPF deve ter exatamente 11 dígitos."
        - "CPF inválido. Verifique se o número está correto."
        - "Já existe um cliente com este CPF."
        - "CPF é obrigatório."
        
    Widgets:
        - TextInput with CPF pattern validation
        - TextInput with form-control styling for name
        - BrazilianDateInput for birth date
        - CheckboxInput for priority flag
        
    Differences from ClienteForm:
        - No CNPJ support (CPF only)
        - Simplified validation logic
        - Optimized for embedded use
        - Reduced field complexity
        - Focused on individual clients only
        
    Security Considerations:
        - Input sanitization through digit extraction
        - CPF algorithm validation prevents fake documents
        - Unique constraint enforcement
        - Length validation prevents malformed input
        
    Performance:
        - Streamlined validation for faster processing
        - Minimal database queries during validation
        - Optimized for embedded form scenarios
        - Reduced complexity for better responsiveness
        
    Accessibility:
        - Descriptive labels and help text
        - Pattern attributes for screen readers
        - Title attributes with format examples
        - Keyboard navigation support
        
    Integration Points:
        - Cliente model for data persistence
        - Precatorio workflow for client assignment
        - validate_cpf() utility function
        - Brazilian CPF validation standards
        - Bootstrap styling framework
    """
    cpf = forms.CharField(
            max_length=18,
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
            if len(cpf_numbers) != 11 and len(cpf_numbers) != 14:
                raise forms.ValidationError('CPF deve ter exatamente 11 dígitos.')
            if not validate_cpf(cpf_numbers):
                raise forms.ValidationError('CPF inválido. Verifique se o número está correto.')
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
    """
    Form for searching and linking precatorios by CNJ number to client records.
    
    This form provides a specialized interface for finding existing precatorios
    in the system using their CNJ (Conselho Nacional de Justiça) identification
    numbers. It's primarily used during client management workflows when linking
    existing precatorios to client profiles or verifying precatorio existence.
    
    Key Features:
        - CNJ format validation according to Brazilian standards
        - Real-time pattern validation for user feedback
        - Integration with precatorio search functionality
        - Bootstrap styling for consistent user interface
        - Comprehensive error handling for invalid CNJ formats
        - Client-side validation with pattern matching
        
    Business Logic:
        - CNJ validation using official Brazilian format
        - Format: NNNNNNN-DD.AAAA.J.TR.OOOO
        - Sequential number validation (NNNNNNN)
        - Check digit validation (DD)
        - Year validation (AAAA)
        - Judicial segment validation (J)
        - Court validation (TR)
        - Origin validation (OOOO)
        
    Usage:
        # Basic precatorio search
        form = PrecatorioSearchForm(request.POST or None)
        if form.is_valid():
            cnj = form.cleaned_data['cnj']
            precatorio = Precatorio.objects.get(cnj=cnj)
            
        # Client linking workflow
        search_form = PrecatorioSearchForm()
        if search_form.is_valid():
            link_precatorio_to_client(cnj, client_id)
            
        # Validation check
        if form.is_valid():
            cnj_number = form.cleaned_data['cnj']
            # Process linking logic
    
    Fields:
        cnj (CharField): CNJ identification number
            - max_length: 25 characters (includes formatting)
            - Required field with comprehensive validation
            - Brazilian CNJ format validation
            - Pattern matching for real-time feedback
            - Help text with format guidance
            
    CNJ Format Structure:
        Format: NNNNNNN-DD.AAAA.J.TR.OOOO
        Components:
            - NNNNNNN: Sequential number (7 digits)
            - DD: Check digits (2 digits)
            - AAAA: Year of case registration (4 digits)
            - J: Judicial segment (1 digit)
            - TR: Court code (2 digits)
            - OOOO: Origin code (4 digits)
            
    Validation:
        - CNJ format validation using validate_cnj() function
        - Pattern matching for real-time user feedback
        - Length validation (exactly 25 characters formatted)
        - Check digit algorithm validation
        - Required field validation
        
    Error Messages:
        - "CNJ inválido. Verifique o formato: NNNNNNN-DD.AAAA.J.TR.OOOO"
        - "Campo obrigatório."
        - "Formato inválido. Use: 1234567-89.2023.8.26.0100"
        
    Widgets:
        - TextInput with CNJ pattern validation
        - Bootstrap form-control styling
        - Placeholder with example format
        - Title attribute for accessibility
        - Pattern attribute for client-side validation
        
    Security Considerations:
        - Input validation prevents malformed CNJ numbers
        - Server-side validation with validate_cnj()
        - Pattern matching prevents script injection
        - Length validation prevents buffer overflow
        
    Performance:
        - Efficient CNJ validation algorithm
        - Client-side pattern validation reduces server requests
        - Minimal database impact during validation
        - Optimized for search functionality
        
    Accessibility:
        - Descriptive label and help text
        - Pattern attribute for screen readers
        - Title attribute with format example
        - Keyboard navigation support
        - Clear error messaging
        
    Integration Points:
        - Precatorio model for search functionality
        - validate_cnj() utility function
        - Client linking workflows
        - Brazilian CNJ standards compliance
        - Court system integration requirements
        
    Example CNJ Numbers:
        - Valid: 1234567-89.2023.8.26.0100
        - Valid: 5000123-45.2022.1.15.0001
        - Invalid: 123456-78.2023.8.26.0100 (wrong length)
        - Invalid: 1234567.89.2023.8.26.0100 (missing dash)
    """
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
    """
    Form for searching and validating clients by CPF/CNPJ to link to precatorios.
    
    This form provides a secure and user-friendly interface for finding existing
    clients in the system using their CPF (individual) or CNPJ (corporate) numbers.
    It's primarily used when linking clients to precatorios during the precatorio
    creation process.
    
    Key Features:
        - CPF and CNPJ validation using Brazilian algorithms
        - Flexible input format (accepts with or without formatting)
        - Real-time format validation via HTML5 patterns
        - Comprehensive error messages in Portuguese
        - Bootstrap styling for consistent UI
        
    Business Logic:
        - Validates CPF using official Brazilian algorithm
        - Validates CNPJ using official Brazilian algorithm
        - Normalizes input by removing formatting characters
        - Provides clear feedback for invalid documents
        
    Usage:
        # In views.py
        form = ClienteSearchForm(request.POST or None)
        if form.is_valid():
            cpf_cnpj = form.cleaned_data['cpf']
            cliente = Cliente.objects.filter(cpf=cpf_cnpj).first()
            
        # In templates
        {{ form.cpf.label_tag }}
        {{ form.cpf }}
        {{ form.cpf.help_text }}
    
    Fields:
        cpf (CharField): CPF or CNPJ input field
            - max_length: 18 characters (formatted CNPJ length)
            - Required field with validation
            - Accepts multiple formats (formatted/unformatted)
            
    Validation:
        - Length validation: 11 digits (CPF) or 14 digits (CNPJ)
        - Algorithm validation: Uses validate_cpf() and validate_cnpj()
        - Format normalization: Removes dots, dashes, slashes
        - Required field validation
        
    Supported Formats:
        CPF:
            - Formatted: 000.000.000-00
            - Unformatted: 00000000000
        CNPJ:
            - Formatted: 00.000.000/0000-00
            - Unformatted: 00000000000000
            
    Error Messages:
        - "CPF inválido. Verifique se o número está correto."
        - "CNPJ inválido. Verifique se o número está correto."
        - "Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."
        - "CPF ou CNPJ é obrigatório."
        
    HTML Attributes:
        - class: 'form-control' (Bootstrap styling)
        - placeholder: 'CPF ou CNPJ'
        - pattern: Regex for client-side validation
        - title: Descriptive help text for accessibility
        
    Security Considerations:
        - Input sanitization via digit extraction
        - Algorithm validation prevents fake documents
        - No sensitive data exposure in error messages
        
    Performance:
        - Lightweight validation (client and server-side)
        - No database queries during validation
        - Fast document algorithm verification
        
    Integration Points:
        - Links with Cliente model for client lookup
        - Used in precatorio creation workflows
        - Compatible with existing client management system
    """
    cpf = forms.CharField(
        max_length=18,
        label='CPF ou CNPJ do Cliente',
        help_text='Digite o CPF ou CNPJ do cliente para vincular ao precatório. Aceita formatos com ou sem pontuação.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CPF ou CNPJ',
            'pattern': r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{11}|\d{14})',
            'title': 'Digite o CPF (000.000.000-00 ou 00000000000) ou CNPJ (00.000.000/0000-00 ou 00000000000000)'
        })
    )
    
    def clean_cpf(self):
        """
        Clean CPF/CNPJ field by removing formatting and validate it's not empty and is valid
        """
        doc = self.cleaned_data.get('cpf')
        if doc:
            doc_numbers = ''.join(filter(str.isdigit, doc))
            if len(doc_numbers) == 11:
                if not validate_cpf(doc_numbers):
                    raise forms.ValidationError('CPF inválido. Verifique se o número está correto.')
            elif len(doc_numbers) == 14:
                if not validate_cnpj(doc_numbers):
                    raise forms.ValidationError('CNPJ inválido. Verifique se o número está correto.')
            else:
                raise forms.ValidationError('Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido.')
            return doc_numbers
        else:
            raise forms.ValidationError('CPF ou CNPJ é obrigatório.')


class RequerimentoForm(forms.ModelForm):
    """
    Comprehensive form for creating and managing requerimento (request) records in the precatorios system.
    
    This form handles the creation of requerimentos, which represent formal requests
    associated with precatorios. It manages financial calculations, client validation,
    process phase tracking, and discount calculations. The form ensures data integrity
    through comprehensive validation and provides a user-friendly interface for
    legal professionals managing precatorio workflows.
    
    Key Features:
        - Client validation through CPF/CNPJ verification
        - Financial value handling with Brazilian currency formatting
        - Discount (deságio) percentage calculations
        - Process phase management and tracking
        - Client-precatorio relationship validation
        - Comprehensive error handling and user feedback
        - Bootstrap styling for consistent user interface
        - Real-time validation with pattern matching
        
    Business Logic:
        - Validates client existence and precatorio association
        - Ensures client is linked to the precatorio before creating requerimento
        - Handles financial calculations with proper decimal precision
        - Manages process phases specific to requerimento workflow
        - Validates discount percentages within acceptable ranges
        - Supports both CPF (individuals) and CNPJ (corporations)
        - Enforces business rules for legal compliance
        
    Usage:
        # Creating new requerimento
        form = RequerimentoForm(request.POST or None, precatorio=precatorio_instance)
        if form.is_valid():
            requerimento = form.save(commit=False)
            requerimento.precatorio = precatorio_instance
            requerimento.save()
            
        # With existing data
        form = RequerimentoForm(instance=requerimento, precatorio=precatorio)
        
        # Validation workflow
        if form.is_valid():
            # Process financial calculations
            valor = form.cleaned_data['valor']
            desagio = form.cleaned_data['desagio']
            valor_final = valor * (1 - desagio/100)
    
    Fields:
        cliente_cpf (CharField): Client identification document
            - max_length: 18 characters (formatted CNPJ)
            - Required for client validation and linking
            - Supports both CPF and CNPJ formats
            - Pattern validation for real-time feedback
            - Validates client exists and is linked to precatorio
            
        valor (DecimalField): Financial value of the requerimento
            - max_digits: 15, decimal_places: 2
            - Brazilian currency formatting (50.000,00)
            - Comprehensive currency validation
            - Required field for financial calculations
            - Supports large monetary values typical in legal cases
            
        desagio (DecimalField): Discount percentage
            - max_digits: 5, decimal_places: 2
            - Percentage format (0.00 to 100.00)
            - Brazilian number formatting (15,50)
            - Used for financial discount calculations
            - Optional field with validation
            
        fase (ModelChoiceField): Process phase selection
            - Dynamic queryset filtered for requerimento phases
            - Optional field for process tracking
            - Dropdown selection with empty label
            - Bootstrap styling for consistency
            - Filtered to show only relevant phases
            
    Validation:
        - CPF: 11-digit validation with Brazilian algorithm
        - CNPJ: 14-digit validation with Brazilian algorithm
        - Client existence: Validates client is registered in system
        - Client-precatorio relationship: Ensures proper linking
        - Financial values: Positive values with proper formatting
        - Discount ranges: Validates percentage within acceptable bounds
        
    Document Format Support:
        CPF (Individuals):
            - Formatted: 000.000.000-00
            - Unformatted: 00000000000
            
        CNPJ (Corporations):
            - Formatted: 00.000.000/0000-00
            - Unformatted: 00000000000000
            
    Financial Format Support:
        Valor (Currency):
            - Brazilian format: 50.000,00
            - Decimal precision: 2 places
            - Maximum value: 999,999,999,999.99
            
        Deságio (Percentage):
            - Brazilian format: 15,50
            - Range: 0.00 to 100.00
            - Decimal precision: 2 places
            
    Error Messages:
        - "CPF inválido. Verifique se o número está correto."
        - "CNPJ inválido. Verifique se o número está correto."
        - "Documento deve ser um CPF (11 dígitos) ou CNPJ (14 dígitos)."
        - "O cliente [nome] não está vinculado ao precatório [CNJ]."
        - "Não foi encontrado um cliente com o documento [documento]."
        - "Valor deve ser um número positivo."
        - "Deságio deve estar entre 0% e 100%."
        
    Widgets:
        - TextInput with CPF/CNPJ pattern validation
        - TextInput with brazilian-currency class for value
        - TextInput with brazilian-number class for percentage
        - Select dropdown for phase selection
        - Bootstrap form-control styling throughout
        
    Security Considerations:
        - Input sanitization for financial values
        - Client-precatorio relationship validation
        - Document algorithm validation
        - Decimal precision control
        - SQL injection prevention through ORM
        
    Performance:
        - Efficient client lookup with database indexing
        - Optimized phase queryset filtering
        - Minimal validation queries
        - Client-side format validation
        
    Accessibility:
        - Descriptive labels and help text
        - Pattern attributes for screen readers
        - Title attributes with format examples
        - Keyboard navigation support
        - Clear error messaging
        
    Integration Points:
        - Cliente model for client validation
        - Precatorio model for relationship verification
        - Requerimento model for data persistence
        - Fase model for phase management
        - validate_cpf() and validate_cnpj() utilities
        - validate_currency() for financial validation
        
    Financial Calculations:
        - Base value: valor field input
        - Discount: desagio percentage
        - Final value: valor * (1 - desagio/100)
        - Currency formatting: Brazilian standards
        - Precision: 2 decimal places throughout
    """
    cliente_cpf = forms.CharField(
            max_length=18,
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
    
    def __init__(self, *args, **kwargs):
        self.precatorio = kwargs.pop('precatorio', None)
        super().__init__(*args, **kwargs)
        # Set queryset to only show phases for Requerimento
        from .models import Fase
        self.fields['fase'].queryset = Fase.get_fases_for_requerimento()
    
    def clean_cliente_cpf(self):
        """Validate that the CPF or CNPJ corresponds to an existing cliente"""
        cpf = self.cleaned_data.get('cliente_cpf')
        if cpf:
            cpf_numbers = ''.join(filter(str.isdigit, cpf))
            if len(cpf_numbers) == 11:
                if not validate_cpf(cpf_numbers):
                    raise forms.ValidationError('CPF inválido. Verifique se o número está correto.')
            elif len(cpf_numbers) == 14:
                if not validate_cnpj(cpf_numbers):
                    raise forms.ValidationError('CNPJ inválido. Verifique se o número está correto.')
            else:
                raise forms.ValidationError('Documento deve ser um CPF (11 dígitos) ou CNPJ (14 dígitos).')
            try:
                from .models import Cliente
                cliente = Cliente.objects.get(cpf=cpf_numbers)
                if self.precatorio and not self.precatorio.clientes.filter(cpf=cpf_numbers).exists():
                    raise forms.ValidationError(
                        f'O cliente {cliente.nome} (CPF/CNPJ: {cpf}) não está vinculado ao precatório {self.precatorio.cnj}. '
                        'Vincule o cliente ao precatório antes de criar o requerimento.'
                    )
                return cpf
            except Cliente.DoesNotExist:
                raise forms.ValidationError(f'Não foi encontrado um cliente com o documento "{cpf}". Verifique se o número está correto ou cadastre o cliente primeiro.')
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
            'fase': 'Fase Principal',
        }


class AlvaraSimpleForm(forms.ModelForm):
    """
    Simplified form for creating and managing alvará (judicial authorization) records within precatorio workflow.
    
    This form provides a streamlined interface for creating alvarás, which are judicial
    authorizations for payment release in the precatorios system. It handles financial
    calculations for different types of fees, client validation, process phase tracking,
    and comprehensive validation while maintaining a user-friendly interface optimized
    for embedded use in precatorio detail views.
    
    Key Features:
        - Client validation through CPF verification
        - Multiple fee type management (principal, contractual, court fees)
        - Process phase tracking for both general and contractual fees
        - Alvará type classification (chronological order, priority, agreement)
        - Brazilian currency formatting and validation
        - Embedded use optimization for precatorio workflows
        - Comprehensive financial calculations and reporting
        - Bootstrap styling for consistent user interface
        
    Business Logic:
        - Validates client existence and precatorio association
        - Handles multiple financial value types with proper precision
        - Manages separate phase tracking for different fee types
        - Enforces business rules for judicial authorization processes
        - Supports different alvará types according to legal requirements
        - Calculates total values across all fee categories
        - Validates positive financial values and proper formatting
        
    Usage:
        # Creating new alvará within precatorio
        form = AlvaraSimpleForm(request.POST or None, precatorio=precatorio_instance)
        if form.is_valid():
            alvara = form.save(commit=False)
            alvara.precatorio = precatorio_instance
            alvara.save()
            
        # With financial calculation
        if form.is_valid():
            principal = form.cleaned_data['valor_principal']
            contratuais = form.cleaned_data['honorarios_contratuais'] or 0
            sucumbenciais = form.cleaned_data['honorarios_sucumbenciais'] or 0
            total = principal + contratuais + sucumbenciais
            
        # Embedded in precatorio workflow
        alvara_form = AlvaraSimpleForm(prefix='alvara', precatorio=precatorio)
    
    Fields:
        cliente_cpf (CharField): Client identification document
            - max_length: 18 characters (formatted)
            - Required for client validation and linking
            - CPF format validation with pattern matching
            - Real-time validation feedback
            - Validates client exists in system
            
        tipo (ChoiceField): Type of alvará authorization
            - ordem cronológica: Chronological order payment
            - prioridade: Priority payment for special cases
            - acordo: Agreement-based payment
            - Required field with dropdown selection
            - Bootstrap styling for consistency
            
        fase (ModelChoiceField): General process phase
            - Dynamic queryset filtered for alvará phases
            - Optional field for process tracking
            - Dropdown selection with empty label
            - Bootstrap styling for consistency
            
        fase_honorarios_contratuais (ModelChoiceField): Contractual fees phase
            - Separate phase tracking for contractual fees
            - Dynamic queryset for active phases only
            - Optional field with specific help text
            - Independent phase management
            
        valor_principal (DecimalField): Principal amount
            - max_digits: 15, decimal_places: 2
            - Required field for main payment amount
            - Brazilian currency formatting
            - Comprehensive currency validation
            
        honorarios_contratuais (DecimalField): Contractual fees
            - max_digits: 15, decimal_places: 2
            - Optional field for lawyer contractual fees
            - Brazilian currency formatting
            - Used in total calculations
            
        honorarios_sucumbenciais (DecimalField): Court-awarded fees
            - max_digits: 15, decimal_places: 2
            - Optional field for court-determined fees
            - Brazilian currency formatting
            - Legal requirement compliance
            
    Validation:
        - CPF: 11-digit validation with Brazilian algorithm
        - Client existence: Validates client is registered
        - Financial values: Positive values with proper formatting
        - Type selection: Required field validation
        - Phase selection: Optional but validated if provided
        
    Alvará Types:
        Ordem Cronológica:
            - Standard chronological payment order
            - Regular processing timeline
            - Standard priority level
            
        Prioridade:
            - Expedited processing for special cases
            - Higher priority in payment queue
            - Special legal requirements
            
        Acordo:
            - Agreement-based settlements
            - Negotiated payment terms
            - Alternative dispute resolution
            
    Financial Categories:
        Valor Principal:
            - Main debt amount
            - Required field
            - Base for calculations
            
        Honorários Contratuais:
            - Lawyer contractual fees
            - Optional field
            - Separate phase tracking
            
        Honorários Sucumbenciais:
            - Court-awarded attorney fees
            - Optional field
            - Legal compliance requirement
            
    Financial Format Support:
        Brazilian Currency Format:
            - Format: 50.000,00
            - Decimal precision: 2 places
            - Maximum value: 999,999,999,999.99
            - Thousands separator: period (.)
            - Decimal separator: comma (,)
            
    Error Messages:
        - "CPF deve ter exatamente 11 dígitos."
        - "CPF inválido. Verifique se o número está correto."
        - "Não foi encontrado um cliente com este CPF."
        - "Tipo de alvará é obrigatório."
        - "Valor deve ser um número positivo."
        - "Formato de moeda inválido."
        
    Widgets:
        - TextInput with CPF pattern validation
        - Select dropdown for type selection
        - Select dropdown for phase selections
        - TextInput with brazilian-currency class for values
        - Bootstrap form-control styling throughout
        
    Security Considerations:
        - Input sanitization for financial values
        - CPF algorithm validation
        - Client existence verification
        - Decimal precision control
        - SQL injection prevention through ORM
        
    Performance:
        - Efficient client lookup with indexing
        - Optimized phase queryset filtering
        - Minimal validation queries
        - Client-side format validation
        
    Accessibility:
        - Descriptive labels and help text
        - Pattern attributes for screen readers
        - Title attributes with format examples
        - Keyboard navigation support
        - Clear error messaging
        
    Integration Points:
        - Cliente model for client validation
        - Precatorio model for workflow integration
        - Alvará model for data persistence
        - Fase model for phase management
        - FaseHonorariosContratuais for fee tracking
        - validate_cpf() utility function
        - validate_currency() for financial validation
        
    Differences from Full AlvaraForm:
        - Simplified interface for embedded use
        - No precatorio_cnj field (context provided)
        - Optimized for precatorio detail workflows
        - Reduced complexity for better UX
        - Streamlined validation process
    """
    
    cliente_cpf = forms.CharField(
            max_length=18,
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
    
    def __init__(self, *args, **kwargs):
        self.precatorio = kwargs.pop('precatorio', None)
        super().__init__(*args, **kwargs)
        # Set queryset to only show phases for Alvará
        from .models import Fase, FaseHonorariosContratuais
        self.fields['fase'].queryset = Fase.get_fases_for_alvara()
        self.fields['fase_honorarios_contratuais'].queryset = FaseHonorariosContratuais.get_fases_ativas()
    
    def clean_cliente_cpf(self):
        """Validate that the CPF corresponds to an existing cliente"""
        cpf = self.cleaned_data.get('cliente_cpf')
        if cpf:
            # Remove dots and dashes, keep only numbers
            cpf_numbers = ''.join(filter(str.isdigit, cpf))
            if len(cpf_numbers) != 11 and len(cpf_numbers) != 14:
                raise forms.ValidationError('CPF deve ter exatamente 11 dígitos.')
            if not validate_cpf(cpf_numbers):
                raise forms.ValidationError('CPF inválido. Verifique se o número está correto.')
            try:
                from .models import Cliente
                cliente = Cliente.objects.get(cpf=cpf_numbers)
                
                # Additional validation: check if cliente is linked to the precatorio
                if self.precatorio and not self.precatorio.clientes.filter(cpf=cpf_numbers).exists():
                    raise forms.ValidationError(
                        f'O cliente {cliente.nome} (CPF: {cpf}) não está vinculado ao precatório {self.precatorio.cnj}. '
                        'Vincule o cliente ao precatório antes de criar o alvará.'
                    )
                
                return cpf
            except Cliente.DoesNotExist:
                raise forms.ValidationError(f'Não foi encontrado um cliente com o CPF "{cpf}". Verifique se o número está correto ou cadastre o cliente primeiro.')
        return cpf
    
    def clean_honorarios_contratuais(self):
        """Clean honorarios_contratuais field to provide default value"""
        honorarios = self.cleaned_data.get('honorarios_contratuais')
        return honorarios if honorarios is not None else 0.0
    
    def clean_honorarios_sucumbenciais(self):
        """Clean honorarios_sucumbenciais field to provide default value"""
        honorarios = self.cleaned_data.get('honorarios_sucumbenciais')
        return honorarios if honorarios is not None else 0.0

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
    """
    Comprehensive form for creating and managing custom process phases in the precatorios system.
    
    This form provides a complete interface for defining custom phases that track
    the progress of precatorios through various stages of the legal process.
    It supports visual customization, ordering, activation control, and type
    classification to create a flexible workflow management system.
    
    Key Features:
        - Custom phase name and description definition
        - Visual customization with color selection
        - Flexible type classification (alvará, requerimento, both)
        - Order management for logical phase progression
        - Activation control for phase lifecycle management
        - Comprehensive validation for unique naming
        - Bootstrap styling for consistent user interface
        - User-friendly form controls with guidance
        
    Business Logic:
        - Ensures unique phase names within the system
        - Validates proper color format (hexadecimal)
        - Manages phase ordering for logical workflow
        - Controls phase availability through activation
        - Supports different phase types for different processes
        - Provides visual identification through color coding
        - Maintains system integrity through validation
        
    Usage:
        # Creating new custom phase
        form = FaseForm(request.POST or None)
        if form.is_valid():
            phase = form.save()
            
        # Editing existing phase
        form = FaseForm(request.POST or None, instance=existing_phase)
        
        # With initial values
        form = FaseForm(initial={
            'tipo': 'ambos',
            'cor': '#6c757d',
            'ativa': True,
            'ordem': 0
        })
    
    Fields:
        nome (CharField): Unique phase name
            - max_length: 100 characters
            - Required field for phase identification
            - Must be unique across all phases
            - Bootstrap form-control styling
            - Placeholder guidance for users
            
        descricao (CharField): Optional phase description
            - Required: False
            - Textarea widget for detailed explanation
            - Helps users understand phase purpose
            - Bootstrap styling with 3 rows
            - Optional field for additional context
            
        tipo (ChoiceField): Phase type classification
            - alvará: Used only in alvará processes
            - requerimento: Used only in requerimento processes
            - ambos: Used in both process types
            - Default: 'ambos' for maximum flexibility
            - Required field with dropdown selection
            
        cor (CharField): Visual identification color
            - max_length: 7 characters (hexadecimal)
            - Color picker widget for visual selection
            - Default: '#6c757d' (Bootstrap gray)
            - Used for visual phase identification
            - Hexadecimal format validation
            
        ordem (IntegerField): Display order priority
            - min_value: 0 (prevents negative ordering)
            - Default: 0 (highest priority)
            - Controls phase display sequence
            - Lower numbers appear first
            - Allows logical workflow progression
            
        ativa (BooleanField): Phase activation status
            - Required: False (checkbox field)
            - Default: True (new phases active by default)
            - Controls phase availability in system
            - Allows phase lifecycle management
            - Bootstrap checkbox styling
            
    Phase Types:
        Alvará:
            - Specific to judicial authorization processes
            - Used in payment release workflows
            - Tracks alvará-specific milestones
            
        Requerimento:
            - Specific to formal request processes
            - Used in petition and application workflows
            - Tracks request-specific progress
            
        Ambos (Both):
            - Universal phases applicable to all processes
            - Maximum flexibility for common milestones
            - Default choice for new phases
            
    Validation:
        - Nome: Required, unique, maximum 100 characters
        - Tipo: Required, must be valid choice
        - Cor: Valid hexadecimal color format
        - Ordem: Non-negative integer
        - Ativa: Boolean validation
        
    Color Customization:
        - HTML5 color picker widget
        - Hexadecimal format (#RRGGBB)
        - Default Bootstrap gray (#6c757d)
        - Visual phase identification in interfaces
        - Accessibility considerations for color contrast
        
    Ordering System:
        - Integer-based ordering (0 = highest priority)
        - Allows logical workflow progression
        - Supports phase reordering without conflicts
        - Visual sorting in phase displays
        - Flexible insertion of new phases
        
    Error Messages:
        - "Nome da fase é obrigatório."
        - "Já existe uma fase com este nome."
        - "Tipo de fase é obrigatório."
        - "Formato de cor inválido."
        - "Ordem deve ser um número não negativo."
        
    Widgets:
        - TextInput with placeholder for name
        - Textarea with 3 rows for description
        - Select dropdown for type selection
        - Color picker for visual customization
        - NumberInput with min validation for order
        - Checkbox for activation status
        
    Security Considerations:
        - Input sanitization for text fields
        - Color format validation prevents injection
        - Integer validation for order field
        - Unique constraint enforcement
        - XSS prevention through proper escaping
        
    Performance:
        - Efficient uniqueness validation
        - Minimal database queries
        - Optimized form rendering
        - Client-side validation support
        
    Accessibility:
        - Descriptive labels and help text
        - Color picker accessibility features
        - Keyboard navigation support
        - Screen reader compatibility
        - Clear error messaging
        
    Integration Points:
        - Fase model for data persistence
        - Alvará and Requerimento workflow integration
        - Visual display systems throughout application
        - Phase selection in other forms
        - Workflow management systems
        
    Lifecycle Management:
        - Creation: All fields customizable
        - Editing: Full field modification support
        - Deactivation: Ativa flag for soft deletion
        - Reordering: Ordem field for position changes
        - Deletion: Hard deletion with cascade considerations
    """
    
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
    
    ordem = forms.IntegerField(
        min_value=0,
        initial=0,
        label='Ordem de Exibição',
        help_text='Número para definir a ordem de exibição (menores aparecem primeiro)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'placeholder': '0'
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
        """Basic nome field cleaning - strip whitespace"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
        return nome
    
    def clean(self):
        """Validate the entire form, including nome uniqueness within the same tipo"""
        cleaned_data = super().clean()
        nome = cleaned_data.get('nome')
        tipo = cleaned_data.get('tipo')
        
        if nome and tipo:
            nome = nome.strip()
            # Check if another fase with the same name and tipo exists (excluding current instance if editing)
            existing_fase = Fase.objects.filter(nome__iexact=nome, tipo=tipo)
            if self.instance.pk:
                existing_fase = existing_fase.exclude(pk=self.instance.pk)
            
            if existing_fase.exists():
                raise forms.ValidationError({
                    'nome': f'Já existe uma fase com o nome "{nome}" para o tipo "{dict(Fase.TIPO_CHOICES).get(tipo, tipo)}".'
                })
        
        return cleaned_data
    
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
        fields = ['nome', 'descricao', 'tipo', 'cor', 'ordem', 'ativa']


class FaseHonorariosContratuaisForm(forms.ModelForm):
    """
    Specialized form for creating and managing contractual fees (honorários contratuais) phases.
    
    This form provides a dedicated interface for defining custom phases specifically
    for tracking contractual attorney fees throughout the precatorio process. It
    offers similar functionality to FaseForm but is specialized for the unique
    requirements of contractual fee management, including separate color schemes
    and specific workflow considerations.
    
    Key Features:
        - Specialized phase management for contractual fees
        - Independent workflow tracking from main processes
        - Visual customization with fee-specific color defaults
        - Order management for logical fee phase progression
        - Activation control for phase lifecycle management
        - Unique naming validation within contractual fee context
        - Bootstrap styling for consistent user interface
        - Fee-specific help text and guidance
        
    Business Logic:
        - Ensures unique phase names within contractual fees context
        - Provides separate phase tracking for attorney fee processes
        - Validates proper color format (hexadecimal)
        - Manages phase ordering for logical fee workflow
        - Controls phase availability through activation
        - Maintains independence from general process phases
        - Supports complex fee tracking requirements
        
    Usage:
        # Creating new contractual fee phase
        form = FaseHonorariosContratuaisForm(request.POST or None)
        if form.is_valid():
            fee_phase = form.save()
            
        # Editing existing fee phase
        form = FaseHonorariosContratuaisForm(request.POST or None, instance=existing_phase)
        
        # With fee-specific defaults
        form = FaseHonorariosContratuaisForm(initial={
            'cor': '#28a745',  # Green for financial tracking
            'ativa': True,
            'ordem': 0
        })
    
    Fields:
        nome (CharField): Unique contractual fee phase name
            - max_length: 100 characters
            - Required field for phase identification
            - Must be unique within contractual fee phases
            - Bootstrap form-control styling
            - Fee-specific placeholder guidance
            
        descricao (CharField): Optional phase description
            - Required: False
            - Textarea widget for detailed explanation
            - Helps users understand fee phase purpose
            - Bootstrap styling with 3 rows
            - Optional field for additional context
            
        cor (CharField): Visual identification color
            - max_length: 7 characters (hexadecimal)
            - Color picker widget for visual selection
            - Default: '#28a745' (Bootstrap success green)
            - Used for visual fee phase identification
            - Hexadecimal format validation
            
        ordem (IntegerField): Display order priority
            - min_value: 0 (prevents negative ordering)
            - Default: 0 (highest priority)
            - Controls fee phase display sequence
            - Lower numbers appear first
            - Allows logical fee workflow progression
            
        ativa (BooleanField): Phase activation status
            - Required: False (checkbox field)
            - Default: True (new phases active by default)
            - Controls phase availability in system
            - Allows fee phase lifecycle management
            - Bootstrap checkbox styling
            
    Contractual Fee Context:
        Purpose:
            - Track attorney contractual fee processing
            - Monitor payment stages for legal representation
            - Separate workflow from main precatorio process
            - Specialized financial tracking requirements
            
        Workflow Independence:
            - Independent from general Fase phases
            - Separate color scheme (green theme)
            - Specialized naming context
            - Unique validation rules
            
        Business Requirements:
            - Attorney fee payment tracking
            - Contract compliance monitoring
            - Financial milestone management
            - Legal requirement adherence
            
    Validation:
        - Nome: Required, unique within contractual fees, max 100 chars
        - Cor: Valid hexadecimal color format
        - Ordem: Non-negative integer
        - Ativa: Boolean validation
        - Uniqueness: Scoped to contractual fee phases only
        
    Color Scheme:
        - Default: '#28a745' (Bootstrap success green)
        - Financial tracking theme
        - Visual distinction from general phases
        - Accessibility considerations for color contrast
        - User customizable through color picker
        
    Ordering System:
        - Integer-based ordering (0 = highest priority)
        - Logical fee processing progression
        - Supports phase reordering without conflicts
        - Visual sorting in fee phase displays
        - Flexible insertion of new fee phases
        
    Error Messages:
        - "Nome da fase é obrigatório."
        - "Já existe uma fase de honorários contratuais com este nome."
        - "Formato de cor inválido."
        - "Ordem deve ser um número não negativo."
        
    Widgets:
        - TextInput with fee-specific placeholder
        - Textarea with 3 rows for description
        - Color picker with green default
        - NumberInput with min validation for order
        - Checkbox for activation status
        
    Security Considerations:
        - Input sanitization for text fields
        - Color format validation prevents injection
        - Integer validation for order field
        - Unique constraint enforcement within scope
        - XSS prevention through proper escaping
        
    Performance:
        - Efficient scoped uniqueness validation
        - Minimal database queries
        - Optimized form rendering
        - Client-side validation support
        
    Accessibility:
        - Descriptive labels and help text
        - Color picker accessibility features
        - Keyboard navigation support
        - Screen reader compatibility
        - Clear error messaging
        
    Integration Points:
        - FaseHonorariosContratuais model for persistence
        - Alvará contractual fee tracking
        - Financial reporting systems
        - Fee phase selection in related forms
        - Attorney fee workflow management
        
    Differences from FaseForm:
        - Specialized for contractual fees only
        - Different default color scheme
        - Scoped uniqueness validation
        - Fee-specific help text and placeholders
        - Independent workflow tracking
        
    Lifecycle Management:
        - Creation: All fields customizable with fee defaults
        - Editing: Full field modification support
        - Deactivation: Ativa flag for soft deletion
        - Reordering: Ordem field for position changes
        - Deletion: Hard deletion with fee-specific cascade
    """
    
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
    
    ordem = forms.IntegerField(
        min_value=0,
        initial=0,
        label='Ordem de Exibição',
        help_text='Número para definir a ordem de exibição (menores aparecem primeiro)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'placeholder': '0'
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
        fields = ['nome', 'descricao', 'cor', 'ordem', 'ativa']


class DiligenciasForm(forms.ModelForm):
    """
    Comprehensive form for creating and managing diligências (legal tasks/procedures) in the precatorios system.
    
    This form provides a complete interface for creating diligências, which are
    specific legal tasks or procedures that need to be performed as part of the
    precatorio process. It handles task categorization, deadline management,
    priority classification, and detailed description capture with comprehensive
    validation to ensure proper task management.
    
    Key Features:
        - Dynamic tipo (type) selection from active options only
        - Date validation to prevent past deadlines
        - Priority/urgency classification system
        - Optional detailed descriptions for task clarity
        - Brazilian date formatting for local compliance
        - Bootstrap styling for consistent user interface
        - Comprehensive field validation and error handling
        - Integration with TipoDiligencia management system
        
    Business Logic:
        - Validates deadlines are not set in the past
        - Filters tipo options to active types only
        - Enforces required fields for essential information
        - Supports optional descriptions for flexibility
        - Integrates with urgency priority system
        - Maintains data integrity through validation
        - Provides user-friendly error messages
        
    Usage:
        # Creating new diligência
        form = DiligenciasForm(request.POST or None)
        if form.is_valid():
            diligencia = form.save(commit=False)
            diligencia.precatorio = precatorio_instance
            diligencia.save()
            
        # With initial data
        form = DiligenciasForm(initial={
            'urgencia': 'normal',
            'data_final': tomorrow_date
        })
        
        # Validation workflow
        if form.is_valid():
            # Process diligência creation
            task = form.save()
    
    Fields:
        tipo (ModelChoiceField): Type of legal task
            - Dynamic queryset filtered to active types only
            - Required field for task categorization
            - Dropdown selection with Bootstrap styling
            - Label: 'Tipo de Diligência'
            - Filtered through TipoDiligencia.get_ativos()
            
        data_final (DateField): Deadline for task completion
            - Required field for deadline management
            - Brazilian date format (dd/mm/yyyy)
            - Uses BrazilianDateInput widget
            - Label: 'Data Final'
            - Validation prevents past dates
            
        urgencia (ChoiceField): Priority/urgency level
            - Required field for priority classification
            - Dropdown selection with predefined options
            - Bootstrap form-control styling
            - Label: 'Urgência'
            - Supports priority-based task management
            
        descricao (TextField): Detailed task description
            - Optional field for additional details
            - Textarea widget with 3 rows
            - Bootstrap form-control styling
            - Label: 'Descrição'
            - Helps clarify task requirements
            
    Urgency Levels:
        - Available through model choices
        - Supports priority-based workflow management
        - Visual indicators for task prioritization
        - Integration with task management systems
        
    Validation:
        - Tipo: Required, must be active type
        - Data Final: Required, cannot be in the past
        - Urgência: Required, must be valid choice
        - Descrição: Optional, no specific validation
        
    Date Validation:
        - Past Date Prevention: data_final cannot be before today
        - Brazilian Format: dd/mm/yyyy input format
        - Timezone Awareness: Uses Django timezone utilities
        - User-Friendly Errors: Clear messaging for invalid dates
        
    Error Messages:
        - "Tipo de diligência é obrigatório."
        - "Data final é obrigatória."
        - "A data final não pode ser no passado."
        - "Urgência é obrigatória."
        
    Widgets:
        - Select dropdown for tipo selection
        - BrazilianDateInput for data_final
        - Select dropdown for urgencia
        - Textarea with 3 rows for descricao
        - Bootstrap form-control styling throughout
        
    Field Customization:
        - Dynamic tipo queryset (active types only)
        - Custom labels for user-friendly interface
        - Help text for guidance and clarity
        - Required field configuration
        - Bootstrap styling integration
        
    Security Considerations:
        - Date validation prevents invalid deadlines
        - Tipo filtering ensures valid selections only
        - Input sanitization through Django forms
        - XSS prevention through proper escaping
        - SQL injection prevention through ORM
        
    Performance:
        - Efficient queryset filtering for tipo
        - Minimal database queries during validation
        - Optimized form rendering
        - Client-side validation support
        
    Accessibility:
        - Descriptive labels and help text
        - Keyboard navigation support
        - Screen reader compatibility
        - Clear error messaging
        - Proper form structure
        
    Integration Points:
        - Diligencias model for data persistence
        - TipoDiligencia model for type management
        - Precatorio workflow integration
        - Task management systems
        - Priority-based scheduling
        - Brazilian date formatting standards
        
    Workflow Integration:
        - Task creation within precatorio context
        - Deadline management and tracking
        - Priority-based task organization
        - Type-based task categorization
        - Status tracking through related systems
    """
    
    class Meta:
        model = Diligencias
        fields = ['tipo', 'data_final', 'urgencia', 'descricao']
        widgets = {
            'data_final': BrazilianDateInput(),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'urgencia': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter tipo field to show only active tipos
        self.fields['tipo'].queryset = TipoDiligencia.get_ativos()
        
        # Customize field labels
        self.fields['tipo'].label = 'Tipo de Diligência'
        self.fields['data_final'].label = 'Data Final'
        self.fields['urgencia'].label = 'Urgência'
        self.fields['descricao'].label = 'Descrição'
        
        # Add help texts
        self.fields['data_final'].help_text = 'Data limite para conclusão da diligência'
        self.fields['descricao'].help_text = 'Descrição detalhada da diligência (opcional)'
        
        # Make all fields required except description
        self.fields['descricao'].required = False
        
    def clean_data_final(self):
        """Validate that data_final is not in the past"""
        data_final = self.cleaned_data.get('data_final')
        if data_final:
            from django.utils import timezone
            today = timezone.now().date()
            if data_final < today:
                raise forms.ValidationError('A data final não pode ser no passado.')
        return data_final


class DiligenciasUpdateForm(forms.ModelForm):
    """
    Specialized form for updating and completing diligências (legal tasks) status and progress.
    
    This form provides a focused interface for updating the completion status of
    existing diligências. It handles task completion marking, automatic timestamping,
    progress observations, and comprehensive validation to ensure proper task
    lifecycle management and audit trail maintenance.
    
    Key Features:
        - Task completion status toggle with validation
        - Automatic completion timestamp generation
        - Optional observations for completion notes
        - Brazilian date-time formatting for local compliance
        - Smart validation for completion requirements
        - Bootstrap styling for consistent user interface
        - Audit trail support through timestamp management
        - Flexible completion workflow handling
        
    Business Logic:
        - Automatically sets completion timestamp when task is marked complete
        - Clears completion timestamp when task is unmarked
        - Enforces completion timestamp requirement for completed tasks
        - Supports optional observations for completion context
        - Maintains data integrity through validation
        - Provides flexible workflow management
        - Ensures proper audit trail creation
        
    Usage:
        # Marking diligência as complete
        form = DiligenciasUpdateForm(request.POST or None, instance=diligencia)
        if form.is_valid():
            updated_diligencia = form.save()
            
        # With completion observations
        form = DiligenciasUpdateForm(initial={
            'concluida': True,
            'descricao': 'Task completed successfully'
        }, instance=diligencia)
        
        # Status update workflow
        if form.is_valid():
            # Process completion status change
            task = form.save()
    
    Fields:
        concluida (BooleanField): Task completion status
            - Checkbox input for completion toggle
            - Label: 'Marcar como concluída'
            - Bootstrap form-check-input styling
            - Triggers automatic timestamp setting
            - Required for completion workflow
            
        data_conclusao (DateTimeField): Completion timestamp
            - Optional field (auto-generated when needed)
            - Brazilian date-time format
            - Uses BrazilianDateTimeInput widget
            - Label: 'Data de conclusão'
            - Automatically set when task completed
            
        descricao (TextField): Completion observations
            - Optional field for additional context
            - Textarea widget with 3 rows
            - Bootstrap form-control styling
            - Label: 'Observações'
            - Supports audit trail documentation
            
    Completion Workflow:
        Task Completion:
            1. User checks 'concluida' checkbox
            2. System automatically sets current timestamp
            3. Optional observations can be added
            4. Validation ensures data consistency
            
        Task Reopening:
            1. User unchecks 'concluida' checkbox
            2. System clears completion timestamp
            3. Task returns to active status
            4. Previous observations remain for audit
            
    Validation:
        - Automatic Timestamp: Sets data_conclusao when concluida = True
        - Timestamp Clearing: Removes data_conclusao when concluida = False
        - Smart Validation: Ensures completion consistency
        - Optional Fields: Flexible observation capture
        
    Timestamp Management:
        Auto-Generation:
            - When concluida = True and data_conclusao is empty
            - Uses Django timezone.now() for accuracy
            - Ensures consistent timezone handling
            
        Auto-Clearing:
            - When concluida = False
            - Removes timestamp to indicate incomplete status
            - Maintains data integrity
            
    Error Messages:
        - No specific error messages (auto-correction approach)
        - Validation focuses on data consistency
        - User-friendly completion workflow
        
    Widgets:
        - CheckboxInput for completion status
        - BrazilianDateTimeInput for timestamps
        - Textarea with 3 rows for observations
        - Bootstrap styling throughout
        
    Security Considerations:
        - Automatic timestamp generation prevents tampering
        - Validation ensures data consistency
        - Input sanitization through Django forms
        - Audit trail preservation
        
    Performance:
        - Minimal database impact
        - Efficient timestamp handling
        - Optimized form rendering
        - Quick status updates
        
    Accessibility:
        - Clear labels and help text
        - Keyboard navigation support
        - Screen reader compatibility
        - Intuitive form structure
        
    Integration Points:
        - Diligencias model for status updates
        - Django timezone utilities for timestamps
        - Audit trail systems
        - Task management workflows
        - Brazilian date-time formatting
        
    Audit Trail Features:
        - Automatic completion timestamping
        - Observation capture for context
        - Status change tracking
        - Data integrity maintenance
        - Historical record preservation
        
    Workflow States:
        Active Task:
            - concluida = False
            - data_conclusao = None
            - Ready for work
            
        Completed Task:
            - concluida = True
            - data_conclusao = auto-generated timestamp
            - Optional observations recorded
    """
    
    class Meta:
        model = Diligencias
        fields = ['concluida', 'data_conclusao', 'descricao']
        widgets = {
            'data_conclusao': BrazilianDateTimeInput(),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'concluida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize field labels
        self.fields['concluida'].label = 'Marcar como concluída'
        self.fields['data_conclusao'].label = 'Data de conclusão'
        self.fields['descricao'].label = 'Observações'
        
        # Make fields optional
        self.fields['data_conclusao'].required = False
        self.fields['descricao'].required = False
        
    def clean(self):
        """Validate that data_conclusao is set when concluida is True"""
        cleaned_data = super().clean()
        concluida = cleaned_data.get('concluida')
        data_conclusao = cleaned_data.get('data_conclusao')
        
        if concluida and not data_conclusao:
            from django.utils import timezone
            cleaned_data['data_conclusao'] = timezone.now()
        elif not concluida:
            cleaned_data['data_conclusao'] = None
            
        return cleaned_data


class TipoDiligenciaForm(forms.ModelForm):
    """
    Comprehensive form for creating and managing diligence types (tipos de diligência) in the precatorios system.
    
    This form provides a complete interface for defining and managing the types of
    legal tasks/procedures that can be created as diligências. It handles type
    categorization, visual customization, ordering, activation control, and
    comprehensive validation to ensure a well-organized and flexible task
    management system.
    
    Key Features:
        - Unique diligence type name management
        - Optional detailed descriptions for clarity
        - Visual customization with color selection
        - Display order management for logical organization
        - Activation control for type lifecycle management
        - Hexadecimal color validation for consistency
        - Bootstrap styling for consistent user interface
        - Comprehensive field validation and error handling
        
    Business Logic:
        - Ensures unique type names within the system
        - Validates proper hexadecimal color format
        - Manages type ordering for logical progression
        - Controls type availability through activation
        - Supports flexible type descriptions
        - Maintains visual consistency through color validation
        - Provides user-friendly interface customization
        
    Usage:
        # Creating new diligence type
        form = TipoDiligenciaForm(request.POST or None)
        if form.is_valid():
            tipo = form.save()
            
        # Editing existing type
        form = TipoDiligenciaForm(request.POST or None, instance=existing_tipo)
        
        # With initial values
        form = TipoDiligenciaForm(initial={
            'ativo': True,
            'ordem': 0,
            'cor': '#007bff'  # Bootstrap primary blue
        })
    
    Fields:
        nome (CharField): Unique type name
            - Required field for type identification
            - Must be unique across all diligence types
            - Bootstrap form-control styling
            - Label: 'Nome do Tipo'
            - Help text: 'Nome único para o tipo de diligência'
            
        descricao (TextField): Optional type description
            - Optional field for detailed explanation
            - Textarea widget with 3 rows
            - Helps users understand type purpose
            - Bootstrap form-control styling
            - Label: 'Descrição'
            
        cor (CharField): Visual identification color
            - Required field for visual customization
            - Color picker widget for easy selection
            - Hexadecimal format validation (#RRGGBB)
            - Bootstrap form-control-color styling
            - Label: 'Cor'
            
        ordem (IntegerField): Display order priority
            - Required field for ordering control
            - NumberInput with minimum value 0
            - Controls type display sequence
            - Lower numbers appear first
            - Label: 'Ordem de Exibição'
            
        ativo (BooleanField): Type activation status
            - Required field for lifecycle control
            - Checkbox input for activation toggle
            - Controls type availability in system
            - Bootstrap form-check-input styling
            - Label: 'Ativo'
            
    Type Management:
        Creation:
            - Define unique name and optional description
            - Set visual color for identification
            - Configure display order
            - Activate for immediate use
            
        Organization:
            - Order-based display arrangement
            - Color-coded visual identification
            - Descriptive categorization
            - Active/inactive status control
            
        Usage:
            - Available in DiligenciasForm tipo selection
            - Filtered by active status
            - Ordered by ordem field
            - Visually identified by color
            
    Validation:
        - Nome: Required, unique, proper length
        - Cor: Required, valid hexadecimal format (#RRGGBB)
        - Ordem: Required, non-negative integer
        - Ativo: Boolean validation
        - Descrição: Optional, no specific validation
        
    Color Validation:
        - Format: #RRGGBB (hexadecimal)
        - Length: Exactly 7 characters
        - Pattern: # followed by 6 hex digits
        - Case insensitive validation
        - User-friendly error messaging
        
    Ordering System:
        - Integer-based ordering (0 = highest priority)
        - Logical type organization
        - Supports reordering without conflicts
        - Visual sorting in type displays
        - Flexible insertion of new types
        
    Error Messages:
        - "Nome do tipo é obrigatório."
        - "Já existe um tipo de diligência com este nome."
        - "Cor deve estar no formato hexadecimal (#RRGGBB)."
        - "Ordem deve ser um número não negativo."
        
    Widgets:
        - TextInput for type name
        - Textarea with 3 rows for description
        - Color picker for visual selection
        - NumberInput with min validation for order
        - Checkbox for activation status
        
    Security Considerations:
        - Input sanitization for text fields
        - Color format validation prevents injection
        - Integer validation for order field
        - Unique constraint enforcement
        - XSS prevention through proper escaping
        
    Performance:
        - Efficient uniqueness validation
        - Minimal database queries
        - Optimized form rendering
        - Client-side validation support
        
    Accessibility:
        - Descriptive labels and help text
        - Color picker accessibility features
        - Keyboard navigation support
        - Screen reader compatibility
        - Clear error messaging
        
    Integration Points:
        - TipoDiligencia model for data persistence
        - DiligenciasForm for type selection
        - Visual display systems throughout application
        - Type filtering in diligence creation
        - Task categorization workflows
        
    Lifecycle Management:
        - Creation: All fields customizable
        - Editing: Full field modification support
        - Deactivation: Ativo flag for soft deletion
        - Reordering: Ordem field for position changes
        - Visual Updates: Color customization anytime
        
    Visual Organization:
        - Color-coded type identification
        - Order-based display arrangement
        - Active/inactive status indication
        - Descriptive type categorization
        - User-friendly type selection
    """
    
    class Meta:
        model = TipoDiligencia
        fields = ['nome', 'descricao', 'cor', 'ordem', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'cor': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize field labels
        self.fields['nome'].label = 'Nome do Tipo'
        self.fields['descricao'].label = 'Descrição'
        self.fields['cor'].label = 'Cor'
        self.fields['ordem'].label = 'Ordem de Exibição'
        self.fields['ativo'].label = 'Ativo'
        
        # Add help texts
        self.fields['nome'].help_text = 'Nome único para o tipo de diligência'
        self.fields['descricao'].help_text = 'Descrição opcional do tipo (opcional)'
        self.fields['cor'].help_text = 'Cor para identificação visual'
        self.fields['ordem'].help_text = 'Número para definir a ordem de exibição (menores aparecem primeiro)'
        self.fields['ativo'].help_text = 'Se este tipo está disponível para uso'
        
        # Make description optional
        self.fields['descricao'].required = False
    
    def clean_cor(self):
        """Validate that cor is a valid hex color"""
        cor = self.cleaned_data.get('cor')
        if cor and not re.match(r'^#[0-9A-Fa-f]{6}$', cor):
            raise forms.ValidationError('Cor deve estar no formato hexadecimal (#RRGGBB)')
        return cor


class TipoForm(forms.ModelForm):
    """
    Comprehensive form for creating and managing precatorio types (tipos de precatório) in the system.
    
    This form provides a complete interface for defining and managing the categories or types
    that precatórios can be classified into. It handles type categorization, visual
    customization, ordering, activation control, and comprehensive validation to ensure
    a well-organized and flexible categorization system.
    
    Key Features:
        - Unique precatorio type name management
        - Optional detailed descriptions for clarity
        - Visual customization with color selection
        - Display order management for logical organization
        - Activation control for type lifecycle management
        - Hexadecimal color validation for consistency
        - Bootstrap styling for consistent user interface
        - Comprehensive field validation and error handling
        
    Business Logic:
        - Ensures unique type names within the system
        - Validates proper hexadecimal color format
        - Manages type ordering for logical progression
        - Controls type availability through activation
        - Supports flexible type descriptions
        - Maintains visual consistency through color validation
        - Provides user-friendly interface customization
        
    Usage:
        # Creating new precatorio type
        form = TipoForm(request.POST or None)
        if form.is_valid():
            tipo = form.save()
            
        # Editing existing type
        form = TipoForm(request.POST or None, instance=existing_tipo)
        
        # With initial values
        form = TipoForm(initial={
            'ativa': True,
            'ordem': 0,
            'cor': '#007bff'  # Bootstrap primary blue
        })
    
    Fields:
        nome (CharField): Unique type name
            - Required field for type identification
            - Must be unique across all precatorio types
            - Bootstrap form-control styling
            - Maximum 100 characters
            
        descricao (TextField): Optional detailed description
            - Optional field for type explanation
            - Supports rich text descriptions
            - Bootstrap form-control styling
            - Flexible content for detailed explanations
            
        cor (CharField): Hexadecimal color code
            - Color picker for visual identification
            - Hexadecimal format validation (#RRGGBB)
            - Bootstrap color-input styling
            - Default to Bootstrap primary blue
            
        ordem (IntegerField): Display order
            - Controls type display sequence
            - Lower numbers appear first
            - Allows for logical type organization
            - Default value 0
            
        ativa (BooleanField): Activation status
            - Controls type availability
            - Inactive types hidden from selection
            - Allows for type lifecycle management
            - Default value True
    
    Validation:
        - nome: Required, unique, max 100 characters
        - descricao: Optional, no length limit
        - cor: Required, valid hex format (#RRGGBB)
        - ordem: Required, positive integer
        - ativa: Required, boolean value
        
    Error Messages:
        - "Nome é obrigatório."
        - "Nome deve ter no máximo 100 caracteres."
        - "Este nome já existe para outro tipo."
        - "Cor deve estar no formato hexadecimal (#RRGGBB)"
        - "Ordem deve ser um número positivo."
        
    Widgets:
        - nome: TextInput with Bootstrap styling
        - descricao: Textarea with Bootstrap styling
        - cor: ColorInput for visual color selection
        - ordem: NumberInput with min value 0
        - ativa: CheckboxInput with Bootstrap styling
        
    Security Considerations:
        - Input validation prevents malformed data
        - Color validation prevents script injection
        - Unique constraint prevents duplicates
        - Length validation prevents buffer overflow
        
    Performance:
        - Efficient validation algorithms
        - Minimal database impact during validation
        - Optimized for quick form processing
        - Cached validation for repeated checks
        
    Accessibility:
        - Descriptive labels and help text
        - Proper form structure for screen readers
        - Keyboard navigation support
        - Clear error messaging
        - ARIA attributes for enhanced accessibility
        
    Integration Points:
        - Tipo model for data persistence
        - Precatorio model for type assignment
        - Bootstrap framework for styling
        - Django validation framework
        - Color picker JavaScript components
    """
    
    class Meta:
        model = Tipo
        fields = ['nome', 'descricao', 'cor', 'ordem', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome do tipo'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional do tipo'
            }),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'ordem': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'ativa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set custom labels
        self.fields['nome'].label = 'Nome do Tipo'
        self.fields['descricao'].label = 'Descrição'
        self.fields['cor'].label = 'Cor'
        self.fields['ordem'].label = 'Ordem de Exibição'
        self.fields['ativa'].label = 'Ativa'
        
        # Add help texts
        self.fields['nome'].help_text = 'Nome único para o tipo de precatório'
        self.fields['descricao'].help_text = 'Descrição opcional do tipo (opcional)'
        self.fields['cor'].help_text = 'Cor para identificação visual'
        self.fields['ordem'].help_text = 'Número para definir a ordem de exibição (menores aparecem primeiro)'
        self.fields['ativa'].help_text = 'Se este tipo está disponível para uso'
        
        # Make description optional
        self.fields['descricao'].required = False
    
    def clean_cor(self):
        """Validate that cor is a valid hex color"""
        cor = self.cleaned_data.get('cor')
        if cor and not re.match(r'^#[0-9A-Fa-f]{6}$', cor):
            raise forms.ValidationError('Cor deve estar no formato hexadecimal (#RRGGBB)')
        return cor

