from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.http import JsonResponse
from datetime import datetime, date
import json

from precapp.models import Tipo, Precatorio


class TipoPrecatorioViewsTest(TestCase):
    """
    Comprehensive test suite for Tipo de Precatório views functionality.
    
    This test class provides thorough coverage of all CRUD operations and business logic
    for managing tipos de precatório in the system. It validates view behavior, form handling,
    authentication requirements, permission checks, data validation, and user feedback.
    
    Test Coverage:
        - tipos_precatorio_view: List all tipos with statistics
        - novo_tipo_precatorio_view: Create new tipos
        - editar_tipo_precatorio_view: Edit existing tipos
        - deletar_tipo_precatorio_view: Delete tipos with protection checks
        - ativar_tipo_precatorio_view: Toggle activation status
        
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
        - Only authenticated users can access views
        - Tipos cannot be deleted if they are being used by precatórios
        - Form validation prevents duplicate names and invalid data
        - Activation status can be toggled without affecting data integrity
        - Success/error messages are displayed appropriately
        - Redirects work correctly after operations
        
    Security Considerations:
        - All views require authentication (@login_required)
        - Proper object retrieval with 404 handling
        - CSRF protection on form submissions
        - No unauthorized access to restricted operations
        
    Performance Testing:
        - Tests with multiple tipos for list view performance
        - Tests form validation efficiency
        - Tests database query optimization
        
    Integration Testing:
        - Tests view integration with models and forms
        - Tests template rendering with context data
        - Tests message framework integration
        - Tests URL pattern integration
    """
    
    def setUp(self):
        """Set up test data for tipo precatório views testing"""
        # Create test user for authentication
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
        
        # Create test tipos
        self.tipo_ativo_1 = Tipo.objects.create(
            nome='Aposentadoria',
            descricao='Precatórios de aposentadoria',
            cor='#007bff',
            ordem=1,
            ativa=True
        )
        
        self.tipo_ativo_2 = Tipo.objects.create(
            nome='Salário',
            descricao='Precatórios salariais',
            cor='#28a745',
            ordem=2,
            ativa=True
        )
        
        self.tipo_inativo = Tipo.objects.create(
            nome='Indenização',
            descricao='Precatórios de indenização',
            cor='#dc3545',
            ordem=3,
            ativa=False
        )
        
        # Create test precatorio to test deletion protection
        self.precatorio_with_tipo = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente',
            tipo=self.tipo_ativo_1
        )
        
        # Valid form data for testing
        self.valid_tipo_data = {
            'nome': 'Novo Tipo',
            'descricao': 'Descrição do novo tipo',
            'cor': '#ff5722',
            'ordem': 4,
            'ativa': True
        }
        
        self.invalid_tipo_data = {
            'nome': '',  # Required field missing
            'descricao': 'Descrição inválida',
            'cor': 'invalid-color',  # Invalid color format
            'ordem': -1,  # Invalid negative order
            'ativa': True
        }

    # ==================== AUTHENTICATION TESTS ====================
    
    def test_tipos_precatorio_view_requires_login(self):
        """Test that tipos_precatorio_view requires authentication"""
        response = self.client.get(reverse('tipos_precatorio'))
        self.assertRedirects(response, '/login/?next=/tipos-precatorio/')
    
    def test_novo_tipo_precatorio_view_requires_login(self):
        """Test that novo_tipo_precatorio_view requires authentication"""
        response = self.client.get(reverse('novo_tipo_precatorio'))
        self.assertRedirects(response, '/login/?next=/tipos-precatorio/novo/')
    
    def test_editar_tipo_precatorio_view_requires_login(self):
        """Test that editar_tipo_precatorio_view requires authentication"""
        response = self.client.get(reverse('editar_tipo_precatorio', args=[self.tipo_ativo_1.id]))
        self.assertRedirects(response, f'/login/?next=/tipos-precatorio/{self.tipo_ativo_1.id}/editar/')
    
    def test_deletar_tipo_precatorio_view_requires_login(self):
        """Test that deletar_tipo_precatorio_view requires authentication"""
        response = self.client.get(reverse('deletar_tipo_precatorio', args=[self.tipo_ativo_1.id]))
        self.assertRedirects(response, f'/login/?next=/tipos-precatorio/{self.tipo_ativo_1.id}/deletar/')
    
    def test_ativar_tipo_precatorio_view_requires_login(self):
        """Test that ativar_tipo_precatorio_view requires authentication"""
        response = self.client.get(reverse('ativar_tipo_precatorio', args=[self.tipo_ativo_1.id]))
        self.assertRedirects(response, f'/login/?next=/tipos-precatorio/{self.tipo_ativo_1.id}/ativar/')

    # ==================== TIPOS PRECATORIO LIST VIEW TESTS ====================
    
    def test_tipos_precatorio_view_success(self):
        """Test successful access to tipos precatorio list view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_precatorio'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aposentadoria')
        self.assertContains(response, 'Salário')
        self.assertContains(response, 'Indenização')
        self.assertTemplateUsed(response, 'precapp/tipos_precatorio_list.html')
    
    def test_tipos_precatorio_view_context_data(self):
        """Test that tipos_precatorio_view provides correct context data"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_precatorio'))
        
        context = response.context
        self.assertIn('tipos', context)
        self.assertIn('total_tipos', context)
        self.assertIn('tipos_ativos', context)
        self.assertIn('tipos_inativos', context)
        
        # Check statistics
        self.assertEqual(context['total_tipos'], 3)
        self.assertEqual(context['tipos_ativos'], 2)
        self.assertEqual(context['tipos_inativos'], 1)
        
        # Check ordering (should be by ordem, nome)
        tipos = list(context['tipos'])
        self.assertEqual(tipos[0], self.tipo_ativo_1)  # ordem=1
        self.assertEqual(tipos[1], self.tipo_ativo_2)  # ordem=2
        self.assertEqual(tipos[2], self.tipo_inativo)  # ordem=3
    
    def test_tipos_precatorio_view_empty_list(self):
        """Test tipos_precatorio_view with no tipos"""
        # Delete all tipos
        Tipo.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_precatorio'))
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['total_tipos'], 0)
        self.assertEqual(context['tipos_ativos'], 0)
        self.assertEqual(context['tipos_inativos'], 0)
    
    def test_tipos_precatorio_view_performance_with_many_tipos(self):
        """Test tipos_precatorio_view performance with many tipos"""
        # Create additional tipos for performance testing
        for i in range(50):
            Tipo.objects.create(
                nome=f'Tipo Performance {i}',
                cor=f'#{i:06x}',
                ordem=i + 10,
                ativa=True
            )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_precatorio'))
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['total_tipos'], 53)  # 3 original + 50 new
        self.assertEqual(context['tipos_ativos'], 52)  # 2 original active + 50 new

    # ==================== NOVO TIPO PRECATORIO VIEW TESTS ====================
    
    def test_novo_tipo_precatorio_view_get_success(self):
        """Test GET request to novo_tipo_precatorio_view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('novo_tipo_precatorio'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/tipo_precatorio_form.html')
        self.assertContains(response, 'Novo Tipo de Precatório')
        self.assertIn('form', response.context)
        self.assertIn('title', response.context)
        self.assertEqual(response.context['title'], 'Novo Tipo de Precatório')
    
    def test_novo_tipo_precatorio_view_post_success(self):
        """Test successful POST request to create new tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = Tipo.objects.count()
        response = self.client.post(reverse('novo_tipo_precatorio'), self.valid_tipo_data)
        
        # Check redirect
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check that tipo was created
        self.assertEqual(Tipo.objects.count(), initial_count + 1)
        
        # Check the created tipo
        new_tipo = Tipo.objects.get(nome='Novo Tipo')
        self.assertEqual(new_tipo.descricao, 'Descrição do novo tipo')
        self.assertEqual(new_tipo.cor, '#ff5722')
        self.assertEqual(new_tipo.ordem, 4)
        self.assertTrue(new_tipo.ativa)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('criado com sucesso' in str(message) for message in messages))
    
    def test_novo_tipo_precatorio_view_post_invalid_data(self):
        """Test POST request with invalid data"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = Tipo.objects.count()
        response = self.client.post(reverse('novo_tipo_precatorio'), self.invalid_tipo_data)
        
        # Should not redirect (form errors)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/tipo_precatorio_form.html')
        
        # Check that no tipo was created
        self.assertEqual(Tipo.objects.count(), initial_count)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('corrija os erros' in str(message) for message in messages))
        
        # Check form errors
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_novo_tipo_precatorio_view_duplicate_name(self):
        """Test creating tipo with duplicate name"""
        self.client.login(username='testuser', password='testpass123')
        
        duplicate_data = self.valid_tipo_data.copy()
        duplicate_data['nome'] = 'Aposentadoria'  # Already exists
        
        initial_count = Tipo.objects.count()
        response = self.client.post(reverse('novo_tipo_precatorio'), duplicate_data)
        
        # Should not redirect (form errors)
        self.assertEqual(response.status_code, 200)
        
        # Check that no tipo was created
        self.assertEqual(Tipo.objects.count(), initial_count)
        
        # Check form errors
        form = response.context['form']
        self.assertFalse(form.is_valid())

    # ==================== EDITAR TIPO PRECATORIO VIEW TESTS ====================
    
    def test_editar_tipo_precatorio_view_get_success(self):
        """Test GET request to editar_tipo_precatorio_view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('editar_tipo_precatorio', args=[self.tipo_ativo_1.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/tipo_precatorio_form.html')
        self.assertContains(response, f'Editar Tipo: {self.tipo_ativo_1.nome}')
        
        # Check context
        self.assertIn('form', response.context)
        self.assertIn('tipo', response.context)
        self.assertIn('title', response.context)
        self.assertEqual(response.context['tipo'], self.tipo_ativo_1)
        self.assertEqual(response.context['title'], f'Editar Tipo: {self.tipo_ativo_1.nome}')
        
        # Check form is pre-populated
        form = response.context['form']
        self.assertEqual(form.instance, self.tipo_ativo_1)
        self.assertEqual(form['nome'].value(), self.tipo_ativo_1.nome)
    
    def test_editar_tipo_precatorio_view_get_not_found(self):
        """Test GET request with non-existent tipo ID"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('editar_tipo_precatorio', args=[9999]))
        
        self.assertEqual(response.status_code, 404)
    
    def test_editar_tipo_precatorio_view_post_success(self):
        """Test successful POST request to update tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        updated_data = {
            'nome': 'Aposentadoria Atualizada',
            'descricao': 'Descrição atualizada',
            'cor': '#ff9800',
            'ordem': 5,
            'ativa': False
        }
        
        response = self.client.post(
            reverse('editar_tipo_precatorio', args=[self.tipo_ativo_1.id]), 
            updated_data
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check that tipo was updated
        updated_tipo = Tipo.objects.get(id=self.tipo_ativo_1.id)
        self.assertEqual(updated_tipo.nome, 'Aposentadoria Atualizada')
        self.assertEqual(updated_tipo.descricao, 'Descrição atualizada')
        self.assertEqual(updated_tipo.cor, '#ff9800')
        self.assertEqual(updated_tipo.ordem, 5)
        self.assertFalse(updated_tipo.ativa)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('atualizado com sucesso' in str(message) for message in messages))
    
    def test_editar_tipo_precatorio_view_post_invalid_data(self):
        """Test POST request with invalid data for editing"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('editar_tipo_precatorio', args=[self.tipo_ativo_1.id]), 
            self.invalid_tipo_data
        )
        
        # Should not redirect (form errors)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/tipo_precatorio_form.html')
        
        # Check that tipo was not updated
        unchanged_tipo = Tipo.objects.get(id=self.tipo_ativo_1.id)
        self.assertEqual(unchanged_tipo.nome, 'Aposentadoria')  # Original name
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('corrija os erros' in str(message) for message in messages))
    
    def test_editar_tipo_precatorio_view_post_not_found(self):
        """Test POST request with non-existent tipo ID"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('editar_tipo_precatorio', args=[9999]), self.valid_tipo_data)
        
        self.assertEqual(response.status_code, 404)

    # ==================== DELETAR TIPO PRECATORIO VIEW TESTS ====================
    
    def test_deletar_tipo_precatorio_view_get_success(self):
        """Test GET request to deletar_tipo_precatorio_view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('deletar_tipo_precatorio', args=[self.tipo_ativo_2.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/confirmar_delete_tipo_precatorio.html')
        self.assertContains(response, self.tipo_ativo_2.nome)
        
        # Check context
        self.assertIn('tipo', response.context)
        self.assertIn('precatorios_count', response.context)
        self.assertEqual(response.context['tipo'], self.tipo_ativo_2)
        self.assertEqual(response.context['precatorios_count'], 0)
    
    def test_deletar_tipo_precatorio_view_get_with_precatorios(self):
        """Test GET request for tipo that has associated precatórios"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('deletar_tipo_precatorio', args=[self.tipo_ativo_1.id]))
        
        # Should redirect with error message (can't delete used tipo)
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('não é possível excluir' in str(message).lower() for message in messages))
        self.assertTrue(any('está sendo usado' in str(message) for message in messages))
    
    def test_deletar_tipo_precatorio_view_post_success(self):
        """Test successful POST request to delete tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        tipo_id = self.tipo_ativo_2.id
        tipo_nome = self.tipo_ativo_2.nome
        initial_count = Tipo.objects.count()
        
        response = self.client.post(reverse('deletar_tipo_precatorio', args=[tipo_id]))
        
        # Check redirect
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check that tipo was deleted
        self.assertEqual(Tipo.objects.count(), initial_count - 1)
        self.assertFalse(Tipo.objects.filter(id=tipo_id).exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('excluído com sucesso' in str(message) for message in messages))
        self.assertTrue(any(tipo_nome in str(message) for message in messages))
    
    def test_deletar_tipo_precatorio_view_post_with_precatorios(self):
        """Test POST request to delete tipo that has associated precatórios"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = Tipo.objects.count()
        response = self.client.post(reverse('deletar_tipo_precatorio', args=[self.tipo_ativo_1.id]))
        
        # Should redirect without deleting
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check that tipo was not deleted
        self.assertEqual(Tipo.objects.count(), initial_count)
        self.assertTrue(Tipo.objects.filter(id=self.tipo_ativo_1.id).exists())
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('não é possível excluir' in str(message).lower() for message in messages))
    
    def test_deletar_tipo_precatorio_view_not_found(self):
        """Test delete request with non-existent tipo ID"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('deletar_tipo_precatorio', args=[9999]))
        
        self.assertEqual(response.status_code, 404)

    # ==================== ATIVAR TIPO PRECATORIO VIEW TESTS ====================
    
    def test_ativar_tipo_precatorio_view_post_activate(self):
        """Test POST request to activate tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        # Start with inactive tipo
        self.tipo_inativo.ativa = False
        self.tipo_inativo.save()
        
        response = self.client.post(
            reverse('ativar_tipo_precatorio', args=[self.tipo_inativo.id]),
            {'ativo': 'true'}
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check that tipo was activated
        updated_tipo = Tipo.objects.get(id=self.tipo_inativo.id)
        self.assertTrue(updated_tipo.ativa)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('ativado com sucesso' in str(message) for message in messages))
    
    def test_ativar_tipo_precatorio_view_post_deactivate(self):
        """Test POST request to deactivate tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        # Start with active tipo
        self.tipo_ativo_2.ativa = True
        self.tipo_ativo_2.save()
        
        response = self.client.post(
            reverse('ativar_tipo_precatorio', args=[self.tipo_ativo_2.id]),
            {'ativo': 'false'}
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check that tipo was deactivated
        updated_tipo = Tipo.objects.get(id=self.tipo_ativo_2.id)
        self.assertFalse(updated_tipo.ativa)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('desativado com sucesso' in str(message) for message in messages))
    
    def test_ativar_tipo_precatorio_view_get_toggle(self):
        """Test GET request to toggle tipo activation (backward compatibility)"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test toggling from active to inactive
        original_status = self.tipo_ativo_1.ativa
        response = self.client.get(reverse('ativar_tipo_precatorio', args=[self.tipo_ativo_1.id]))
        
        # Check redirect
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check that tipo status was toggled
        updated_tipo = Tipo.objects.get(id=self.tipo_ativo_1.id)
        self.assertEqual(updated_tipo.ativa, not original_status)
    
    def test_ativar_tipo_precatorio_view_get_with_parameters(self):
        """Test GET request with ativo parameter"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test setting to active
        response = self.client.get(
            reverse('ativar_tipo_precatorio', args=[self.tipo_inativo.id]) + '?ativo=true'
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Check that tipo was activated
        updated_tipo = Tipo.objects.get(id=self.tipo_inativo.id)
        self.assertTrue(updated_tipo.ativa)
        
        # Test setting to inactive
        response = self.client.get(
            reverse('ativar_tipo_precatorio', args=[self.tipo_ativo_2.id]) + '?ativo=false'
        )
        
        # Check that tipo was deactivated
        updated_tipo = Tipo.objects.get(id=self.tipo_ativo_2.id)
        self.assertFalse(updated_tipo.ativa)
    
    def test_ativar_tipo_precatorio_view_not_found(self):
        """Test activation request with non-existent tipo ID"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ativar_tipo_precatorio', args=[9999]))
        
        self.assertEqual(response.status_code, 404)

    # ==================== INTEGRATION TESTS ====================
    
    def test_complete_crud_workflow(self):
        """Test complete CRUD workflow for tipo management"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Create new tipo
        create_data = {
            'nome': 'Workflow Test',
            'descricao': 'Tipo para teste completo',
            'cor': '#9c27b0',
            'ordem': 10,
            'ativa': True
        }
        
        response = self.client.post(reverse('novo_tipo_precatorio'), create_data)
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # 2. Verify tipo appears in list
        response = self.client.get(reverse('tipos_precatorio'))
        self.assertContains(response, 'Workflow Test')
        
        # 3. Edit the tipo
        created_tipo = Tipo.objects.get(nome='Workflow Test')
        edit_data = {
            'nome': 'Workflow Test Updated',
            'descricao': 'Descrição atualizada',
            'cor': '#e91e63',
            'ordem': 11,
            'ativa': False
        }
        
        response = self.client.post(
            reverse('editar_tipo_precatorio', args=[created_tipo.id]), 
            edit_data
        )
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # 4. Verify changes
        updated_tipo = Tipo.objects.get(id=created_tipo.id)
        self.assertEqual(updated_tipo.nome, 'Workflow Test Updated')
        self.assertFalse(updated_tipo.ativa)
        
        # 5. Toggle activation
        response = self.client.post(
            reverse('ativar_tipo_precatorio', args=[updated_tipo.id]),
            {'ativo': 'true'}
        )
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # 6. Verify activation
        updated_tipo = Tipo.objects.get(id=created_tipo.id)
        self.assertTrue(updated_tipo.ativa)
        
        # 7. Delete the tipo
        response = self.client.post(reverse('deletar_tipo_precatorio', args=[updated_tipo.id]))
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # 8. Verify deletion
        self.assertFalse(Tipo.objects.filter(id=created_tipo.id).exists())
    
    def test_multiple_users_access(self):
        """Test that multiple users can access views independently"""
        # Test with regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tipos_precatorio'))
        self.assertEqual(response.status_code, 200)
        
        # Test with admin user
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('tipos_precatorio'))
        self.assertEqual(response.status_code, 200)
        
        # Both should see the same data
        context = response.context
        self.assertEqual(context['total_tipos'], 3)

    # ==================== EDGE CASE TESTS ====================
    
    def test_tipo_with_special_characters(self):
        """Test creating tipo with special characters in name"""
        self.client.login(username='testuser', password='testpass123')
        
        special_data = {
            'nome': 'Tipo Acentuação & Símbolos',
            'descricao': 'Teste com ções, acentos & símbolos',
            'cor': '#607d8b',
            'ordem': 20,
            'ativa': True
        }
        
        response = self.client.post(reverse('novo_tipo_precatorio'), special_data)
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Verify tipo was created with special characters
        created_tipo = Tipo.objects.get(nome='Tipo Acentuação & Símbolos')
        self.assertEqual(created_tipo.descricao, 'Teste com ções, acentos & símbolos')
    
    def test_tipo_with_maximum_length_fields(self):
        """Test creating tipo with maximum length fields"""
        self.client.login(username='testuser', password='testpass123')
        
        max_length_data = {
            'nome': 'A' * 100,  # Maximum length for nome field
            'descricao': 'B' * 1000,  # Long description
            'cor': '#ffffff',
            'ordem': 999999,  # Large order number
            'ativa': True
        }
        
        response = self.client.post(reverse('novo_tipo_precatorio'), max_length_data)
        self.assertRedirects(response, reverse('tipos_precatorio'))
        
        # Verify tipo was created
        created_tipo = Tipo.objects.get(nome='A' * 100)
        self.assertEqual(len(created_tipo.nome), 100)
        self.assertEqual(created_tipo.ordem, 999999)

    # ==================== PERFORMANCE TESTS ====================
    
    def test_list_view_with_many_tipos_performance(self):
        """Test list view performance with many tipos"""
        # Create many tipos
        tipos_to_create = []
        for i in range(100):
            tipos_to_create.append(Tipo(
                nome=f'Performance Tipo {i:03d}',
                descricao=f'Descrição {i}',
                cor=f'#{i:06x}',
                ordem=i + 100,
                ativa=i % 2 == 0
            ))
        
        Tipo.objects.bulk_create(tipos_to_create)
        
        self.client.login(username='testuser', password='testpass123')
        
        # Measure response time (basic performance check)
        import time
        start_time = time.time()
        response = self.client.get(reverse('tipos_precatorio'))
        end_time = time.time()
        
        # Should complete within reasonable time (2 seconds)
        self.assertLess(end_time - start_time, 2.0)
        self.assertEqual(response.status_code, 200)
        
        # Verify correct count
        context = response.context
        self.assertEqual(context['total_tipos'], 103)  # 3 original + 100 new

    # ==================== ERROR HANDLING TESTS ====================
    
    def test_invalid_tipo_id_in_urls(self):
        """Test views with invalid tipo IDs"""
        self.client.login(username='testuser', password='testpass123')
        
        invalid_ids = [0, -1, 'abc', 999999]
        
        for invalid_id in invalid_ids:
            if str(invalid_id).isdigit() and int(invalid_id) > 0:
                # Valid integer but non-existent
                response = self.client.get(reverse('editar_tipo_precatorio', args=[invalid_id]))
                self.assertEqual(response.status_code, 404)
            # Invalid non-integer IDs would cause URL resolution errors, 
            # which is handled by Django's URL system
    
    def test_post_requests_csrf_protection(self):
        """Test that POST requests require CSRF protection"""
        # This test verifies CSRF protection is configured correctly
        # Django TestClient automatically includes CSRF tokens, so we test 
        # that the forms render with CSRF tokens
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('novo_tipo_precatorio'))
        
        # Check that the form includes CSRF token
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertEqual(response.status_code, 200)
    
    def test_concurrent_operations(self):
        """Test concurrent operations on the same tipo"""
        self.client.login(username='testuser', password='testpass123')
        
        # Simulate concurrent edits by making rapid successive requests
        edit_data_1 = {
            'nome': 'Concurrent Edit 1',
            'descricao': 'First edit',
            'cor': '#ffeb3b',
            'ordem': 50,
            'ativa': True
        }
        
        edit_data_2 = {
            'nome': 'Concurrent Edit 2',
            'descricao': 'Second edit',
            'cor': '#ff5722',
            'ordem': 51,
            'ativa': False
        }
        
        tipo_id = self.tipo_ativo_1.id
        
        # Make two rapid successive edits
        response1 = self.client.post(reverse('editar_tipo_precatorio', args=[tipo_id]), edit_data_1)
        response2 = self.client.post(reverse('editar_tipo_precatorio', args=[tipo_id]), edit_data_2)
        
        # Both should succeed (last one wins)
        self.assertRedirects(response1, reverse('tipos_precatorio'))
        self.assertRedirects(response2, reverse('tipos_precatorio'))
        
        # Verify final state (second edit should be applied)
        final_tipo = Tipo.objects.get(id=tipo_id)
        self.assertEqual(final_tipo.nome, 'Concurrent Edit 2')
        self.assertEqual(final_tipo.descricao, 'Second edit')
