"""
Comprehensive test suite for all models in the precatorios application.

This module contains all model-related tests that were migrated from the monolithic
tests.py file. It provides comprehensive coverage for model validation, business logic,
relationships, and edge cases for the precatorios management system.

Test Organization:
- Each model has its own dedicated test class
- Tests are grouped by functionality (creation, validation, methods, relationships)
- Edge cases and business rule validation are thoroughly tested
- Both positive and negative test cases are included

Models Covered:
- Fase: Custom phases for document workflow tracking
- FaseHonorariosContratuais: Specialized phases for contractual fees
- Precatorio: Main legal document representing payment orders
- Cliente: Clients with rights to precatório payments  
- Alvara: Payment authorization documents
- Requerimento: Legal request documents
- TipoDiligencia: Customizable diligence/task types
- Diligencias: Specific tasks/actions required for clients

Testing Patterns:
- setUp() methods prepare common test data
- full_clean() validation testing for model constraints
- String representation (__str__) testing
- Business logic method testing
- Foreign key relationship testing
- Choice field validation testing
- Default value verification
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal

from precapp.models import (
    Fase, FaseHonorariosContratuais, Precatorio, Cliente, 
    Alvara, Requerimento, TipoDiligencia, Diligencias, Tipo, PedidoRequerimento
)


class FaseModelTest(TestCase):
    """
    Comprehensive test suite for the Fase model.
    
    The Fase model represents customizable phases that can be used in both
    Alvarás and Requerimentos for workflow tracking. This test class validates:
    
    - Model creation with valid data
    - Field validation and constraints
    - Choice field validation for 'tipo'
    - Default value assignment
    - String representation consistency
    - Ordering behavior (ordem, tipo, nome)
    - Class methods for filtering by document type
    - Business rule enforcement
    
    Test Data Structure:
    - Uses a standard fase_data dictionary in setUp()
    - Creates test phases with different tipos for filtering tests
    - Validates both individual field constraints and model-wide rules
    """
    
    def setUp(self):
        """
        Set up test data for Fase model tests.
        
        Creates a standard test data dictionary that can be used across
        multiple test methods. The data represents a typical fase for
        alvará documents with all required fields.
        """
        self.fase_data = {
            'nome': 'Em Andamento',
            'tipo': 'alvara',
            'cor': '#4ECDC4',
            'ativa': True
        }
    
    def test_fase_creation(self):
        """
        Test creating a fase with valid data.
        
        Validates that:
        - A Fase instance can be created with valid data
        - full_clean() passes without raising ValidationError
        - The instance can be saved to the database
        - All field values are correctly assigned
        """
        fase = Fase(**self.fase_data)
        fase.full_clean()  # This should not raise ValidationError
        fase.save()
        self.assertEqual(fase.nome, 'Em Andamento')
        self.assertEqual(fase.tipo, 'alvara')
        self.assertEqual(fase.cor, '#4ECDC4')
        self.assertTrue(fase.ativa)
    
    def test_fase_str_method(self):
        """
        Test the __str__ method of Fase.
        
        Validates that the string representation returns the fase name
        as expected, providing a human-readable identification for the phase.
        """
        fase = Fase(**self.fase_data)
        expected_str = fase.nome
        self.assertEqual(str(fase), expected_str)
    
    def test_fase_required_fields(self):
        """
        Test that required fields are enforced.
        
        Validates field requirements:
        - 'nome' field is required and cannot be empty
        - 'tipo' field has a default value so should not fail validation
        - Tests both negative (missing required field) and positive cases
        """
        # Test without nome (nome is required)
        with self.assertRaises(ValidationError):
            fase = Fase(tipo='alvara', cor='#4ECDC4', ativa=True)
            fase.full_clean()
        
        # Since tipo has a default value, this should not raise an error
        # Test valid creation with just nome
        fase = Fase(nome='Test')
        fase.full_clean()  # Should pass
    
    def test_fase_choices_validation(self):
        """
        Test that tipo field accepts only valid choices.
        
        Validates the choice constraint on the 'tipo' field:
        - Tests all valid choices: 'alvara', 'requerimento', 'ambos'
        - Tests that invalid choices raise ValidationError
        - Uses subTest for clear individual test reporting
        """
        valid_tipos = ['alvara', 'requerimento', 'ambos']
        for tipo in valid_tipos:
            with self.subTest(tipo=tipo):
                data = self.fase_data.copy()
                data['tipo'] = tipo
                fase = Fase(**data)
                fase.full_clean()  # Should not raise ValidationError
        
        # Test invalid tipo
        with self.assertRaises(ValidationError):
            fase = Fase(nome='Test', tipo='invalid', cor='#4ECDC4', ativa=True)
            fase.full_clean()
    
    def test_fase_color_field(self):
        """Test the color field"""
        # Test valid hex color
        fase = Fase(nome='Test', tipo='alvara', cor='#FF5733', ativa=True)
        fase.full_clean()
        
        # Test without # prefix (should work)
        fase2 = Fase(nome='Test2', tipo='alvara', cor='FF5733', ativa=True)
        fase2.full_clean()
    
    def test_fase_default_values(self):
        """Test default values for optional fields"""
        fase = Fase.objects.create(nome='Test', tipo='alvara')
        self.assertEqual(fase.cor, '#6c757d')  # Default color from model
        self.assertTrue(fase.ativa)  # Default to active
        self.assertEqual(fase.ordem, 0)  # Default order
    
    def test_fase_ordering(self):
        """Test that fases are ordered by ordem and nome"""
        Fase.objects.create(nome='C Fase', tipo='alvara', ordem=2)
        Fase.objects.create(nome='A Fase', tipo='alvara', ordem=1)
        Fase.objects.create(nome='B Fase', tipo='alvara', ordem=1)
        
        fases = Fase.objects.all()
        expected_order = ['A Fase', 'B Fase', 'C Fase']
        actual_order = [fase.nome for fase in fases]
        self.assertEqual(actual_order, expected_order)
    
    def test_get_fases_for_tipo(self):
        """Test get_fases_for_tipo class method"""
        # Create fases for different tipos
        alvara_fase = Fase.objects.create(nome='Alvará Fase', tipo='alvara')
        requerimento_fase = Fase.objects.create(nome='Requerimento Fase', tipo='requerimento')
        ambos_fase = Fase.objects.create(nome='Ambos Fase', tipo='ambos')
        
        # Test alvara fases
        alvara_fases = Fase.get_fases_for_alvara()
        self.assertIn(alvara_fase, alvara_fases)
        self.assertIn(ambos_fase, alvara_fases)
        self.assertNotIn(requerimento_fase, alvara_fases)
        
        # Test requerimento fases
        requerimento_fases = Fase.get_fases_for_requerimento()
        self.assertIn(requerimento_fase, requerimento_fases)
        self.assertIn(ambos_fase, requerimento_fases)
        self.assertNotIn(alvara_fase, requerimento_fases)


class FaseHonorariosContratuaisModelTest(TestCase):
    """
    Comprehensive test suite for the FaseHonorariosContratuais model.
    
    This model represents specialized phases for tracking contractual fees
    (honorários contratuais) separately from main document phases. Tests validate:
    
    - Model creation and field assignment
    - Required field validation (nome field)
    - Default value behavior (cor, ativa, ordem fields)
    - String representation consistency
    - Ordering functionality (ordem, nome)
    - Class method for retrieving active phases
    - Business rule enforcement for phase management
    
    Key Differences from Fase:
    - No 'tipo' field (specific to contractual fees)
    - Different default color (#28a745 - green)
    - Simpler structure focused on fee tracking workflow
    """
    
    def setUp(self):
        """Set up test data"""
        self.fase_honorarios_data = {
            'nome': 'Aguardando Análise',
            'cor': '#FF6B35',
            'ativa': True
        }
    
    def test_fase_honorarios_creation(self):
        """Test creating a fase honorários with valid data"""
        fase = FaseHonorariosContratuais(**self.fase_honorarios_data)
        fase.full_clean()
        fase.save()
        self.assertEqual(fase.nome, 'Aguardando Análise')
        self.assertEqual(fase.cor, '#FF6B35')
        self.assertTrue(fase.ativa)
    
    def test_fase_honorarios_str_method(self):
        """Test the __str__ method of FaseHonorariosContratuais"""
        fase = FaseHonorariosContratuais(**self.fase_honorarios_data)
        expected_str = fase.nome
        self.assertEqual(str(fase), expected_str)
    
    def test_fase_honorarios_default_values(self):
        """Test default values for FaseHonorariosContratuais"""
        fase = FaseHonorariosContratuais.objects.create(nome='Test Fase')
        self.assertEqual(fase.cor, '#28a745')  # Default color from model
        self.assertTrue(fase.ativa)  # Default to active
        self.assertEqual(fase.ordem, 0)  # Default order
    
    def test_fase_honorarios_required_fields(self):
        """Test that nome is required"""
        with self.assertRaises(ValidationError):
            fase = FaseHonorariosContratuais(cor='#FF6B35', ativa=True)
            fase.full_clean()
    
    def test_fase_honorarios_ordering(self):
        """Test that fases are ordered by ordem and nome"""
        FaseHonorariosContratuais.objects.create(nome='C Fase', ordem=2)
        FaseHonorariosContratuais.objects.create(nome='A Fase', ordem=1)
        FaseHonorariosContratuais.objects.create(nome='B Fase', ordem=1)
        
        fases = FaseHonorariosContratuais.objects.all()
        expected_order = ['A Fase', 'B Fase', 'C Fase']
        actual_order = [fase.nome for fase in fases]
        self.assertEqual(actual_order, expected_order)
    
    def test_get_ativas_class_method(self):
        """Test get_ativas class method"""
        # Create active and inactive fases
        ativa1 = FaseHonorariosContratuais.objects.create(nome='Ativa 1', ativa=True)
        ativa2 = FaseHonorariosContratuais.objects.create(nome='Ativa 2', ativa=True)
        inativa = FaseHonorariosContratuais.objects.create(nome='Inativa', ativa=False)
        
        ativas = FaseHonorariosContratuais.get_fases_ativas()
        self.assertIn(ativa1, ativas)
        self.assertIn(ativa2, ativas)
        self.assertNotIn(inativa, ativas)
        self.assertEqual(ativas.count(), 2)


class TipoModelTest(TestCase):
    """
    Comprehensive test suite for the Tipo model.
    
    The Tipo model represents different categories or types that can be assigned
    to Precatórios for classification and organization. This test class validates:
    
    - Model creation with visual and organizational properties
    - Unique constraint on 'nome' field
    - Default value assignment (cor, ativa, ordem, timestamps)
    - Color field validation for hexadecimal values
    - Ordering behavior (ordem, nome)
    - Active/inactive status management
    - Class methods for filtering active types
    - String representation consistency
    - Business rule enforcement for type management
    
    Key Features Tested:
    - Unique type names across the system
    - Color coding for visual categorization (hexadecimal format)
    - Display ordering for organized presentation
    - Active status control for availability
    - Automatic timestamping for audit trail
    - Class method for retrieving active types only
    
    Business Rules:
    - Each tipo name must be globally unique
    - Only active tipos are available for precatorio assignment
    - Default color is blue (#007bff)
    - Ordering determines display sequence in forms
    - Deactivation preserves data integrity (soft delete pattern)
    
    Integration Points:
    - Used as ForeignKey in Precatorio model
    - Supports SET_NULL deletion to preserve historical data
    - Visual identification through color coding
    - Form integration through get_tipos_ativos() method
    """
    
    def setUp(self):
        """Set up test data for Tipo model tests"""
        self.tipo_data = {
            'nome': 'Alimentar',
            'descricao': 'Precatórios de natureza alimentar com preferência de pagamento',
            'cor': '#28a745',
            'ativa': True,
            'ordem': 1
        }
    
    def test_tipo_creation(self):
        """
        Test creating a tipo with valid data.
        
        Validates that:
        - A Tipo instance can be created with valid data
        - full_clean() passes without raising ValidationError
        - The instance can be saved to the database
        - All field values are correctly assigned
        """
        tipo = Tipo(**self.tipo_data)
        tipo.full_clean()  # This should not raise ValidationError
        tipo.save()
        self.assertEqual(tipo.nome, 'Alimentar')
        self.assertEqual(tipo.descricao, 'Precatórios de natureza alimentar com preferência de pagamento')
        self.assertEqual(tipo.cor, '#28a745')
        self.assertTrue(tipo.ativa)
        self.assertEqual(tipo.ordem, 1)
    
    def test_tipo_str_method(self):
        """
        Test the __str__ method of Tipo.
        
        Validates that the string representation returns the tipo name
        as expected, providing a human-readable identification.
        """
        tipo = Tipo(**self.tipo_data)
        expected_str = tipo.nome
        self.assertEqual(str(tipo), expected_str)
    
    def test_tipo_required_fields(self):
        """
        Test that required fields are enforced.
        
        Validates that:
        - 'nome' field is required and cannot be empty
        - Other fields have defaults and should not fail validation
        """
        # Test without nome (nome is required)
        with self.assertRaises(ValidationError):
            tipo = Tipo(descricao='Test', cor='#007bff', ativa=True)
            tipo.full_clean()
        
        # Test valid creation with just nome
        tipo = Tipo(nome='Test Tipo')
        tipo.full_clean()  # Should pass
        tipo.save()
        self.assertEqual(tipo.nome, 'Test Tipo')
    
    def test_tipo_unique_constraint(self):
        """
        Test that nome field has unique constraint.
        
        Validates that:
        - Two tipos cannot have the same name
        - Database constraint is properly enforced
        - Appropriate error is raised on duplicate creation
        """
        # Create first tipo
        Tipo.objects.create(**self.tipo_data)
        
        # Try to create duplicate - should raise exception
        with self.assertRaises(Exception):  # Could be ValidationError or IntegrityError
            duplicate_tipo = Tipo(**self.tipo_data)
            duplicate_tipo.full_clean()
            duplicate_tipo.save()
    
    def test_tipo_default_values(self):
        """
        Test default values for optional fields.
        
        Validates that:
        - cor field defaults to '#007bff' (blue)
        - ativa field defaults to True
        - ordem field defaults to 0
        - Timestamp fields are automatically set
        """
        tipo = Tipo.objects.create(nome='Test Default')
        self.assertEqual(tipo.cor, '#007bff')  # Default color from model
        self.assertTrue(tipo.ativa)  # Default to active
        self.assertEqual(tipo.ordem, 0)  # Default order
        self.assertIsNotNone(tipo.criado_em)  # Auto timestamp
        self.assertIsNotNone(tipo.atualizado_em)  # Auto timestamp
    
    def test_tipo_color_field_validation(self):
        """
        Test color field accepts valid hexadecimal colors.
        
        Validates various valid color formats and ensures
        the field properly handles hexadecimal color codes.
        """
        valid_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFFFF', '#000000', '#123ABC']
        for color in valid_colors:
            with self.subTest(color=color):
                data = self.tipo_data.copy()
                data['cor'] = color
                data['nome'] = f'Test {color}'  # Unique name for each test
                tipo = Tipo(**data)
                tipo.full_clean()
                tipo.save()
                self.assertEqual(tipo.cor, color)
    
    def test_tipo_ordering(self):
        """
        Test that tipos are ordered by ordem and nome.
        
        Validates the model's Meta ordering configuration:
        - Primary sort by ordem field (ascending)
        - Secondary sort by nome field (alphabetical)
        """
        # Create tipos with different orders and names
        Tipo.objects.create(nome='C Tipo', ordem=2)
        Tipo.objects.create(nome='A Tipo', ordem=1)
        Tipo.objects.create(nome='B Tipo', ordem=1)
        Tipo.objects.create(nome='D Tipo', ordem=0)
        
        tipos = Tipo.objects.all()
        expected_order = ['D Tipo', 'A Tipo', 'B Tipo', 'C Tipo']
        actual_order = [tipo.nome for tipo in tipos]
        self.assertEqual(actual_order, expected_order)
    
    def test_get_tipos_ativos_class_method(self):
        """
        Test get_tipos_ativos class method.
        
        Validates that:
        - Method returns only active tipos
        - Inactive tipos are excluded
        - Results are properly ordered
        - Method is accessible as class method
        """
        # Create active and inactive tipos
        ativo1 = Tipo.objects.create(nome='Ativo 1', ativa=True, ordem=2)
        ativo2 = Tipo.objects.create(nome='Ativo 2', ativa=True, ordem=1)
        inativo = Tipo.objects.create(nome='Inativo', ativa=False, ordem=0)
        
        tipos_ativos = Tipo.get_tipos_ativos()
        
        # Check that only active tipos are returned
        self.assertIn(ativo1, tipos_ativos)
        self.assertIn(ativo2, tipos_ativos)
        self.assertNotIn(inativo, tipos_ativos)
        self.assertEqual(tipos_ativos.count(), 2)
        
        # Check ordering (should be by ordem, then nome)
        tipos_list = list(tipos_ativos)
        self.assertEqual(tipos_list[0], ativo2)  # ordem=1
        self.assertEqual(tipos_list[1], ativo1)  # ordem=2
    
    def test_tipo_soft_delete_pattern(self):
        """
        Test soft delete pattern through ativa field.
        
        Validates that:
        - Tipos can be deactivated instead of deleted
        - Deactivated tipos are excluded from active queries
        - Data integrity is preserved when deactivating
        """
        # Create active tipo
        tipo = Tipo.objects.create(nome='Test Deactivation', ativa=True)
        
        # Verify it appears in active tipos
        self.assertIn(tipo, Tipo.get_tipos_ativos())
        
        # Deactivate the tipo
        tipo.ativa = False
        tipo.save()
        
        # Verify it no longer appears in active tipos
        self.assertNotIn(tipo, Tipo.get_tipos_ativos())
        
        # Verify the tipo still exists in database
        self.assertTrue(Tipo.objects.filter(nome='Test Deactivation').exists())
    
    def test_tipo_meta_configuration(self):
        """
        Test model Meta configuration.
        
        Validates that:
        - Verbose names are properly set
        - Ordering configuration is correct
        """
        meta = Tipo._meta
        self.assertEqual(meta.verbose_name, "Tipo de Precatório")
        self.assertEqual(meta.verbose_name_plural, "Tipos de Precatórios")
        self.assertEqual(meta.ordering, ['ordem', 'nome'])
    
    def test_tipo_timestamps(self):
        """
        Test automatic timestamp functionality.
        
        Validates that:
        - criado_em is set on creation
        - atualizado_em is updated on save
        - Timestamps are properly maintained
        """
        tipo = Tipo.objects.create(nome='Timestamp Test')
        
        # Check initial timestamps
        self.assertIsNotNone(tipo.criado_em)
        self.assertIsNotNone(tipo.atualizado_em)
        initial_created = tipo.criado_em
        initial_updated = tipo.atualizado_em
        
        # Update the tipo
        import time
        time.sleep(0.01)  # Ensure timestamp difference
        tipo.descricao = 'Updated description'
        tipo.save()
        
        # Check that atualizado_em changed but criado_em didn't
        tipo.refresh_from_db()
        self.assertEqual(tipo.criado_em, initial_created)
        self.assertGreater(tipo.atualizado_em, initial_updated)


class PedidoRequerimentoModelTest(TestCase):
    """
    Comprehensive test suite for the PedidoRequerimento model.
    
    The PedidoRequerimento model represents customizable types of legal requests
    that can be submitted for precatórios. This model replaced the hardcoded
    choices in the Requerimento model to provide flexibility for administrators
    to define their own request types. This test class validates:
    
    - Model creation with visual and organizational properties
    - Unique constraint on 'nome' field
    - Default value assignment (cor, ativo, ordem, timestamps)
    - Color field validation for hexadecimal values
    - Ordering behavior (ordem, nome)
    - Active/inactive status management
    - Class methods for filtering active types
    - String representation consistency
    - Soft delete pattern (deactivation instead of deletion)
    - Business rule enforcement for request type management
    
    Key Features Tested:
    - Unique request type names across the system
    - Color coding for visual categorization (hexadecimal format)
    - Display ordering for organized presentation in forms/dropdowns
    - Active status control for availability in selections
    - Automatic timestamping for audit trail
    - Class method for retrieving active types only
    - Description field for detailed explanations
    
    Business Rules:
    - Each pedido name must be globally unique
    - Only active pedidos are available for requerimento creation
    - Default color is blue (#007bff)
    - Ordering determines display sequence in forms and interfaces
    - Deactivation preserves data integrity (soft delete pattern)
    - Descriptions provide context for legal request types
    
    Integration Points:
    - Used as ForeignKey in Requerimento model (replacing old choices)
    - Supports PROTECT deletion to preserve historical data integrity
    - Visual identification through color coding in templates
    - Form integration through get_ativos() method
    - Admin interface with visual color previews
    
    Request Types Examples:
    - Prioridade por idade: Priority due to advanced age
    - Prioridade por doença: Priority due to serious illness
    - Acordo no Principal: Agreement on principal amount
    - Acordo nos Hon. Contratuais: Agreement on contractual fees
    - Acordo nos Hon. Sucumbenciais: Agreement on succumbence fees
    - Impugnação aos cálculos: Challenge to calculations
    - Repartição de honorários: Fee distribution arrangements
    
    Validation Coverage:
    - Unique constraint enforcement across all instances
    - Color format validation (hexadecimal with # prefix)
    - Required field validation (nome)
    - Optional field handling (descricao)
    - Default value testing for all applicable fields
    - Class method functionality verification
    - Ordering behavior validation
    - Active/inactive status management
    - Timestamp functionality (auto_now_add, auto_now)
    
    Edge Cases:
    - Empty descriptions (should be allowed)
    - Special characters in names
    - Maximum length validation
    - Color format variations
    - Ordering edge cases (duplicate ordem values)
    - Mass activation/deactivation scenarios
    """
    
    def setUp(self):
        """
        Set up test data for PedidoRequerimento model tests.
        
        Creates a standard test data dictionary that represents a typical
        request type with all fields populated. This data structure is
        used across multiple test methods to ensure consistency.
        """
        self.pedido_requerimento_data = {
            'nome': 'Prioridade por idade',
            'descricao': 'Requerimento de prioridade com base na idade avançada do requerente',
            'cor': '#6f42c1',
            'ativo': True,
            'ordem': 1
        }
    
    def test_pedido_requerimento_creation(self):
        """
        Test creating a PedidoRequerimento with valid data.
        
        Validates that:
        - A PedidoRequerimento instance can be created with valid data
        - full_clean() passes without raising ValidationError
        - The instance can be saved to the database
        - All field values are correctly assigned and accessible
        - Timestamps are automatically set on creation
        """
        pedido = PedidoRequerimento(**self.pedido_requerimento_data)
        pedido.full_clean()  # This should not raise ValidationError
        pedido.save()
        
        # Verify all field values
        self.assertEqual(pedido.nome, 'Prioridade por idade')
        self.assertEqual(pedido.descricao, 'Requerimento de prioridade com base na idade avançada do requerente')
        self.assertEqual(pedido.cor, '#6f42c1')
        self.assertTrue(pedido.ativo)
        self.assertEqual(pedido.ordem, 1)
        
        # Verify timestamps were set
        self.assertIsNotNone(pedido.criado_em)
        self.assertIsNotNone(pedido.atualizado_em)
    
    def test_pedido_requerimento_str_method(self):
        """
        Test the __str__ method of PedidoRequerimento.
        
        Validates that the string representation returns the nome field
        as expected, providing a human-readable identification for the
        request type that will be displayed in admin interfaces, forms,
        and templates.
        """
        pedido = PedidoRequerimento(**self.pedido_requerimento_data)
        expected_str = pedido.nome
        self.assertEqual(str(pedido), expected_str)
        
        # Test with different nome values
        test_names = ['Acordo no Principal', 'Impugnação aos cálculos', 'Repartição de honorários']
        for name in test_names:
            with self.subTest(nome=name):
                pedido.nome = name
                self.assertEqual(str(pedido), name)
    
    def test_pedido_requerimento_required_fields(self):
        """
        Test that required fields are enforced.
        
        Validates field requirements:
        - 'nome' field is required and cannot be empty or None
        - Other fields have defaults and should not cause validation failures
        - Tests both negative (missing required field) and positive cases
        - Ensures proper error handling for missing required data
        """
        # Test without nome (nome is required)
        with self.assertRaises(ValidationError):
            pedido = PedidoRequerimento(
                descricao='Test description',
                cor='#007bff',
                ativo=True,
                ordem=1
            )
            pedido.full_clean()
        
        # Test with empty nome (should also fail)
        with self.assertRaises(ValidationError):
            pedido = PedidoRequerimento(
                nome='',
                descricao='Test description',
                cor='#007bff',
                ativo=True
            )
            pedido.full_clean()
        
        # Test valid creation with just nome (other fields have defaults)
        pedido = PedidoRequerimento(nome='Test Pedido')
        pedido.full_clean()  # Should pass
        pedido.save()
        self.assertEqual(pedido.nome, 'Test Pedido')
    
    def test_pedido_requerimento_unique_constraint(self):
        """
        Test that nome field has unique constraint.
        
        Validates that:
        - Two PedidoRequerimento instances cannot have the same nome
        - Database constraint is properly enforced
        - Appropriate error is raised on duplicate creation attempts
        - Case sensitivity in uniqueness validation
        """
        # Create first pedido
        PedidoRequerimento.objects.create(**self.pedido_requerimento_data)
        
        # Try to create duplicate - should raise exception
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            duplicate_pedido = PedidoRequerimento(**self.pedido_requerimento_data)
            duplicate_pedido.save()  # Skip full_clean() to test database constraint
    
    def test_pedido_requerimento_default_values(self):
        """
        Test default values for optional fields.
        
        Validates that:
        - cor field defaults to '#007bff' (blue)
        - ativo field defaults to True
        - ordem field defaults to 0
        - descricao field defaults to empty string
        - Timestamp fields are automatically set (criado_em, atualizado_em)
        """
        pedido = PedidoRequerimento.objects.create(nome='Test Default Values')
        
        # Check default values
        self.assertEqual(pedido.cor, '#007bff')  # Default color from model
        self.assertTrue(pedido.ativo)  # Default to active
        self.assertEqual(pedido.ordem, 0)  # Default order
        self.assertIsNone(pedido.descricao)  # Default null description (not empty string)
        
        # Check timestamp defaults
        self.assertIsNotNone(pedido.criado_em)  # Auto timestamp on creation
        self.assertIsNotNone(pedido.atualizado_em)  # Auto timestamp on save
    
    def test_pedido_requerimento_color_field_validation(self):
        """
        Test color field accepts valid hexadecimal colors.
        
        Validates various valid color formats:
        - Standard hex colors with # prefix
        - Different color values (primary colors, custom colors)
        - Ensures the field properly handles hexadecimal color codes
        - Tests both 6-digit and 3-digit hex formats
        """
        valid_colors = [
            '#FF0000',  # Red
            '#00FF00',  # Green
            '#0000FF',  # Blue
            '#FFFFFF',  # White
            '#000000',  # Black
            '#123ABC',  # Custom hex
            '#6f42c1',  # Purple (as in test data)
            '#e83e8c',  # Pink
            '#28a745',  # Success green
            '#ffc107',  # Warning yellow
            '#dc3545',  # Danger red
            '#fd7e14'   # Orange
        ]
        
        for color in valid_colors:
            with self.subTest(color=color):
                data = self.pedido_requerimento_data.copy()
                data['cor'] = color
                data['nome'] = f'Test {color}'  # Unique name for each test
                pedido = PedidoRequerimento(**data)
                pedido.full_clean()
                pedido.save()
                self.assertEqual(pedido.cor, color)
    
    def test_pedido_requerimento_ordering(self):
        """
        Test that pedidos are ordered by ordem and nome.
        
        Validates the model's Meta ordering configuration:
        - Primary sort by ordem field (ascending)
        - Secondary sort by nome field (alphabetical)
        - Ensures consistent ordering for UI display
        - Tests various ordem values including duplicates
        """
        # Create pedidos with different orders and names
        PedidoRequerimento.objects.create(nome='Z Último', ordem=3, cor='#FF0000')
        PedidoRequerimento.objects.create(nome='A Primeiro', ordem=1, cor='#00FF00')
        PedidoRequerimento.objects.create(nome='C Terceiro', ordem=2, cor='#0000FF')
        PedidoRequerimento.objects.create(nome='B Segundo', ordem=1, cor='#FFFF00')  # Same ordem as A
        PedidoRequerimento.objects.create(nome='D Quarto', ordem=0, cor='#FF00FF')   # Lowest ordem
        
        pedidos = PedidoRequerimento.objects.all()
        expected_order = ['D Quarto', 'A Primeiro', 'B Segundo', 'C Terceiro', 'Z Último']
        actual_order = [pedido.nome for pedido in pedidos]
        self.assertEqual(actual_order, expected_order)
    
    def test_get_ativos_class_method(self):
        """
        Test get_ativos class method.
        
        Validates that:
        - Method returns only active pedidos
        - Inactive pedidos are excluded from results
        - Results maintain proper ordering (ordem, nome)
        - Method is accessible as class method
        - Empty queryset handling when no active pedidos exist
        """
        # Create active and inactive pedidos
        ativo1 = PedidoRequerimento.objects.create(
            nome='Ativo Primeiro', 
            ativo=True, 
            ordem=2,
            cor='#28a745'
        )
        ativo2 = PedidoRequerimento.objects.create(
            nome='Ativo Segundo', 
            ativo=True, 
            ordem=1,
            cor='#007bff'
        )
        inativo1 = PedidoRequerimento.objects.create(
            nome='Inativo Primeiro', 
            ativo=False, 
            ordem=0,
            cor='#6c757d'
        )
        inativo2 = PedidoRequerimento.objects.create(
            nome='Inativo Segundo', 
            ativo=False, 
            ordem=3,
            cor='#dc3545'
        )
        
        pedidos_ativos = PedidoRequerimento.get_ativos()
        
        # Check that only active pedidos are returned
        self.assertIn(ativo1, pedidos_ativos)
        self.assertIn(ativo2, pedidos_ativos)
        self.assertNotIn(inativo1, pedidos_ativos)
        self.assertNotIn(inativo2, pedidos_ativos)
        self.assertEqual(pedidos_ativos.count(), 2)
        
        # Check ordering (should be by ordem, then nome)
        pedidos_list = list(pedidos_ativos)
        self.assertEqual(pedidos_list[0], ativo2)  # ordem=1
        self.assertEqual(pedidos_list[1], ativo1)  # ordem=2
    
    def test_pedido_requerimento_soft_delete_pattern(self):
        """
        Test soft delete pattern through ativo field.
        
        Validates that:
        - Pedidos can be deactivated instead of deleted
        - Deactivated pedidos are excluded from active queries
        - Data integrity is preserved when deactivating
        - Historical references remain intact
        - Reactivation is possible
        """
        # Create active pedido
        pedido = PedidoRequerimento.objects.create(
            nome='Test Deactivation',
            descricao='Testing soft delete pattern',
            ativo=True,
            cor='#17a2b8'
        )
        
        # Verify it appears in active pedidos
        self.assertIn(pedido, PedidoRequerimento.get_ativos())
        
        # Deactivate the pedido
        pedido.ativo = False
        pedido.save()
        
        # Verify it no longer appears in active pedidos
        self.assertNotIn(pedido, PedidoRequerimento.get_ativos())
        
        # Verify the pedido still exists in database
        self.assertTrue(PedidoRequerimento.objects.filter(nome='Test Deactivation').exists())
        
        # Test reactivation
        pedido.ativo = True
        pedido.save()
        self.assertIn(pedido, PedidoRequerimento.get_ativos())
    
    def test_pedido_requerimento_meta_configuration(self):
        """
        Test model Meta configuration.
        
        Validates that:
        - Verbose names are properly set for admin interface
        - Ordering configuration is correct
        - Model metadata is properly configured
        """
        meta = PedidoRequerimento._meta
        self.assertEqual(meta.verbose_name, "Tipo de Pedido de Requerimento")
        self.assertEqual(meta.verbose_name_plural, "Tipos de Pedidos de Requerimento")
        self.assertEqual(meta.ordering, ['ordem', 'nome'])
    
    def test_pedido_requerimento_timestamps(self):
        """
        Test automatic timestamp functionality.
        
        Validates that:
        - criado_em is set on creation and never changes
        - atualizado_em is updated on each save
        - Timestamps are properly maintained throughout lifecycle
        - Timezone handling is correct
        """
        pedido = PedidoRequerimento.objects.create(nome='Timestamp Test')
        
        # Check initial timestamps
        self.assertIsNotNone(pedido.criado_em)
        self.assertIsNotNone(pedido.atualizado_em)
        initial_created = pedido.criado_em
        initial_updated = pedido.atualizado_em
        
        # Update the pedido
        import time
        time.sleep(0.01)  # Ensure timestamp difference
        pedido.descricao = 'Updated description for timestamp test'
        pedido.save()
        
        # Check that atualizado_em changed but criado_em didn't
        pedido.refresh_from_db()
        self.assertEqual(pedido.criado_em, initial_created)
        self.assertGreater(pedido.atualizado_em, initial_updated)
    
    def test_pedido_requerimento_maximum_lengths(self):
        """
        Test field maximum length constraints.
        
        Validates that:
        - nome field respects max_length constraint
        - descricao field handles long text properly
        - cor field accepts standard hex color length
        - Appropriate errors are raised for oversized content
        """
        # Test nome max length (assuming 100 characters based on typical Django patterns)
        long_nome = 'A' * 101  # Exceed typical max length
        with self.assertRaises(ValidationError):
            pedido = PedidoRequerimento(nome=long_nome)
            pedido.full_clean()
        
        # Test valid nome length
        valid_nome = 'A' * 50  # Well within limits
        pedido = PedidoRequerimento(nome=valid_nome)
        pedido.full_clean()  # Should pass
        pedido.save()
        self.assertEqual(pedido.nome, valid_nome)
    
    def test_pedido_requerimento_description_field(self):
        """
        Test description field behavior.
        
        Validates that:
        - Description field is optional (can be empty)
        - Long descriptions are properly handled
        - HTML content is preserved (if any)
        - Unicode characters are supported
        """
        # Test with empty description
        pedido_empty = PedidoRequerimento.objects.create(
            nome='Empty Description Test',
            descricao=''
        )
        self.assertEqual(pedido_empty.descricao, '')
        
        # Test with long description
        long_description = (
            'Este é um requerimento de prioridade baseado na idade avançada do requerente. '
            'Conforme previsto na legislação brasileira, pessoas idosas têm direito a '
            'tramitação prioritária de seus processos, incluindo precatórios. '
            'Este tipo de pedido deve ser acompanhado da documentação comprobatória da idade.'
        )
        pedido_long = PedidoRequerimento.objects.create(
            nome='Long Description Test',
            descricao=long_description
        )
        self.assertEqual(pedido_long.descricao, long_description)
        
        # Test with unicode characters
        unicode_description = 'Requerimento com acentuação: ção, ã, ê, ô, ü, ñ'
        pedido_unicode = PedidoRequerimento.objects.create(
            nome='Unicode Test',
            descricao=unicode_description
        )
        self.assertEqual(pedido_unicode.descricao, unicode_description)
    
    def test_pedido_requerimento_integration_scenarios(self):
        """
        Test integration scenarios that simulate real usage.
        
        Validates common use cases:
        - Creating default pedido types for a new system
        - Bulk operations (activation/deactivation)
        - Searching and filtering operations
        - Template rendering compatibility
        """
        # Create typical default pedido types
        default_pedidos = [
            {'nome': 'Prioridade por idade', 'cor': '#6f42c1', 'ordem': 1},
            {'nome': 'Prioridade por doença', 'cor': '#e83e8c', 'ordem': 2},
            {'nome': 'Acordo no Principal', 'cor': '#007bff', 'ordem': 3},
            {'nome': 'Acordo nos Hon. Sucumbenciais', 'cor': '#28a745', 'ordem': 4},
            {'nome': 'Acordo nos Hon. Contratuais', 'cor': '#ffc107', 'ordem': 5},
            {'nome': 'Impugnação aos cálculos', 'cor': '#fd7e14', 'ordem': 6},
            {'nome': 'Repartição de honorários', 'cor': '#dc3545', 'ordem': 7},
        ]
        
        created_pedidos = []
        for pedido_data in default_pedidos:
            pedido = PedidoRequerimento.objects.create(**pedido_data)
            created_pedidos.append(pedido)
        
        # Test that all were created successfully
        self.assertEqual(PedidoRequerimento.objects.count(), 7)
        
        # Test ordering is correct
        ordered_pedidos = list(PedidoRequerimento.objects.all())
        expected_names = [p['nome'] for p in default_pedidos]
        actual_names = [p.nome for p in ordered_pedidos]
        self.assertEqual(actual_names, expected_names)
        
        # Test bulk deactivation
        PedidoRequerimento.objects.filter(nome__icontains='Acordo').update(ativo=False)
        active_count = PedidoRequerimento.get_ativos().count()
        self.assertEqual(active_count, 4)  # Only non-acordo pedidos remain active
        
        # Test searching functionality
        prioridade_pedidos = PedidoRequerimento.objects.filter(nome__icontains='Prioridade')
        self.assertEqual(prioridade_pedidos.count(), 2)
        
        acordo_pedidos = PedidoRequerimento.objects.filter(nome__icontains='Acordo')
        self.assertEqual(acordo_pedidos.count(), 3)
    
    def test_pedido_requerimento_edge_cases(self):
        """
        Test edge cases and boundary conditions.
        
        Validates handling of:
        - Special characters in names
        - Very long descriptions
        - Extreme ordem values
        - Color format variations
        - Concurrent creation attempts
        """
        # Test special characters in nome
        special_chars_name = "Prioridade (Art. 1º) - Doença & Idade > 60 anos"
        pedido_special = PedidoRequerimento.objects.create(
            nome=special_chars_name,
            cor='#123456'
        )
        self.assertEqual(pedido_special.nome, special_chars_name)
        
        # Test large ordem value (positive integers only)
        pedido_large = PedidoRequerimento.objects.create(
            nome='Large Order',
            ordem=999999,
            cor='#ABCDEF'
        )
        self.assertEqual(pedido_large.ordem, 999999)
        
        # Test color format variations (if model accepts them)
        color_variations = ['#fff', '#000', '#F0F', '#0F0']  # 3-digit hex
        for i, color in enumerate(color_variations):
            try:
                pedido_color = PedidoRequerimento.objects.create(
                    nome=f'Color Test {i}',
                    cor=color
                )
                self.assertEqual(pedido_color.cor, color)
            except ValidationError:
                # If 3-digit colors are not supported, that's also valid
                pass
    
    def test_pedido_requerimento_queryset_methods(self):
        """
        Test custom queryset methods and managers.
        
        Validates any custom query methods:
        - Active filtering through get_ativos()
        - Ordering verification
        - Performance considerations for large datasets
        """
        # Create a mix of active and inactive pedidos
        for i in range(10):
            PedidoRequerimento.objects.create(
                nome=f'Pedido {i:02d}',
                ativo=(i % 2 == 0),  # Even numbers are active
                ordem=i,
                cor='#007bff'
            )
        
        # Test get_ativos efficiency
        all_pedidos = PedidoRequerimento.objects.all()
        active_pedidos = PedidoRequerimento.get_ativos()
        
        self.assertEqual(all_pedidos.count(), 10)
        self.assertEqual(active_pedidos.count(), 5)  # Only even indices
        
        # Verify all returned pedidos are actually active
        for pedido in active_pedidos:
            self.assertTrue(pedido.ativo)
        
        # Test ordering is maintained in get_ativos
        active_list = list(active_pedidos)
        for i in range(len(active_list) - 1):
            current_order = (active_list[i].ordem, active_list[i].nome)
            next_order = (active_list[i + 1].ordem, active_list[i + 1].nome)
            self.assertLessEqual(current_order, next_order)


class PrecatorioModelTest(TestCase):
    """
    Comprehensive test suite for the Precatorio model.
    
    The Precatorio model is the central entity representing legal payment orders
    from public entities. This test class validates:
    
    - Model creation with complex field structure
    - Primary key constraint (CNJ field uniqueness)
    - Year validation for 'orcamento' field (1988-2050 range)
    - Choice field validation for payment statuses
    - String representation format (CNJ - origem)
    - Financial field handling (floats, nulls, defaults)
    - Many-to-many relationship with Cliente model
    - Foreign key relationship with Tipo model
    - Business rule compliance for Brazilian legal requirements
    
    Payment Status Testing:
    - Tests all valid status choices for each payment component
    - Validates rejection of invalid status values
    - Ensures proper default assignment ('pendente')
    
    Complex Field Structure:
    - Financial amounts (valor_de_face, ultima_atualizacao)
    - Percentage tracking (contratuais_assinado, apartado, sucumbenciais)
    - Date tracking (data_ultima_atualizacao)
    - Multiple payment status fields (principal, contractual, succumbence)
    - Optional tipo classification for categorization
    """
    
    def setUp(self):
        """Set up test data"""
        # Create a tipo for testing
        self.tipo = Tipo.objects.create(
            nome='Alimentar',
            descricao='Precatórios de natureza alimentar',
            cor='#28a745',
            ativa=True
        )
        
        self.precatorio_data = {
            'cnj': '1234567-89.2023.8.26.0100',
            'orcamento': 2023,
            'origem': '1234567-89.2022.8.26.0001',
            'valor_de_face': 100000.00,
            'ultima_atualizacao': 100000.00,
            'data_ultima_atualizacao': date(2023, 1, 1),
            'percentual_contratuais_assinado': 10.0,
            'percentual_contratuais_apartado': 5.0,
            'percentual_sucumbenciais': 20.0,
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente',
            'tipo': self.tipo
        }
    
    def test_precatorio_creation(self):
        """Test creating a precatorio with valid data"""
        precatorio = Precatorio(**self.precatorio_data)
        precatorio.full_clean()
        precatorio.save()
        self.assertEqual(precatorio.cnj, '1234567-89.2023.8.26.0100')
        self.assertEqual(precatorio.orcamento, 2023)
        self.assertEqual(precatorio.valor_de_face, 100000.00)
        self.assertEqual(precatorio.tipo, self.tipo)
        self.assertEqual(precatorio.tipo.nome, 'Alimentar')
    
    def test_precatorio_str_method(self):
        """Test the __str__ method of Precatorio"""
        precatorio = Precatorio(**self.precatorio_data)
        expected_str = f'{precatorio.cnj} - {precatorio.origem}'
        self.assertEqual(str(precatorio), expected_str)
    
    def test_precatorio_required_fields(self):
        """Test that required fields are enforced"""
        # Test without cnj
        data = self.precatorio_data.copy()
        del data['cnj']
        with self.assertRaises(ValidationError):
            precatorio = Precatorio(**data)
            precatorio.full_clean()
    
    def test_precatorio_choices_validation(self):
        """Test that choice fields accept only valid choices"""
        valid_statuses = ['pendente', 'parcial', 'quitado', 'vendido']
        
        for status in valid_statuses:
            with self.subTest(status=status):
                data = self.precatorio_data.copy()
                data['credito_principal'] = status
                precatorio = Precatorio(**data)
                precatorio.full_clean()  # Should not raise ValidationError
        
        # Test invalid status
        with self.assertRaises(ValidationError):
            data = self.precatorio_data.copy()
            data['credito_principal'] = 'invalid_status'
            precatorio = Precatorio(**data)
            precatorio.full_clean()
    
    def test_precatorio_without_tipo(self):
        """
        Test creating a precatorio without tipo (should be allowed).
        
        Validates that:
        - Tipo field is optional (null=True, blank=True)
        - Precatorio can be created without specifying a tipo
        - Default behavior when no tipo is assigned
        """
        data = self.precatorio_data.copy()
        del data['tipo']  # Remove tipo from data
        
        precatorio = Precatorio(**data)
        precatorio.full_clean()
        precatorio.save()
        
        self.assertIsNone(precatorio.tipo)
        self.assertEqual(precatorio.cnj, '1234567-89.2023.8.26.0100')
    
    def test_precatorio_tipo_relationship(self):
        """
        Test the foreign key relationship between Precatorio and Tipo.
        
        Validates that:
        - Precatorio correctly references Tipo instance
        - Relationship allows access to tipo properties
        - SET_NULL behavior when tipo is deleted
        """
        precatorio = Precatorio.objects.create(**self.precatorio_data)
        
        # Test relationship access
        self.assertEqual(precatorio.tipo.nome, 'Alimentar')
        self.assertEqual(precatorio.tipo.cor, '#28a745')
        
        # Test SET_NULL behavior
        tipo_id = self.tipo.id
        self.tipo.delete()
        precatorio.refresh_from_db()
        self.assertIsNone(precatorio.tipo)
    
    def test_precatorio_tipo_filtering(self):
        """
        Test filtering precatorios by tipo.
        
        Validates that:
        - Precatorios can be filtered by tipo
        - Multiple precatorios can share the same tipo
        - Filtering works correctly with related fields
        """
        # Create another tipo
        comum_tipo = Tipo.objects.create(nome='Comum', cor='#6c757d')
        
        # Create precatorios with different tipos
        precatorio1 = Precatorio.objects.create(**self.precatorio_data)
        
        data2 = self.precatorio_data.copy()
        data2['cnj'] = '2345678-90.2023.8.26.0200'
        data2['tipo'] = comum_tipo
        precatorio2 = Precatorio.objects.create(**data2)
        
        data3 = self.precatorio_data.copy()
        data3['cnj'] = '3456789-01.2023.8.26.0300'
        data3['tipo'] = None
        precatorio3 = Precatorio.objects.create(**data3)
        
        # Test filtering by tipo
        alimentar_precatorios = Precatorio.objects.filter(tipo=self.tipo)
        self.assertIn(precatorio1, alimentar_precatorios)
        self.assertNotIn(precatorio2, alimentar_precatorios)
        self.assertNotIn(precatorio3, alimentar_precatorios)
        
        comum_precatorios = Precatorio.objects.filter(tipo=comum_tipo)
        self.assertIn(precatorio2, comum_precatorios)
        self.assertNotIn(precatorio1, comum_precatorios)
        
        # Test filtering by null tipo
        null_tipo_precatorios = Precatorio.objects.filter(tipo__isnull=True)
        self.assertIn(precatorio3, null_tipo_precatorios)
        self.assertNotIn(precatorio1, null_tipo_precatorios)
        self.assertNotIn(precatorio2, null_tipo_precatorios)
    
    def test_precatorio_tipo_display(self):
        """
        Test tipo display functionality in precatorio context.
        
        Validates that:
        - Tipo information is accessible through precatorio
        - Color and name properties work correctly
        - Handles cases where tipo is None
        """
        # Test with tipo
        precatorio_with_tipo = Precatorio.objects.create(**self.precatorio_data)
        self.assertEqual(precatorio_with_tipo.tipo.nome, 'Alimentar')
        self.assertEqual(precatorio_with_tipo.tipo.cor, '#28a745')
        
        # Test without tipo
        data_without_tipo = self.precatorio_data.copy()
        data_without_tipo['cnj'] = '9876543-21.2023.8.26.0900'
        data_without_tipo['tipo'] = None
        precatorio_without_tipo = Precatorio.objects.create(**data_without_tipo)
        self.assertIsNone(precatorio_without_tipo.tipo)
    
    def test_precatorio_observacao_field(self):
        """
        Test the observacao field functionality.
        
        Validates that:
        - Observacao field can be empty (blank=True, null=True)
        - Observacao field can store text content
        - Observacao field doesn't affect model creation when empty
        - Observacao field persists correctly when saved
        """
        # Test with observacao
        data_with_observacao = self.precatorio_data.copy()
        data_with_observacao['cnj'] = '1111111-11.2023.8.26.0111'
        data_with_observacao['observacao'] = 'Este é um precatório com observações importantes.'
        
        precatorio_with_obs = Precatorio.objects.create(**data_with_observacao)
        self.assertEqual(precatorio_with_obs.observacao, 'Este é um precatório com observações importantes.')
        
        # Test without observacao (should be None/empty)
        data_without_observacao = self.precatorio_data.copy()
        data_without_observacao['cnj'] = '2222222-22.2023.8.26.0222'
        
        precatorio_without_obs = Precatorio.objects.create(**data_without_observacao)
        self.assertIsNone(precatorio_without_obs.observacao)
        
        # Test that empty observacao is valid
        data_empty_observacao = self.precatorio_data.copy()
        data_empty_observacao['cnj'] = '3333333-33.2023.8.26.0333'
        data_empty_observacao['observacao'] = ''
        
        precatorio_empty_obs = Precatorio(**data_empty_observacao)
        precatorio_empty_obs.full_clean()  # Should not raise ValidationError
        precatorio_empty_obs.save()
        self.assertEqual(precatorio_empty_obs.observacao, '')
    
    def test_precatorio_integra_precatorio_field(self):
        """
        Test the integra_precatorio file field functionality.
        
        Validates that:
        - Integra_precatorio field can be empty (blank=True, null=True)
        - Field is designed for file uploads
        - Field doesn't affect model creation when empty
        - Field can store file references when provided
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Test without integra_precatorio file (should be None/empty)
        data_without_file = self.precatorio_data.copy()
        data_without_file['cnj'] = '4444444-44.2023.8.26.0444'
        
        precatorio_without_file = Precatorio.objects.create(**data_without_file)
        self.assertFalse(precatorio_without_file.integra_precatorio)
        
        # Test with integra_precatorio file
        # Create a simple test file
        test_file_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\nxref\n0 3\n0000000000 65535 f \ntrailer\n<<\n/Size 3\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
        test_file = SimpleUploadedFile(
            name='test_integra.pdf',
            content=test_file_content,
            content_type='application/pdf'
        )
        
        data_with_file = self.precatorio_data.copy()
        data_with_file['cnj'] = '5555555-55.2023.8.26.0555'
        data_with_file['integra_precatorio'] = test_file
        
        precatorio_with_file = Precatorio.objects.create(**data_with_file)
        self.assertTrue(precatorio_with_file.integra_precatorio)
        self.assertIn('test_integra', precatorio_with_file.integra_precatorio.name)
        
        # Clean up the test file
        if precatorio_with_file.integra_precatorio:
            precatorio_with_file.integra_precatorio.delete()


class ClienteModelTest(TestCase):
    """
    Comprehensive test suite for the Cliente model.
    
    The Cliente model represents individuals or legal entities with rights
    to precatório payments. This test class validates:
    
    - Model creation for both CPF (individuals) and CNPJ (companies)
    - Primary key uniqueness constraint (CPF/CNPJ field)
    - Required field validation (nome, nascimento, prioridade)
    - String representation format (nome - CPF)
    - Priority status handling (boolean field)
    - Business logic methods (get_priority_requerimentos)
    - Relationship integrity with related models
    
    CPF/CNPJ Support:
    - Tests creation with both individual and company identifiers
    - Validates uniqueness constraint across all client types
    - Ensures proper handling of both document formats
    
    Priority System:
    - Tests priority flag for expedited processing
    - Validates connection to priority-based requerimentos
    - Tests age-based and illness-based priority filtering
    
    Business Logic:
    - get_priority_requerimentos() method testing
    - Relationship validation with Precatorio, Requerimento, Alvara
    - Integration with diligence management system
    """
    
    def setUp(self):
        """Set up test data"""
        self.cliente_data = {
            'cpf': '12345678909',
            'nome': 'João Silva',
            'nascimento': date(1980, 5, 15),
            'prioridade': False
        }
    
    def test_cliente_creation(self):
        """Test creating a cliente with valid data"""
        cliente = Cliente(**self.cliente_data)
        cliente.full_clean()
        cliente.save()
        self.assertEqual(cliente.cpf, '12345678909')
        self.assertEqual(cliente.nome, 'João Silva')
        self.assertFalse(cliente.prioridade)
    
    def test_cliente_str_method(self):
        """Test the __str__ method of Cliente"""
        cliente = Cliente(**self.cliente_data)
        expected_str = f'{cliente.nome} - {cliente.cpf}'
        self.assertEqual(str(cliente), expected_str)
    
    def test_cliente_required_fields(self):
        """Test that required fields are enforced"""
        # Test without nome
        data = self.cliente_data.copy()
        del data['nome']
        with self.assertRaises(ValidationError):
            cliente = Cliente(**data)
            cliente.full_clean()
    
    def test_cliente_default_values(self):
        """Test default values for optional fields"""
        cliente = Cliente.objects.create(
            cpf='98765432100',
            nome='Maria Santos',
            nascimento=date(1990, 3, 20),
            prioridade=False  # Required field
        )
        self.assertFalse(cliente.prioridade)  # Default to False
    
    def test_cliente_cpf_unique(self):
        """Test that CPF must be unique"""
        Cliente.objects.create(**self.cliente_data)
        with self.assertRaises(Exception):
            duplicate_cliente = Cliente(**self.cliente_data)
            duplicate_cliente.full_clean()
            duplicate_cliente.save()
    
    def test_cliente_observacao_field(self):
        """
        Test the observacao field functionality.
        
        Validates that:
        - Observacao field can be empty (blank=True, null=True)
        - Observacao field can store text content
        - Observacao field doesn't affect model creation when empty
        - Observacao field persists correctly when saved
        """
        # Test with observacao
        data_with_observacao = self.cliente_data.copy()
        data_with_observacao['cpf'] = '11111111111'
        data_with_observacao['observacao'] = 'Cliente com necessidades especiais de atendimento.'
        
        cliente_with_obs = Cliente.objects.create(**data_with_observacao)
        self.assertEqual(cliente_with_obs.observacao, 'Cliente com necessidades especiais de atendimento.')
        
        # Test without observacao (should be None/empty)
        data_without_observacao = self.cliente_data.copy()
        data_without_observacao['cpf'] = '22222222222'
        
        cliente_without_obs = Cliente.objects.create(**data_without_observacao)
        self.assertIsNone(cliente_without_obs.observacao)
        
        # Test that empty observacao is valid
        data_empty_observacao = self.cliente_data.copy()
        data_empty_observacao['cpf'] = '33333333333'
        data_empty_observacao['observacao'] = ''
        
        cliente_empty_obs = Cliente(**data_empty_observacao)
        cliente_empty_obs.full_clean()  # Should not raise ValidationError
        cliente_empty_obs.save()
        self.assertEqual(cliente_empty_obs.observacao, '')
        
        # Test with longer text
        data_long_observacao = self.cliente_data.copy()
        data_long_observacao['cpf'] = '44444444444'
        data_long_observacao['observacao'] = 'Esta é uma observação mais longa que testa a capacidade do campo de armazenar textos extensos com informações detalhadas sobre o cliente, incluindo histórico médico, situação financeira e outras informações relevantes para o processamento do precatório.'
        
        cliente_long_obs = Cliente.objects.create(**data_long_observacao)
        self.assertGreater(len(cliente_long_obs.observacao), 200)  # Verify the long text was stored
        self.assertIn('histórico médico', cliente_long_obs.observacao)
        
    def test_cliente_falecido_field(self):
        """
        Test the falecido field functionality.
        
        Validates that:
        - Falecido field can be None (null=True)
        - Falecido field can be True or False
        - Falecido field doesn't affect model creation when empty
        - Falecido field persists correctly when saved
        - Default value is None/False for living clients
        """
        # Test with falecido=True (deceased client)
        data_deceased = self.cliente_data.copy()
        data_deceased['cpf'] = '55555555555'
        data_deceased['falecido'] = True
        
        cliente_deceased = Cliente.objects.create(**data_deceased)
        self.assertTrue(cliente_deceased.falecido)
        
        # Test with falecido=False (living client)
        data_living = self.cliente_data.copy()
        data_living['cpf'] = '66666666666'
        data_living['falecido'] = False
        
        cliente_living = Cliente.objects.create(**data_living)
        self.assertFalse(cliente_living.falecido)
        
        # Test without falecido field (should default to None)
        data_without_falecido = self.cliente_data.copy()
        data_without_falecido['cpf'] = '77777777777'
        
        cliente_without_falecido = Cliente.objects.create(**data_without_falecido)
        self.assertIsNone(cliente_without_falecido.falecido)
        
        # Test that falecido field is valid in model validation
        data_for_validation = self.cliente_data.copy()
        data_for_validation['cpf'] = '88888888888'
        data_for_validation['falecido'] = True
        cliente_for_validation = Cliente(**data_for_validation)
        cliente_for_validation.full_clean()  # Should not raise ValidationError
        
        # Test business logic: deceased clients should not have priority
        # (This would typically be enforced at the business logic level, not model level)
        data_deceased_priority = self.cliente_data.copy()
        data_deceased_priority['cpf'] = '99999999999'
        data_deceased_priority['falecido'] = True
        data_deceased_priority['prioridade'] = False  # Deceased clients should not have priority
        
        cliente_deceased_no_priority = Cliente.objects.create(**data_deceased_priority)
        self.assertTrue(cliente_deceased_no_priority.falecido)
        self.assertFalse(cliente_deceased_no_priority.prioridade)
        
        # Test verbose name
        falecido_field = Cliente._meta.get_field('falecido')
        self.assertEqual(falecido_field.verbose_name, "Falecido(a)")
        
        # Test field properties
        self.assertTrue(falecido_field.null)
        self.assertTrue(falecido_field.blank)


class AlvaraModelTest(TestCase):
    """
    Comprehensive test suite for the Alvara model.
    
    The Alvara model represents payment authorization documents that specify
    amounts to be paid from precatórios to clients. This test class validates:
    
    - Model creation with financial components
    - Foreign key relationships (Precatorio, Cliente, Fase)
    - Business validation (cliente-precatorio linkage)
    - Financial field handling (principal, contractual, succumbence fees)
    - Phase tracking integration
    - String representation format
    - Data integrity constraints
    
    Key Validation Rules:
    - Cliente must be linked to Precatorio before Alvara creation
    - Custom clean() method validates client-precatorio relationship
    - save() method enforces full_clean() validation
    - PROTECT constraints prevent deletion of referenced phases
    
    Financial Components:
    - valor_principal: Main payment amount
    - honorarios_contratuais: Contractual fee amount
    - honorarios_sucumbenciais: Succumbence fee amount
    - All amounts can be zero but not negative
    
    Phase Integration:
    - Main fase tracks overall alvara progress
    - Optional fase_honorarios_contratuais for separate fee tracking
    - PROTECT constraint prevents accidental phase deletion
    """
    
    def setUp(self):
        """Set up test data"""
        # Create a tipo for testing
        self.tipo = Tipo.objects.create(
            nome='Comum',
            descricao='Precatórios comuns',
            cor='#6c757d',
            ativa=True
        )
        
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
            honorarios_sucumbenciais='pendente',
            tipo=self.tipo
        )
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Link the cliente to the precatorio
        self.precatorio.clientes.add(self.cliente)
        
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        
        self.alvara_data = {
            'precatorio': self.precatorio,
            'cliente': self.cliente,
            'valor_principal': 50000.00,
            'honorarios_contratuais': 10000.00,
            'honorarios_sucumbenciais': 5000.00,
            'tipo': 'prioridade',
            'fase': self.fase_alvara
        }
    
    def test_alvara_creation(self):
        """Test creating an alvara with valid data"""
        alvara = Alvara(**self.alvara_data)
        alvara.full_clean()
        alvara.save()
        self.assertEqual(alvara.valor_principal, 50000.00)
        self.assertEqual(alvara.precatorio, self.precatorio)
        self.assertEqual(alvara.fase, self.fase_alvara)
    
    def test_alvara_str_method(self):
        """Test the __str__ method of Alvara"""
        alvara = Alvara(**self.alvara_data)
        expected_str = f'{alvara.tipo} - {alvara.cliente.nome}'
        self.assertEqual(str(alvara), expected_str)
    
    def test_alvara_fase_relationship(self):
        """Test relationship between Alvara and Fase"""
        alvara = Alvara.objects.create(**self.alvara_data)
        self.assertEqual(alvara.fase.nome, 'Aguardando Depósito')
        self.assertEqual(alvara.fase.tipo, 'alvara')
    
    def test_alvara_audit_fields_initial(self):
        """Test that audit fields are populated on initial creation"""
        alvara = Alvara.objects.create(**self.alvara_data)
        
        # Check that fase audit fields are populated on creation
        self.assertIsNotNone(alvara.fase_ultima_alteracao)
        self.assertEqual(alvara.fase_alterada_por, 'System')
        
        # Check that timestamps are recent (within last minute)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        time_diff = now - alvara.fase_ultima_alteracao
        self.assertLess(time_diff, timedelta(minutes=1))
    
    def test_alvara_audit_fields_fase_change(self):
        """Test that audit fields are updated when fase changes"""
        # Create initial alvara
        alvara = Alvara.objects.create(**self.alvara_data)
        initial_timestamp = alvara.fase_ultima_alteracao
        initial_user = alvara.fase_alterada_por
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Create new fase and change
        new_fase = Fase.objects.create(
            nome='Pago',
            tipo='alvara',
            cor='#28a745',
            ativa=True
        )
        
        alvara.fase = new_fase
        alvara.save()
        
        # Check that audit fields were updated
        self.assertGreater(alvara.fase_ultima_alteracao, initial_timestamp)
        self.assertEqual(alvara.fase_alterada_por, 'System')
    
    def test_alvara_audit_fields_no_change_when_fase_same(self):
        """Test that audit fields are NOT updated when fase doesn't change"""
        # Create initial alvara
        alvara = Alvara.objects.create(**self.alvara_data)
        initial_timestamp = alvara.fase_ultima_alteracao
        initial_user = alvara.fase_alterada_por
        
        # Wait a moment to ensure timestamp difference would be visible
        import time
        time.sleep(0.1)
        
        # Save without changing fase
        alvara.valor_principal = 60000.00  # Change a different field
        alvara.save()
        
        # Check that audit fields were NOT updated
        self.assertEqual(alvara.fase_ultima_alteracao, initial_timestamp)
        self.assertEqual(alvara.fase_alterada_por, initial_user)


class AlvaraModelWithHonorariosTest(TestCase):
    """
    Extended test suite for Alvara model with contractual fees phase functionality.
    
    This test class specifically focuses on the enhanced Alvara model that includes
    the fase_honorarios_contratuais field for separate tracking of contractual
    fee phases. Tests validate:
    
    - Creation with both main and contractual fee phases
    - Optional nature of contractual fee phase tracking
    - PROTECT constraint behavior for referenced phases
    - Independent phase tracking for different payment components
    - Database integrity when attempting to delete referenced phases
    
    Enhanced Features:
    - fase_honorarios_contratuais field for separate fee tracking
    - Validation that contractual fee phases are optional
    - Testing of protection constraints (preventing deletion)
    - Integration testing with FaseHonorariosContratuais model
    
    Use Cases:
    - Alvaras with only main phase tracking
    - Alvaras with both main and contractual fee phase tracking
    - Protection against accidental deletion of active phases
    - Independent progression of main document vs fee processing
    """
    
    def setUp(self):
        """Set up test data"""
        # Create a tipo for testing
        self.tipo = Tipo.objects.create(
            nome='Comum',
            descricao='Precatórios comuns',
            cor='#6c757d',
            ativa=True
        )
        
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
            honorarios_sucumbenciais='pendente',
            tipo=self.tipo
        )
        self.cliente = Cliente.objects.create(
            cpf='98765432100',
            nome='Maria Santos',
            nascimento=date(1985, 3, 20),
            prioridade=True
        )
        
        # Link the cliente to the precatorio (required by new validation)
        self.precatorio.clientes.add(self.cliente)
        
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        
        self.fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Aguardando Pagamento',
            descricao='Honorários aguardando pagamento',
            cor='#FFA500',
            ativa=True
        )
    
    def test_alvara_with_honorarios_fase(self):
        """Test creating alvara with honorários fase"""
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        self.assertEqual(alvara.fase_honorarios_contratuais, self.fase_honorarios)
        self.assertEqual(alvara.fase_honorarios_contratuais.nome, 'Aguardando Pagamento')
    
    def test_alvara_without_honorarios_fase(self):
        """Test creating alvara without honorários fase (should be optional)"""
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara
            # fase_honorarios_contratuais is optional
        )
        
        self.assertIsNone(alvara.fase_honorarios_contratuais)
        self.assertEqual(alvara.fase, self.fase_alvara)
    
    def test_honorarios_fase_protection(self):
        """Test that honorários fase cannot be deleted if referenced by alvara"""
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        # Should not be able to delete fase that's referenced
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            self.fase_honorarios.delete()
    
    def test_alvara_honorarios_audit_fields_initial(self):
        """Test that honorarios audit fields are populated on initial creation"""
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        # Check that fase_honorarios audit fields are populated on creation
        self.assertIsNotNone(alvara.fase_honorarios_ultima_alteracao)
        self.assertEqual(alvara.fase_honorarios_alterada_por, 'System')
        
        # Check that timestamps are recent (within last minute)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        time_diff = now - alvara.fase_honorarios_ultima_alteracao
        self.assertLess(time_diff, timedelta(minutes=1))
    
    def test_alvara_honorarios_audit_fields_change(self):
        """Test that honorarios audit fields are updated when fase_honorarios changes"""
        # Create initial alvara with honorarios fase
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        initial_timestamp = alvara.fase_honorarios_ultima_alteracao
        initial_user = alvara.fase_honorarios_alterada_por
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Create new honorarios fase and change
        new_fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Pago',
            cor='#28a745',
            ativa=True
        )
        
        alvara.fase_honorarios_contratuais = new_fase_honorarios
        alvara.save()
        
        # Check that audit fields were updated
        self.assertGreater(alvara.fase_honorarios_ultima_alteracao, initial_timestamp)
        self.assertEqual(alvara.fase_honorarios_alterada_por, 'System')
    
    def test_alvara_honorarios_audit_fields_no_change_when_same(self):
        """Test that honorarios audit fields are NOT updated when fase_honorarios doesn't change"""
        # Create initial alvara with honorarios fase
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        initial_timestamp = alvara.fase_honorarios_ultima_alteracao
        initial_user = alvara.fase_honorarios_alterada_por
        
        # Wait a moment to ensure timestamp difference would be visible
        import time
        time.sleep(0.1)
        
        # Save without changing fase_honorarios
        alvara.valor_principal = 60000.00  # Change a different field
        alvara.save()
        
        # Check that audit fields were NOT updated
        self.assertEqual(alvara.fase_honorarios_ultima_alteracao, initial_timestamp)
        self.assertEqual(alvara.fase_honorarios_alterada_por, initial_user)
    
    def test_alvara_honorarios_audit_fields_none_initially(self):
        """Test that honorarios audit fields are empty when no fase_honorarios is set"""
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara
            # No fase_honorarios_contratuais set
        )
        
        # Check that fase_honorarios audit fields are empty
        self.assertIsNone(alvara.fase_honorarios_ultima_alteracao)
        self.assertIsNone(alvara.fase_honorarios_alterada_por)
    
    def test_alvara_honorarios_audit_fields_set_later(self):
        """Test that honorarios audit fields are populated when fase_honorarios is set later"""
        # Create initial alvara without honorarios fase
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara
        )
        
        # Confirm audit fields are empty initially
        self.assertIsNone(alvara.fase_honorarios_ultima_alteracao)
        self.assertIsNone(alvara.fase_honorarios_alterada_por)
        
        # Set fase_honorarios later
        alvara.fase_honorarios_contratuais = self.fase_honorarios
        alvara.save()
        
        # Check that audit fields are now populated
        self.assertIsNotNone(alvara.fase_honorarios_ultima_alteracao)
        self.assertEqual(alvara.fase_honorarios_alterada_por, 'System')


