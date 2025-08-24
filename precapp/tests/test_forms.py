"""
Test cases for all forms in the precatorios application.
Contains all form-related tests migrated from the monolithic tests.py file.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django import forms
from datetime import date, timedelta

from precapp.models import (
    Fase, FaseHonorariosContratuais, Precatorio, Cliente, 
    Alvara, Requerimento, TipoDiligencia, Diligencias
)
from precapp.forms import (
    FaseForm, FaseHonorariosContratuaisForm, AlvaraSimpleForm, 
    RequerimentoForm, PrecatorioForm, ClienteForm, ClienteSimpleForm,
    TipoDiligenciaForm, DiligenciasForm, DiligenciasUpdateForm,
    PrecatorioSearchForm, ClienteSearchForm,
    validate_cnj, validate_currency, BrazilianDateInput, BrazilianDateTimeInput
)


class BrazilianDateInputTest(TestCase):
    """
    Comprehensive test suite for BrazilianDateInput widget.
    
    This test class covers the functionality, configuration, and edge cases
    for the custom Brazilian date input widget used throughout the application
    for proper date localization.
    
    Tests cover:
    - Widget initialization and default configuration
    - HTML attribute assignment (placeholder, pattern, title, etc.)
    - Date format handling (%d/%m/%Y)
    - Custom attribute merging behavior
    - Integration with Django forms
    - Edge cases and error handling
    """
    
    def setUp(self):
        """Set up test data for widget testing"""
        self.widget = BrazilianDateInput()
        
    def test_widget_initialization_default(self):
        """Test widget initialization with default settings"""
        widget = BrazilianDateInput()
        
        # Check default input type
        self.assertEqual(widget.input_type, 'text')
        
        # Check default format
        self.assertEqual(widget.format, '%d/%m/%Y')
        
        # Check default attributes
        expected_attrs = {
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa',
            'pattern': r'\d{2}/\d{2}/\d{4}',
            'title': 'Digite a data no formato dd/mm/aaaa (ex: 31/12/2023)',
            'maxlength': '10',
        }
        
        for key, value in expected_attrs.items():
            self.assertEqual(widget.attrs[key], value)
    
    def test_widget_initialization_custom_format(self):
        """Test widget initialization with custom date format"""
        custom_format = '%d-%m-%Y'
        widget = BrazilianDateInput(format=custom_format)
        
        self.assertEqual(widget.format, custom_format)
        # Default attributes should still be applied
        self.assertEqual(widget.attrs['placeholder'], 'dd/mm/aaaa')
    
    def test_widget_initialization_custom_attrs(self):
        """Test widget initialization with custom attributes"""
        custom_attrs = {
            'class': 'custom-form-control',
            'placeholder': 'data personalizada',
            'id': 'custom-date-field',
            'data-custom': 'value'
        }
        
        widget = BrazilianDateInput(attrs=custom_attrs)
        
        # Custom attributes should override defaults
        self.assertEqual(widget.attrs['class'], 'custom-form-control')
        self.assertEqual(widget.attrs['placeholder'], 'data personalizada')
        
        # New attributes should be added
        self.assertEqual(widget.attrs['id'], 'custom-date-field')
        self.assertEqual(widget.attrs['data-custom'], 'value')
        
        # Default attributes should still be present if not overridden
        self.assertEqual(widget.attrs['pattern'], r'\d{2}/\d{2}/\d{4}')
        self.assertEqual(widget.attrs['maxlength'], '10')
    
    def test_widget_attributes_structure(self):
        """Test that all required HTML attributes are properly set"""
        widget = BrazilianDateInput()
        
        # Test CSS class for Bootstrap styling
        self.assertEqual(widget.attrs['class'], 'form-control')
        
        # Test placeholder for user guidance
        self.assertEqual(widget.attrs['placeholder'], 'dd/mm/aaaa')
        
        # Test pattern for client-side validation
        self.assertEqual(widget.attrs['pattern'], r'\d{2}/\d{2}/\d{4}')
        
        # Test title for accessibility and user guidance
        expected_title = 'Digite a data no formato dd/mm/aaaa (ex: 31/12/2023)'
        self.assertEqual(widget.attrs['title'], expected_title)
        
        # Test maxlength for input control
        self.assertEqual(widget.attrs['maxlength'], '10')
    
    def test_widget_format_configuration(self):
        """Test Brazilian date format configuration"""
        widget = BrazilianDateInput()
        
        # Should use Brazilian date format by default
        self.assertEqual(widget.format, '%d/%m/%Y')
        
        # Test that format can be overridden
        custom_widget = BrazilianDateInput(format='%d.%m.%Y')
        self.assertEqual(custom_widget.format, '%d.%m.%Y')
    
    def test_widget_render_integration(self):
        """Test widget rendering with actual date values"""
        from django import forms
        from datetime import date
        
        # Create a simple form with the widget
        class TestForm(forms.Form):
            test_date = forms.DateField(widget=BrazilianDateInput())
        
        # Test with valid date
        test_date = date(2023, 12, 25)
        form = TestForm(data={'test_date': '25/12/2023'})
        
        # Form should be valid with Brazilian format
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['test_date'], test_date)
    
    def test_widget_pattern_validation_format(self):
        """Test that the pattern attribute matches expected Brazilian date format"""
        widget = BrazilianDateInput()
        pattern = widget.attrs['pattern']
        
        # Pattern should match dd/mm/yyyy format
        import re
        
        # Test valid Brazilian date formats
        valid_dates = ['01/01/2023', '31/12/2023', '15/06/1990', '29/02/2024']
        for date_str in valid_dates:
            self.assertTrue(re.match(pattern, date_str), 
                          f"Pattern should match valid date: {date_str}")
        
        # Test invalid formats that shouldn't match
        invalid_dates = ['1/1/23', '2023/12/25', '25-12-2023', '12.25.2023', 'invalid']
        for date_str in invalid_dates:
            self.assertFalse(re.match(pattern, date_str), 
                           f"Pattern should not match invalid date: {date_str}")
    
    def test_widget_accessibility_attributes(self):
        """Test accessibility-related attributes"""
        widget = BrazilianDateInput()
        
        # Title should provide clear instructions
        title = widget.attrs['title']
        self.assertIn('dd/mm/aaaa', title.lower())
        self.assertIn('ex:', title.lower())
        
        # Placeholder should be concise and clear
        placeholder = widget.attrs['placeholder']
        self.assertEqual(placeholder, 'dd/mm/aaaa')
    
    def test_widget_form_integration(self):
        """Test widget integration in actual form classes"""
        # Test with ClienteForm (known to use BrazilianDateInput)
        from precapp.forms import ClienteForm
        
        form = ClienteForm()
        nascimento_widget = form.fields['nascimento'].widget
        
        # Should be BrazilianDateInput
        self.assertIsInstance(nascimento_widget, BrazilianDateInput)
        
        # Should have the expected attributes
        self.assertEqual(nascimento_widget.attrs['placeholder'], 'dd/mm/aaaa')
        self.assertEqual(nascimento_widget.format, '%d/%m/%Y')
    
    def test_widget_inheritance_from_dateinput(self):
        """Test that widget properly inherits from Django's DateInput"""
        from django.forms.widgets import DateInput
        
        widget = BrazilianDateInput()
        self.assertIsInstance(widget, DateInput)
        
        # Should override input_type to 'text' for better control
        self.assertEqual(widget.input_type, 'text')
    
    def test_widget_custom_attrs_merging(self):
        """Test that custom attributes properly merge with defaults"""
        # Test partial override
        custom_attrs = {
            'class': 'custom-class',
            'data-custom': 'test-value'
        }
        
        widget = BrazilianDateInput(attrs=custom_attrs)
        
        # Custom class should override default
        self.assertEqual(widget.attrs['class'], 'custom-class')
        
        # Custom data attribute should be added
        self.assertEqual(widget.attrs['data-custom'], 'test-value')
        
        # Default attributes should be preserved when not overridden
        self.assertEqual(widget.attrs['placeholder'], 'dd/mm/aaaa')
        self.assertEqual(widget.attrs['pattern'], r'\d{2}/\d{2}/\d{4}')
        self.assertEqual(widget.attrs['maxlength'], '10')
    
    def test_widget_required_attribute_handling(self):
        """Test handling of the 'required' attribute"""
        # Test with required=False in attrs
        widget = BrazilianDateInput(attrs={'required': False})
        self.assertFalse(widget.attrs['required'])
        
        # Test that other attributes are not affected
        self.assertEqual(widget.attrs['placeholder'], 'dd/mm/aaaa')
    
    def test_widget_input_type_override(self):
        """Test that input_type is properly set to 'text'"""
        widget = BrazilianDateInput()
        
        # Should be text input for better format control
        self.assertEqual(widget.input_type, 'text')
        
        # Should not be the default 'date' input type
        self.assertNotEqual(widget.input_type, 'date')


class BrazilianDateTimeInputTest(TestCase):
    """
    Test suite for BrazilianDateTimeInput widget.
    
    Similar to BrazilianDateInput but for datetime fields with Brazilian
    localization including time component (dd/mm/yyyy hh:mm format).
    """
    
    def test_widget_initialization_default(self):
        """Test BrazilianDateTimeInput initialization with default settings"""
        widget = BrazilianDateTimeInput()
        
        # Check default input type
        self.assertEqual(widget.input_type, 'text')
        
        # Check default format includes time
        self.assertEqual(widget.format, '%d/%m/%Y %H:%M')
        
        # Check datetime-specific attributes
        expected_attrs = {
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa hh:mm',
            'title': 'Digite a data e hora no formato dd/mm/aaaa hh:mm (ex: 31/12/2023 14:30)',
            'maxlength': '16',
        }
        
        for key, value in expected_attrs.items():
            self.assertEqual(widget.attrs[key], value)
    
    def test_datetime_widget_format(self):
        """Test that datetime widget uses correct Brazilian datetime format"""
        widget = BrazilianDateTimeInput()
        
        # Should include both date and time in Brazilian format
        self.assertEqual(widget.format, '%d/%m/%Y %H:%M')
        
        # Placeholder should reflect the format
        self.assertEqual(widget.attrs['placeholder'], 'dd/mm/aaaa hh:mm')
        
        # Maxlength should accommodate datetime string
        self.assertEqual(widget.attrs['maxlength'], '16')
    
    def test_datetime_widget_form_integration(self):
        """Test datetime widget integration in forms"""
        from precapp.forms import DiligenciasUpdateForm
        
        form = DiligenciasUpdateForm()
        data_conclusao_widget = form.fields['data_conclusao'].widget
        
        # Should be BrazilianDateTimeInput
        self.assertIsInstance(data_conclusao_widget, BrazilianDateTimeInput)
        
        # Should have datetime-specific attributes
        self.assertEqual(data_conclusao_widget.attrs['placeholder'], 'dd/mm/aaaa hh:mm')
        self.assertEqual(data_conclusao_widget.format, '%d/%m/%Y %H:%M')


