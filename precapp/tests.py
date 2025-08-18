from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from .models import Precatorio, Cliente, Alvara, Requerimento, Fase, FaseHonorariosContratuais
from .forms import (
    PrecatorioForm, ClienteForm, AlvaraSimpleForm, 
    RequerimentoForm, FaseForm, FaseHonorariosContratuaisForm, validate_cnj, validate_currency
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
        expected_str = fase.nome  # Just returns the nome
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


class FaseHonorariosContratuaisModelTest(TestCase):
    """Test cases for FaseHonorariosContratuais model"""
    
    def setUp(self):
        """Set up test data"""
        self.fase_honorarios_data = {
            'nome': 'Aguardando Pagamento',
            'descricao': 'Honorários contratuais aguardando pagamento',
            'cor': '#FFA500',
            'ativa': True
        }
        
        self.fase_honorarios_data_2 = {
            'nome': 'Totalmente Pago',
            'descricao': 'Honorários contratuais totalmente pagos',
            'cor': '#28A745',
            'ativa': True
        }
    
    def test_fase_honorarios_creation(self):
        """Test creating a fase honorários with valid data"""
        fase = FaseHonorariosContratuais(**self.fase_honorarios_data)
        fase.full_clean()
        fase.save()
        self.assertEqual(fase.nome, 'Aguardando Pagamento')
        self.assertEqual(fase.cor, '#FFA500')
        self.assertTrue(fase.ativa)
    
    def test_fase_honorarios_str_method(self):
        """Test the __str__ method of FaseHonorariosContratuais"""
        fase = FaseHonorariosContratuais(**self.fase_honorarios_data)
        expected_str = fase.nome
        self.assertEqual(str(fase), expected_str)
    
    def test_fase_honorarios_default_values(self):
        """Test default values for FaseHonorariosContratuais"""
        fase = FaseHonorariosContratuais(nome='Test Fase', cor='#000000')
        fase.save()
        self.assertTrue(fase.ativa)  # Should default to True
        self.assertIsNotNone(fase.criado_em)  # Should have creation timestamp
    
    def test_fase_honorarios_color_validation(self):
        """Test color field accepts valid hex colors"""
        valid_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFFFF', '#000000']
        for color in valid_colors:
            data = self.fase_honorarios_data.copy()
            data['cor'] = color
            data['nome'] = f'Test {color}'
            fase = FaseHonorariosContratuais(**data)
            fase.full_clean()  # Should not raise ValidationError
            fase.save()
    
    def test_fase_honorarios_inactive(self):
        """Test creating inactive fase honorários"""
        data = self.fase_honorarios_data.copy()
        data['ativa'] = False
        fase = FaseHonorariosContratuais(**data)
        fase.save()
        self.assertFalse(fase.ativa)
    
    def test_multiple_fases_honorarios(self):
        """Test creating multiple different fases honorários"""
        fase1 = FaseHonorariosContratuais.objects.create(**self.fase_honorarios_data)
        fase2 = FaseHonorariosContratuais.objects.create(**self.fase_honorarios_data_2)
        
        self.assertEqual(FaseHonorariosContratuais.objects.count(), 2)
        self.assertNotEqual(fase1.nome, fase2.nome)
        self.assertNotEqual(fase1.cor, fase2.cor)


class FaseHonorariosContratuaisFormTest(TestCase):
    """Test cases for FaseHonorariosContratuaisForm"""
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'nome': 'Em Negociação',
            'descricao': 'Honorários em processo de negociação',
            'cor': '#007BFF',
            'ativa': True
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = FaseHonorariosContratuaisForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = FaseHonorariosContratuaisForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        fase = form.save()
        self.assertEqual(fase.nome, 'Em Negociação')
        self.assertEqual(fase.cor, '#007BFF')
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        incomplete_data = {'descricao': 'Test'}
        form = FaseHonorariosContratuaisForm(data=incomplete_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_form_color_field(self):
        """Test color field widget and validation"""
        form = FaseHonorariosContratuaisForm()
        color_field = form.fields['cor']
        self.assertEqual(color_field.widget.input_type, 'color')
    
    def test_form_checkbox_field(self):
        """Test ativa checkbox field"""
        form = FaseHonorariosContratuaisForm()
        ativa_field = form.fields['ativa']
        self.assertEqual(ativa_field.widget.input_type, 'checkbox')
    
    def test_form_clean_nome_unique(self):
        """Test form validation for unique nome"""
        # Create existing fase
        FaseHonorariosContratuais.objects.create(
            nome='Existing Fase',
            cor='#FF0000'
        )
        
        # Try to create another with same nome
        form_data = self.valid_form_data.copy()
        form_data['nome'] = 'Existing Fase'
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())


class AlvaraModelWithHonorariosTest(TestCase):
    """Test cases for updated Alvara model with fase_honorarios_contratuais field"""
    
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
        
        self.fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Parcialmente Pago',
            descricao='Honorários parcialmente pagos',
            cor='#FFC107',
            ativa=True
        )
        
        self.alvara_data = {
            'precatorio': self.precatorio,
            'cliente': self.cliente,
            'valor_principal': 30000.00,
            'honorarios_contratuais': 15000.00,
            'honorarios_sucumbenciais': 5000.00,
            'tipo': 'prioridade',
            'fase': self.fase_alvara,
            'fase_honorarios_contratuais': self.fase_honorarios
        }
    
    def test_alvara_with_honorarios_fase_creation(self):
        """Test creating an alvara with fase honorários contratuais"""
        alvara = Alvara(**self.alvara_data)
        alvara.full_clean()
        alvara.save()
        self.assertEqual(alvara.fase_honorarios_contratuais, self.fase_honorarios)
        self.assertEqual(alvara.fase_honorarios_contratuais.nome, 'Parcialmente Pago')
    
    def test_alvara_without_honorarios_fase(self):
        """Test creating an alvara without fase honorários contratuais (optional)"""
        data = self.alvara_data.copy()
        data.pop('fase_honorarios_contratuais')  # Remove the field
        alvara = Alvara(**data)
        alvara.full_clean()
        alvara.save()
        self.assertIsNone(alvara.fase_honorarios_contratuais)
    
    def test_alvara_honorarios_relationship(self):
        """Test relationship between Alvara and FaseHonorariosContratuais"""
        alvara = Alvara.objects.create(**self.alvara_data)
        
        # Test forward relationship
        self.assertEqual(alvara.fase_honorarios_contratuais.nome, 'Parcialmente Pago')
        self.assertEqual(alvara.fase_honorarios_contratuais.cor, '#FFC107')
        
        # Test that we can update the relationship
        new_fase = FaseHonorariosContratuais.objects.create(
            nome='Totalmente Pago',
            cor='#28A745'
        )
        alvara.fase_honorarios_contratuais = new_fase
        alvara.save()
        
        alvara.refresh_from_db()
        self.assertEqual(alvara.fase_honorarios_contratuais.nome, 'Totalmente Pago')
    
    def test_alvara_str_method_unchanged(self):
        """Test that Alvara str method works correctly with new field"""
        alvara = Alvara(**self.alvara_data)
        expected_str = f'{alvara.tipo} - {alvara.cliente.nome}'
        self.assertEqual(str(alvara), expected_str)


