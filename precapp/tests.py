from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import Precatorio, Cliente, Alvara, Requerimento, Fase
from .forms import (
    PrecatorioForm, ClienteForm, AlvaraForm, AlvaraSimpleForm, 
    RequerimentoForm, FaseForm, validate_cnj, validate_currency
)


class FaseModelTest(TestCase):
    """Test cases for Fase model"""
    
    def setUp(self):
        """Set up test data"""
        self.fase_alvara_data = {
            'nome': 'Aguardando Depósito',
            'descricao': 'Alvará aguardando depósito judicial',
            'tipo': 'alvara',
            'cor': '#FF6B35',
            'ativa': True
        }
        
        self.fase_requerimento_data = {
            'nome': 'Em Andamento',
            'descricao': 'Requerimento em tramitação',
            'tipo': 'requerimento',
            'cor': '#4ECDC4',
            'ativa': True
        }
        
        self.fase_ambos_data = {
            'nome': 'Cancelado',
            'descricao': 'Processo cancelado',
            'tipo': 'ambos',
            'cor': '#95A5A6',
            'ativa': True
        }
    
    def test_fase_creation_alvara(self):
        """Test creating a fase for alvará"""
        fase = Fase(**self.fase_alvara_data)
        fase.full_clean()
        fase.save()
        self.assertEqual(fase.nome, 'Aguardando Depósito')
        self.assertEqual(fase.tipo, 'alvara')
    
    def test_fase_creation_requerimento(self):
        """Test creating a fase for requerimento"""
        fase = Fase(**self.fase_requerimento_data)
        fase.full_clean()
        fase.save()
        self.assertEqual(fase.nome, 'Em Andamento')
        self.assertEqual(fase.tipo, 'requerimento')
    
    def test_fase_creation_ambos(self):
        """Test creating a fase for both types"""
        fase = Fase(**self.fase_ambos_data)
        fase.full_clean()
        fase.save()
        self.assertEqual(fase.nome, 'Cancelado')
        self.assertEqual(fase.tipo, 'ambos')
    
    def test_fase_str_method(self):
        """Test the __str__ method of Fase"""
        fase = Fase(**self.fase_alvara_data)
        expected_str = f'{fase.nome} (Alvará)'  # Should show display value
        self.assertEqual(str(fase), expected_str)
    
    def test_fase_unique_constraint(self):
        """Test that nome+tipo combination must be unique"""
        Fase.objects.create(**self.fase_alvara_data)
        # Try to create another fase with the same nome+tipo
        with self.assertRaises(Exception):
            duplicate_fase = Fase(**self.fase_alvara_data)
            duplicate_fase.full_clean()
            duplicate_fase.save()
    
    def test_fase_same_nome_different_tipo(self):
        """Test that same nome can exist for different tipos"""
        # Create 'Cancelado' for alvara
        fase_alvara = Fase(
            nome='Cancelado',
            tipo='alvara',
            cor='#FF0000',
            ativa=True
        )
        fase_alvara.save()
        
        # Create 'Cancelado' for requerimento - should work
        fase_requerimento = Fase(
            nome='Cancelado',
            tipo='requerimento',
            cor='#00FF00',
            ativa=True
        )
        fase_requerimento.save()
        
        self.assertEqual(Fase.objects.filter(nome='Cancelado').count(), 2)
    
    def test_get_fases_for_alvara(self):
        """Test class method get_fases_for_alvara"""
        # Create test phases
        Fase.objects.create(nome='Alvara Específico', tipo='alvara', cor='#FF0000')
        Fase.objects.create(nome='Requerimento Específico', tipo='requerimento', cor='#00FF00')
        Fase.objects.create(nome='Compartilhado', tipo='ambos', cor='#0000FF')
        
        alvara_fases = Fase.get_fases_for_alvara()
        
        # Should include alvara and ambos, not requerimento
        self.assertEqual(alvara_fases.count(), 2)
        tipos_alvara = set(alvara_fases.values_list('tipo', flat=True))
        self.assertEqual(tipos_alvara, {'alvara', 'ambos'})
    
    def test_get_fases_for_requerimento(self):
        """Test class method get_fases_for_requerimento"""
        # Create test phases
        Fase.objects.create(nome='Alvara Específico', tipo='alvara', cor='#FF0000')
        Fase.objects.create(nome='Requerimento Específico', tipo='requerimento', cor='#00FF00')
        Fase.objects.create(nome='Compartilhado', tipo='ambos', cor='#0000FF')
        
        requerimento_fases = Fase.get_fases_for_requerimento()
        
        # Should include requerimento and ambos, not alvara
        self.assertEqual(requerimento_fases.count(), 2)
        tipos_requerimento = set(requerimento_fases.values_list('tipo', flat=True))
        self.assertEqual(tipos_requerimento, {'requerimento', 'ambos'})


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
        
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        
        self.alvara_data = {
            'precatorio': self.precatorio,
            'cliente': self.cliente,
            'valor_principal': 30000.00,
            'honorarios_contratuais': 15000.00,
            'honorarios_sucumbenciais': 5000.00,
            'tipo': 'prioridade',
            'fase': self.fase_alvara
        }
    
    def test_alvara_creation(self):
        """Test creating an alvara with valid data"""
        alvara = Alvara(**self.alvara_data)
        alvara.full_clean()  # This should not raise ValidationError
        alvara.save()
        self.assertEqual(alvara.tipo, 'prioridade')
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


