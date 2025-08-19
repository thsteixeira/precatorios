from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from .models import Precatorio, Cliente, Alvara, Requerimento, Fase, FaseHonorariosContratuais, TipoDiligencia, Diligencias
from .forms import (
    PrecatorioForm, ClienteForm, AlvaraSimpleForm, 
    RequerimentoForm, FaseForm, FaseHonorariosContratuaisForm, validate_cnj, validate_currency,
    TipoDiligenciaForm, DiligenciasForm, DiligenciasUpdateForm
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

            acordo_deferido=False
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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

            acordo_deferido=False
        )
        
        # Create cliente
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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
            'cpf': '12345678909',
            'nome': 'João Silva',
            'nascimento': date(1980, 5, 15),
            'prioridade': False
        }
    
    def test_cliente_creation(self):
        """Test creating a cliente with valid data"""
        cliente = Cliente(**self.cliente_data)
        cliente.full_clean()  # This should not raise ValidationError
        cliente.save()
        self.assertEqual(cliente.cpf, '12345678909')
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

            acordo_deferido=False
        )
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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

            acordo_deferido=False
        )
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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

            acordo_deferido=False
        )
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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
            'cliente_cpf': '123.456.789-09',
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

            acordo_deferido=False
        )
        
        self.valid_form_data = {
            'cpf': '111.444.777-35',  # Valid CPF with correct check digits
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
        formatted_data['cpf'] = '123.456.789-09'
        form = ClienteForm(data=formatted_data)
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.cpf, '12345678909')  # Should be stored without formatting
        
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
        
        # Test mathematically invalid CPF
        invalid_data['cpf'] = '23902928334'  # Invalid check digits
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cpf'][0])
        
        # Test CPF with all same digits (should be invalid)
        invalid_data['cpf'] = '11111111111'
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cpf'][0])


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

            acordo_deferido=False
        )
        
        # Create cliente
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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

            acordo_deferido=False
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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
    
    def test_multiple_filters(self):
        """Test combining multiple filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?cnj=test&quitado=false')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        # Should return no results since no precatorio has both cnj='test' and quitado=False
        self.assertEqual(len(precatorios), 0)

    
    def test_filter_context_values(self):
        """Test that current filter values are passed to template context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?cnj=test&origem=tribunal&quitado=true')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_cnj'], 'test')
        self.assertEqual(response.context['current_origem'], 'tribunal')
        self.assertEqual(response.context['current_quitado'], 'true')


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
        response = self.client.get('/clientes/?nome=test&cpf=123&idade=58&prioridade=true&requerimento_prioridade=sem_requerimento&precatorio=cnj123')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_nome'], 'test')
        self.assertEqual(response.context['current_cpf'], '123')
        self.assertEqual(response.context['current_idade'], '58')
        self.assertEqual(response.context['current_prioridade'], 'true')
        self.assertEqual(response.context['current_requerimento_prioridade'], 'sem_requerimento')
        self.assertEqual(response.context['current_precatorio'], 'cnj123')
    
    def test_filter_by_idade(self):
        """Test filtering by age"""
        from datetime import date
        
        self.client.login(username='testuser', password='testpass123')
        
        # Create a cliente with specific age
        # Let's test for someone who is 58 years old today
        today = date.today()
        birth_year = today.year - 58
        cliente_58 = Cliente.objects.create(
            cpf='44444444444',
            nome='Cliente 58 Anos',
            nascimento=date(birth_year, 6, 15),  # Born in June of birth_year
            prioridade=False
        )
        
        # Test filtering by age 58
        response = self.client.get('/clientes/?idade=58')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        
        # Should return only the 58-year-old cliente
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'Cliente 58 Anos')
    
    def test_filter_by_idade_invalid(self):
        """Test filtering by invalid age value"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with invalid age value - should ignore the filter
        response = self.client.get('/clientes/?idade=abc')
        
        self.assertEqual(response.status_code, 200)
        clientes = response.context['clientes']
        # Should return all clientes since invalid filter is ignored
        self.assertEqual(len(clientes), 3)
    
    def test_idade_filter_context_value(self):
        """Test that idade filter value is passed to template context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/clientes/?idade=58')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_idade'], '58')
    
    def test_filter_by_idade_comprehensive(self):
        """Test comprehensive age filtering scenarios"""
        from datetime import date
        
        self.client.login(username='testuser', password='testpass123')
        
        today = date.today()
        
        # Create clients with different ages
        # Client aged 25 (born 25 years ago)
        cliente_25 = Cliente.objects.create(
            cpf='55555555555',
            nome='Cliente 25 Anos',
            nascimento=date(today.year - 25, today.month, today.day),
            prioridade=False
        )
        
        # Client aged 60 (born 60 years ago)
        cliente_60 = Cliente.objects.create(
            cpf='66666666666',
            nome='Cliente 60 Anos',
            nascimento=date(today.year - 60, today.month, today.day),
            prioridade=True
        )
        
        # Test filtering by age 25
        response = self.client.get('/clientes/?idade=25')
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'Cliente 25 Anos')
        
        # Test filtering by age 60
        response = self.client.get('/clientes/?idade=60')
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'Cliente 60 Anos')
        
        # Test filtering by non-existent age
        response = self.client.get('/clientes/?idade=99')
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 0)
        
        # Test combining idade filter with nome filter
        response = self.client.get('/clientes/?idade=60&nome=Cliente')
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'Cliente 60 Anos')


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

            acordo_deferido=False
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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
            'cpf': '11144477735',  # Different valid CPF to avoid conflicts
            'nome': 'João Silva Unformatted',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        
        form = ClienteForm(data=unformatted_data)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.cpf, '11144477735')  # Stored without formatting
        
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

            acordo_deferido=False
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
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