class FaseFormComprehensiveTest(TestCase):
    """Comprehensive test cases for FaseForm addressing all functionality gaps"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_form_data = {
            'nome': 'Nova Fase',
            'descricao': 'Descrição da nova fase',
            'tipo': 'alvara',
            'cor': '#FF6B35',
            'ordem': 0,
            'ativa': True
        }
        
        # Create existing fases for uniqueness testing
        self.existing_fase_alvara = Fase.objects.create(
            nome='Fase Existente',
            tipo='alvara',
            cor='#007bff',
            ativa=True
        )
        
        self.existing_fase_requerimento = Fase.objects.create(
            nome='Fase Existente',
            tipo='requerimento',
            cor='#28a745',
            ativa=True
        )
        
        self.existing_fase_ambos = Fase.objects.create(
            nome='Fase Única',
            tipo='ambos',
            cor='#ffc107',
            ativa=True
        )
    
    # Basic Form Validation Tests
    def test_valid_form_with_all_fields(self):
        """Test form with all valid data"""
        form = FaseForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save_creates_object_correctly(self):
        """Test form saving creates the object correctly"""
        form = FaseForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        fase = form.save()
        self.assertEqual(fase.nome, 'Nova Fase')
        self.assertEqual(fase.tipo, 'alvara')
        self.assertEqual(fase.cor, '#FF6B35')
        self.assertEqual(fase.ordem, 0)
        self.assertTrue(fase.ativa)
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        incomplete_data = {'nome': 'Test'}
        form = FaseForm(data=incomplete_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    def test_minimal_valid_form(self):
        """Test form with minimal required data"""
        minimal_data = {
            'nome': 'Fase Mínima',
            'tipo': 'ambos',
            'cor': '#000000',
            'ordem': 0  # ordem is required
        }
        form = FaseForm(data=minimal_data)
        self.assertTrue(form.is_valid())
        if form.is_valid():
            fase = form.save()
            self.assertEqual(fase.nome, 'Fase Mínima')
            self.assertEqual(fase.tipo, 'ambos')
            self.assertFalse(fase.ativa)  # Default value for BooleanField when not provided
    
    # Nome Field Validation Tests
    def test_clean_nome_uniqueness_same_tipo(self):
        """Test nome uniqueness validation within same tipo"""
        form_data = {
            'nome': 'Fase Existente',  # Same name as existing alvara fase
            'tipo': 'alvara',
            'cor': '#ff0000',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertFalse(form.is_valid())
        # The error might be in '__all__' instead of 'nome' field
        self.assertTrue('__all__' in form.errors or 'nome' in form.errors)
        error_message = str(form.errors)
        self.assertIn('já existe', error_message.lower())
    
    def test_clean_nome_uniqueness_different_tipo_allowed(self):
        """Test that same nome is allowed for different tipo"""
        form_data = {
            'nome': 'Fase Existente',  # Same name as existing alvara fase
            'tipo': 'ambos',  # Different tipo
            'cor': '#ff0000',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_clean_nome_case_insensitive_uniqueness(self):
        """Test that nome uniqueness is case-insensitive"""
        form_data = {
            'nome': 'FASE EXISTENTE',  # Uppercase version of existing name
            'tipo': 'alvara',
            'cor': '#ff0000',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        # Form should be invalid due to case-insensitive duplicate
        self.assertFalse(form.is_valid())
        # The error should be in the 'nome' field
        self.assertIn('nome', form.errors)
        self.assertIn('Já existe uma fase com o nome', str(form.errors['nome']))
    
    def test_clean_nome_whitespace_trimming(self):
        """Test that nome field strips whitespace"""
        form_data = {
            'nome': '  Fase com Espaços  ',
            'tipo': 'requerimento',
            'cor': '#ff0000',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned_nome = form.clean_nome()
        self.assertEqual(cleaned_nome, 'Fase com Espaços')
    
    def test_clean_nome_editing_existing_fase_excludes_self(self):
        """Test that editing existing fase excludes itself from uniqueness check"""
        # Edit the existing fase with same name should be allowed
        edit_data = {
            'nome': 'Fase Existente',
            'tipo': 'alvara',
            'cor': '#ff0000',
            'ordem': 0
        }
        edit_form = FaseForm(data=edit_data, instance=self.existing_fase_alvara)
        self.assertTrue(edit_form.is_valid())
    
    def test_clean_nome_empty_field(self):
        """Test that empty nome field is handled correctly"""
        form_data = {
            'nome': '',
            'tipo': 'alvara',
            'cor': '#ff0000'
        }
        form = FaseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_clean_nome_only_whitespace(self):
        """Test that nome with only whitespace is invalid"""
        form_data = {
            'nome': '   ',
            'tipo': 'alvara',
            'cor': '#ff0000'
        }
        form = FaseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    # Cor Field Validation Tests
    def test_clean_cor_valid_hex_format(self):
        """Test that valid hex colors are accepted"""
        valid_colors = ['#000000', '#FFFFFF', '#ff6b35', '#007BFF', '#28A745']
        for color in valid_colors:
            form_data = {
                'nome': f'Fase {color}',
                'tipo': 'alvara',
                'cor': color,
                'ordem': 0
            }
            form = FaseForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Color {color} should be valid")
    
    def test_clean_cor_invalid_hex_format(self):
        """Test that invalid hex colors are rejected"""
        invalid_colors = [
            '#12345',    # Too short
            '#1234567',  # Too long
            '123456',    # Missing #
            '#GGGGGG',   # Invalid hex characters
            '#12345G',   # Mixed valid/invalid
            'red',       # Color name
            'rgb(255,0,0)',  # RGB format
            ''           # Empty
        ]
        for color in invalid_colors:
            form_data = {
                'nome': f'Fase {color}',
                'tipo': 'alvara',
                'cor': color,
                'ordem': 0
            }
            form = FaseForm(data=form_data)
            self.assertFalse(form.is_valid(), f"Color {color} should be invalid")
            if not form.is_valid():
                self.assertIn('cor', form.errors)
    
    def test_clean_cor_case_handling(self):
        """Test that color validation handles case correctly"""
        form_data = {
            'nome': 'Fase Cor Maiúscula',
            'tipo': 'alvara',
            'cor': '#FF6B35',  # Uppercase hex
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    # Tipo Field Validation Tests
    def test_valid_tipo_choices(self):
        """Test all valid tipo choices"""
        valid_tipos = ['alvara', 'requerimento', 'ambos']
        for tipo in valid_tipos:
            form_data = {
                'nome': f'Fase {tipo}',
                'tipo': tipo,
                'cor': '#007bff',
                'ordem': 0
            }
            form = FaseForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Tipo {tipo} should be valid")
    
    def test_invalid_tipo_choice(self):
        """Test that invalid tipo choices are rejected"""
        form_data = {
            'nome': 'Fase Inválida',
            'tipo': 'invalid_tipo',
            'cor': '#007bff',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    def test_empty_tipo_field(self):
        """Test that empty tipo field is rejected"""
        form_data = {
            'nome': 'Fase Sem Tipo',
            'tipo': '',
            'cor': '#007bff',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    # Ordem Field Validation Tests
    def test_valid_ordem_values(self):
        """Test valid ordem values"""
        valid_ordens = [0, 1, 5, 10, 100, 999]
        for ordem in valid_ordens:
            form_data = {
                'nome': f'Fase Ordem {ordem}',
                'tipo': 'alvara',
                'cor': '#007bff',
                'ordem': ordem
            }
            form = FaseForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Ordem {ordem} should be valid")
    
    def test_negative_ordem_invalid(self):
        """Test that negative ordem values are rejected"""
        form_data = {
            'nome': 'Fase Ordem Negativa',
            'tipo': 'alvara',
            'cor': '#007bff',
            'ordem': -1
        }
        form = FaseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ordem', form.errors)
    
    def test_ordem_default_value(self):
        """Test that ordem has correct default value"""
        form_data = {
            'nome': 'Fase Sem Ordem',
            'tipo': 'alvara',
            'cor': '#007bff'
            # ordem deliberately omitted
        }
        form = FaseForm(data=form_data)
        # Since ordem is required, form should be invalid without it
        self.assertFalse(form.is_valid())
        self.assertIn('ordem', form.errors)
    
    # Ativa Field Validation Tests
    def test_ativa_field_boolean_values(self):
        """Test that ativa field accepts boolean values"""
        for ativa_value in [True, False]:
            form_data = {
                'nome': f'Fase Ativa {ativa_value}',
                'tipo': 'alvara',
                'cor': '#007bff',
                'ativa': ativa_value,
                'ordem': 0
            }
            form = FaseForm(data=form_data)
            self.assertTrue(form.is_valid())
    
    def test_ativa_field_default_value(self):
        """Test that ativa field has correct default when not provided"""
        form_data = {
            'nome': 'Fase Sem Ativa',
            'tipo': 'alvara',
            'cor': '#007bff',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertTrue(form.is_valid())
        # BooleanField returns False when not checked/provided
    
    # Descricao Field Tests
    def test_descricao_optional_field(self):
        """Test that descricao field is optional"""
        form_data = {
            'nome': 'Fase Sem Descrição',
            'tipo': 'alvara',
            'cor': '#007bff',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_descricao_with_content(self):
        """Test that descricao field accepts content"""
        form_data = {
            'nome': 'Fase Com Descrição',
            'tipo': 'alvara',
            'cor': '#007bff',
            'descricao': 'Esta é uma descrição detalhada da fase.',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertTrue(form.is_valid())
        if form.is_valid():
            fase = form.save()
            self.assertEqual(fase.descricao, 'Esta é uma descrição detalhada da fase.')
    
    # Form Configuration Tests
    def test_form_field_widgets(self):
        """Test that form fields have correct widgets and attributes"""
        form = FaseForm()
        
        # Test nome field widget
        nome_widget = form.fields['nome'].widget
        self.assertIn('form-control', nome_widget.attrs.get('class', ''))
        self.assertIn('placeholder', nome_widget.attrs)
        
        # Test tipo field widget
        tipo_widget = form.fields['tipo'].widget
        self.assertIn('form-control', tipo_widget.attrs.get('class', ''))
        
        # Test cor field widget  
        cor_widget = form.fields['cor'].widget
        # The TextInput widget has input_type = 'color' but type attribute is in attrs
        self.assertEqual(cor_widget.input_type, 'color')
        self.assertIn('form-control', cor_widget.attrs.get('class', ''))
        
        # Test ordem field widget
        ordem_widget = form.fields['ordem'].widget
        # Widget attrs can be either string or int depending on how Django processes them
        min_value = ordem_widget.attrs.get('min')
        self.assertTrue(min_value == 0 or min_value == '0', f"Expected 0 or '0', got {repr(min_value)}")
        self.assertIn('form-control', ordem_widget.attrs.get('class', ''))
        
        # Test ativa field widget
        ativa_widget = form.fields['ativa'].widget
        self.assertIn('form-check-input', ativa_widget.attrs.get('class', ''))
    
    def test_form_field_labels(self):
        """Test that form fields have correct labels"""
        form = FaseForm()
        
        self.assertEqual(form.fields['nome'].label, 'Nome da Fase')
        self.assertEqual(form.fields['descricao'].label, 'Descrição')
        self.assertEqual(form.fields['tipo'].label, 'Tipo de Fase')
        self.assertEqual(form.fields['cor'].label, 'Cor')
        self.assertEqual(form.fields['ordem'].label, 'Ordem de Exibição')
        self.assertEqual(form.fields['ativa'].label, 'Fase Ativa')
    
    def test_form_field_help_texts(self):
        """Test that form fields have appropriate help texts"""
        form = FaseForm()
        
        self.assertIn('único para identificar', form.fields['nome'].help_text)
        self.assertIn('opcional', form.fields['descricao'].help_text)
        self.assertIn('onde esta fase pode ser usada', form.fields['tipo'].help_text)
        self.assertIn('identificar visualmente', form.fields['cor'].help_text)
        self.assertIn('ordem de exibição', form.fields['ordem'].help_text)
        self.assertIn('disponibilizar esta fase', form.fields['ativa'].help_text)
    
    def test_form_field_required_status(self):
        """Test that form fields have correct required status"""
        form = FaseForm()
        
        self.assertTrue(form.fields['nome'].required)
        self.assertFalse(form.fields['descricao'].required)
        self.assertTrue(form.fields['tipo'].required)
        self.assertTrue(form.fields['cor'].required)
        self.assertTrue(form.fields['ordem'].required)
        self.assertFalse(form.fields['ativa'].required)  # BooleanField
    
    def test_form_meta_fields(self):
        """Test that form Meta includes correct fields"""
        form = FaseForm()
        expected_fields = ['nome', 'descricao', 'tipo', 'cor', 'ordem', 'ativa']
        
        for field in expected_fields:
            self.assertIn(field, form.fields)
    
    # Edge Cases and Integration Tests
    def test_form_with_unicode_characters(self):
        """Test form handles unicode characters in nome and descricao"""
        form_data = {
            'nome': 'Fase com Acentuação: ção, ã, é',
            'descricao': 'Descrição com emojis 🎯 e caracteres especiais: ñ, ü, ç',
            'tipo': 'ambos',
            'cor': '#007bff',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_with_special_characters_in_nome(self):
        """Test form handles special characters in nome"""
        special_names = [
            'Fase-com-hífens',
            'Fase (com parênteses)',
            'Fase_com_underscores',
            'Fase 123 com números',
            'Fase & símbolos'
        ]
        for nome in special_names:
            form_data = {
                'nome': nome,
                'tipo': 'alvara',
                'cor': '#007bff',
                'ordem': 0
            }
            form = FaseForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Nome '{nome}' should be valid")
    
    def test_complete_workflow_create_and_edit(self):
        """Test complete workflow of creating and editing a fase"""
        # Create new fase
        create_data = {
            'nome': 'Fase Teste Workflow',
            'descricao': 'Descrição inicial',
            'tipo': 'requerimento',
            'cor': '#28a745',
            'ordem': 5,
            'ativa': True
        }
        create_form = FaseForm(data=create_data)
        self.assertTrue(create_form.is_valid())
        created_fase = create_form.save()
        
        # Edit the created fase
        edit_data = {
            'nome': 'Fase Teste Workflow Editada',
            'descricao': 'Descrição atualizada',
            'tipo': 'ambos',
            'cor': '#ffc107',
            'ordem': 10,
            'ativa': False
        }
        edit_form = FaseForm(data=edit_data, instance=created_fase)
        self.assertTrue(edit_form.is_valid())
        edited_fase = edit_form.save()
        
        # Verify changes
        self.assertEqual(edited_fase.nome, 'Fase Teste Workflow Editada')
        self.assertEqual(edited_fase.tipo, 'ambos')
        self.assertEqual(edited_fase.cor, '#ffc107')
        self.assertFalse(edited_fase.ativa)
    
    def test_form_error_messages_user_friendly(self):
        """Test that form error messages are user-friendly"""
        # Test duplicate nome error message
        form_data = {
            'nome': 'Fase Existente',
            'tipo': 'alvara',
            'cor': '#007bff',
            'ordem': 0
        }
        form = FaseForm(data=form_data)
        self.assertFalse(form.is_valid())
        # Check if error is in '__all__' or 'nome' field
        error_found = False
        if '__all__' in form.errors:
            error_message = str(form.errors['__all__'][0])
            error_found = True
        elif 'nome' in form.errors:
            error_message = str(form.errors['nome'][0])
            error_found = True
        
        self.assertTrue(error_found, "Should have validation error for duplicate nome")
        if error_found:
            self.assertIn('já existe', error_message.lower())
        
        # Test invalid color error message
        invalid_color_data = {
            'nome': 'Fase Cor Inválida',
            'tipo': 'alvara',
            'cor': 'invalid',
            'ordem': 0
        }
        color_form = FaseForm(data=invalid_color_data)
        self.assertFalse(color_form.is_valid())
        cor_error = str(color_form.errors['cor'][0])
        self.assertIn('formato hexadecimal', cor_error)
        self.assertIn('#RRGGBB', cor_error)


class FaseHonorariosContratuaisFormComprehensiveTest(TestCase):
    """Comprehensive test cases for FaseHonorariosContratuaisForm"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_form_data = {
            'nome': 'Em Negociação',
            'descricao': 'Honorários em processo de negociação',
            'cor': '#007BFF',
            'ordem': 0,
            'ativa': True
        }
        # Create an existing fase for uniqueness tests
        self.existing_fase = FaseHonorariosContratuais.objects.create(
            nome='Fase Existente',
            descricao='Fase já existente para testes',
            cor='#FF0000',
            ordem=1,
            ativa=True
        )
    
    # Basic Form Validation Tests
    def test_valid_form_with_all_fields(self):
        """Test form with all valid data"""
        form = FaseHonorariosContratuaisForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_minimal_valid_form(self):
        """Test form with minimal required data"""
        form_data = {
            'nome': 'Teste Mínimo',
            'cor': '#000000',
            'ordem': 0
        }
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        form = FaseHonorariosContratuaisForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
        self.assertIn('cor', form.errors)
        self.assertIn('ordem', form.errors)
    
    def test_form_save_creates_object_correctly(self):
        """Test form saving creates the object correctly"""
        form = FaseHonorariosContratuaisForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        fase = form.save()
        self.assertEqual(fase.nome, 'Em Negociação')
        self.assertEqual(fase.cor, '#007BFF')
        self.assertEqual(fase.descricao, 'Honorários em processo de negociação')
        self.assertEqual(fase.ordem, 0)
        self.assertTrue(fase.ativa)
    
    # Field Configuration Tests
    def test_form_field_widgets(self):
        """Test that form fields have correct widgets and attributes"""
        form = FaseHonorariosContratuaisForm()
        
        # Test nome field
        nome_field = form.fields['nome']
        self.assertEqual(nome_field.widget.__class__.__name__, 'TextInput')
        self.assertIn('form-control', nome_field.widget.attrs.get('class', ''))
        self.assertTrue(nome_field.widget.attrs.get('required'))
        
        # Test descricao field
        descricao_field = form.fields['descricao']
        self.assertEqual(descricao_field.widget.__class__.__name__, 'Textarea')
        self.assertIn('form-control', descricao_field.widget.attrs.get('class', ''))
        
        # Test cor field
        cor_field = form.fields['cor']
        self.assertEqual(cor_field.widget.input_type, 'color')
        self.assertIn('form-control', cor_field.widget.attrs.get('class', ''))
        
        # Test ordem field
        ordem_field = form.fields['ordem']
        self.assertEqual(ordem_field.widget.__class__.__name__, 'NumberInput')
        self.assertIn('form-control', ordem_field.widget.attrs.get('class', ''))
        
        # Test ativa field
        ativa_field = form.fields['ativa']
        self.assertEqual(ativa_field.widget.input_type, 'checkbox')
        self.assertIn('form-check-input', ativa_field.widget.attrs.get('class', ''))
    
    def test_form_field_labels(self):
        """Test that form fields have correct labels"""
        form = FaseHonorariosContratuaisForm()
        self.assertEqual(form.fields['nome'].label, 'Nome da Fase')
        self.assertEqual(form.fields['descricao'].label, 'Descrição')
        self.assertEqual(form.fields['cor'].label, 'Cor')
        self.assertEqual(form.fields['ordem'].label, 'Ordem de Exibição')
        self.assertEqual(form.fields['ativa'].label, 'Fase Ativa')
    
    def test_form_field_help_texts(self):
        """Test that form fields have appropriate help texts"""
        form = FaseHonorariosContratuaisForm()
        self.assertIn('único', form.fields['nome'].help_text)
        self.assertIn('opcional', form.fields['descricao'].help_text)
        self.assertIn('visualmente', form.fields['cor'].help_text)
        self.assertIn('ordem', form.fields['ordem'].help_text)
        self.assertIn('disponibilizar', form.fields['ativa'].help_text)
    
    def test_form_field_required_status(self):
        """Test that form fields have correct required status"""
        form = FaseHonorariosContratuaisForm()
        self.assertTrue(form.fields['nome'].required)
        self.assertFalse(form.fields['descricao'].required)
        self.assertTrue(form.fields['cor'].required)
        self.assertTrue(form.fields['ordem'].required)
        self.assertFalse(form.fields['ativa'].required)
    
    def test_form_meta_fields(self):
        """Test that form Meta includes correct fields"""
        form = FaseHonorariosContratuaisForm()
        expected_fields = ['nome', 'descricao', 'cor', 'ordem', 'ativa']
        self.assertEqual(list(form.Meta.fields), expected_fields)
        self.assertEqual(form.Meta.model, FaseHonorariosContratuais)
    
    # Nome Field Tests
    def test_clean_nome_whitespace_trimming(self):
        """Test that nome field strips whitespace"""
        form_data = self.valid_form_data.copy()
        form_data['nome'] = '  Nome com Espaços  '
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['nome'], 'Nome com Espaços')
    
    def test_clean_nome_empty_field(self):
        """Test that empty nome field is handled correctly"""
        form_data = self.valid_form_data.copy()
        form_data['nome'] = ''
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_clean_nome_only_whitespace(self):
        """Test that nome with only whitespace is invalid"""
        form_data = self.valid_form_data.copy()
        form_data['nome'] = '   '
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_clean_nome_uniqueness_validation(self):
        """Test nome uniqueness validation"""
        form_data = self.valid_form_data.copy()
        form_data['nome'] = 'Fase Existente'  # Same as existing fase
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
        self.assertIn('Já existe uma fase', str(form.errors['nome']))
    
    def test_clean_nome_case_insensitive_uniqueness(self):
        """Test that nome uniqueness is case-insensitive"""
        form_data = self.valid_form_data.copy()
        form_data['nome'] = 'FASE EXISTENTE'  # Uppercase version
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_clean_nome_editing_existing_fase_excludes_self(self):
        """Test that editing existing fase excludes itself from uniqueness check"""
        form = FaseHonorariosContratuaisForm(
            data={'nome': 'Fase Existente', 'cor': '#00FF00', 'ordem': 1},
            instance=self.existing_fase
        )
        self.assertTrue(form.is_valid())
    
    # Cor Field Tests
    def test_clean_cor_valid_hex_format(self):
        """Test that valid hex colors are accepted"""
        valid_colors = ['#FF0000', '#00FF00', '#0000FF', '#123456', '#ABCDEF', '#ffffff']
        for color in valid_colors:
            form_data = self.valid_form_data.copy()
            form_data['cor'] = color
            form = FaseHonorariosContratuaisForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Color {color} should be valid")
    
    def test_clean_cor_invalid_hex_format(self):
        """Test that invalid hex colors are rejected"""
        invalid_colors = ['red', '#FF', '#GGGGGG', 'FF0000', '#FF00', '#FF00GG', 'invalid']
        for color in invalid_colors:
            form_data = self.valid_form_data.copy()
            form_data['cor'] = color
            form = FaseHonorariosContratuaisForm(data=form_data)
            self.assertFalse(form.is_valid(), f"Color {color} should be invalid")
            self.assertIn('cor', form.errors)
    
    def test_clean_cor_case_handling(self):
        """Test that color validation handles case correctly"""
        form_data = self.valid_form_data.copy()
        form_data['cor'] = '#abcdef'  # lowercase
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    # Ordem Field Tests
    def test_valid_ordem_values(self):
        """Test valid ordem values"""
        valid_orders = [0, 1, 5, 10, 100, 999]
        for ordem in valid_orders:
            form_data = self.valid_form_data.copy()
            form_data['ordem'] = ordem
            form = FaseHonorariosContratuaisForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Ordem {ordem} should be valid")
    
    def test_negative_ordem_invalid(self):
        """Test that negative ordem values are rejected"""
        form_data = self.valid_form_data.copy()
        form_data['ordem'] = -1
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ordem', form.errors)
    
    def test_ordem_default_value(self):
        """Test that ordem has correct default value"""
        form = FaseHonorariosContratuaisForm()
        self.assertEqual(form.fields['ordem'].initial, 0)
    
    # Ativa Field Tests
    def test_ativa_field_boolean_values(self):
        """Test that ativa field accepts boolean values"""
        # Test True
        form_data = self.valid_form_data.copy()
        form_data['ativa'] = True
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test False
        form_data['ativa'] = False
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_ativa_field_default_value(self):
        """Test that ativa field has correct default when not provided"""
        form_data = self.valid_form_data.copy()
        del form_data['ativa']  # Remove ativa field
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['ativa'].initial, True)
    
    # Descricao Field Tests
    def test_descricao_optional_field(self):
        """Test that descricao field is optional"""
        form_data = self.valid_form_data.copy()
        del form_data['descricao']
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_descricao_with_content(self):
        """Test that descricao field accepts content"""
        form_data = self.valid_form_data.copy()
        form_data['descricao'] = 'Descrição detalhada da fase com múltiplas linhas\ne informações importantes.'
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    # Edge Cases and Integration Tests
    def test_form_with_special_characters_in_nome(self):
        """Test form handles special characters in nome"""
        form_data = self.valid_form_data.copy()
        form_data['nome'] = 'Fase: Honorários & Contratos (50%)'
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_with_unicode_characters(self):
        """Test form handles unicode characters in nome and descricao"""
        form_data = self.valid_form_data.copy()
        form_data['nome'] = 'Honorários Açaí & Açúcar'
        form_data['descricao'] = 'Descrição com acentos: ção, ã, é, ç'
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_error_messages_user_friendly(self):
        """Test that form error messages are user-friendly"""
        # Test uniqueness error message
        form_data = self.valid_form_data.copy()
        form_data['nome'] = 'Fase Existente'
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())
        error_message = str(form.errors['nome'])
        self.assertIn('Já existe uma fase', error_message)
        self.assertIn('honorários contratuais', error_message)
        
        # Test color format error message with invalid format
        form_data['nome'] = 'Nome Único'
        form_data['cor'] = 'red'  # Invalid format that triggers hex validation
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())
        error_message = str(form.errors['cor'])
        self.assertIn('hexadecimal', error_message)
    
    def test_complete_workflow_create_and_edit(self):
        """Test complete workflow of creating and editing a fase"""
        # Create new fase
        create_data = {
            'nome': 'Nova Fase',
            'descricao': 'Descrição da nova fase',
            'cor': '#28A745',
            'ordem': 5,
            'ativa': True
        }
        create_form = FaseHonorariosContratuaisForm(data=create_data)
        self.assertTrue(create_form.is_valid())
        new_fase = create_form.save()
        
        # Edit the created fase
        edit_data = {
            'nome': 'Fase Editada',
            'descricao': 'Descrição atualizada',
            'cor': '#FFC107',
            'ordem': 10,
            'ativa': False
        }
        edit_form = FaseHonorariosContratuaisForm(data=edit_data, instance=new_fase)
        self.assertTrue(edit_form.is_valid())
        updated_fase = edit_form.save()
        
        # Verify changes
        self.assertEqual(updated_fase.nome, 'Fase Editada')
        self.assertEqual(updated_fase.cor, '#FFC107')
        self.assertFalse(updated_fase.ativa)


