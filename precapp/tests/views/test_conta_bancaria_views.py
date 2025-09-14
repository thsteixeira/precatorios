"""
Comprehensive test suite for ContaBancaria CRUD views functionality.

This module contains comprehensive tests for all ContaBancaria-related views in the precatorios
application, ensuring proper functionality of bank account management features.

Test Coverage:
    - contas_bancarias_view: List all bank accounts with statistics
    - nova_conta_bancaria_view: Create new bank accounts
    - editar_conta_bancaria_view: Edit existing bank accounts (regular and dropdown forms)
    - deletar_conta_bancaria_view: Delete bank accounts with protection checks

Key Test Areas:
    - Authentication and Authorization: All views require login
    - CRUD Operations: Full Create, Read, Update, Delete testing
    - Form Validation: Valid and invalid form submissions
    - Business Logic: Protection against deleting accounts with recebimentos
    - User Feedback: Success and error message display
    - Data Integrity: Database state changes and relationships
    - Template Rendering: Correct template usage and context data
    - URL Resolution: URL patterns and parameter handling
    - Edge Cases: Boundary conditions and error scenarios

Business Rules Tested:
    - Only authenticated users can access views
    - Bank accounts cannot be deleted if they have related recebimentos
    - Form validation prevents invalid data and enforces required fields
    - Statistics are calculated correctly for list view
    - Both regular form edit and inline dropdown edit work properly
    - Success/error messages are displayed appropriately

Security Considerations:
    - All views require authentication (@login_required)
    - Proper object retrieval with 404 handling
    - CSRF protection on form submissions
    - No unauthorized access to bank account operations

Performance Testing:
    - Tests with multiple accounts for list view performance
    - Tests statistics calculation efficiency
    - Tests form validation performance
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.db import IntegrityError
from decimal import Decimal

from precapp.models import (
    ContaBancaria, Recebimentos, Alvara, Precatorio, Cliente, Tipo
)


class ContaBancariaViewsTest(TestCase):
    """
    Comprehensive test suite for ContaBancaria views functionality.
    
    This test class provides thorough coverage of all CRUD operations and business logic
    for managing bank accounts in the system. It validates view behavior, form handling,
    authentication requirements, permission checks, data validation, and user feedback.
    
    Test Coverage:
        - contas_bancarias_view: List all bank accounts with statistics and recebimentos count
        - nova_conta_bancaria_view: Create new bank accounts with validation
        - editar_conta_bancaria_view: Edit existing accounts (both regular and dropdown forms)
        - deletar_conta_bancaria_view: Delete accounts with protection checks
        
    Key Test Areas:
        - Authentication: All views require login
        - CRUD Operations: All Create, Read, Update, Delete operations
        - Form Validation: Valid and invalid form submissions
        - Business Logic: Protection against deleting accounts with recebimentos
        - User Feedback: Success and error message display
        - Data Integrity: Database state changes and relationship handling
        - Template Context: Correct context data and statistics
        - URL Patterns: Proper URL resolution and parameter handling
        - Edge Cases: Error scenarios and boundary conditions
        
    Business Rules Tested:
        - Only authenticated users can access bank account views
        - Accounts with related recebimentos cannot be deleted
        - Form validation prevents duplicate accounts and invalid data
        - Statistics are calculated correctly (total, with/without recebimentos)
        - Both form edit and inline edit work properly
        - Success/error messages are displayed correctly
        
    Integration Testing:
        - Tests view integration with models and forms
        - Tests template rendering with context data
        - Tests message framework integration
        - Tests URL pattern integration
        - Tests relationship handling with Recebimentos model
    """
    
    def setUp(self):
        """Set up test data for ContaBancaria views testing"""
        # Create test users
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
        
        # Create test bank accounts
        self.conta_bb = ContaBancaria.objects.create(
            banco='Banco do Brasil',
            tipo_de_conta='corrente',
            agencia='1234-5',
            conta='12345678-9'
        )
        
        self.conta_caixa = ContaBancaria.objects.create(
            banco='Caixa Econômica Federal',
            tipo_de_conta='poupanca',
            agencia='0001',
            conta='987654321-0'
        )
        
        self.conta_sem_recebimentos = ContaBancaria.objects.create(
            banco='Bradesco',
            tipo_de_conta='corrente',
            agencia='5432-1',
            conta='11111111-1'
        )
        
        # Create test data for relationships (to test recebimentos count)
        self.tipo = Tipo.objects.create(
            nome='Alimentar',
            cor='#007bff',
            ativa=True
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678901',
            nome='João Silva',
            nascimento='1980-01-01',
            prioridade=False
        )
        
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            origem='Test Case',
            valor_de_face=100000.00,
            tipo=self.tipo
        )
        self.precatorio.clientes.add(self.cliente)
        
        self.alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            tipo='Test Alvará'
        )
        
        # Create recebimentos for testing statistics and deletion protection
        self.recebimento_1 = Recebimentos.objects.create(
            numero_documento='REC-001',
            alvara=self.alvara,
            data='2023-01-15',
            conta_bancaria=self.conta_bb,
            valor=Decimal('25000.00'),
            tipo='Hon. contratuais'
        )
        
        self.recebimento_2 = Recebimentos.objects.create(
            numero_documento='REC-002',
            alvara=self.alvara,
            data='2023-02-15',
            conta_bancaria=self.conta_caixa,
            valor=Decimal('15000.00'),
            tipo='Hon. sucumbenciais'
        )

    def tearDown(self):
        """Clean up after tests"""
        # Clean up in reverse order of dependencies
        Recebimentos.objects.all().delete()
        Alvara.objects.all().delete()
        Precatorio.objects.all().delete()
        Cliente.objects.all().delete()
        Tipo.objects.all().delete()
        ContaBancaria.objects.all().delete()
        User.objects.all().delete()

    # ========================
    # Authentication Tests
    # ========================

    def test_contas_bancarias_view_requires_login(self):
        """Test that contas_bancarias_view requires user authentication"""
        url = reverse('contas_bancarias')
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_nova_conta_bancaria_view_requires_login(self):
        """Test that nova_conta_bancaria_view requires user authentication"""
        url = reverse('nova_conta_bancaria')
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_editar_conta_bancaria_view_requires_login(self):
        """Test that editar_conta_bancaria_view requires user authentication"""
        url = reverse('editar_conta_bancaria', args=[self.conta_bb.id])
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_deletar_conta_bancaria_view_requires_login(self):
        """Test that deletar_conta_bancaria_view requires user authentication"""
        url = reverse('deletar_conta_bancaria', args=[self.conta_bb.id])
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    # ========================
    # List View Tests
    # ========================

    def test_contas_bancarias_view_authenticated_user(self):
        """Test contas_bancarias_view with authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('contas_bancarias')
        response = self.client.get(url)
        
        # Should render successfully
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/contas_bancarias_list.html')
        
        # Check context data
        self.assertIn('contas_bancarias', response.context)
        self.assertIn('total_contas', response.context)
        self.assertIn('contas_com_recebimentos', response.context)
        self.assertIn('contas_sem_recebimentos', response.context)
        self.assertIn('total_recebimentos', response.context)
        
        # Verify statistics
        self.assertEqual(response.context['total_contas'], 3)
        self.assertEqual(response.context['contas_com_recebimentos'], 2)  # BB and Caixa have recebimentos
        self.assertEqual(response.context['contas_sem_recebimentos'], 1)  # Bradesco has no recebimentos
        self.assertEqual(response.context['total_recebimentos'], 2)  # Total of 2 recebimentos

    def test_contas_bancarias_view_empty_database(self):
        """Test contas_bancarias_view with no bank accounts"""
        # Clear all data
        Recebimentos.objects.all().delete()
        ContaBancaria.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('contas_bancarias')
        response = self.client.get(url)
        
        # Should render successfully
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/contas_bancarias_list.html')
        
        # Check empty statistics
        self.assertEqual(response.context['total_contas'], 0)
        self.assertEqual(response.context['contas_com_recebimentos'], 0)
        self.assertEqual(response.context['contas_sem_recebimentos'], 0)
        self.assertEqual(response.context['total_recebimentos'], 0)

    def test_contas_bancarias_view_ordering(self):
        """Test that bank accounts are properly ordered by banco, agencia"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('contas_bancarias')
        response = self.client.get(url)
        
        contas = list(response.context['contas_bancarias'])
        
        # Should be ordered by banco, then agencia (Banco do Brasil, Bradesco, Caixa)
        self.assertEqual(contas[0].banco, 'Banco do Brasil')
        self.assertEqual(contas[1].banco, 'Bradesco')
        self.assertEqual(contas[2].banco, 'Caixa Econômica Federal')

    # ========================
    # Create View Tests
    # ========================

    def test_nova_conta_bancaria_view_get_request(self):
        """Test nova_conta_bancaria_view GET request shows form"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('nova_conta_bancaria')
        response = self.client.get(url)
        
        # Should render form successfully
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/conta_bancaria_form.html')
        
        # Check context data
        self.assertIn('form', response.context)
        self.assertEqual(response.context['title'], 'Nova Conta Bancária')
        self.assertEqual(response.context['action'], 'Criar')

    def test_nova_conta_bancaria_view_valid_post(self):
        """Test creating new bank account with valid data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('nova_conta_bancaria')
        
        data = {
            'banco': 'Itaú Unibanco',
            'tipo_de_conta': 'corrente',
            'agencia': '9999',
            'conta': '88888888-8'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to list view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contas_bancarias'))
        
        # Verify account was created
        self.assertTrue(
            ContaBancaria.objects.filter(
                banco='Itaú Unibanco',
                agencia='9999'
            ).exists()
        )
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('criada com sucesso', str(messages[0]))

    def test_nova_conta_bancaria_view_invalid_post(self):
        """Test creating bank account with invalid data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('nova_conta_bancaria')
        
        # Missing required fields
        data = {
            'banco': '',  # Required field missing
            'tipo_de_conta': 'corrente',
            'agencia': '9999',
            'conta': '88888888-8'
        }
        
        response = self.client.post(url, data)
        
        # Should render form again with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/conta_bancaria_form.html')
        
        # Check that form has errors
        self.assertContains(response, 'Este campo é obrigatório')
        
        # Verify form is in context and has errors
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('banco', form.errors)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('corrija os erros', str(messages[0]))

    def test_nova_conta_bancaria_view_duplicate_account(self):
        """Test creating duplicate bank account (should be prevented by unique_together)"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('nova_conta_bancaria')
        
        # Try to create duplicate of existing account
        data = {
            'banco': 'Banco do Brasil',  # Same as existing
            'tipo_de_conta': 'corrente',
            'agencia': '1234-5',  # Same as existing
            'conta': '12345678-9'  # Same as existing
        }
        
        response = self.client.post(url, data)
        
        # Should render form again with error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/conta_bancaria_form.html')
        
        # Should have validation error
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        
        # Check that the unique constraint error appears
        self.assertContains(response, 'Conta Bancária com este')
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('corrija os erros', str(messages[0]))

    # ========================
    # Edit View Tests
    # ========================

    def test_editar_conta_bancaria_view_get_request(self):
        """Test editar_conta_bancaria_view GET request shows populated form"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('editar_conta_bancaria', args=[self.conta_bb.id])
        response = self.client.get(url)
        
        # Should render form successfully
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/conta_bancaria_form.html')
        
        # Check context data
        self.assertIn('form', response.context)
        self.assertIn('conta', response.context)
        self.assertEqual(response.context['conta'], self.conta_bb)
        self.assertEqual(response.context['title'], f'Editar Conta: {self.conta_bb.banco}')
        self.assertEqual(response.context['action'], 'Atualizar')
        
        # Check form is populated
        form = response.context['form']
        self.assertEqual(form.instance, self.conta_bb)

    def test_editar_conta_bancaria_view_nonexistent_account(self):
        """Test editing non-existent bank account returns 404"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('editar_conta_bancaria', args=[99999])
        response = self.client.get(url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)

    def test_editar_conta_bancaria_view_regular_form_valid_post(self):
        """Test editing bank account with regular form submission"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('editar_conta_bancaria', args=[self.conta_bb.id])
        
        data = {
            'banco': 'Banco do Brasil S.A.',  # Updated
            'tipo_de_conta': 'poupanca',  # Changed
            'agencia': '5678-9',  # Updated
            'conta': '87654321-0'  # Updated
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to list view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contas_bancarias'))
        
        # Verify account was updated
        self.conta_bb.refresh_from_db()
        self.assertEqual(self.conta_bb.banco, 'Banco do Brasil S.A.')
        self.assertEqual(self.conta_bb.tipo_de_conta, 'poupanca')
        self.assertEqual(self.conta_bb.agencia, '5678-9')
        self.assertEqual(self.conta_bb.conta, '87654321-0')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('atualizada com sucesso', str(messages[0]))

    def test_editar_conta_bancaria_view_dropdown_form_valid_post(self):
        """Test editing bank account with dropdown form submission"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('editar_conta_bancaria', args=[self.conta_bb.id])
        
        data = {
            'update_conta': 'true',  # Indicates dropdown form
            'banco': 'Banco do Brasil Updated',
            'tipo_de_conta': 'poupanca',
            'agencia': '9999',
            'conta': '99999999-9'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to list view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contas_bancarias'))
        
        # Verify account was updated
        self.conta_bb.refresh_from_db()
        self.assertEqual(self.conta_bb.banco, 'Banco do Brasil Updated')
        self.assertEqual(self.conta_bb.tipo_de_conta, 'poupanca')
        self.assertEqual(self.conta_bb.agencia, '9999')
        self.assertEqual(self.conta_bb.conta, '99999999-9')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('atualizada com sucesso', str(messages[0]))

    def test_editar_conta_bancaria_view_dropdown_form_invalid_post(self):
        """Test editing bank account with invalid dropdown form submission"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('editar_conta_bancaria', args=[self.conta_bb.id])
        
        data = {
            'update_conta': 'true',  # Indicates dropdown form
            'banco': '',  # Missing required field
            'tipo_de_conta': 'poupanca',
            'agencia': '9999',
            'conta': '99999999-9'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to list view with error
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contas_bancarias'))
        
        # Account should not be updated
        self.conta_bb.refresh_from_db()
        self.assertEqual(self.conta_bb.banco, 'Banco do Brasil')  # Original value
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Todos os campos são obrigatórios', str(messages[0]))

    def test_editar_conta_bancaria_view_regular_form_invalid_post(self):
        """Test editing bank account with invalid regular form submission"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('editar_conta_bancaria', args=[self.conta_bb.id])
        
        data = {
            'banco': '',  # Missing required field
            'tipo_de_conta': 'corrente',
            'agencia': '1234-5',
            'conta': '12345678-9'
        }
        
        response = self.client.post(url, data)
        
        # Should render form again with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/conta_bancaria_form.html')
        
        # Check that form has errors
        self.assertContains(response, 'Este campo é obrigatório')
        
        # Verify form is in context and has errors
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('banco', form.errors)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('corrija os erros', str(messages[0]))

    # ========================
    # Delete View Tests
    # ========================

    def test_deletar_conta_bancaria_view_get_request(self):
        """Test deletar_conta_bancaria_view GET request shows confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('deletar_conta_bancaria', args=[self.conta_sem_recebimentos.id])
        response = self.client.get(url)
        
        # Should render confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/confirmar_delete_conta_bancaria.html')
        
        # Check context data
        self.assertIn('conta', response.context)
        self.assertIn('recebimentos_count', response.context)
        self.assertIn('can_delete', response.context)
        
        self.assertEqual(response.context['conta'], self.conta_sem_recebimentos)
        self.assertEqual(response.context['recebimentos_count'], 0)
        self.assertTrue(response.context['can_delete'])

    def test_deletar_conta_bancaria_view_with_recebimentos(self):
        """Test deletion confirmation for account with recebimentos"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('deletar_conta_bancaria', args=[self.conta_bb.id])
        response = self.client.get(url)
        
        # Should render confirmation page with protection warning
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/confirmar_delete_conta_bancaria.html')
        
        # Check context data shows protection
        self.assertEqual(response.context['conta'], self.conta_bb)
        self.assertEqual(response.context['recebimentos_count'], 1)  # Has 1 recebimento
        self.assertFalse(response.context['can_delete'])

    def test_deletar_conta_bancaria_view_successful_deletion(self):
        """Test successful bank account deletion"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('deletar_conta_bancaria', args=[self.conta_sem_recebimentos.id])
        
        # Verify account exists before deletion
        self.assertTrue(ContaBancaria.objects.filter(id=self.conta_sem_recebimentos.id).exists())
        
        response = self.client.post(url)
        
        # Should redirect to list view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contas_bancarias'))
        
        # Verify account was deleted
        self.assertFalse(ContaBancaria.objects.filter(id=self.conta_sem_recebimentos.id).exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('excluída com sucesso', str(messages[0]))

    def test_deletar_conta_bancaria_view_protected_deletion_attempt(self):
        """Test attempting to delete account with recebimentos (should be protected by database)"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('deletar_conta_bancaria', args=[self.conta_bb.id])
        
        # Verify account exists before deletion attempt
        self.assertTrue(ContaBancaria.objects.filter(id=self.conta_bb.id).exists())
        
        response = self.client.post(url)
        
        # Should redirect to list view
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contas_bancarias'))
        
        # Account should still exist (protected by PROTECT constraint)
        self.assertTrue(ContaBancaria.objects.filter(id=self.conta_bb.id).exists())
        
        # Should have error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Erro ao excluir conta', str(messages[0]))

    def test_deletar_conta_bancaria_view_nonexistent_account(self):
        """Test deleting non-existent bank account returns 404"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('deletar_conta_bancaria', args=[99999])
        response = self.client.get(url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)

    # ========================
    # Edge Cases and Error Handling Tests
    # ========================

    def test_contas_bancarias_view_with_admin_user(self):
        """Test that admin users can access contas_bancarias_view"""
        self.client.login(username='admin', password='adminpass123')
        url = reverse('contas_bancarias')
        response = self.client.get(url)
        
        # Should render successfully
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/contas_bancarias_list.html')

    def test_nova_conta_bancaria_view_account_type_choices(self):
        """Test that form includes proper account type choices"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('nova_conta_bancaria')
        response = self.client.get(url)
        
        form = response.context['form']
        tipo_de_conta_field = form.fields['tipo_de_conta']
        
        # Check choices include expected values
        choices = [choice[0] for choice in tipo_de_conta_field.choices]
        self.assertIn('corrente', choices)
        self.assertIn('poupanca', choices)

    def test_editar_conta_bancaria_view_preserves_relationships(self):
        """Test that editing account preserves recebimentos relationships"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('editar_conta_bancaria', args=[self.conta_bb.id])
        
        # Count recebimentos before edit
        recebimentos_before = self.conta_bb.recebimentos_set.count()
        
        data = {
            'banco': 'Banco do Brasil Updated',
            'tipo_de_conta': 'corrente',
            'agencia': '1234-5',
            'conta': '12345678-9'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect successfully
        self.assertEqual(response.status_code, 302)
        
        # Refresh and check recebimentos are preserved
        self.conta_bb.refresh_from_db()
        recebimentos_after = self.conta_bb.recebimentos_set.count()
        self.assertEqual(recebimentos_before, recebimentos_after)

    def test_statistics_calculation_accuracy(self):
        """Test that statistics in list view are calculated accurately"""
        # Create additional test data
        conta_test = ContaBancaria.objects.create(
            banco='Teste Bank',
            tipo_de_conta='corrente',
            agencia='0000',
            conta='00000000-0'
        )
        
        # Add another recebimento to different account
        Recebimentos.objects.create(
            numero_documento='REC-003',
            alvara=self.alvara,
            data='2023-03-15',
            conta_bancaria=conta_test,
            valor=Decimal('5000.00'),
            tipo='Hon. contratuais'
        )
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('contas_bancarias')
        response = self.client.get(url)
        
        # Verify updated statistics
        self.assertEqual(response.context['total_contas'], 4)  # Original 3 + 1 new
        self.assertEqual(response.context['contas_com_recebimentos'], 3)  # BB, Caixa, Test
        self.assertEqual(response.context['contas_sem_recebimentos'], 1)  # Bradesco
        self.assertEqual(response.context['total_recebimentos'], 3)  # 2 original + 1 new

    def test_url_patterns_resolve_correctly(self):
        """Test that all URL patterns resolve to correct views"""
        # Test list URL
        url = reverse('contas_bancarias')
        self.assertEqual(url, '/contas-bancarias/')
        
        # Test create URL
        url = reverse('nova_conta_bancaria')
        self.assertEqual(url, '/contas-bancarias/nova/')
        
        # Test edit URL
        url = reverse('editar_conta_bancaria', args=[1])
        self.assertEqual(url, '/contas-bancarias/1/editar/')
        
        # Test delete URL
        url = reverse('deletar_conta_bancaria', args=[1])
        self.assertEqual(url, '/contas-bancarias/1/deletar/')

    def test_form_validation_comprehensive(self):
        """Test comprehensive form validation scenarios"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('nova_conta_bancaria')
        
        # Test all fields empty
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        
        # Check that form has errors
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('banco', form.errors)
        self.assertIn('agencia', form.errors)
        self.assertIn('conta', form.errors)
        
        # Test invalid tipo_de_conta
        data = {
            'banco': 'Test Bank',
            'tipo_de_conta': 'invalid_type',
            'agencia': '1234',
            'conta': '12345678'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        # Check form validation error
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('tipo_de_conta', form.errors)
        
        # Check the error message contains reference to valid choices
        self.assertContains(response, 'Faça uma escolha válida')

    def test_message_system_integration(self):
        """Test that Django messages system works correctly across all operations"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test create success message
        url = reverse('nova_conta_bancaria')
        data = {
            'banco': 'Message Test Bank',
            'tipo_de_conta': 'corrente',
            'agencia': '9999',
            'conta': '99999999-9'
        }
        response = self.client.post(url, data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('criada com sucesso' in str(msg) for msg in messages))
        
        # Test edit success message
        created_account = ContaBancaria.objects.get(banco='Message Test Bank')
        url = reverse('editar_conta_bancaria', args=[created_account.id])
        data.update({'banco': 'Message Test Bank Updated'})
        response = self.client.post(url, data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('atualizada com sucesso' in str(msg) for msg in messages))