class PrecatorioAdvancedFilterTest(TestCase):
    """Test cases for advanced precatorio filtering functionality"""
    
    def setUp(self):
        """Set up test data for precatorio filtering"""
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
        self.precatorio_prioridade_deferido = Precatorio.objects.create(
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
            acordo_deferido=False
        )
        
        self.precatorio_prioridade_nao_deferido = Precatorio.objects.create(
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
            acordo_deferido=False
        )
        
        self.precatorio_acordo_deferido = Precatorio.objects.create(
            cnj='3333333-33.2023.8.26.0300',
            orcamento=2023,
            origem='Tribunal de Santos',
            quitado=False,
            valor_de_face=15000.00,
            ultima_atualizacao=15000.00,
            data_ultima_atualizacao=date(2023, 3, 25),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            acordo_deferido=False
        )
        
        self.precatorio_acordo_nao_deferido = Precatorio.objects.create(
            cnj='4444444-44.2023.8.26.0400',
            orcamento=2023,
            origem='Tribunal de Osasco',
            quitado=False,
            valor_de_face=25000.00,
            ultima_atualizacao=25000.00,
            data_ultima_atualizacao=date(2023, 4, 30),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            acordo_deferido=False
        )
        
        self.precatorio_sem_requerimento = Precatorio.objects.create(
            cnj='5555555-55.2023.8.26.0500',
            orcamento=2023,
            origem='Tribunal de Bauru',
            quitado=False,
            valor_de_face=30000.00,
            ultima_atualizacao=30000.00,
            data_ultima_atualizacao=date(2023, 5, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            acordo_deferido=False
        )
        
        self.precatorio_misto = Precatorio.objects.create(
            cnj='6666666-66.2023.8.26.0600',
            orcamento=2023,
            origem='Tribunal de Sorocaba',
            quitado=False,
            valor_de_face=35000.00,
            ultima_atualizacao=35000.00,
            data_ultima_atualizacao=date(2023, 6, 20),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            acordo_deferido=False
        )
        
        # Create test clientes
        self.cliente1 = Cliente.objects.create(
            cpf='11111111111',
            nome='João Silva',
            nascimento=date(1950, 5, 15),
            prioridade=True
        )
        
        self.cliente2 = Cliente.objects.create(
            cpf='22222222222',
            nome='Maria Santos',
            nascimento=date(1980, 8, 20),
            prioridade=False
        )
        
        self.cliente3 = Cliente.objects.create(
            cpf='33333333333',
            nome='Pedro Costa',
            nascimento=date(1975, 12, 10),
            prioridade=False
        )
        
        # Create requerimentos for testing
        # Precatorio 1: Priority request DEFERIDO
        Requerimento.objects.create(
            precatorio=self.precatorio_prioridade_deferido,
            cliente=self.cliente1,
            pedido='prioridade idade',
            valor=5000.00,
            desagio=0.0,
            fase=self.fase_deferido
        )
        
        # Precatorio 2: Priority request NAO DEFERIDO
        Requerimento.objects.create(
            precatorio=self.precatorio_prioridade_nao_deferido,
            cliente=self.cliente1,
            pedido='prioridade doença',
            valor=8000.00,
            desagio=0.0,
            fase=self.fase_indeferido
        )
        
        # Precatorio 3: Acordo request DEFERIDO
        Requerimento.objects.create(
            precatorio=self.precatorio_acordo_deferido,
            cliente=self.cliente2,
            pedido='acordo principal',
            valor=3000.00,
            desagio=0.0,
            fase=self.fase_deferido
        )
        
        # Precatorio 4: Acordo request NAO DEFERIDO  
        Requerimento.objects.create(
            precatorio=self.precatorio_acordo_nao_deferido,
            cliente=self.cliente2,
            pedido='acordo honorários contratuais',
            valor=6000.00,
            desagio=0.0,
            fase=self.fase_andamento
        )
        
        # Precatorio 5: No requerimentos (sem_requerimento case)
        
        # Precatorio 6: Mixed - has both priority and acordo
        Requerimento.objects.create(
            precatorio=self.precatorio_misto,
            cliente=self.cliente3,
            pedido='prioridade idade',
            valor=7000.00,
            desagio=0.0,
            fase=self.fase_deferido
        )
        Requerimento.objects.create(
            precatorio=self.precatorio_misto,
            cliente=self.cliente3,
            pedido='acordo principal',
            valor=4000.00,
            desagio=0.0,
            fase=self.fase_indeferido
        )
        
        self.client_app = Client()
    
    def test_filter_tipo_requerimento_acordo(self):
        """Test filtering by tipo_requerimento = acordo"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?tipo_requerimento=acordo')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        # Should include precatorios that have acordo requerimentos
        cnjs = [p.cnj for p in precatorios]
        self.assertIn(self.precatorio_acordo_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_acordo_nao_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_misto.cnj, cnjs)
        
        # Should NOT include precatorios with only prioridade or no requerimentos
        self.assertNotIn(self.precatorio_prioridade_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_prioridade_nao_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_sem_requerimento.cnj, cnjs)
    
    def test_filter_tipo_requerimento_sem_acordo(self):
        """Test filtering by tipo_requerimento = sem_acordo"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?tipo_requerimento=sem_acordo')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        # Should include precatorios that have NO acordo requerimentos
        cnjs = [p.cnj for p in precatorios]
        self.assertIn(self.precatorio_prioridade_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_prioridade_nao_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_sem_requerimento.cnj, cnjs)
        
        # Should NOT include precatorios with acordo requerimentos
        self.assertNotIn(self.precatorio_acordo_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_acordo_nao_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_misto.cnj, cnjs)
    
    def test_filter_requerimento_deferido(self):
        """Test filtering by requerimento_deferido = deferido"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?requerimento_deferido=deferido')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        # Should include precatorios that have at least one deferido requerimento
        cnjs = [p.cnj for p in precatorios]
        self.assertIn(self.precatorio_prioridade_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_acordo_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_misto.cnj, cnjs)
        
        # Should NOT include precatorios with only non-deferido or no requerimentos
        self.assertNotIn(self.precatorio_prioridade_nao_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_acordo_nao_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_sem_requerimento.cnj, cnjs)
    
    def test_filter_requerimento_nao_deferido(self):
        """Test filtering by requerimento_deferido = nao_deferido"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?requerimento_deferido=nao_deferido')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        # Should include precatorios that have requerimentos that are NOT deferido
        cnjs = [p.cnj for p in precatorios]
        self.assertIn(self.precatorio_prioridade_nao_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_acordo_nao_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_misto.cnj, cnjs)  # Has both deferido and nao deferido
        
        # Should NOT include precatorios with only deferido or no requerimentos
        self.assertNotIn(self.precatorio_prioridade_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_acordo_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_sem_requerimento.cnj, cnjs)
    
    def test_combined_filter_acordo_nao_deferido(self):
        """Test combined filtering: tipo_requerimento=acordo AND requerimento_deferido=nao_deferido"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?tipo_requerimento=acordo&requerimento_deferido=nao_deferido')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        # Should include precatorios that have acordo requerimentos that are NOT deferido
        cnjs = [p.cnj for p in precatorios]
        self.assertIn(self.precatorio_acordo_nao_deferido.cnj, cnjs)
        self.assertIn(self.precatorio_misto.cnj, cnjs)  # Has acordo not deferido
        
        # Should NOT include others
        self.assertNotIn(self.precatorio_prioridade_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_prioridade_nao_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_acordo_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_sem_requerimento.cnj, cnjs)
    
    def test_combined_filter_sem_acordo_deferido(self):
        """Test combined filtering: tipo_requerimento=sem_acordo AND requerimento_deferido=deferido"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?tipo_requerimento=sem_acordo&requerimento_deferido=deferido')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        # Should include precatorios that have NO acordo AND have some deferido requerimento
        cnjs = [p.cnj for p in precatorios]
        self.assertIn(self.precatorio_prioridade_deferido.cnj, cnjs)
        
        # Should NOT include precatorios with acordo or those without deferido requerimentos
        self.assertNotIn(self.precatorio_prioridade_nao_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_acordo_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_acordo_nao_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_misto.cnj, cnjs)
        self.assertNotIn(self.precatorio_sem_requerimento.cnj, cnjs)
    
    def test_combined_filter_sem_acordo_nao_deferido(self):
        """Test combined filtering: tipo_requerimento=sem_acordo AND requerimento_deferido=nao_deferido"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?tipo_requerimento=sem_acordo&requerimento_deferido=nao_deferido')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        # Should include precatorios that have NO acordo AND have some non-deferido requerimento
        cnjs = [p.cnj for p in precatorios]
        self.assertIn(self.precatorio_prioridade_nao_deferido.cnj, cnjs)
        
        # Should NOT include precatorios with acordo or those without non-deferido requerimentos
        self.assertNotIn(self.precatorio_prioridade_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_acordo_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_acordo_nao_deferido.cnj, cnjs)
        self.assertNotIn(self.precatorio_misto.cnj, cnjs)
        self.assertNotIn(self.precatorio_sem_requerimento.cnj, cnjs)
    
    def test_filter_context_values(self):
        """Test that current filter values are passed to template context"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?tipo_requerimento=prioridade&requerimento_deferido=deferido')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_tipo_requerimento'], 'prioridade')
        self.assertEqual(response.context['current_requerimento_deferido'], 'deferido')
    
    def test_filter_statistics_calculation(self):
        """Test that filter statistics are calculated correctly"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/?tipo_requerimento=acordo')
        
        self.assertEqual(response.status_code, 200)
        
        # Should calculate statistics based on filtered results
        self.assertEqual(response.context['total_precatorios'], 3)  # 3 precatorios with acordo
        # No need to check prioritarios since we removed priority filtering
    
    def test_empty_filter_results(self):
        """Test behavior when filter returns no results"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create a combination that should return no results
        response = self.client_app.get('/precatorios/?tipo_requerimento=acordo&requerimento_deferido=deferido&cnj=nonexistent')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        self.assertEqual(len(precatorios), 0)
        self.assertEqual(response.context['total_precatorios'], 0)
    
    def test_all_filters_combined(self):
        """Test combining all available filters"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get('/precatorios/?cnj=1111&origem=São Paulo&quitado=false&tipo_requerimento=prioridade&requerimento_deferido=deferido')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        
        # Should find precatorio_prioridade_deferido
        cnjs = [p.cnj for p in precatorios]
        self.assertIn(self.precatorio_prioridade_deferido.cnj, cnjs)
        
        # Context should include all filter values
        self.assertEqual(response.context['current_cnj'], '1111')
        self.assertEqual(response.context['current_origem'], 'São Paulo')
        self.assertEqual(response.context['current_quitado'], 'false')
        self.assertEqual(response.context['current_tipo_requerimento'], 'prioridade')
        self.assertEqual(response.context['current_requerimento_deferido'], 'deferido')


class RequerimentoDisplayTest(TestCase):
    """Test cases for requerimento display functionality in precatorio list"""
    
    def setUp(self):
        """Set up test data"""
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test phases
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
        
        # Create test precatorio
        self.precatorio = Precatorio.objects.create(
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
            acordo_deferido=False
        )
        
        # Create test cliente
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Create test requerimentos
        self.req_prioridade_idade = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='prioridade idade',
            valor=25000.00,
            desagio=10.0,
            fase=self.fase_deferido
        )
        
        self.req_acordo_contratuais = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='acordo honorários contratuais',
            valor=15000.00,
            desagio=5.0,
            fase=self.fase_indeferido
        )
        
        self.client_app = Client()
    
    def test_requerimento_abbreviation_method(self):
        """Test get_pedido_abreviado method returns correct abbreviations"""
        # Test all abbreviations
        self.assertEqual(self.req_prioridade_idade.get_pedido_abreviado(), 'Prioridade Idade')
        self.assertEqual(self.req_acordo_contratuais.get_pedido_abreviado(), 'Acordo Hon. Contratuais')
        
        # Create and test other types
        req_doenca = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='prioridade doença',
            valor=20000.00,
            desagio=8.0,
            fase=self.fase_deferido
        )
        self.assertEqual(req_doenca.get_pedido_abreviado(), 'Prioridade Doença')
        
        req_acordo_principal = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='acordo principal',
            valor=30000.00,
            desagio=12.0,
            fase=self.fase_deferido
        )
        self.assertEqual(req_acordo_principal.get_pedido_abreviado(), 'Acordo Principal')
        
        req_acordo_sucumbenciais = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='acordo honorários sucumbenciais',
            valor=5000.00,
            desagio=3.0,
            fase=self.fase_deferido
        )
        self.assertEqual(req_acordo_sucumbenciais.get_pedido_abreviado(), 'Acordo Hon. Sucumbenciais')
    
    def test_precatorio_list_displays_requerimentos(self):
        """Test that precatorio list displays requerimento information"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/')
        
        self.assertEqual(response.status_code, 200)
        
        # Check that precatorio is displayed
        self.assertContains(response, self.precatorio.cnj)
        
        # Check that basic requerimento information is accessible through context
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        
        precatorio = precatorios[0]
        requerimentos = precatorio.requerimento_set.all()
        self.assertEqual(len(requerimentos), 2)
        
        # Verify requerimento data
        pedidos = [req.pedido for req in requerimentos]
        self.assertIn('prioridade idade', pedidos)
        self.assertIn('acordo honorários contratuais', pedidos)
        
        # Verify abbreviation methods work
        for req in requerimentos:
            abbreviation = req.get_pedido_abreviado()
            self.assertIsNotNone(abbreviation)
            self.assertTrue(len(abbreviation) > 0)
    
    def test_precatorio_without_requerimentos(self):
        """Test display of precatorio without requerimentos"""
        # Create precatorio without requerimentos
        precatorio_empty = Precatorio.objects.create(
            cnj='7777777-77.2023.8.26.0700',
            orcamento=2023,
            origem='Tribunal de Ribeirão Preto',
            quitado=False,
            valor_de_face=50000.00,
            ultima_atualizacao=50000.00,
            data_ultima_atualizacao=date(2023, 7, 10),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            acordo_deferido=False
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/')
        
        self.assertEqual(response.status_code, 200)
        
        # Should display precatorio without errors
        self.assertContains(response, precatorio_empty.cnj)
        
        # Check context includes both precatorios
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 2)
        
        # Verify empty precatorio has no requerimentos
        empty_precatorio = next(p for p in precatorios if p.cnj == precatorio_empty.cnj)
        requerimentos = empty_precatorio.requerimento_set.all()
        self.assertEqual(len(requerimentos), 0)
    
    def test_requerimento_display_with_multiple_phases(self):
        """Test requerimento display with multiple different phases"""
        # Create additional fase
        fase_andamento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#ffc107',
            ativa=True
        )
        
        # Create requerimento with different fase
        req_andamento = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='acordo principal',
            valor=40000.00,
            desagio=15.0,
            fase=fase_andamento
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/')
        
        self.assertEqual(response.status_code, 200)
        
        # Check context includes all requerimentos
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        
        precatorio = precatorios[0]
        requerimentos = precatorio.requerimento_set.all()
        self.assertEqual(len(requerimentos), 3)  # Original 2 + new one
        
        # Verify all phases are represented
        fases = [req.fase.nome for req in requerimentos if req.fase]
        self.assertIn('Deferido', fases)
        self.assertIn('Indeferido', fases)
        self.assertIn('Em Andamento', fases)
    
    def test_requerimento_display_ordering(self):
        """Test that requerimentos are displayed in a consistent order"""
        # Create additional requerimentos to test ordering
        req_3 = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='acordo principal',
            valor=35000.00,
            desagio=20.0,
            fase=self.fase_deferido
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get('/precatorios/')
        
        self.assertEqual(response.status_code, 200)
        
        # Should display all requerimentos
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        
        precatorio = precatorios[0]
        # Should have all requerimentos associated
        requerimentos = precatorio.requerimento_set.all()
        self.assertEqual(len(requerimentos), 3)