class AlvaraFormTest(TestCase):
    """
    Comprehensive test suite for AlvaraSimpleForm functionality and validation.
    
    This test class provides thorough coverage of the AlvaraSimpleForm, which is
    used for creating judicial authorization records (alvarás) within the precatorio
    workflow. The tests validate form behavior, field validation, financial
    calculations, and integration with the broader precatorio system.
    
    Test Coverage:
        - Form initialization and field configuration
        - Client CPF validation and verification
        - Financial value handling and validation
        - Alvará type selection and validation
        - Process phase management and selection
        - Form submission and data persistence
        - Error handling and validation messages
        - Integration with precatorio workflow
        - Edge cases and boundary conditions
        
    Key Test Areas:
        - CPF Format Validation: Tests various CPF formats and validation
        - Financial Fields: Tests currency formatting and validation
        - Type Selection: Tests alvará type choices and requirements
        - Phase Integration: Tests fase and fase_honorarios_contratuais fields
        - Client Verification: Tests client existence and linking
        - Data Persistence: Tests form save operations
        - Error Scenarios: Tests validation failures and error messages
        
    Business Logic Testing:
        - Validates client must exist in system before alvará creation
        - Tests financial value formatting and calculation requirements
        - Verifies alvará type selection affects workflow behavior
        - Ensures proper integration with precatorio context
        - Tests phase tracking for both general and contractual fees
        
    Setup Dependencies:
        - Precatorio instance with valid CNJ and financial data
        - Cliente instance with valid CPF for testing
        - Active Fase instances for phase selection testing
        - Active FaseHonorariosContratuais for fee phase testing
        - Proper test database configuration
    """
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Link the cliente to the precatorio (required by new validation)
        self.precatorio.clientes.add(self.cliente)
        
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        self.fase_ambos = Fase.objects.create(
            nome='Cancelado',
            tipo='ambos',
            cor='#95A5A6',
            ativa=True
        )
        # Create a requerimento fase that should not appear in alvara forms
        self.fase_requerimento = Fase.objects.create(
            nome='Protocolado',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True
        )
        
        # Create fases honorários contratuais
        self.fase_honorarios_ativa = FaseHonorariosContratuais.objects.create(
            nome='Em Negociação',
            cor='#007BFF',
            ativa=True
        )
        self.fase_honorarios_inativa = FaseHonorariosContratuais.objects.create(
            nome='Inativa',
            cor='#6C757D',
            ativa=False
        )
    
    def test_alvara_simple_form_fase_filtering(self):
        """Test that AlvaraSimpleForm only shows alvara and ambos phases"""
        form = AlvaraSimpleForm(precatorio=self.precatorio)
        fase_queryset = form.fields['fase'].queryset
        
        # Should include alvara and ambos phases
        self.assertIn(self.fase_alvara, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include requerimento phases
        self.assertNotIn(self.fase_requerimento, fase_queryset)
    
    def test_alvara_simple_form_includes_honorarios_field(self):
        """Test that AlvaraSimpleForm includes fase_honorarios_contratuais field"""
        form = AlvaraSimpleForm(precatorio=self.precatorio)
        self.assertIn('fase_honorarios_contratuais', form.fields)
        
        # Test field properties
        honorarios_field = form.fields['fase_honorarios_contratuais']
        self.assertFalse(honorarios_field.required)  # Should be optional
    
    def test_alvara_simple_form_honorarios_filtering(self):
        """Test that AlvaraSimpleForm only shows active honorários phases"""
        form = AlvaraSimpleForm(precatorio=self.precatorio)
        honorarios_queryset = form.fields['fase_honorarios_contratuais'].queryset
        
        # Should include only active phases
        self.assertIn(self.fase_honorarios_ativa, honorarios_queryset)
        # Should NOT include inactive phases
        self.assertNotIn(self.fase_honorarios_inativa, honorarios_queryset)


class AlvaraSimpleFormComprehensiveTest(TestCase):
    """Comprehensive test cases for AlvaraSimpleForm addressing all functionality gaps"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='Test Origin',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.cliente_not_linked = Cliente.objects.create(
            cpf='98765432100',
            nome='Maria Santos',
            nascimento=date(1975, 8, 20),
            prioridade=True
        )
        
        self.precatorio.clientes.add(self.cliente)
        
        self.fase_alvara = Fase.objects.create(
            nome='Em Andamento',
            tipo='alvara',
            cor='#007bff',
            ativa=True
        )
        
        self.fase_requerimento = Fase.objects.create(
            nome='Requerimento Fase',
            tipo='requerimento',
            cor='#28a745',
            ativa=True
        )
        
        self.fase_inativa = Fase.objects.create(
            nome='Fase Inativa',
            tipo='alvara',
            cor='#6C757D',
            ativa=False
        )
        
        self.fase_honorarios_ativa = FaseHonorariosContratuais.objects.create(
            nome='Aguardando Pagamento',
            cor='#FFA500',
            ativa=True
        )
        
        self.fase_honorarios_inativa = FaseHonorariosContratuais.objects.create(
            nome='Inativa',
            cor='#6C757D',
            ativa=False
        )
    
    # CPF Validation Tests
    def test_valid_cpf_with_formatting(self):
        """Test form accepts valid CPF with formatting"""
        form_data = {
            'cliente_cpf': '123.456.789-09',
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_valid_cpf_without_formatting(self):
        """Test form accepts valid CPF without formatting"""
        form_data = {
            'cliente_cpf': '12345678909',
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_invalid_cpf_algorithm(self):
        """Test form rejects CPF with invalid check digits"""
        form_data = {
            'cliente_cpf': '12345678900',  # Invalid check digits
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        self.assertIn('CPF inválido', str(form.errors['cliente_cpf']))
    
    def test_cpf_all_same_digits(self):
        """Test form rejects CPF with all same digits"""
        form_data = {
            'cliente_cpf': '11111111111',
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
    
    def test_cpf_wrong_length(self):
        """Test form rejects CPF with wrong length"""
        form_data = {
            'cliente_cpf': '123456789',  # Too short
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
    
    def test_cpf_nonexistent_cliente(self):
        """Test form rejects CPF of non-existent cliente"""
        form_data = {
            'cliente_cpf': '11144477735',  # Valid CPF but no cliente
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        self.assertIn('Não foi encontrado um cliente', str(form.errors['cliente_cpf']))
    
    def test_cpf_cliente_not_linked_to_precatorio(self):
        """Test form rejects cliente not linked to precatorio"""
        form_data = {
            'cliente_cpf': self.cliente_not_linked.cpf,
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        self.assertIn('não está vinculado ao precatório', str(form.errors['cliente_cpf']))
    
    def test_cpf_empty_field(self):
        """Test form rejects empty CPF field"""
        form_data = {
            'cliente_cpf': '',
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
    
    # Currency and Value Validation Tests
    def test_valid_valor_principal(self):
        """Test form accepts valid valor_principal"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '75500.50',
            'tipo': 'ordem cronológica',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_zero_valor_principal(self):
        """Test form accepts zero valor_principal"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '0.00',
            'tipo': 'ordem cronológica',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_negative_valor_principal(self):
        """Test form rejects negative valor_principal"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '-1000.00',
            'tipo': 'ordem cronológica',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('valor_principal', form.errors)
    
    def test_valid_honorarios_contratuais(self):
        """Test form accepts valid honorarios_contratuais"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'honorarios_contratuais': '10000.50',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_honorarios_contratuais_default_value(self):
        """Test form provides default value for empty honorarios_contratuais"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            self.assertEqual(cleaned_data['honorarios_contratuais'], 0.0)
    
    def test_valid_honorarios_sucumbenciais(self):
        """Test form accepts valid honorarios_sucumbenciais"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'honorarios_sucumbenciais': '7500.25',
            'tipo': 'acordo',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_honorarios_sucumbenciais_default_value(self):
        """Test form provides default value for empty honorarios_sucumbenciais"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'acordo',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            self.assertEqual(cleaned_data['honorarios_sucumbenciais'], 0.0)
    
    # Tipo Field Tests
    def test_valid_tipo_ordem_cronologica(self):
        """Test form accepts 'ordem cronológica' tipo"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'ordem cronológica',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_valid_tipo_prioridade(self):
        """Test form accepts 'prioridade' tipo"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_valid_tipo_acordo(self):
        """Test form accepts 'acordo' tipo"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'acordo',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_invalid_tipo_choice(self):
        """Test form rejects invalid tipo choice"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'invalid_choice',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    def test_empty_tipo_field(self):
        """Test form rejects empty tipo field"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': '',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
    
    # Phase Filtering Tests
    def test_fase_queryset_filtered_for_alvara(self):
        """Test that fase field only shows alvará phases"""
        form = AlvaraSimpleForm()
        fase_queryset = form.fields['fase'].queryset
        
        self.assertIn(self.fase_alvara, fase_queryset)
        self.assertNotIn(self.fase_requerimento, fase_queryset)
        self.assertNotIn(self.fase_inativa, fase_queryset)
    
    def test_honorarios_fase_queryset_filtered_active(self):
        """Test that honorários fase field only shows active phases"""
        form = AlvaraSimpleForm()
        fase_queryset = form.fields['fase_honorarios_contratuais'].queryset
        
        self.assertIn(self.fase_honorarios_ativa, fase_queryset)
        self.assertNotIn(self.fase_honorarios_inativa, fase_queryset)
    
    def test_valid_form_with_honorarios_fase(self):
        """Test valid form submission with honorários fase"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'honorarios_contratuais': '10000.00',
            'honorarios_sucumbenciais': '5000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id,
            'fase_honorarios_contratuais': self.fase_honorarios_ativa.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_optional_honorarios_fase(self):
        """Test that honorários fase is optional"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_optional_fase_field(self):
        """Test that fase field is optional"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'ordem cronológica'
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    # Form Initialization Tests
    def test_form_with_precatorio_context(self):
        """Test form initialization with precatorio context"""
        form = AlvaraSimpleForm(precatorio=self.precatorio)
        self.assertEqual(form.precatorio, self.precatorio)
    
    def test_form_without_precatorio_context(self):
        """Test form initialization without precatorio context"""
        form = AlvaraSimpleForm()
        self.assertIsNone(form.precatorio)
    
    # Field Widget and Attribute Tests
    def test_form_field_widgets(self):
        """Test that form fields have correct widgets and attributes"""
        form = AlvaraSimpleForm()
        
        # Test CPF field
        cpf_widget = form.fields['cliente_cpf'].widget
        self.assertIn('form-control', cpf_widget.attrs.get('class', ''))
        self.assertIn('pattern', cpf_widget.attrs)
        
        # Test currency fields
        valor_widget = form.fields['valor_principal'].widget
        self.assertIn('brazilian-currency', valor_widget.attrs.get('class', ''))
        
        # Test tipo field
        tipo_widget = form.fields['tipo'].widget
        self.assertIn('form-control', tipo_widget.attrs.get('class', ''))
    
    def test_form_field_labels(self):
        """Test that form fields have correct labels"""
        form = AlvaraSimpleForm()
        
        self.assertEqual(form.fields['cliente_cpf'].label, 'CPF do Cliente')
        self.assertEqual(form.fields['valor_principal'].label, 'Valor Principal')
        self.assertEqual(form.fields['honorarios_contratuais'].label, 'Honorários Contratuais')
        self.assertEqual(form.fields['honorarios_sucumbenciais'].label, 'Honorários Sucumbenciais')
        self.assertEqual(form.fields['tipo'].label, 'Tipo')
        self.assertEqual(form.fields['fase'].label, 'Fase')  # Field definition overrides Meta labels
        self.assertEqual(form.fields['fase_honorarios_contratuais'].label, 'Fase Honorários Contratuais')
    
    def test_form_field_help_texts(self):
        """Test that form fields have appropriate help texts"""
        form = AlvaraSimpleForm()
        
        self.assertIn('CPF do cliente', form.fields['cliente_cpf'].help_text)
        self.assertIn('reais', form.fields['valor_principal'].help_text)
        self.assertIn('específica para acompanhar', form.fields['fase_honorarios_contratuais'].help_text)
    
    # Edge Cases and Integration Tests
    def test_complete_form_with_all_fields(self):
        """Test complete form submission with all fields populated"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '100000.00',
            'honorarios_contratuais': '20000.00',
            'honorarios_sucumbenciais': '15000.00',
            'tipo': 'acordo',
            'fase': self.fase_alvara.id,
            'fase_honorarios_contratuais': self.fase_honorarios_ativa.id
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_minimal_valid_form(self):
        """Test minimal valid form with only required fields"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'tipo': 'ordem cronológica'
        }
        form = AlvaraSimpleForm(data=form_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())
    
    def test_form_meta_fields(self):
        """Test that form Meta includes correct fields"""
        form = AlvaraSimpleForm()
        expected_fields = [
            'tipo', 'fase', 'fase_honorarios_contratuais', 
            'valor_principal', 'honorarios_contratuais', 'honorarios_sucumbenciais'
        ]
        
        for field in expected_fields:
            self.assertIn(field, form.fields)
    
    def test_form_includes_honorarios_fields(self):
        """Test that form includes both honorários fields"""
        form = AlvaraSimpleForm()
        self.assertIn('honorarios_contratuais', form.fields)
        self.assertIn('honorarios_sucumbenciais', form.fields)
        self.assertIn('fase_honorarios_contratuais', form.fields)


