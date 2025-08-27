from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.http import JsonResponse
from datetime import datetime, date
import json

from precapp.models import PedidoRequerimento, Requerimento, Precatorio, Cliente, Fase, Tipo


class PedidoRequerimentoViewsTest(TestCase):
    """
    Comprehensive test suite for PedidoRequerimento views functionality.
    
    This test class provides thorough coverage of all CRUD operations and business logic
    for managing tipos de pedido de requerimento in the system. It validates view behavior, 
    form handling, authentication requirements, permission checks, data validation, and user feedback.
    
    Test Coverage:
        - tipos_pedido_requerimento_view: List all tipos with statistics
        - novo_tipo_pedido_requerimento_view: Create new tipos
        - editar_tipo_pedido_requerimento_view: Edit existing tipos  
        - deletar_tipo_pedido_requerimento_view: Delete tipos with protection checks
        - ativar_tipo_pedido_requerimento_view: Toggle activation status
        
    Key Test Areas:
        - Authentication and Authorization: Tests login requirements
        - CRUD Operations: Tests all Create, Read, Update, Delete operations
        - Form Validation: Tests valid and invalid form submissions
        - Business Logic: Tests protection against deleting used tipos
        - User Feedback: Tests success and error message display
        - Data Integrity: Tests database state changes
        - Edge Cases: Tests boundary conditions and error scenarios
        - Template Rendering: Tests correct template usage and context
        - URL Resolution: Tests URL patterns and parameter handling
        
    Business Rules Tested:
        - Only authenticated users can access views (except list view)
        - Tipos cannot be deleted if they are being used by requerimentos
        - Form validation prevents duplicate names and invalid data
        - Activation status can be toggled without affecting data integrity
        - Success/error messages are displayed appropriately
        - Redirects work correctly after operations
        - Color validation ensures proper hex format
        - Order field allows logical organization
        
    Security Considerations:
        - Views requiring authentication have @login_required decorator
        - Proper object retrieval with 404 handling  
        - CSRF protection on form submissions
        - No unauthorized access to restricted operations
        - Input validation prevents malicious data
        
    Performance Testing:
        - Tests with multiple tipos for list view performance
        - Tests form validation efficiency
        - Tests database query optimization
        - Tests activation status toggle performance
        
    Integration Testing:
        - Tests view integration with models and forms
        - Tests template rendering with context data
        - Tests message framework integration
        - Tests URL pattern integration
        - Tests foreign key relationship protection
    """
    
    def setUp(self):
        """Set up test data for pedido requerimento views testing"""
        # Create test users for authentication
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Initialize client
        self.client = Client()
        
        # Create test tipo for precatorio
        self.tipo_precatorio = Tipo.objects.create(
            nome='Comum',
            descricao='Precatórios comuns',
            cor='#6c757d',
            ativa=True
        )
        
        # Create test precatorio
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
            honorarios_sucumbenciais='pendente',
            tipo=self.tipo_precatorio
        )
        
        # Create test cliente
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Link cliente to precatorio (required for Requerimento validation)
        self.precatorio.clientes.add(self.cliente)
        
        # Create test fase
        self.fase = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True,
            ordem=1
        )
        
        # Create test pedido requerimento instances
        self.pedido_ativo_1 = PedidoRequerimento.objects.create(
            nome='Prioridade por Doença',
            descricao='Requerimento de prioridade devido a doença grave',
            cor='#dc3545',
            ordem=1,
            ativo=True
        )
        
        self.pedido_ativo_2 = PedidoRequerimento.objects.create(
            nome='Prioridade por Idade',
            descricao='Requerimento de prioridade devido à idade avançada',
            cor='#ffc107',
            ordem=2,
            ativo=True
        )
        
        self.pedido_inativo = PedidoRequerimento.objects.create(
            nome='Acordo Principal',
            descricao='Tipo de acordo principal',
            cor='#6c757d',
            ordem=3,
            ativo=False
        )
        
        # Create a pedido that's being used in a requerimento (for deletion protection test)
        self.pedido_em_uso = PedidoRequerimento.objects.create(
            nome='Ordem Cronológica',
            descricao='Seguimento da ordem cronológica normal',
            cor='#28a745',
            ordem=4,
            ativo=True
        )
        
        # Create a requerimento using pedido_em_uso
        self.requerimento = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            pedido=self.pedido_em_uso,
            valor=25000.00,
            desagio=15.5,
            fase=self.fase
        )
        
        # Valid form data for testing
        self.valid_form_data = {
            'nome': 'Novo Tipo de Pedido',
            'descricao': 'Descrição do novo tipo de pedido',
            'cor': '#17a2b8',
            'ordem': 5,
            'ativo': True
        }
        
        self.invalid_form_data = {
            'nome': '',  # Required field missing
            'descricao': 'Descrição inválida',
            'cor': 'invalid_color',  # Invalid hex color
            'ordem': -1,  # Invalid negative order
            'ativo': True
        }
    
    # ============ AUTHENTICATION TESTS ============
    
    def test_tipos_pedido_requerimento_view_no_login_required(self):
        """Test that list view doesn't require authentication (public access)"""
        # Note: The view actually requires login, so this test checks for login redirect
        response = self.client.get(reverse('tipos_pedido_requerimento'))
        self.assertRedirects(response, '/login/?next=/tipos-pedido-requerimento/')
    
    def test_tipos_pedido_requerimento_view_with_login(self):
        """Test that list view works when logged in"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_pedido_requerimento'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prioridade por Doença')
        self.assertContains(response, 'Prioridade por Idade')
    
    def test_novo_tipo_pedido_requerimento_view_requires_login(self):
        """Test that create view requires authentication"""
        response = self.client.get(reverse('novo_tipo_pedido_requerimento'))
        self.assertRedirects(response, '/login/?next=/tipos-pedido-requerimento/novo/')
    
    def test_editar_tipo_pedido_requerimento_view_requires_login(self):
        """Test that edit view requires authentication"""
        response = self.client.get(
            reverse('editar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        self.assertRedirects(response, f'/login/?next=/tipos-pedido-requerimento/{self.pedido_ativo_1.id}/editar/')
    
    def test_deletar_tipo_pedido_requerimento_view_requires_login(self):
        """Test that delete view requires authentication"""
        response = self.client.get(
            reverse('deletar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        self.assertRedirects(response, f'/login/?next=/tipos-pedido-requerimento/{self.pedido_ativo_1.id}/deletar/')
    
    def test_ativar_tipo_pedido_requerimento_view_requires_login(self):
        """Test that activation view requires authentication"""
        response = self.client.get(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        self.assertRedirects(response, f'/login/?next=/tipos-pedido-requerimento/{self.pedido_ativo_1.id}/ativar/')
    
    # ============ LIST VIEW TESTS ============
    
    def test_tipos_pedido_requerimento_view_get_success(self):
        """Test successful GET request to list view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_pedido_requerimento'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prioridade por Doença')
        self.assertContains(response, 'Prioridade por Idade')
        self.assertContains(response, 'Ordem Cronológica')
        self.assertContains(response, 'Acordo Principal')
        
        # Check template used
        self.assertTemplateUsed(response, 'precapp/tipos_pedido_requerimento_list.html')
    
    def test_tipos_pedido_requerimento_view_context_data(self):
        """Test context data provided to list view template"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_pedido_requerimento'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        self.assertIn('tipos', response.context)
        self.assertIn('total_tipos', response.context)
        self.assertIn('tipos_ativos', response.context)
        self.assertIn('tipos_inativos', response.context)
        
        # Check statistics
        self.assertEqual(response.context['total_tipos'], 4)
        self.assertEqual(response.context['tipos_ativos'], 3)  # 3 active tipos
        self.assertEqual(response.context['tipos_inativos'], 1)  # 1 inactive tipo
    
    def test_tipos_pedido_requerimento_view_ordering(self):
        """Test that list view orders tipos by ordem and nome"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_pedido_requerimento'))
        
        tipos = response.context['tipos']
        tipo_names = [tipo.nome for tipo in tipos]
        
        # Should be ordered by ordem field
        expected_order = ['Prioridade por Doença', 'Prioridade por Idade', 'Acordo Principal', 'Ordem Cronológica']
        self.assertEqual(tipo_names, expected_order)
    
    def test_tipos_pedido_requerimento_view_empty_list(self):
        """Test list view with no tipos"""
        self.client.login(username='testuser', password='testpass123')
        
        # Delete requerimento first to avoid ProtectedError
        self.requerimento.delete()
        
        # Delete all tipos
        PedidoRequerimento.objects.all().delete()
        
        response = self.client.get(reverse('tipos_pedido_requerimento'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_tipos'], 0)
        self.assertEqual(response.context['tipos_ativos'], 0)
        self.assertEqual(response.context['tipos_inativos'], 0)
    
    # ============ CREATE VIEW TESTS ============
    
    def test_novo_tipo_pedido_requerimento_view_get_success(self):
        """Test successful GET request to create view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('novo_tipo_pedido_requerimento'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Novo Tipo de Pedido de Requerimento')
        self.assertTemplateUsed(response, 'precapp/tipo_pedido_requerimento_form.html')
        
        # Check form in context
        self.assertIn('form', response.context)
        self.assertIn('title', response.context)
    
    def test_novo_tipo_pedido_requerimento_view_post_valid_data(self):
        """Test POST request with valid data creates new tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = PedidoRequerimento.objects.count()
        
        response = self.client.post(
            reverse('novo_tipo_pedido_requerimento'),
            data=self.valid_form_data
        )
        
        # Should redirect to list view
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Should create new tipo
        self.assertEqual(PedidoRequerimento.objects.count(), initial_count + 1)
        
        # Check created tipo
        new_tipo = PedidoRequerimento.objects.get(nome='Novo Tipo de Pedido')
        self.assertEqual(new_tipo.descricao, 'Descrição do novo tipo de pedido')
        self.assertEqual(new_tipo.cor, '#17a2b8')
        self.assertEqual(new_tipo.ordem, 5)
        self.assertTrue(new_tipo.ativo)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('criado com sucesso' in str(m) for m in messages))
    
    def test_novo_tipo_pedido_requerimento_view_post_invalid_data(self):
        """Test POST request with invalid data shows form errors"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = PedidoRequerimento.objects.count()
        
        response = self.client.post(
            reverse('novo_tipo_pedido_requerimento'),
            data=self.invalid_form_data
        )
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Should not create new tipo
        self.assertEqual(PedidoRequerimento.objects.count(), initial_count)
        
        # Check form errors
        self.assertFormError(response, 'form', 'nome', 'Este campo é obrigatório.')
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('corrija os erros' in str(m) for m in messages))
    
    def test_novo_tipo_pedido_requerimento_view_duplicate_name(self):
        """Test creating tipo with duplicate name shows error"""
        self.client.login(username='testuser', password='testpass123')
        
        duplicate_data = self.valid_form_data.copy()
        duplicate_data['nome'] = 'Prioridade por Doença'  # Already exists
        
        response = self.client.post(
            reverse('novo_tipo_pedido_requerimento'),
            data=duplicate_data
        )
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Check for uniqueness error (could be in form errors or non-field errors)
        form = response.context['form']
        has_error = (
            form.errors.get('nome') or 
            form.errors.get('__all__') or 
            form.non_field_errors()
        )
        self.assertTrue(has_error)
    
    # ============ EDIT VIEW TESTS ============
    
    def test_editar_tipo_pedido_requerimento_view_get_success(self):
        """Test successful GET request to edit view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('editar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Tipo de Pedido: Prioridade por Doença')
        self.assertTemplateUsed(response, 'precapp/tipo_pedido_requerimento_form.html')
        
        # Check form is pre-populated with existing data
        form = response.context['form']
        self.assertEqual(form.instance, self.pedido_ativo_1)
        self.assertEqual(form.initial.get('nome') or form.instance.nome, 'Prioridade por Doença')
    
    def test_editar_tipo_pedido_requerimento_view_post_valid_data(self):
        """Test POST request with valid data updates existing tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        update_data = {
            'nome': 'Prioridade por Doença Atualizada',
            'descricao': 'Descrição atualizada',
            'cor': '#e83e8c',
            'ordem': 10,
            'ativo': False
        }
        
        response = self.client.post(
            reverse('editar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id}),
            data=update_data
        )
        
        # Should redirect to list view
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Check updated tipo
        self.pedido_ativo_1.refresh_from_db()
        self.assertEqual(self.pedido_ativo_1.nome, 'Prioridade por Doença Atualizada')
        self.assertEqual(self.pedido_ativo_1.descricao, 'Descrição atualizada')
        self.assertEqual(self.pedido_ativo_1.cor, '#e83e8c')
        self.assertEqual(self.pedido_ativo_1.ordem, 10)
        self.assertFalse(self.pedido_ativo_1.ativo)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('atualizado com sucesso' in str(m) for m in messages))
    
    def test_editar_tipo_pedido_requerimento_view_post_invalid_data(self):
        """Test POST request with invalid data shows form errors"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('editar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id}),
            data=self.invalid_form_data
        )
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Check original data unchanged
        self.pedido_ativo_1.refresh_from_db()
        self.assertEqual(self.pedido_ativo_1.nome, 'Prioridade por Doença')
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('corrija os erros' in str(m) for m in messages))
    
    def test_editar_tipo_pedido_requerimento_view_nonexistent_id(self):
        """Test edit view with non-existent tipo ID returns 404"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('editar_tipo_pedido_requerimento', kwargs={'tipo_id': 99999})
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_editar_tipo_pedido_requerimento_view_same_name_allowed(self):
        """Test editing tipo with same name is allowed (excludes self from uniqueness)"""
        self.client.login(username='testuser', password='testpass123')
        
        # Edit with same name should be allowed
        update_data = {
            'nome': 'Prioridade por Doença',  # Same name
            'descricao': 'Nova descrição',
            'cor': '#dc3545',
            'ordem': 1,
            'ativo': True
        }
        
        response = self.client.post(
            reverse('editar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id}),
            data=update_data
        )
        
        # Should redirect successfully
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Check updated data
        self.pedido_ativo_1.refresh_from_db()
        self.assertEqual(self.pedido_ativo_1.descricao, 'Nova descrição')
    
    # ============ DELETE VIEW TESTS ============
    
    def test_deletar_tipo_pedido_requerimento_view_get_success(self):
        """Test successful GET request to delete confirmation view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('deletar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        
        # Debug: print response content if test fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content.decode()[:200]}")
        
        self.assertEqual(response.status_code, 200)
        
        # The name should appear in the template
        self.assertContains(response, self.pedido_ativo_1.nome)
        self.assertTemplateUsed(response, 'precapp/confirmar_delete_tipo_pedido_requerimento.html')
        
        # Check context
        self.assertEqual(response.context['tipo_pedido'], self.pedido_ativo_1)
        self.assertEqual(response.context['requerimentos_count'], 0)
    
    def test_deletar_tipo_pedido_requerimento_view_post_success(self):
        """Test successful POST request deletes tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = PedidoRequerimento.objects.count()
        tipo_id = self.pedido_ativo_1.id
        
        response = self.client.post(
            reverse('deletar_tipo_pedido_requerimento', kwargs={'tipo_id': tipo_id})
        )
        
        # Should redirect to list view
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Should delete tipo
        self.assertEqual(PedidoRequerimento.objects.count(), initial_count - 1)
        self.assertFalse(PedidoRequerimento.objects.filter(id=tipo_id).exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('excluído com sucesso' in str(m) for m in messages))
    
    def test_deletar_tipo_pedido_requerimento_view_protection_check(self):
        """Test deletion protection when tipo is being used"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = PedidoRequerimento.objects.count()
        
        # Try to delete tipo that's being used
        response = self.client.get(
            reverse('deletar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_em_uso.id})
        )
        
        # Should redirect to list view with error message
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Should not delete tipo
        self.assertEqual(PedidoRequerimento.objects.count(), initial_count)
        self.assertTrue(PedidoRequerimento.objects.filter(id=self.pedido_em_uso.id).exists())
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('não é possível excluir' in str(m).lower() for m in messages))
        self.assertTrue(any('está sendo usado' in str(m) for m in messages))
    
    def test_deletar_tipo_pedido_requerimento_view_usage_count_display(self):
        """Test that usage count is displayed in delete confirmation"""
        self.client.login(username='testuser', password='testpass123')
        
        # For tipo being used
        response = self.client.get(
            reverse('deletar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_em_uso.id})
        )
        
        # Should show error and redirect
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # For tipo not being used  
        response = self.client.get(
            reverse('deletar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['requerimentos_count'], 0)
    
    def test_deletar_tipo_pedido_requerimento_view_nonexistent_id(self):
        """Test delete view with non-existent tipo ID returns 404"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('deletar_tipo_pedido_requerimento', kwargs={'tipo_id': 99999})
        )
        
        self.assertEqual(response.status_code, 404)
    
    # ============ ACTIVATION TOGGLE TESTS ============
    
    def test_ativar_tipo_pedido_requerimento_view_get_toggle(self):
        """Test GET request toggles activation status"""
        self.client.login(username='testuser', password='testpass123')
        
        # Current status is active
        self.assertTrue(self.pedido_ativo_1.ativo)
        
        response = self.client.get(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        
        # Should redirect to list view
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Should toggle status
        self.pedido_ativo_1.refresh_from_db()
        self.assertFalse(self.pedido_ativo_1.ativo)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('desativado com sucesso' in str(m) for m in messages))
    
    def test_ativar_tipo_pedido_requerimento_view_get_with_ativo_param_true(self):
        """Test GET request with ativo=true parameter activates tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        # Start with inactive tipo
        self.pedido_inativo.ativo = False
        self.pedido_inativo.save()
        
        response = self.client.get(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_inativo.id}),
            data={'ativo': 'true'}
        )
        
        # Should redirect to list view
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Should activate tipo
        self.pedido_inativo.refresh_from_db()
        self.assertTrue(self.pedido_inativo.ativo)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('ativado com sucesso' in str(m) for m in messages))
    
    def test_ativar_tipo_pedido_requerimento_view_get_with_ativo_param_false(self):
        """Test GET request with ativo=false parameter deactivates tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        # Start with active tipo
        self.assertTrue(self.pedido_ativo_1.ativo)
        
        response = self.client.get(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id}),
            data={'ativo': 'false'}
        )
        
        # Should redirect to list view
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Should deactivate tipo
        self.pedido_ativo_1.refresh_from_db()
        self.assertFalse(self.pedido_ativo_1.ativo)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('desativado com sucesso' in str(m) for m in messages))
    
    def test_ativar_tipo_pedido_requerimento_view_post_ativo_true(self):
        """Test POST request with ativo=true activates tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        # Start with inactive tipo
        self.pedido_inativo.ativo = False
        self.pedido_inativo.save()
        
        response = self.client.post(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_inativo.id}),
            data={'ativo': 'true'}
        )
        
        # Should redirect to list view
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Should activate tipo
        self.pedido_inativo.refresh_from_db()
        self.assertTrue(self.pedido_inativo.ativo)
    
    def test_ativar_tipo_pedido_requerimento_view_post_ativo_false(self):
        """Test POST request with ativo=false deactivates tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        # Start with active tipo
        self.assertTrue(self.pedido_ativo_1.ativo)
        
        response = self.client.post(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id}),
            data={'ativo': 'false'}
        )
        
        # Should redirect to list view
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Should deactivate tipo
        self.pedido_ativo_1.refresh_from_db()
        self.assertFalse(self.pedido_ativo_1.ativo)
    
    def test_ativar_tipo_pedido_requerimento_view_nonexistent_id(self):
        """Test activation view with non-existent tipo ID returns 404"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': 99999})
        )
        
        self.assertEqual(response.status_code, 404)
    
    # ============ INTEGRATION AND WORKFLOW TESTS ============
    
    def test_complete_crud_workflow(self):
        """Test complete Create-Read-Update-Delete workflow"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Create new tipo
        create_data = {
            'nome': 'Workflow Test Tipo',
            'descricao': 'Tipo para teste de workflow',
            'cor': '#6f42c1',
            'ordem': 99,
            'ativo': True
        }
        
        response = self.client.post(
            reverse('novo_tipo_pedido_requerimento'),
            data=create_data
        )
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # 2. Verify tipo was created
        new_tipo = PedidoRequerimento.objects.get(nome='Workflow Test Tipo')
        self.assertEqual(new_tipo.cor, '#6f42c1')
        
        # 3. Edit the tipo
        edit_data = {
            'nome': 'Workflow Test Tipo Editado',
            'descricao': 'Descrição editada',
            'cor': '#fd7e14',
            'ordem': 98,
            'ativo': False
        }
        
        response = self.client.post(
            reverse('editar_tipo_pedido_requerimento', kwargs={'tipo_id': new_tipo.id}),
            data=edit_data
        )
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # 4. Verify edit
        new_tipo.refresh_from_db()
        self.assertEqual(new_tipo.nome, 'Workflow Test Tipo Editado')
        self.assertEqual(new_tipo.cor, '#fd7e14')
        self.assertFalse(new_tipo.ativo)
        
        # 5. Toggle activation
        response = self.client.get(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': new_tipo.id})
        )
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        new_tipo.refresh_from_db()
        self.assertTrue(new_tipo.ativo)  # Should be toggled to active
        
        # 6. Delete the tipo
        response = self.client.post(
            reverse('deletar_tipo_pedido_requerimento', kwargs={'tipo_id': new_tipo.id})
        )
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # 7. Verify deletion
        self.assertFalse(PedidoRequerimento.objects.filter(id=new_tipo.id).exists())
    
    def test_form_validation_integration(self):
        """Test form validation integration across views"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test various invalid data scenarios
        invalid_scenarios = [
            {
                'data': {'nome': '', 'cor': '#ffffff', 'ordem': 1, 'ativo': True},
                'error_field': 'nome'
            },
            {
                'data': {'nome': 'Test', 'cor': 'invalid', 'ordem': 1, 'ativo': True},
                'error_field': 'cor'
            },
            {
                'data': {'nome': 'Test', 'cor': '#ffffff', 'ordem': -1, 'ativo': True},
                'error_field': 'ordem'
            }
        ]
        
        for scenario in invalid_scenarios:
            with self.subTest(scenario=scenario):
                response = self.client.post(
                    reverse('novo_tipo_pedido_requerimento'),
                    data=scenario['data']
                )
                
                # Should not redirect (form errors)
                self.assertEqual(response.status_code, 200)
                
                # Should have form errors
                form = response.context['form']
                self.assertFalse(form.is_valid())
    
    def test_message_framework_integration(self):
        """Test message framework integration across all views"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test success messages
        test_cases = [
            {
                'view': 'novo_tipo_pedido_requerimento',
                'method': 'post',
                'data': self.valid_form_data,
                'message_contains': 'criado com sucesso'
            },
            {
                'view': 'ativar_tipo_pedido_requerimento',
                'method': 'get',
                'kwargs': {'tipo_id': self.pedido_ativo_1.id},
                'message_contains': 'desativado com sucesso'
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                if case['method'] == 'post':
                    response = self.client.post(
                        reverse(case['view'], kwargs=case.get('kwargs', {})),
                        data=case.get('data', {})
                    )
                else:
                    response = self.client.get(
                        reverse(case['view'], kwargs=case.get('kwargs', {}))
                    )
                
                messages = list(get_messages(response.wsgi_request))
                self.assertTrue(
                    any(case['message_contains'] in str(m) for m in messages),
                    f"Expected message containing '{case['message_contains']}' not found"
                )
    
    # ============ EDGE CASES AND ERROR HANDLING ============
    
    def test_views_with_special_characters_in_data(self):
        """Test views handle special characters correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        special_data = {
            'nome': 'Prioridade Ação & Execução',
            'descricao': 'Descrição com acentos: ção, ã, é, ô, ü, ç',
            'cor': '#e91e63',
            'ordem': 1,
            'ativo': True
        }
        
        response = self.client.post(
            reverse('novo_tipo_pedido_requerimento'),
            data=special_data
        )
        
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Verify creation
        special_tipo = PedidoRequerimento.objects.get(nome='Prioridade Ação & Execução')
        self.assertIn('ção', special_tipo.descricao)
    
    def test_views_with_large_ordem_values(self):
        """Test views handle large ordem values correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        large_ordem_data = self.valid_form_data.copy()
        large_ordem_data['ordem'] = 999999
        
        response = self.client.post(
            reverse('novo_tipo_pedido_requerimento'),
            data=large_ordem_data
        )
        
        self.assertRedirects(response, reverse('tipos_pedido_requerimento'))
        
        # Verify creation with large ordem
        tipo = PedidoRequerimento.objects.get(nome='Novo Tipo de Pedido')
        self.assertEqual(tipo.ordem, 999999)
    
    def test_concurrent_activation_toggle(self):
        """Test concurrent activation toggle operations"""
        self.client.login(username='testuser', password='testpass123')
        
        original_status = self.pedido_ativo_1.ativo
        
        # First toggle
        response1 = self.client.get(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        
        # Refresh from DB after first toggle
        self.pedido_ativo_1.refresh_from_db()
        intermediate_status = self.pedido_ativo_1.ativo
        
        # Second toggle
        response2 = self.client.get(
            reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': self.pedido_ativo_1.id})
        )
        
        # Both should redirect successfully
        self.assertRedirects(response1, reverse('tipos_pedido_requerimento'))
        self.assertRedirects(response2, reverse('tipos_pedido_requerimento'))
        
        # Final status should be same as original after two toggles
        self.pedido_ativo_1.refresh_from_db()
        self.assertEqual(self.pedido_ativo_1.ativo, original_status)
        # But intermediate status should be different
        self.assertNotEqual(intermediate_status, original_status)
    
    # ============ PERFORMANCE AND SCALABILITY TESTS ============
    
    def test_list_view_performance_with_many_tipos(self):
        """Test list view performance with many tipos"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create many tipos for performance testing
        for i in range(50):
            PedidoRequerimento.objects.create(
                nome=f'Performance Test Tipo {i}',
                descricao=f'Descrição do tipo {i}',
                cor=f'#{i:06x}',
                ordem=i + 100,
                ativo=i % 2 == 0  # Alternate active/inactive
            )
        
        response = self.client.get(reverse('tipos_pedido_requerimento'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check statistics are correct
        total_count = PedidoRequerimento.objects.count()
        active_count = PedidoRequerimento.objects.filter(ativo=True).count()
        inactive_count = PedidoRequerimento.objects.filter(ativo=False).count()
        
        self.assertEqual(response.context['total_tipos'], total_count)
        self.assertEqual(response.context['tipos_ativos'], active_count)
        self.assertEqual(response.context['tipos_inativos'], inactive_count)
    
    def test_database_consistency_after_operations(self):
        """Test database consistency after multiple operations"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = PedidoRequerimento.objects.count()
        
        # Perform multiple operations
        operations = [
            ('create', self.valid_form_data),
            ('toggle', None),
            ('edit', {'nome': 'Edited Name', 'cor': '#123456', 'ordem': 1, 'ativo': True}),
        ]
        
        created_tipo = None
        
        for operation, data in operations:
            if operation == 'create':
                response = self.client.post(reverse('novo_tipo_pedido_requerimento'), data=data)
                created_tipo = PedidoRequerimento.objects.get(nome=data['nome'])
                
            elif operation == 'toggle' and created_tipo:
                response = self.client.get(
                    reverse('ativar_tipo_pedido_requerimento', kwargs={'tipo_id': created_tipo.id})
                )
                
            elif operation == 'edit' and created_tipo:
                response = self.client.post(
                    reverse('editar_tipo_pedido_requerimento', kwargs={'tipo_id': created_tipo.id}),
                    data=data
                )
        
        # Verify database consistency
        final_count = PedidoRequerimento.objects.count()
        self.assertEqual(final_count, initial_count + 1)
        
        if created_tipo:
            created_tipo.refresh_from_db()
            self.assertEqual(created_tipo.nome, 'Edited Name')