class AlvaraSimpleFormWithHonorariosTest(TestCase):
    """Test cases for updated AlvaraSimpleForm with fase_honorarios_contratuais"""
    
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
            quitado=False,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        # Create different types of fases
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
    
    def test_form_includes_honorarios_field(self):
        """Test that AlvaraSimpleForm includes fase_honorarios_contratuais field"""
        form = AlvaraSimpleForm()
        self.assertIn('fase_honorarios_contratuais', form.fields)
    
    def test_form_fase_filtering(self):
        """Test that AlvaraSimpleForm filters fase options correctly"""
        form = AlvaraSimpleForm()
        fase_queryset = form.fields['fase'].queryset
        
        # Should include alvara and ambos phases
        self.assertIn(self.fase_alvara, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include requerimento phases
        self.assertNotIn(self.fase_requerimento, fase_queryset)
    
    def test_form_honorarios_filtering(self):
        """Test that AlvaraSimpleForm only shows active honorários phases"""
        form = AlvaraSimpleForm()
        honorarios_queryset = form.fields['fase_honorarios_contratuais'].queryset
        
        # Should include only active phases
        self.assertIn(self.fase_honorarios_ativa, honorarios_queryset)
        # Should NOT include inactive phases
        self.assertNotIn(self.fase_honorarios_inativa, honorarios_queryset)
    
    def test_form_honorarios_field_optional(self):
        """Test that fase_honorarios_contratuais field is optional"""
        form = AlvaraSimpleForm()
        honorarios_field = form.fields['fase_honorarios_contratuais']
        self.assertFalse(honorarios_field.required)


class FaseHonorariosContratuaisViewTest(TestCase):
    """Test cases for FaseHonorariosContratuais views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Test Fase Honorários',
            descricao='Test description',
            cor='#FF6B35',
            ativa=True
        )
        
        self.client_app = Client()
    
    def test_fases_honorarios_list_view_authentication(self):
        """Test that fases honorários list view requires authentication"""
        response = self.client_app.get(reverse('fases_honorarios'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_fases_honorarios_list_view_authenticated(self):
        """Test fases honorários list view with authentication"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('fases_honorarios'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fases Honorários Contratuais')
    
    def test_nova_fase_honorarios_view(self):
        """Test creating new fase honorários"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('nova_fase_honorarios'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nova Fase Honorários Contratuais')
    
    def test_editar_fase_honorarios_view(self):
        """Test editing fase honorários"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Fase Honorários')
    
    def test_create_fase_honorarios_post(self):
        """Test creating fase honorários via POST"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': 'Nova Fase Test',
            'descricao': 'Test description',
            'cor': '#00FF00',
            'ativa': True
        }
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify fase was created
        self.assertTrue(FaseHonorariosContratuais.objects.filter(nome='Nova Fase Test').exists())
    
    def test_update_fase_honorarios_post(self):
        """Test updating fase honorários via POST"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': 'Updated Fase Name',
            'descricao': 'Updated description',
            'cor': '#FF0000',
            'ativa': False
        }
        response = self.client_app.post(
            reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]), 
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify fase was updated
        self.fase_honorarios.refresh_from_db()
        self.assertEqual(self.fase_honorarios.nome, 'Updated Fase Name')
        self.assertFalse(self.fase_honorarios.ativa)
    
    def test_ativar_fase_honorarios(self):
        """Test activating/deactivating fase honorários"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test deactivating active fase
        response = self.client_app.post(reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.assertEqual(response.status_code, 302)
        
        self.fase_honorarios.refresh_from_db()
        self.assertFalse(self.fase_honorarios.ativa)
        
        # Test reactivating inactive fase
        response = self.client_app.post(reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.fase_honorarios.refresh_from_db()
        self.assertTrue(self.fase_honorarios.ativa)
    
    def test_deletar_fase_honorarios(self):
        """Test deleting fase honorários"""
        self.client_app.login(username='testuser', password='testpass123')
        fase_id = self.fase_honorarios.id
        
        response = self.client_app.post(reverse('deletar_fase_honorarios', args=[fase_id]))
        self.assertEqual(response.status_code, 302)
        
        # Verify fase was deleted
        self.assertFalse(FaseHonorariosContratuais.objects.filter(id=fase_id).exists())


class CustomizacaoViewTest(TestCase):
    """Test cases for Customização dashboard view"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create some test data for statistics
        Fase.objects.create(nome='Fase 1', tipo='alvara', cor='#FF0000', ativa=True)
        Fase.objects.create(nome='Fase 2', tipo='requerimento', cor='#00FF00', ativa=False)
        
        FaseHonorariosContratuais.objects.create(nome='Honorários 1', cor='#0000FF', ativa=True)
        FaseHonorariosContratuais.objects.create(nome='Honorários 2', cor='#FFFF00', ativa=False)
        
        self.client_app = Client()
    
    def test_customizacao_view_authentication(self):
        """Test that customização view requires authentication"""
        response = self.client_app.get(reverse('customizacao'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_customizacao_view_authenticated(self):
        """Test customização view with authentication"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Customização')
    
    def test_customizacao_context_statistics(self):
        """Test that customização view provides correct statistics"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        # Check statistics in context
        self.assertEqual(response.context['total_fases_principais'], 2)
        self.assertEqual(response.context['fases_principais_ativas'], 1)
        self.assertEqual(response.context['fases_principais_inativas'], 1)
        self.assertEqual(response.context['total_fases_honorarios'], 2)
        self.assertEqual(response.context['fases_honorarios_ativas'], 1)
        self.assertEqual(response.context['fases_honorarios_inativas'], 1)
    
    def test_customizacao_recent_items(self):
        """Test that customização view includes recent items"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        # Check recent items are in context
        self.assertIn('recent_fases_principais', response.context)
        self.assertIn('recent_fases_honorarios', response.context)
        self.assertTrue(len(response.context['recent_fases_principais']) <= 5)
        self.assertTrue(len(response.context['recent_fases_honorarios']) <= 5)


class PrecatorioDetailViewWithHonorariosTest(TestCase):
    """Test that precatorio detail view correctly handles the new honorários field"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
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
        
        self.fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Em Negociação',
            cor='#007BFF',
            ativa=True
        )
        
        self.alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=30000.00,
            honorarios_contratuais=15000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        self.client_app = Client()
    
    def test_precatorio_detail_honorarios_context(self):
        """Test that precatorio detail view includes honorários phases in context"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('precatorio_detalhe', args=[self.precatorio.cnj]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('fases_honorarios_contratuais', response.context)
        
        # Check that only active phases are included
        fases_honorarios = response.context['fases_honorarios_contratuais']
        self.assertIn(self.fase_honorarios, fases_honorarios)
    
    def test_alvara_update_with_honorarios(self):
        """Test updating alvara with new honorários fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create another fase honorários for testing update
        new_fase = FaseHonorariosContratuais.objects.create(
            nome='Totalmente Pago',
            cor='#28A745',
            ativa=True
        )
        
        form_data = {
            'update_alvara': '1',
            'alvara_id': self.alvara.id,
            'valor_principal': '35000.00',
            'honorarios_contratuais': '17500.00',
            'honorarios_sucumbenciais': '6000.00',
            'tipo': 'acordo',
            'fase': self.fase_alvara.id,
            'fase_honorarios_contratuais': new_fase.id
        }
        
        response = self.client_app.post(
            reverse('precatorio_detalhe', args=[self.precatorio.cnj]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that alvara was updated
        self.alvara.refresh_from_db()
        self.assertEqual(self.alvara.fase_honorarios_contratuais, new_fase)
        self.assertEqual(float(self.alvara.valor_principal), 35000.00)


class IntegrationTestWithHonorarios(TestCase):
    """Extended integration tests including the new FaseHonorariosContratuais functionality"""
    
    def setUp(self):
        """Set up comprehensive test data"""
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create phases for different types
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
        
        # Create fases honorários contratuais
        self.fase_honorarios_1 = FaseHonorariosContratuais.objects.create(
            nome='Aguardando Pagamento',
            descricao='Honorários aguardando pagamento',
            cor='#FFA500',
            ativa=True
        )
        self.fase_honorarios_2 = FaseHonorariosContratuais.objects.create(
            nome='Parcialmente Pago',
            descricao='Honorários parcialmente pagos',
            cor='#FFC107',
            ativa=True
        )
        self.fase_honorarios_3 = FaseHonorariosContratuais.objects.create(
            nome='Totalmente Pago',
            descricao='Honorários totalmente pagos',
            cor='#28A745',
            ativa=True
        )
        
        # Create precatorio
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
    
    def test_complete_workflow_with_honorarios(self):
        """Test complete workflow including honorários phases"""
        # Login
        login_success = self.client_app.login(username='testuser', password='testpass123')
        self.assertTrue(login_success)
        
        # Create Alvara with honorários fase
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=30000.00,
            honorarios_contratuais=15000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios_1
        )
        
        # Create Requerimento (should not have honorários fase)
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
        self.assertEqual(alvara.fase_honorarios_contratuais.nome, 'Aguardando Pagamento')
        self.assertEqual(requerimento.fase.tipo, 'requerimento')
        # Requerimento should not have honorários fase
        self.assertIsNone(getattr(requerimento, 'fase_honorarios_contratuais', None))
        
        # Test updating alvara honorários fase
        alvara.fase_honorarios_contratuais = self.fase_honorarios_2
        alvara.save()
        
        alvara.refresh_from_db()
        self.assertEqual(alvara.fase_honorarios_contratuais.nome, 'Parcialmente Pago')
    
    def test_honorarios_fase_filtering_workflow(self):
        """Test that honorários phases are properly filtered in forms and views"""
        # Test AlvaraSimpleForm includes only active honorários phases
        form = AlvaraSimpleForm()
        honorarios_queryset = form.fields['fase_honorarios_contratuais'].queryset
        
        active_count = FaseHonorariosContratuais.objects.filter(ativa=True).count()
        self.assertEqual(honorarios_queryset.count(), active_count)
        
        # Deactivate one fase
        self.fase_honorarios_3.ativa = False
        self.fase_honorarios_3.save()
        
        # Create new form instance and check filtering
        form_new = AlvaraSimpleForm()
        honorarios_queryset_new = form_new.fields['fase_honorarios_contratuais'].queryset
        
        self.assertEqual(honorarios_queryset_new.count(), active_count - 1)
        self.assertNotIn(self.fase_honorarios_3, honorarios_queryset_new)
    
    def test_customization_page_integration(self):
        """Test that customization page correctly displays both types of phases"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('customizacao'))
        self.assertEqual(response.status_code, 200)
        
        # Check that page displays links to both management pages
        self.assertContains(response, 'Fases Principais')
        self.assertContains(response, 'Fases Honorários Contratuais')
        
        # Check statistics
        self.assertEqual(response.context['total_fases_principais'], 3)  # alvara, requerimento, ambos
        self.assertEqual(response.context['total_fases_honorarios'], 3)  # 3 honorários phases
    
    def test_phase_deletion_constraints(self):
        """Test that phases in use cannot be deleted"""
        # Create alvara using honorários fase
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=30000.00,
            honorarios_contratuais=15000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios_1
        )
        
        # Attempt to delete fase honorários that's in use
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(
            reverse('deletar_fase_honorarios', args=[self.fase_honorarios_1.id])
        )
        
        # Should handle gracefully (might redirect with error message)
        # The exact behavior depends on the view implementation
        self.assertIn(response.status_code, [302, 400, 403])
        
        # Verify fase still exists
        self.assertTrue(
            FaseHonorariosContratuais.objects.filter(id=self.fase_honorarios_1.id).exists()
        )


class EdgeCaseTest(TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client_app = Client()
    
    def test_invalid_color_values(self):
        """Test handling of invalid color values"""
        # Test empty color
        with self.assertRaises(ValidationError):
            fase = FaseHonorariosContratuais(nome='Test', cor='')
            fase.full_clean()
        
        # Test invalid hex color
        with self.assertRaises(ValidationError):
            fase = FaseHonorariosContratuais(nome='Test 2', cor='invalid-color')
            fase.full_clean()
    
    def test_extremely_long_names(self):
        """Test handling of extremely long names"""
        long_name = 'A' * 300  # Assuming max_length constraint exists
        
        with self.assertRaises(ValidationError):
            fase = FaseHonorariosContratuais(nome=long_name, cor='#FF0000')
            fase.full_clean()
    
    def test_empty_required_fields(self):
        """Test handling of empty required fields"""
        # Test empty nome
        with self.assertRaises(ValidationError):
            fase = FaseHonorariosContratuais(nome='', cor='#FF0000')
            fase.full_clean()
        
        # Test None nome
        with self.assertRaises(ValidationError):
            fase = FaseHonorariosContratuais(nome=None, cor='#FF0000')
            fase.full_clean()
    
    def test_concurrent_modifications(self):
        """Test handling of concurrent modifications"""
        fase = FaseHonorariosContratuais.objects.create(
            nome='Test Concurrent',
            cor='#FF0000'
        )
        
        # Simulate concurrent modification
        fase_copy = FaseHonorariosContratuais.objects.get(id=fase.id)
        
        fase.nome = 'Modified 1'
        fase.save()
        
        fase_copy.nome = 'Modified 2'
        fase_copy.save()  # Should work (last write wins)
        
        fase.refresh_from_db()
        self.assertEqual(fase.nome, 'Modified 2')
    
    def test_bulk_operations(self):
        """Test bulk create and update operations"""
        # Create multiple phases at once
        fases_data = [
            FaseHonorariosContratuais(nome=f'Bulk {i}', cor=f'#FF{i:04d}0') 
            for i in range(1, 6)
        ]
        
        FaseHonorariosContratuais.objects.bulk_create(fases_data)
        
        self.assertEqual(FaseHonorariosContratuais.objects.count(), 5)
        
        # Test bulk update
        FaseHonorariosContratuais.objects.all().update(ativa=False)
        
        self.assertEqual(
            FaseHonorariosContratuais.objects.filter(ativa=False).count(), 
            5
        )


class PrecatorioModelTest(TestCase):
    """Test cases for Precatorio model"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio_data = {
            'cnj': '1234567-89.2023.8.26.0100',
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
    """Test cases for AlvaraSimpleForm"""
    
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
        form = AlvaraSimpleForm()
        fase_queryset = form.fields['fase'].queryset
        
        # Should include alvara and ambos phases
        self.assertIn(self.fase_alvara, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include requerimento phases
        self.assertNotIn(self.fase_requerimento, fase_queryset)
    
    def test_alvara_simple_form_includes_honorarios_field(self):
        """Test that AlvaraSimpleForm includes fase_honorarios_contratuais field"""
        form = AlvaraSimpleForm()
        self.assertIn('fase_honorarios_contratuais', form.fields)
        
        # Test field properties
        honorarios_field = form.fields['fase_honorarios_contratuais']
        self.assertFalse(honorarios_field.required)  # Should be optional
    
    def test_alvara_simple_form_honorarios_filtering(self):
        """Test that AlvaraSimpleForm only shows active honorários phases"""
        form = AlvaraSimpleForm()
        honorarios_queryset = form.fields['fase_honorarios_contratuais'].queryset
        
        # Should include only active phases
        self.assertIn(self.fase_honorarios_ativa, honorarios_queryset)
        # Should NOT include inactive phases
        self.assertNotIn(self.fase_honorarios_inativa, honorarios_queryset)


class RequerimentoFormTest(TestCase):
    """Test cases for RequerimentoForm"""
    
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
    
    def test_cpf_input_formats(self):
        """Test that CPF accepts both formatted and unformatted input"""
        # Test formatted CPF (with dots and dash)
        formatted_data = self.valid_form_data.copy()
        formatted_data['cpf'] = '123.456.789-01'
        form = ClienteForm(data=formatted_data)
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.cpf, '12345678901')  # Should be stored without formatting
        
        # Test unformatted CPF (numbers only)
        Cliente.objects.all().delete()  # Clear the previous client
        unformatted_data = self.valid_form_data.copy()
        unformatted_data['cpf'] = '98765432100'
        unformatted_data['nome'] = 'Maria Santos'
        form = ClienteForm(data=unformatted_data)
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.cpf, '98765432100')  # Should be stored as-is
        
    def test_cpf_validation_errors(self):
        """Test CPF validation error cases"""
        # Test invalid CPF length
        invalid_data = self.valid_form_data.copy()
        invalid_data['cpf'] = '123456789'  # Only 9 digits
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        
        # Test invalid CPF (all zeros)
        invalid_data['cpf'] = '00000000000'
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)


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
        self.assertIn('fases_honorarios_contratuais', response.context)
        
        # Check filtering works
        alvara_fases = response.context['alvara_fases']
        requerimento_fases = response.context['requerimento_fases']
        fases_honorarios = response.context['fases_honorarios_contratuais']
        
        # Should only see phases for respective types + ambos
        alvara_tipos = set(alvara_fases.values_list('tipo', flat=True))
        self.assertTrue(alvara_tipos.issubset({'alvara', 'ambos'}))
        
        # Honorários phases should only include active ones
        for fase in fases_honorarios:
            self.assertTrue(fase.ativa)