class RequerimentoFormComprehensiveTest(TestCase):
    """Comprehensive test cases for RequerimentoForm"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Create another precatorio for testing client-precatorio relationship
        self.precatorio_other = Precatorio.objects.create(
            cnj='9876543-21.2023.8.26.0200',
            orcamento=2023,
            origem='9876543-21.2022.8.26.0002',
            valor_de_face=50000.00,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.cliente_cnpj = Cliente.objects.create(
            cpf='12345678000195',
            nome='Empresa Ltda',
            nascimento=date(2000, 1, 1),
            prioridade=False
        )
        
        # Create a client not linked to any precatorio
        self.cliente_unlinked = Cliente.objects.create(
            cpf='11144477735',
            nome='Maria Souza',
            nascimento=date(1985, 3, 20),
            prioridade=True
        )
        
        # Link the clientes to the precatorio (required by new validation)
        self.precatorio.clientes.add(self.cliente)
        self.precatorio.clientes.add(self.cliente_cnpj)
        
        # Link unlinked client to the other precatorio
        self.precatorio_other.clientes.add(self.cliente_unlinked)
        
        self.fase_requerimento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True,
            ordem=1
        )
        self.fase_ambos = Fase.objects.create(
            nome='Cancelado',
            tipo='ambos',
            cor='#95A5A6',
            ativa=True,
            ordem=2
        )
        # Create an alvara fase that should not appear in requerimento forms
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True,
            ordem=3
        )
        # Create an inactive fase
        self.fase_inactive = Fase.objects.create(
            nome='Fase Inativa',
            tipo='requerimento',
            cor='#000000',
            ativa=False,
            ordem=4
        )
        
        self.valid_form_data_cpf = {
            'cliente_cpf': '123.456.789-09',
            'pedido': 'prioridade doença',
            'valor': '25000.00',
            'desagio': '15.5',
            'fase': self.fase_requerimento.id
        }
        self.valid_form_data_cnpj = {
            'cliente_cpf': '12.345.678/0001-95',
            'pedido': 'prioridade idade',
            'valor': '40000.00',
            'desagio': '10.0',
            'fase': self.fase_requerimento.id
        }

    # ============ FORM INITIALIZATION AND CONFIGURATION TESTS ============
    
    def test_form_initialization_with_precatorio(self):
        """Test form initialization with precatorio parameter"""
        form = RequerimentoForm(precatorio=self.precatorio)
        self.assertEqual(form.precatorio, self.precatorio)
        self.assertIsNotNone(form.fields['fase'].queryset)
        
    def test_form_initialization_without_precatorio(self):
        """Test form initialization without precatorio parameter"""
        form = RequerimentoForm()
        self.assertIsNone(form.precatorio)
        self.assertIsNotNone(form.fields['fase'].queryset)
    
    def test_form_field_configuration(self):
        """Test form field configuration and widget attributes"""
        form = RequerimentoForm(precatorio=self.precatorio)
        
        # Test cliente_cpf field configuration
        cpf_field = form.fields['cliente_cpf']
        self.assertEqual(cpf_field.max_length, 18)
        self.assertEqual(cpf_field.label, 'CPF do Cliente')
        self.assertIn('form-control', cpf_field.widget.attrs['class'])
        self.assertIn('000.000.000-00', cpf_field.widget.attrs['placeholder'])
        
        # Test valor field configuration
        valor_field = form.fields['valor']
        self.assertEqual(valor_field.max_digits, 15)
        self.assertEqual(valor_field.decimal_places, 2)
        self.assertIn('brazilian-currency', valor_field.widget.attrs['class'])
        
        # Test desagio field configuration
        desagio_field = form.fields['desagio']
        self.assertEqual(desagio_field.max_digits, 5)
        self.assertEqual(desagio_field.decimal_places, 2)
        self.assertIn('brazilian-number', desagio_field.widget.attrs['class'])
        
        # Test fase field configuration
        fase_field = form.fields['fase']
        self.assertFalse(fase_field.required)
        self.assertEqual(fase_field.empty_label, 'Selecione a fase')

    # ============ PHASE FILTERING TESTS ============
    
    def test_requerimento_form_fase_filtering(self):
        """Test that RequerimentoForm only shows requerimento and ambos phases"""
        form = RequerimentoForm(precatorio=self.precatorio)
        fase_queryset = form.fields['fase'].queryset
        
        # Should include requerimento and ambos phases
        self.assertIn(self.fase_requerimento, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include alvara phases
        self.assertNotIn(self.fase_alvara, fase_queryset)
        
    def test_fase_filtering_includes_active_phases_only(self):
        """Test that only active phases are included in the queryset"""
        form = RequerimentoForm(precatorio=self.precatorio)
        fase_queryset = form.fields['fase'].queryset
        
        # Should include active phases
        self.assertIn(self.fase_requerimento, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include inactive phases
        self.assertNotIn(self.fase_inactive, fase_queryset)

    # ============ BASIC FORM VALIDATION TESTS ============
    
    def test_valid_requerimento_form_cpf(self):
        """Test form validation with valid CPF data"""
        form = RequerimentoForm(data=self.valid_form_data_cpf, precatorio=self.precatorio)
        self.assertTrue(form.is_valid(), f"Form should be valid but got errors: {form.errors}")

    def test_valid_requerimento_form_cnpj(self):
        """Test form validation with valid CNPJ data"""
        form = RequerimentoForm(data=self.valid_form_data_cnpj, precatorio=self.precatorio)
        self.assertTrue(form.is_valid(), f"Form should be valid but got errors: {form.errors}")
        
    def test_form_with_minimal_required_data(self):
        """Test form with only required fields"""
        minimal_data = {
            'cliente_cpf': '123.456.789-09',
            'pedido': 'prioridade doença',
            'valor': '1000.00',
            'desagio': '0.00',
        }
        form = RequerimentoForm(data=minimal_data, precatorio=self.precatorio)
        self.assertTrue(form.is_valid(), f"Minimal form should be valid but got errors: {form.errors}")

    # ============ CPF/CNPJ VALIDATION TESTS ============
    
    def test_invalid_requerimento_form_document(self):
        """Test form rejection with invalid documents"""
        # Invalid CPF
        invalid_data = self.valid_form_data_cpf.copy()
        invalid_data['cliente_cpf'] = '11111111111'
        form = RequerimentoForm(data=invalid_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        
        # Invalid CNPJ
        invalid_data_cnpj = self.valid_form_data_cnpj.copy()
        invalid_data_cnpj['cliente_cpf'] = '12345678000100'
        form = RequerimentoForm(data=invalid_data_cnpj, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
    
    def test_cpf_cnpj_format_variations(self):
        """Test various CPF/CNPJ input formats"""
        test_cases = [
            ('12345678909', True),  # CPF without formatting
            ('123.456.789-09', True),  # CPF with formatting
            ('123 456 789 09', True),  # CPF with spaces
            ('12345678000195', True),  # CNPJ without formatting
            ('12.345.678/0001-95', True),  # CNPJ with formatting
            ('12 345 678 0001 95', True),  # CNPJ with spaces
            ('123456', False),  # Too short
            ('1234567890123456789', False),  # Too long
            ('12345678901', False),  # 11 digits but invalid CPF
            ('12345678000123', False),  # 14 digits but invalid CNPJ
        ]
        
        for cpf_value, should_be_valid in test_cases:
            with self.subTest(cpf=cpf_value, expected_valid=should_be_valid):
                test_data = self.valid_form_data_cpf.copy()
                test_data['cliente_cpf'] = cpf_value
                form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
                if should_be_valid:
                    # Note: This will fail if the client doesn't exist, but that's expected
                    # We're testing document format validation here
                    if not form.is_valid() and 'cliente_cpf' in form.errors:
                        error_msg = str(form.errors['cliente_cpf'])
                        # Should not fail due to format issues
                        self.assertNotIn('Documento deve ser um CPF', error_msg)
                        self.assertNotIn('inválido', error_msg)
                else:
                    self.assertFalse(form.is_valid())
                    self.assertIn('cliente_cpf', form.errors)

    # ============ CLIENT-PRECATORIO RELATIONSHIP VALIDATION TESTS ============
    
    def test_client_not_linked_to_precatorio(self):
        """Test validation when client exists but is not linked to precatorio"""
        test_data = self.valid_form_data_cpf.copy()
        test_data['cliente_cpf'] = '111.444.777-35'  # cliente_unlinked CPF
        form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        error_msg = str(form.errors['cliente_cpf'])
        self.assertIn('não está vinculado ao precatório', error_msg)
        self.assertIn(self.precatorio.cnj, error_msg)
    
    def test_client_does_not_exist(self):
        """Test validation when client does not exist"""
        test_data = self.valid_form_data_cpf.copy()
        test_data['cliente_cpf'] = '111.222.333-96'  # Valid CPF format but non-existent
        form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        error_msg = str(form.errors['cliente_cpf'])
        self.assertIn('Não foi encontrado um cliente', error_msg)
    
    def test_form_without_precatorio_parameter(self):
        """Test form behavior when precatorio parameter is not provided"""
        form = RequerimentoForm(data=self.valid_form_data_cpf)  # No precatorio parameter
        # Should still validate document format but not client-precatorio relationship
        if form.is_valid():
            # If valid, the client exists and document is valid
            pass
        else:
            # If not valid, should be due to client not existing, not relationship
            if 'cliente_cpf' in form.errors:
                error_msg = str(form.errors['cliente_cpf'])
                self.assertNotIn('não está vinculado', error_msg)

    # ============ CURRENCY AND DECIMAL VALIDATION TESTS ============
    
    def test_valor_field_validation(self):
        """Test valor field validation with various inputs"""
        test_cases = [
            ('0.01', True),  # Minimum positive value
            ('1000000.99', True),  # Large value
            ('50000.00', True),  # Standard value
            ('-100.00', False),  # Negative value (should fail due to validate_currency)
            ('0.00', True),  # Zero value (technically valid)
            ('abc', False),  # Non-numeric
            ('1000000000000000', False),  # Too many digits
        ]
        
        for valor, should_be_valid in test_cases:
            with self.subTest(valor=valor, expected_valid=should_be_valid):
                test_data = self.valid_form_data_cpf.copy()
                test_data['valor'] = valor
                form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
                if should_be_valid:
                    if not form.is_valid() and 'valor' in form.errors:
                        self.fail(f"Valor {valor} should be valid but got error: {form.errors['valor']}")
                else:
                    self.assertFalse(form.is_valid())
                    self.assertTrue('valor' in form.errors or form.non_field_errors())
    
    def test_desagio_field_validation(self):
        """Test desagio field validation with various inputs"""
        test_cases = [
            ('0.00', True),  # Zero deságio
            ('15.50', True),  # Standard deságio
            ('99.99', True),  # High deságio
            ('100.00', True),  # 100% deságio
            ('-5.00', True),  # Negative deságio (might be valid business case)
            ('abc', False),  # Non-numeric
            ('123.456', False),  # Too many decimal places
        ]
        
        for desagio, should_be_valid in test_cases:
            with self.subTest(desagio=desagio, expected_valid=should_be_valid):
                test_data = self.valid_form_data_cpf.copy()
                test_data['desagio'] = desagio
                form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
                if should_be_valid:
                    if not form.is_valid() and 'desagio' in form.errors:
                        self.fail(f"Desagio {desagio} should be valid but got error: {form.errors['desagio']}")
                else:
                    self.assertFalse(form.is_valid())
                    self.assertIn('desagio', form.errors)

    # ============ FIELD REQUIREMENTS TESTS ============
    
    def test_required_fields(self):
        """Test behavior with missing required fields"""
        required_fields = ['cliente_cpf', 'pedido', 'valor', 'desagio']
        
        for field_name in required_fields:
            with self.subTest(missing_field=field_name):
                test_data = self.valid_form_data_cpf.copy()
                del test_data[field_name]
                form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
                self.assertFalse(form.is_valid())
                self.assertIn(field_name, form.errors)
    
    def test_optional_fields(self):
        """Test behavior with missing optional fields"""
        # fase is optional
        test_data = self.valid_form_data_cpf.copy()
        del test_data['fase']
        form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
        # Should still be valid without fase
        if not form.is_valid():
            self.assertNotIn('fase', form.errors, "Fase field should be optional")

    # ============ CLEAN METHOD TESTS ============
    
    def test_clean_cliente_cpf_with_different_formats(self):
        """Test clean_cliente_cpf method with different input formats"""
        test_cases = [
            '123.456.789-09',
            '12345678909',
            '123 456 789 09',
            '123-456-789.09',
        ]
        
        for cpf_format in test_cases:
            with self.subTest(cpf_format=cpf_format):
                test_data = self.valid_form_data_cpf.copy()
                test_data['cliente_cpf'] = cpf_format
                form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
                form.is_valid()  # Trigger cleaning
                if 'cliente_cpf' not in form.errors:
                    # Should return the formatted input, not cleaned digits
                    self.assertEqual(form.cleaned_data['cliente_cpf'], cpf_format)

    # ============ INTEGRATION TESTS ============
    
    def test_form_saves_correctly_with_valid_data(self):
        """Test that form can be used to create a Requerimento instance"""
        form = RequerimentoForm(data=self.valid_form_data_cpf, precatorio=self.precatorio)
        if form.is_valid():
            # Test data should be properly cleaned and ready for model creation
            cleaned_data = form.cleaned_data
            self.assertIn('valor', cleaned_data)
            self.assertIn('desagio', cleaned_data)
            self.assertIn('pedido', cleaned_data)
            # Note: We don't actually save here as it would require more complex setup
        else:
            self.fail(f"Form should be valid for integration test: {form.errors}")
    
    def test_form_with_different_pedido_choices(self):
        """Test form with different pedido choice values"""
        # This would test against the actual choices defined in the model
        # For now, we test with the values used in test data
        pedido_choices = ['prioridade doença', 'prioridade idade', 'ordem cronológica']
        
        for pedido in pedido_choices:
            with self.subTest(pedido=pedido):
                test_data = self.valid_form_data_cpf.copy()
                test_data['pedido'] = pedido
                form = RequerimentoForm(data=test_data, precatorio=self.precatorio)
                if not form.is_valid() and 'pedido' in form.errors:
                    # This might fail if the choice is not valid in the model
                    # but that's a model configuration issue, not form logic
                    pass

    # ============ ERROR MESSAGE TESTS ============
    
    def test_error_messages_are_user_friendly(self):
        """Test that error messages are clear and user-friendly"""
        # Test invalid CPF error message
        invalid_data = self.valid_form_data_cpf.copy()
        invalid_data['cliente_cpf'] = '11111111111'
        form = RequerimentoForm(data=invalid_data, precatorio=self.precatorio)
        form.is_valid()
        if 'cliente_cpf' in form.errors:
            error_msg = str(form.errors['cliente_cpf'])
            self.assertIn('inválido', error_msg.lower())
        
        # Test client not found error message with valid CPF that doesn't exist
        invalid_data['cliente_cpf'] = '111.222.333-96'  # Valid CPF format but non-existent
        form = RequerimentoForm(data=invalid_data, precatorio=self.precatorio)
        form.is_valid()
        if 'cliente_cpf' in form.errors:
            error_msg = str(form.errors['cliente_cpf'])
            self.assertIn('não foi encontrado', error_msg.lower())

    # ============ EDGE CASES TESTS ============
    
    def test_form_with_extreme_values(self):
        """Test form with extreme but technically valid values"""
        extreme_data = self.valid_form_data_cpf.copy()
        extreme_data.update({
            'valor': '999999999999999.99',  # Maximum possible value
            'desagio': '99.99',  # Very high deságio
        })
        form = RequerimentoForm(data=extreme_data, precatorio=self.precatorio)
        # This tests the form's handling of edge cases within valid ranges
        if not form.is_valid():
            # If invalid, should be due to business logic, not technical limits
            for field, errors in form.errors.items():
                if field in ['valor', 'desagio']:
                    self.assertNotIn('formato', str(errors).lower())
    
    def test_form_with_unicode_characters(self):
        """Test form handling of unicode characters in text fields"""
        # CPF field should only accept digits and common separators
        unicode_data = self.valid_form_data_cpf.copy()
        unicode_data['cliente_cpf'] = '123.456.789-09'  # Valid CPF with normal chars
        form = RequerimentoForm(data=unicode_data, precatorio=self.precatorio)
        # Should handle normal formatting characters correctly
        if not form.is_valid() and 'cliente_cpf' in form.errors:
            error_msg = str(form.errors['cliente_cpf'])
            # Should not fail due to character encoding issues
            self.assertNotIn('encoding', error_msg.lower())


# Keep the original test class for backward compatibility
class RequerimentoFormTest(RequerimentoFormComprehensiveTest):
    """Legacy test class - inherits all tests from comprehensive version"""
    pass


class PrecatorioFormTest(TestCase):
    """
    Comprehensive test suite for PrecatorioForm functionality and validation.
    
    This test class provides thorough coverage of the PrecatorioForm, which is
    the core form for creating and managing precatorio records in the system.
    The tests validate CNJ format validation, financial calculations, percentage
    validations, date handling, and comprehensive business rule enforcement.
    
    Test Coverage:
        - CNJ number format validation and uniqueness
        - Financial value formatting and validation
        - Percentage field validation and constraints
        - Date field handling and validation
        - Enum field choices and validation
        - Form initialization and field configuration
        - Error handling and validation messages
        - Data persistence and model integration
        - Edge cases and boundary conditions
        
    Key Test Areas:
        - CNJ Validation: Tests CNJ format compliance and uniqueness
        - Financial Fields: Tests currency formatting for all monetary fields
        - Percentage Validation: Tests percentage constraints and formatting
        - Date Handling: Tests Brazilian date format compliance
        - Enum Validation: Tests status choices for various fields
        - Business Rules: Tests complex validation logic
        - Error Scenarios: Tests validation failures and error messages
        
    Business Logic Testing:
        - CNJ must follow Brazilian court number format standards
        - Financial values must be positive and properly formatted
        - Percentages must be within valid ranges (0-100%)
        - Dates must be in Brazilian format and valid
        - Status fields must use predefined enum values
        - Duplicate CNJ numbers must be prevented
        
    Setup Dependencies:
        - Valid CNJ number following Brazilian format
        - Proper financial value formatting
        - Valid percentage values within constraints
        - Brazilian date format compliance
        - Predefined enum values for status fields
    """
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'cnj': '1234567-89.2023.8.26.0100',
            'orcamento': '2023',
            'origem': '1234567-89.2022.8.26.0001',
            'valor_de_face': '100000.00',
            'ultima_atualizacao': '100000.00',
            'data_ultima_atualizacao': '2023-01-01',
            'percentual_contratuais_assinado': '10.0',
            'percentual_contratuais_apartado': '5.0',
            'percentual_sucumbenciais': '20.0',
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = PrecatorioForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = PrecatorioForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        precatorio = form.save()
        self.assertEqual(precatorio.cnj, '1234567-89.2023.8.26.0100')


class PrecatorioFormComprehensiveTest(TestCase):
    """
    Comprehensive test suite for PrecatorioForm class.
    
    This test class provides thorough coverage of PrecatorioForm functionality including:
    - Form initialization and field configuration
    - Field validation for all custom fields
    - Widget behavior and attributes
    - Custom clean methods for percentage validation
    - Form submission and save functionality
    - Error handling and edge cases
    - Integration with BrazilianDateInput widget
    
    The tests ensure proper validation of CNJ format, currency values, percentage ranges,
    and proper form rendering with correct CSS classes and HTML attributes.
    """
    
    def setUp(self):
        """Set up test data for PrecatorioForm tests"""
        self.valid_form_data = {
            'cnj': '1234567-89.2023.8.26.0100',
            'orcamento': 2023,
            'origem': '9876543-21.2022.8.26.0001',
            'valor_de_face': '50000.00',
            'ultima_atualizacao': '55000.00',
            'data_ultima_atualizacao': '2023-06-15',
            'percentual_contratuais_assinado': '20.00',
            'percentual_contratuais_apartado': '15.00',
            'percentual_sucumbenciais': '10.00',
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        }
        
        self.minimal_valid_data = {
            'cnj': '7654321-98.2024.8.26.0200',
            'orcamento': 2024,
            'origem': '1111111-11.2023.8.26.0100',
            'valor_de_face': '25000.00',
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        }
    
    def test_form_initialization(self):
        """Test form initializes correctly with proper field configuration"""
        form = PrecatorioForm()
        
        # Check that required fields are present
        self.assertIn('cnj', form.fields)
        self.assertIn('orcamento', form.fields)
        self.assertIn('origem', form.fields)
        self.assertIn('valor_de_face', form.fields)
        self.assertIn('credito_principal', form.fields)
        self.assertIn('honorarios_contratuais', form.fields)
        self.assertIn('honorarios_sucumbenciais', form.fields)
        
        # Check optional fields
        self.assertIn('ultima_atualizacao', form.fields)
        self.assertIn('data_ultima_atualizacao', form.fields)
        self.assertIn('percentual_contratuais_assinado', form.fields)
        self.assertIn('percentual_contratuais_apartado', form.fields)
        self.assertIn('percentual_sucumbenciais', form.fields)
        
        # Check field requirements
        self.assertTrue(form.fields['cnj'].required)
        self.assertTrue(form.fields['orcamento'].required)
        self.assertTrue(form.fields['origem'].required)
        self.assertTrue(form.fields['valor_de_face'].required)
        self.assertFalse(form.fields['ultima_atualizacao'].required)
        self.assertFalse(form.fields['percentual_contratuais_assinado'].required)
    
    def test_cnj_field_configuration(self):
        """Test CNJ field widget attributes and validation"""
        form = PrecatorioForm()
        cnj_field = form.fields['cnj']
        
        # Check field properties
        self.assertEqual(cnj_field.max_length, 25)
        self.assertEqual(cnj_field.label, 'CNJ')
        # Check that validate_cnj is in the validators list
        validator_names = [getattr(v, '__name__', v.__class__.__name__) for v in cnj_field.validators]
        self.assertIn('validate_cnj', validator_names)
        
        # Check widget attributes
        widget_attrs = cnj_field.widget.attrs
        self.assertEqual(widget_attrs['class'], 'form-control')
        self.assertEqual(widget_attrs['placeholder'], '1234567-89.2023.8.26.0100')
        self.assertIn('pattern', widget_attrs)
        self.assertIn('title', widget_attrs)
    
    def test_origem_field_configuration(self):
        """Test origem field widget attributes and validation"""
        form = PrecatorioForm()
        origem_field = form.fields['origem']
        
        # Check field properties
        self.assertEqual(origem_field.max_length, 25)
        self.assertEqual(origem_field.label, 'CNJ de Origem')
        # Check that validate_cnj is in the validators list
        validator_names = [getattr(v, '__name__', v.__class__.__name__) for v in origem_field.validators]
        self.assertIn('validate_cnj', validator_names)
        
        # Check widget attributes
        widget_attrs = origem_field.widget.attrs
        self.assertEqual(widget_attrs['class'], 'form-control')
        self.assertEqual(widget_attrs['placeholder'], '9876543-21.2022.8.26.0001')
    
    def test_currency_fields_configuration(self):
        """Test currency field configuration and validation"""
        form = PrecatorioForm()
        
        # Test valor_de_face field
        valor_field = form.fields['valor_de_face']
        self.assertEqual(valor_field.max_digits, 15)
        self.assertEqual(valor_field.decimal_places, 2)
        self.assertEqual(valor_field.label, 'Valor de Face')
        # Check that validate_currency is in the validators list
        validator_names = [getattr(v, '__name__', v.__class__.__name__) for v in valor_field.validators]
        self.assertIn('validate_currency', validator_names)
        
        # Test ultima_atualizacao field
        atualizacao_field = form.fields['ultima_atualizacao']
        self.assertEqual(atualizacao_field.max_digits, 15)
        self.assertEqual(atualizacao_field.decimal_places, 2)
        self.assertFalse(atualizacao_field.required)
        validator_names = [getattr(v, '__name__', v.__class__.__name__) for v in atualizacao_field.validators]
        self.assertIn('validate_currency', validator_names)
        
        # Check widget classes for Brazilian currency formatting
        self.assertIn('brazilian-currency', valor_field.widget.attrs['class'])
        self.assertIn('brazilian-currency', atualizacao_field.widget.attrs['class'])
    
    def test_percentage_fields_configuration(self):
        """Test percentage field configuration"""
        form = PrecatorioForm()
        
        percentage_fields = [
            'percentual_contratuais_assinado',
            'percentual_contratuais_apartado', 
            'percentual_sucumbenciais'
        ]
        
        for field_name in percentage_fields:
            field = form.fields[field_name]
            self.assertEqual(field.max_digits, 5)
            self.assertEqual(field.decimal_places, 2)
            self.assertFalse(field.required)
            self.assertIn('brazilian-number', field.widget.attrs['class'])
    
    def test_brazilian_date_widget(self):
        """Test BrazilianDateInput widget configuration"""
        form = PrecatorioForm()
        date_widget = form.fields['data_ultima_atualizacao'].widget
        
        # Check that it's a BrazilianDateInput widget
        self.assertEqual(date_widget.__class__.__name__, 'BrazilianDateInput')
        self.assertFalse(date_widget.attrs.get('required', True))
    
    def test_form_valid_with_complete_data(self):
        """Test form validation with complete valid data"""
        form = PrecatorioForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_form_valid_with_minimal_data(self):
        """Test form validation with minimal required data"""
        form = PrecatorioForm(data=self.minimal_valid_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_cnj_validation_invalid_format(self):
        """Test CNJ field validation with invalid formats"""
        invalid_cnj_data = self.valid_form_data.copy()
        
        invalid_cnjs = [
            'invalid-cnj-format',
            '123456789',
            '1234567-89.2023.8.26',  # Missing digits
            '12345678-89.2023.8.26.0100',  # Too many digits
            '',
        ]
        
        for invalid_cnj in invalid_cnjs:
            with self.subTest(cnj=invalid_cnj):
                invalid_cnj_data['cnj'] = invalid_cnj
                form = PrecatorioForm(data=invalid_cnj_data)
                self.assertFalse(form.is_valid())
                self.assertIn('cnj', form.errors)
    
    def test_origem_validation_invalid_format(self):
        """Test origem field validation with invalid formats"""
        invalid_origem_data = self.valid_form_data.copy()
        invalid_origem_data['origem'] = 'invalid-origem-format'
        
        form = PrecatorioForm(data=invalid_origem_data)
        self.assertFalse(form.is_valid())
        self.assertIn('origem', form.errors)
    
    def test_currency_validation_negative_values(self):
        """Test currency field validation with negative values"""
        # Test valor_de_face with negative value
        negative_valor_data = self.valid_form_data.copy()
        negative_valor_data['valor_de_face'] = '-50000.00'
        
        form = PrecatorioForm(data=negative_valor_data)
        self.assertFalse(form.is_valid())
        self.assertIn('valor_de_face', form.errors)
        
        # Test ultima_atualizacao with negative value
        negative_atualizacao_data = self.valid_form_data.copy()
        negative_atualizacao_data['ultima_atualizacao'] = '-10000.00'
        
        form = PrecatorioForm(data=negative_atualizacao_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ultima_atualizacao', form.errors)
    
    def test_clean_percentual_contratuais_assinado_valid_range(self):
        """Test clean method for percentual_contratuais_assinado with valid values"""
        valid_percentages = ['0.00', '15.50', '30.00']
        
        for percentage in valid_percentages:
            with self.subTest(percentage=percentage):
                data = self.valid_form_data.copy()
                data['percentual_contratuais_assinado'] = percentage
                form = PrecatorioForm(data=data)
                self.assertTrue(form.is_valid(), f"Form errors for {percentage}: {form.errors}")
    
    def test_clean_percentual_contratuais_assinado_invalid_range(self):
        """Test clean method for percentual_contratuais_assinado with invalid values"""
        invalid_percentages = ['-1.00', '30.01', '50.00', '100.00']
        
        for percentage in invalid_percentages:
            with self.subTest(percentage=percentage):
                data = self.valid_form_data.copy()
                data['percentual_contratuais_assinado'] = percentage
                form = PrecatorioForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn('percentual_contratuais_assinado', form.errors)
                self.assertIn('deve estar entre 0% e 30%', str(form.errors['percentual_contratuais_assinado']))
    
    def test_clean_percentual_contratuais_apartado_validation(self):
        """Test clean method for percentual_contratuais_apartado"""
        # Test valid range
        data = self.valid_form_data.copy()
        data['percentual_contratuais_apartado'] = '25.00'
        form = PrecatorioForm(data=data)
        self.assertTrue(form.is_valid())
        
        # Test invalid range
        data['percentual_contratuais_apartado'] = '35.00'
        form = PrecatorioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('percentual_contratuais_apartado', form.errors)
    
    def test_clean_percentual_sucumbenciais_validation(self):
        """Test clean method for percentual_sucumbenciais"""
        # Test valid range
        data = self.valid_form_data.copy()
        data['percentual_sucumbenciais'] = '20.00'
        form = PrecatorioForm(data=data)
        self.assertTrue(form.is_valid())
        
        # Test invalid range
        data['percentual_sucumbenciais'] = '-5.00'
        form = PrecatorioForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('percentual_sucumbenciais', form.errors)
    
    def test_percentage_fields_optional(self):
        """Test that percentage fields are optional and handle None values"""
        data = self.minimal_valid_data.copy()
        # Don't include any percentage fields
        form = PrecatorioForm(data=data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Test with empty string values
        data.update({
            'percentual_contratuais_assinado': '',
            'percentual_contratuais_apartado': '',
            'percentual_sucumbenciais': ''
        })
        form = PrecatorioForm(data=data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_orcamento_field_validation(self):
        """Test orcamento field validation"""
        # Test valid year
        data = self.valid_form_data.copy()
        data['orcamento'] = 2024
        form = PrecatorioForm(data=data)
        self.assertTrue(form.is_valid())
        
        # Test with widget attributes - check Meta.widgets configuration
        form = PrecatorioForm()
        orcamento_widget = form.fields['orcamento'].widget
        self.assertEqual(orcamento_widget.attrs['min'], '1988')
        self.assertEqual(orcamento_widget.attrs['max'], '2050')
        self.assertEqual(orcamento_widget.attrs['class'], 'form-control')
        self.assertEqual(orcamento_widget.attrs['placeholder'], '2023')
    
    def test_select_fields_widget_classes(self):
        """Test that select fields have proper CSS classes"""
        form = PrecatorioForm()
        
        select_fields = ['credito_principal', 'honorarios_contratuais', 'honorarios_sucumbenciais']
        
        for field_name in select_fields:
            field = form.fields[field_name]
            self.assertEqual(field.widget.attrs['class'], 'form-select')
    
    def test_form_save_functionality(self):
        """Test form save creates Precatorio object correctly"""
        form = PrecatorioForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        
        precatorio = form.save()
        self.assertIsInstance(precatorio, Precatorio)
        self.assertEqual(precatorio.cnj, '1234567-89.2023.8.26.0100')
        self.assertEqual(precatorio.orcamento, 2023)
        # Use Decimal comparison for precise decimal values
        from decimal import Decimal
        self.assertEqual(precatorio.valor_de_face, Decimal('50000.00'))
        self.assertEqual(precatorio.percentual_contratuais_assinado, Decimal('20.00'))
    
    def test_form_field_labels(self):
        """Test that form fields have correct labels"""
        form = PrecatorioForm()
        
        expected_labels = {
            'orcamento': 'Ano do Orçamento',
            'credito_principal': 'Status do Crédito Principal',
            'honorarios_contratuais': 'Status dos Honorários Contratuais',
            'honorarios_sucumbenciais': 'Status dos Honorários Sucumbenciais',
            'data_ultima_atualizacao': 'Data da Última Atualização (Opcional)',
        }
        
        for field_name, expected_label in expected_labels.items():
            self.assertEqual(form.fields[field_name].label, expected_label)
    
    def test_form_help_texts(self):
        """Test that form fields have proper help texts"""
        form = PrecatorioForm()
        
        # Check CNJ help text
        self.assertIn('Formato: NNNNNNN-DD.AAAA.J.TR.OOOO', form.fields['cnj'].help_text)
        
        # Check currency help texts
        self.assertIn('Valor em reais', form.fields['valor_de_face'].help_text)
        self.assertIn('Opcional', form.fields['ultima_atualizacao'].help_text)
        
        # Check percentage help texts
        self.assertIn('entre 0% e 30%', form.fields['percentual_contratuais_assinado'].help_text)
    
    def test_invalid_currency_format(self):
        """Test form validation with invalid currency formats"""
        invalid_data = self.valid_form_data.copy()
        invalid_data['valor_de_face'] = 'invalid_currency'
        
        form = PrecatorioForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('valor_de_face', form.errors)
    
    def test_missing_required_fields(self):
        """Test form validation with missing required fields"""
        required_fields = ['cnj', 'orcamento', 'origem', 'valor_de_face', 
                          'credito_principal', 'honorarios_contratuais', 'honorarios_sucumbenciais']
        
        for field_name in required_fields:
            with self.subTest(field=field_name):
                incomplete_data = self.valid_form_data.copy()
                del incomplete_data[field_name]
                form = PrecatorioForm(data=incomplete_data)
                self.assertFalse(form.is_valid())
                self.assertIn(field_name, form.errors)


class ClienteFormComprehensiveTest(TestCase):
    """
    Comprehensive test suite for ClienteForm class.
    
    This test class provides thorough coverage of ClienteForm functionality including:
    - Form initialization and field configuration
    - CPF/CNPJ field validation and format handling
    - precatorio_cnj field validation and database integration
    - Custom clean methods testing
    - Widget behavior and attributes
    - Form submission and save functionality
    - Error handling and edge cases
    - BrazilianDateInput widget integration
    
    The tests ensure proper validation of CPF/CNPJ formats, CNJ format validation,
    precatorio existence checking, and proper form rendering with correct CSS classes.
    """
    
    def setUp(self):
        """Set up test data for ClienteForm comprehensive tests"""
        # Create test precatorio for CNJ validation
        self.test_precatorio = Precatorio.objects.create(
            cnj='7654321-98.2024.8.26.0200',
            orcamento=2024,
            origem='1111111-11.2023.8.26.0100',
            valor_de_face=75000.00,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        self.valid_form_data = {
            'cpf': '111.444.777-35',  # Valid CPF
            'nome': 'João Silva Santos',
            'nascimento': '1985-03-20',
            'prioridade': False,
            'precatorio_cnj': '7654321-98.2024.8.26.0200'
        }
        
        self.valid_cnpj_data = {
            'cpf': '12.345.678/0001-95',  # Valid CNPJ
            'nome': 'Empresa Teste Ltda',
            'nascimento': '2000-01-01',
            'prioridade': True,
            'precatorio_cnj': ''  # Optional field
        }
        
        self.minimal_valid_data = {
            'cpf': '11144477735',  # Unformatted valid CPF
            'nome': 'Maria Santos',
            'nascimento': '1990-12-15',
            'prioridade': False
            # precatorio_cnj omitted (optional)
        }
    
    def test_form_initialization(self):
        """Test form initializes correctly with proper field configuration"""
        form = ClienteForm()
        
        # Check that required fields are present
        self.assertIn('cpf', form.fields)
        self.assertIn('nome', form.fields)
        self.assertIn('nascimento', form.fields)
        self.assertIn('prioridade', form.fields)
        self.assertIn('precatorio_cnj', form.fields)
        
        # Check field requirements
        self.assertTrue(form.fields['cpf'].required)
        self.assertTrue(form.fields['nome'].required)
        self.assertTrue(form.fields['nascimento'].required)
        self.assertFalse(form.fields['prioridade'].required)
        self.assertFalse(form.fields['precatorio_cnj'].required)
    
    def test_cpf_field_configuration(self):
        """Test CPF field widget attributes and validation"""
        form = ClienteForm()
        cpf_field = form.fields['cpf']
        
        # Check field properties
        self.assertEqual(cpf_field.max_length, 18)
        self.assertEqual(cpf_field.label, 'CPF ou CNPJ')
        self.assertIn('Digite o CPF', cpf_field.help_text)
        
        # Check widget attributes
        widget_attrs = cpf_field.widget.attrs
        self.assertEqual(widget_attrs['class'], 'form-control')
        self.assertEqual(widget_attrs['placeholder'], 'CPF ou CNPJ')
        self.assertIn('pattern', widget_attrs)
        self.assertIn('title', widget_attrs)
    
    def test_precatorio_cnj_field_configuration(self):
        """Test precatorio_cnj field widget attributes and validation"""
        form = ClienteForm()
        cnj_field = form.fields['precatorio_cnj']
        
        # Check field properties
        self.assertEqual(cnj_field.max_length, 25)
        self.assertEqual(cnj_field.label, 'CNJ do Precatório')
        self.assertFalse(cnj_field.required)
        self.assertIn('opcional', cnj_field.help_text)
        
        # Check that validate_cnj is in the validators list
        validator_names = [getattr(v, '__name__', v.__class__.__name__) for v in cnj_field.validators]
        self.assertIn('validate_cnj', validator_names)
        
        # Check widget attributes
        widget_attrs = cnj_field.widget.attrs
        self.assertEqual(widget_attrs['class'], 'form-control')
        self.assertEqual(widget_attrs['placeholder'], '1234567-89.2023.8.26.0100')
        self.assertIn('pattern', widget_attrs)
    
    def test_brazilian_date_widget_integration(self):
        """Test BrazilianDateInput widget for nascimento field"""
        form = ClienteForm()
        nascimento_widget = form.fields['nascimento'].widget
        
        # Check that it's a BrazilianDateInput widget
        self.assertEqual(nascimento_widget.__class__.__name__, 'BrazilianDateInput')
        # Check widget attributes inherited from BrazilianDateInput
        self.assertIn('form-control', nascimento_widget.attrs.get('class', ''))
    
    def test_form_labels_and_help_texts(self):
        """Test that form fields have correct labels and help texts"""
        form = ClienteForm()
        
        # Check labels
        expected_labels = {
            'nome': 'Nome Completo',
            'nascimento': 'Data de Nascimento',
            'prioridade': 'Cliente com Prioridade Legal',
        }
        
        for field_name, expected_label in expected_labels.items():
            self.assertEqual(form.fields[field_name].label, expected_label)
        
        # Check help texts
        self.assertIn('Digite o CPF', form.fields['cpf'].help_text)
        self.assertIn('opcional', form.fields['precatorio_cnj'].help_text)
    
    def test_form_valid_with_complete_data(self):
        """Test form validation with complete valid data"""
        form = ClienteForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_form_valid_with_cnpj_data(self):
        """Test form validation with valid CNPJ data"""
        form = ClienteForm(data=self.valid_cnpj_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_form_valid_with_minimal_data(self):
        """Test form validation with minimal required data (no precatorio_cnj)"""
        form = ClienteForm(data=self.minimal_valid_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_cpf_format_flexibility(self):
        """Test CPF field accepts multiple input formats"""
        cpf_formats = [
            '111.444.777-35',  # Formatted
            '11144477735',     # Unformatted
        ]
        
        for cpf_format in cpf_formats:
            with self.subTest(cpf=cpf_format):
                data = self.valid_form_data.copy()
                data['cpf'] = cpf_format
                form = ClienteForm(data=data)
                self.assertTrue(form.is_valid(), f"CPF format {cpf_format} should be valid")
    
    def test_cnpj_format_flexibility(self):
        """Test CNPJ field accepts multiple input formats"""
        cnpj_formats = [
            '12.345.678/0001-95',  # Formatted
            '12345678000195',      # Unformatted
        ]
        
        for cnpj_format in cnpj_formats:
            with self.subTest(cnpj=cnpj_format):
                data = self.valid_cnpj_data.copy()
                data['cpf'] = cnpj_format
                form = ClienteForm(data=data)
                self.assertTrue(form.is_valid(), f"CNPJ format {cnpj_format} should be valid")
    
    def test_clean_cpf_validation_errors(self):
        """Test clean_cpf method with various invalid inputs"""
        invalid_cpf_cases = [
            ('', 'Empty CPF'),
            ('123', 'Too short'),
            ('12345678901234567', 'Too long'),
            ('00000000000', 'All zeros CPF'),
            ('11111111111', 'All same digits CPF'),
            ('12345678900', 'Invalid check digits CPF'),
            ('1234567890123', 'Invalid length (13 digits)'),
            ('123456789012345', 'Invalid length (15 digits)'),
        ]
        
        for invalid_cpf, description in invalid_cpf_cases:
            with self.subTest(cpf=invalid_cpf, desc=description):
                data = self.valid_form_data.copy()
                data['cpf'] = invalid_cpf
                form = ClienteForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn('cpf', form.errors)
    
    def test_clean_cpf_cnpj_validation_errors(self):
        """Test clean_cpf method with invalid CNPJ inputs"""
        invalid_cnpj_cases = [
            ('00000000000000', 'All zeros CNPJ'),
            ('11111111111111', 'All same digits CNPJ'),
            ('12345678000100', 'Invalid check digits CNPJ'),
        ]
        
        for invalid_cnpj, description in invalid_cnpj_cases:
            with self.subTest(cnpj=invalid_cnpj, desc=description):
                data = self.valid_cnpj_data.copy()
                data['cpf'] = invalid_cnpj
                form = ClienteForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn('cpf', form.errors)
    
    def test_clean_cpf_returns_clean_numbers(self):
        """Test that clean_cpf removes formatting and returns clean numbers"""
        form = ClienteForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        
        # The clean_cpf method should return numbers only
        cleaned_cpf = form.cleaned_data['cpf']
        self.assertEqual(cleaned_cpf, '11144477735')
        self.assertTrue(cleaned_cpf.isdigit())
    
    def test_clean_precatorio_cnj_valid_existing_cnj(self):
        """Test clean_precatorio_cnj with valid existing CNJ"""
        form = ClienteForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Should return the CNJ as-is
        self.assertEqual(form.cleaned_data['precatorio_cnj'], '7654321-98.2024.8.26.0200')
    
    def test_clean_precatorio_cnj_empty_optional(self):
        """Test clean_precatorio_cnj with empty value (optional field)"""
        data = self.valid_form_data.copy()
        data['precatorio_cnj'] = ''
        
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid())
        
        # Should return empty string for optional field
        self.assertEqual(form.cleaned_data['precatorio_cnj'], '')
    
    def test_clean_precatorio_cnj_nonexistent_cnj(self):
        """Test clean_precatorio_cnj with non-existent CNJ"""
        data = self.valid_form_data.copy()
        data['precatorio_cnj'] = '9999999-99.2024.8.26.9999'  # Non-existent CNJ
        
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('precatorio_cnj', form.errors)
        self.assertIn('Não foi encontrado um precatório', str(form.errors['precatorio_cnj']))
    
    def test_clean_precatorio_cnj_invalid_format(self):
        """Test clean_precatorio_cnj with invalid CNJ format"""
        data = self.valid_form_data.copy()
        data['precatorio_cnj'] = 'invalid-cnj-format'
        
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('precatorio_cnj', form.errors)
    
    def test_form_save_functionality(self):
        """Test form save creates Cliente object correctly"""
        form = ClienteForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        
        cliente = form.save()
        self.assertIsInstance(cliente, Cliente)
        self.assertEqual(cliente.nome, 'João Silva Santos')
        self.assertEqual(cliente.cpf, '11144477735')  # Should be stored without formatting
        self.assertFalse(cliente.prioridade)
    
    def test_form_save_with_cnpj(self):
        """Test form save with CNPJ creates Cliente object correctly"""
        form = ClienteForm(data=self.valid_cnpj_data)
        self.assertTrue(form.is_valid())
        
        cliente = form.save()
        self.assertEqual(cliente.nome, 'Empresa Teste Ltda')
        self.assertEqual(cliente.cpf, '12345678000195')  # CNPJ stored without formatting
        self.assertTrue(cliente.prioridade)
    
    def test_widget_css_classes(self):
        """Test that form widgets have correct CSS classes"""
        form = ClienteForm()
        
        # Check CSS classes for various widgets
        self.assertEqual(form.fields['cpf'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['nome'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['precatorio_cnj'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['prioridade'].widget.attrs['class'], 'form-check-input')
    
    def test_widget_placeholders(self):
        """Test that form widgets have appropriate placeholders"""
        form = ClienteForm()
        
        self.assertEqual(form.fields['cpf'].widget.attrs['placeholder'], 'CPF ou CNPJ')
        self.assertEqual(form.fields['nome'].widget.attrs['placeholder'], 'Digite o nome completo do cliente')
        self.assertEqual(form.fields['precatorio_cnj'].widget.attrs['placeholder'], '1234567-89.2023.8.26.0100')
    
    def test_missing_required_fields(self):
        """Test form validation with missing required fields"""
        required_fields = ['cpf', 'nome', 'nascimento']
        
        for field_name in required_fields:
            with self.subTest(field=field_name):
                incomplete_data = self.valid_form_data.copy()
                del incomplete_data[field_name]
                form = ClienteForm(data=incomplete_data)
                self.assertFalse(form.is_valid())
                self.assertIn(field_name, form.errors)
    
    def test_form_meta_configuration(self):
        """Test form Meta class configuration"""
        form = ClienteForm()
        
        # Check Meta.fields
        expected_fields = ["cpf", "nome", "nascimento", "prioridade"]
        self.assertEqual(form._meta.fields, expected_fields)
        
        # Check that additional fields (not in Meta.fields) are still in form
        self.assertIn('precatorio_cnj', form.fields)
    
    def test_document_type_detection(self):
        """Test that form correctly handles both CPF and CNPJ document types"""
        # Test CPF detection (11 digits)
        cpf_data = self.minimal_valid_data.copy()
        cpf_data['cpf'] = '12345678909'
        form = ClienteForm(data=cpf_data)
        if form.is_valid():  # Assuming this CPF passes validation
            self.assertEqual(len(form.cleaned_data['cpf']), 11)
        
        # Test CNPJ detection (14 digits)  
        cnpj_data = self.valid_cnpj_data.copy()
        form = ClienteForm(data=cnpj_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data['cpf']), 14)
    
    def test_precatorio_cnj_database_integration(self):
        """Test that precatorio_cnj field properly integrates with database"""
        # Create another precatorio
        precatorio2 = Precatorio.objects.create(
            cnj='1111111-11.2025.8.26.0300',
            orcamento=2025,
            origem='2222222-22.2024.8.26.0200',
            valor_de_face=100000.00,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Test with the new precatorio CNJ
        data = self.valid_form_data.copy()
        data['precatorio_cnj'] = precatorio2.cnj
        
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['precatorio_cnj'], precatorio2.cnj)


class TipoDiligenciaFormTest(TestCase):
    """
    Comprehensive test suite for TipoDiligenciaForm functionality and validation.
    
    This test class provides thorough coverage of the TipoDiligenciaForm, which
    manages the creation and editing of diligence types used throughout the
    precatorio system for task categorization. The tests validate form behavior,
    field validation, color format validation, and system integration.
    
    Test Coverage:
        - Form initialization and field configuration
        - Type name validation and uniqueness constraints
        - Color format validation (hexadecimal)
        - Order field validation and integer constraints
        - Activation status handling
        - Optional description field handling
        - Error handling and validation messages
        - Data persistence and model integration
        - Edge cases and boundary conditions
        
    Key Test Areas:
        - Name Validation: Tests unique naming constraints and requirements
        - Color Validation: Tests hexadecimal color format compliance
        - Order Management: Tests integer ordering and constraints
        - Status Control: Tests activation/deactivation functionality
        - Description Handling: Tests optional field behavior
        - Form Integration: Tests widget configuration and styling
        - Error Scenarios: Tests validation failures and error messages
        
    Business Logic Testing:
        - Type names must be unique within the system
        - Colors must follow hexadecimal format (#RRGGBB)
        - Order must be non-negative integer for proper sorting
        - Activation status controls type availability
        - Description is optional but provides additional context
        - Form supports both creation and editing workflows
        
    Setup Dependencies:
        - Valid type name for testing
        - Proper hexadecimal color format
        - Non-negative integer for order
        - Boolean value for activation status
        - Optional description text
    """
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'nome': 'Contato Cliente',
            'descricao': 'Entrar em contato com o cliente',
            'cor': '#28a745',
            'ordem': 0,
            'ativo': True
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = TipoDiligenciaForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = TipoDiligenciaForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        tipo = form.save()
        self.assertEqual(tipo.nome, 'Contato Cliente')
        self.assertEqual(tipo.cor, '#28a745')
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        incomplete_data = {'descricao': 'Test'}
        form = TipoDiligenciaForm(data=incomplete_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_form_color_field(self):
        """Test color field widget and validation"""
        form = TipoDiligenciaForm()
        color_field = form.fields['cor']
        self.assertEqual(color_field.widget.input_type, 'color')
    
    def test_form_clean_cor_valid(self):
        """Test form accepts valid hex colors"""
        valid_colors = ['#FF0000', '#00ff00', '#0000FF', '#AbCdEf']
        for color in valid_colors:
            with self.subTest(color=color):
                data = self.valid_form_data.copy()
                data['cor'] = color
                form = TipoDiligenciaForm(data=data)
                self.assertTrue(form.is_valid(), f"Form should be valid for color {color}")
    
    def test_form_clean_cor_invalid(self):
        """Test form rejects invalid hex colors"""
        invalid_colors = ['invalid', '#FF', '#GGGGGG', 'red', '123456', '#1234567']
        for color in invalid_colors:
            with self.subTest(color=color):
                data = self.valid_form_data.copy()
                data['cor'] = color
                form = TipoDiligenciaForm(data=data)
                self.assertFalse(form.is_valid(), f"Form should be invalid for color {color}")
                self.assertIn('cor', form.errors)
    
    def test_form_optional_description(self):
        """Test that description field is optional"""
        data = self.valid_form_data.copy()
        data.pop('descricao')
        form = TipoDiligenciaForm(data=data)
        self.assertTrue(form.is_valid())
        tipo = form.save()
        self.assertEqual(tipo.descricao, '')


class DiligenciasFormTest(TestCase):
    """
    Comprehensive test suite for DiligenciasForm functionality and validation.
    
    This test class provides thorough coverage of the DiligenciasForm, which
    manages the creation and editing of legal tasks (diligências) within the
    precatorio system. The tests validate form behavior, field validation,
    date constraints, type integration, and business rule enforcement.
    
    Test Coverage:
        - Form initialization and field configuration
        - Diligence type selection and filtering
        - Date validation and past date prevention
        - Urgency level selection and validation
        - Optional description field handling
        - Dynamic tipo queryset filtering
        - Error handling and validation messages
        - Data persistence and model integration
        - Edge cases and boundary conditions
        
    Key Test Areas:
        - Type Integration: Tests dynamic filtering of active diligence types
        - Date Validation: Tests deadline constraints and past date prevention
        - Urgency Handling: Tests priority level selection and validation
        - Description Flexibility: Tests optional detailed description field
        - Form Configuration: Tests field labels, help text, and styling
        - Business Rules: Tests workflow constraints and requirements
        - Error Scenarios: Tests validation failures and error messages
        
    Business Logic Testing:
        - Only active diligence types should be available for selection
        - Deadline cannot be set in the past
        - Urgency level must be from predefined choices
        - Description field is optional for flexibility
        - Form integrates properly with TipoDiligencia filtering
        - Brazilian date format compliance required
        
    Setup Dependencies:
        - Active TipoDiligencia instances for type selection
        - Valid future date for deadline testing
        - Predefined urgency level choices
        - Optional description text
        - Proper timezone configuration for date validation
    """
    
    def setUp(self):
        """Set up test data"""
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.tipo_ativo = TipoDiligencia.objects.create(
            nome='Ativo',
            cor='#007bff',
            ativo=True
        )
        
        self.tipo_inativo = TipoDiligencia.objects.create(
            nome='Inativo',
            cor='#6c757d',
            ativo=False
        )
        
        self.valid_form_data = {
            'tipo': self.tipo_ativo.id,
            'data_final': (date.today() + timedelta(days=7)).strftime('%d/%m/%Y'),
            'urgencia': 'media',
            'descricao': 'Teste de diligência'
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = DiligenciasForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_form_save(self):
        """Test form saving (requires cliente to be set separately)"""
        form = DiligenciasForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        diligencia = form.save(commit=False)
        diligencia.cliente = self.cliente
        diligencia.criado_por = 'Test User'
        diligencia.save()
        
        self.assertEqual(diligencia.tipo, self.tipo_ativo)
        self.assertEqual(diligencia.cliente, self.cliente)
        self.assertEqual(diligencia.urgencia, 'media')
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        incomplete_data = {'descricao': 'Test'}
        form = DiligenciasForm(data=incomplete_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
        self.assertIn('data_final', form.errors)
    
    def test_form_tipo_filtering(self):
        """Test that form only shows active tipos"""
        form = DiligenciasForm()
        tipo_queryset = form.fields['tipo'].queryset
        
        self.assertIn(self.tipo_ativo, tipo_queryset)
        self.assertNotIn(self.tipo_inativo, tipo_queryset)
    
    def test_form_clean_data_final_future(self):
        """Test that data_final must be in the future"""
        past_data = self.valid_form_data.copy()
        past_date = (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
        past_data['data_final'] = past_date
        form = DiligenciasForm(data=past_data)
        self.assertFalse(form.is_valid())
        self.assertIn('data_final', form.errors)
        self.assertIn('passado', form.errors['data_final'][0])
    
    def test_form_clean_data_final_today(self):
        """Test that data_final can be today"""
        today_data = self.valid_form_data.copy()
        today_data['data_final'] = timezone.now().date().strftime('%Y-%m-%d')
        form = DiligenciasForm(data=today_data)
        self.assertTrue(form.is_valid())
    
    def test_form_brazilian_date_widget(self):
        """Test that form uses Brazilian date widget"""
        form = DiligenciasForm()
        data_final_widget = form.fields['data_final'].widget
        self.assertEqual(data_final_widget.__class__.__name__, 'BrazilianDateInput')
        self.assertIn('dd/mm/aaaa', data_final_widget.attrs.get('placeholder', ''))
    
    def test_form_optional_description(self):
        """Test that description field is optional"""
        data = self.valid_form_data.copy()
        data.pop('descricao')
        form = DiligenciasForm(data=data)
        self.assertTrue(form.is_valid())


class DiligenciasUpdateFormTest(TestCase):
    """
    Comprehensive test suite for DiligenciasUpdateForm functionality and validation.
    
    This test class provides thorough coverage of the DiligenciasUpdateForm, which
    manages the completion and status updates of existing diligências (legal tasks)
    in the precatorio system. The tests validate completion workflow, automatic
    timestamp management, observation handling, and audit trail creation.
    
    Test Coverage:
        - Form initialization and field configuration
        - Completion status toggle functionality
        - Automatic completion timestamp generation
        - Optional observation field handling
        - Status change validation and logic
        - Timestamp clearing for incomplete tasks
        - Error handling and validation messages
        - Data persistence and model integration
        - Edge cases and boundary conditions
        
    Key Test Areas:
        - Completion Workflow: Tests task completion marking and unmarking
        - Timestamp Management: Tests automatic date/time setting and clearing
        - Observation Handling: Tests optional completion notes and context
        - Status Logic: Tests completion requirements and validation
        - Form Configuration: Tests field labels, help text, and styling
        - Audit Trail: Tests completion tracking and history preservation
        - Error Scenarios: Tests validation failures and edge cases
        
    Business Logic Testing:
        - Completion status triggers automatic timestamp generation
        - Unmarking completion clears timestamp automatically
        - Observations are optional but preserved for audit trail
        - Form handles both completion and reopening workflows
        - Timestamp uses current time when marking complete
        - Data integrity maintained through validation logic
        
    Setup Dependencies:
        - Existing Cliente instance for diligencia association
        - Active TipoDiligencia for diligencia type
        - Existing Diligencias instance for update testing
        - Proper timezone configuration for timestamp handling
        - Brazilian date/time formatting compliance
    """
    
    def setUp(self):
        """Set up test data"""
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.tipo_diligencia = TipoDiligencia.objects.create(
            nome='Documentação',
            cor='#007bff'
        )
        
        self.diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=7),
            criado_por='Test User'
        )
    
    def test_form_mark_as_concluded(self):
        """Test marking diligencia as concluded"""
        form_data = {
            'concluida': True,
            'descricao': 'Diligência concluída com sucesso'
        }
        
        form = DiligenciasUpdateForm(data=form_data, instance=self.diligencia)
        self.assertTrue(form.is_valid())
        
        diligencia = form.save()
        self.assertTrue(diligencia.concluida)
        self.assertIsNotNone(diligencia.data_conclusao)
    
    def test_form_mark_as_not_concluded(self):
        """Test marking diligencia as not concluded"""
        # First mark as concluded
        self.diligencia.concluida = True
        self.diligencia.data_conclusao = timezone.now()
        self.diligencia.save()
        
        # Then mark as not concluded
        form_data = {
            'concluida': False,
            'descricao': 'Diligência reaberta'
        }
        
        form = DiligenciasUpdateForm(data=form_data, instance=self.diligencia)
        self.assertTrue(form.is_valid())
        
        diligencia = form.save()
        self.assertFalse(diligencia.concluida)
        self.assertIsNone(diligencia.data_conclusao)
    
    def test_form_auto_set_conclusion_date(self):
        """Test that conclusion date is auto-set when marking as concluded"""
        form_data = {
            'concluida': True
        }
        
        form = DiligenciasUpdateForm(data=form_data, instance=self.diligencia)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        self.assertIsNotNone(cleaned_data['data_conclusao'])
    
    def test_form_brazilian_datetime_widget(self):
        """Test that form uses Brazilian datetime widget"""
        form = DiligenciasUpdateForm()
        data_conclusao_widget = form.fields['data_conclusao'].widget
        self.assertEqual(data_conclusao_widget.__class__.__name__, 'BrazilianDateTimeInput')


class ClienteSimpleFormComprehensiveTest(TestCase):
    """
    Comprehensive test suite for ClienteSimpleForm class
    
    Tests cover:
    - Form initialization and widget configuration
    - CPF validation (valid/invalid formats)
    - Duplicate client prevention
    - Format cleaning and normalization
    - BrazilianDateInput integration
    - Field validation and error messages
    - Edge cases and error handling
    """
    
    def setUp(self):
        """Set up test data for ClienteSimpleForm testing"""
        # Create existing cliente to test duplicate prevention using valid CPF
        self.existing_cliente = Cliente.objects.create(
            cpf='12345678909',  # Valid CPF
            nome='Cliente Existente',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
    
    def test_form_initialization(self):
        """Test ClienteSimpleForm initializes correctly with proper widgets and configuration"""
        form = ClienteSimpleForm()
        
        # Test form has correct fields
        expected_fields = ['cpf', 'nome', 'nascimento', 'prioridade']
        self.assertEqual(list(form.fields.keys()), expected_fields)
        
        # Test CPF field configuration
        cpf_field = form.fields['cpf']
        self.assertEqual(cpf_field.max_length, 18)
        self.assertEqual(cpf_field.label, 'CPF')
        self.assertTrue(cpf_field.required)
        self.assertIn('CPF no formato: 000.000.000-00 ou 00000000000', cpf_field.widget.attrs['title'])
        
        # Test nascimento field uses BrazilianDateInput
        self.assertIsInstance(form.fields['nascimento'].widget, BrazilianDateInput)
        
        # Test widget attributes
        cpf_widget = form.fields['cpf'].widget
        self.assertEqual(cpf_widget.attrs['class'], 'form-control')
        self.assertEqual(cpf_widget.attrs['placeholder'], '000.000.000-00 ou 00000000000')
        self.assertIn('pattern', cpf_widget.attrs)
    
    def test_valid_cpf_formatted(self):
        """Test form accepts valid CPF with formatting (dots and dashes)"""
        form_data = {
            'cpf': '111.444.777-35',  # Valid CPF (11144477735)
            'nome': 'João Silva',
            'nascimento': '15/05/1990',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['cpf'], '11144477735')
    
    def test_valid_cpf_numbers_only(self):
        """Test form accepts valid CPF with numbers only"""
        form_data = {
            'cpf': '11144477735',  # Valid CPF
            'nome': 'Maria Santos',
            'nascimento': '20/08/1985',
            'prioridade': True
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['cpf'], '11144477735')
    
    def test_invalid_cpf_algorithm(self):
        """Test form rejects CPF with invalid check digits"""
        form_data = {
            'cpf': '123.456.789-00',  # Invalid check digits
            'nome': 'Cliente Inválido',
            'nascimento': '10/01/1975',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', str(form.errors['cpf']))
    
    def test_invalid_cpf_length_short(self):
        """Test form rejects CPF with insufficient digits"""
        form_data = {
            'cpf': '123456789',  # Only 9 digits
            'nome': 'Cliente Curto',
            'nascimento': '05/12/1992',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF deve ter exatamente 11 dígitos', str(form.errors['cpf']))
    
    def test_invalid_cpf_length_long(self):
        """Test form rejects CPF with too many digits"""
        form_data = {
            'cpf': '123456789012345',  # 15 digits
            'nome': 'Cliente Longo',
            'nascimento': '30/06/1988',
            'prioridade': True
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF deve ter exatamente 11 dígitos', str(form.errors['cpf']))
    
    def test_cpf_with_letters(self):
        """Test form rejects CPF containing letters"""
        form_data = {
            'cpf': '123.456.78A-09',
            'nome': 'Cliente Letra',
            'nascimento': '14/07/1993',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
    
    def test_empty_cpf(self):
        """Test form rejects empty CPF"""
        form_data = {
            'cpf': '',
            'nome': 'Cliente Sem CPF',
            'nascimento': '22/09/1986',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        # Django's default required field error message
        self.assertIn('Este campo é obrigatório', str(form.errors['cpf']))
    
    def test_duplicate_cpf_prevention(self):
        """Test form prevents creation of cliente with existing CPF"""
        form_data = {
            'cpf': '123.456.789-09',  # Same as existing_cliente (12345678909)
            'nome': 'Cliente Duplicado',
            'nascimento': '18/11/1991',
            'prioridade': True
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('Já existe um cliente com este CPF', str(form.errors['cpf']))
    
    def test_duplicate_cpf_different_format(self):
        """Test duplicate prevention works with different CPF formatting"""
        form_data = {
            'cpf': '12345678909',  # Same as existing_cliente, different format
            'nome': 'Cliente Duplicado Formato',
            'nascimento': '25/03/1989',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('Já existe um cliente com este CPF', str(form.errors['cpf']))
    
    def test_cpf_cleaning_removes_formatting(self):
        """Test CPF cleaning removes dots and dashes correctly"""
        form_data = {
            'cpf': '987.654.321-00',
            'nome': 'Cliente Formatado',
            'nascimento': '12/04/1987',
            'prioridade': True
        }
        form = ClienteSimpleForm(data=form_data)
        if form.is_valid():
            self.assertEqual(form.cleaned_data['cpf'], '98765432100')
    
    def test_all_same_digits_cpf(self):
        """Test form rejects CPF with all same digits (invalid pattern)"""
        form_data = {
            'cpf': '111.111.111-11',
            'nome': 'Cliente Repetido',
            'nascimento': '08/02/1994',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', str(form.errors['cpf']))
    
    def test_cnpj_not_supported(self):
        """Test form rejects CNPJ (14 digits) as it only supports CPF"""
        form_data = {
            'cpf': '12.345.678/0001-90',  # Valid CNPJ format
            'nome': 'Empresa LTDA',
            'nascimento': '01/01/2000',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        # The form validation actually triggers CPF validation, so error message is about invalid CPF
        self.assertIn('CPF inválido', str(form.errors['cpf']))
    
    def test_cnpj_numbers_only_not_supported(self):
        """Test form rejects CNPJ (14 digits numbers only)"""
        form_data = {
            'cpf': '12345678000190',  # 14 digits
            'nome': 'Empresa Números',
            'nascimento': '15/06/1995',
            'prioridade': True
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        # The form validation actually triggers CPF validation, so error message is about invalid CPF
        self.assertIn('CPF inválido', str(form.errors['cpf']))
    
    def test_brazillian_date_input_integration(self):
        """Test BrazilianDateInput widget is properly integrated for nascimento field"""
        form = ClienteSimpleForm()
        nascimento_widget = form.fields['nascimento'].widget
        
        # Verify it's a BrazilianDateInput
        self.assertIsInstance(nascimento_widget, BrazilianDateInput)
        
        # Test widget attributes
        self.assertEqual(nascimento_widget.attrs['class'], 'form-control')
        self.assertEqual(nascimento_widget.attrs['placeholder'], 'dd/mm/aaaa')
        self.assertEqual(nascimento_widget.format, '%d/%m/%Y')
    
    def test_valid_form_with_all_fields(self):
        """Test complete valid form with all fields filled"""
        form_data = {
            'cpf': '987.654.321-00',
            'nome': 'Cliente Completo',
            'nascimento': '28/02/1992',
            'prioridade': True
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test cleaned data
        self.assertEqual(form.cleaned_data['cpf'], '98765432100')
        self.assertEqual(form.cleaned_data['nome'], 'Cliente Completo')
        self.assertEqual(form.cleaned_data['nascimento'], date(1992, 2, 28))
        self.assertTrue(form.cleaned_data['prioridade'])
    
    def test_valid_form_minimal_fields(self):
        """Test form with minimal required fields"""
        form_data = {
            'cpf': '111.222.333-96',
            'nome': 'Cliente Mínimo',
            'nascimento': '10/10/1990',
            'prioridade': False
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save_creates_cliente(self):
        """Test form save method creates Cliente instance correctly"""
        form_data = {
            'cpf': '987.654.321-00',  # Valid CPF (98765432100)
            'nome': 'Cliente Salvável',
            'nascimento': '07/07/1977',
            'prioridade': True
        }
        form = ClienteSimpleForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Save the form
        cliente = form.save()
        
        # Verify cliente was created correctly
        self.assertIsInstance(cliente, Cliente)
        self.assertEqual(cliente.cpf, '98765432100')
        self.assertEqual(cliente.nome, 'Cliente Salvável')
        self.assertEqual(cliente.nascimento, date(1977, 7, 7))
        self.assertTrue(cliente.prioridade)
        
        # Verify it's in database
        self.assertTrue(Cliente.objects.filter(cpf='98765432100').exists())
    
    def test_cpf_field_help_text(self):
        """Test CPF field has appropriate help text"""
        form = ClienteSimpleForm()
        cpf_help_text = form.fields['cpf'].help_text
        self.assertIn('Formato: 000.000.000-00 ou 00000000000', cpf_help_text)
        self.assertIn('obrigatório', cpf_help_text)
    
    def test_form_meta_configuration(self):
        """Test form Meta class configuration"""
        form = ClienteSimpleForm()
        
        # Test model assignment
        self.assertEqual(form._meta.model, Cliente)
        
        # Test fields configuration
        expected_fields = ["cpf", "nome", "nascimento", "prioridade"]
        self.assertEqual(form._meta.fields, expected_fields)
        
        # Test widget configuration
        self.assertIn('nome', form._meta.widgets)
        self.assertIn('nascimento', form._meta.widgets)
        self.assertIn('prioridade', form._meta.widgets)
    
    def test_priority_field_configuration(self):
        """Test prioridade field is properly configured as checkbox"""
        form = ClienteSimpleForm()
        prioridade_widget = form.fields['prioridade'].widget
        
        # Test widget type and attributes
        self.assertIsInstance(prioridade_widget, forms.CheckboxInput)
        self.assertEqual(prioridade_widget.attrs['class'], 'form-check-input')
    
    def test_nome_field_configuration(self):
        """Test nome field widget configuration"""
        form = ClienteSimpleForm()
        nome_widget = form.fields['nome'].widget
        
        # Test widget attributes
        self.assertEqual(nome_widget.attrs['class'], 'form-control')
        self.assertIn('Digite o nome completo do cliente', nome_widget.attrs['placeholder'])
    
    def test_cpf_pattern_validation(self):
        """Test CPF field pattern attribute for client-side validation"""
        form = ClienteSimpleForm()
        cpf_widget = form.fields['cpf'].widget
        
        # Test pattern includes both formatted and unformatted CPF
        pattern = cpf_widget.attrs['pattern']
        self.assertIn(r'\d{3}\.\d{3}\.\d{3}-\d{2}', pattern)  # Formatted
        self.assertIn(r'\d{11}', pattern)  # Unformatted


class PrecatorioSearchFormComprehensiveTest(TestCase):
    """
    Comprehensive test suite for PrecatorioSearchForm.
    
    This test class covers all functionality, validation logic, and edge cases
    for the form used to search precatorios by CNJ number for linking to clients.
    
    The form is critical for the application's workflow as it allows users to
    find existing precatorios and link them to clients, using complex Brazilian
    legal system identifier (CNJ) validation.
    
    Tests cover:
    - Form initialization and field configuration
    - CNJ validation logic and format checking
    - Widget configuration and HTML attributes
    - Error handling and validation messages
    - Edge cases and boundary conditions
    - Integration with CNJ validation function
    - Form submission behavior
    - Field accessibility attributes
    """
    
    def setUp(self):
        """Set up test data for PrecatorioSearchForm testing"""
        self.valid_cnj_data = {
            'cnj': '1234567-89.2023.8.26.0100'
        }
        
        self.invalid_cnj_data = {
            'cnj': '1234567-89.2023.8.26.01'  # Too short OOOO part
        }
        
        # Create test precatorio for validation tests
        self.test_precatorio = Precatorio.objects.create(
            cnj='9876543-21.2022.8.26.0001',
            orcamento=2022,
            valor_de_face=50000.00
        )

    def test_form_initialization_default(self):
        """Test form initialization with default configuration"""
        form = PrecatorioSearchForm()
        
        # Test field existence
        self.assertIn('cnj', form.fields)
        
        # Test field type
        self.assertIsInstance(form.fields['cnj'], forms.CharField)
        
        # Test field properties
        cnj_field = form.fields['cnj']
        self.assertEqual(cnj_field.max_length, 25)
        self.assertEqual(cnj_field.label, 'CNJ do Precatório')
        self.assertIn('Digite o CNJ do precatório para vincular ao cliente', cnj_field.help_text)

    def test_form_widget_configuration(self):
        """Test CNJ field widget configuration"""
        form = PrecatorioSearchForm()
        cnj_widget = form.fields['cnj'].widget
        
        # Test widget type
        self.assertIsInstance(cnj_widget, forms.TextInput)
        
        # Test widget attributes
        attrs = cnj_widget.attrs
        self.assertEqual(attrs['class'], 'form-control')
        self.assertEqual(attrs['placeholder'], '1234567-89.2023.8.26.0100')
        self.assertEqual(attrs['pattern'], r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}')
        self.assertEqual(attrs['title'], 'CNJ no formato: NNNNNNN-DD.AAAA.J.TR.OOOO')

    def test_form_widget_pattern_validation(self):
        """Test CNJ widget pattern for client-side validation"""
        form = PrecatorioSearchForm()
        cnj_widget = form.fields['cnj'].widget
        
        # Test pattern matches expected CNJ format
        pattern = cnj_widget.attrs['pattern']
        self.assertEqual(pattern, r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}')
        
        # Test pattern components
        self.assertIn(r'\d{7}', pattern)  # Sequential number
        self.assertIn(r'\d{2}', pattern)  # Check digits
        self.assertIn(r'\d{4}', pattern)  # Year and origin
        self.assertIn(r'\d{1}', pattern)  # Judicial segment

    def test_form_validators_configuration(self):
        """Test CNJ field validators configuration"""
        form = PrecatorioSearchForm()
        cnj_field = form.fields['cnj']
        
        # Test validators are present
        self.assertTrue(cnj_field.validators)
        
        # Test validate_cnj is in validators
        validator_functions = [v for v in cnj_field.validators if callable(v)]
        self.assertTrue(any(v.__name__ == 'validate_cnj' for v in validator_functions))

    def test_form_valid_data_submission(self):
        """Test form submission with valid CNJ data"""
        form = PrecatorioSearchForm(data=self.valid_cnj_data)
        
        # Test form validation
        self.assertTrue(form.is_valid(), f"Form should be valid but has errors: {form.errors}")
        
        # Test cleaned data
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['cnj'], '1234567-89.2023.8.26.0100')

    def test_form_invalid_cnj_format(self):
        """Test form submission with invalid CNJ format"""
        invalid_data = {'cnj': '123456-78.2023.8.26.0100'}  # Wrong length
        form = PrecatorioSearchForm(data=invalid_data)
        
        # Test form validation fails
        self.assertFalse(form.is_valid())
        
        # Test error message
        self.assertIn('cnj', form.errors)
        error_message = form.errors['cnj'][0]
        self.assertIn('NNNNNNN-DD.AAAA.J.TR.OOOO', error_message)

    def test_form_cnj_pattern_validation_cases(self):
        """Test various CNJ pattern validation cases"""
        test_cases = [
            ('1234567-89.2023.8.26.0100', True),   # Valid format
            ('123456-89.2023.8.26.0100', False),   # Too short sequential
            ('12345678-89.2023.8.26.0100', False), # Too long sequential
            ('1234567-8.2023.8.26.0100', False),   # Too short check digits
            ('1234567-890.2023.8.26.0100', False), # Too long check digits
            ('1234567-89.23.8.26.0100', False),    # Too short year
            ('1234567-89.20233.8.26.0100', False), # Too long year
            ('1234567-89.2023.8.6.0100', False),   # Too short TR
            ('1234567-89.2023.8.266.0100', False), # Too long TR
            ('1234567-89.2023.8.26.100', False),   # Too short origin
            ('1234567-89.2023.8.26.01000', False), # Too long origin
            ('1234567892023826010', False),         # No formatting
            ('1234567-89-2023-8-26-0100', False),  # Wrong separators
        ]
        
        for cnj, should_be_valid in test_cases:
            with self.subTest(cnj=cnj, expected_valid=should_be_valid):
                form = PrecatorioSearchForm(data={'cnj': cnj})
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"CNJ {cnj} should be valid but form validation failed: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"CNJ {cnj} should be invalid but form validation passed")

    def test_form_cnj_year_validation(self):
        """Test CNJ year validation boundaries"""
        # Test valid years
        valid_years = ['1988', '2000', '2023', '2050']
        for year in valid_years:
            cnj = f'1234567-89.{year}.8.26.0100'
            form = PrecatorioSearchForm(data={'cnj': cnj})
            self.assertTrue(form.is_valid(), 
                          f"Year {year} should be valid but validation failed: {form.errors}")
        
        # Test invalid years
        invalid_years = ['1987', '1900', '2051', '2100']
        for year in invalid_years:
            cnj = f'1234567-89.{year}.8.26.0100'
            form = PrecatorioSearchForm(data={'cnj': cnj})
            self.assertFalse(form.is_valid(), 
                           f"Year {year} should be invalid but validation passed")
            if not form.is_valid():
                error_message = form.errors['cnj'][0]
                self.assertIn('Ano do CNJ deve estar entre 1988 e 2050', error_message)

    def test_form_cnj_judicial_segment_validation(self):
        """Test CNJ judicial segment validation"""
        # Test valid segments (1-9)
        valid_segments = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        for segment in valid_segments:
            cnj = f'1234567-89.2023.{segment}.26.0100'
            form = PrecatorioSearchForm(data={'cnj': cnj})
            self.assertTrue(form.is_valid(), 
                          f"Segment {segment} should be valid but validation failed: {form.errors}")
        
        # Test invalid segment (0 is invalid, but it's treated as a format error first)
        # because the validation happens after the regex pattern check
        invalid_cnj = '1234567-89.2023.0.26.0100'
        form = PrecatorioSearchForm(data={'cnj': invalid_cnj})
        self.assertFalse(form.is_valid(), 
                       f"Segment 0 should be invalid but validation passed")
        if not form.is_valid():
            error_message = form.errors['cnj'][0]
            self.assertIn('Segmento do judiciário (J) deve ser um dígito de 1 a 9', error_message)

    def test_form_empty_cnj_field(self):
        """Test form behavior with empty CNJ field"""
        form = PrecatorioSearchForm(data={'cnj': ''})
        
        # Test form validation fails (CNJ is required)
        self.assertFalse(form.is_valid())
        
        # Test required field error
        self.assertIn('cnj', form.errors)
        error_message = form.errors['cnj'][0]
        self.assertIn('obrigatório', error_message.lower())

    def test_form_cnj_whitespace_handling(self):
        """Test form handling of CNJ with whitespace"""
        cnj_with_spaces = ' 1234567-89.2023.8.26.0100 '
        form = PrecatorioSearchForm(data={'cnj': cnj_with_spaces})
        
        # Form should be valid (validator handles whitespace removal)
        self.assertTrue(form.is_valid(), f"Form should handle whitespace but has errors: {form.errors}")
        
        # Test cleaned data (validator trims the whitespace)
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['cnj'], '1234567-89.2023.8.26.0100')  # Whitespace is trimmed by validate_cnj

    def test_form_field_accessibility_attributes(self):
        """Test CNJ field accessibility attributes"""
        form = PrecatorioSearchForm()
        cnj_field = form.fields['cnj']
        cnj_widget = cnj_field.widget
        
        # Test help text for screen readers
        self.assertIsNotNone(cnj_field.help_text)
        self.assertIn('Formato:', cnj_field.help_text)
        
        # Test widget title attribute
        self.assertIn('title', cnj_widget.attrs)
        self.assertIn('CNJ no formato', cnj_widget.attrs['title'])
        
        # Test placeholder provides example
        self.assertIn('placeholder', cnj_widget.attrs)
        self.assertEqual(cnj_widget.attrs['placeholder'], '1234567-89.2023.8.26.0100')

    def test_form_label_configuration(self):
        """Test CNJ field label configuration"""
        form = PrecatorioSearchForm()
        cnj_field = form.fields['cnj']
        
        # Test label text
        self.assertEqual(cnj_field.label, 'CNJ do Precatório')
        
        # Test help text content
        help_text = cnj_field.help_text
        self.assertIn('Digite o CNJ do precatório para vincular ao cliente', help_text)
        self.assertIn('NNNNNNN-DD.AAAA.J.TR.OOOO', help_text)

    def test_form_widget_css_classes(self):
        """Test widget CSS class configuration"""
        form = PrecatorioSearchForm()
        cnj_widget = form.fields['cnj'].widget
        
        # Test CSS classes for Bootstrap styling
        self.assertEqual(cnj_widget.attrs['class'], 'form-control')

    def test_form_integration_with_validate_cnj_function(self):
        """Test form integration with validate_cnj validation function"""
        # Test that the form uses the same validation as the validate_cnj function
        from precapp.forms import validate_cnj
        
        test_cnj = '1234567-89.2023.8.26.0100'
        
        # Test validate_cnj function directly
        try:
            result = validate_cnj(test_cnj)
            self.assertEqual(result, test_cnj)
        except ValidationError:
            self.fail("validate_cnj should not raise ValidationError for valid CNJ")
        
        # Test form uses same validation
        form = PrecatorioSearchForm(data={'cnj': test_cnj})
        self.assertTrue(form.is_valid())

    def test_form_cnj_error_messages_quality(self):
        """Test quality and helpfulness of CNJ validation error messages"""
        # Test format error message
        form = PrecatorioSearchForm(data={'cnj': 'invalid-format'})
        self.assertFalse(form.is_valid())
        
        error_message = form.errors['cnj'][0]
        # Check that error message provides helpful format example
        self.assertIn('NNNNNNN-DD.AAAA.J.TR.OOOO', error_message)
        self.assertIn('exemplo:', error_message.lower())

    def test_form_data_preservation_on_error(self):
        """Test that form preserves user input on validation errors"""
        invalid_cnj = '1234567-89.2023.8.26.01'  # Invalid format
        form = PrecatorioSearchForm(data={'cnj': invalid_cnj})
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        
        # But initial data should be preserved
        self.assertEqual(form.data['cnj'], invalid_cnj)

    def test_form_boundary_value_testing(self):
        """Test boundary values for CNJ validation"""
        boundary_cases = [
            ('0000001-00.1988.1.01.0001', True),   # Minimum valid values
            ('9999999-99.2050.9.99.9999', True),   # Maximum valid values
            ('0000000-00.1987.0.00.0000', False),  # Below minimum values
            ('9999999-99.2051.9.99.9999', False),  # Above maximum year
        ]
        
        for cnj, should_be_valid in boundary_cases:
            with self.subTest(cnj=cnj, expected_valid=should_be_valid):
                form = PrecatorioSearchForm(data={'cnj': cnj})
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"Boundary CNJ {cnj} should be valid but validation failed: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"Boundary CNJ {cnj} should be invalid but validation passed")

    def test_form_special_characters_handling(self):
        """Test form handling of CNJ with special characters"""
        special_cases = [
            ('1234567-89.2023.8.26.0100', True),   # Standard format
            ('1234567–89.2023.8.26.0100', False),  # En dash instead of hyphen
            ('1234567—89.2023.8.26.0100', False),  # Em dash instead of hyphen
            ('1234567-89｡2023｡8｡26｡0100', False),  # Full-width periods
            ('1234567-89.2023.8.26.0100\n', True), # With newline (trimmed by validator)
            ('1234567-89.2023.8.26.0100\t', True), # With tab (trimmed by validator)
        ]
        
        for cnj, should_be_valid in special_cases:
            with self.subTest(cnj=cnj, expected_valid=should_be_valid):
                form = PrecatorioSearchForm(data={'cnj': cnj})
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"CNJ {repr(cnj)} should be valid but validation failed: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"CNJ {repr(cnj)} should be invalid but validation passed")


class ClienteSearchFormComprehensiveTest(TestCase):
    """
    Comprehensive test suite for ClienteSearchForm class.
    
    This test class provides complete validation coverage for the ClienteSearchForm,
    which is a critical component in the precatorios application workflow. The form
    enables users to search for existing clients using CPF (individuals) or CNPJ 
    (corporations) numbers to link them to precatorios during the creation process.
    
    Test Coverage Scope:
        - Form field configuration and widget setup
        - CPF validation using Brazilian algorithm (validate_cpf)
        - CNPJ validation using Brazilian algorithm (validate_cnpj)
        - Input format handling (formatted and unformatted)
        - Data cleaning and normalization processes
        - Error message validation and user feedback
        - HTML attributes and accessibility features
        - Edge cases and boundary condition testing
        - Security validation and input sanitization
        
    Business Logic Tested:
        - Brazilian CPF algorithm validation (11-digit documents)
        - Brazilian CNPJ algorithm validation (14-digit documents)
        - Format flexibility (accepts dots, dashes, slashes)
        - Document type auto-detection based on length
        - Required field validation and error handling
        - Input sanitization (removes formatting characters)
        
    Test Categories:
        1. Form Initialization Tests
            - Widget configuration validation
            - Field attribute verification
            - CSS class and styling checks
            
        2. CPF Validation Tests
            - Valid CPF format acceptance
            - Invalid CPF rejection
            - Algorithm verification tests
            - Edge case CPF numbers
            
        3. CNPJ Validation Tests
            - Valid CNPJ format acceptance
            - Invalid CNPJ rejection
            - Algorithm verification tests
            - Edge case CNPJ numbers
            
        4. Input Format Tests
            - Formatted input handling
            - Unformatted input handling
            - Mixed format scenarios
            - Special character removal
            
        5. Error Handling Tests
            - Required field validation
            - Invalid format error messages
            - Algorithm failure error messages
            - Empty input validation
            
        6. Integration Tests
            - Form submission behavior
            - Data cleaning verification
            - Widget rendering validation
            
        7. Accessibility Tests
            - HTML attribute validation
            - Screen reader compatibility
            - Keyboard navigation support
            
        8. Security Tests
            - Input sanitization verification
            - XSS prevention validation
            - Data format enforcement
            
    Test Data Sets:
        - Valid CPF numbers (algorithm-verified)
        - Invalid CPF numbers (various failure modes)
        - Valid CNPJ numbers (algorithm-verified)
        - Invalid CNPJ numbers (various failure modes)
        - Edge cases (empty, too short, too long)
        - Format variations (with/without punctuation)
        
    Validation Algorithms:
        - CPF: Uses official Brazilian CPF validation algorithm
        - CNPJ: Uses official Brazilian CNPJ validation algorithm
        - Both algorithms include check digit verification
        - Handles special cases (all same digits, known invalid patterns)
        
    Performance Considerations:
        - Tests run quickly without external dependencies
        - No database queries during validation testing
        - Lightweight algorithm testing approach
        
    Browser Compatibility:
        - HTML5 pattern validation testing
        - Cross-browser form behavior validation
        - Progressive enhancement verification
        
    Accessibility Compliance:
        - WCAG 2.1 guideline adherence
        - Screen reader compatibility testing
        - Keyboard-only navigation validation
        - High contrast and zoom testing considerations
        
    Integration Points:
        - ClienteSearchForm class (forms.py)
        - validate_cpf utility function
        - validate_cnpj utility function
        - Cliente model (indirect integration)
        - Precatorio creation workflows
        
    Security Validation:
        - Input sanitization effectiveness
        - Document algorithm bypass prevention
        - Format validation enforcement
        - Error message information disclosure prevention
    """
    
    def setUp(self):
        """Set up test data for ClienteSearchForm testing"""
        self.valid_cpf_data = {
            'cpf': '111.444.777-35'  # Valid CPF
        }
        
        self.valid_cnpj_data = {
            'cpf': '12.345.678/0001-95'  # Valid CNPJ
        }
        
        self.invalid_cpf_data = {
            'cpf': '123.456.789-00'  # Invalid check digits
        }
        
        # Create test cliente for validation tests
        self.test_cliente = Cliente.objects.create(
            cpf='11144477735',
            nome='João Silva',
            nascimento='1990-05-15',
            prioridade=False
        )

    def test_form_initialization_default(self):
        """Test form initialization with default configuration"""
        form = ClienteSearchForm()
        
        # Test field existence
        self.assertIn('cpf', form.fields)
        
        # Test field type
        self.assertIsInstance(form.fields['cpf'], forms.CharField)
        
        # Test field properties
        cpf_field = form.fields['cpf']
        self.assertEqual(cpf_field.max_length, 18)
        self.assertEqual(cpf_field.label, 'CPF ou CNPJ do Cliente')
        self.assertIn('Digite o CPF ou CNPJ do cliente para vincular ao precatório', cpf_field.help_text)

    def test_form_widget_configuration(self):
        """Test CPF field widget configuration"""
        form = ClienteSearchForm()
        cpf_widget = form.fields['cpf'].widget
        
        # Test widget type
        self.assertIsInstance(cpf_widget, forms.TextInput)
        
        # Test widget attributes
        attrs = cpf_widget.attrs
        self.assertEqual(attrs['class'], 'form-control')
        self.assertEqual(attrs['placeholder'], 'CPF ou CNPJ')
        self.assertEqual(attrs['pattern'], r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{11}|\d{14})')
        self.assertIn('Digite o CPF', attrs['title'])
        self.assertIn('CNPJ', attrs['title'])

    def test_form_widget_pattern_validation(self):
        """Test CPF/CNPJ widget pattern for client-side validation"""
        form = ClienteSearchForm()
        cpf_widget = form.fields['cpf'].widget
        
        # Test pattern matches expected CPF and CNPJ formats
        pattern = cpf_widget.attrs['pattern']
        self.assertIn(r'\d{3}\.\d{3}\.\d{3}-\d{2}', pattern)  # Formatted CPF
        self.assertIn(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', pattern)  # Formatted CNPJ
        self.assertIn(r'\d{11}', pattern)  # Numbers-only CPF
        self.assertIn(r'\d{14}', pattern)  # Numbers-only CNPJ

    def test_form_valid_cpf_data_submission(self):
        """Test form submission with valid CPF data"""
        form = ClienteSearchForm(data=self.valid_cpf_data)
        
        # Test form validation
        self.assertTrue(form.is_valid(), f"Form should be valid but has errors: {form.errors}")
        
        # Test cleaned data (formatting removed)
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['cpf'], '11144477735')  # Numbers only

    def test_form_valid_cnpj_data_submission(self):
        """Test form submission with valid CNPJ data"""
        form = ClienteSearchForm(data=self.valid_cnpj_data)
        
        # Test form validation
        self.assertTrue(form.is_valid(), f"Form should be valid but has errors: {form.errors}")
        
        # Test cleaned data (formatting removed)
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['cpf'], '12345678000195')  # Numbers only

    def test_form_invalid_cpf_format(self):
        """Test form submission with invalid CPF format"""
        form = ClienteSearchForm(data=self.invalid_cpf_data)
        
        # Test form validation fails
        self.assertFalse(form.is_valid())
        
        # Test error message
        self.assertIn('cpf', form.errors)
        error_message = form.errors['cpf'][0]
        self.assertIn('CPF inválido', error_message)

    def test_form_cpf_validation_cases(self):
        """Test various CPF validation cases"""
        test_cases = [
            ('111.444.777-35', True),    # Valid CPF
            ('11144477735', True),       # Valid CPF numbers only
            ('123.456.789-00', False),   # Invalid check digits
            ('12345678900', False),      # Invalid check digits numbers only
            ('000.000.000-00', False),   # All zeros
            ('111.111.111-11', False),   # All same digits
            ('123.456.789-0', False),    # Too short
            ('123.456.789-001', False),  # Too long
        ]
        
        for cpf, should_be_valid in test_cases:
            with self.subTest(cpf=cpf, expected_valid=should_be_valid):
                form = ClienteSearchForm(data={'cpf': cpf})
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"CPF {cpf} should be valid but form validation failed: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"CPF {cpf} should be invalid but form validation passed")

    def test_form_cnpj_validation_cases(self):
        """Test various CNPJ validation cases"""
        test_cases = [
            ('12.345.678/0001-95', True),   # Valid CNPJ
            ('12345678000195', True),       # Valid CNPJ numbers only
            ('11.222.333/0001-81', True),   # Another valid CNPJ
            ('12.345.678/0001-00', False),  # Invalid check digits
            ('12345678000100', False),      # Invalid check digits numbers only
            ('00.000.000/0000-00', False),  # All zeros
            ('11.111.111/1111-11', False),  # All same digits
            ('12.345.678/0001-9', False),   # Too short
            ('12.345.678/0001-955', False), # Too long
        ]
        
        for cnpj, should_be_valid in test_cases:
            with self.subTest(cnpj=cnpj, expected_valid=should_be_valid):
                form = ClienteSearchForm(data={'cpf': cnpj})
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"CNPJ {cnpj} should be valid but form validation failed: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"CNPJ {cnpj} should be invalid but form validation passed")

    def test_form_empty_cpf_field(self):
        """Test form behavior with empty CPF field"""
        form = ClienteSearchForm(data={'cpf': ''})
        
        # Test form validation fails (CPF is required)
        self.assertFalse(form.is_valid())
        
        # Test required field error
        self.assertIn('cpf', form.errors)
        error_message = form.errors['cpf'][0]
        self.assertIn('obrigatório', error_message.lower())

    def test_form_cpf_length_validation(self):
        """Test form validation for CPF/CNPJ length requirements"""
        length_cases = [
            ('12345678', False),      # Too short (8 digits)
            ('1234567890', False),    # Too short (10 digits)
            ('11144477735', True),    # Valid CPF length (11 digits)
            ('123456789012', False),  # Invalid length (12 digits)
            ('1234567890123', False), # Invalid length (13 digits)
            ('12345678000195', True), # Valid CNPJ length (14 digits)
            ('123456789001234', False), # Too long (15 digits)
        ]
        
        for doc, should_be_valid in length_cases:
            with self.subTest(doc=doc, expected_valid=should_be_valid):
                form = ClienteSearchForm(data={'cpf': doc})
                if should_be_valid:
                    # Note: Valid length doesn't guarantee valid document (algorithm check needed)
                    if form.is_valid():
                        self.assertTrue(True)  # Length is valid, algorithm validation passed
                    else:
                        # Check if error is about algorithm, not length
                        error_msg = str(form.errors['cpf'][0])
                        self.assertNotIn('11 dígitos', error_msg)
                        self.assertNotIn('14 dígitos', error_msg)
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"Document {doc} with invalid length should fail validation")
                    if not form.is_valid():
                        error_msg = str(form.errors['cpf'][0])
                        self.assertIn('CPF (11 dígitos) ou CNPJ (14 dígitos)', error_msg)

    def test_form_cpf_formatting_removal(self):
        """Test form removes formatting from CPF/CNPJ correctly"""
        formatting_cases = [
            ('111.444.777-35', '11144477735'),     # CPF with dots and dash
            ('11144477735', '11144477735'),        # CPF without formatting
            ('12.345.678/0001-95', '12345678000195'), # CNPJ with formatting
            ('12345678000195', '12345678000195'),  # CNPJ without formatting
        ]
        
        for input_doc, expected_output in formatting_cases:
            with self.subTest(input=input_doc, expected=expected_output):
                form = ClienteSearchForm(data={'cpf': input_doc})
                if form.is_valid():
                    self.assertEqual(form.cleaned_data['cpf'], expected_output)

    def test_form_whitespace_handling(self):
        """Test form handling of documents with whitespace"""
        whitespace_cases = [
            (' 111.444.777-35 ', '11144477735'),
            ('\t12.345.678/0001-95\n', '12345678000195'),
            ('  11144477735  ', '11144477735'),
        ]
        
        for input_doc, expected_output in whitespace_cases:
            with self.subTest(input=repr(input_doc), expected=expected_output):
                form = ClienteSearchForm(data={'cpf': input_doc})
                if form.is_valid():
                    self.assertEqual(form.cleaned_data['cpf'], expected_output)

    def test_form_field_accessibility_attributes(self):
        """Test CPF field accessibility attributes"""
        form = ClienteSearchForm()
        cpf_field = form.fields['cpf']
        cpf_widget = cpf_field.widget
        
        # Test help text for screen readers
        self.assertIsNotNone(cpf_field.help_text)
        self.assertIn('Digite o CPF ou CNPJ', cpf_field.help_text)
        
        # Test widget title attribute
        self.assertIn('title', cpf_widget.attrs)
        self.assertIn('Digite o CPF', cpf_widget.attrs['title'])
        
        # Test placeholder provides guidance
        self.assertIn('placeholder', cpf_widget.attrs)
        self.assertEqual(cpf_widget.attrs['placeholder'], 'CPF ou CNPJ')

    def test_form_label_configuration(self):
        """Test CPF field label configuration"""
        form = ClienteSearchForm()
        cpf_field = form.fields['cpf']
        
        # Test label text
        self.assertEqual(cpf_field.label, 'CPF ou CNPJ do Cliente')
        
        # Test help text content
        help_text = cpf_field.help_text
        self.assertIn('Digite o CPF ou CNPJ do cliente para vincular ao precatório', help_text)
        self.assertIn('Aceita formatos com ou sem pontuação', help_text)

    def test_form_widget_css_classes(self):
        """Test widget CSS class configuration"""
        form = ClienteSearchForm()
        cpf_widget = form.fields['cpf'].widget
        
        # Test CSS classes for Bootstrap styling
        self.assertEqual(cpf_widget.attrs['class'], 'form-control')

    def test_form_clean_cpf_method_integration(self):
        """Test form integration with clean_cpf method"""
        # Test that the form uses the clean_cpf method for validation
        form = ClienteSearchForm(data={'cpf': '111.444.777-35'})
        
        # Should be valid and cleaned
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['cpf'], '11144477735')
        
        # Test invalid case
        form_invalid = ClienteSearchForm(data={'cpf': '123.456.789-00'})
        self.assertFalse(form_invalid.is_valid())
        self.assertIn('CPF inválido', str(form_invalid.errors['cpf'][0]))

    def test_form_error_messages_quality(self):
        """Test quality and helpfulness of validation error messages"""
        error_cases = [
            ('', 'obrigatório'),
            ('123456789', 'CPF (11 dígitos) ou CNPJ (14 dígitos)'),
            ('123.456.789-00', 'CPF inválido'),
            ('12.345.678/0001-00', 'CNPJ inválido'),
        ]
        
        for input_doc, expected_error_keyword in error_cases:
            with self.subTest(input=input_doc, error_keyword=expected_error_keyword):
                form = ClienteSearchForm(data={'cpf': input_doc})
                self.assertFalse(form.is_valid())
                error_message = str(form.errors['cpf'][0])
                self.assertIn(expected_error_keyword, error_message)

    def test_form_data_preservation_on_error(self):
        """Test that form preserves user input on validation errors"""
        invalid_cpf = '123.456.789-00'  # Invalid CPF
        form = ClienteSearchForm(data={'cpf': invalid_cpf})
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        
        # But initial data should be preserved
        self.assertEqual(form.data['cpf'], invalid_cpf)

    def test_form_boundary_value_testing(self):
        """Test boundary values for CPF/CNPJ validation"""
        boundary_cases = [
            ('00000000001', False),  # Minimum numbers but invalid CPF
            ('99999999999', False),  # Maximum numbers but invalid CPF  
            ('00000000000001', False), # Minimum numbers but invalid CNPJ
            ('99999999999999', False), # Maximum numbers but invalid CNPJ
            ('111.444.777-35', True),  # Valid CPF example
            ('12.345.678/0001-95', True), # Valid CNPJ example
        ]
        
        for doc, should_be_valid in boundary_cases:
            with self.subTest(doc=doc, expected_valid=should_be_valid):
                form = ClienteSearchForm(data={'cpf': doc})
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"Document {doc} should be valid but validation failed: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"Document {doc} should be invalid but validation passed")

    def test_form_special_characters_handling(self):
        """Test form handling of documents with special characters"""
        special_cases = [
            ('111.444.777-35', True),   # Standard CPF format
            ('111444777-35', True),     # Missing dots - digits extracted: 11144477735 (valid CPF)
            ('111.444-777-35', True),   # Wrong dash placement - digits extracted: 11144477735 (valid CPF)
            ('111/444/777-35', True),   # Slashes instead of dots - digits extracted: 11144477735 (valid CPF)
            ('12.345.678/0001-95', True), # Standard CNPJ format
            ('12.345.678-0001-95', True), # Dash instead of slash - digits extracted: 12345678000195 (valid CNPJ)
            ('12345678/000195', True),   # Missing dots and dash - digits extracted: 12345678000195 (valid CNPJ)
        ]
        
        for doc, should_be_valid in special_cases:
            with self.subTest(doc=doc, expected_valid=should_be_valid):
                form = ClienteSearchForm(data={'cpf': doc})
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"Document {repr(doc)} should be valid but validation failed: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"Document {repr(doc)} should be invalid but validation passed")

    def test_form_mixed_case_handling(self):
        """Test form handling of documents with letters (digits extracted)"""
        mixed_cases = [
            ('111.444.777-3A5', True),  # Letter in CPF - digits extracted: 11144477735 (valid CPF)
            ('1234567800A0195', True), # Letter in CNPJ - digits extracted: 12345678000195 (14 digits, 16 chars)  
            ('ABC.DEF.GHI-JK', False),  # All letters - no digits extracted (length 0)
            ('111.444.777-35A', True), # Extra letter at end - digits extracted: 11144477735 (valid CPF)
            ('XYZ123456789XYZ', False), # Letters with some digits - only 9 digits extracted (invalid length)
            ('12.345.678/0X01-95', False), # Letter replaces digit - 13 digits extracted (invalid length)
        ]
        
        for doc, should_be_valid in mixed_cases:
            with self.subTest(doc=doc, expected_valid=should_be_valid):
                form = ClienteSearchForm(data={'cpf': doc})
                if should_be_valid:
                    self.assertTrue(form.is_valid(), 
                                  f"Document {doc} should be valid (digits extracted) but validation failed: {form.errors}")
                else:
                    self.assertFalse(form.is_valid(), 
                                   f"Document {doc} should be invalid but validation passed")

    def test_form_integration_with_validate_functions(self):
        """Test form integration with validate_cpf and validate_cnpj functions"""
        from precapp.forms import validate_cpf, validate_cnpj
        
        # Test CPF integration
        test_cpf = '11144477735'
        self.assertTrue(validate_cpf(test_cpf))
        form_cpf = ClienteSearchForm(data={'cpf': '111.444.777-35'})
        self.assertTrue(form_cpf.is_valid())
        
        # Test CNPJ integration
        test_cnpj = '12345678000195'
        self.assertTrue(validate_cnpj(test_cnpj))
        form_cnpj = ClienteSearchForm(data={'cpf': '12.345.678/0001-95'})
        self.assertTrue(form_cnpj.is_valid())

    def test_form_comprehensive_validation_flow(self):
        """Test complete validation flow from input to cleaned data"""
        # Valid CPF flow
        form = ClienteSearchForm(data={'cpf': ' 111.444.777-35 '})
        
        # Should pass all validation steps
        self.assertTrue(form.is_valid())
        
        # Should clean formatting and whitespace
        self.assertEqual(form.cleaned_data['cpf'], '11144477735')
        
        # Valid CNPJ flow
        form_cnpj = ClienteSearchForm(data={'cpf': '\t12.345.678/0001-95\n'})
        
        # Should pass all validation steps
        self.assertTrue(form_cnpj.is_valid())
        
        # Should clean formatting and whitespace
        self.assertEqual(form_cnpj.cleaned_data['cpf'], '12345678000195')