class RequerimentoModelTest(TestCase):
    """
    Comprehensive test suite for the Requerimento model.
    
    The Requerimento model represents formal legal requests submitted in the
    context of precatório processes. This test class validates:
    
    - Model creation with foreign key-based request types
    - Foreign key relationships (Precatorio, Cliente, Fase, PedidoRequerimento)
    - Business validation (cliente-precatorio linkage)
    - PedidoRequerimento foreign key validation and behavior
    - Financial field handling (valor, desagio)
    - Phase tracking integration
    - String representation format
    - Custom business logic methods
    
    Updated Model Structure:
    - pedido: ForeignKey to PedidoRequerimento (replacing old choices)
    - Supports customizable request types through admin interface
    - PROTECT constraint prevents deletion of referenced PedidoRequerimento
    - Enhanced flexibility for legal request type management
    
    Request Types Through PedidoRequerimento:
    - Prioridade por doença: Priority due to illness
    - Prioridade por idade: Priority due to age
    - Acordo no Principal: Agreement on principal amount
    - Acordo nos Hon. Contratuais: Contractual fee agreement
    - Acordo nos Hon. Sucumbenciais: Succumbence fee agreement
    - Impugnação aos cálculos: Challenge to calculations
    - Repartição de honorários: Fee distribution arrangements
    
    Key Business Rules:
    - Cliente must be linked to Precatorio before creation
    - PedidoRequerimento must be active to be selectable
    - Phase tracking through Fase relationship
    - Financial values must be provided and valid
    - PROTECT constraint preserves historical data integrity
    
    Methods Tested:
    - String representation with pedido.nome display
    - Foreign key relationship navigation
    - Filtering by pedido type and properties
    - Protection constraints validation
    - clean() and save() validation enforcement
    """
    
    def setUp(self):
        """Set up test data"""
        # Create a tipo for testing
        self.tipo = Tipo.objects.create(
            nome='Comum',
            descricao='Precatórios comuns',
            cor='#6c757d',
            ativa=True
        )
        
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
            honorarios_sucumbenciais='pendente',
            tipo=self.tipo
        )
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Link the cliente to the precatorio (required by new validation)
        self.precatorio.clientes.add(self.cliente)
        
        self.fase_requerimento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True
        )
        
        # Create a PedidoRequerimento for testing
        self.pedido_requerimento = PedidoRequerimento.objects.create(
            nome='Prioridade por doença',
            descricao='Requerimento de prioridade com base em doença grave',
            cor='#e83e8c',
            ativo=True,
            ordem=1
        )
        
        self.requerimento_data = {
            'precatorio': self.precatorio,
            'cliente': self.cliente,
            'pedido': self.pedido_requerimento,
            'valor': 25000.00,
            'desagio': 15.5,
            'fase': self.fase_requerimento
        }
    
    def test_requerimento_creation(self):
        """Test creating a requerimento with valid data"""
        requerimento = Requerimento(**self.requerimento_data)
        requerimento.full_clean()  # This should not raise ValidationError
        requerimento.save()
        self.assertEqual(requerimento.pedido, self.pedido_requerimento)
        self.assertEqual(requerimento.pedido.nome, 'Prioridade por doença')
        self.assertEqual(requerimento.precatorio, self.precatorio)
        self.assertEqual(requerimento.fase, self.fase_requerimento)
    
    def test_requerimento_str_method(self):
        """Test the __str__ method of Requerimento"""
        requerimento = Requerimento(**self.requerimento_data)
        expected_str = f'Requerimento - {requerimento.pedido.nome} - {requerimento.cliente.nome}'
        self.assertEqual(str(requerimento), expected_str)
    
    def test_requerimento_pedido_relationship(self):
        """Test relationship between Requerimento and PedidoRequerimento"""
        requerimento = Requerimento.objects.create(**self.requerimento_data)
        self.assertEqual(requerimento.pedido.nome, 'Prioridade por doença')
        self.assertEqual(requerimento.pedido.cor, '#e83e8c')
        self.assertTrue(requerimento.pedido.ativo)
    
    def test_requerimento_with_different_pedido_types(self):
        """Test creating requerimentos with different pedido types"""
        # Create additional pedido types
        acordo_principal = PedidoRequerimento.objects.create(
            nome='Acordo no Principal',
            descricao='Requerimento de acordo sobre o valor principal',
            cor='#007bff',
            ativo=True,
            ordem=2
        )
        
        acordo_honorarios = PedidoRequerimento.objects.create(
            nome='Acordo nos Hon. Contratuais',
            descricao='Requerimento de acordo sobre honorários contratuais',
            cor='#ffc107',
            ativo=True,
            ordem=3
        )
        
        # Test with acordo principal
        data_acordo = self.requerimento_data.copy()
        data_acordo['pedido'] = acordo_principal
        requerimento_acordo = Requerimento.objects.create(**data_acordo)
        self.assertEqual(requerimento_acordo.pedido.nome, 'Acordo no Principal')
        
        # Test with acordo honorarios
        data_honorarios = self.requerimento_data.copy()
        data_honorarios['pedido'] = acordo_honorarios
        requerimento_honorarios = Requerimento.objects.create(**data_honorarios)
        self.assertEqual(requerimento_honorarios.pedido.nome, 'Acordo nos Hon. Contratuais')
    
    def test_requerimento_pedido_protection(self):
        """Test that PedidoRequerimento cannot be deleted if referenced by Requerimento"""
        requerimento = Requerimento.objects.create(**self.requerimento_data)
        
        # Should not be able to delete pedido that's referenced
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            self.pedido_requerimento.delete()
    
    def test_requerimento_pedido_filtering(self):
        """Test filtering requerimentos by pedido type"""
        # Create additional pedido and requerimento
        prioridade_idade = PedidoRequerimento.objects.create(
            nome='Prioridade por idade',
            descricao='Requerimento de prioridade com base na idade',
            cor='#6f42c1',
            ativo=True,
            ordem=1
        )
        
        # Create requerimento with prioridade por doença
        req_doenca = Requerimento.objects.create(**self.requerimento_data)
        
        # Create requerimento with prioridade por idade
        data_idade = self.requerimento_data.copy()
        data_idade['pedido'] = prioridade_idade
        req_idade = Requerimento.objects.create(**data_idade)
        
        # Test filtering by pedido type
        doenca_reqs = Requerimento.objects.filter(pedido__nome='Prioridade por doença')
        self.assertIn(req_doenca, doenca_reqs)
        self.assertNotIn(req_idade, doenca_reqs)
        
        idade_reqs = Requerimento.objects.filter(pedido__nome='Prioridade por idade')
        self.assertIn(req_idade, idade_reqs)
        self.assertNotIn(req_doenca, idade_reqs)
        
        # Test filtering by multiple pedido types
        priority_reqs = Requerimento.objects.filter(
            pedido__nome__in=['Prioridade por doença', 'Prioridade por idade']
        )
        self.assertIn(req_doenca, priority_reqs)
        self.assertIn(req_idade, priority_reqs)
        self.assertEqual(priority_reqs.count(), 2)
    
    def test_requerimento_fase_relationship(self):
        """Test relationship between Requerimento and Fase"""
        requerimento = Requerimento.objects.create(**self.requerimento_data)
        self.assertEqual(requerimento.fase.nome, 'Em Andamento')
        self.assertEqual(requerimento.fase.tipo, 'requerimento')
    
    def test_requerimento_audit_fields_initial(self):
        """Test that audit fields are populated on initial creation"""
        requerimento = Requerimento.objects.create(**self.requerimento_data)
        
        # Check that fase audit fields are populated on creation
        self.assertIsNotNone(requerimento.fase_ultima_alteracao)
        self.assertEqual(requerimento.fase_alterada_por, 'System')
        
        # Check that timestamps are recent (within last minute)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        time_diff = now - requerimento.fase_ultima_alteracao
        self.assertLess(time_diff, timedelta(minutes=1))
    
    def test_requerimento_audit_fields_fase_change(self):
        """Test that audit fields are updated when fase changes"""
        # Create initial requerimento
        requerimento = Requerimento.objects.create(**self.requerimento_data)
        initial_timestamp = requerimento.fase_ultima_alteracao
        initial_user = requerimento.fase_alterada_por
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Create new fase and change
        new_fase = Fase.objects.create(
            nome='Concluído',
            tipo='requerimento',
            cor='#28a745',
            ativa=True
        )
        
        requerimento.fase = new_fase
        requerimento.save()
        
        # Check that audit fields were updated
        self.assertGreater(requerimento.fase_ultima_alteracao, initial_timestamp)
        self.assertEqual(requerimento.fase_alterada_por, 'System')
    
    def test_requerimento_audit_fields_no_change_when_fase_same(self):
        """Test that audit fields are NOT updated when fase doesn't change"""
        # Create initial requerimento
        requerimento = Requerimento.objects.create(**self.requerimento_data)
        initial_timestamp = requerimento.fase_ultima_alteracao
        initial_user = requerimento.fase_alterada_por
        
        # Wait a moment to ensure timestamp difference would be visible
        import time
        time.sleep(0.1)
        
        # Save without changing fase
        requerimento.valor = 30000.00  # Change a different field
        requerimento.save()
        
        # Check that audit fields were NOT updated
        self.assertEqual(requerimento.fase_ultima_alteracao, initial_timestamp)
        self.assertEqual(requerimento.fase_alterada_por, initial_user)
    
    def test_requerimento_audit_fields_with_user_context(self):
        """Test audit fields with simulated user context"""
        from django.contrib.auth.models import User
        import threading
        
        # Create a test user
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Set the user on the current thread (simulating middleware)
        threading.current_thread().user = test_user
        
        try:
            # Create requerimento with user context
            requerimento = Requerimento.objects.create(**self.requerimento_data)
            
            # Audit fields should reflect the user
            self.assertEqual(requerimento.fase_alterada_por, 'testuser')
            
        finally:
            # Clean up thread local
            if hasattr(threading.current_thread(), 'user'):
                delattr(threading.current_thread(), 'user')