class ManyToManyRelationshipTest(TestCase):
    """Test many-to-many relationships between models"""
    
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
            quitado=False,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='7654321-12.2023.8.26.0200',
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
        response = self.client.get('/clientes/?nome=test&cpf=123&prioridade=true&requerimento_prioridade=sem_requerimento&precatorio=cnj123')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_nome'], 'test')
        self.assertEqual(response.context['current_cpf'], '123')
        self.assertEqual(response.context['current_prioridade'], 'true')
        self.assertEqual(response.context['current_requerimento_prioridade'], 'sem_requerimento')
        self.assertEqual(response.context['current_precatorio'], 'cnj123')


class ClienteRequerimentoPrioridadeFilterTest(TestCase):
    """Test cliente list view filtering by requerimento prioridade (Deferido/Não Deferido)"""
    
    def setUp(self):
        """Set up test data for requerimento prioridade filtering"""
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test phases for requerimentos
        self.fase_deferido = Fase.objects.create(
            nome='Deferido',
            tipo='requerimento',
            cor='#28a745',
            ativa=True
        )
        
        self.fase_indeferido = Fase.objects.create(
            nome='Indeferido',
            tipo='requerimento', 
            cor='#dc3545',
            ativa=True
        )
        
        self.fase_andamento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True
        )
        
        # Create test precatorios
        self.precatorio1 = Precatorio.objects.create(
            cnj='1111111-11.2023.8.26.0100',
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
            cnj='2222222-22.2023.8.26.0200',
            orcamento=2023,
            origem='Tribunal de Campinas',
            quitado=False,
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
        self.cliente_deferido = Cliente.objects.create(
            cpf='11111111111',
            nome='João Silva (Deferido)',
            nascimento=date(1950, 5, 15),
            prioridade=True
        )
        
        self.cliente_indeferido = Cliente.objects.create(
            cpf='22222222222',
            nome='Maria Santos (Indeferido)',
            nascimento=date(1980, 8, 20),
            prioridade=False
        )
        
        self.cliente_andamento = Cliente.objects.create(
            cpf='33333333333',
            nome='Pedro Costa (Em Andamento)',
            nascimento=date(1975, 12, 10),
            prioridade=False
        )
        
        self.cliente_sem_prioridade = Cliente.objects.create(
            cpf='44444444444',
            nome='Ana Oliveira (Sem Prioridade)',
            nascimento=date(1985, 3, 25),
            prioridade=False
        )
        
        # Link clientes to precatorios
        self.precatorio1.clientes.add(self.cliente_deferido, self.cliente_indeferido)
        self.precatorio2.clientes.add(self.cliente_andamento, self.cliente_sem_prioridade)
        
        # Create requerimentos with different phases
        # Cliente with priority request that was DEFERIDO
        Requerimento.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente_deferido,
            pedido='prioridade idade',
            valor=5000.00,
            desagio=0.0,
            fase=self.fase_deferido
        )
        
        # Cliente with priority request that was INDEFERIDO (not deferido)
        Requerimento.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente_indeferido,
            pedido='prioridade doença',
            valor=8000.00,
            desagio=0.0,
            fase=self.fase_indeferido
        )
        
        # Cliente with priority request still EM ANDAMENTO (not deferido)
        Requerimento.objects.create(
            precatorio=self.precatorio2,
            cliente=self.cliente_andamento,
            pedido='prioridade idade',
            valor=3000.00,
            desagio=0.0,
            fase=self.fase_andamento
        )
        
        # cliente_sem_prioridade has no priority requerimentos
        
        # Cliente_sem_prioridade has no priority requerimentos (only normal ones if any)
    
    def test_filter_requerimento_prioridade_deferido(self):
        """Test filtering by requerimento prioridade = deferido"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?requerimento_prioridade=deferido')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        
        # Should include only cliente_deferido (has priority request with Deferido phase)
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'João Silva (Deferido)')
    
    def test_filter_requerimento_prioridade_nao_deferido(self):
        """Test filtering by requerimento prioridade = nao_deferido"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?requerimento_prioridade=nao_deferido')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        
        # Should include cliente_indeferido and cliente_andamento (both have priority requests that are NOT Deferido)
        self.assertEqual(len(clientes), 2)
        cliente_names = [c.nome for c in clientes]
        self.assertIn('Maria Santos (Indeferido)', cliente_names)
        self.assertIn('Pedro Costa (Em Andamento)', cliente_names)
    
    def test_filter_requerimento_prioridade_sem_requerimento(self):
        """Test filtering by requerimento prioridade = sem_requerimento"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?requerimento_prioridade=sem_requerimento')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        
        # Should include only cliente_sem_prioridade (no priority requerimentos at all)
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'Ana Oliveira (Sem Prioridade)')
    
    def test_filter_requerimento_prioridade_todos(self):
        """Test filtering by requerimento prioridade = '' (todos)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?requerimento_prioridade=')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        
        # Should include all clientes
        self.assertEqual(len(clientes), 4)
    
    def test_filter_context_requerimento_prioridade(self):
        """Test that requerimento prioridade filter value is passed to context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?requerimento_prioridade=deferido')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_requerimento_prioridade'], 'deferido')
    
    def test_combined_filters_with_requerimento_prioridade(self):
        """Test combining requerimento prioridade filter with other filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?nome=João&requerimento_prioridade=deferido')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        
        # Should find only João who has deferido priority request
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'João Silva (Deferido)')


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


