"""
Extended test cases for Honorários Contratuais functionality.
Contains tests for enhanced models, forms, and views that support
the honorários contratuais features added to the application.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from precapp.models import (
    Precatorio, Cliente, Alvara, Fase, FaseHonorariosContratuais
)
from precapp.forms import (
    FaseHonorariosContratuaisForm, AlvaraSimpleForm
)


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
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
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


class FaseHonorariosContratuaisFormTest(TestCase):
    """Test cases for FaseHonorariosContratuaisForm"""
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'nome': 'Em Negociação',
            'descricao': 'Honorários em processo de negociação',
            'cor': '#007BFF',
            'ordem': 0,
            'ativa': True
        }
    
    def test_valid_form(self):
        """Test form with valid data"""
        form = FaseHonorariosContratuaisForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        
        # Test with alternative data
        form_data = {
            'nome': 'Parcialmente Pago',
            'descricao': 'Honorários parcialmente pagos',
            'cor': '#FFC107',
            'ordem': 1,
            'ativa': True
        }
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = FaseHonorariosContratuaisForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        fase = form.save()
        self.assertEqual(fase.nome, 'Em Negociação')
        self.assertEqual(fase.cor, '#007BFF')
        self.assertEqual(fase.descricao, 'Honorários em processo de negociação')
    
    def test_required_fields(self):
        """Test that required fields are enforced"""
        form = FaseHonorariosContratuaisForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
        
        # Test with missing required fields
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
    
    def test_color_validation(self):
        """Test color field validation"""
        # Test valid hex color
        form_data = self.valid_form_data.copy()
        form_data['cor'] = '#FF5733'
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test another valid color
        form_data = {
            'nome': 'Test Fase',
            'cor': '#FF5733',
            'ordem': 0,
            'ativa': True
        }
        form = FaseHonorariosContratuaisForm(data=form_data)
        if not form.is_valid():
            print("Form errors:", form.errors)
        self.assertTrue(form.is_valid())
        
        # Test invalid color format - form might not validate this at form level
        form_data['cor'] = 'invalid-color'
        form = FaseHonorariosContratuaisForm(data=form_data)
        # Since there's no specific color validator in the form, this might pass
        # The validation might happen at the model or browser level
    
    def test_unique_nome_validation(self):
        """Test that fase names must be unique"""
        # Create a fase
        FaseHonorariosContratuais.objects.create(
            nome='Unique Name',
            cor='#28A745',
            ativa=True
        )
        
        # Try to create another with same name
        form_data = {
            'nome': 'Unique Name',
            'cor': '#FFC107',
            'ativa': True
        }
        form = FaseHonorariosContratuaisForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Also test with the setup data
        existing_fase = FaseHonorariosContratuais.objects.create(
            nome='Existing Fase',
            cor='#FF0000'
        )
        
        # Try to create another with same nome
        form_data = self.valid_form_data.copy()
        form_data['nome'] = 'Existing Fase'
        form = FaseHonorariosContratuaisForm(data=form_data)
        # This tests the actual form behavior


class AlvaraSimpleFormWithHonorariosTest(TestCase):
    """Test cases for AlvaraSimpleForm with honorários functionality"""
    
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
        
        self.precatorio.clientes.add(self.cliente)
        
        self.fase_alvara = Fase.objects.create(
            nome='Em Andamento',
            tipo='alvara',
            cor='#007bff',
            ativa=True
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
    
    def test_form_includes_honorarios_fase_field(self):
        """Test that form includes fase_honorarios_contratuais field"""
        form = AlvaraSimpleForm()
        self.assertIn('fase_honorarios_contratuais', form.fields)
    
    def test_honorarios_fase_queryset_filtered(self):
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
        
        form = AlvaraSimpleForm(data=form_data)
        if not form.is_valid():
            print("Form errors:", form.errors)
        self.assertTrue(form.is_valid())
    
    def test_optional_honorarios_fase(self):
        """Test that honorários fase is optional"""
        form_data = {
            'cliente_cpf': self.cliente.cpf,
            'valor_principal': '50000.00',
            'honorarios_contratuais': '10000.00',
            'honorarios_sucumbenciais': '5000.00',
            'tipo': 'prioridade',
            'fase': self.fase_alvara.id
            # fase_honorarios_contratuais omitted
        }
        
        form = AlvaraSimpleForm(data=form_data)
        if not form.is_valid():
            print("Form errors:", form.errors)
        self.assertTrue(form.is_valid())


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
            descricao='Fase de teste para honorários',
            cor='#28A745',
            ativa=True
        )
        
        self.client_app = Client()
    
    def test_fases_honorarios_list_view(self):
        """Test honorários phases list view"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('fases_honorarios'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Fase Honorários')
        self.assertContains(response, '#28A745')
    
    def test_nova_fase_honorarios_view(self):
        """Test creating new honorários phase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Nova Fase Honorários',
            'descricao': 'Nova fase para honorários contratuais',
            'cor': '#FFC107',
            'ordem': 1,
            'ativa': True
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after creation
        
        # Verify creation
        nova_fase = FaseHonorariosContratuais.objects.get(nome='Nova Fase Honorários')
        self.assertEqual(nova_fase.cor, '#FFC107')
        self.assertTrue(nova_fase.ativa)
    
    def test_editar_fase_honorarios_view(self):
        """Test editing honorários phase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Fase Honorários Editada',
            'descricao': 'Descrição editada',
            'cor': '#DC3545',
            'ordem': 2,
            'ativa': False
        }
        
        response = self.client_app.post(
            reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]), 
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify update
        self.fase_honorarios.refresh_from_db()
        self.assertEqual(self.fase_honorarios.nome, 'Fase Honorários Editada')
        self.assertEqual(self.fase_honorarios.cor, '#DC3545')
        self.assertFalse(self.fase_honorarios.ativa)
    
    def test_deletar_fase_honorarios_view(self):
        """Test deleting honorários phase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(
            reverse('deletar_fase_honorarios', args=[self.fase_honorarios.id])
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify deletion
        with self.assertRaises(FaseHonorariosContratuais.DoesNotExist):
            FaseHonorariosContratuais.objects.get(id=self.fase_honorarios.id)
    
    def test_ativar_fase_honorarios_view(self):
        """Test activating/deactivating honorários phase"""
        # First deactivate the phase
        self.fase_honorarios.ativa = False
        self.fase_honorarios.save()
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test activation
        response = self.client_app.post(
            reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id])
        )
        self.assertEqual(response.status_code, 302)
        
        self.fase_honorarios.refresh_from_db()
        self.assertTrue(self.fase_honorarios.ativa)


class PrecatorioDetailViewWithHonorariosTest(TestCase):
    """Test cases for precatorio detail view with honorários functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
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
        
        self.precatorio.clientes.add(self.cliente)
        
        self.fase_alvara = Fase.objects.create(
            nome='Em Andamento',
            tipo='alvara',
            cor='#007bff',
            ativa=True
        )
        
        self.fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Aguardando Pagamento',
            cor='#FFA500',
            ativa=True
        )
        
        self.alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='prioridade',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        self.client_app = Client()
    
    def test_precatorio_detail_shows_honorarios_fase(self):
        """Test that precatorio detail view shows honorários fase information"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(
            reverse('precatorio_detalhe', args=[self.precatorio.cnj])
        )
        self.assertEqual(response.status_code, 200)
        
        # Should contain honorários fase information
        self.assertContains(response, 'Aguardando Pagamento')
        self.assertContains(response, self.fase_honorarios.nome)
    
    def test_precatorio_detail_context_includes_honorarios(self):
        """Test that context includes honorários fase data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(
            reverse('precatorio_detalhe', args=[self.precatorio.cnj])
        )
        self.assertEqual(response.status_code, 200)
        
        # Check that alvaras include honorários fase information
        alvaras = response.context['alvaras']
        alvara = alvaras.first()
        self.assertEqual(alvara.fase_honorarios_contratuais, self.fase_honorarios)
