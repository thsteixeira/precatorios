from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import Precatorio, Cliente, Alvara
from .forms import PrecatorioForm, ClienteForm, AlvaraForm, validate_cnj, validate_currency


class PrecatorioModelTest(TestCase):
    """Test cases for Precatorio model"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio_data = {
            'cnj': '1234567-89.2023.8.26.0100',
            'data_oficio': date(2023, 1, 1),
            'orcamento': 2023,
            'origem': '1234567-89.2022.8.26.0001',
            'valor_de_face': Decimal('100000.00'),
            'ultima_atualizacao': Decimal('100000.00'),
            'data_ultima_atualizacao': date(2023, 1, 1),
            'percentual_contratuais_assinado': Decimal('10.0'),
            'percentual_contratuais_apartado': Decimal('5.0'),
            'percentual_sucumbenciais': Decimal('20.0'),
            'quitado': False,
            'prioridade_deferida': False,
            'acordo_deferido': False
        }

    def test_precatorio_creation(self):
        """Test creating a precatorio with valid data"""
        precatorio = Precatorio(**self.precatorio_data)
        precatorio.full_clean()  # This should not raise ValidationError
        precatorio.save()
        self.assertEqual(precatorio.cnj, '1234567-89.2023.8.26.0100')

    def test_precatorio_str_method(self):
        """Test the __str__ method of Precatorio"""
        precatorio = Precatorio(**self.precatorio_data)
        expected_str = f'{precatorio.cnj} - {precatorio.origem}'
        self.assertEqual(str(precatorio), expected_str)

    def test_precatorio_unique_cnj(self):
        """Test that CNJ must be unique"""
        Precatorio.objects.create(**self.precatorio_data)
        # Try to create another precatorio with the same CNJ
        with self.assertRaises(Exception):
            duplicate_precatorio = Precatorio(**self.precatorio_data)
            duplicate_precatorio.full_clean()
            duplicate_precatorio.save()


class ClienteModelTest(TestCase):
    """Test cases for Cliente model"""
    
    def setUp(self):
        """Set up test data"""
        self.cliente_data = {
            'cpf': '12345678901',
            'nome': 'João Silva',
            'nascimento': date(1980, 5, 15),
            'prioridade': False
        }
    
    def test_cliente_creation(self):
        """Test creating a cliente with valid data"""
        cliente = Cliente(**self.cliente_data)
        cliente.full_clean()  # This should not raise ValidationError
        cliente.save()
        self.assertEqual(cliente.cpf, '12345678901')
        self.assertEqual(cliente.nome, 'João Silva')
    
    def test_cliente_str_method(self):
        """Test the __str__ method of Cliente"""
        cliente = Cliente(**self.cliente_data)
        expected_str = f'{cliente.nome} - {cliente.cpf}'
        self.assertEqual(str(cliente), expected_str)

    def test_cliente_unique_cpf(self):
        """Test that CPF must be unique"""
        Cliente.objects.create(**self.cliente_data)
        # Try to create another cliente with the same CPF
        with self.assertRaises(Exception):
            duplicate_cliente = Cliente(**self.cliente_data)
            duplicate_cliente.full_clean()
            duplicate_cliente.save()


class AlvaraModelTest(TestCase):
    """Test cases for Alvara model"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            data_oficio=date(2023, 1, 1),
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            quitado=False,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        self.cliente = Cliente.objects.create(
            cpf='98765432100',
            nome='Maria Santos',
            nascimento=date(1985, 3, 20),
            prioridade=True
        )
        
        self.alvara_data = {
            'precatorio': self.precatorio,
            'cliente': self.cliente,
            'valor_principal': 30000.00,
            'honorarios_contratuais': 15000.00,
            'honorarios_sucumbenciais': 5000.00,
            'tipo': 'Ordem de Pagamento',
            'fase': 'Execução'
        }
    
    def test_alvara_creation(self):
        """Test creating an alvara with valid data"""
        alvara = Alvara(**self.alvara_data)
        alvara.full_clean()  # This should not raise ValidationError
        alvara.save()
        self.assertEqual(alvara.tipo, 'Ordem de Pagamento')
        self.assertEqual(alvara.precatorio, self.precatorio)
    
    def test_alvara_str_method(self):
        """Test the __str__ method of Alvara"""
        alvara = Alvara(**self.alvara_data)
        expected_str = f'{alvara.tipo} - {alvara.cliente.nome}'
        self.assertEqual(str(alvara), expected_str)


