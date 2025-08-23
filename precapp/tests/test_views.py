"""
Test cases for all views in the precatorios application.
Contains all view-related tests migrated from the monolithic tests.py file.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from precapp.models import (
    Fase, FaseHonorariosContratuais, Precatorio, Cliente, 
    Alvara, Requerimento, TipoDiligencia, Diligencias
)


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
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
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
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente',
            valor_de_face=10000.00,
            ultima_atualizacao=10000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='2345678-90.2023.8.26.0200',
            orcamento=2023,
            origem='Tribunal de Campinas',
            credito_principal='quitado',
            honorarios_contratuais='quitado',
            honorarios_sucumbenciais='quitado',
            valor_de_face=20000.00,
            ultima_atualizacao=20000.00,
            data_ultima_atualizacao=date(2023, 2, 20),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0
        )
        
        self.precatorio3 = Precatorio.objects.create(
            cnj='3456789-01.2023.8.26.0300',
            orcamento=2023,
            origem='Tribunal de Santos',
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente',
            valor_de_face=15000.00,
            ultima_atualizacao=15000.00,
            data_ultima_atualizacao=date(2023, 3, 25),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0
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
    
    def test_filter_by_credito_principal_quitado(self):
        """Test filtering by credito_principal status (quitado)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?credito_principal=quitado')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 1)
        self.assertEqual(precatorios[0].credito_principal, 'quitado')
    
    def test_filter_by_credito_principal_pendente(self):
        """Test filtering by credito_principal status (pendente)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?credito_principal=pendente')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        self.assertEqual(len(precatorios), 2)
        for precatorio in precatorios:
            self.assertEqual(precatorio.credito_principal, 'pendente')
    
    def test_multiple_filters(self):
        """Test combining multiple filters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?cnj=test&credito_principal=pendente')
        
        self.assertEqual(response.status_code, 200)
        precatorios = response.context['precatorios']
        # Should return no results since no precatorio has both cnj='test' and credito_principal='pendente'
        self.assertEqual(len(precatorios), 0)

    def test_filter_context_values(self):
        """Test that current filter values are passed to template context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/precatorios/?cnj=test&origem=tribunal&credito_principal=quitado')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_cnj'], 'test')
        self.assertEqual(response.context['current_origem'], 'tribunal')
        self.assertEqual(response.context['current_credito_principal'], 'quitado')


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
            'ordem': 0,
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
            'ordem': 1,
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
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
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
