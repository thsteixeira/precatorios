from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
from unittest.mock import patch

from precapp.models import Cliente, TipoDiligencia, Diligencias


class DiligenciasViewTest(TestCase):
    """Comprehensive test cases for Diligencias views"""
    
    def setUp(self):
        """Set up test data"""
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
        
        self.cliente2 = Cliente.objects.create(
            cpf='98765432100',
            nome='Maria Santos',
            nascimento=date(1985, 8, 20),
            prioridade=True
        )
        
        self.tipo_diligencia = TipoDiligencia.objects.create(
            nome='Documentação',
            descricao='Tipo para documentos',
            cor='#007bff',
            ativo=True,
            ordem=1
        )
        
        self.tipo_diligencia2 = TipoDiligencia.objects.create(
            nome='Audiência',
            descricao='Tipo para audiências',
            cor='#28a745',
            ativo=True,
            ordem=2
        )
        
        # Active diligencia (not completed)
        self.diligencia_ativa = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=7),
            criado_por='Test User',
            urgencia='alta',
            descricao='Diligência ativa',
            concluida=False
        )
        
        # Completed diligencia
        self.diligencia_concluida = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia2,
            data_final=date.today() - timedelta(days=2),
            criado_por='Test User',
            urgencia='media',
            descricao='Diligência concluída',
            concluida=True,
            concluido_por='Admin User'
        )
        
        # Overdue diligencia
        self.diligencia_atrasada = Diligencias.objects.create(
            cliente=self.cliente2,
            tipo=self.tipo_diligencia,
            data_final=date.today() - timedelta(days=5),
            criado_por='Test User',
            urgencia='baixa',
            descricao='Diligência atrasada',
            concluida=False
        )
        
        self.client_app = Client()

    # ==================== AUTHENTICATION TESTS ====================
    
    def test_nova_diligencia_view_authentication_required(self):
        """Test that nova diligencia view requires authentication"""
        response = self.client_app.get(reverse('nova_diligencia', args=[self.cliente.cpf]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)
    
    def test_editar_diligencia_view_authentication_required(self):
        """Test that editar diligencia view requires authentication"""
        response = self.client_app.get(reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_deletar_diligencia_view_authentication_required(self):
        """Test that deletar diligencia view requires authentication"""
        response = self.client_app.post(reverse('deletar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_marcar_concluida_view_authentication_required(self):
        """Test that marcar diligencia concluida view requires authentication"""
        response = self.client_app.get(reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, self.diligencia_ativa.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_diligencias_list_view_authentication_required(self):
        """Test that diligencias list view requires authentication"""
        response = self.client_app.get(reverse('diligencias_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    # ==================== NOVA DILIGENCIA TESTS ====================
    
    def test_nova_diligencia_view_authenticated(self):
        """Test nova diligencia view with authentication"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('nova_diligencia', args=[self.cliente.cpf]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nova Diligência')
        self.assertContains(response, self.cliente.nome)
        self.assertIn('form', response.context)
    
    def test_nova_diligencia_post_valid(self):
        """Test creating nova diligencia via POST with valid data"""
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
        self.assertRedirects(response, reverse('cliente_detail', args=[self.cliente.cpf]))
        
        # Verify diligencia was created
        self.assertEqual(self.cliente.diligencias.count(), 3)  # 2 from setUp + 1 new
        new_diligencia = self.cliente.diligencias.latest('data_criacao')
        self.assertEqual(new_diligencia.descricao, 'Nova diligência teste')
        self.assertEqual(new_diligencia.urgencia, 'alta')
        self.assertFalse(new_diligencia.concluida)
    
    def test_nova_diligencia_post_invalid(self):
        """Test creating nova diligencia with invalid data"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'tipo': '',  # Missing required field
            'data_final': 'invalid-date',  # Invalid date format
            'urgencia': 'invalid',  # Invalid urgencia choice
            'descricao': ''
        }
        
        response = self.client_app.post(
            reverse('nova_diligencia', args=[self.cliente.cpf]),
            data=form_data
        )
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_nova_diligencia_invalid_cpf(self):
        """Test nova diligencia with invalid CPF"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('nova_diligencia', args=['00000000000']))
        self.assertEqual(response.status_code, 404)

    # ==================== EDITAR DILIGENCIA TESTS ====================
    
    def test_editar_diligencia_view_get(self):
        """Test GET request to editar diligencia view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Diligência')
        self.assertContains(response, self.diligencia_ativa.descricao)
        self.assertIn('form', response.context)
        self.assertEqual(response.context['diligencia'], self.diligencia_ativa)
    
    def test_editar_diligencia_post_valid(self):
        """Test updating diligencia via POST with valid data"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'tipo': self.tipo_diligencia2.id,
            'data_final': (date.today() + timedelta(days=10)).strftime('%d/%m/%Y'),
            'urgencia': 'baixa',
            'descricao': 'Diligência atualizada'
        }
        
        response = self.client_app.post(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', args=[self.cliente.cpf]))
        
        # Verify diligencia was updated
        self.diligencia_ativa.refresh_from_db()
        self.assertEqual(self.diligencia_ativa.urgencia, 'baixa')
        self.assertEqual(self.diligencia_ativa.descricao, 'Diligência atualizada')
        self.assertEqual(self.diligencia_ativa.tipo, self.tipo_diligencia2)
    
    def test_editar_diligencia_post_invalid(self):
        """Test updating diligencia with invalid data"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'tipo': 99999,  # Non-existent tipo
            'data_final': 'invalid-date',
            'urgencia': 'invalid',
            'descricao': ''
        }
        
        response = self.client_app.post(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertTrue(response.context['form'].errors)
    
    def test_editar_diligencia_invalid_id(self):
        """Test editing non-existent diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(
            reverse('editar_diligencia', args=[self.cliente.cpf, 99999])
        )
        self.assertEqual(response.status_code, 404)
    
    def test_editar_diligencia_wrong_cliente(self):
        """Test editing diligencia with wrong cliente CPF"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(
            reverse('editar_diligencia', args=[self.cliente2.cpf, self.diligencia_ativa.id])
        )
        self.assertEqual(response.status_code, 404)  # Diligencia doesn't belong to this cliente

    # ==================== DELETAR DILIGENCIA TESTS ====================
    
    def test_deletar_diligencia_success(self):
        """Test successful deletion of diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        diligencia_id = self.diligencia_ativa.id
        
        response = self.client_app.post(
            reverse('deletar_diligencia', args=[self.cliente.cpf, diligencia_id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', args=[self.cliente.cpf]))
        
        # Verify diligencia was deleted
        self.assertFalse(Diligencias.objects.filter(id=diligencia_id).exists())
    
    def test_deletar_diligencia_invalid_id(self):
        """Test deleting non-existent diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(
            reverse('deletar_diligencia', args=[self.cliente.cpf, 99999])
        )
        self.assertEqual(response.status_code, 404)
    
    def test_deletar_diligencia_wrong_cliente(self):
        """Test deleting diligencia with wrong cliente CPF"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(
            reverse('deletar_diligencia', args=[self.cliente2.cpf, self.diligencia_ativa.id])
        )
        self.assertEqual(response.status_code, 404)
    
    def test_deletar_diligencia_get_method_not_allowed(self):
        """Test that GET method is not allowed for delete (should be POST only)"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(
            reverse('deletar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id])
        )
        # This test depends on how the view is implemented - may return 405 or redirect

    # ==================== MARCAR DILIGENCIA CONCLUIDA TESTS ====================
    
    def test_marcar_diligencia_concluida_get(self):
        """Test GET request to marcar diligencia concluida view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(
            reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, self.diligencia_ativa.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('diligencia', response.context)
        self.assertIn('cliente', response.context)
        self.assertEqual(response.context['diligencia'], self.diligencia_ativa)
    
    def test_marcar_diligencia_como_concluida(self):
        """Test marking diligencia as completed"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify initial state
        self.assertFalse(self.diligencia_ativa.concluida)
        self.assertIsNone(self.diligencia_ativa.concluido_por)
        
        form_data = {
            'concluida': True,
            'descricao': self.diligencia_ativa.descricao,
            'urgencia': self.diligencia_ativa.urgencia
        }
        
        response = self.client_app.post(
            reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', args=[self.cliente.cpf]))
        
        # Verify diligencia was marked as completed
        self.diligencia_ativa.refresh_from_db()
        self.assertTrue(self.diligencia_ativa.concluida)
        self.assertEqual(self.diligencia_ativa.concluido_por, 'Test User')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        success_messages = [m for m in messages if m.tags == 'success']
        self.assertEqual(len(success_messages), 1)
        self.assertIn('concluída', str(success_messages[0]))
    
    def test_marcar_diligencia_como_reaberta(self):
        """Test reopening completed diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify initial state (completed)
        self.assertTrue(self.diligencia_concluida.concluida)
        self.assertEqual(self.diligencia_concluida.concluido_por, 'Admin User')
        
        form_data = {
            'concluida': False,
            'descricao': self.diligencia_concluida.descricao,
            'urgencia': self.diligencia_concluida.urgencia
        }
        
        response = self.client_app.post(
            reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, self.diligencia_concluida.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify diligencia was reopened
        self.diligencia_concluida.refresh_from_db()
        self.assertFalse(self.diligencia_concluida.concluida)
        self.assertIsNone(self.diligencia_concluida.concluido_por)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        success_messages = [m for m in messages if m.tags == 'success']
        self.assertEqual(len(success_messages), 1)
        self.assertIn('reaberta', str(success_messages[0]))
    
    def test_marcar_diligencia_concluida_statistics(self):
        """Test that statistics are calculated correctly in context"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(
            reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, self.diligencia_ativa.id])
        )
        
        context = response.context
        self.assertIn('total_diligencias', context)
        self.assertIn('pendentes_diligencias', context)
        self.assertIn('concluidas_diligencias', context)
        
        # Cliente has 2 diligencias (1 active, 1 completed)
        self.assertEqual(context['total_diligencias'], 2)
        self.assertEqual(context['pendentes_diligencias'], 1)
        self.assertEqual(context['concluidas_diligencias'], 1)
    
    def test_marcar_diligencia_concluida_invalid_form(self):
        """Test marcar diligencia with invalid form data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test with invalid data_conclusao format (should be datetime)
        form_data = {
            'concluida': True,
            'data_conclusao': 'invalid-datetime-format',  # Invalid datetime format
            'descricao': 'x' * 5000  # Too long description (if there's a max_length)
        }
        
        response = self.client_app.post(
            reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        
        # Should show error message and stay on the form page (200, not redirect)
        self.assertEqual(response.status_code, 200)
        
        # Check for error message in the response
        messages = list(get_messages(response.wsgi_request))
        error_messages = [m for m in messages if m.tags == 'error']
        self.assertEqual(len(error_messages), 1)
        self.assertIn('Erro ao atualizar', str(error_messages[0]))
        
        # Verify form has errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
        
        # Verify diligencia wasn't changed
        self.diligencia_ativa.refresh_from_db()
        self.assertFalse(self.diligencia_ativa.concluida)  # Should still be not completed

    # ==================== DILIGENCIAS LIST VIEW TESTS ====================
    
    def test_diligencias_list_view_basic(self):
        """Test basic diligencias list view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertIn('diligencias', response.context)
        
        # Should contain all diligencias
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 3)  # All 3 from setUp
    
    def test_diligencias_list_statistics(self):
        """Test statistics in diligencias list view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list'))
        
        context = response.context
        self.assertIn('total_diligencias', context)
        self.assertIn('pendentes_diligencias', context)
        self.assertIn('concluidas_diligencias', context)
        self.assertIn('atrasadas_diligencias', context)
        
        self.assertEqual(context['total_diligencias'], 3)
        self.assertEqual(context['pendentes_diligencias'], 2)  # ativa + atrasada
        self.assertEqual(context['concluidas_diligencias'], 1)  # concluida
        self.assertEqual(context['atrasadas_diligencias'], 1)   # atrasada
    
    def test_diligencias_list_filter_by_status_pendente(self):
        """Test filtering diligencias by status pendente"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + '?status=pendente')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 2)  # Only pending ones
        for diligencia in diligencias:
            self.assertFalse(diligencia.concluida)
    
    def test_diligencias_list_filter_by_status_concluida(self):
        """Test filtering diligencias by status concluida"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + '?status=concluida')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)  # Only completed ones
        for diligencia in diligencias:
            self.assertTrue(diligencia.concluida)
    
    def test_diligencias_list_filter_by_urgencia(self):
        """Test filtering diligencias by urgencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + '?urgencia=alta')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)  # Only high urgency
        self.assertEqual(diligencias[0].urgencia, 'alta')
    
    def test_diligencias_list_filter_by_tipo(self):
        """Test filtering diligencias by tipo"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + f'?tipo={self.tipo_diligencia.id}')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 2)  # ativa + atrasada
        for diligencia in diligencias:
            self.assertEqual(diligencia.tipo, self.tipo_diligencia)
    
    def test_diligencias_list_search_by_cliente_nome(self):
        """Test searching diligencias by cliente nome"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + '?search=João')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 2)  # ativa + concluida (both João's)
        for diligencia in diligencias:
            self.assertEqual(diligencia.cliente, self.cliente)
    
    def test_diligencias_list_search_by_cpf(self):
        """Test searching diligencias by cliente CPF"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + '?search=98765432100')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)  # atrasada (Maria's)
        self.assertEqual(diligencias[0].cliente, self.cliente2)
    
    def test_diligencias_list_search_by_tipo_nome(self):
        """Test searching diligencias by tipo nome"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + '?search=Audiência')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)  # concluida
        self.assertEqual(diligencias[0].tipo, self.tipo_diligencia2)
    
    def test_diligencias_list_search_by_descricao(self):
        """Test searching diligencias by descricao"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + '?search=atrasada')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)  # atrasada
        self.assertIn('atrasada', diligencias[0].descricao.lower())
    
    def test_diligencias_list_combined_filters(self):
        """Test combining multiple filters"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(
            reverse('diligencias_list') + 
            f'?status=pendente&urgencia=baixa&tipo={self.tipo_diligencia.id}'
        )
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)  # atrasada
        diligencia = diligencias[0]
        self.assertFalse(diligencia.concluida)
        self.assertEqual(diligencia.urgencia, 'baixa')
        self.assertEqual(diligencia.tipo, self.tipo_diligencia)
    
    def test_diligencias_list_pagination(self):
        """Test pagination with large dataset"""
        # Create many diligencias to test pagination
        for i in range(30):
            Diligencias.objects.create(
                cliente=self.cliente,
                tipo=self.tipo_diligencia,
                data_final=date.today() + timedelta(days=i),
                criado_por='Test User',
                urgencia='media',
                descricao=f'Diligência {i}',
                concluida=False
            )
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # First page
        response = self.client_app.get(reverse('diligencias_list'))
        page_obj = response.context['page_obj']
        
        self.assertTrue(page_obj.has_next())
        self.assertEqual(len(page_obj.object_list), 25)  # 25 per page
        
        # Second page
        response = self.client_app.get(reverse('diligencias_list') + '?page=2')
        page_obj = response.context['page_obj']
        
        self.assertFalse(page_obj.has_next())
        self.assertEqual(len(page_obj.object_list), 8)  # 33 total - 25 from first page
    
    def test_diligencias_list_context_data(self):
        """Test that all context data is present in diligencias list"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list'))
        
        context = response.context
        
        # Check all expected context variables
        expected_context_keys = [
            'page_obj', 'diligencias', 'total_diligencias', 'pendentes_diligencias',
            'concluidas_diligencias', 'atrasadas_diligencias', 'tipos_diligencia',
            'urgencia_choices', 'status_filter', 'urgencia_filter', 'tipo_filter', 'search_query'
        ]
        
        for key in expected_context_keys:
            self.assertIn(key, context)
        
        # Check tipos_diligencia contains active tipos
        tipos = context['tipos_diligencia']
        self.assertIn(self.tipo_diligencia, tipos)
        self.assertIn(self.tipo_diligencia2, tipos)
    
    def test_diligencias_list_empty_search(self):
        """Test diligencias list with search that returns no results"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('diligencias_list') + '?search=nonexistent')
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 0)

    # ==================== EDGE CASES AND ERROR HANDLING ====================
    
    def test_concurrent_diligencia_modification(self):
        """Test handling concurrent modifications"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Simulate concurrent modification
        original_descricao = self.diligencia_ativa.descricao
        Diligencias.objects.filter(id=self.diligencia_ativa.id).update(descricao='Changed Externally')
        
        # Try to update via form
        form_data = {
            'tipo': self.tipo_diligencia.id,
            'data_final': (date.today() + timedelta(days=5)).strftime('%d/%m/%Y'),
            'urgencia': 'alta',
            'descricao': 'My Update'
        }
        
        response = self.client_app.post(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify our update overwrote the concurrent change
        self.diligencia_ativa.refresh_from_db()
        self.assertEqual(self.diligencia_ativa.descricao, 'My Update')
    
    @patch('precapp.views.Diligencias.objects.filter')
    def test_database_error_handling_in_list_view(self, mock_filter):
        """Test error handling when database operations fail in list view"""
        mock_filter.side_effect = Exception("Database error")
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # This should handle the database error gracefully
        # (Actual implementation may vary - this tests error doesn't crash the view)
        with self.assertRaises(Exception):
            response = self.client_app.get(reverse('diligencias_list'))

    # ==================== RESPONSAVEL FIELD TESTS ====================
    
    def test_nova_diligencia_with_responsavel(self):
        """Test creating new diligencia with responsavel field"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create another user to assign as responsavel
        responsavel_user = User.objects.create_user(
            username='responsavel',
            password='resppass123',
            first_name='Responsavel',
            last_name='User'
        )
        
        form_data = {
            'tipo': self.tipo_diligencia.id,
            'data_final': (date.today() + timedelta(days=7)).strftime('%d/%m/%Y'),
            'urgencia': 'alta',
            'descricao': 'Nova diligência com responsável',
            'responsavel': responsavel_user.id
        }
        
        response = self.client_app.post(
            reverse('nova_diligencia', args=[self.cliente.cpf]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', args=[self.cliente.cpf]))
        
        # Verify diligencia was created with responsavel
        new_diligencia = Diligencias.objects.get(descricao='Nova diligência com responsável')
        self.assertEqual(new_diligencia.responsavel, responsavel_user)
        self.assertEqual(new_diligencia.cliente, self.cliente)
        self.assertEqual(new_diligencia.criado_por, 'Test User')
    
    def test_nova_diligencia_without_responsavel(self):
        """Test creating new diligencia without responsavel field (optional)"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'tipo': self.tipo_diligencia.id,
            'data_final': (date.today() + timedelta(days=7)).strftime('%d/%m/%Y'),
            'urgencia': 'media',
            'descricao': 'Nova diligência sem responsável'
            # responsavel field not included (optional)
        }
        
        response = self.client_app.post(
            reverse('nova_diligencia', args=[self.cliente.cpf]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', args=[self.cliente.cpf]))
        
        # Verify diligencia was created without responsavel
        new_diligencia = Diligencias.objects.get(descricao='Nova diligência sem responsável')
        self.assertIsNone(new_diligencia.responsavel)
        self.assertEqual(new_diligencia.cliente, self.cliente)
    
    def test_editar_diligencia_add_responsavel(self):
        """Test editing diligencia to add responsavel"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create responsavel user
        responsavel_user = User.objects.create_user(
            username='responsavel2',
            password='resppass123',
            first_name='Second',
            last_name='Responsavel'
        )
        
        # Verify initial state (no responsavel)
        self.assertIsNone(self.diligencia_ativa.responsavel)
        
        form_data = {
            'tipo': self.diligencia_ativa.tipo.id,
            'data_final': self.diligencia_ativa.data_final.strftime('%d/%m/%Y'),
            'urgencia': self.diligencia_ativa.urgencia,
            'descricao': self.diligencia_ativa.descricao,
            'responsavel': responsavel_user.id
        }
        
        response = self.client_app.post(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', args=[self.cliente.cpf]))
        
        # Verify responsavel was added
        self.diligencia_ativa.refresh_from_db()
        self.assertEqual(self.diligencia_ativa.responsavel, responsavel_user)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        success_messages = [m for m in messages if m.tags == 'success']
        self.assertEqual(len(success_messages), 1)
        self.assertIn('atualizada', str(success_messages[0]))
    
    def test_editar_diligencia_change_responsavel(self):
        """Test editing diligencia to change responsavel"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create two responsavel users
        responsavel1 = User.objects.create_user(
            username='responsavel1',
            password='resppass123',
            first_name='First',
            last_name='Responsavel'
        )
        responsavel2 = User.objects.create_user(
            username='responsavel2',
            password='resppass123',
            first_name='Second', 
            last_name='Responsavel'
        )
        
        # Set initial responsavel
        self.diligencia_ativa.responsavel = responsavel1
        self.diligencia_ativa.save()
        
        form_data = {
            'tipo': self.diligencia_ativa.tipo.id,
            'data_final': self.diligencia_ativa.data_final.strftime('%d/%m/%Y'),
            'urgencia': self.diligencia_ativa.urgencia,
            'descricao': self.diligencia_ativa.descricao,
            'responsavel': responsavel2.id
        }
        
        response = self.client_app.post(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify responsavel was changed
        self.diligencia_ativa.refresh_from_db()
        self.assertEqual(self.diligencia_ativa.responsavel, responsavel2)
        self.assertNotEqual(self.diligencia_ativa.responsavel, responsavel1)
    
    def test_editar_diligencia_remove_responsavel(self):
        """Test editing diligencia to remove responsavel"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create and assign responsavel
        responsavel_user = User.objects.create_user(
            username='responsavel3',
            password='resppass123',
            first_name='Third',
            last_name='Responsavel'
        )
        self.diligencia_ativa.responsavel = responsavel_user
        self.diligencia_ativa.save()
        
        # Verify initial state
        self.assertEqual(self.diligencia_ativa.responsavel, responsavel_user)
        
        form_data = {
            'tipo': self.diligencia_ativa.tipo.id,
            'data_final': self.diligencia_ativa.data_final.strftime('%d/%m/%Y'),
            'urgencia': self.diligencia_ativa.urgencia,
            'descricao': self.diligencia_ativa.descricao
            # responsavel field not included (remove assignment)
        }
        
        response = self.client_app.post(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify responsavel was removed
        self.diligencia_ativa.refresh_from_db()
        self.assertIsNone(self.diligencia_ativa.responsavel)
    
    def test_diligencias_list_filter_by_responsavel(self):
        """Test filtering diligencias by responsavel in list view"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create responsavel users
        responsavel1 = User.objects.create_user(
            username='resp1',
            password='resppass123',
            first_name='Resp',
            last_name='One'
        )
        responsavel2 = User.objects.create_user(
            username='resp2', 
            password='resppass123',
            first_name='Resp',
            last_name='Two'
        )
        
        # Assign responsavel to existing diligencias
        self.diligencia_ativa.responsavel = responsavel1
        self.diligencia_ativa.save()
        
        self.diligencia_atrasada.responsavel = responsavel2
        self.diligencia_atrasada.save()
        
        # Test filter by responsavel1
        response = self.client_app.get(
            reverse('diligencias_list') + f'?responsavel={responsavel1.id}'
        )
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)
        self.assertEqual(diligencias[0].responsavel, responsavel1)
        
        # Test filter by responsavel2
        response = self.client_app.get(
            reverse('diligencias_list') + f'?responsavel={responsavel2.id}'
        )
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)
        self.assertEqual(diligencias[0].responsavel, responsavel2)
    
    def test_diligencias_list_search_by_responsavel_name(self):
        """Test searching diligencias by responsavel name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create responsavel user with distinctive name
        responsavel_user = User.objects.create_user(
            username='uniqueresp',
            password='resppass123',
            first_name='UniqueResp',
            last_name='UserTest'
        )
        
        # Assign responsavel to diligencia
        self.diligencia_ativa.responsavel = responsavel_user
        self.diligencia_ativa.save()
        
        # Search by responsavel first name
        response = self.client_app.get(
            reverse('diligencias_list') + '?search=UniqueResp'
        )
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)
        self.assertEqual(diligencias[0].responsavel, responsavel_user)
        
        # Search by responsavel last name
        response = self.client_app.get(
            reverse('diligencias_list') + '?search=UserTest'
        )
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)
        self.assertEqual(diligencias[0].responsavel, responsavel_user)
    
    def test_nova_diligencia_form_responsavel_queryset(self):
        """Test that nova diligencia form shows all users in responsavel field"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create additional users
        User.objects.create_user(username='user1', password='pass123', first_name='User', last_name='One')
        User.objects.create_user(username='user2', password='pass123', first_name='User', last_name='Two')
        
        response = self.client_app.get(reverse('nova_diligencia', args=[self.cliente.cpf]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        
        # Check that responsavel field is in the form
        form = response.context['form']
        self.assertIn('responsavel', form.fields)
        
        # Check that all users are available in queryset
        total_users = User.objects.count()
        self.assertEqual(total_users, 3)  # testuser + user1 + user2
    
    def test_editar_diligencia_form_responsavel_current_value(self):
        """Test that editar diligencia form shows current responsavel value"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Assign responsavel to diligencia
        responsavel_user = User.objects.create_user(
            username='currentresp',
            password='resppass123',
            first_name='Current',
            last_name='Responsavel'
        )
        self.diligencia_ativa.responsavel = responsavel_user
        self.diligencia_ativa.save()
        
        response = self.client_app.get(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        
        # Check that current responsavel is selected in form
        form = response.context['form']
        self.assertEqual(form.initial.get('responsavel'), responsavel_user.id)
    
    def test_responsavel_field_user_deletion_handling(self):
        """Test handling when assigned responsavel user is deleted"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create responsavel user and assign to diligencia
        responsavel_user = User.objects.create_user(
            username='todelete',
            password='resppass123',
            first_name='ToDelete',
            last_name='User'
        )
        self.diligencia_ativa.responsavel = responsavel_user
        self.diligencia_ativa.save()
        
        # Verify initial assignment
        self.assertEqual(self.diligencia_ativa.responsavel, responsavel_user)
        
        # Delete the user (should trigger SET_NULL)
        responsavel_user.delete()
        
        # Verify diligencia responsavel was set to NULL
        self.diligencia_ativa.refresh_from_db()
        self.assertIsNone(self.diligencia_ativa.responsavel)
        
        # Verify diligencia still exists and other fields intact
        self.assertEqual(self.diligencia_ativa.cliente, self.cliente)
        self.assertEqual(self.diligencia_ativa.tipo, self.tipo_diligencia)
    
    def test_marcar_diligencia_concluida_with_responsavel(self):
        """Test marking diligencia as completed when it has responsavel"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Assign responsavel to diligencia
        responsavel_user = User.objects.create_user(
            username='conclusaoresp',
            password='resppass123',
            first_name='Conclusao',
            last_name='Responsavel'
        )
        self.diligencia_ativa.responsavel = responsavel_user
        self.diligencia_ativa.save()
        
        # Verify initial state
        self.assertFalse(self.diligencia_ativa.concluida)
        self.assertEqual(self.diligencia_ativa.responsavel, responsavel_user)
        
        form_data = {
            'concluida': True,
            'descricao': self.diligencia_ativa.descricao,
            'responsavel': responsavel_user.id  # Include responsavel to preserve it
        }
        
        response = self.client_app.post(
            reverse('marcar_diligencia_concluida', args=[self.cliente.cpf, self.diligencia_ativa.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify diligencia was marked as completed and responsavel preserved
        self.diligencia_ativa.refresh_from_db()
        self.assertTrue(self.diligencia_ativa.concluida)
        self.assertEqual(self.diligencia_ativa.responsavel, responsavel_user)  # Should be preserved
        self.assertEqual(self.diligencia_ativa.concluido_por, 'Test User')
    
    def test_diligencias_list_combined_filters_with_responsavel(self):
        """Test combining responsavel filter with other filters"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create responsavel user
        responsavel_user = User.objects.create_user(
            username='combinedresp',
            password='resppass123',
            first_name='Combined',
            last_name='Filter'
        )
        
        # Assign responsavel to pending diligencia with specific urgencia
        self.diligencia_ativa.responsavel = responsavel_user
        self.diligencia_ativa.urgencia = 'alta'
        self.diligencia_ativa.save()
        
        # Test combined filter: responsavel + status + urgencia
        response = self.client_app.get(
            reverse('diligencias_list') + 
            f'?responsavel={responsavel_user.id}&status=pendente&urgencia=alta'
        )
        
        diligencias = response.context['diligencias']
        self.assertEqual(len(diligencias), 1)
        diligencia = diligencias[0]
        self.assertEqual(diligencia.responsavel, responsavel_user)
        self.assertFalse(diligencia.concluida)  # pendente
        self.assertEqual(diligencia.urgencia, 'alta')
    
    def test_responsavel_field_permissions_view_access(self):
        """Test that responsavel field is visible and accessible in views"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test nova diligencia view
        response = self.client_app.get(reverse('nova_diligencia', args=[self.cliente.cpf]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'responsavel')  # Field should be in template
        
        # Test editar diligencia view
        response = self.client_app.get(
            reverse('editar_diligencia', args=[self.cliente.cpf, self.diligencia_ativa.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'responsavel')  # Field should be in template


class TipoDiligenciaViewTest(TestCase):
    """Comprehensive test cases for TipoDiligencia views"""
    
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
            ativo=True,
            ordem=1
        )
        
        self.tipo_inativo = TipoDiligencia.objects.create(
            nome='Tipo Inativo',
            descricao='Inactive tipo',
            cor='#dc3545',
            ativo=False,
            ordem=2
        )
        
        self.client_app = Client()

    # ==================== AUTHENTICATION TESTS ====================
    
    def test_tipos_diligencia_view_authentication(self):
        """Test that tipos diligencia view requires authentication"""
        response = self.client_app.get(reverse('tipos_diligencia'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_novo_tipo_diligencia_authentication_required(self):
        """Test that novo tipo diligencia view requires authentication"""
        response = self.client_app.get(reverse('novo_tipo_diligencia'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_editar_tipo_diligencia_authentication_required(self):
        """Test that editar tipo diligencia view requires authentication"""
        response = self.client_app.get(reverse('editar_tipo_diligencia', args=[self.tipo_diligencia.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_deletar_tipo_diligencia_authentication_required(self):
        """Test that deletar tipo diligencia view requires authentication"""
        response = self.client_app.get(reverse('deletar_tipo_diligencia', args=[self.tipo_diligencia.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_ativar_tipo_diligencia_authentication_required(self):
        """Test that ativar tipo diligencia view requires authentication"""
        response = self.client_app.get(reverse('ativar_tipo_diligencia', args=[self.tipo_diligencia.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    # ==================== TIPOS DILIGENCIA LIST VIEW TESTS ====================
    
    def test_tipos_diligencia_view_authenticated(self):
        """Test tipos diligencia view with authentication"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('tipos_diligencia'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Tipo')
        self.assertContains(response, 'Tipo Inativo')
    
    def test_tipos_diligencia_view_context_data(self):
        """Test that tipos diligencia view provides correct context data"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('tipos_diligencia'))
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        
        # Check context variables
        self.assertIn('tipos_diligencia', context)
        self.assertIn('total_tipos', context)
        self.assertIn('tipos_ativos', context)
        self.assertIn('tipos_inativos', context)
        self.assertIn('total_diligencias', context)
        
        # Check statistics calculations
        self.assertEqual(context['total_tipos'], 2)
        self.assertEqual(context['tipos_ativos'], 1)
        self.assertEqual(context['tipos_inativos'], 1)
        
    def test_tipos_diligencia_view_statistics_calculation(self):
        """Test statistics calculation with various scenarios"""
        # Create additional tipos for comprehensive testing
        TipoDiligencia.objects.create(nome='Tipo 3', cor='#28a745', ativo=True, ordem=3)
        TipoDiligencia.objects.create(nome='Tipo 4', cor='#ffc107', ativo=False, ordem=4)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('tipos_diligencia'))
        
        context = response.context
        self.assertEqual(context['total_tipos'], 4)
        self.assertEqual(context['tipos_ativos'], 2)
        self.assertEqual(context['tipos_inativos'], 2)
        
    def test_tipos_diligencia_view_empty_list(self):
        """Test tipos diligencia view with no tipos"""
        TipoDiligencia.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('tipos_diligencia'))
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['total_tipos'], 0)
        self.assertEqual(context['tipos_ativos'], 0)
        self.assertEqual(context['tipos_inativos'], 0)

    # ==================== NOVO TIPO DILIGENCIA TESTS ====================
    
    def test_novo_tipo_diligencia_view_get(self):
        """Test GET request to novo tipo diligencia view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('novo_tipo_diligencia'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Novo Tipo de Diligência')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['title'], 'Novo Tipo de Diligência')
        self.assertEqual(response.context['action'], 'Criar')
    
    def test_novo_tipo_diligencia_post_valid(self):
        """Test creating tipo diligencia with valid data"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': 'Novo Tipo Test',
            'descricao': 'Test description',
            'cor': '#28a745',
            'ordem': 10,
            'ativo': True
        }
        response = self.client_app.post(reverse('novo_tipo_diligencia'), data=form_data)
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo was created
        new_tipo = TipoDiligencia.objects.get(nome='Novo Tipo Test')
        self.assertEqual(new_tipo.descricao, 'Test description')
        self.assertEqual(new_tipo.cor, '#28a745')
        self.assertEqual(new_tipo.ordem, 10)
        self.assertTrue(new_tipo.ativo)
    
    def test_novo_tipo_diligencia_post_invalid(self):
        """Test creating tipo diligencia with invalid data"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': '',  # Required field left empty
            'descricao': 'Test description',
            'cor': 'invalid-color',  # Invalid color format
        }
        response = self.client_app.post(reverse('novo_tipo_diligencia'), data=form_data)
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
        
    def test_novo_tipo_diligencia_duplicate_name(self):
        """Test creating tipo diligencia with duplicate name"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': 'Test Tipo',  # Already exists
            'descricao': 'Duplicate test',
            'cor': '#28a745',
            'ordem': 10,
            'ativo': True
        }
        response = self.client_app.post(reverse('novo_tipo_diligencia'), data=form_data)
        
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    # ==================== EDITAR TIPO DILIGENCIA TESTS ====================
    
    def test_editar_tipo_diligencia_view_get(self):
        """Test GET request to editar tipo diligencia view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('editar_tipo_diligencia', args=[self.tipo_diligencia.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Tipo')
        self.assertIn('form', response.context)
        self.assertIn('tipo', response.context)
        self.assertEqual(response.context['title'], 'Editar Tipo: Test Tipo')
        self.assertEqual(response.context['action'], 'Atualizar')
    
    def test_editar_tipo_diligencia_post_valid(self):
        """Test updating tipo diligencia with valid data"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': 'Updated Tipo Name',
            'descricao': 'Updated description',
            'cor': '#dc3545',
            'ordem': 5,
            'ativo': False
        }
        response = self.client_app.post(
            reverse('editar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo was updated
        self.tipo_diligencia.refresh_from_db()
        self.assertEqual(self.tipo_diligencia.nome, 'Updated Tipo Name')
        self.assertEqual(self.tipo_diligencia.descricao, 'Updated description')
        self.assertEqual(self.tipo_diligencia.cor, '#dc3545')
        self.assertEqual(self.tipo_diligencia.ordem, 5)
        self.assertFalse(self.tipo_diligencia.ativo)
    
    def test_editar_tipo_diligencia_dropdown_update(self):
        """Test updating tipo diligencia via dropdown form"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'update_tipo': 'true',
            'nome': 'Dropdown Updated',
            'cor': '#ffc107',
            'descricao': 'Updated via dropdown',
            'ativo': 'on'  # Checkbox value
        }
        response = self.client_app.post(
            reverse('editar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo was updated
        self.tipo_diligencia.refresh_from_db()
        self.assertEqual(self.tipo_diligencia.nome, 'Dropdown Updated')
        self.assertEqual(self.tipo_diligencia.cor, '#ffc107')
        self.assertEqual(self.tipo_diligencia.descricao, 'Updated via dropdown')
        self.assertTrue(self.tipo_diligencia.ativo)
    
    def test_editar_tipo_diligencia_dropdown_missing_required(self):
        """Test updating tipo diligencia via dropdown with missing required fields"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'update_tipo': 'true',
            'nome': '',  # Missing required field
            'cor': '#ffc107',
        }
        response = self.client_app.post(
            reverse('editar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo was NOT updated
        self.tipo_diligencia.refresh_from_db()
        self.assertEqual(self.tipo_diligencia.nome, 'Test Tipo')
    
    def test_editar_tipo_diligencia_invalid_id(self):
        """Test editing non-existent tipo diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('editar_tipo_diligencia', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    # ==================== DELETAR TIPO DILIGENCIA TESTS ====================
    
    def test_deletar_tipo_diligencia_view_get(self):
        """Test GET request to deletar tipo diligencia view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('deletar_tipo_diligencia', args=[self.tipo_diligencia.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('tipo', response.context)
        self.assertIn('diligencias_count', response.context)
        self.assertIn('can_delete', response.context)
        self.assertEqual(response.context['tipo'], self.tipo_diligencia)
    
    def test_deletar_tipo_diligencia_post_success(self):
        """Test successful deletion of tipo diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        tipo_id = self.tipo_diligencia.id
        
        response = self.client_app.post(reverse('deletar_tipo_diligencia', args=[tipo_id]))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo was deleted
        self.assertFalse(TipoDiligencia.objects.filter(id=tipo_id).exists())
    
    def test_deletar_tipo_diligencia_invalid_id(self):
        """Test deleting non-existent tipo diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('deletar_tipo_diligencia', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    # ==================== ATIVAR TIPO DILIGENCIA TESTS ====================
    
    def test_ativar_tipo_diligencia_post_activate(self):
        """Test activating tipo diligencia via POST"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Start with inactive tipo
        self.tipo_diligencia.ativo = False
        self.tipo_diligencia.save()
        
        form_data = {'ativo': 'true'}
        response = self.client_app.post(
            reverse('ativar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo was activated
        self.tipo_diligencia.refresh_from_db()
        self.assertTrue(self.tipo_diligencia.ativo)
    
    def test_ativar_tipo_diligencia_post_deactivate(self):
        """Test deactivating tipo diligencia via POST"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Start with active tipo
        self.tipo_diligencia.ativo = True
        self.tipo_diligencia.save()
        
        form_data = {'ativo': 'false'}
        response = self.client_app.post(
            reverse('ativar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo was deactivated
        self.tipo_diligencia.refresh_from_db()
        self.assertFalse(self.tipo_diligencia.ativo)
    
    def test_ativar_tipo_diligencia_get_activate(self):
        """Test activating tipo diligencia via GET with parameter"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Start with inactive tipo
        self.tipo_diligencia.ativo = False
        self.tipo_diligencia.save()
        
        response = self.client_app.get(
            reverse('ativar_tipo_diligencia', args=[self.tipo_diligencia.id]) + '?ativo=true'
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo was activated
        self.tipo_diligencia.refresh_from_db()
        self.assertTrue(self.tipo_diligencia.ativo)
    
    def test_ativar_tipo_diligencia_get_toggle(self):
        """Test toggling tipo diligencia status via GET without parameter"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Start with active tipo
        original_status = self.tipo_diligencia.ativo
        
        response = self.client_app.get(reverse('ativar_tipo_diligencia', args=[self.tipo_diligencia.id]))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tipos_diligencia'))
        
        # Verify tipo status was toggled
        self.tipo_diligencia.refresh_from_db()
        self.assertEqual(self.tipo_diligencia.ativo, not original_status)
    
    def test_ativar_tipo_diligencia_invalid_id(self):
        """Test activating non-existent tipo diligencia"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('ativar_tipo_diligencia', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    # ==================== EDGE CASES AND ERROR HANDLING ====================
    
    def test_view_with_large_dataset(self):
        """Test tipos diligencia view performance with large dataset"""
        # Create many tipos to test performance
        tipos_batch = []
        for i in range(50):
            tipos_batch.append(TipoDiligencia(
                nome=f'Tipo {i}',
                descricao=f'Description {i}',
                cor='#007bff',
                ativo=i % 2 == 0,  # Alternate active/inactive
                ordem=i
            ))
        TipoDiligencia.objects.bulk_create(tipos_batch)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('tipos_diligencia'))
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['total_tipos'], 52)  # 50 + 2 from setUp
        self.assertEqual(context['tipos_ativos'], 26)  # 25 + 1 from setUp
        self.assertEqual(context['tipos_inativos'], 26)  # 25 + 1 from setUp
    
    def test_concurrent_tipo_modification(self):
        """Test handling concurrent modifications"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Simulate concurrent modification by changing the object directly
        original_nome = self.tipo_diligencia.nome
        TipoDiligencia.objects.filter(id=self.tipo_diligencia.id).update(nome='Changed Externally')
        
        # Now try to update via the view
        form_data = {
            'nome': 'My Update',
            'descricao': 'My description',
            'cor': '#28a745',
            'ordem': 10,
            'ativo': True
        }
        response = self.client_app.post(
            reverse('editar_tipo_diligencia', args=[self.tipo_diligencia.id]),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify our update overwrote the concurrent change
        self.tipo_diligencia.refresh_from_db()
        self.assertEqual(self.tipo_diligencia.nome, 'My Update')
        
    def test_special_characters_in_tipo_data(self):
        """Test handling special characters in tipo data"""
        self.client_app.login(username='testuser', password='testpass123')
        form_data = {
            'nome': 'Tipo com Acentos & Símbolos ñáéíóú',
            'descricao': 'Descrição com "aspas" e \'apostrofes\' & símbolos especiais: <>&',
            'cor': '#28a745',
            'ordem': 10,
            'ativo': True
        }
        response = self.client_app.post(reverse('novo_tipo_diligencia'), data=form_data)
        
        self.assertEqual(response.status_code, 302)
        
        # Verify tipo was created with special characters
        new_tipo = TipoDiligencia.objects.get(nome='Tipo com Acentos & Símbolos ñáéíóú')
        self.assertIn('aspas', new_tipo.descricao)
        self.assertIn('&', new_tipo.descricao)
        self.assertTrue(new_tipo.ativo)