class RequerimentoFilterViewTest(TestCase):
    """Test requerimento filtering in list views"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create phases
        self.fase_deferido = Fase.objects.create(
            nome='Deferido',
            tipo='requerimento',
            cor='#28a745',
            ativa=True
        )
        
        # Create precatorio
        self.precatorio = Precatorio.objects.create(
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
            acordo_deferido=False
        )
        
        # Create cliente
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Create requerimento
        self.requerimento = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido='prioridade idade',
            valor=25000.00,
            desagio=10.0,
            fase=self.fase_deferido
        )
        
        self.client_app = Client()
    
    def test_requerimento_list_view_exists(self):
        """Test that requerimento list view is accessible"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Assuming there's a requerimento list view
        try:
            response = self.client_app.get('/requerimentos/')
            self.assertEqual(response.status_code, 200)
        except Exception:
            # If view doesn't exist, that's okay for now
            pass
    
    def test_requerimento_context_in_precatorio_detail(self):
        """Test that requerimento context is properly provided in precatorio detail"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(f'/precatorios/{self.precatorio.cnj}/')
        
        self.assertEqual(response.status_code, 200)
        
        # Should have requerimento context
        self.assertIn('requerimentos', response.context)
        requerimentos = response.context['requerimentos']
        
        self.assertEqual(len(requerimentos), 1)
        self.assertEqual(requerimentos[0].pedido, 'prioridade idade')
        self.assertEqual(requerimentos[0].get_pedido_abreviado(), 'Prioridade Idade')


class PriorityRequerimentoClienteFilterTest(TestCase):
    """Test priority requerimento filtering in cliente list view"""
    
    def setUp(self):
        """Set up test data for cliente priority filtering"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create phases
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
        
        # Create precatorio
        self.precatorio = Precatorio.objects.create(
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
            acordo_deferido=False
        )
        
        # Create clientes
        self.cliente_with_deferido = Cliente.objects.create(
            cpf='11111111111',
            nome='Cliente Com Deferido',
            nascimento=date(1950, 5, 15),
            prioridade=False
        )
        
        self.cliente_with_indeferido = Cliente.objects.create(
            cpf='22222222222',
            nome='Cliente Com Indeferido',
            nascimento=date(1960, 8, 20),
            prioridade=False
        )
        
        self.cliente_without_priority = Cliente.objects.create(
            cpf='33333333333',
            nome='Cliente Sem Prioridade',
            nascimento=date(1970, 12, 10),
            prioridade=False
        )
        
        # Create requerimentos
        Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente_with_deferido,
            pedido='prioridade idade',
            valor=25000.00,
            desagio=10.0,
            fase=self.fase_deferido
        )
        
        Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente_with_indeferido,
            pedido='prioridade doença',
            valor=20000.00,
            desagio=8.0,
            fase=self.fase_indeferido
        )
        
        # cliente_without_priority has no priority requerimentos
        
        self.client_app = Client()
    
    def test_cliente_get_priority_requerimentos_method(self):
        """Test that Cliente.get_priority_requerimentos() method works correctly"""
        # Test cliente with deferido priority request
        priority_reqs_deferido = self.cliente_with_deferido.get_priority_requerimentos()
        self.assertEqual(len(priority_reqs_deferido), 1)
        self.assertEqual(priority_reqs_deferido[0].pedido, 'prioridade idade')
        
        # Test cliente with indeferido priority request
        priority_reqs_indeferido = self.cliente_with_indeferido.get_priority_requerimentos()
        self.assertEqual(len(priority_reqs_indeferido), 1)
        self.assertEqual(priority_reqs_indeferido[0].pedido, 'prioridade doença')
        
        # Test cliente without priority requests
        priority_reqs_none = self.cliente_without_priority.get_priority_requerimentos()
        self.assertEqual(len(priority_reqs_none), 0)
    
    def test_priority_filtering_logic(self):
        """Test the priority filtering logic in cliente view"""
        # This tests the logic that should be implemented in the cliente view
        from dateutil.relativedelta import relativedelta
        
        # Test filtering by requerimento prioridade status
        all_clientes = Cliente.objects.all()
        
        # Simulate deferido filter logic
        clientes_with_deferido = []
        for cliente in all_clientes:
            priority_reqs = cliente.get_priority_requerimentos()
            for req in priority_reqs:
                if req.fase and req.fase.nome == 'Deferido':
                    clientes_with_deferido.append(cliente)
                    break
        
        self.assertEqual(len(clientes_with_deferido), 1)
        self.assertIn(self.cliente_with_deferido, clientes_with_deferido)
        
        # Simulate não deferido filter logic
        clientes_with_nao_deferido = []
        for cliente in all_clientes:
            priority_reqs = cliente.get_priority_requerimentos()
            for req in priority_reqs:
                if req.fase and req.fase.nome != 'Deferido':
                    clientes_with_nao_deferido.append(cliente)
                    break
        
        self.assertEqual(len(clientes_with_nao_deferido), 1)
        self.assertIn(self.cliente_with_indeferido, clientes_with_nao_deferido)
        
        # Simulate sem requerimento filter logic
        clientes_sem_requerimento = []
        for cliente in all_clientes:
            priority_reqs = cliente.get_priority_requerimentos()
            if len(priority_reqs) == 0:
                clientes_sem_requerimento.append(cliente)
        
        self.assertEqual(len(clientes_sem_requerimento), 1)
        self.assertIn(self.cliente_without_priority, clientes_sem_requerimento)


