from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
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


# Run tests with: python manage.py test precapp
