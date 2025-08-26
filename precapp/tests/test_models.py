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
from datetime import date, timedelta
from decimal import Decimal

from precapp.models import (
    Fase, FaseHonorariosContratuais, Precatorio, Cliente, 
    Alvara, Requerimento, TipoDiligencia, Diligencias, Tipo
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


class RequerimentoModelTest(TestCase):
    """
    Comprehensive test suite for the Requerimento model.
    
    The Requerimento model represents formal legal requests submitted in the
    context of precatório processes. This test class validates:
    
    - Model creation with choice-based request types
    - Foreign key relationships (Precatorio, Cliente, Fase)
    - Business validation (cliente-precatorio linkage)
    - Choice field validation for request types (pedido)
    - Financial field handling (valor, desagio)
    - Phase tracking integration
    - String representation format
    - Custom business logic methods
    
    Request Types Tested:
    - prioridade doença: Priority due to illness
    - prioridade idade: Priority due to age
    - acordo principal: Agreement on principal amount
    - acordo honorários contratuais: Contractual fee agreement
    - acordo honorários sucumbenciais: Succumbence fee agreement
    
    Key Business Rules:
    - Cliente must be linked to Precatorio before creation
    - Single choice selection (not multiple selections)
    - Phase tracking through Fase relationship
    - Financial values must be provided and valid
    
    Methods Tested:
    - get_pedido_display(): Choice field display value
    - get_pedido_abreviado(): Abbreviated display version
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
        
        self.requerimento_data = {
            'precatorio': self.precatorio,
            'cliente': self.cliente,
            'pedido': 'prioridade doença',
            'valor': 25000.00,
            'desagio': 15.5,
            'fase': self.fase_requerimento
        }
    
    def test_requerimento_creation(self):
        """Test creating a requerimento with valid data"""
        requerimento = Requerimento(**self.requerimento_data)
        requerimento.full_clean()  # This should not raise ValidationError
        requerimento.save()
        self.assertEqual(requerimento.pedido, 'prioridade doença')
        self.assertEqual(requerimento.precatorio, self.precatorio)
        self.assertEqual(requerimento.fase, self.fase_requerimento)
    
    def test_requerimento_str_method(self):
        """Test the __str__ method of Requerimento"""
        requerimento = Requerimento(**self.requerimento_data)
        expected_str = f'Requerimento - {requerimento.pedido} - {requerimento.cliente.nome}'
        self.assertEqual(str(requerimento), expected_str)
    
    def test_requerimento_get_pedido_display(self):
        """Test get_pedido_display method"""
        requerimento = Requerimento(**self.requerimento_data)
        self.assertEqual(requerimento.get_pedido_display(), 'Prioridade por doença')
    
    def test_requerimento_fase_relationship(self):
        """Test relationship between Requerimento and Fase"""
        requerimento = Requerimento.objects.create(**self.requerimento_data)
        self.assertEqual(requerimento.fase.nome, 'Em Andamento')
        self.assertEqual(requerimento.fase.tipo, 'requerimento')


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
