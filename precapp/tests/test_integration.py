"""
Integration test cases for the precatorios application.
Contains all integration tests migrated from the monolithic tests.py file.
These tests validate complete workflows and end-to-end functionality.
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
from precapp.forms import AlvaraSimpleForm


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
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Create cliente
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Link the cliente to the precatorio (required by new validation)
        self.precatorio.clientes.add(self.cliente)
        
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
        
        # Check that both types of phases are counted correctly
        context = response.context
        self.assertEqual(context['total_fases_principais'], 3)  # alvara, requerimento, ambos
        self.assertEqual(context['total_fases_honorarios'], 3)  # 3 honorários phases
        self.assertEqual(context['fases_principais_ativas'], 3)  # All should be active
        self.assertEqual(context['fases_honorarios_ativas'], 3)  # All should be active


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
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Create cliente
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Link cliente to precatorio
        self.precatorio.clientes.add(self.cliente)
        
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


class PriorityUpdateIntegrationTest(TestCase):
    """Integration tests for the complete priority update workflow"""
    
    def setUp(self):
        """Set up comprehensive test data"""
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
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='2345678-90.2023.8.26.0200',
            orcamento=2023,
            origem='Tribunal de Campinas',
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente',
            valor_de_face=75000.00,
            ultima_atualizacao=75000.00,
            data_ultima_atualizacao=date(2023, 2, 20),
            percentual_contratuais_assinado=25.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=15.0
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
        
        # Verify initial state
        self.assertFalse(self.client_senior_no_priority.prioridade)
        
        # 2. Execute priority update by age
        response = self.client_app.post(reverse('update_priority_by_age'))
        self.assertEqual(response.status_code, 302)  # Should redirect after update
        
        # 3. Verify database changes
        self.client_senior_no_priority.refresh_from_db()
        self.client_senior_has_priority.refresh_from_db()
        self.client_young.refresh_from_db()
        
        # Senior without priority should now have priority
        self.assertTrue(self.client_senior_no_priority.prioridade)
        # Senior who already had priority should still have priority
        self.assertTrue(self.client_senior_has_priority.prioridade)
        # Young client should still not have priority
        self.assertFalse(self.client_young.prioridade)
        
        # 4. Verify in client list after update
        response = self.client_app.get(reverse('clientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Maria Santos (65 anos)')


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
        
        # 3. Mark as concluded using DiligenciasUpdateForm
        from precapp.forms import DiligenciasUpdateForm
        conclusion_data = {
            'concluida': True,
            'descricao': 'Diligência concluída com sucesso'
        }
        
        form = DiligenciasUpdateForm(data=conclusion_data, instance=diligencia)
        self.assertTrue(form.is_valid())
        updated_diligencia = form.save()
        
        self.assertTrue(updated_diligencia.concluida)
        self.assertIsNotNone(updated_diligencia.data_conclusao)
        
        # 4. Verify list view shows proper statistics
        response = self.client_app.get(reverse('diligencias_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'João Silva')
    
    def test_diligencia_with_cliente_detail_integration(self):
        """Test diligencia creation from cliente detail page"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Access cliente detail page
        response = self.client_app.get(reverse('cliente_detail', args=[self.cliente.cpf]))
        self.assertEqual(response.status_code, 200)
        
        # Create diligencia from cliente detail
        diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_normal,
            data_final=date.today() + timedelta(days=7),
            urgencia='media',
            criado_por=self.user.get_full_name() or self.user.username,
            descricao='Diligência criada via detalhe do cliente'
        )
        
        # Verify integration
        self.assertEqual(diligencia.cliente, self.cliente)
        self.assertIn(diligencia, self.cliente.diligencias.all())
        
        # Test that cliente detail page shows the diligencia
        response = self.client_app.get(reverse('cliente_detail', args=[self.cliente.cpf]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Diligência criada via detalhe')
    
    def test_overdue_diligencias_integration(self):
        """Test integration with overdue diligencias functionality"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create overdue diligencia
        overdue_diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_urgente,
            data_final=date.today() - timedelta(days=2),  # 2 days overdue
            urgencia='alta',
            criado_por=self.user.username,
            descricao='Diligência em atraso'
        )
        
        # Create future diligencia
        future_diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_normal,
            data_final=date.today() + timedelta(days=5),
            urgencia='media',
            criado_por=self.user.username,
            descricao='Diligência futura'
        )
        
        # Test is_overdue method
        self.assertTrue(overdue_diligencia.is_overdue())
        self.assertFalse(future_diligencia.is_overdue())
        
        # Test days_until_deadline
        self.assertEqual(overdue_diligencia.days_until_deadline(), -2)
        self.assertEqual(future_diligencia.days_until_deadline(), 5)
        
        # Test urgencia color
        self.assertEqual(overdue_diligencia.get_urgencia_color(), 'danger')
        self.assertEqual(future_diligencia.get_urgencia_color(), 'warning')