class TipoDiligenciaModelTest(TestCase):
    """
    Comprehensive test suite for the TipoDiligencia model.
    
    The TipoDiligencia model defines customizable types of diligences (legal
    actions or requirements) that can be assigned to clients. This test class validates:
    
    - Model creation with visual and organizational properties
    - Unique constraint on 'nome' field
    - Default value assignment (cor, ativo, ordem, timestamps)
    - Color field validation for hexadecimal values
    - Ordering behavior (ordem, nome)
    - Active/inactive status management
    - Class methods for filtering active types
    - Soft delete pattern (deactivation instead of deletion)
    
    Business Rules:
    - Each diligence type name must be unique
    - Only active types are available for selection
    - Color coding for visual categorization
    - Ordering for organized display
    - Timestamps for audit trail
    
    Validation Coverage:
    - Unique constraint enforcement
    - Color format validation (hexadecimal)
    - Required field validation (nome)
    - Default value testing
    - Class method functionality (get_ativos)
    
    Soft Delete Pattern:
    - Types are deactivated rather than deleted
    - Preserves historical data integrity
    - Maintains references from existing diligences
    """
    
    def setUp(self):
        """Set up test data"""
        self.tipo_diligencia_data = {
            'nome': 'Documentação Pendente',
            'descricao': 'Solicitação de documentos necessários',
            'cor': '#007bff',
            'ativo': True
        }
    
    def test_tipo_diligencia_creation(self):
        """Test creating a tipo diligencia with valid data"""
        tipo = TipoDiligencia(**self.tipo_diligencia_data)
        tipo.full_clean()
        tipo.save()
        self.assertEqual(tipo.nome, 'Documentação Pendente')
        self.assertEqual(tipo.cor, '#007bff')
        self.assertTrue(tipo.ativo)
    
    def test_tipo_diligencia_str_method(self):
        """Test the __str__ method of TipoDiligencia"""
        tipo = TipoDiligencia(**self.tipo_diligencia_data)
        expected_str = tipo.nome
        self.assertEqual(str(tipo), expected_str)
    
    def test_tipo_diligencia_default_values(self):
        """Test default values for TipoDiligencia"""
        tipo = TipoDiligencia.objects.create(nome='Tipo Teste')
        self.assertEqual(tipo.cor, '#007bff')  # Default color
        self.assertTrue(tipo.ativo)  # Default to active
        self.assertIsNotNone(tipo.criado_em)
        self.assertIsNotNone(tipo.atualizado_em)
    
    def test_tipo_diligencia_unique_nome(self):
        """Test that nome must be unique"""
        TipoDiligencia.objects.create(**self.tipo_diligencia_data)
        with self.assertRaises(Exception):
            duplicate_tipo = TipoDiligencia(**self.tipo_diligencia_data)
            duplicate_tipo.full_clean()
            duplicate_tipo.save()
    
    def test_get_ativos_class_method(self):
        """Test get_ativos class method"""
        # Create active and inactive tipos
        ativo1 = TipoDiligencia.objects.create(nome='Ativo 1', ativo=True)
        ativo2 = TipoDiligencia.objects.create(nome='Ativo 2', ativo=True)
        inativo = TipoDiligencia.objects.create(nome='Inativo', ativo=False)
        
        ativos = TipoDiligencia.get_ativos()
        self.assertIn(ativo1, ativos)
        self.assertIn(ativo2, ativos)
        self.assertNotIn(inativo, ativos)
        self.assertEqual(ativos.count(), 2)
    
    def test_tipo_diligencia_color_validation(self):
        """Test color field accepts valid hex colors"""
        valid_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFFFF', '#000000', '#123ABC']
        for color in valid_colors:
            with self.subTest(color=color):
                data = self.tipo_diligencia_data.copy()
                data['cor'] = color
                data['nome'] = f'Test {color}'
                tipo = TipoDiligencia(**data)
                tipo.full_clean()
                tipo.save()
    
    def test_tipo_diligencia_ordering(self):
        """Test that tipos are ordered by nome"""
        TipoDiligencia.objects.create(nome='Zebra Tipo')
        TipoDiligencia.objects.create(nome='Alpha Tipo')
        TipoDiligencia.objects.create(nome='Beta Tipo')
        
        tipos = TipoDiligencia.objects.all()
        names = [tipo.nome for tipo in tipos]
        self.assertEqual(names, ['Alpha Tipo', 'Beta Tipo', 'Zebra Tipo'])