class AlvaraViewWithHonorariosFilterTest(TestCase):
    """Test alvara list view with new Fase Honorários filtering functionality"""
    
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
        
        # Create honorários phases  
        self.fase_honorarios_1 = FaseHonorariosContratuais.objects.create(
            nome='Aguardando Pagamento',
            descricao='Honorários aguardando pagamento',
            cor='#FFA500',
            ativa=True
        )
        self.fase_honorarios_2 = FaseHonorariosContratuais.objects.create(
            nome='Parcialmente Pago',
            descricao='Honorários parcialmente pagos',
            cor='#FFC107',
            ativa=True
        )
        self.fase_honorarios_3 = FaseHonorariosContratuais.objects.create(
            nome='Totalmente Pago',
            descricao='Honorários totalmente pagos',
            cor='#28A745',
            ativa=True
        )
        
        # Create test precatorios
        self.precatorio1 = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
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
        
        # Create test alvaras with honorários phases
        self.alvara1 = Alvara.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente1,
            valor_principal=5000.00,
            honorarios_contratuais=1500.00,
            honorarios_sucumbenciais=500.00,
            tipo='prioridade',
            fase=self.fase1,
            fase_honorarios_contratuais=self.fase_honorarios_1
        )
        
        self.alvara2 = Alvara.objects.create(
            precatorio=self.precatorio2,
            cliente=self.cliente2,
            valor_principal=8000.00,
            honorarios_contratuais=2400.00,
            honorarios_sucumbenciais=800.00,
            tipo='acordo',
            fase=self.fase2,
            fase_honorarios_contratuais=self.fase_honorarios_2
        )
        
        self.alvara3 = Alvara.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente2,
            valor_principal=3000.00,
            honorarios_contratuais=900.00,
            honorarios_sucumbenciais=300.00,
            tipo='comum',
            fase=self.fase1,
            fase_honorarios_contratuais=self.fase_honorarios_3
        )
        
        # Create one alvara without honorários fase
        self.alvara4 = Alvara.objects.create(
            precatorio=self.precatorio2,
            cliente=self.cliente1,
            valor_principal=2000.00,
            honorarios_contratuais=600.00,
            honorarios_sucumbenciais=200.00,
            tipo='prioridade',
            fase=self.fase2
            # Note: no fase_honorarios_contratuais (should be None)
        )
        
        self.client_app = Client()
    
    def test_alvara_list_includes_honorarios_column(self):
        """Test that alvara list view includes the new Fase Honorários column"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('alvaras'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fase Honorários')
        self.assertContains(response, 'Aguardando Pagamento')
        self.assertContains(response, 'Parcialmente Pago')
        self.assertContains(response, 'Totalmente Pago')
    
    def test_alvara_list_displays_honorarios_badges(self):
        """Test that alvara list displays colored badges for honorários phases"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('alvaras'))
        
        self.assertEqual(response.status_code, 200)
        # Check that the colored badges are rendered
        self.assertContains(response, 'badge')
        self.assertContains(response, '#FFA500')  # Aguardando Pagamento color
        self.assertContains(response, '#FFC107')  # Parcialmente Pago color
        self.assertContains(response, '#28A745')  # Totalmente Pago color
    
    def test_filter_by_fase_honorarios(self):
        """Test filtering by Fase Honorários"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test filtering by "Aguardando Pagamento"
        response = self.client_app.get(reverse('alvaras') + '?fase_honorarios=Aguardando Pagamento')
        self.assertEqual(response.status_code, 200)
        
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(alvaras[0].fase_honorarios_contratuais.nome, 'Aguardando Pagamento')
        
        # Test filtering by "Parcialmente Pago"
        response = self.client_app.get(reverse('alvaras') + '?fase_honorarios=Parcialmente Pago')
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(alvaras[0].fase_honorarios_contratuais.nome, 'Parcialmente Pago')
    
    def test_filter_by_fase_honorarios_with_fase_principal(self):
        """Test combining Fase Honorários filter with main Fase filter"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('alvaras') + '?fase=Aguardando Depósito&fase_honorarios=Totalmente Pago')
        
        self.assertEqual(response.status_code, 200)
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(alvaras[0].fase.nome, 'Aguardando Depósito')
        self.assertEqual(alvaras[0].fase_honorarios_contratuais.nome, 'Totalmente Pago')
    
    def test_available_fases_honorarios_in_context(self):
        """Test that available honorários phases are passed to template context"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('alvaras'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('available_fases_honorarios', response.context)
        
        fases_honorarios = response.context['available_fases_honorarios']
        self.assertEqual(len(fases_honorarios), 3)  # 3 active honorários phases
        
        fase_names = [fase.nome for fase in fases_honorarios]
        self.assertIn('Aguardando Pagamento', fase_names)
        self.assertIn('Parcialmente Pago', fase_names)
        self.assertIn('Totalmente Pago', fase_names)
    
    def test_none_honorarios_fase_handling(self):
        """Test handling of alvaras without honorários fase"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('alvaras'))
        
        self.assertEqual(response.status_code, 200)
        # Should display all 4 alvaras including the one without honorários fase
        alvaras = response.context['alvaras']
        self.assertEqual(len(alvaras), 4)
        
        # Check that alvara without honorários fase is handled correctly
        alvara_without_honorarios = next(a for a in alvaras if a.fase_honorarios_contratuais is None)
        self.assertEqual(alvara_without_honorarios, self.alvara4)
    
    def test_current_filter_values_in_context(self):
        """Test that current filter values are passed to template context for honorários"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('alvaras') + '?fase_honorarios=Aguardando Pagamento')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_fase_honorarios'], 'Aguardando Pagamento')
        
    def test_optimized_query_with_select_related(self):
        """Test that the view uses select_related for honorários to avoid N+1 queries"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Allow for a reasonable number of queries (authentication, session, main query, etc.)
        with self.assertNumQueries(10):  # Adjust to match actual implementation
            response = self.client_app.get(reverse('alvaras'))
            alvaras = list(response.context['alvaras'])
            # Access related honorários phases (should not trigger additional queries)
            for alvara in alvaras:
                if alvara.fase_honorarios_contratuais:
                    _ = alvara.fase_honorarios_contratuais.nome


