"""
Test cases for all models in the precatorios application.
Contains all model-related tests migrated from the monolithic tests.py file.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from precapp.models import (
    Fase, FaseHonorariosContratuais, Precatorio, Cliente, 
    Alvara, Requerimento, TipoDiligencia, Diligencias
)


class FaseModelTest(TestCase):
    """Test cases for Fase model"""
    
    def setUp(self):
        """Set up test data"""
        self.fase_data = {
            'nome': 'Em Andamento',
            'tipo': 'alvara',
            'cor': '#4ECDC4',
            'ativa': True
        }
    
    def test_fase_creation(self):
        """Test creating a fase with valid data"""
        fase = Fase(**self.fase_data)
        fase.full_clean()  # This should not raise ValidationError
        fase.save()
        self.assertEqual(fase.nome, 'Em Andamento')
        self.assertEqual(fase.tipo, 'alvara')
        self.assertEqual(fase.cor, '#4ECDC4')
        self.assertTrue(fase.ativa)
    
    def test_fase_str_method(self):
        """Test the __str__ method of Fase"""
        fase = Fase(**self.fase_data)
        expected_str = fase.nome
        self.assertEqual(str(fase), expected_str)
    
    def test_fase_required_fields(self):
        """Test that required fields are enforced"""
        # Test without nome (nome is required)
        with self.assertRaises(ValidationError):
            fase = Fase(tipo='alvara', cor='#4ECDC4', ativa=True)
            fase.full_clean()
        
        # Since tipo has a default value, this should not raise an error
        # Test valid creation with just nome
        fase = Fase(nome='Test')
        fase.full_clean()  # Should pass
    
    def test_fase_choices_validation(self):
        """Test that tipo field accepts only valid choices"""
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
    """Test cases for FaseHonorariosContratuais model"""
    
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


class PrecatorioModelTest(TestCase):
    """Test cases for Precatorio model"""
    
    def setUp(self):
        """Set up test data"""
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
            'honorarios_sucumbenciais': 'pendente'
        }
    
    def test_precatorio_creation(self):
        """Test creating a precatorio with valid data"""
        precatorio = Precatorio(**self.precatorio_data)
        precatorio.full_clean()
        precatorio.save()
        self.assertEqual(precatorio.cnj, '1234567-89.2023.8.26.0100')
        self.assertEqual(precatorio.orcamento, 2023)
        self.assertEqual(precatorio.valor_de_face, 100000.00)
    
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


class ClienteModelTest(TestCase):
    """Test cases for Cliente model"""
    
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
    """Test cases for Alvara model"""
    
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


class RequerimentoModelTest(TestCase):
    """Test cases for Requerimento model"""
    
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
    """Test cases for TipoDiligencia model"""
    
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
    """Test cases for Diligencias model"""
    
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