class RequerimentoModelTest(TestCase):
    """Test cases for Requerimento model"""
    
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
            cpf='12345678901',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
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


class FaseFormTest(TestCase):
    """Test cases for FaseForm"""
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'nome': 'Nova Fase',
            'descricao': 'Descrição da nova fase',
            'tipo': 'alvara',
            'cor': '#FF6B35',
            'ativa': True
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = FaseForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = FaseForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        fase = form.save()
        self.assertEqual(fase.nome, 'Nova Fase')
        self.assertEqual(fase.tipo, 'alvara')
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        incomplete_data = {'nome': 'Test'}
        form = FaseForm(data=incomplete_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)


class AlvaraFormTest(TestCase):
    """Test cases for AlvaraForm and AlvaraSimpleForm"""
    
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
            cpf='12345678901',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
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
    
    def test_alvara_form_fase_filtering(self):
        """Test that AlvaraForm only shows alvara and ambos phases"""
        form = AlvaraForm()
        fase_queryset = form.fields['fase'].queryset
        
        # Should include alvara and ambos phases
        self.assertIn(self.fase_alvara, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include requerimento phases
        self.assertNotIn(self.fase_requerimento, fase_queryset)
    
    def test_alvara_simple_form_fase_filtering(self):
        """Test that AlvaraSimpleForm only shows alvara and ambos phases"""
        form = AlvaraSimpleForm()
        fase_queryset = form.fields['fase'].queryset
        
        # Should include alvara and ambos phases
        self.assertIn(self.fase_alvara, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include requerimento phases
        self.assertNotIn(self.fase_requerimento, fase_queryset)


class RequerimentoFormTest(TestCase):
    """Test cases for RequerimentoForm"""
    
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
            cpf='12345678901',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        self.fase_requerimento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True
        )
        self.fase_ambos = Fase.objects.create(
            nome='Cancelado',
            tipo='ambos',
            cor='#95A5A6',
            ativa=True
        )
        # Create an alvara fase that should not appear in requerimento forms
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        
        self.valid_form_data = {
            'cliente_cpf': '123.456.789-01',
            'pedido': 'prioridade doença',
            'valor': '25000.00',
            'desagio': '15.5',
            'fase': self.fase_requerimento.id
        }
    
    def test_requerimento_form_fase_filtering(self):
        """Test that RequerimentoForm only shows requerimento and ambos phases"""
        form = RequerimentoForm()
        fase_queryset = form.fields['fase'].queryset
        
        # Should include requerimento and ambos phases
        self.assertIn(self.fase_requerimento, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include alvara phases
        self.assertNotIn(self.fase_alvara, fase_queryset)
    
    def test_valid_requerimento_form(self):
        """Test form with valid data"""
        form = RequerimentoForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())


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


class IntegrationTest(TestCase):
    """Integration tests for the complete workflow"""
    
    def setUp(self):
        """Set up test data"""
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create phases
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        self.fase_requerimento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True
        )
        self.fase_ambos = Fase.objects.create(
            nome='Cancelado',
            tipo='ambos',
            cor='#95A5A6',
            ativa=True
        )
        
        # Create precatorio
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
        
        # Create cliente
        self.cliente = Cliente.objects.create(
            cpf='12345678901',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.client_app = Client()
    
    def test_complete_workflow(self):
        """Test complete workflow: login, create alvara, create requerimento"""
        # Login
        login_success = self.client_app.login(username='testuser', password='testpass123')
        self.assertTrue(login_success)
        
        # Create Alvara
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=30000.00,
            honorarios_contratuais=15000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara
        )
        
        # Create Requerimento
        requerimento = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='prioridade doença',
            valor=25000.00,
            desagio=15.5,
            fase=self.fase_requerimento
        )
        
        # Verify relationships
        self.assertEqual(alvara.fase.tipo, 'alvara')
        self.assertEqual(requerimento.fase.tipo, 'requerimento')
        self.assertEqual(alvara.precatorio, self.precatorio)
        self.assertEqual(requerimento.precatorio, self.precatorio)
    
    def test_fase_filtering_integration(self):
        """Test that phase filtering works correctly in practice"""
        # Test that different document types see appropriate phases
        alvara_fases = Fase.get_fases_for_alvara()
        requerimento_fases = Fase.get_fases_for_requerimento()
        
        # Alvara should see 'alvara' and 'ambos' phases
        alvara_tipos = set(alvara_fases.values_list('tipo', flat=True))
        self.assertEqual(alvara_tipos, {'alvara', 'ambos'})
        
        # Requerimento should see 'requerimento' and 'ambos' phases
        requerimento_tipos = set(requerimento_fases.values_list('tipo', flat=True))
        self.assertEqual(requerimento_tipos, {'requerimento', 'ambos'})
        
        # Both should see the 'ambos' phase
        self.assertIn(self.fase_ambos, alvara_fases)
        self.assertIn(self.fase_ambos, requerimento_fases)