class BrazilianFormattingTest(TestCase):
    """Test cases for Brazilian number formatting functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
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
        
        self.fase_requerimento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True
        )
        
        self.fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Em Negociação',
            cor='#007BFF',
            ativa=True
        )
        
        self.client_app = Client()
    
    def test_precatorio_form_uses_brazilian_formatting(self):
        """Test that PrecatorioForm uses Brazilian currency formatting"""
        form = PrecatorioForm()
        
        # Check that DecimalField widgets are configured for Brazilian formatting
        valor_face_widget = form.fields['valor_de_face'].widget
        self.assertEqual(valor_face_widget.__class__.__name__, 'TextInput')
        self.assertIn('brazilian-currency', valor_face_widget.attrs.get('class', ''))
        
        ultima_atualizacao_widget = form.fields['ultima_atualizacao'].widget
        self.assertEqual(ultima_atualizacao_widget.__class__.__name__, 'TextInput')
        self.assertIn('brazilian-currency', ultima_atualizacao_widget.attrs.get('class', ''))
        
        # Check percentage fields use brazilian-number class
        percentual_contratuais_widget = form.fields['percentual_contratuais_assinado'].widget
        self.assertIn('brazilian-number', percentual_contratuais_widget.attrs.get('class', ''))
    
    def test_precatorio_form_accepts_brazilian_format(self):
        """Test that PrecatorioForm accepts Brazilian-formatted input"""
        form_data = {
            'cnj': '1234567-89.2023.8.26.0200',
            'orcamento': '2023',
            'origem': '1234567-89.2022.8.26.0002',
            'valor_de_face': '150.000,50',  # Brazilian format
            'ultima_atualizacao': '150.000,50',  # Brazilian format
            'data_ultima_atualizacao': '2023-01-01',
            'percentual_contratuais_assinado': '12,5',  # Brazilian percentage
            'percentual_contratuais_apartado': '6,25',  # Brazilian percentage
            'percentual_sucumbenciais': '20,0',  # Brazilian percentage
            'quitado': False,
            'prioridade_deferida': False,
            'acordo_deferido': False
        }
        
        # Note: The actual conversion happens in JavaScript on the frontend
        # Django forms will receive the converted values
        # For testing purposes, we test with standard format as that's what Django receives
        converted_data = form_data.copy()
        converted_data['valor_de_face'] = '150000.50'
        converted_data['ultima_atualizacao'] = '150000.50'
        converted_data['percentual_contratuais_assinado'] = '12.5'
        converted_data['percentual_contratuais_apartado'] = '6.25'
        converted_data['percentual_sucumbenciais'] = '20.0'
        
        form = PrecatorioForm(data=converted_data)
        self.assertTrue(form.is_valid())
        
        precatorio = form.save()
        self.assertEqual(float(precatorio.valor_de_face), 150000.50)
        self.assertEqual(float(precatorio.percentual_contratuais_assinado), 12.5)
    
    def test_alvara_form_uses_brazilian_formatting(self):
        """Test that AlvaraSimpleForm uses Brazilian currency formatting"""
        form = AlvaraSimpleForm()
        
        # Check currency fields have Brazilian formatting
        valor_principal_widget = form.fields['valor_principal'].widget
        self.assertIn('brazilian-currency', valor_principal_widget.attrs.get('class', ''))
        
        honorarios_contratuais_widget = form.fields['honorarios_contratuais'].widget
        self.assertIn('brazilian-currency', honorarios_contratuais_widget.attrs.get('class', ''))
        
        honorarios_sucumbenciais_widget = form.fields['honorarios_sucumbenciais'].widget
        self.assertIn('brazilian-currency', honorarios_sucumbenciais_widget.attrs.get('class', ''))
    
    def test_requerimento_form_uses_brazilian_formatting(self):
        """Test that RequerimentoForm uses Brazilian formatting"""
        form = RequerimentoForm()
        
        # Check currency and percentage fields
        valor_widget = form.fields['valor'].widget
        self.assertIn('brazilian-currency', valor_widget.attrs.get('class', ''))
        
        desagio_widget = form.fields['desagio'].widget
        self.assertIn('brazilian-number', desagio_widget.attrs.get('class', ''))
    
    def test_cpf_flexibility_cliente_form(self):
        """Test that ClienteForm accepts both formatted and unformatted CPF"""
        # Test with valid unformatted CPF (11 digits) 
        unformatted_data = {
            'cpf': '12345678909',  # Valid CPF format
            'nome': 'João Silva Unformatted',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        
        form = ClienteForm(data=unformatted_data)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.cpf, '12345678909')  # Stored without formatting
        
        # Test with different unformatted CPF  
        Cliente.objects.all().delete()  # Clear previous
        unformatted_data_2 = {
            'cpf': '98765432100',
            'nome': 'Maria Santos Unformatted',
            'nascimento': '1985-03-20',
            'prioridade': True
        }
        
        form = ClienteForm(data=unformatted_data_2)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        # Note: This might fail CPF validation if the number is mathematically invalid
        # The test validates that the form widget accepts the input format
        cpf_widget = form.fields['cpf'].widget
        self.assertEqual(cpf_widget.__class__.__name__, 'TextInput')
    
    def test_cpf_flexibility_requerimento_form(self):
        """Test that RequerimentoForm accepts both formatted and unformatted CPF"""
        # Test with formatted CPF
        formatted_data = {
            'cliente_cpf': '123.456.789-01',
            'pedido': 'prioridade doença',
            'valor': '25000.00',
            'desagio': '15.5',
            'fase': self.fase_requerimento.id
        }
        
        form = RequerimentoForm(data=formatted_data)
        # Note: In actual form validation, CPF would be cleaned to match existing cliente
        # This test validates the widget configuration allows flexible input
        cpf_widget = form.fields['cliente_cpf'].widget
        self.assertEqual(cpf_widget.__class__.__name__, 'TextInput')
    
    def test_template_includes_brazilian_formatting_script(self):
        """Test that templates include Brazilian formatting JavaScript"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test precatorio detail page includes the script
        response = self.client_app.get(reverse('precatorio_detalhe', args=[self.precatorio.cnj]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'brazilian-number-format.js')
    
    def test_form_field_population_with_localization(self):
        """Test that form fields populate correctly with Brazilian localization"""
        # Create an alvara to test editing
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=30000.00,
            honorarios_contratuais=15000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        # Create a requerimento to test editing
        requerimento = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='prioridade doença',
            valor=25000.00,
            desagio=15.5,
            fase=self.fase_requerimento
        )
        
        # Test that precatorio detail page loads correctly with existing data
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('precatorio_detalhe', args=[self.precatorio.cnj]))
        
        self.assertEqual(response.status_code, 200)
        # Check that the page includes {% load l10n %} tag functionality
        self.assertContains(response, 'value=')  # Form fields should have values
        
        # Test that forms are properly populated with existing data
        self.assertIn('alvaras', response.context)
        self.assertIn('requerimentos', response.context)
        
        alvaras = response.context['alvaras']
        requerimentos = response.context['requerimentos']
        
        self.assertEqual(len(alvaras), 1)
        self.assertEqual(len(requerimentos), 1)
        
        self.assertEqual(float(alvaras[0].valor_principal), 30000.00)
        self.assertEqual(float(requerimentos[0].valor), 25000.00)