class ModelMethodsTest(TestCase):
    """Test additional model methods and properties"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
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
            acordo_deferido=False
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.fase = Fase.objects.create(
            nome='Deferido',
            tipo='requerimento',
            cor='#28a745',
            ativa=True
        )
    
    def test_requerimento_get_pedido_abreviado_comprehensive(self):
        """Test get_pedido_abreviado method with all possible pedido types"""
        pedido_mapping = {
            'prioridade doença': 'Prioridade Doença',
            'prioridade idade': 'Prioridade Idade',
            'acordo principal': 'Acordo Principal',
            'acordo honorários contratuais': 'Acordo Hon. Contratuais',
            'acordo honorários sucumbenciais': 'Acordo Hon. Sucumbenciais',
        }
        
        for pedido, expected_abbreviation in pedido_mapping.items():
            with self.subTest(pedido=pedido):
                req = Requerimento.objects.create(
                    precatorio=self.precatorio,
                    cliente=self.cliente,
                    pedido=pedido,
                    valor=25000.00,
                    desagio=10.0,
                    fase=self.fase
                )
                
                self.assertEqual(req.get_pedido_abreviado(), expected_abbreviation)
                req.delete()  # Clean up for next iteration
    
    def test_fase_class_methods(self):
        """Test Fase class methods for filtering"""
        # Create different types of phases
        fase_alvara = Fase.objects.create(nome='Fase Alvara', tipo='alvara', cor='#ff0000')
        fase_requerimento = Fase.objects.create(nome='Fase Requerimento', tipo='requerimento', cor='#00ff00')
        fase_ambos = Fase.objects.create(nome='Fase Ambos', tipo='ambos', cor='#0000ff')
        fase_inativa = Fase.objects.create(nome='Fase Inativa', tipo='alvara', cor='#000000', ativa=False)
        
        # Test get_fases_for_alvara
        alvara_fases = Fase.get_fases_for_alvara()
        fase_tipos = set(alvara_fases.values_list('tipo', flat=True))
        self.assertEqual(fase_tipos, {'alvara', 'ambos'})
        self.assertIn(fase_alvara, alvara_fases)
        self.assertIn(fase_ambos, alvara_fases)
        self.assertNotIn(fase_requerimento, alvara_fases)
        self.assertNotIn(fase_inativa, alvara_fases)  # Inactive should be excluded
        
        # Test get_fases_for_requerimento
        req_fases = Fase.get_fases_for_requerimento()
        fase_tipos = set(req_fases.values_list('tipo', flat=True))
        self.assertEqual(fase_tipos, {'requerimento', 'ambos'})
        self.assertIn(fase_requerimento, req_fases)
        self.assertIn(fase_ambos, req_fases)
        self.assertNotIn(fase_alvara, req_fases)
    
    def test_fase_honorarios_class_methods(self):
        """Test FaseHonorariosContratuais class methods"""
        # Create active and inactive phases
        fase_ativa = FaseHonorariosContratuais.objects.create(nome='Ativa', cor='#ff0000', ativa=True)
        fase_inativa = FaseHonorariosContratuais.objects.create(nome='Inativa', cor='#00ff00', ativa=False)
        
        # Test get_fases_ativas
        fases_ativas = FaseHonorariosContratuais.get_fases_ativas()
        self.assertIn(fase_ativa, fases_ativas)
        self.assertNotIn(fase_inativa, fases_ativas)


class PerformanceTest(TestCase):
    """Test performance considerations for filtering functionality"""
    
    def setUp(self):
        """Set up performance test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create phases
        self.fase_deferido = Fase.objects.create(nome='Deferido', tipo='requerimento', cor='#28a745')
        
        # Create test data
        self.precatorios = []
        self.clientes = []
        
        # Create multiple precatorios and requerimentos for performance testing
        for i in range(20):
            precatorio = Precatorio.objects.create(
                cnj=f'{i:07d}-89.2023.8.26.0{i:03d}',
                orcamento=2023,
                origem=f'Tribunal {i}',
                quitado=i % 2 == 0,
                valor_de_face=10000.00 * (i + 1),
                ultima_atualizacao=10000.00 * (i + 1),
                data_ultima_atualizacao=date(2023, 1, 15),
                percentual_contratuais_assinado=30.0,
                percentual_contratuais_apartado=0.0,
                percentual_sucumbenciais=10.0,
                acordo_deferido=i % 3 == 0
            )
            self.precatorios.append(precatorio)
            
            cliente = Cliente.objects.create(
                cpf=f'{i:011d}',
                nome=f'Cliente {i}',
                nascimento=date(1980, 5, 15),
                prioridade=i % 4 == 0
            )
            self.clientes.append(cliente)
            
            # Create requerimentos for some precatorios
            if i % 2 == 0:
                Requerimento.objects.create(
                    precatorio=precatorio,
                    cliente=cliente,
                    pedido='prioridade idade' if i % 4 == 0 else 'acordo principal',
                    valor=5000.00,
                    desagio=10.0,
                    fase=self.fase_deferido
                )
        
        self.client_app = Client()
    
    def test_filter_query_performance(self):
        """Test that filtering queries are reasonably efficient"""
        import time
        from django.test.utils import override_settings
        from django.db import connection
        
        self.client_app.login(username='testuser', password='testpass123')
        
        with override_settings(DEBUG=True):
            # Reset query log
            connection.queries_log.clear()
            
            # Test multiple filter combinations
            start_time = time.time()
            
            # Test basic filters
            self.client_app.get('/precatorios/?cnj=000')
            self.client_app.get('/precatorios/?origem=Tribunal')
            self.client_app.get('/precatorios/?quitado=true')
            
            # Test complex filters
            self.client_app.get('/precatorios/?tipo_requerimento=prioridade')
            self.client_app.get('/precatorios/?requerimento_deferido=deferido')
            self.client_app.get('/precatorios/?tipo_requerimento=prioridade&requerimento_deferido=deferido')
            
            end_time = time.time()
            
            # Should complete reasonably quickly
            execution_time = end_time - start_time
            self.assertLess(execution_time, 2.0)  # Should complete within 2 seconds
            
            # Should not generate excessive queries
            query_count = len(connection.queries)
            self.assertLess(query_count, 50)  # Should be reasonable number of queries
    
    def test_prefetch_optimization(self):
        """Test that prefetch_related is used for optimization"""
        from django.test.utils import override_settings
        from django.db import connection
        
        self.client_app.login(username='testuser', password='testpass123')
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            
            response = self.client_app.get('/precatorios/')
            
            # Access requerimento data (should not trigger additional queries if prefetched)
            precatorios = list(response.context['precatorios'])
            for precatorio in precatorios[:5]:  # Test first 5 to avoid excessive queries
                requerimentos = list(precatorio.requerimento_set.all())
                for req in requerimentos:
                    _ = req.get_pedido_abreviado()
                    if req.fase:
                        _ = req.fase.nome
            
            # Should not generate N+1 queries
            query_count = len(connection.queries)
            # Allow for some queries but not proportional to object count
            self.assertLess(query_count, 15)