class ViewTest(TestCase):
    """Test cases for views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.fase = Fase.objects.create(
            nome='Test Phase',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        
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
        
        self.client_app = Client()
    
    def test_login_required(self):
        """Test that views require authentication"""
        # Test that accessing precatorio detail redirects to login
        response = self.client_app.get(reverse('precatorio_detalhe', args=[self.precatorio.cnj]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_authenticated_access(self):
        """Test that authenticated users can access views"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('precatorio_detalhe', args=[self.precatorio.cnj]))
        self.assertEqual(response.status_code, 200)
    
    def test_fase_context_in_precatorio_detail(self):
        """Test that precatorio detail view provides phase context"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('precatorio_detalhe', args=[self.precatorio.cnj]))
        
        # Check that phase lists are in context
        self.assertIn('alvara_fases', response.context)
        self.assertIn('requerimento_fases', response.context)
        
        # Check filtering works
        alvara_fases = response.context['alvara_fases']
        requerimento_fases = response.context['requerimento_fases']
        
        # Should only see phases for respective types + ambos
        alvara_tipos = set(alvara_fases.values_list('tipo', flat=True))
        self.assertTrue(alvara_tipos.issubset({'alvara', 'ambos'}))


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


class PrecatorioViewFilterTest(TestCase):
    """Test precatorio list view filtering functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test precatorios with different attributes
        self.precatorio1 = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            data_oficio=date(2023, 1, 15),
            orcamento=2023,
            origem='Tribunal de São Paulo',
            quitado=False,
            valor_de_face=10000.00,
            ultima_atualizacao=10000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            prioridade_deferida=True,
            acordo_deferido=False
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='2345678-90.2023.8.26.0200',
            data_oficio=date(2023, 2, 20),
            orcamento=2023,
            origem='Tribunal de Campinas',
            quitado=True,
            valor_de_face=20000.00,
            ultima_atualizacao=20000.00,
            data_ultima_atualizacao=date(2023, 2, 20),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        self.precatorio3 = Precatorio.objects.create(
            cnj='3456789-01.2023.8.26.0300',
            data_oficio=date(2023, 3, 25),
            orcamento=2023,
            origem='Tribunal de Santos',
            quitado=False,
            valor_de_face=15000.00,
            ultima_atualizacao=15000.00,
            data_ultima_atualizacao=date(2023, 3, 25),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            prioridade_deferida=False,
            acordo_deferido=False
        )
    
    def test_precatorio_list_no_filters(self):
        """Test precatorio list view without filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Consultar Precatórios')
        self.assertEqual(len(response.context['precatorios']), 3)
    
    def test_filter_by_cnj(self):
        """Test filtering by CNJ"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?cnj=1234567')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        self.assertEqual(precatorios[0].cnj, '1234567-89.2023.8.26.0100')
    
    def test_filter_by_origem(self):
        """Test filtering by origem"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?origem=São Paulo')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        self.assertEqual(precatorios[0].origem, 'Tribunal de São Paulo')
    
    def test_filter_by_quitado_true(self):
        """Test filtering by quitado status (true)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?quitado=true')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        self.assertTrue(precatorios[0].quitado)
    
    def test_filter_by_quitado_false(self):
        """Test filtering by quitado status (false)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?quitado=false')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 2)
        for precatorio in precatorios:
            self.assertFalse(precatorio.quitado)
    
    def test_filter_by_prioridade_true(self):
        """Test filtering by prioridade status (true)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?prioridade=true')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        self.assertTrue(precatorios[0].prioridade_deferida)
    
    def test_filter_by_prioridade_false(self):
        """Test filtering by prioridade status (false)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?prioridade=false')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 2)
        for precatorio in precatorios:
            self.assertFalse(precatorio.prioridade_deferida)
    
    def test_multiple_filters(self):
        """Test combining multiple filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?quitado=false&prioridade=true')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        self.assertFalse(precatorios[0].quitado)
        self.assertTrue(precatorios[0].prioridade_deferida)
    
    def test_filter_context_values(self):
        """Test that current filter values are passed to template context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?cnj=test&origem=tribunal&quitado=true&prioridade=false')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_cnj'], 'test')
        self.assertEqual(response.context['current_origem'], 'tribunal')
        self.assertEqual(response.context['current_quitado'], 'true')
        self.assertEqual(response.context['current_prioridade'], 'false')


class ClienteViewFilterTest(TestCase):
    """Test cliente list view filtering functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test precatorios
        self.precatorio1 = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            data_oficio=date(2023, 1, 15),
            orcamento=2023,
            origem='Tribunal de São Paulo',
            quitado=False,
            valor_de_face=10000.00,
            ultima_atualizacao=10000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            prioridade_deferida=True,
            acordo_deferido=False
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='2345678-90.2023.8.26.0200',
            data_oficio=date(2023, 2, 20),
            orcamento=2023,
            origem='Tribunal de Campinas',
            quitado=True,
            valor_de_face=20000.00,
            ultima_atualizacao=20000.00,
            data_ultima_atualizacao=date(2023, 2, 20),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        # Create test clientes with different attributes
        self.cliente1 = Cliente.objects.create(
            cpf='11111111111',
            nome='João Silva Santos',
            nascimento=date(1980, 5, 15),
            prioridade=True
        )
        
        self.cliente2 = Cliente.objects.create(
            cpf='22222222222',
            nome='Maria Santos Oliveira',
            nascimento=date(1975, 8, 20),
            prioridade=False
        )
        
        self.cliente3 = Cliente.objects.create(
            cpf='33333333333',
            nome='Pedro Costa Lima',
            nascimento=date(1985, 12, 10),
            prioridade=False
        )
        
        # Link clientes to precatorios
        self.precatorio1.clientes.add(self.cliente1, self.cliente2)
        self.precatorio2.clientes.add(self.cliente3)
    
    def test_cliente_list_no_filters(self):
        """Test cliente list view without filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de Clientes')
        self.assertEqual(len(response.context['clientes']), 3)
    
    def test_filter_by_nome(self):
        """Test filtering by nome"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?nome=João')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'João Silva Santos')
    
    def test_filter_by_nome_partial(self):
        """Test filtering by partial nome match"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?nome=Santos')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 2)  # João Silva Santos and Maria Santos Oliveira
    
    def test_filter_by_cpf(self):
        """Test filtering by CPF"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?cpf=111111')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].cpf, '11111111111')
    
    def test_filter_by_prioridade_true(self):
        """Test filtering by prioridade (true)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?prioridade=true')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertTrue(clientes[0].prioridade)
        self.assertEqual(clientes[0].nome, 'João Silva Santos')
    
    def test_filter_by_prioridade_false(self):
        """Test filtering by prioridade (false)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?prioridade=false')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 2)
        for cliente in clientes:
            self.assertFalse(cliente.prioridade)
    
    def test_filter_by_precatorio(self):
        """Test filtering by precatorio CNJ"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?precatorio=1234567')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 2)  # João and Maria are linked to precatorio1
        cliente_names = [c.nome for c in clientes]
        self.assertIn('João Silva Santos', cliente_names)
        self.assertIn('Maria Santos Oliveira', cliente_names)
    
    def test_multiple_filters(self):
        """Test combining multiple filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?nome=Santos&prioridade=false')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'Maria Santos Oliveira')
        self.assertFalse(clientes[0].prioridade)
    
    def test_filter_context_values(self):
        """Test that current filter values are passed to template context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?nome=test&cpf=123&prioridade=true&precatorio=cnj123')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_nome'], 'test')
        self.assertEqual(response.context['current_cpf'], '123')
        self.assertEqual(response.context['current_prioridade'], 'true')
        self.assertEqual(response.context['current_precatorio'], 'cnj123')


class AlvaraViewFilterTest(TestCase):
    """Test alvara list view filtering functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create phases for alvaras
        self.fase1 = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        self.fase2 = Fase.objects.create(
            nome='Depósito Judicial',
            tipo='alvara',
            cor='#4ECDC4',
            ativa=True
        )
        
        # Create test precatorios
        self.precatorio1 = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            data_oficio=date(2023, 1, 15),
            orcamento=2023,
            origem='Tribunal de São Paulo',
            quitado=False,
            valor_de_face=10000.00,
            ultima_atualizacao=10000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            prioridade_deferida=True,
            acordo_deferido=False
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='2345678-90.2023.8.26.0200',
            data_oficio=date(2023, 2, 20),
            orcamento=2023,
            origem='Tribunal de Campinas',
            quitado=True,
            valor_de_face=20000.00,
            ultima_atualizacao=20000.00,
            data_ultima_atualizacao=date(2023, 2, 20),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        # Create test clientes
        self.cliente1 = Cliente.objects.create(
            cpf='11111111111',
            nome='João Silva Santos',
            nascimento=date(1980, 5, 15),
            prioridade=True
        )
        
        self.cliente2 = Cliente.objects.create(
            cpf='22222222222',
            nome='Maria Costa Oliveira',
            nascimento=date(1975, 8, 20),
            prioridade=False
        )
        
        # Create test alvaras
        self.alvara1 = Alvara.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente1,
            valor_principal=5000.00,
            honorarios_contratuais=1500.00,
            honorarios_sucumbenciais=500.00,
            tipo='aguardando depósito',
            fase=self.fase1
        )
        
        self.alvara2 = Alvara.objects.create(
            precatorio=self.precatorio2,
            cliente=self.cliente2,
            valor_principal=8000.00,
            honorarios_contratuais=2400.00,
            honorarios_sucumbenciais=800.00,
            tipo='depósito judicial',
            fase=self.fase2
        )
        
        self.alvara3 = Alvara.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente2,
            valor_principal=3000.00,
            honorarios_contratuais=900.00,
            honorarios_sucumbenciais=300.00,
            tipo='recebido pelo cliente',
            fase=self.fase1
        )
    
    def test_alvara_list_no_filters(self):
        """Test alvara list view without filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/alvaras/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de Alvarás')
        self.assertEqual(len(response.context['alvaras']), 3)
    
    def test_filter_by_nome(self):
        """Test filtering by client nome"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/alvaras/?nome=João')
        
        self.assertEqual(response.status_code, 200)
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(alvaras[0].cliente.nome, 'João Silva Santos')
    
    def test_filter_by_nome_partial(self):
        """Test filtering by partial nome match"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/alvaras/?nome=Costa')
        
        self.assertEqual(response.status_code, 200)
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 2)  # Maria appears in 2 alvaras (alvara2 and alvara3)
        for alvara in alvaras:
            self.assertIn('Costa', alvara.cliente.nome)
    
    def test_filter_by_precatorio(self):
        """Test filtering by precatorio CNJ"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/alvaras/?precatorio=1234567')
        
        self.assertEqual(response.status_code, 200)
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 2)  # alvara1 and alvara3 belong to precatorio1
        for alvara in alvaras:
            self.assertIn('1234567', alvara.precatorio.cnj)
    
    def test_filter_by_tipo(self):
        """Test filtering by alvara tipo"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/alvaras/?tipo=aguardando depósito')
        
        self.assertEqual(response.status_code, 200)
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(alvaras[0].tipo, 'aguardando depósito')
    
    def test_filter_by_fase(self):
        """Test filtering by fase nome"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/alvaras/?fase=Aguardando Depósito')
        
        self.assertEqual(response.status_code, 200)
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 2)  # alvara1 and alvara3 both use fase1 (Aguardando Depósito)
        for alvara in alvaras:
            self.assertEqual(alvara.fase.nome, 'Aguardando Depósito')
    
    def test_multiple_filters(self):
        """Test combining multiple filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/alvaras/?nome=Maria&tipo=recebido pelo cliente')
        
        self.assertEqual(response.status_code, 200)
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(alvaras[0].cliente.nome, 'Maria Costa Oliveira')
        self.assertEqual(alvaras[0].tipo, 'recebido pelo cliente')
    
    def test_filter_context_values(self):
        """Test that current filter values are passed to template context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/alvaras/?nome=test&precatorio=cnj123&tipo=aguardando&fase=fase1')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_nome'], 'test')
        self.assertEqual(response.context['current_precatorio'], 'cnj123')
        self.assertEqual(response.context['current_tipo'], 'aguardando')
        self.assertEqual(response.context['current_fase'], 'fase1')
    
    def test_filter_by_multiple_types(self):
        """Test filtering returns different tipos"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test depósito judicial (exact match)
        response = self.client.get('/alvaras/?tipo=depósito judicial')
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(alvaras[0].tipo, 'depósito judicial')
        
        # Test recebido pelo cliente (exact match)
        response = self.client.get('/alvaras/?tipo=recebido pelo cliente')
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(alvaras[0].tipo, 'recebido pelo cliente')


# Run tests with: python manage.py test precapp