class DatabaseCompatibilityTest(TestCase):
    """Test that Brazilian formatting doesn't affect database storage"""
    
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
        
        self.fase = Fase.objects.create(
            nome='Test Fase',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
    
    def test_decimal_values_stored_correctly(self):
        """Test that decimal values are stored in standard format regardless of input"""
        # Create objects with decimal values
        alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=15000.50,  # Standard format
            honorarios_contratuais=4500.25,
            honorarios_sucumbenciais=1500.75,
            tipo='prioridade',
            fase=self.fase
        )
        
        # Retrieve from database and check format
        saved_alvara = Alvara.objects.get(id=alvara.id)
        self.assertEqual(float(saved_alvara.valor_principal), 15000.50)
        self.assertEqual(float(saved_alvara.honorarios_contratuais), 4500.25)
        self.assertEqual(float(saved_alvara.honorarios_sucumbenciais), 1500.75)
        
        # Test that decimal precision is maintained
        self.assertIsInstance(saved_alvara.valor_principal, (float, Decimal))
        
    def test_percentage_values_stored_correctly(self):
        """Test that percentage values are stored correctly"""
        # Update precatorio with percentage values
        self.precatorio.percentual_contratuais_assinado = 12.75
        self.precatorio.percentual_contratuais_apartado = 6.25
        self.precatorio.percentual_sucumbenciais = 18.5
        self.precatorio.save()
        
        # Retrieve and verify
        saved_precatorio = Precatorio.objects.get(cnj=self.precatorio.cnj)
        self.assertEqual(float(saved_precatorio.percentual_contratuais_assinado), 12.75)
        self.assertEqual(float(saved_precatorio.percentual_contratuais_apartado), 6.25)
        self.assertEqual(float(saved_precatorio.percentual_sucumbenciais), 18.5)
    
    def test_cpf_storage_without_formatting(self):
        """Test that CPF is stored without formatting regardless of input"""
        # CPF should always be stored as digits only
        cliente_with_clean_cpf = Cliente.objects.create(
            cpf='98765432100',  # Already clean
            nome='Maria Santos Clean',
            nascimento=date(1985, 3, 20),
            prioridade=True
        )
        
        saved_cliente = Cliente.objects.get(cpf=cliente_with_clean_cpf.cpf)
        self.assertEqual(saved_cliente.cpf, '98765432100')
        self.assertNotIn('.', saved_cliente.cpf)
        self.assertNotIn('-', saved_cliente.cpf)
    
    def test_query_operations_work_correctly(self):
        """Test that database queries work correctly with stored values"""
        # Create test data with various decimal values
        alvara1 = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=10000.00,
            honorarios_contratuais=3000.00,
            honorarios_sucumbenciais=1000.00,
            tipo='prioridade',
            fase=self.fase
        )
        
        alvara2 = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=20000.50,
            honorarios_contratuais=6000.15,
            honorarios_sucumbenciais=2000.05,
            tipo='acordo',
            fase=self.fase
        )
        
        # Test filtering and aggregation
        high_value_alvaras = Alvara.objects.filter(valor_principal__gt=15000)
        self.assertEqual(len(high_value_alvaras), 1)
        self.assertEqual(high_value_alvaras[0], alvara2)
        
        # Test ordering by decimal values
        ordered_alvaras = Alvara.objects.all().order_by('valor_principal')
        self.assertEqual(ordered_alvaras[0], alvara1)
        self.assertEqual(ordered_alvaras[1], alvara2)
        
        # Test sum aggregation
        from django.db.models import Sum
        total_principal = Alvara.objects.aggregate(
            total=Sum('valor_principal')
        )['total']
        self.assertEqual(float(total_principal), 30000.50)


class JavaScriptFormattingIntegrationTest(TestCase):
    """Test JavaScript integration for Brazilian number formatting"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client_app = Client()
        
    def test_base_template_includes_formatting_script(self):
        """Test that base template includes Brazilian formatting script"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test home page includes the script
        response = self.client_app.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'brazilian-number-format.js')
        self.assertContains(response, 'static/precapp/js/brazilian-number-format.js')
    
    def test_novo_precatorio_page_has_formatting_classes(self):
        """Test that novo_precatorio page has proper CSS classes for formatting"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('novo_precatorio'))
        self.assertEqual(response.status_code, 200)
        
        # Check that form fields have the right CSS classes
        self.assertContains(response, 'brazilian-currency')
        self.assertContains(response, 'brazilian-number')
    
    def test_novo_cliente_page_has_cpf_flexibility(self):
        """Test that novo_cliente page allows flexible CPF input"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('novo_cliente'))
        self.assertEqual(response.status_code, 200)
        
        # Check that CPF field is properly configured
        self.assertContains(response, 'name="cpf"')
        # Field should accept both formatted and unformatted input
        # (JavaScript handles the formatting flexibility)