class PrecatorioFormTest(TestCase):
    """Test cases for PrecatorioForm"""
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'cnj': '1234567-89.2023.8.26.0100',
            'data_oficio': '2023-01-01',
            'orcamento': '2023',
            'origem': '1234567-89.2022.8.26.0001',
            'valor_de_face': '100000.00',
            'ultima_atualizacao': '100000.00',
            'data_ultima_atualizacao': '2023-01-01',
            'percentual_contratuais_assinado': '10.0',
            'percentual_contratuais_apartado': '5.0',
            'percentual_sucumbenciais': '20.0',
            'quitado': False,
            'prioridade_deferida': False,
            'acordo_deferido': False
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


class ClienteFormTest(TestCase):
    """Test cases for ClienteForm"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            data_oficio=date(2023, 1, 1),
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            quitado=False,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        self.valid_form_data = {
            'cpf': '123.456.789-01',
            'nome': 'João Silva',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = ClienteForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = ClienteForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.nome, 'João Silva')


class ValidatorTest(TestCase):
    """Test custom validators"""
    
    def test_validate_cnj_valid(self):
        """Test CNJ validator with valid CNJ"""
        valid_cnj = '1234567-89.2023.8.26.0100'
        # Should not raise ValidationError
        validate_cnj(valid_cnj)
    
    def test_validate_cnj_invalid(self):
        """Test CNJ validator with invalid CNJ"""
        invalid_cnj = 'invalid-cnj-format'
        with self.assertRaises(ValidationError):
            validate_cnj(invalid_cnj)
    
    def test_validate_currency_valid(self):
        """Test currency validator with valid values"""
        valid_values = [100.00, 1000.50, 0.00]
        for value in valid_values:
            # Should not raise ValidationError
            validate_currency(value)
    
    def test_validate_currency_negative(self):
        """Test currency validator with negative values"""
        with self.assertRaises(ValidationError):
            validate_currency(-100.00)


class ManyToManyRelationshipTest(TestCase):
    """Test many-to-many relationships between models"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            data_oficio=date(2023, 1, 1),
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            quitado=False,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='7654321-12.2023.8.26.0200',
            data_oficio=date(2023, 2, 1),
            orcamento=2023,
            origem='1234567-98.2022.8.26.0002',
            valor_de_face=75000.00,
            ultima_atualizacao=75000.00,
            data_ultima_atualizacao=date(2023, 2, 1),
            percentual_contratuais_assinado=12.0,
            percentual_contratuais_apartado=6.0,
            percentual_sucumbenciais=18.0,
            quitado=False,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678901',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.cliente2 = Cliente.objects.create(
            cpf='98765432100',
            nome='Maria Santos',
            nascimento=date(1985, 3, 20),
            prioridade=True
        )
    
    def test_cliente_precatorio_relationship(self):
        """Test linking cliente to precatorio"""
        self.cliente.precatorios.add(self.precatorio)
        
        # Verify relationship from both sides
        self.assertIn(self.precatorio, self.cliente.precatorios.all())
        self.assertIn(self.cliente, self.precatorio.clientes.all())
    
    def test_multiple_relationships(self):
        """Test multiple relationships"""
        # Link cliente to multiple precatorios
        self.cliente.precatorios.add(self.precatorio, self.precatorio2)
        
        # Link multiple clientes to one precatorio
        self.precatorio.clientes.add(self.cliente, self.cliente2)
        
        # Verify relationships
        self.assertEqual(self.cliente.precatorios.count(), 2)
        self.assertEqual(self.precatorio.clientes.count(), 2)
    
    def test_relationship_unlinking(self):
        """Test unlinking relationships"""
        # Create relationships
        self.cliente.precatorios.add(self.precatorio, self.precatorio2)
        self.cliente2.precatorios.add(self.precatorio)
        
        # Verify setup
        self.assertEqual(self.cliente.precatorios.count(), 2)
        self.assertIn(self.cliente2, self.precatorio.clientes.all())
        
        # Test unlinking one relationship doesn't affect others
        self.precatorio.clientes.remove(self.cliente)
        
        # Verify partial unlink worked
        self.assertNotIn(self.cliente, self.precatorio.clientes.all())
        self.assertIn(self.cliente2, self.precatorio.clientes.all())
        self.assertIn(self.precatorio2, self.cliente.precatorios.all())


# Run tests with: python manage.py test precapp