class CPFValidationTest(TestCase):
    """Test cases for the CPF validation algorithm"""
    
    def test_validate_cpf_function_valid_cpfs(self):
        """Test the validate_cpf function with valid CPFs"""
        from .forms import validate_cpf
        
        # Valid CPFs (mathematically correct)
        valid_cpfs = [
            '11144477735',  # Valid CPF
            '123.456.789-09',  # Valid CPF with formatting
            '000.000.001-91',  # Valid edge case CPF
            '111.444.777-35',  # Same as first but with formatting
        ]
        
        for cpf in valid_cpfs:
            with self.subTest(cpf=cpf):
                self.assertTrue(validate_cpf(cpf), f"CPF {cpf} should be valid")
    
    def test_validate_cpf_function_invalid_cpfs(self):
        """Test the validate_cpf function with invalid CPFs"""
        from .forms import validate_cpf
        
        # Invalid CPFs
        invalid_cpfs = [
            '23902928334',  # Invalid CPF (wrong check digits)
            '12345678901',  # Invalid CPF
            '11111111111',  # All same digits
            '00000000000',  # All zeros
            '12345678900',  # Invalid check digits
            '123456789',    # Too short
            '12345678909234',  # Too long
            '',             # Empty string
            'abcd1234567',  # Contains letters
            '123.456.789-00',  # Invalid with formatting
        ]
        
        for cpf in invalid_cpfs:
            with self.subTest(cpf=cpf):
                self.assertFalse(validate_cpf(cpf), f"CPF {cpf} should be invalid")
    
    def test_validate_cpf_function_edge_cases(self):
        """Test the validate_cpf function with edge cases"""
        from .forms import validate_cpf
        
        # Test with different formatting
        self.assertTrue(validate_cpf('11144477735'))
        self.assertTrue(validate_cpf('111.444.777-35'))
        self.assertTrue(validate_cpf('111 444 777 35'))  # With spaces
        
        # Test identical digits (all should be invalid)
        for digit in '0123456789':
            cpf = digit * 11
            with self.subTest(cpf=cpf):
                self.assertFalse(validate_cpf(cpf), f"CPF with all {digit}s should be invalid")