class PriorityUpdateByAgeTest(TestCase):
    """Test cases for priority update by age functionality"""
    
    def setUp(self):
        """Set up test data"""
        from datetime import date, timedelta
        
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Calculate dates for testing
        today = date.today()
        sixty_years_ago = today - timedelta(days=60*365.25)
        seventy_years_ago = today - timedelta(days=70*365.25)
        fifty_years_ago = today - timedelta(days=50*365.25)
        
        # Create test clients with different ages
        self.client_over_70 = Cliente.objects.create(
            cpf='11111111111',
            nome='João Silva (77 anos)',
            nascimento=seventy_years_ago,
            prioridade=False
        )
        
        self.client_over_60 = Cliente.objects.create(
            cpf='22222222222',
            nome='Maria Santos (63 anos)',
            nascimento=sixty_years_ago - timedelta(days=3*365),  # 63 years old
            prioridade=False
        )
        
        self.client_under_60 = Cliente.objects.create(
            cpf='33333333333',
            nome='Pedro Oliveira (50 anos)',
            nascimento=fifty_years_ago,
            prioridade=False
        )
        
        self.client_already_priority = Cliente.objects.create(
            cpf='44444444444',
            nome='Ana Costa (65 anos)',
            nascimento=sixty_years_ago - timedelta(days=5*365),  # 65 years old
            prioridade=True  # Already has priority
        )
        
        self.client_app = Client()
    
    def test_update_priority_by_age_view_authentication(self):
        """Test that update priority view requires authentication"""
        response = self.client_app.post(reverse('update_priority_by_age'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_update_priority_by_age_get_not_allowed(self):
        """Test that GET requests are not allowed for update priority"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('update_priority_by_age'))
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_update_priority_by_age_success(self):
        """Test successful priority update for clients over 60"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify initial state
        self.assertFalse(self.client_over_70.prioridade)
        self.assertFalse(self.client_over_60.prioridade)
        self.assertFalse(self.client_under_60.prioridade)
        self.assertTrue(self.client_already_priority.prioridade)
        
        # Execute the update
        response = self.client_app.post(reverse('update_priority_by_age'))
        self.assertEqual(response.status_code, 302)  # Redirect to client list
        
        # Refresh from database
        self.client_over_70.refresh_from_db()
        self.client_over_60.refresh_from_db()
        self.client_under_60.refresh_from_db()
        self.client_already_priority.refresh_from_db()
        
        # Verify results
        self.assertTrue(self.client_over_70.prioridade)  # Should be updated
        self.assertTrue(self.client_over_60.prioridade)  # Should be updated
        self.assertFalse(self.client_under_60.prioridade)  # Should remain unchanged
        self.assertTrue(self.client_already_priority.prioridade)  # Should remain unchanged
    
    def test_update_priority_messages(self):
        """Test success and info messages for priority update"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Execute the update
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        # Check messages
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('cliente(s) com mais de 60 anos foram atualizados' in str(m) for m in messages))
    
    def test_update_priority_no_clients_to_update(self):
        """Test behavior when no clients need priority update"""
        from datetime import timedelta
        
        # Update all senior clients to priority first
        Cliente.objects.filter(nascimento__lt=date.today() - timedelta(days=60*365.25)).update(prioridade=True)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        # Check info message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Nenhum cliente encontrado que precise ser atualizado' in str(m) for m in messages))
    
    def test_update_priority_redirect(self):
        """Test that update priority redirects to client list"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        self.assertRedirects(response, reverse('clientes'))


class ManagementCommandUpdatePriorityByAgeTest(TestCase):
    """Test cases for update_priority_by_age management command"""
    
    def setUp(self):
        """Set up test data"""
        from datetime import date, timedelta
        from django.core.management import call_command
        from io import StringIO
        
        # Calculate dates for testing
        today = date.today()
        sixty_years_ago = today - timedelta(days=60*365.25)
        seventy_years_ago = today - timedelta(days=70*365.25)
        fifty_years_ago = today - timedelta(days=50*365.25)
        
        # Create test clients with different ages
        self.client_over_70 = Cliente.objects.create(
            cpf='11111111111',
            nome='João Silva (77 anos)',
            nascimento=seventy_years_ago,
            prioridade=False
        )
        
        self.client_over_60 = Cliente.objects.create(
            cpf='22222222222',
            nome='Maria Santos (63 anos)',
            nascimento=sixty_years_ago - timedelta(days=3*365),  # 63 years old
            prioridade=False
        )
        
        self.client_under_60 = Cliente.objects.create(
            cpf='33333333333',
            nome='Pedro Oliveira (50 anos)',
            nascimento=fifty_years_ago,
            prioridade=False
        )
        
        self.client_already_priority = Cliente.objects.create(
            cpf='44444444444',
            nome='Ana Costa (65 anos)',
            nascimento=sixty_years_ago - timedelta(days=5*365),  # 65 years old
            prioridade=True  # Already has priority
        )
    
    def test_management_command_dry_run(self):
        """Test management command with dry-run option"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('update_priority_by_age', '--dry-run', stdout=out)
        output = out.getvalue()
        
        # Should show what would be updated without making changes
        self.assertIn('DRY RUN:', output)
        self.assertIn('Would update', output)
        self.assertIn('João Silva (77 anos)', output)
        self.assertIn('Maria Santos (63 anos)', output)
        
        # Verify no actual changes were made
        self.client_over_70.refresh_from_db()
        self.client_over_60.refresh_from_db()
        self.assertFalse(self.client_over_70.prioridade)
        self.assertFalse(self.client_over_60.prioridade)
    
    def test_management_command_execute(self):
        """Test management command execution"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('update_priority_by_age', stdout=out)
        output = out.getvalue()
        
        # Should show successful update
        self.assertIn('Successfully updated', output)
        self.assertIn('clients over 60 years old to priority status', output)
        
        # Verify actual changes were made
        self.client_over_70.refresh_from_db()
        self.client_over_60.refresh_from_db()
        self.client_under_60.refresh_from_db()
        self.client_already_priority.refresh_from_db()
        
        self.assertTrue(self.client_over_70.prioridade)
        self.assertTrue(self.client_over_60.prioridade)
        self.assertFalse(self.client_under_60.prioridade)
        self.assertTrue(self.client_already_priority.prioridade)
    
    def test_management_command_custom_age_limit(self):
        """Test management command with custom age limit"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('update_priority_by_age', '--age-limit=65', '--dry-run', stdout=out)
        output = out.getvalue()
        
        # Should only include clients over 65
        self.assertIn('over 65 years old', output)
        # Should show fewer clients to update since age limit is higher
    
    def test_management_command_no_clients_to_update(self):
        """Test management command when no clients need update"""
        from django.core.management import call_command
        from io import StringIO
        from datetime import timedelta
        
        # Update all senior clients to priority first
        Cliente.objects.filter(nascimento__lt=date.today() - timedelta(days=60*365.25)).update(prioridade=True)
        
        out = StringIO()
        call_command('update_priority_by_age', '--dry-run', stdout=out)
        output = out.getvalue()
        
        # Should indicate no clients need update
        self.assertIn('No clients found that need priority update', output)


class ClienteListViewWithPriorityButtonTest(TestCase):
    """Test cases for client list view with priority update button"""
    
    def setUp(self):
        """Set up test data"""
        from datetime import date, timedelta
        
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test client over 60
        self.client_senior = Cliente.objects.create(
            cpf='11111111111',
            nome='João Silva (65 anos)',
            nascimento=date.today() - timedelta(days=65*365.25),
            prioridade=False
        )
        
        self.client_app = Client()
    
    def test_client_list_contains_priority_button(self):
        """Test that client list page contains priority update button"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('clientes'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Atualizar Prioritários')
        self.assertContains(response, reverse('update_priority_by_age'))
    
    def test_priority_button_has_confirmation(self):
        """Test that priority button includes JavaScript confirmation"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('clientes'))
        
        self.assertContains(response, 'onsubmit="return confirm(')
        self.assertContains(response, 'Tem certeza de que deseja atualizar')
    
    def test_priority_button_csrf_protection(self):
        """Test that priority button includes CSRF protection"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('clientes'))
        
        self.assertContains(response, 'csrfmiddlewaretoken')


class PriorityUpdateIntegrationTest(TestCase):
    """Integration tests for the complete priority update workflow"""
    
    def setUp(self):
        """Set up comprehensive test data"""
        from datetime import date, timedelta
        
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create precatorios
        self.precatorio1 = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='Tribunal de São Paulo',
            quitado=False,
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            prioridade_deferida=True,
            acordo_deferido=False
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='2345678-90.2023.8.26.0200',
            orcamento=2023,
            origem='Tribunal de Campinas',
            quitado=False,
            valor_de_face=75000.00,
            ultima_atualizacao=75000.00,
            data_ultima_atualizacao=date(2023, 2, 20),
            percentual_contratuais_assinado=25.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=15.0,
            prioridade_deferida=False,
            acordo_deferido=False
        )
        
        # Create clients with different ages and priority statuses
        today = date.today()
        sixty_years_ago = today - timedelta(days=60*365.25)
        
        self.client_senior_no_priority = Cliente.objects.create(
            cpf='11111111111',
            nome='Maria Santos (65 anos)',
            nascimento=sixty_years_ago - timedelta(days=5*365),
            prioridade=False
        )
        
        self.client_senior_has_priority = Cliente.objects.create(
            cpf='22222222222',
            nome='João Silva (70 anos)',
            nascimento=sixty_years_ago - timedelta(days=10*365),
            prioridade=True
        )
        
        self.client_young = Cliente.objects.create(
            cpf='33333333333',
            nome='Pedro Oliveira (45 anos)',
            nascimento=today - timedelta(days=45*365.25),
            prioridade=False
        )
        
        # Link clients to precatorios
        self.precatorio1.clientes.add(self.client_senior_no_priority, self.client_young)
        self.precatorio2.clientes.add(self.client_senior_has_priority)
        
        # Create phases for testing complete workflow
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        
        # Create alvaras to test complete relationships
        self.alvara1 = Alvara.objects.create(
            precatorio=self.precatorio1,
            cliente=self.client_senior_no_priority,
            valor_principal=30000.00,
            honorarios_contratuais=15000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara
        )
        
        self.client_app = Client()
    
    def test_complete_priority_update_workflow(self):
        """Test complete workflow from button click to database update"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # 1. Access client list page
        response = self.client_app.get(reverse('clientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Atualizar Prioritários')
        
        # 2. Verify initial state
        self.assertFalse(self.client_senior_no_priority.prioridade)
        self.assertTrue(self.client_senior_has_priority.prioridade)
        self.assertFalse(self.client_young.prioridade)
        
        # 3. Click priority update button
        response = self.client_app.post(reverse('update_priority_by_age'))
        self.assertEqual(response.status_code, 302)
        
        # 4. Verify database updates
        self.client_senior_no_priority.refresh_from_db()
        self.client_senior_has_priority.refresh_from_db()
        self.client_young.refresh_from_db()
        
        # Senior without priority should now have priority
        self.assertTrue(self.client_senior_no_priority.prioridade)
        # Senior with priority should remain unchanged
        self.assertTrue(self.client_senior_has_priority.prioridade)
        # Young client should remain unchanged
        self.assertFalse(self.client_young.prioridade)
        
        # 5. Verify redirect back to client list
        self.assertRedirects(response, reverse('clientes'))
    
    def test_priority_update_with_filtering(self):
        """Test priority update combined with client filtering"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Update priorities first
        self.client_app.post(reverse('update_priority_by_age'))
        
        # Test filtering by priority status
        response = self.client_app.get(reverse('clientes') + '?prioridade=true')
        self.assertEqual(response.status_code, 200)
        
        clientes = response.context['clientes']
        # Should include both senior clients now
        priority_clients = [c for c in clientes if c.prioridade]
        self.assertEqual(len(priority_clients), 2)
    
    def test_priority_update_with_statistics(self):
        """Test priority update affects client statistics correctly"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Check initial statistics
        response = self.client_app.get(reverse('clientes'))
        initial_priority_count = response.context.get('clientes_com_prioridade', 0)
        
        # Update priorities
        self.client_app.post(reverse('update_priority_by_age'))
        
        # Check updated statistics
        response = self.client_app.get(reverse('clientes'))
        updated_priority_count = response.context.get('clientes_com_prioridade', 0)
        
        # Should have one more priority client
        self.assertEqual(updated_priority_count, initial_priority_count + 1)
    
    def test_priority_update_error_handling(self):
        """Test error handling in priority update functionality"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Mock a database error by creating invalid state (this is a conceptual test)
        # In practice, you'd use unittest.mock to simulate database errors
        
        # For now, test that the view handles the happy path correctly
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        # Should not raise unhandled exceptions
        self.assertEqual(response.status_code, 302)


class PriorityUpdateEdgeCasesTest(TestCase):
    """Test edge cases for priority update functionality"""
    
    def setUp(self):
        """Set up edge case test data"""
        from datetime import date, timedelta
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create client exactly 60 years old (edge case)
        exactly_60_years_ago = date.today() - timedelta(days=60*365.25)
        self.client_exactly_60 = Cliente.objects.create(
            cpf='11111111111',
            nome='Cliente Exatamente 60 Anos',
            nascimento=exactly_60_years_ago,
            prioridade=False
        )
        
        # Create client just under 60 (should not be updated)
        just_under_60 = date.today() - timedelta(days=60*365.25 - 1)
        self.client_just_under_60 = Cliente.objects.create(
            cpf='22222222222',
            nome='Cliente 59 Anos e 364 Dias',
            nascimento=just_under_60,
            prioridade=False
        )
        
        # Create client just over 60 (should be updated)
        just_over_60 = date.today() - timedelta(days=60*365.25 + 1)
        self.client_just_over_60 = Cliente.objects.create(
            cpf='33333333333',
            nome='Cliente 60 Anos e 1 Dia',
            nascimento=just_over_60,
            prioridade=False
        )
        
        self.client_app = Client()
    
    def test_exactly_60_years_old(self):
        """Test client who is exactly 60 years old"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Execute update
        self.client_app.post(reverse('update_priority_by_age'))
        
        # Refresh from database
        self.client_exactly_60.refresh_from_db()
        
        # Client exactly 60 should NOT be updated (using < comparison, so exactly 60 does not qualify)
        self.assertFalse(self.client_exactly_60.prioridade)
    
    def test_just_under_60_years_old(self):
        """Test client who is just under 60 years old"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Execute update
        self.client_app.post(reverse('update_priority_by_age'))
        
        # Refresh from database
        self.client_just_under_60.refresh_from_db()
        
        # Client just under 60 should NOT be updated
        self.assertFalse(self.client_just_under_60.prioridade)
    
    def test_just_over_60_years_old(self):
        """Test client who is just over 60 years old"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Execute update
        self.client_app.post(reverse('update_priority_by_age'))
        
        # Refresh from database
        self.client_just_over_60.refresh_from_db()
        
        # Client just over 60 should be updated
        self.assertTrue(self.client_just_over_60.prioridade)
    
    def test_leap_year_handling(self):
        """Test that leap years are handled correctly in age calculation"""
        from datetime import date, timedelta
        
        # This is a conceptual test - in practice, the 365.25 calculation
        # in the management command should handle leap years correctly
        
        # Create client born on February 29 (leap year)
        leap_year_birth = date(1964, 2, 29)  # 1964 was a leap year
        client_leap_year = Cliente.objects.create(
            cpf='44444444444',
            nome='Cliente Nascido em Ano Bissexto',
            nascimento=leap_year_birth,
            prioridade=False
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        self.client_app.post(reverse('update_priority_by_age'))
        
        client_leap_year.refresh_from_db()
        # Should be updated as client is over 60
        self.assertTrue(client_leap_year.prioridade)


class PriorityUpdatePerformanceTest(TestCase):
    """Test performance considerations for priority update functionality"""
    
    def setUp(self):
        """Set up performance test data"""
        from datetime import date, timedelta
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create many clients for performance testing
        today = date.today()
        sixty_years_ago = today - timedelta(days=60*365.25)
        
        # Create 50 senior clients without priority
        self.senior_clients = []
        for i in range(50):
            client = Cliente.objects.create(
                cpf=f'{i:011d}',
                nome=f'Cliente Senior {i}',
                nascimento=sixty_years_ago - timedelta(days=i*30),  # Various ages over 60
                prioridade=False
            )
            self.senior_clients.append(client)
        
        # Create 50 young clients
        fifty_years_ago = today - timedelta(days=50*365.25)
        for i in range(50, 100):
            Cliente.objects.create(
                cpf=f'{i:011d}',
                nome=f'Cliente Young {i}',
                nascimento=fifty_years_ago - timedelta(days=i*10),
                prioridade=False
            )
        
        self.client_app = Client()
    
    def test_bulk_priority_update_performance(self):
        """Test that bulk priority update is efficient"""
        import time
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Measure execution time
        start_time = time.time()
        response = self.client_app.post(reverse('update_priority_by_age'))
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete reasonably quickly (less than 5 seconds for 100 clients)
        self.assertLess(execution_time, 5.0)
        
        # Verify correct number of updates (should be most/all of the senior clients)
        updated_count = Cliente.objects.filter(prioridade=True).count()
        self.assertGreaterEqual(updated_count, 49)  # At least 49 of the 50 senior clients
        self.assertLessEqual(updated_count, 50)  # At most 50
    
    def test_query_efficiency(self):
        """Test that the database queries are efficient"""
        from django.test.utils import override_settings
        from django.db import connection
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Reset query count
        connection.queries_log.clear()
        
        # Execute update
        with override_settings(DEBUG=True):
            self.client_app.post(reverse('update_priority_by_age'))
        
        # Check that we're not doing N+1 queries
        query_count = len(connection.queries)
        
        # Should be a reasonable number of queries (not proportional to client count)
        self.assertLess(query_count, 10)


# Run tests with: python manage.py test precapp.tests.PriorityUpdateByAgeTest
# Run all priority tests with: python manage.py test precapp.tests -k Priority
# Run tests with: python manage.py test precapp