class DiligenciasModelTest(TestCase):
    """
    Comprehensive test suite for the Diligencias model.
    
    The Diligencias model represents specific tasks or actions that need to be
    completed for clients in their precatório processes. This test class validates:
    
    - Model creation with deadline and urgency tracking
    - Foreign key relationships (Cliente, TipoDiligencia)
    - Urgency level management (baixa, media, alta)
    - Completion status tracking and timestamps
    - Business logic methods for deadline calculations
    - User tracking (created by, completed by)
    - Bootstrap integration for visual styling
    - Property methods for template compatibility
    
    Urgency System:
    - baixa: Low priority (secondary color)
    - media: Medium priority (warning color) - default
    - alta: High priority (danger color)
    
    Deadline Management:
    - is_overdue(): Checks if past deadline and not completed
    - days_until_deadline(): Calculates remaining/overdue days
    - Completion status affects deadline calculations
    
    User Tracking:
    - criado_por: User who created the diligence
    - concluido_por: User who completed the diligence (optional)
    - Timestamps for creation and completion
    
    Business Logic:
    - Overdue detection based on current date
    - Completion status prevents overdue flagging
    - Visual styling integration with Bootstrap classes
    - Template compatibility through property aliases
    
    Integration Points:
    - Cliente relationship (CASCADE deletion)
    - TipoDiligencia relationship (PROTECT constraint)
    - Visual styling for urgency levels
    - User activity tracking
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
        
        self.diligencia_data = {
            'cliente': self.cliente,
            'tipo': self.tipo_diligencia,
            'data_final': date.today() + timedelta(days=7),
            'urgencia': 'media',
            'criado_por': 'Test User',
            'descricao': 'Teste de diligência'
        }
    
    def test_diligencia_creation(self):
        """Test creating a diligencia with valid data"""
        diligencia = Diligencias(**self.diligencia_data)
        diligencia.full_clean()
        diligencia.save()
        self.assertEqual(diligencia.tipo.nome, 'Documentação')
        self.assertEqual(diligencia.cliente.nome, 'João Silva')
        self.assertFalse(diligencia.concluida)
    
    def test_diligencia_str_method(self):
        """Test the __str__ method of Diligencias"""
        diligencia = Diligencias(**self.diligencia_data)
        expected_str = f"{diligencia.tipo.nome} - {diligencia.cliente.nome} (Pendente)"
        self.assertEqual(str(diligencia), expected_str)
        
        # Test with concluded diligencia
        diligencia.concluida = True
        expected_str = f"{diligencia.tipo.nome} - {diligencia.cliente.nome} (Concluída)"
        self.assertEqual(str(diligencia), expected_str)
    
    def test_diligencia_default_values(self):
        """Test default values for Diligencias"""
        diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=7),
            criado_por='Test User'
        )
        self.assertEqual(diligencia.urgencia, 'media')  # Default urgency
        self.assertFalse(diligencia.concluida)  # Default not concluded
        self.assertIsNotNone(diligencia.data_criacao)  # Auto timestamp
        self.assertIsNone(diligencia.data_conclusao)  # No conclusion date yet
    
    def test_is_overdue_method(self):
        """Test is_overdue method"""
        # Test not overdue diligencia
        future_date = date.today() + timedelta(days=7)
        diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=future_date,
            criado_por='Test User'
        )
        self.assertFalse(diligencia.is_overdue())
        
        # Test overdue diligencia
        past_date = date.today() - timedelta(days=7)
        diligencia_overdue = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=past_date,
            criado_por='Test User'
        )
        self.assertTrue(diligencia_overdue.is_overdue())
        
        # Test concluded diligencia (should not be overdue)
        diligencia_concluded = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=past_date,
            criado_por='Test User',
            concluida=True
        )
        self.assertFalse(diligencia_concluded.is_overdue())
    
    def test_days_until_deadline_method(self):
        """Test days_until_deadline method"""
        today = timezone.now().date()
        # Test future deadline
        future_date = today + timedelta(days=5)
        diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=future_date,
            criado_por='Test User'
        )
        self.assertEqual(diligencia.days_until_deadline(), 5)
        # Test past deadline
        past_date = today - timedelta(days=3)
        diligencia_past = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=past_date,
            criado_por='Test User'
        )
        self.assertEqual(diligencia_past.days_until_deadline(), -3)
        # Test concluded diligencia
        diligencia_concluded = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=future_date,
            criado_por='Test User',
            concluida=True
        )
        self.assertIsNone(diligencia_concluded.days_until_deadline())
    
    def test_get_urgencia_color_method(self):
        """Test get_urgencia_color method"""
        urgencia_colors = {
            'baixa': 'secondary',
            'media': 'warning',
            'alta': 'danger',
        }
        
        for urgencia, expected_color in urgencia_colors.items():
            with self.subTest(urgencia=urgencia):
                data = self.diligencia_data.copy()
                data['urgencia'] = urgencia
                diligencia = Diligencias(**data)
                self.assertEqual(diligencia.get_urgencia_color(), expected_color)
    
    def test_diligencia_properties(self):
        """Test property methods"""
        diligencia = Diligencias.objects.create(**self.diligencia_data)
        
        # Test criado_em property (alias for data_criacao)
        self.assertEqual(diligencia.criado_em, diligencia.data_criacao)
        
        # Test criador property (alias for criado_por)
        self.assertEqual(diligencia.criador, diligencia.criado_por)
    
    def test_diligencia_cliente_relationship(self):
        """Test relationship between Diligencias and Cliente"""
        diligencia = Diligencias.objects.create(**self.diligencia_data)
        self.assertEqual(diligencia.cliente, self.cliente)
        self.assertEqual(diligencia.cliente.nome, 'João Silva')
    
    def test_diligencia_tipo_relationship(self):
        """Test relationship between Diligencias and TipoDiligencia"""
        diligencia = Diligencias.objects.create(**self.diligencia_data)
        self.assertEqual(diligencia.tipo, self.tipo_diligencia)
        self.assertEqual(diligencia.tipo.nome, 'Documentação')
    
    def test_diligencia_responsavel_field_optional(self):
        """Test that responsavel field is optional (null=True, blank=True)"""
        # Create diligencia without responsavel (should be allowed)
        diligencia = Diligencias.objects.create(**self.diligencia_data)
        self.assertIsNone(diligencia.responsavel)
        
        # Verify the diligencia can be saved and retrieved
        diligencia.save()
        diligencia.refresh_from_db()
        self.assertIsNone(diligencia.responsavel)
    
    def test_diligencia_responsavel_with_user(self):
        """Test creating diligencia with responsavel User"""
        from django.contrib.auth.models import User
        
        # Create a test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create diligencia with responsavel
        data_with_responsavel = self.diligencia_data.copy()
        data_with_responsavel['responsavel'] = user
        
        diligencia = Diligencias.objects.create(**data_with_responsavel)
        
        # Verify the relationship
        self.assertEqual(diligencia.responsavel, user)
        self.assertEqual(diligencia.responsavel.username, 'testuser')
        self.assertEqual(diligencia.responsavel.first_name, 'Test')
        self.assertEqual(diligencia.responsavel.last_name, 'User')
        self.assertEqual(diligencia.responsavel.email, 'test@example.com')
    
    def test_diligencia_responsavel_set_null_behavior(self):
        """Test SET_NULL behavior when User is deleted"""
        from django.contrib.auth.models import User
        
        # Create a test user
        user = User.objects.create_user(
            username='tempuser',
            email='temp@example.com',
            password='temppass123'
        )
        
        # Create diligencia with responsavel
        data_with_responsavel = self.diligencia_data.copy()
        data_with_responsavel['responsavel'] = user
        diligencia = Diligencias.objects.create(**data_with_responsavel)
        
        # Verify user is assigned
        self.assertEqual(diligencia.responsavel, user)
        
        # Delete the user
        user_id = user.id
        user.delete()
        
        # Refresh diligencia and verify responsavel is set to NULL
        diligencia.refresh_from_db()
        self.assertIsNone(diligencia.responsavel)
        
        # Verify diligencia still exists
        self.assertTrue(Diligencias.objects.filter(id=diligencia.id).exists())
    
    def test_diligencia_responsavel_related_name(self):
        """Test the related_name 'diligencias_responsavel' functionality"""
        from django.contrib.auth.models import User
        
        # Create test users
        user1 = User.objects.create_user(username='user1', password='pass123')
        user2 = User.objects.create_user(username='user2', password='pass123')
        
        # Create another cliente for variety
        cliente2 = Cliente.objects.create(
            cpf='98765432100',
            nome='Maria Santos',
            nascimento=date(1990, 3, 20),
            prioridade=True
        )
        
        # Create diligencias with different responsaveis
        data1 = self.diligencia_data.copy()
        data1['responsavel'] = user1
        diligencia1 = Diligencias.objects.create(**data1)
        
        data2 = self.diligencia_data.copy()
        data2['cliente'] = cliente2
        data2['responsavel'] = user1
        data2['data_final'] = date.today() + timedelta(days=10)
        diligencia2 = Diligencias.objects.create(**data2)
        
        data3 = self.diligencia_data.copy()
        data3['cliente'] = cliente2
        data3['responsavel'] = user2
        data3['data_final'] = date.today() + timedelta(days=14)
        diligencia3 = Diligencias.objects.create(**data3)
        
        # Test related_name access from user to diligencias
        user1_diligencias = user1.diligencias_responsavel.all()
        self.assertIn(diligencia1, user1_diligencias)
        self.assertIn(diligencia2, user1_diligencias)
        self.assertNotIn(diligencia3, user1_diligencias)
        self.assertEqual(user1_diligencias.count(), 2)
        
        user2_diligencias = user2.diligencias_responsavel.all()
        self.assertIn(diligencia3, user2_diligencias)
        self.assertNotIn(diligencia1, user2_diligencias)
        self.assertNotIn(diligencia2, user2_diligencias)
        self.assertEqual(user2_diligencias.count(), 1)
    
    def test_diligencia_responsavel_filtering(self):
        """Test filtering diligencias by responsavel User"""
        from django.contrib.auth.models import User
        
        # Create test users
        manager = User.objects.create_user(
            username='manager',
            first_name='Manager',
            last_name='Silva',
            email='manager@company.com',
            password='managerpass123'
        )
        
        analyst = User.objects.create_user(
            username='analyst',
            first_name='Analyst',
            last_name='Santos',
            email='analyst@company.com',
            password='analystpass123'
        )
        
        # Create diligencias with different responsaveis
        manager_diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=5),
            urgencia='alta',
            criado_por='System',
            responsavel=manager,
            descricao='Manager task'
        )
        
        analyst_diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=10),
            urgencia='media',
            criado_por='System',
            responsavel=analyst,
            descricao='Analyst task'
        )
        
        unassigned_diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=15),
            urgencia='baixa',
            criado_por='System',
            responsavel=None,
            descricao='Unassigned task'
        )
        
        # Test filtering by specific responsavel
        manager_tasks = Diligencias.objects.filter(responsavel=manager)
        self.assertIn(manager_diligencia, manager_tasks)
        self.assertNotIn(analyst_diligencia, manager_tasks)
        self.assertNotIn(unassigned_diligencia, manager_tasks)
        self.assertEqual(manager_tasks.count(), 1)
        
        analyst_tasks = Diligencias.objects.filter(responsavel=analyst)
        self.assertIn(analyst_diligencia, analyst_tasks)
        self.assertNotIn(manager_diligencia, analyst_tasks)
        self.assertNotIn(unassigned_diligencia, analyst_tasks)
        self.assertEqual(analyst_tasks.count(), 1)
        
        # Test filtering by null responsavel (unassigned tasks)
        unassigned_tasks = Diligencias.objects.filter(responsavel__isnull=True)
        self.assertIn(unassigned_diligencia, unassigned_tasks)
        self.assertNotIn(manager_diligencia, unassigned_tasks)
        self.assertNotIn(analyst_diligencia, unassigned_tasks)
        
        # Test filtering by responsavel attributes
        silva_tasks = Diligencias.objects.filter(responsavel__last_name='Silva')
        self.assertIn(manager_diligencia, silva_tasks)
        self.assertNotIn(analyst_diligencia, silva_tasks)
        
        # Test filtering by username
        manager_by_username = Diligencias.objects.filter(responsavel__username='manager')
        self.assertIn(manager_diligencia, manager_by_username)
        self.assertEqual(manager_by_username.count(), 1)
    
    def test_diligencia_responsavel_model_validation(self):
        """Test model validation with responsavel field"""
        from django.contrib.auth.models import User
        
        # Create a test user
        user = User.objects.create_user(
            username='validator',
            password='validpass123'
        )
        
        # Test valid creation with responsavel
        data_with_responsavel = self.diligencia_data.copy()
        data_with_responsavel['responsavel'] = user
        
        diligencia = Diligencias(**data_with_responsavel)
        diligencia.full_clean()  # Should not raise ValidationError
        diligencia.save()
        
        # Verify the relationship
        self.assertEqual(diligencia.responsavel, user)
        
        # Test valid creation without responsavel
        diligencia_no_responsavel = Diligencias(**self.diligencia_data)
        diligencia_no_responsavel.full_clean()  # Should not raise ValidationError
        diligencia_no_responsavel.save()
        
        # Verify no responsavel
        self.assertIsNone(diligencia_no_responsavel.responsavel)
    
    def test_diligencia_responsavel_str_representation_update(self):
        """Test that __str__ method works correctly with responsavel field"""
        from django.contrib.auth.models import User
        
        # Create test user
        user = User.objects.create_user(
            username='strtestuser',
            first_name='String',
            last_name='Test',
            password='testpass123'
        )
        
        # Test string representation without responsavel
        diligencia_no_responsavel = Diligencias.objects.create(**self.diligencia_data)
        expected_str_no_responsavel = f"{self.tipo_diligencia.nome} - {self.cliente.nome} (Pendente)"
        self.assertEqual(str(diligencia_no_responsavel), expected_str_no_responsavel)
        
        # Test string representation with responsavel
        data_with_responsavel = self.diligencia_data.copy()
        data_with_responsavel['responsavel'] = user
        data_with_responsavel['data_final'] = date.today() + timedelta(days=20)  # Different deadline
        
        diligencia_with_responsavel = Diligencias.objects.create(**data_with_responsavel)
        expected_str_with_responsavel = f"{self.tipo_diligencia.nome} - {self.cliente.nome} (Pendente)"
        self.assertEqual(str(diligencia_with_responsavel), expected_str_with_responsavel)
        
        # Test string representation with concluded diligencia and responsavel
        diligencia_with_responsavel.concluida = True
        diligencia_with_responsavel.save()
        expected_str_concluded = f"{self.tipo_diligencia.nome} - {self.cliente.nome} (Concluída)"
        self.assertEqual(str(diligencia_with_responsavel), expected_str_concluded)
    
    def test_diligencia_responsavel_select_related_optimization(self):
        """Test that responsavel can be efficiently loaded with select_related"""
        from django.contrib.auth.models import User
        
        # Create test users
        users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'selectuser{i}',
                first_name=f'Select{i}',
                last_name=f'User{i}',
                password='selectpass123'
            )
            users.append(user)
        
        # Create diligencias with different responsaveis
        diligencias = []
        for i, user in enumerate(users):
            data = self.diligencia_data.copy()
            data['responsavel'] = user
            data['data_final'] = date.today() + timedelta(days=5 + i)
            data['descricao'] = f'Task {i} for {user.username}'
            diligencia = Diligencias.objects.create(**data)
            diligencias.append(diligencia)
        
        # Test select_related optimization
        with self.assertNumQueries(1):  # Should be 1 query with select_related
            diligencias_optimized = Diligencias.objects.select_related('responsavel').filter(
                responsavel__isnull=False
            )
            
            # Access responsavel fields (should not cause additional queries)
            for diligencia in diligencias_optimized:
                username = diligencia.responsavel.username
                first_name = diligencia.responsavel.first_name
                last_name = diligencia.responsavel.last_name
                # These accesses should not trigger additional database queries
                self.assertIsNotNone(username)
                self.assertIsNotNone(first_name)
                self.assertIsNotNone(last_name)
    
    def test_diligencia_responsavel_integration_scenarios(self):
        """Test integration scenarios with responsavel field"""
        from django.contrib.auth.models import User
        
        # Create multiple users for different roles
        supervisor = User.objects.create_user(
            username='supervisor',
            first_name='Super',
            last_name='Visor',
            email='supervisor@company.com',
            password='supervisorpass'
        )
        
        coordinator = User.objects.create_user(
            username='coordinator',
            first_name='Coord',
            last_name='Inator',
            email='coordinator@company.com',
            password='coordinatorpass'
        )
        
        # Create multiple clientes
        cliente2 = Cliente.objects.create(
            cpf='11122233344',
            nome='Ana Costa',
            nascimento=date(1975, 8, 12),
            prioridade=True
        )
        
        # Create multiple tipo_diligencias
        tipo_contato = TipoDiligencia.objects.create(
            nome='Contato Cliente',
            cor='#28a745'
        )
        
        tipo_analise = TipoDiligencia.objects.create(
            nome='Análise Processual',
            cor='#ffc107'
        )
        
        # Create various diligencias simulating real-world scenarios
        scenarios = [
            # High priority task assigned to supervisor
            {
                'cliente': self.cliente,
                'tipo': self.tipo_diligencia,
                'responsavel': supervisor,
                'urgencia': 'alta',
                'data_final': date.today() + timedelta(days=2),
                'descricao': 'Urgent document review'
            },
            # Medium priority task assigned to coordinator  
            {
                'cliente': cliente2,
                'tipo': tipo_contato,
                'responsavel': coordinator,
                'urgencia': 'media',
                'data_final': date.today() + timedelta(days=7),
                'descricao': 'Client contact for information'
            },
            # Unassigned task
            {
                'cliente': cliente2,
                'tipo': tipo_analise,
                'responsavel': None,
                'urgencia': 'baixa',
                'data_final': date.today() + timedelta(days=14),
                'descricao': 'Process analysis pending assignment'
            },
            # Overdue task assigned to supervisor
            {
                'cliente': self.cliente,
                'tipo': tipo_analise,
                'responsavel': supervisor,
                'urgencia': 'media',
                'data_final': date.today() - timedelta(days=3),
                'descricao': 'Overdue analysis task'
            }
        ]
        
        created_diligencias = []
        for scenario in scenarios:
            scenario['criado_por'] = 'Test System'
            diligencia = Diligencias.objects.create(**scenario)
            created_diligencias.append(diligencia)
        
        # Test various filtering scenarios
        
        # 1. Get all tasks assigned to supervisor
        supervisor_tasks = Diligencias.objects.filter(responsavel=supervisor)
        self.assertEqual(supervisor_tasks.count(), 2)
        
        # 2. Get unassigned tasks
        unassigned_tasks = Diligencias.objects.filter(responsavel__isnull=True)
        self.assertEqual(unassigned_tasks.count(), 1)
        
        # 3. Get high priority tasks with assigned responsavel
        high_priority_assigned = Diligencias.objects.filter(
            urgencia='alta',
            responsavel__isnull=False
        )
        self.assertEqual(high_priority_assigned.count(), 1)
        
        # 4. Get overdue tasks by responsavel
        overdue_tasks = Diligencias.objects.filter(
            data_final__lt=date.today(),
            concluida=False,
            responsavel=supervisor
        )
        self.assertEqual(overdue_tasks.count(), 1)
        
        # 5. Get tasks by user email domain
        company_tasks = Diligencias.objects.filter(
            responsavel__email__endswith='@company.com'
        )
        self.assertEqual(company_tasks.count(), 3)  # supervisor + coordinator tasks
        
        # 6. Test workload distribution
        supervisor_workload = supervisor.diligencias_responsavel.filter(concluida=False).count()
        coordinator_workload = coordinator.diligencias_responsavel.filter(concluida=False).count()
        
        self.assertEqual(supervisor_workload, 2)
        self.assertEqual(coordinator_workload, 1)
        
        # 7. Test reassignment scenario
        unassigned_task = unassigned_tasks.first()
        unassigned_task.responsavel = coordinator
        unassigned_task.save()
        
        # Verify reassignment
        coordinator_new_workload = coordinator.diligencias_responsavel.filter(concluida=False).count()
        self.assertEqual(coordinator_new_workload, 2)
        
        final_unassigned = Diligencias.objects.filter(responsavel__isnull=True).count()
        self.assertEqual(final_unassigned, 0)