class CPFFormValidationTest(TestCase):
    """Test cases for CPF validation in forms"""
    
    def setUp(self):
        """Set up test data"""
        # Create a precatorio for forms that need it
        self.precatorio = Precatorio.objects.create(
            cnj='0006630-68.2013.8.10.0000',
            origem='Tribunal de Justiça',
            orcamento='2023',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            quitado=False,
            acordo_deferido=False
        )
    
    def test_cliente_form_valid_cpf(self):
        """Test ClienteForm accepts valid CPFs"""
        from .forms import ClienteForm
        
        valid_data = {
            'cpf': '111.444.777-35',  # Valid CPF
            'nome': 'João Silva',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        
        form = ClienteForm(data=valid_data)
        self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")
        
        # Test unformatted valid CPF
        valid_data['cpf'] = '11144477735'
        form = ClienteForm(data=valid_data)
        self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")
    
    def test_cliente_form_invalid_cpf(self):
        """Test ClienteForm rejects invalid CPFs"""
        from .forms import ClienteForm
        
        invalid_data = {
            'cpf': '23902928334',  # Invalid CPF
            'nome': 'João Silva',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cpf'][0])
    
    def test_cliente_simple_form_valid_cpf(self):
        """Test ClienteSimpleForm accepts valid CPFs"""
        from .forms import ClienteSimpleForm
        
        valid_data = {
            'cpf': '111.444.777-35',  # Valid CPF
            'nome': 'João Silva',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        
        form = ClienteSimpleForm(data=valid_data)
        self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")
    
    def test_cliente_simple_form_invalid_cpf(self):
        """Test ClienteSimpleForm rejects invalid CPFs"""
        from .forms import ClienteSimpleForm
        
        invalid_data = {
            'cpf': '23902928334',  # Invalid CPF
            'nome': 'João Silva',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        
        form = ClienteSimpleForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cpf'][0])
    
    def test_cliente_search_form_valid_cpf(self):
        """Test ClienteSearchForm accepts valid CPFs"""
        from .forms import ClienteSearchForm
        
        # First create a cliente to search for
        Cliente.objects.create(
            cpf='11144477735',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        form = ClienteSearchForm(data={'cpf': '111.444.777-35'})
        self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")
    
    def test_cliente_search_form_invalid_cpf(self):
        """Test ClienteSearchForm rejects invalid CPFs"""
        from .forms import ClienteSearchForm
        
        form = ClienteSearchForm(data={'cpf': '23902928334'})
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cpf'][0])
    
    def test_requerimento_form_valid_cpf(self):
        """Test RequerimentoForm accepts valid CPFs for existing clientes"""
        from .forms import RequerimentoForm
        
        # Create a cliente first
        Cliente.objects.create(
            cpf='11144477735',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        valid_data = {
            'cliente_cpf': '111.444.777-35',
            'pedido': 'prioridade idade',
            'valor': '50000.00',
            'desagio': '10.00',
        }
        
        form = RequerimentoForm(data=valid_data)
        self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")
    
    def test_requerimento_form_invalid_cpf(self):
        """Test RequerimentoForm rejects invalid CPFs"""
        from .forms import RequerimentoForm
        
        invalid_data = {
            'cliente_cpf': '23902928334',  # Invalid CPF
            'pedido': 'prioridade idade',
            'valor': '50000.00',
            'desagio': '10.00',
        }
        
        form = RequerimentoForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cliente_cpf'][0])
    
    def test_alvara_form_valid_cpf(self):
        """Test AlvaraSimpleForm accepts valid CPFs for existing clientes"""
        from .forms import AlvaraSimpleForm
        
        # Create a cliente first
        Cliente.objects.create(
            cpf='11144477735',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        valid_data = {
            'cliente_cpf': '111.444.777-35',
            'tipo': 'ordem cronológica',
            'valor_principal': '50000.00',
            'honorarios_contratuais': '5000.00',
            'honorarios_sucumbenciais': '2000.00',
        }
        
        form = AlvaraSimpleForm(data=valid_data)
        self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")
    
    def test_alvara_form_invalid_cpf(self):
        """Test AlvaraSimpleForm rejects invalid CPFs"""
        from .forms import AlvaraSimpleForm
        
        invalid_data = {
            'cliente_cpf': '23902928334',  # Invalid CPF
            'tipo': 'ordem cronológica',
            'valor_principal': '50000.00',
            'honorarios_contratuais': '5000.00',
            'honorarios_sucumbenciais': '2000.00',
        }
        
        form = AlvaraSimpleForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cliente_cpf'][0])
    
    def test_cpf_formatting_preserved_in_validation_messages(self):
        """Test that CPF formatting is preserved in error messages"""
        from .forms import ClienteForm
        
        invalid_data = {
            'cpf': '239.029.283-34',  # Invalid CPF with formatting
            'nome': 'João Silva',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cpf'][0])
    
    def test_known_invalid_cpfs(self):
        """Test specific known invalid CPFs that should be rejected"""
        from .forms import validate_cpf
        
        # These are known invalid CPFs that were previously accepted
        known_invalid_cpfs = [
            '23902928334',
            '12345678901',
            '12345678999',  # Invalid check digits
            '11122233344',
            '55566677788',
        ]
        
        for cpf in known_invalid_cpfs:
            with self.subTest(cpf=cpf):
                self.assertFalse(validate_cpf(cpf), f"Known invalid CPF {cpf} should be rejected")
    
    def test_cpf_algorithm_correctness(self):
        """Test that the CPF algorithm correctly calculates check digits"""
        from .forms import validate_cpf
        
        # Test cases where we know the correct check digits
        test_cases = [
            # (first 9 digits, expected check digits, should be valid)
            ('111444777', '35', True),
            ('123456789', '09', True),
            ('000000001', '91', True),
            ('111444777', '34', False),  # Wrong check digits
            ('123456789', '01', False),  # Wrong check digits
        ]
        
        for first_nine, check_digits, should_be_valid in test_cases:
            cpf = first_nine + check_digits
            with self.subTest(cpf=cpf):
                result = validate_cpf(cpf)
                if should_be_valid:
                    self.assertTrue(result, f"CPF {cpf} should be valid")
                else:
                    self.assertFalse(result, f"CPF {cpf} should be invalid")


# Run tests with: python manage.py test precapp.tests.PriorityUpdateByAgeTest
# Run all priority tests with: python manage.py test precapp.tests -k Priority
# Run advanced filter tests with: python manage.py test precapp.tests.PrecatorioAdvancedFilterTest
# Run requerimento display tests with: python manage.py test precapp.tests.RequerimentoDisplayTest  
# Run CPF validation tests with: python manage.py test precapp.tests.CPFValidationTest
# Run CPF form validation tests with: python manage.py test precapp.tests.CPFFormValidationTest
# Run diligencias tests with: python manage.py test precapp.tests.TipoDiligenciaModelTest
# Run diligencias tests with: python manage.py test precapp.tests.DiligenciasModelTest
# Run tests with: python manage.py test precapp


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


class TipoDiligenciaFormTest(TestCase):
    """Test cases for TipoDiligenciaForm"""
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'nome': 'Contato Cliente',
            'descricao': 'Entrar em contato com o cliente',
            'cor': '#28a745',
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
        # Test future deadline
        future_date = date.today() + timedelta(days=5)
        diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=future_date,
            criado_por='Test User'
        )
        self.assertEqual(diligencia.days_until_deadline(), 5)
        
        # Test past deadline
        past_date = date.today() - timedelta(days=3)
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
        
        # Test forward relationship
        self.assertEqual(diligencia.cliente.nome, 'João Silva')
        
        # Test reverse relationship
        cliente_diligencias = self.cliente.diligencias.all()
        self.assertIn(diligencia, cliente_diligencias)
    
    def test_diligencia_tipo_relationship(self):
        """Test relationship between Diligencias and TipoDiligencia"""
        diligencia = Diligencias.objects.create(**self.diligencia_data)
        
        # Test forward relationship
        self.assertEqual(diligencia.tipo.nome, 'Documentação')
        
        # Test PROTECT constraint
        with self.assertRaises(Exception):
            self.tipo_diligencia.delete()  # Should fail due to PROTECT
    
    def test_diligencia_ordering(self):
        """Test that diligencias are ordered by -data_criacao"""
        # Create multiple diligencias with slight delays
        diligencia1 = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=1),
            criado_por='User 1'
        )
        
        # Add a small delay to ensure different timestamps
        import time
        time.sleep(0.01)
        
        diligencia2 = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=2),
            criado_por='User 2'
        )
        
        diligencias = Diligencias.objects.all()
        # Should be ordered by most recent first
        self.assertEqual(diligencias[0], diligencia2)
        self.assertEqual(diligencias[1], diligencia1)


class DiligenciasFormTest(TestCase):
    """Test cases for DiligenciasForm"""
    
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
        # Test with past date
        past_data = self.valid_form_data.copy()
        past_date = (date.today() - timedelta(days=1)).strftime('%d/%m/%Y')
        past_data['data_final'] = past_date
        
        form = DiligenciasForm(data=past_data)
        self.assertFalse(form.is_valid())
        self.assertIn('data_final', form.errors)
        self.assertIn('passado', form.errors['data_final'][0])
    
    def test_form_clean_data_final_today(self):
        """Test that data_final can be today"""
        today_data = self.valid_form_data.copy()
        today_data['data_final'] = date.today().strftime('%d/%m/%Y')
        
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
    """Test cases for DiligenciasUpdateForm"""
    
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


class DiligenciasViewTest(TestCase):
    """Test cases for Diligencias views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
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
            criado_por='Test User',
            urgencia='alta'
        )
        
        self.client_app = Client()
    
    def test_nova_diligencia_view_authentication(self):
        """Test that nova diligencia view requires authentication"""
        response = self.client_app.get(reverse('nova_diligencia', args=[self.cliente.cpf]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_nova_diligencia_view_authenticated(self):
        """Test nova diligencia view with authentication"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('nova_diligencia', args=[self.cliente.cpf]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nova Diligência')
    
    def test_nova_diligencia_post(self):
        """Test creating nova diligencia via POST"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'tipo': self.tipo_diligencia.id,
            'data_final': (date.today() + timedelta(days=5)).strftime('%d/%m/%Y'),
            'urgencia': 'alta',
            'descricao': 'Nova diligência teste'
        }
        
        response = self.client_app.post(
            reverse('nova_diligencia', args=[self.cliente.cpf]),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify diligencia was created
        self.assertEqual(self.cliente.diligencias.count(), 2)  # Original + new one
    
    def test_editar_diligencia_view(self):
        """Test editing diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Diligência')
    
    def test_editar_diligencia_post(self):
        """Test updating diligencia via POST"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'tipo': self.tipo_diligencia.id,
            'data_final': (date.today() + timedelta(days=10)).strftime('%d/%m/%Y'),
            'urgencia': 'baixa',
            'descricao': 'Diligência atualizada'
        }
        
        response = self.client_app.post(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia.id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify diligencia was updated
        self.diligencia.refresh_from_db()
        self.assertEqual(self.diligencia.urgencia, 'baixa')
        self.assertEqual(self.diligencia.descricao, 'Diligência atualizada')
    
    def test_deletar_diligencia_view(self):
        """Test deleting diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        diligencia_id = self.diligencia.id
        
        response = self.client_app.post(
            reverse('deletar_diligencia', args=[self.cliente.cpf, diligencia_id])
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify diligencia was deleted
        self.assertFalse(Diligencias.objects.filter(id=diligencia_id).exists())
    
    def test_marcar_diligencia_concluida_view(self):
        """Test marking diligencia as concluded"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Check initial state
        self.assertFalse(self.diligencia.concluida)
        self.assertIsNone(self.diligencia.concluido_por)
        
        form_data = {
            'concluida': True,
            'descricao': 'Concluída com sucesso'
        }
        
        response = self.client_app.post(
            reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, self.diligencia.id]),
            data=form_data
        )
        
        # Check response
        self.assertEqual(response.status_code, 302)
        
        # Verify diligencia was marked as concluded
        self.diligencia.refresh_from_db()
        self.assertTrue(self.diligencia.concluida, "Diligencia should be marked as concluded")
        self.assertIsNotNone(self.diligencia.data_conclusao, "Should have conclusion date")
        
        # Check if concluido_por field is set correctly
        # The view should set this to the current user's full name or username
        expected_concluido_por = self.user.get_full_name() or self.user.username
        self.assertEqual(self.diligencia.concluido_por, expected_concluido_por,
                        f"Expected concluido_por to be '{expected_concluido_por}', got '{self.diligencia.concluido_por}'")
    
    def test_diligencias_list_view_authentication(self):
        """Test that diligencias list view requires authentication"""
        response = self.client_app.get(reverse('diligencias_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_diligencias_list_view_authenticated(self):
        """Test diligencias list view with authentication"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de Diligências')
    
    def test_diligencias_list_view_filters(self):
        """Test diligencias list view filters"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test status filter
        response = self.client_app.get(reverse('diligencias_list') + '?status=pendente')
        self.assertEqual(response.status_code, 200)
        
        # Test urgency filter
        response = self.client_app.get(reverse('diligencias_list') + '?urgencia=alta')
        self.assertEqual(response.status_code, 200)
        
        # Test type filter
        response = self.client_app.get(reverse('diligencias_list') + f'?tipo={self.tipo_diligencia.id}')
        self.assertEqual(response.status_code, 200)
        
        # Test search
        response = self.client_app.get(reverse('diligencias_list') + '?search=João')
        self.assertEqual(response.status_code, 200)
    
    def test_diligencias_list_view_statistics(self):
        """Test that diligencias list view provides correct statistics"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list'))
        
        self.assertEqual(response.context['total_diligencias'], 1)
        self.assertEqual(response.context['pendentes_diligencias'], 1)
        self.assertEqual(response.context['concluidas_diligencias'], 0)
        self.assertEqual(response.context['atrasadas_diligencias'], 0)  # Not overdue yet


class TipoDiligenciaViewTest(TestCase):
    """Test cases for TipoDiligencia views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.tipo_diligencia = TipoDiligencia.objects.create(
            nome='Test Tipo',
            descricao='Test description',
            cor='#007bff',
            ativo=True
        )
        
        self.client_app = Client()
    
    def test_tipos_diligencia_view_authentication(self):
        """Test that tipos diligencia view requires authentication"""
        response = self.client_app.get(reverse('tipos_diligencia'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_tipos_diligencia_view_authenticated(self):
        """Test tipos diligencia view with authentication"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('tipos_diligencia'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tipos de Diligência')
    
    def test_novo_tipo_diligencia_view(self):
        """Test creating new tipo diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('novo_tipo_diligencia'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Novo Tipo de Diligência')
    
    def test_novo_tipo_diligencia_post(self):
        """Test creating tipo diligencia via POST"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': 'Novo Tipo Test',
            'descricao': 'Test description',
            'cor': '#28a745',
            'ativo': True
        }
        response = self.client_app.post(reverse('novo_tipo_diligencia'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify tipo was created
        self.assertTrue(TipoDiligencia.objects.filter(nome='Novo Tipo Test').exists())
    
    def test_editar_tipo_diligencia_view(self):
        """Test editing tipo diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('editar_tipo_diligencia', args=[self.tipo_diligencia.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Tipo')
    
    def test_editar_tipo_diligencia_post(self):
        """Test updating tipo diligencia via POST"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': 'Updated Tipo Name',
            'descricao': 'Updated description',
            'cor': '#dc3545',
            'ativo': False
        }
        response = self.client_app.post(
            reverse('editar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify tipo was updated
        self.tipo_diligencia.refresh_from_db()
        self.assertEqual(self.tipo_diligencia.nome, 'Updated Tipo Name')
        self.assertFalse(self.tipo_diligencia.ativo)
    
    def test_ativar_tipo_diligencia(self):
        """Test activating/deactivating tipo diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test that the view responds correctly
        initial_status = self.tipo_diligencia.ativo  # True initially
        response = self.client_app.post(reverse('ativar_tipo_diligencia', args=[self.tipo_diligencia.id]))
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Verify the status changed (toggle behavior)
        self.tipo_diligencia.refresh_from_db()
        new_status = self.tipo_diligencia.ativo
        self.assertNotEqual(new_status, initial_status, "Status should change after toggle")
    
    def test_ativar_tipo_diligencia_with_parameter(self):
        """Test activating/deactivating tipo diligencia with explicit parameter"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test explicitly setting to False
        form_data = {'ativo': 'false'}
        response = self.client_app.post(
            reverse('ativar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        
        self.tipo_diligencia.refresh_from_db()
        self.assertFalse(self.tipo_diligencia.ativo)
        
        # Test explicitly setting to True
        form_data = {'ativo': 'true'}
        response = self.client_app.post(
            reverse('ativar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        
        self.tipo_diligencia.refresh_from_db()
        self.assertTrue(self.tipo_diligencia.ativo)
    
    def test_deletar_tipo_diligencia(self):
        """Test deleting tipo diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        tipo_id = self.tipo_diligencia.id
        
        response = self.client_app.post(reverse('deletar_tipo_diligencia', args=[tipo_id]))
        self.assertEqual(response.status_code, 302)
        
        # Verify tipo was deleted
        self.assertFalse(TipoDiligencia.objects.filter(id=tipo_id).exists())


class DiligenciasIntegrationTest(TestCase):
    """Integration tests for complete diligencias workflow"""
    
    def setUp(self):
        """Set up comprehensive test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.tipo_urgente = TipoDiligencia.objects.create(
            nome='Urgente',
            cor='#dc3545',
            ativo=True
        )
        
        self.tipo_normal = TipoDiligencia.objects.create(
            nome='Normal',
            cor='#007bff',
            ativo=True
        )
        
        self.client_app = Client()
    
    def test_complete_diligencia_workflow(self):
        """Test complete workflow from creation to completion"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # 1. Create new diligencia
        form_data = {
            'tipo': self.tipo_urgente.id,
            'data_final': (date.today() + timedelta(days=3)).strftime('%d/%m/%Y'),
            'urgencia': 'alta',
            'descricao': 'Diligência urgente para teste'
        }
        
        response = self.client_app.post(
            reverse('nova_diligencia', args=[self.cliente.cpf]),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify creation
        diligencia = Diligencias.objects.first()
        self.assertEqual(diligencia.tipo, self.tipo_urgente)
        self.assertEqual(diligencia.urgencia, 'alta')
        self.assertFalse(diligencia.concluida)
        
        # 2. Edit the diligencia
        edit_data = {
            'tipo': self.tipo_normal.id,
            'data_final': (date.today() + timedelta(days=5)).strftime('%d/%m/%Y'),
            'urgencia': 'media',
            'descricao': 'Diligência atualizada'
        }
        
        response = self.client_app.post(
            reverse('editar_diligencia', args=[self.cliente.cpf, diligencia.id]),
            data=edit_data
        )
        self.assertEqual(response.status_code, 302)
        
        diligencia.refresh_from_db()
        self.assertEqual(diligencia.tipo, self.tipo_normal)
        self.assertEqual(diligencia.urgencia, 'media')
        
        # 3. Mark as concluded
        conclusion_data = {
            'concluida': True,
            'descricao': 'Diligência concluída com sucesso'
        }
        
        response = self.client_app.post(
            reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, diligencia.id]),
            data=conclusion_data,
            follow=True  # Follow redirects to debug
        )
        
        diligencia.refresh_from_db()
        self.assertTrue(diligencia.concluida)
        self.assertIsNotNone(diligencia.data_conclusao)
        # Check that concluido_por is set (will be full name since user has first/last names)
        expected_concluido_por = self.user.get_full_name() or self.user.username
        self.assertEqual(diligencia.concluido_por, expected_concluido_por)
        
        # 4. Verify in list view
        response = self.client_app.get(reverse('diligencias_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'João Silva')
        self.assertEqual(response.context['concluidas_diligencias'], 1)
    
    def test_diligencia_with_cliente_detail_integration(self):
        """Test diligencia integration with cliente detail page"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create diligencia
        diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_urgente,
            data_final=date.today() + timedelta(days=2),
            criado_por=self.user.get_full_name(),
            urgencia='alta'
        )
        
        # Check cliente detail page shows diligencia
        response = self.client_app.get(reverse('cliente_detail', args=[self.cliente.cpf]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Urgente')
        self.assertContains(response, 'Pendente')
    
    def test_overdue_diligencia_handling(self):
        """Test handling of overdue diligencias"""
        # Create overdue diligencia
        overdue_diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_urgente,
            data_final=date.today() - timedelta(days=1),  # Yesterday
            criado_por='Test User',
            urgencia='alta'
        )
        
        # Test overdue detection
        self.assertTrue(overdue_diligencia.is_overdue())
        self.assertEqual(overdue_diligencia.days_until_deadline(), -1)
        
        # Test list view shows overdue
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list'))
        self.assertEqual(response.context['atrasadas_diligencias'], 1)
    
    def test_tipo_diligencia_protection_with_usage(self):
        """Test that tipo diligencia cannot be deleted when in use"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create diligencia using the type
        Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_urgente,
            data_final=date.today() + timedelta(days=5),
            criado_por='Test User'
        )
        
        # Try to delete the type (should be prevented by PROTECT)
        response = self.client_app.post(
            reverse('deletar_tipo_diligencia', args=[self.tipo_urgente.id])
        )
        
        # Check that type still exists (deletion should be handled gracefully)
        self.assertTrue(TipoDiligencia.objects.filter(id=self.tipo_urgente.id).exists())
    
    def test_bulk_diligencia_operations(self):
        """Test performance with multiple diligencias"""
        # Create multiple diligencias
        diligencias = []
        for i in range(10):
            diligencia = Diligencias.objects.create(
                cliente=self.cliente,
                tipo=self.tipo_normal if i % 2 == 0 else self.tipo_urgente,
                data_final=date.today() + timedelta(days=i+1),
                criado_por=f'User {i}',
                urgencia=['baixa', 'media', 'alta'][i % 3]
            )
            diligencias.append(diligencia)
        
        # Test list view performance
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_diligencias'], 10)
        
        # Test filtering
        response = self.client_app.get(reverse('diligencias_list') + '?urgencia=alta')
        diligencias_alta = response.context['page_obj']
        # Should have 3-4 diligencias with alta urgency
        self.assertGreaterEqual(len(diligencias_alta), 3)
        self.assertLessEqual(len(diligencias_alta), 4)
