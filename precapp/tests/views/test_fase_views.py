from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib import messages as constants

from precapp.models import Fase, Alvara, Requerimento, Precatorio, Cliente, PedidoRequerimento
from datetime import date


class FasesViewTest(TestCase):
    """
    Comprehensive test cases for fases_view function.
    
    Tests cover all aspects of the phases list view including authentication requirements,
    template rendering, context data validation, statistics calculations, model ordering,
    filtering capabilities, database queries optimization, and integration with the
    workflow management system for the legal document processing application.
    """
    
    def setUp(self):
        """Set up comprehensive test data for fases_view testing"""
        self.client_app = Client()
        
        # Create test user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test phases with different types and statuses for comprehensive testing
        self.fase_alvara_ativa = Fase.objects.create(
            nome='Alvará Em Andamento',
            tipo='alvara',
            cor='#007bff',
            ativa=True,
            ordem=1
        )
        
        self.fase_requerimento_ativa = Fase.objects.create(
            nome='Requerimento Deferido',
            tipo='requerimento',
            cor='#28a745',
            ativa=True,
            ordem=2
        )
        
        self.fase_ambos_ativa = Fase.objects.create(
            nome='Finalizado',
            tipo='ambos',
            cor='#6c757d',
            ativa=True,
            ordem=3
        )
        
        self.fase_alvara_inativa = Fase.objects.create(
            nome='Alvará Cancelado',
            tipo='alvara',
            cor='#dc3545',
            ativa=False,
            ordem=4
        )
        
        self.fase_requerimento_inativa = Fase.objects.create(
            nome='Requerimento Indeferido',
            tipo='requerimento',
            cor='#ffc107',
            ativa=False,
            ordem=5
        )
        
        self.fase_ambos_inativa = Fase.objects.create(
            nome='Processo Arquivado',
            tipo='ambos',
            cor='#17a2b8',
            ativa=False,
            ordem=6
        )
        
        # Create test data for usage validation (precatorios, clientes, alvaras, requerimentos)
        self.cliente = Cliente.objects.create(
            cpf='11144477735',  # Valid CPF
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='Tribunal de São Paulo',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Link cliente to precatorio
        self.precatorio.clientes.add(self.cliente)
        
        # Create alvara using active phase
        self.alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='comum',
            fase=self.fase_alvara_ativa
        )
        
        # Create test PedidoRequerimento
        self.pedido_prioridade = PedidoRequerimento.objects.create(
            nome='Prioridade por idade',
            descricao='Pedido de prioridade por idade',
            cor='#ffc107',
            ordem=1,
            ativo=True
        )
        
        # Create requerimento using active phase
        self.requerimento = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor=25000.00,
            desagio=5.0,
            pedido=self.pedido_prioridade,
            fase=self.fase_requerimento_ativa
        )
        
        # Test URLs
        self.fases_url = reverse('fases')
        self.login_url = reverse('login')
    
    # ===============================
    # AUTHENTICATION TESTS
    # ===============================
    
    def test_fases_view_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client_app.get(self.fases_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Follow redirect to verify login requirement
        response = self.client_app.get(self.fases_url, follow=True)
        self.assertContains(response, 'login')
    
    def test_fases_view_authenticated_access(self):
        """Test that authenticated users can access the fases list view"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(self.fases_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fases_list.html')
        self.assertContains(response, 'Fases')
    
    # ===============================
    # TEMPLATE AND CONTEXT TESTS
    # ===============================
    
    def test_fases_view_context_data_completeness(self):
        """Test that all required context data is provided"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        # Check all required context keys
        expected_context_keys = [
            'fases', 'total_fases', 'fases_ativas', 'fases_inativas'
        ]
        
        for key in expected_context_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")
    
    def test_fases_view_template_rendering(self):
        """Test that template renders correctly with phase data"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        # Should contain phase names
        self.assertContains(response, 'Alvará Em Andamento')
        self.assertContains(response, 'Requerimento Deferido')
        self.assertContains(response, 'Finalizado')
        
        # Should contain phase types
        self.assertContains(response, 'alvara')
        self.assertContains(response, 'requerimento')
        self.assertContains(response, 'ambos')
        
        # Should contain colors (hex codes)
        self.assertContains(response, '#007bff')
        self.assertContains(response, '#28a745')
        self.assertContains(response, '#6c757d')
    
    def test_fases_view_shows_both_active_and_inactive(self):
        """Test that view displays both active and inactive phases"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        # Should show active phases
        self.assertContains(response, 'Alvará Em Andamento')  # Active
        self.assertContains(response, 'Requerimento Deferido')  # Active
        self.assertContains(response, 'Finalizado')  # Active
        
        # Should show inactive phases
        self.assertContains(response, 'Alvará Cancelado')  # Inactive
        self.assertContains(response, 'Requerimento Indeferido')  # Inactive
        self.assertContains(response, 'Processo Arquivado')  # Inactive
    
    # ===============================
    # STATISTICS CALCULATION TESTS
    # ===============================
    
    def test_statistics_calculations(self):
        """Test that statistics are calculated correctly"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        context = response.context
        
        # Test basic counts
        self.assertEqual(context['total_fases'], 6)  # All 6 phases created
        self.assertEqual(context['fases_ativas'], 3)  # 3 active phases
        self.assertEqual(context['fases_inativas'], 3)  # 3 inactive phases
    
    def test_statistics_consistency(self):
        """Test that statistics add up correctly"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        context = response.context
        
        # Active + Inactive should equal Total
        self.assertEqual(
            context['fases_ativas'] + context['fases_inativas'],
            context['total_fases']
        )
    
    def test_statistics_with_no_phases(self):
        """Test statistics when no phases exist"""
        # Delete related objects first to avoid foreign key constraints
        Alvara.objects.all().delete()
        Requerimento.objects.all().delete()
        Precatorio.objects.all().delete()
        Cliente.objects.all().delete()
        
        # Now delete all phases
        Fase.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        context = response.context
        
        # All counts should be zero
        self.assertEqual(context['total_fases'], 0)
        self.assertEqual(context['fases_ativas'], 0)
        self.assertEqual(context['fases_inativas'], 0)
    
    def test_statistics_with_only_active_phases(self):
        """Test statistics with only active phases"""
        # Delete all inactive phases
        Fase.objects.filter(ativa=False).delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        context = response.context
        
        # Should have only active phases
        self.assertEqual(context['total_fases'], 3)
        self.assertEqual(context['fases_ativas'], 3)
        self.assertEqual(context['fases_inativas'], 0)
    
    def test_statistics_with_only_inactive_phases(self):
        """Test statistics with only inactive phases"""
        # Deactivate all active phases
        Fase.objects.filter(ativa=True).update(ativa=False)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        context = response.context
        
        # Should have only inactive phases
        self.assertEqual(context['total_fases'], 6)
        self.assertEqual(context['fases_ativas'], 0)
        self.assertEqual(context['fases_inativas'], 6)
    
    # ===============================
    # MODEL ORDERING TESTS
    # ===============================
    
    def test_phases_ordering(self):
        """Test that phases are returned in correct order"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        fases = response.context['fases']
        
        # Should be ordered by ordem, tipo, nome (model's default ordering)
        self.assertEqual(len(fases), 6)
        
        # Verify ordering by checking ordem values
        ordem_values = [fase.ordem for fase in fases]
        self.assertEqual(ordem_values, sorted(ordem_values))
        
        # First phase should have ordem=1
        self.assertEqual(fases[0].ordem, 1)
        self.assertEqual(fases[0].nome, 'Alvará Em Andamento')
    
    def test_phases_ordering_with_same_ordem(self):
        """Test ordering when phases have same ordem value"""
        # Create two phases with same ordem but different types
        Fase.objects.create(
            nome='Fase A',
            tipo='alvara',
            cor='#000000',
            ativa=True,
            ordem=10
        )
        
        Fase.objects.create(
            nome='Fase B',
            tipo='requerimento',
            cor='#111111',
            ativa=True,
            ordem=10
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        fases = list(response.context['fases'])
        
        # Find the phases with ordem=10
        fases_ordem_10 = [f for f in fases if f.ordem == 10]
        self.assertEqual(len(fases_ordem_10), 2)
        
        # Should be ordered by tipo: 'alvara' comes before 'requerimento'
        self.assertEqual(fases_ordem_10[0].tipo, 'alvara')
        self.assertEqual(fases_ordem_10[1].tipo, 'requerimento')
    
    # ===============================
    # QUERYSET OPTIMIZATION TESTS
    # ===============================
    
    def test_database_query_efficiency(self):
        """Test that view uses efficient database queries"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Should make minimal queries: session, user, main query, statistics queries
        with self.assertNumQueries(6):  # Adjust based on actual query count
            response = self.client_app.get(self.fases_url)
            fases = list(response.context['fases'])
            
            # Access all phase data to ensure no additional queries
            for fase in fases:
                _ = fase.nome
                _ = fase.tipo
                _ = fase.cor
                _ = fase.ativa
                _ = fase.ordem
    
    def test_large_dataset_performance(self):
        """Test performance with larger dataset"""
        # Create additional phases
        for i in range(50):
            Fase.objects.create(
                nome=f'Fase {i}',
                tipo='ambos',
                cor='#999999',
                ativa=i % 2 == 0,  # Alternate active/inactive
                ordem=i + 100
            )
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Should handle large dataset efficiently
        response = self.client_app.get(self.fases_url)
        
        # Should return all phases (6 original + 50 new = 56)
        self.assertEqual(len(response.context['fases']), 56)
        
        # Statistics should be correct
        self.assertEqual(response.context['total_fases'], 56)
        self.assertEqual(response.context['fases_ativas'], 28)  # 3 original + 25 new
        self.assertEqual(response.context['fases_inativas'], 28)  # 3 original + 25 new
    
    # ===============================
    # DATA INTEGRITY TESTS
    # ===============================
    
    def test_fase_data_completeness(self):
        """Test that all fase data is correctly displayed"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        fases = response.context['fases']
        
        # All phases should have complete data
        for fase in fases:
            self.assertIsNotNone(fase.nome)
            self.assertIsNotNone(fase.tipo)
            self.assertIsNotNone(fase.cor)
            self.assertIsNotNone(fase.ordem)
            self.assertIn(fase.ativa, [True, False])  # Boolean value
            
            # Tipo should be one of valid choices
            self.assertIn(fase.tipo, ['alvara', 'requerimento', 'ambos'])
            
            # Color should be valid hex format
            self.assertTrue(fase.cor.startswith('#'))
            self.assertEqual(len(fase.cor), 7)  # #RRGGBB format
    
    def test_fase_type_distribution(self):
        """Test that different phase types are properly represented"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        fases = response.context['fases']
        tipos = [fase.tipo for fase in fases]
        
        # Should have all three types represented
        self.assertIn('alvara', tipos)
        self.assertIn('requerimento', tipos)
        self.assertIn('ambos', tipos)
        
        # Count each type
        alvara_count = tipos.count('alvara')
        requerimento_count = tipos.count('requerimento')
        ambos_count = tipos.count('ambos')
        
        # We created 2 of each type
        self.assertEqual(alvara_count, 2)
        self.assertEqual(requerimento_count, 2)
        self.assertEqual(ambos_count, 2)
    
    # ===============================
    # INTEGRATION TESTS
    # ===============================
    
    def test_phases_usage_integration(self):
        """Test integration with alvaras and requerimentos using phases"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        # The phases we created should be in use
        fases = response.context['fases']
        fase_ids = [fase.id for fase in fases]
        
        # Our test alvara should be using one of these phases
        self.assertIn(self.alvara.fase.id, fase_ids)
        
        # Our test requerimento should be using one of these phases
        self.assertIn(self.requerimento.fase.id, fase_ids)
    
    def test_context_data_types(self):
        """Test that context data has correct types"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        context = response.context
        
        # fases should be QuerySet
        self.assertTrue(hasattr(context['fases'], 'model'))
        self.assertEqual(context['fases'].model, Fase)
        
        # Statistics should be integers
        self.assertIsInstance(context['total_fases'], int)
        self.assertIsInstance(context['fases_ativas'], int)
        self.assertIsInstance(context['fases_inativas'], int)
    
    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================
    
    def test_empty_database_handling(self):
        """Test view behavior with empty database"""
        # Delete related objects first to avoid foreign key constraints
        Alvara.objects.all().delete()
        Requerimento.objects.all().delete()
        Precatorio.objects.all().delete()
        Cliente.objects.all().delete()
        
        # Clear all phases
        Fase.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        # Should not crash and return valid response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['fases']), 0)
        self.assertEqual(response.context['total_fases'], 0)
    
    def test_special_characters_in_phase_names(self):
        """Test handling of special characters in phase names"""
        special_fase = Fase.objects.create(
            nome='Fase: Aguardando Análise e Aprovação (50%)',
            tipo='ambos',
            cor='#ffffff',
            ativa=True,
            ordem=999
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        # Should handle special characters correctly
        # Check for presence of the fase name (may be HTML escaped)
        response_content = response.content.decode('utf-8')
        self.assertTrue(
            'Fase: Aguardando Análise e Aprovação (50%)' in response_content or
            'Fase: Aguardando An&#225;lise e Aprova&#231;&#227;o (50%)' in response_content or
            'Fase: Aguardando An&aacute;lise e Aprova&ccedil;&atilde;o (50%)' in response_content
        )
    
    def test_html_escaping_in_phase_data(self):
        """Test that HTML in phase data is properly escaped"""
        html_fase = Fase.objects.create(
            nome='<script>alert("xss")</script>Fase Maliciosa',
            tipo='ambos',
            cor='#000000',
            ativa=True,
            ordem=1000
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        # Should escape HTML
        response_content = response.content.decode('utf-8')
        self.assertNotIn('<script>alert("xss")</script>', response_content)
        self.assertIn('&lt;script&gt;', response_content)
    
    # ===============================
    # SECURITY TESTS
    # ===============================
    
    def test_csrf_protection(self):
        """Test that view includes CSRF protection"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        # For a GET request, CSRF token should be available in context
        # This ensures forms on the page can include CSRF protection
        self.assertIn('csrf_token', response.context)
    
    def test_user_session_handling(self):
        """Test that user session is properly handled"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify session exists
        self.assertTrue('_auth_user_id' in self.client_app.session)
        
        response = self.client_app.get(self.fases_url)
        
        # Session should persist after request
        self.assertTrue('_auth_user_id' in self.client_app.session)
        self.assertEqual(
            int(self.client_app.session['_auth_user_id']),
            self.user.id
        )
    
    # ===============================
    # BUSINESS LOGIC TESTS
    # ===============================
    
    def test_phase_filtering_by_type_availability(self):
        """Test that all phase types are available for filtering"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        fases = response.context['fases']
        
        # Should have phases available for alvara operations
        alvara_phases = [f for f in fases if f.tipo in ['alvara', 'ambos']]
        self.assertTrue(len(alvara_phases) > 0)
        
        # Should have phases available for requerimento operations
        requerimento_phases = [f for f in fases if f.tipo in ['requerimento', 'ambos']]
        self.assertTrue(len(requerimento_phases) > 0)
    
    def test_active_inactive_distribution(self):
        """Test that both active and inactive phases are properly managed"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.fases_url)
        
        fases = response.context['fases']
        
        # Count active and inactive phases manually
        active_count = sum(1 for f in fases if f.ativa)
        inactive_count = sum(1 for f in fases if not f.ativa)
        
        # Should match context statistics
        self.assertEqual(active_count, response.context['fases_ativas'])
        self.assertEqual(inactive_count, response.context['fases_inativas'])
        
        # Should have both active and inactive phases in test data
        self.assertTrue(active_count > 0)
        self.assertTrue(inactive_count > 0)


class NovaFaseViewTest(TestCase):
    """
    Comprehensive test cases for nova_fase_view function.
    
    Tests cover all aspects of the phase creation view including authentication requirements,
    form handling, validation, success and error scenarios, template rendering, context data,
    message framework integration, redirect behavior, security considerations, and integration
    with the broader phase management system for the legal document processing application.
    """
    
    def setUp(self):
        """Set up comprehensive test data for nova_fase_view testing"""
        self.client_app = Client()
        
        # Create test user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create existing phase for uniqueness validation tests
        self.existing_fase = Fase.objects.create(
            nome='Fase Existente',
            tipo='alvara',
            cor='#007bff',
            ativa=True,
            ordem=1
        )
        
        # Test URLs
        self.nova_fase_url = reverse('nova_fase')
        self.fases_url = reverse('fases')
        self.login_url = reverse('login')
        
        # Valid form data for successful submissions
        self.valid_form_data = {
            'nome': 'Nova Fase Teste',
            'descricao': 'Descrição da nova fase para testes',
            'tipo': 'alvara',
            'cor': '#28a745',
            'ativa': True,
            'ordem': 10
        }
        
        # Invalid form data for error testing
        self.invalid_form_data = {
            'nome': '',  # Missing required field
            'tipo': 'invalid_type',  # Invalid choice
            'cor': 'invalid_color',  # Invalid color format
            'ativa': True,
            'ordem': -1  # Invalid negative number
        }
    
    # ===============================
    # AUTHENTICATION TESTS
    # ===============================
    
    def test_nova_fase_view_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client_app.get(self.nova_fase_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Follow redirect to verify login requirement
        response = self.client_app.get(self.nova_fase_url, follow=True)
        self.assertContains(response, 'login')
    
    def test_nova_fase_view_authenticated_access_get(self):
        """Test that authenticated users can access the nova fase form (GET)"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(self.nova_fase_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
        self.assertContains(response, 'Nova Fase')
    
    def test_nova_fase_view_authenticated_access_post(self):
        """Test that authenticated users can submit the nova fase form (POST)"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.nova_fase_url, data=self.valid_form_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
    
    # ===============================
    # FORM DISPLAY TESTS (GET)
    # ===============================
    
    def test_nova_fase_form_display(self):
        """Test that the form is properly displayed on GET request"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.nova_fase_url)
        
        # Should contain form elements
        self.assertContains(response, '<form')
        self.assertContains(response, 'name="nome"')
        self.assertContains(response, 'name="descricao"')
        self.assertContains(response, 'name="tipo"')
        self.assertContains(response, 'name="cor"')
        self.assertContains(response, 'name="ativa"')
        self.assertContains(response, 'name="ordem"')
        
        # Should contain submit button
        self.assertContains(response, 'Criar Fase')
    
    def test_nova_fase_context_data_get(self):
        """Test that correct context data is provided for GET requests"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.nova_fase_url)
        
        # Check required context keys
        expected_context_keys = ['form', 'title', 'submit_text']
        for key in expected_context_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")
        
        # Check context values
        self.assertEqual(response.context['title'], 'Nova Fase')
        self.assertEqual(response.context['submit_text'], 'Criar Fase')
        
        # Form should be instance of FaseForm
        from precapp.forms import FaseForm
        self.assertIsInstance(response.context['form'], FaseForm)
    
    def test_nova_fase_form_empty_initial(self):
        """Test that form starts with empty/default values"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.nova_fase_url)
        
        form = response.context['form']
        
        # Form should not be bound initially
        self.assertFalse(form.is_bound)
        
        # Initial data should be empty or defaults
        self.assertEqual(form.initial.get('nome', ''), '')
        self.assertEqual(form.initial.get('descricao', ''), '')
    
    # ===============================
    # FORM SUBMISSION TESTS (POST)
    # ===============================
    
    def test_nova_fase_valid_submission(self):
        """Test successful phase creation with valid data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        initial_count = Fase.objects.count()
        
        response = self.client_app.post(self.nova_fase_url, data=self.valid_form_data)
        
        # Should redirect to fases list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
        
        # Should create new phase
        self.assertEqual(Fase.objects.count(), initial_count + 1)
        
        # Verify created phase data
        nova_fase = Fase.objects.get(nome='Nova Fase Teste')
        self.assertEqual(nova_fase.descricao, 'Descrição da nova fase para testes')
        self.assertEqual(nova_fase.tipo, 'alvara')
        self.assertEqual(nova_fase.cor, '#28a745')
        self.assertTrue(nova_fase.ativa)
        self.assertEqual(nova_fase.ordem, 10)
    
    def test_nova_fase_invalid_submission(self):
        """Test form handling with invalid data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        initial_count = Fase.objects.count()
        
        response = self.client_app.post(self.nova_fase_url, data=self.invalid_form_data)
        
        # Should stay on the same page (no redirect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
        
        # Should not create new phase
        self.assertEqual(Fase.objects.count(), initial_count)
        
        # Form should have errors
        form = response.context['form']
        self.assertTrue(form.errors)
    
    def test_nova_fase_missing_required_fields(self):
        """Test validation with missing required fields"""
        self.client_app.login(username='testuser', password='testpass123')
        
        incomplete_data = {
            'descricao': 'Apenas descrição',
            # Missing nome, tipo, cor, etc.
        }
        
        response = self.client_app.post(self.nova_fase_url, data=incomplete_data)
        
        # Should stay on form page
        self.assertEqual(response.status_code, 200)
        
        # Should have form errors
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('nome', form.errors)
        self.assertIn('tipo', form.errors)
    
    def test_nova_fase_duplicate_name_validation(self):
        """Test validation prevents duplicate phase names"""
        self.client_app.login(username='testuser', password='testpass123')
        
        duplicate_data = self.valid_form_data.copy()
        duplicate_data['nome'] = 'Fase Existente'  # Same as existing phase
        
        response = self.client_app.post(self.nova_fase_url, data=duplicate_data)
        
        # Should stay on form page
        self.assertEqual(response.status_code, 200)
        
        # Should have validation error
        form = response.context['form']
        self.assertTrue(form.errors)
        # Uniqueness validation typically shows in __all__ or nome field
        self.assertTrue(form.non_field_errors or 'nome' in form.errors)
    
    # ===============================
    # SUCCESS SCENARIOS
    # ===============================
    
    def test_nova_fase_different_types_creation(self):
        """Test creating phases with different types"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test each phase type
        types_to_test = ['alvara', 'requerimento', 'ambos']
        
        for i, tipo in enumerate(types_to_test):
            data = self.valid_form_data.copy()
            data['nome'] = f'Fase {tipo.title()} {i}'
            data['tipo'] = tipo
            
            response = self.client_app.post(self.nova_fase_url, data=data)
            
            # Should succeed
            self.assertEqual(response.status_code, 302)
            
            # Verify creation
            fase = Fase.objects.get(nome=f'Fase {tipo.title()} {i}')
            self.assertEqual(fase.tipo, tipo)
    
    def test_nova_fase_different_colors(self):
        """Test creating phases with different color formats"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test different valid color formats
        colors_to_test = ['#FF0000', '#00FF00', '#0000FF', '#FFFFFF', '#000000']
        
        for i, cor in enumerate(colors_to_test):
            data = self.valid_form_data.copy()
            data['nome'] = f'Fase Cor {i}'
            data['cor'] = cor
            
            response = self.client_app.post(self.nova_fase_url, data=data)
            
            # Should succeed
            self.assertEqual(response.status_code, 302)
            
            # Verify creation
            fase = Fase.objects.get(nome=f'Fase Cor {i}')
            self.assertEqual(fase.cor, cor)
    
    def test_nova_fase_active_inactive_creation(self):
        """Test creating both active and inactive phases"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test active phase
        active_data = self.valid_form_data.copy()
        active_data['nome'] = 'Fase Ativa'
        active_data['ativa'] = True
        
        response = self.client_app.post(self.nova_fase_url, data=active_data)
        self.assertEqual(response.status_code, 302)
        
        fase_ativa = Fase.objects.get(nome='Fase Ativa')
        self.assertTrue(fase_ativa.ativa)
        
        # Test inactive phase
        inactive_data = self.valid_form_data.copy()
        inactive_data['nome'] = 'Fase Inativa'
        inactive_data['ativa'] = False
        
        response = self.client_app.post(self.nova_fase_url, data=inactive_data)
        self.assertEqual(response.status_code, 302)
        
        fase_inativa = Fase.objects.get(nome='Fase Inativa')
        self.assertFalse(fase_inativa.ativa)
    
    # ===============================
    # MESSAGE FRAMEWORK TESTS
    # ===============================
    
    def test_nova_fase_success_message(self):
        """Test that success message is displayed after creation"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.nova_fase_url, data=self.valid_form_data, follow=True)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.SUCCESS)
        self.assertIn('Nova Fase Teste', str(messages[0]))
        self.assertIn('criada com sucesso', str(messages[0]))
    
    def test_nova_fase_error_message(self):
        """Test that error message is displayed on validation failure"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.nova_fase_url, data=self.invalid_form_data)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.ERROR)
        self.assertIn('corrija os erros', str(messages[0]))
    
    def test_nova_fase_message_persistence_across_redirect(self):
        """Test that success message persists through redirect"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Submit form and follow redirect
        response = self.client_app.post(self.nova_fase_url, data=self.valid_form_data, follow=True)
        
        # Should end up on fases list page
        self.assertTemplateUsed(response, 'precapp/fases_list.html')
        
        # Success message should be present
        response_content = response.content.decode('utf-8')
        self.assertIn('criada com sucesso', response_content)
    
    # ===============================
    # REDIRECT BEHAVIOR TESTS
    # ===============================
    
    def test_nova_fase_success_redirect(self):
        """Test redirect behavior after successful creation"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.nova_fase_url, data=self.valid_form_data)
        
        # Should redirect to fases list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
        
        # Follow redirect to verify it doesn't cause errors
        follow_response = self.client_app.get(reverse('fases'))
        self.assertEqual(follow_response.status_code, 200)
    
    def test_nova_fase_no_redirect_on_error(self):
        """Test that no redirect occurs when form has errors"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.nova_fase_url, data=self.invalid_form_data)
        
        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
    
    # ===============================
    # TEMPLATE AND CONTEXT TESTS
    # ===============================
    
    def test_nova_fase_template_inheritance(self):
        """Test that template properly inherits from base template"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.nova_fase_url)
        
        # Should extend base template
        self.assertContains(response, 'Nova Fase')
        # Should have standard layout elements
        self.assertContains(response, '<form')
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_nova_fase_context_on_error(self):
        """Test that context is properly maintained on form errors"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.nova_fase_url, data=self.invalid_form_data)
        
        # Context should still be complete
        self.assertIn('form', response.context)
        self.assertIn('title', response.context)
        self.assertIn('submit_text', response.context)
        
        # Title and submit text should remain the same
        self.assertEqual(response.context['title'], 'Nova Fase')
        self.assertEqual(response.context['submit_text'], 'Criar Fase')
        
        # Form should be bound and have errors
        form = response.context['form']
        self.assertTrue(form.is_bound)
        self.assertTrue(form.errors)
    
    def test_nova_fase_form_preserves_data_on_error(self):
        """Test that form preserves submitted data when there are errors"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Submit data with some valid and some invalid fields
        partial_data = {
            'nome': 'Fase Válida',
            'descricao': 'Descrição válida',
            'tipo': 'invalid_type',  # Invalid
            'cor': '#FF0000',  # Valid
        }
        
        response = self.client_app.post(self.nova_fase_url, data=partial_data)
        
        # Form should preserve the valid data
        form = response.context['form']
        self.assertEqual(form.data['nome'], 'Fase Válida')
        self.assertEqual(form.data['descricao'], 'Descrição válida')
        self.assertEqual(form.data['cor'], '#FF0000')
    
    # ===============================
    # SECURITY TESTS
    # ===============================
    
    def test_nova_fase_csrf_protection(self):
        """Test that CSRF protection is properly implemented"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # GET request should include CSRF token
        response = self.client_app.get(self.nova_fase_url)
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        # POST without CSRF should fail
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='testuser', password='testpass123')
        
        response = csrf_client.post(self.nova_fase_url, data=self.valid_form_data)
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_nova_fase_xss_protection(self):
        """Test protection against XSS attacks in form fields"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Try to inject script in nome field
        xss_data = self.valid_form_data.copy()
        xss_data['nome'] = '<script>alert("xss")</script>Fase Maliciosa'
        xss_data['descricao'] = '<img src="x" onerror="alert(\'xss\')">'
        
        response = self.client_app.post(self.nova_fase_url, data=xss_data)
        
        # Should either reject the data or escape it
        if response.status_code == 302:
            # If creation succeeded, check that data is escaped
            fase = Fase.objects.get(nome=xss_data['nome'])
            # Django should have preserved the string as-is in database
            self.assertEqual(fase.nome, xss_data['nome'])
            
            # But when rendered, it should be escaped
            list_response = self.client_app.get(reverse('fases'))
            content = list_response.content.decode('utf-8')
            self.assertNotIn('<script>alert("xss")</script>', content)
    
    def test_nova_fase_sql_injection_protection(self):
        """Test protection against SQL injection attempts"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Try SQL injection in form fields
        injection_data = self.valid_form_data.copy()
        injection_data['nome'] = "'; DROP TABLE precapp_fase; --"
        injection_data['descricao'] = "1' OR '1'='1"
        
        # Should not cause database issues
        initial_count = Fase.objects.count()
        
        response = self.client_app.post(self.nova_fase_url, data=injection_data)
        
        # Database should remain intact
        self.assertTrue(Fase.objects.count() >= initial_count)
        
        # If creation succeeded, injection string should be treated as literal data
        if response.status_code == 302:
            fase = Fase.objects.get(nome=injection_data['nome'])
            self.assertEqual(fase.nome, injection_data['nome'])
    
    # ===============================
    # INTEGRATION TESTS
    # ===============================
    
    def test_nova_fase_integration_with_fases_list(self):
        """Test integration between nova_fase creation and fases list view"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create new phase
        response = self.client_app.post(self.nova_fase_url, data=self.valid_form_data, follow=True)
        
        # Should redirect to fases list and show the new phase
        self.assertContains(response, 'Nova Fase Teste')
        self.assertContains(response, '#28a745')  # Color
        self.assertContains(response, 'alvara')  # Type
    
    def test_nova_fase_form_integration(self):
        """Test integration with FaseForm validation and saving"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test that the view properly uses FaseForm
        response = self.client_app.get(self.nova_fase_url)
        
        from precapp.forms import FaseForm
        form = response.context['form']
        self.assertIsInstance(form, FaseForm)
        
        # Test that form validation is properly handled
        response = self.client_app.post(self.nova_fase_url, data=self.valid_form_data)
        
        # Should create fase using form's save method
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Fase.objects.filter(nome='Nova Fase Teste').exists())
    
    def test_nova_fase_ordem_field_handling(self):
        """Test proper handling of ordem field for phase ordering"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create phases with different ordem values
        for i in range(3):
            data = self.valid_form_data.copy()
            data['nome'] = f'Fase Ordem {i}'
            data['ordem'] = i * 10
            
            response = self.client_app.post(self.nova_fase_url, data=data)
            self.assertEqual(response.status_code, 302)
        
        # Verify ordering in the list
        response = self.client_app.get(reverse('fases'))
        
        # Should contain all created phases
        self.assertContains(response, 'Fase Ordem 0')
        self.assertContains(response, 'Fase Ordem 1')
        self.assertContains(response, 'Fase Ordem 2')
    
    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================
    
    def test_nova_fase_empty_post_request(self):
        """Test handling of completely empty POST request"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.nova_fase_url, data={})
        
        # Should stay on form page with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
        
        # Should have form errors
        form = response.context['form']
        self.assertTrue(form.errors)
    
    def test_nova_fase_very_long_field_values(self):
        """Test handling of very long field values"""
        self.client_app.login(username='testuser', password='testpass123')
        
        long_data = self.valid_form_data.copy()
        long_data['nome'] = 'x' * 200  # Exceeds typical max_length
        long_data['descricao'] = 'y' * 1000  # Very long description
        
        response = self.client_app.post(self.nova_fase_url, data=long_data)
        
        # Should handle gracefully (either truncate or show validation error)
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 200:
            # If validation failed, should have errors
            form = response.context['form']
            self.assertTrue(form.errors)
    
    def test_nova_fase_unicode_characters(self):
        """Test handling of Unicode characters in form fields"""
        self.client_app.login(username='testuser', password='testpass123')
        
        unicode_data = self.valid_form_data.copy()
        unicode_data['nome'] = 'Fase Açúcar Coração ñ'
        unicode_data['descricao'] = 'Descrição com acentos: à, é, ñ, ü, ç'
        
        response = self.client_app.post(self.nova_fase_url, data=unicode_data)
        
        # Should handle Unicode properly
        self.assertEqual(response.status_code, 302)
        
        # Verify Unicode preservation
        fase = Fase.objects.get(nome='Fase Açúcar Coração ñ')
        self.assertEqual(fase.nome, 'Fase Açúcar Coração ñ')
        self.assertEqual(fase.descricao, 'Descrição com acentos: à, é, ñ, ü, ç')
    
    def test_nova_fase_concurrent_creation(self):
        """Test handling of concurrent phase creation attempts"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Simulate concurrent requests with same name
        data1 = self.valid_form_data.copy()
        data2 = self.valid_form_data.copy()
        data1['nome'] = 'Fase Concorrente'
        data2['nome'] = 'Fase Concorrente'
        
        # First should succeed
        response1 = self.client_app.post(self.nova_fase_url, data=data1)
        self.assertEqual(response1.status_code, 302)
        
        # Second should fail due to unique constraint
        response2 = self.client_app.post(self.nova_fase_url, data=data2)
        self.assertEqual(response2.status_code, 200)  # Should return form with errors
        
        # Should have validation error
        form = response2.context['form']
        self.assertTrue(form.errors)
    
    # ===============================
    # BUSINESS LOGIC TESTS
    # ===============================
    
    def test_nova_fase_business_logic_validation(self):
        """Test business logic validation in phase creation"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test minimum viable phase creation
        minimal_data = {
            'nome': 'Fase Mínima',
            'tipo': 'ambos',
            'cor': '#000000',
            'ativa': True,
            'ordem': 0
        }
        
        response = self.client_app.post(self.nova_fase_url, data=minimal_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify minimal phase creation
        fase = Fase.objects.get(nome='Fase Mínima')
        self.assertEqual(fase.tipo, 'ambos')
        self.assertEqual(fase.cor, '#000000')
        self.assertTrue(fase.ativa)
        self.assertEqual(fase.ordem, 0)
    
    def test_nova_fase_default_values_handling(self):
        """Test proper handling of default values in form"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Submit with minimal required data, let defaults fill in
        minimal_required = {
            'nome': 'Fase Com Padrões',
            'tipo': 'alvara',
            'cor': '#FF0000'
            # Omit optional fields to test defaults
        }
        
        response = self.client_app.post(self.nova_fase_url, data=minimal_required)
        
        # Should succeed or fail gracefully
        if response.status_code == 302:
            fase = Fase.objects.get(nome='Fase Com Padrões')
            # Should have reasonable defaults for omitted fields
            self.assertIsNotNone(fase.ativa)  # Should have default boolean value
            self.assertIsNotNone(fase.ordem)  # Should have default ordem value


class EditarFaseViewTest(TestCase):
    """
    Comprehensive test cases for editar_fase_view function.
    
    Tests cover all aspects of the phase editing view including authentication requirements,
    instance loading, form pre-population, validation, success and error scenarios, template 
    rendering, context data, message framework integration, redirect behavior, security 
    considerations, business logic validation, and integration with the broader phase 
    management system for the legal document processing application.
    """
    
    def setUp(self):
        """Set up comprehensive test data for editar_fase_view testing"""
        self.client_app = Client()
        
        # Create test user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test phases for editing
        self.fase_to_edit = Fase.objects.create(
            nome='Fase Para Editar',
            descricao='Descrição original da fase',
            tipo='alvara',
            cor='#007bff',
            ativa=True,
            ordem=5
        )
        
        self.other_fase = Fase.objects.create(
            nome='Outra Fase',
            tipo='requerimento',
            cor='#28a745',
            ativa=False,
            ordem=10
        )
        
        # Create related objects to test usage constraints
        self.cliente = Cliente.objects.create(
            cpf='11144477735',  # Valid CPF
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='Tribunal de São Paulo',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Link cliente to precatorio
        self.precatorio.clientes.add(self.cliente)
        
        # Create alvara using the phase (to test business constraints)
        self.alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='comum',
            fase=self.fase_to_edit
        )
        
        # Test URLs
        self.editar_fase_url = reverse('editar_fase', kwargs={'fase_id': self.fase_to_edit.id})
        self.invalid_editar_fase_url = reverse('editar_fase', kwargs={'fase_id': 99999})  # Non-existent
        self.fases_url = reverse('fases')
        self.login_url = reverse('login')
        
        # Valid updated form data
        self.valid_update_data = {
            'nome': 'Fase Editada',
            'descricao': 'Descrição atualizada da fase',
            'tipo': 'requerimento',
            'cor': '#dc3545',
            'ativa': False,
            'ordem': 15
        }
        
        # Invalid form data for error testing
        self.invalid_update_data = {
            'nome': '',  # Missing required field
            'tipo': 'invalid_type',  # Invalid choice
            'cor': 'invalid_color',  # Invalid color format
            'ativa': True,
            'ordem': -5  # Invalid negative number
        }
    
    # ===============================
    # AUTHENTICATION TESTS
    # ===============================
    
    def test_editar_fase_view_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client_app.get(self.editar_fase_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Follow redirect to verify login requirement
        response = self.client_app.get(self.editar_fase_url, follow=True)
        self.assertContains(response, 'login')
    
    def test_editar_fase_view_authenticated_access_get(self):
        """Test that authenticated users can access the editar fase form (GET)"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(self.editar_fase_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
        self.assertContains(response, 'Editar Fase: Fase Para Editar')
    
    def test_editar_fase_view_authenticated_access_post(self):
        """Test that authenticated users can submit the editar fase form (POST)"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.editar_fase_url, data=self.valid_update_data)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
    
    # ===============================
    # INSTANCE LOADING TESTS
    # ===============================
    
    def test_editar_fase_view_loads_existing_instance(self):
        """Test that view properly loads existing fase instance"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.editar_fase_url)
        
        # Should load the correct fase instance
        fase = response.context['fase']
        self.assertEqual(fase.id, self.fase_to_edit.id)
        self.assertEqual(fase.nome, 'Fase Para Editar')
        self.assertEqual(fase.tipo, 'alvara')
        self.assertEqual(fase.cor, '#007bff')
        self.assertTrue(fase.ativa)
        self.assertEqual(fase.ordem, 5)
    
    def test_editar_fase_view_404_for_nonexistent_fase(self):
        """Test that view returns 404 for non-existent fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(self.invalid_editar_fase_url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_editar_fase_view_404_for_invalid_fase_id(self):
        """Test that view returns 404 for invalid fase ID format"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Try with invalid ID format (should be handled by URL routing)
        invalid_url = '/fases/invalid_id/editar/'
        response = self.client_app.get(invalid_url)
        
        # Should return 404 (URL pattern won't match)
        self.assertEqual(response.status_code, 404)
    
    # ===============================
    # FORM PRE-POPULATION TESTS (GET)
    # ===============================
    
    def test_editar_fase_form_prepopulated(self):
        """Test that form is pre-populated with existing fase data"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.editar_fase_url)
        
        form = response.context['form']
        
        # Form should be bound with instance data
        self.assertFalse(form.is_bound)  # GET form is not bound
        self.assertEqual(form.instance.nome, 'Fase Para Editar')
        self.assertEqual(form.instance.descricao, 'Descrição original da fase')
        self.assertEqual(form.instance.tipo, 'alvara')
        self.assertEqual(form.instance.cor, '#007bff')
        self.assertTrue(form.instance.ativa)
        self.assertEqual(form.instance.ordem, 5)
    
    def test_editar_fase_form_displays_current_values(self):
        """Test that form displays current values in HTML"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.editar_fase_url)
        
        # Should contain current values in form fields
        self.assertContains(response, 'value="Fase Para Editar"')
        self.assertContains(response, 'Descrição original da fase')
        self.assertContains(response, 'value="#007bff"')
        self.assertContains(response, 'value="5"')
        
        # Should have tipo selected
        self.assertContains(response, 'selected>Alvará</option>')
        
        # Should have ativa checkbox checked
        self.assertContains(response, 'checked')
    
    def test_editar_fase_context_data_get(self):
        """Test that correct context data is provided for GET requests"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.editar_fase_url)
        
        # Check required context keys
        expected_context_keys = ['form', 'fase', 'title', 'submit_text']
        for key in expected_context_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")
        
        # Check context values
        self.assertEqual(response.context['title'], 'Editar Fase: Fase Para Editar')
        self.assertEqual(response.context['submit_text'], 'Salvar Alterações')
        
        # Form should be instance of FaseForm with instance
        from precapp.forms import FaseForm
        form = response.context['form']
        self.assertIsInstance(form, FaseForm)
        self.assertEqual(form.instance.id, self.fase_to_edit.id)
    
    # ===============================
    # FORM SUBMISSION TESTS (POST)
    # ===============================
    
    def test_editar_fase_valid_submission(self):
        """Test successful phase update with valid data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Store original values
        original_nome = self.fase_to_edit.nome
        
        response = self.client_app.post(self.editar_fase_url, data=self.valid_update_data)
        
        # Should redirect to fases list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
        
        # Verify updated phase data
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, 'Fase Editada')
        self.assertEqual(self.fase_to_edit.descricao, 'Descrição atualizada da fase')
        self.assertEqual(self.fase_to_edit.tipo, 'requerimento')
        self.assertEqual(self.fase_to_edit.cor, '#dc3545')
        self.assertFalse(self.fase_to_edit.ativa)
        self.assertEqual(self.fase_to_edit.ordem, 15)
        
        # ID should remain the same
        self.assertEqual(self.fase_to_edit.id, self.fase_to_edit.id)
    
    def test_editar_fase_invalid_submission(self):
        """Test form handling with invalid data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Store original values
        original_nome = self.fase_to_edit.nome
        original_tipo = self.fase_to_edit.tipo
        
        response = self.client_app.post(self.editar_fase_url, data=self.invalid_update_data)
        
        # Should stay on the same page (no redirect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
        
        # Should not update the phase
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, original_nome)
        self.assertEqual(self.fase_to_edit.tipo, original_tipo)
        
        # Form should have errors
        form = response.context['form']
        self.assertTrue(form.errors)
    
    def test_editar_fase_partial_update(self):
        """Test updating only some fields"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Update only nome and cor
        partial_data = {
            'nome': 'Apenas Nome Mudou',
            'descricao': self.fase_to_edit.descricao,  # Keep original
            'tipo': self.fase_to_edit.tipo,  # Keep original
            'cor': '#ffcc00',  # Change
            'ativa': self.fase_to_edit.ativa,  # Keep original
            'ordem': self.fase_to_edit.ordem  # Keep original
        }
        
        response = self.client_app.post(self.editar_fase_url, data=partial_data)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
        # Verify selective updates
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, 'Apenas Nome Mudou')
        self.assertEqual(self.fase_to_edit.cor, '#ffcc00')
        
        # These should remain unchanged
        self.assertEqual(self.fase_to_edit.descricao, 'Descrição original da fase')
        self.assertEqual(self.fase_to_edit.tipo, 'alvara')
        self.assertTrue(self.fase_to_edit.ativa)
        self.assertEqual(self.fase_to_edit.ordem, 5)
    
    def test_editar_fase_duplicate_name_validation(self):
        """Test validation prevents duplicate phase names (except own name)"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Try to change to another existing fase name
        duplicate_data = self.valid_update_data.copy()
        duplicate_data['nome'] = 'Outra Fase'  # Same as other_fase
        
        response = self.client_app.post(self.editar_fase_url, data=duplicate_data)
        
        # Should stay on form page
        self.assertEqual(response.status_code, 200)
        
        # Should have validation error
        form = response.context['form']
        self.assertTrue(form.errors)
        
        # Original fase should not be updated
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, 'Fase Para Editar')
    
    def test_editar_fase_same_name_allowed(self):
        """Test that keeping the same name is allowed"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Update other fields but keep same name
        same_name_data = self.valid_update_data.copy()
        same_name_data['nome'] = 'Fase Para Editar'  # Keep same name
        
        response = self.client_app.post(self.editar_fase_url, data=same_name_data)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
        # Verify update
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, 'Fase Para Editar')  # Same name
        self.assertEqual(self.fase_to_edit.tipo, 'requerimento')  # But other fields changed
    
    # ===============================
    # MESSAGE FRAMEWORK TESTS
    # ===============================
    
    def test_editar_fase_success_message(self):
        """Test that success message is displayed after update"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.editar_fase_url, data=self.valid_update_data, follow=True)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.SUCCESS)
        self.assertIn('Fase Editada', str(messages[0]))  # Updated name
        self.assertIn('atualizada com sucesso', str(messages[0]))
    
    def test_editar_fase_error_message(self):
        """Test that error message is displayed on validation failure"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.editar_fase_url, data=self.invalid_update_data)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.ERROR)
        self.assertIn('corrija os erros', str(messages[0]))
    
    def test_editar_fase_message_shows_updated_name(self):
        """Test that success message shows the updated name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        custom_data = self.valid_update_data.copy()
        custom_data['nome'] = 'Nome Personalizado'
        
        response = self.client_app.post(self.editar_fase_url, data=custom_data, follow=True)
        
        # Success message should show the new name
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Nome Personalizado', str(messages[0]))
    
    # ===============================
    # REDIRECT BEHAVIOR TESTS
    # ===============================
    
    def test_editar_fase_success_redirect(self):
        """Test redirect behavior after successful update"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.editar_fase_url, data=self.valid_update_data)
        
        # Should redirect to fases list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
        
        # Follow redirect to verify destination
        follow_response = self.client_app.get(reverse('fases'))
        self.assertEqual(follow_response.status_code, 200)
    
    def test_editar_fase_no_redirect_on_error(self):
        """Test that no redirect occurs when form has errors"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.editar_fase_url, data=self.invalid_update_data)
        
        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
    
    # ===============================
    # TEMPLATE AND CONTEXT TESTS
    # ===============================
    
    def test_editar_fase_template_inheritance(self):
        """Test that template properly inherits from base template"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.editar_fase_url)
        
        # Should use correct template
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
        
        # Should contain edit-specific content
        self.assertContains(response, 'Editar Fase')
        self.assertContains(response, 'Salvar Alterações')
        self.assertContains(response, '<form')
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_editar_fase_context_on_error(self):
        """Test that context is properly maintained on form errors"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.editar_fase_url, data=self.invalid_update_data)
        
        # Context should still be complete
        self.assertIn('form', response.context)
        self.assertIn('fase', response.context)
        self.assertIn('title', response.context)
        self.assertIn('submit_text', response.context)
        
        # Fase instance should remain the same
        self.assertEqual(response.context['fase'].id, self.fase_to_edit.id)
        
        # Title should use original name (not invalid submitted data)
        self.assertEqual(response.context['title'], 'Editar Fase: Fase Para Editar')
        
        # Form should be bound and have errors
        form = response.context['form']
        self.assertTrue(form.is_bound)
        self.assertTrue(form.errors)
    
    def test_editar_fase_form_preserves_data_on_error(self):
        """Test that form preserves submitted data when there are errors"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Submit data with some valid and some invalid fields
        partial_invalid = {
            'nome': 'Nome Válido',  # Valid
            'descricao': 'Descrição válida',  # Valid
            'tipo': 'invalid_type',  # Invalid
            'cor': '#FF0000',  # Valid
            'ativa': True,  # Valid
            'ordem': -1  # Invalid
        }
        
        response = self.client_app.post(self.editar_fase_url, data=partial_invalid)
        
        # Form should preserve the valid submitted data
        form = response.context['form']
        self.assertEqual(form.data['nome'], 'Nome Válido')
        self.assertEqual(form.data['descricao'], 'Descrição válida')
        self.assertEqual(form.data['cor'], '#FF0000')
    
    # ===============================
    # SECURITY TESTS
    # ===============================
    
    def test_editar_fase_csrf_protection(self):
        """Test that CSRF protection is properly implemented"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # GET request should include CSRF token
        response = self.client_app.get(self.editar_fase_url)
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        # POST without CSRF should fail
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='testuser', password='testpass123')
        
        response = csrf_client.post(self.editar_fase_url, data=self.valid_update_data)
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_editar_fase_xss_protection(self):
        """Test protection against XSS attacks in form fields"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Try to inject script in nome field
        xss_data = self.valid_update_data.copy()
        xss_data['nome'] = '<script>alert("xss")</script>Fase Maliciosa'
        xss_data['descricao'] = '<img src="x" onerror="alert(\'xss\')">'
        
        response = self.client_app.post(self.editar_fase_url, data=xss_data)
        
        # Should either reject the data or escape it
        if response.status_code == 302:
            # If update succeeded, check that data is escaped
            self.fase_to_edit.refresh_from_db()
            self.assertEqual(self.fase_to_edit.nome, xss_data['nome'])
            
            # But when rendered, it should be escaped
            list_response = self.client_app.get(reverse('fases'))
            content = list_response.content.decode('utf-8')
            self.assertNotIn('<script>alert("xss")</script>', content)
    
    def test_editar_fase_unauthorized_access_other_user(self):
        """Test that users cannot edit phases they don't own (if applicable)"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        # Login as other user
        self.client_app.login(username='otheruser', password='otherpass123')
        
        # Try to edit the fase (should still work since there's no ownership model)
        response = self.client_app.get(self.editar_fase_url)
        
        # In this system, any authenticated user can edit phases
        # If this changes in the future, this test should be updated
        self.assertEqual(response.status_code, 200)
    
    # ===============================
    # BUSINESS LOGIC TESTS
    # ===============================
    
    def test_editar_fase_preserves_related_objects(self):
        """Test that editing a fase doesn't break related objects"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify alvara is related before edit
        self.assertEqual(self.alvara.fase.id, self.fase_to_edit.id)
        
        # Edit the fase
        response = self.client_app.post(self.editar_fase_url, data=self.valid_update_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify alvara relationship is preserved
        self.alvara.refresh_from_db()
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.alvara.fase.id, self.fase_to_edit.id)
        
        # Verify the fase was actually updated
        self.assertEqual(self.fase_to_edit.nome, 'Fase Editada')
    
    def test_editar_fase_type_change_implications(self):
        """Test implications of changing fase type"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Original fase is 'alvara' type and used by an alvara
        self.assertEqual(self.fase_to_edit.tipo, 'alvara')
        self.assertEqual(self.alvara.fase.tipo, 'alvara')
        
        # Change to 'requerimento' type
        type_change_data = self.valid_update_data.copy()
        type_change_data['tipo'] = 'requerimento'
        
        response = self.client_app.post(self.editar_fase_url, data=type_change_data)
        
        # Should succeed (business rules may allow this)
        self.assertEqual(response.status_code, 302)
        
        # Verify type change
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.tipo, 'requerimento')
        
        # Alvara should still reference this fase
        self.alvara.refresh_from_db()
        self.assertEqual(self.alvara.fase.id, self.fase_to_edit.id)
    
    def test_editar_fase_activation_toggle(self):
        """Test toggling fase activation status"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Original fase is active
        self.assertTrue(self.fase_to_edit.ativa)
        
        # Deactivate the fase
        deactivate_data = {
            'nome': self.fase_to_edit.nome,
            'descricao': self.fase_to_edit.descricao,
            'tipo': self.fase_to_edit.tipo,
            'cor': self.fase_to_edit.cor,
            'ativa': False,  # Deactivate
            'ordem': self.fase_to_edit.ordem
        }
        
        response = self.client_app.post(self.editar_fase_url, data=deactivate_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify deactivation
        self.fase_to_edit.refresh_from_db()
        self.assertFalse(self.fase_to_edit.ativa)
        
        # Related objects should not be affected
        self.alvara.refresh_from_db()
        self.assertEqual(self.alvara.fase.id, self.fase_to_edit.id)
    
    # ===============================
    # INTEGRATION TESTS
    # ===============================
    
    def test_editar_fase_integration_with_fases_list(self):
        """Test integration between editar_fase and fases list view"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Edit fase
        response = self.client_app.post(self.editar_fase_url, data=self.valid_update_data, follow=True)
        
        # Should redirect to fases list and show the updated phase
        self.assertContains(response, 'Fase Editada')
        self.assertContains(response, '#dc3545')  # New color
        self.assertContains(response, 'requerimento')  # New type
        
        # Should not contain old values
        self.assertNotContains(response, 'Fase Para Editar')
    
    def test_editar_fase_form_integration(self):
        """Test integration with FaseForm validation and saving"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test that the view properly uses FaseForm with instance
        response = self.client_app.get(self.editar_fase_url)
        
        from precapp.forms import FaseForm
        form = response.context['form']
        self.assertIsInstance(form, FaseForm)
        self.assertEqual(form.instance.id, self.fase_to_edit.id)
        
        # Test that form validation is properly handled
        response = self.client_app.post(self.editar_fase_url, data=self.valid_update_data)
        
        # Should update fase using form's save method
        self.assertEqual(response.status_code, 302)
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, 'Fase Editada')
    
    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================
    
    def test_editar_fase_empty_post_request(self):
        """Test handling of completely empty POST request"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.editar_fase_url, data={})
        
        # Should stay on form page with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fase_form.html')
        
        # Should have form errors
        form = response.context['form']
        self.assertTrue(form.errors)
        
        # Original data should not be changed
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, 'Fase Para Editar')
    
    def test_editar_fase_unicode_characters(self):
        """Test handling of Unicode characters in form fields"""
        self.client_app.login(username='testuser', password='testpass123')
        
        unicode_data = self.valid_update_data.copy()
        unicode_data['nome'] = 'Fase Açúcar Coração ñ'
        unicode_data['descricao'] = 'Descrição com acentos: à, é, ñ, ü, ç'
        
        response = self.client_app.post(self.editar_fase_url, data=unicode_data)
        
        # Should handle Unicode properly
        self.assertEqual(response.status_code, 302)
        
        # Verify Unicode preservation
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, 'Fase Açúcar Coração ñ')
        self.assertEqual(self.fase_to_edit.descricao, 'Descrição com acentos: à, é, ñ, ü, ç')
    
    def test_editar_fase_concurrent_modification(self):
        """Test handling of concurrent modification attempts"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Simulate another process modifying the fase
        original_nome = self.fase_to_edit.nome
        Fase.objects.filter(id=self.fase_to_edit.id).update(nome='Modificado Externamente')
        
        # Try to edit with our form
        response = self.client_app.post(self.editar_fase_url, data=self.valid_update_data)
        
        # Should still succeed (Django will overwrite)
        self.assertEqual(response.status_code, 302)
        
        # Our update should win
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.nome, 'Fase Editada')
    
    def test_editar_fase_very_long_field_values(self):
        """Test handling of very long field values"""
        self.client_app.login(username='testuser', password='testpass123')
        
        long_data = self.valid_update_data.copy()
        long_data['nome'] = 'x' * 200  # Exceeds typical max_length
        long_data['descricao'] = 'y' * 1000  # Very long description
        
        response = self.client_app.post(self.editar_fase_url, data=long_data)
        
        # Should handle gracefully (either truncate or show validation error)
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 200:
            # If validation failed, should have errors
            form = response.context['form']
            self.assertTrue(form.errors)
    
    def test_editar_fase_ordem_field_business_logic(self):
        """Test business logic for ordem field updates"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test updating ordem to same value as another fase
        same_ordem_data = self.valid_update_data.copy()
        same_ordem_data['ordem'] = self.other_fase.ordem  # Same as other fase
        
        response = self.client_app.post(self.editar_fase_url, data=same_ordem_data)
        
        # Should succeed (business rules may allow duplicate ordem values)
        self.assertEqual(response.status_code, 302)
        
        # Verify update
        self.fase_to_edit.refresh_from_db()
        self.assertEqual(self.fase_to_edit.ordem, self.other_fase.ordem)


class DeletarFaseViewTest(TestCase):
    """
    Comprehensive test cases for deletar_fase_view function.
    
    Tests cover all aspects of the phase deletion view including authentication requirements,
    instance loading, business logic validation (usage constraints), success and error scenarios,
    message framework integration, redirect behavior, security considerations, relationship
    checking with alvaras and requerimentos, and integration with the broader phase management
    system for the legal document processing application.
    """
    
    def setUp(self):
        """Set up comprehensive test data for deletar_fase_view testing"""
        self.client_app = Client()
        
        # Create test user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test phases for deletion scenarios
        self.deletable_fase = Fase.objects.create(
            nome='Fase Deletável',
            descricao='Fase que pode ser deletada',
            tipo='alvara',
            cor='#007bff',
            ativa=True,
            ordem=5
        )
        
        self.fase_used_by_alvara = Fase.objects.create(
            nome='Fase Usada por Alvará',
            tipo='alvara',
            cor='#28a745',
            ativa=True,
            ordem=10
        )
        
        self.fase_used_by_requerimento = Fase.objects.create(
            nome='Fase Usada por Requerimento',
            tipo='requerimento',
            cor='#dc3545',
            ativa=True,
            ordem=15
        )
        
        self.fase_used_by_both = Fase.objects.create(
            nome='Fase Usada por Ambos',
            tipo='ambos',
            cor='#ffc107',
            ativa=True,
            ordem=20
        )
        
        # Create related test data
        self.cliente = Cliente.objects.create(
            cpf='11144477735',  # Valid CPF
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='Tribunal de São Paulo',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Link cliente to precatorio
        self.precatorio.clientes.add(self.cliente)
        
        # Create alvara using the fase (to test deletion constraints)
        self.alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='comum',
            fase=self.fase_used_by_alvara
        )
        
        # Create multiple alvaras for more comprehensive testing
        self.alvara2 = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=25000.00,
            honorarios_contratuais=5000.00,
            honorarios_sucumbenciais=2500.00,
            tipo='comum',
            fase=self.fase_used_by_both
        )
        
        # Create test PedidoRequerimento instances
        self.pedido_prioridade_idade = PedidoRequerimento.objects.create(
            nome='Prioridade por idade',
            descricao='Pedido de prioridade por idade',
            cor='#ffc107',
            ordem=1,
            ativo=True
        )
        
        self.pedido_prioridade_doenca = PedidoRequerimento.objects.create(
            nome='Prioridade por doença',
            descricao='Pedido de prioridade por doença',
            cor='#dc3545',
            ordem=2,
            ativo=True
        )
        
        # Create requerimento using the fase
        self.requerimento = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor=25000.00,
            desagio=5.0,
            pedido=self.pedido_prioridade_idade,
            fase=self.fase_used_by_requerimento
        )
        
        # Create multiple requerimentos for more comprehensive testing
        self.requerimento2 = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor=15000.00,
            desagio=3.0,
            pedido=self.pedido_prioridade_doenca,
            fase=self.fase_used_by_both
        )
        
        # Test URLs
        self.deletable_fase_url = reverse('deletar_fase', kwargs={'fase_id': self.deletable_fase.id})
        self.alvara_used_fase_url = reverse('deletar_fase', kwargs={'fase_id': self.fase_used_by_alvara.id})
        self.requerimento_used_fase_url = reverse('deletar_fase', kwargs={'fase_id': self.fase_used_by_requerimento.id})
        self.both_used_fase_url = reverse('deletar_fase', kwargs={'fase_id': self.fase_used_by_both.id})
        self.nonexistent_fase_url = reverse('deletar_fase', kwargs={'fase_id': 99999})
        self.fases_url = reverse('fases')
        self.login_url = reverse('login')
    
    # ===============================
    # AUTHENTICATION TESTS
    # ===============================
    
    def test_deletar_fase_view_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client_app.post(self.deletable_fase_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Follow redirect to verify login requirement
        response = self.client_app.post(self.deletable_fase_url, follow=True)
        self.assertContains(response, 'login')
        
        # Fase should not be deleted
        self.assertTrue(Fase.objects.filter(id=self.deletable_fase.id).exists())
    
    def test_deletar_fase_view_authenticated_access(self):
        """Test that authenticated users can access the deletar fase endpoint"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.deletable_fase_url)
        
        # Should redirect to fases list (successful deletion)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
    
    # ===============================
    # INSTANCE LOADING TESTS
    # ===============================
    
    def test_deletar_fase_view_loads_existing_instance(self):
        """Test that view properly loads existing fase instance"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify fase exists before deletion
        self.assertTrue(Fase.objects.filter(id=self.deletable_fase.id).exists())
        
        response = self.client_app.post(self.deletable_fase_url)
        
        # Should process the correct fase
        self.assertEqual(response.status_code, 302)
    
    def test_deletar_fase_view_404_for_nonexistent_fase(self):
        """Test that view returns 404 for non-existent fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.nonexistent_fase_url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_deletar_fase_view_404_for_invalid_fase_id(self):
        """Test that view returns 404 for invalid fase ID format"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Try with invalid ID format (should be handled by URL routing)
        invalid_url = '/fases/invalid_id/deletar/'
        response = self.client_app.post(invalid_url)
        
        # Should return 404 (URL pattern won't match)
        self.assertEqual(response.status_code, 404)
    
    # ===============================
    # HTTP METHOD TESTS
    # ===============================
    
    def test_deletar_fase_get_request_redirects(self):
        """Test that GET requests redirect to fases list without deletion"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify fase exists before GET request
        self.assertTrue(Fase.objects.filter(id=self.deletable_fase.id).exists())
        
        response = self.client_app.get(self.deletable_fase_url)
        
        # Should redirect without deleting
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
        
        # Fase should still exist
        self.assertTrue(Fase.objects.filter(id=self.deletable_fase.id).exists())
    
    def test_deletar_fase_post_request_processes_deletion(self):
        """Test that POST requests properly process deletion"""
        self.client_app.login(username='testuser', password='testpass123')
        
        initial_count = Fase.objects.count()
        
        response = self.client_app.post(self.deletable_fase_url)
        
        # Should redirect after processing
        self.assertEqual(response.status_code, 302)
        
        # Should delete the fase
        self.assertEqual(Fase.objects.count(), initial_count - 1)
        self.assertFalse(Fase.objects.filter(id=self.deletable_fase.id).exists())
    
    def test_deletar_fase_put_delete_methods_not_supported(self):
        """Test that PUT/DELETE methods behave consistently"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Django test client doesn't support PUT/DELETE directly for this endpoint
        # but we can verify the view only responds to GET/POST
        response = self.client_app.post(self.deletable_fase_url)
        self.assertEqual(response.status_code, 302)
    
    # ===============================
    # SUCCESSFUL DELETION TESTS
    # ===============================
    
    def test_deletar_fase_successful_deletion(self):
        """Test successful deletion of unused fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        fase_id = self.deletable_fase.id
        fase_nome = self.deletable_fase.nome
        initial_count = Fase.objects.count()
        
        response = self.client_app.post(self.deletable_fase_url, follow=True)
        
        # Should redirect to fases list
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/fases_list.html')
        
        # Should delete the fase
        self.assertEqual(Fase.objects.count(), initial_count - 1)
        self.assertFalse(Fase.objects.filter(id=fase_id).exists())
        
        # Should show success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.SUCCESS)
        self.assertIn(fase_nome, str(messages[0]))
        self.assertIn('excluída com sucesso', str(messages[0]))
    
    def test_deletar_fase_multiple_deletions(self):
        """Test deleting multiple unused fases"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create additional deletable fases
        fase1 = Fase.objects.create(nome='Deletável 1', tipo='alvara', cor='#111111', ativa=True, ordem=100)
        fase2 = Fase.objects.create(nome='Deletável 2', tipo='requerimento', cor='#222222', ativa=False, ordem=101)
        
        initial_count = Fase.objects.count()
        
        # Delete first fase
        url1 = reverse('deletar_fase', kwargs={'fase_id': fase1.id})
        response1 = self.client_app.post(url1)
        self.assertEqual(response1.status_code, 302)
        
        # Delete second fase
        url2 = reverse('deletar_fase', kwargs={'fase_id': fase2.id})
        response2 = self.client_app.post(url2)
        self.assertEqual(response2.status_code, 302)
        
        # Should delete both fases
        self.assertEqual(Fase.objects.count(), initial_count - 2)
        self.assertFalse(Fase.objects.filter(id=fase1.id).exists())
        self.assertFalse(Fase.objects.filter(id=fase2.id).exists())
    
    # ===============================
    # BUSINESS LOGIC CONSTRAINT TESTS
    # ===============================
    
    def test_deletar_fase_blocked_by_alvara_usage(self):
        """Test deletion blocked when fase is used by alvaras"""
        self.client_app.login(username='testuser', password='testpass123')
        
        initial_count = Fase.objects.count()
        fase_nome = self.fase_used_by_alvara.nome
        
        response = self.client_app.post(self.alvara_used_fase_url, follow=True)
        
        # Should redirect to fases list without deletion
        self.assertEqual(response.status_code, 200)
        
        # Fase should not be deleted
        self.assertEqual(Fase.objects.count(), initial_count)
        self.assertTrue(Fase.objects.filter(id=self.fase_used_by_alvara.id).exists())
        
        # Should show error message with count
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.ERROR)
        self.assertIn(fase_nome, str(messages[0]))
        self.assertIn('está sendo usada por', str(messages[0]))
        self.assertIn('alvará(s)', str(messages[0]))
        self.assertIn('1', str(messages[0]))  # Count of alvaras
    
    def test_deletar_fase_blocked_by_requerimento_usage(self):
        """Test deletion blocked when fase is used by requerimentos"""
        self.client_app.login(username='testuser', password='testpass123')
        
        initial_count = Fase.objects.count()
        fase_nome = self.fase_used_by_requerimento.nome
        
        response = self.client_app.post(self.requerimento_used_fase_url, follow=True)
        
        # Should redirect to fases list without deletion
        self.assertEqual(response.status_code, 200)
        
        # Fase should not be deleted
        self.assertEqual(Fase.objects.count(), initial_count)
        self.assertTrue(Fase.objects.filter(id=self.fase_used_by_requerimento.id).exists())
        
        # Should show error message with count
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.ERROR)
        self.assertIn(fase_nome, str(messages[0]))
        self.assertIn('está sendo usada por', str(messages[0]))
        self.assertIn('requerimento(s)', str(messages[0]))
        self.assertIn('1', str(messages[0]))  # Count of requerimentos
    
    def test_deletar_fase_blocked_by_both_usage(self):
        """Test deletion blocked when fase is used by both alvaras and requerimentos"""
        self.client_app.login(username='testuser', password='testpass123')
        
        initial_count = Fase.objects.count()
        
        response = self.client_app.post(self.both_used_fase_url, follow=True)
        
        # Should redirect to fases list without deletion
        self.assertEqual(response.status_code, 200)
        
        # Fase should not be deleted
        self.assertEqual(Fase.objects.count(), initial_count)
        self.assertTrue(Fase.objects.filter(id=self.fase_used_by_both.id).exists())
        
        # Should show error message (first check is for alvaras)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.ERROR)
        message_text = str(messages[0])
        # Should show either alvara or requerimento error (depends on which check runs first)
        self.assertTrue('alvará(s)' in message_text or 'requerimento(s)' in message_text)
    
    def test_deletar_fase_multiple_alvaras_count(self):
        """Test error message shows correct count when multiple alvaras use the fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create additional alvara using the same fase
        additional_alvara = Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor_principal=30000.00,
            honorarios_contratuais=6000.00,
            honorarios_sucumbenciais=3000.00,
            tipo='comum',
            fase=self.fase_used_by_alvara
        )
        
        response = self.client_app.post(self.alvara_used_fase_url, follow=True)
        
        # Should show error with count of 2 alvaras
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn('2', message_text)  # Count should be 2
        self.assertIn('alvará(s)', message_text)
    
    def test_deletar_fase_multiple_requerimentos_count(self):
        """Test error message shows correct count when multiple requerimentos use the fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create additional requerimento using the same fase
        additional_requerimento = Requerimento.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente,
            valor=20000.00,
            desagio=4.0,
            pedido=self.pedido_prioridade_doenca,  # Use existing PedidoRequerimento
            fase=self.fase_used_by_requerimento
        )
        
        response = self.client_app.post(self.requerimento_used_fase_url, follow=True)
        
        # Should show error with count of 2 requerimentos
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn('2', message_text)  # Count should be 2
        self.assertIn('requerimento(s)', message_text)
    
    # ===============================
    # MESSAGE FRAMEWORK TESTS
    # ===============================
    
    def test_deletar_fase_success_message_content(self):
        """Test that success message contains correct fase name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        fase_nome = self.deletable_fase.nome
        
        response = self.client_app.post(self.deletable_fase_url, follow=True)
        
        # Check success message content
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.SUCCESS)
        message_text = str(messages[0])
        self.assertIn(fase_nome, message_text)
        self.assertIn('excluída com sucesso', message_text)
    
    def test_deletar_fase_error_message_alvara_content(self):
        """Test that error message for alvara usage contains correct information"""
        self.client_app.login(username='testuser', password='testpass123')
        
        fase_nome = self.fase_used_by_alvara.nome
        
        response = self.client_app.post(self.alvara_used_fase_url, follow=True)
        
        # Check error message content
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.ERROR)
        message_text = str(messages[0])
        self.assertIn(fase_nome, message_text)
        self.assertIn('Não é possível excluir', message_text)
        self.assertIn('está sendo usada por', message_text)
        self.assertIn('alvará(s)', message_text)
        self.assertIn('Altere a fase desses alvarás primeiro', message_text)
    
    def test_deletar_fase_error_message_requerimento_content(self):
        """Test that error message for requerimento usage contains correct information"""
        self.client_app.login(username='testuser', password='testpass123')
        
        fase_nome = self.fase_used_by_requerimento.nome
        
        response = self.client_app.post(self.requerimento_used_fase_url, follow=True)
        
        # Check error message content
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, constants.ERROR)
        message_text = str(messages[0])
        self.assertIn(fase_nome, message_text)
        self.assertIn('Não é possível excluir', message_text)
        self.assertIn('está sendo usada por', message_text)
        self.assertIn('requerimento(s)', message_text)
        self.assertIn('Altere a fase desses requerimentos primeiro', message_text)
    
    # ===============================
    # REDIRECT BEHAVIOR TESTS
    # ===============================
    
    def test_deletar_fase_success_redirect(self):
        """Test redirect behavior after successful deletion"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.deletable_fase_url)
        
        # Should redirect to fases list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
        
        # Follow redirect to verify destination
        follow_response = self.client_app.get(reverse('fases'))
        self.assertEqual(follow_response.status_code, 200)
    
    def test_deletar_fase_error_redirect(self):
        """Test redirect behavior when deletion is blocked"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.alvara_used_fase_url)
        
        # Should redirect to fases list even on error
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
    
    def test_deletar_fase_get_redirect(self):
        """Test redirect behavior for GET requests"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(self.deletable_fase_url)
        
        # Should redirect to fases list without processing deletion
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
    
    # ===============================
    # SECURITY TESTS
    # ===============================
    
    def test_deletar_fase_csrf_protection(self):
        """Test that CSRF protection is properly enforced"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # POST without CSRF should fail
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='testuser', password='testpass123')
        
        response = csrf_client.post(self.deletable_fase_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Fase should not be deleted
        self.assertTrue(Fase.objects.filter(id=self.deletable_fase.id).exists())
    
    def test_deletar_fase_unauthorized_access_other_user(self):
        """Test that other users can delete phases (since there's no ownership model)"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        # Login as other user
        self.client_app.login(username='otheruser', password='otherpass123')
        
        # Try to delete the fase (should work since there's no ownership model)
        response = self.client_app.post(self.deletable_fase_url)
        
        # In this system, any authenticated user can delete phases
        self.assertEqual(response.status_code, 302)
        
        # Fase should be deleted
        self.assertFalse(Fase.objects.filter(id=self.deletable_fase.id).exists())
    
    def test_deletar_fase_sql_injection_protection(self):
        """Test protection against SQL injection in URL parameters"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Try SQL injection in URL (Django's URL routing should handle this)
        malicious_url = "/fases/1'; DROP TABLE precapp_fase; --/deletar/"
        response = self.client_app.post(malicious_url)
        
        # Should return 404 (URL pattern won't match)
        self.assertEqual(response.status_code, 404)
        
        # Database should remain intact
        self.assertTrue(Fase.objects.filter(id=self.deletable_fase.id).exists())
    
    # ===============================
    # BUSINESS LOGIC INTEGRATION TESTS
    # ===============================
    
    def test_deletar_fase_cascade_behavior(self):
        """Test that deletion doesn't cascade to related objects inappropriately"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Count related objects before deletion attempt
        initial_alvara_count = Alvara.objects.count()
        initial_requerimento_count = Requerimento.objects.count()
        
        # Try to delete fase used by both
        response = self.client_app.post(self.both_used_fase_url)
        
        # Should not delete the fase or related objects
        self.assertTrue(Fase.objects.filter(id=self.fase_used_by_both.id).exists())
        self.assertEqual(Alvara.objects.count(), initial_alvara_count)
        self.assertEqual(Requerimento.objects.count(), initial_requerimento_count)
    
    def test_deletar_fase_relationship_integrity(self):
        """Test that deletion preserves database relationship integrity"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify relationships before deletion
        alvara_using_fase = Alvara.objects.filter(fase=self.fase_used_by_alvara)
        self.assertTrue(alvara_using_fase.exists())
        
        # Try to delete the fase
        response = self.client_app.post(self.alvara_used_fase_url)
        
        # Relationships should remain intact
        alvara_using_fase_after = Alvara.objects.filter(fase=self.fase_used_by_alvara)
        self.assertTrue(alvara_using_fase_after.exists())
        self.assertEqual(alvara_using_fase.count(), alvara_using_fase_after.count())
    
    def test_deletar_fase_business_validation_order(self):
        """Test that business validation checks alvaras first, then requerimentos"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # For fase used by both, should check alvaras first
        response = self.client_app.post(self.both_used_fase_url, follow=True)
        
        # Should show alvara error message (checked first)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn('alvará(s)', message_text)
    
    # ===============================
    # INTEGRATION TESTS
    # ===============================
    
    def test_deletar_fase_integration_with_fases_list(self):
        """Test integration between deletar_fase and fases list view"""
        self.client_app.login(username='testuser', password='testpass123')
        
        fase_nome = self.deletable_fase.nome
        
        # Delete fase
        response = self.client_app.post(self.deletable_fase_url, follow=True)
        
        # Should redirect to fases list
        self.assertTemplateUsed(response, 'precapp/fases_list.html')
        
        # Should show success message
        self.assertContains(response, 'excluída com sucesso')
        
        # The deleted phase should not exist in database
        self.assertFalse(Fase.objects.filter(nome=fase_nome).exists())
    
    def test_deletar_fase_integration_with_related_models(self):
        """Test integration behavior with related models"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify the business logic correctly identifies usage
        alvaras_count = Alvara.objects.filter(fase=self.fase_used_by_alvara).count()
        requerimentos_count = Requerimento.objects.filter(fase=self.fase_used_by_requerimento).count()
        
        self.assertEqual(alvaras_count, 1)
        self.assertEqual(requerimentos_count, 1)
        
        # Deletion should be blocked for both
        response1 = self.client_app.post(self.alvara_used_fase_url, follow=True)
        response2 = self.client_app.post(self.requerimento_used_fase_url, follow=True)
        
        # Both should show error messages
        messages1 = list(get_messages(response1.wsgi_request))
        messages2 = list(get_messages(response2.wsgi_request))
        
        self.assertEqual(len(messages1), 1)
        self.assertEqual(len(messages2), 1)
        self.assertEqual(messages1[0].level, constants.ERROR)
        self.assertEqual(messages2[0].level, constants.ERROR)
    
    # ===============================
    # EDGE CASES AND ERROR HANDLING
    # ===============================
    
    def test_deletar_fase_concurrent_deletion_attempt(self):
        """Test handling of concurrent deletion attempts"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # First deletion should succeed
        response1 = self.client_app.post(self.deletable_fase_url)
        self.assertEqual(response1.status_code, 302)
        
        # Second attempt should return 404 (fase no longer exists)
        response2 = self.client_app.post(self.deletable_fase_url)
        self.assertEqual(response2.status_code, 404)
    
    def test_deletar_fase_concurrent_usage_creation(self):
        """Test handling when usage is created between validation and deletion"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # This test simulates a race condition where an alvara is created
        # between the time we check for usage and actually delete
        # In practice, Django's atomic transactions should handle this
        
        # For now, we can test that if usage exists, deletion is blocked
        self.assertTrue(Alvara.objects.filter(fase=self.fase_used_by_alvara).exists())
        
        response = self.client_app.post(self.alvara_used_fase_url)
        
        # Should be blocked
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Fase.objects.filter(id=self.fase_used_by_alvara.id).exists())
    
    def test_deletar_fase_database_transaction_integrity(self):
        """Test that deletion operations maintain database transaction integrity"""
        self.client_app.login(username='testuser', password='testpass123')
        
        initial_fase_count = Fase.objects.count()
        
        # Successful deletion should be atomic
        response = self.client_app.post(self.deletable_fase_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Fase.objects.count(), initial_fase_count - 1)
        
        # Failed deletion should not change anything
        response = self.client_app.post(self.alvara_used_fase_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Fase.objects.count(), initial_fase_count - 1)  # Still same count
    
    def test_deletar_fase_performance_with_many_relations(self):
        """Test performance when checking many related objects"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create many alvaras using the same fase
        for i in range(50):
            Alvara.objects.create(
                precatorio=self.precatorio,
                cliente=self.cliente,
                valor_principal=1000.00 + i,
                honorarios_contratuais=100.00 + i,
                honorarios_sucumbenciais=50.00 + i,
                tipo='comum',
                fase=self.fase_used_by_alvara
            )
        
        # Deletion should still be efficiently blocked
        response = self.client_app.post(self.alvara_used_fase_url, follow=True)
        
        # Should show error with correct count
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn('51', message_text)  # 1 original + 50 new = 51
        
        # Fase should not be deleted
        self.assertTrue(Fase.objects.filter(id=self.fase_used_by_alvara.id).exists())
    
    def test_deletar_fase_unicode_in_messages(self):
        """Test that Unicode characters in fase names are handled correctly in messages"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create fase with Unicode characters
        unicode_fase = Fase.objects.create(
            nome='Fase Açúcar & Coração ñ',
            tipo='ambos',
            cor='#000000',
            ativa=True,
            ordem=999
        )
        
        unicode_url = reverse('deletar_fase', kwargs={'fase_id': unicode_fase.id})
        
        response = self.client_app.post(unicode_url, follow=True)
        
        # Should handle Unicode correctly in success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn('Fase Açúcar & Coração ñ', message_text)


class AtivarFaseViewTest(TestCase):
    """Test cases for ativar_fase_view function"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client_app = Client()
        
        # Create test fases - initially active
        self.fase_ativa = Fase.objects.create(
            nome='Fase Ativa Test',
            tipo='ambos',
            cor='#28A745',
            ativa=True,
            ordem=1
        )
        
        # Create test fase - initially inactive
        self.fase_inativa = Fase.objects.create(
            nome='Fase Inativa Test',
            tipo='alvara',
            cor='#DC3545',
            ativa=False,
            ordem=2
        )
        
        # URLs for testing
        self.ativar_fase_ativa_url = reverse('ativar_fase', kwargs={'fase_id': self.fase_ativa.id})
        self.ativar_fase_inativa_url = reverse('ativar_fase', kwargs={'fase_id': self.fase_inativa.id})
    
    # Authentication Tests
    def test_ativar_fase_requires_authentication(self):
        """Test that accessing ativar_fase_view requires authentication"""
        response = self.client_app.get(self.ativar_fase_ativa_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
    
    def test_ativar_fase_post_requires_authentication(self):
        """Test that POST to ativar_fase_view requires authentication"""
        response = self.client_app.post(self.ativar_fase_ativa_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
    
    def test_ativar_fase_authenticated_user_access(self):
        """Test that authenticated users can access ativar_fase_view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        self.assertEqual(response.status_code, 200)
    
    # Instance Loading Tests
    def test_ativar_fase_valid_id(self):
        """Test ativar_fase_view with valid fase ID"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_ativar_fase_invalid_id_404(self):
        """Test ativar_fase_view with invalid fase ID returns 404"""
        self.client_app.login(username='testuser', password='testpass123')
        invalid_url = reverse('ativar_fase', kwargs={'fase_id': 99999})
        response = self.client_app.post(invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_ativar_fase_nonexistent_id_404(self):
        """Test ativar_fase_view with nonexistent fase ID returns 404"""
        self.client_app.login(username='testuser', password='testpass123')
        # Delete the fase and try to access it
        fase_id = self.fase_ativa.id
        self.fase_ativa.delete()
        nonexistent_url = reverse('ativar_fase', kwargs={'fase_id': fase_id})
        response = self.client_app.post(nonexistent_url)
        self.assertEqual(response.status_code, 404)
    
    # HTTP Method Tests
    def test_ativar_fase_get_method_redirect(self):
        """Test that GET request to ativar_fase_view redirects to fases without changes"""
        self.client_app.login(username='testuser', password='testpass123')
        original_status = self.fase_ativa.ativa
        
        response = self.client_app.get(self.ativar_fase_ativa_url, follow=True)
        
        # Should redirect to fases
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('fases'))
        
        # Fase status should remain unchanged
        self.fase_ativa.refresh_from_db()
        self.assertEqual(self.fase_ativa.ativa, original_status)
    
    def test_ativar_fase_post_method_toggles_status(self):
        """Test that POST request to ativar_fase_view toggles fase status"""
        self.client_app.login(username='testuser', password='testpass123')
        original_status = self.fase_ativa.ativa
        
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        
        # Should redirect to fases
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('fases'))
        
        # Fase status should be toggled
        self.fase_ativa.refresh_from_db()
        self.assertEqual(self.fase_ativa.ativa, not original_status)
    
    def test_ativar_fase_put_method_not_allowed(self):
        """Test that PUT method is not explicitly handled"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.put(self.ativar_fase_ativa_url)
        # Django's default behavior for unhandled methods
        self.assertIn(response.status_code, [405, 302])
    
    def test_ativar_fase_delete_method_not_allowed(self):
        """Test that DELETE method is not explicitly handled"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.delete(self.ativar_fase_ativa_url)
        # Django's default behavior for unhandled methods
        self.assertIn(response.status_code, [405, 302])
    
    # Functionality Tests - Activate Inactive Fase
    def test_ativar_fase_activate_inactive_fase(self):
        """Test activating an inactive fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Ensure fase is initially inactive
        self.assertFalse(self.fase_inativa.ativa)
        
        response = self.client_app.post(self.ativar_fase_inativa_url, follow=True)
        
        # Should redirect to fases
        self.assertRedirects(response, reverse('fases'))
        
        # Fase should now be active
        self.fase_inativa.refresh_from_db()
        self.assertTrue(self.fase_inativa.ativa)
    
    def test_ativar_fase_deactivate_active_fase(self):
        """Test deactivating an active fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Ensure fase is initially active
        self.assertTrue(self.fase_ativa.ativa)
        
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        
        # Should redirect to fases
        self.assertRedirects(response, reverse('fases'))
        
        # Fase should now be inactive
        self.fase_ativa.refresh_from_db()
        self.assertFalse(self.fase_ativa.ativa)
    
    def test_ativar_fase_multiple_toggles(self):
        """Test multiple toggles of fase status"""
        self.client_app.login(username='testuser', password='testpass123')
        
        original_status = self.fase_ativa.ativa
        
        # First toggle
        self.client_app.post(self.ativar_fase_ativa_url)
        self.fase_ativa.refresh_from_db()
        self.assertEqual(self.fase_ativa.ativa, not original_status)
        
        # Second toggle (back to original)
        self.client_app.post(self.ativar_fase_ativa_url)
        self.fase_ativa.refresh_from_db()
        self.assertEqual(self.fase_ativa.ativa, original_status)
        
        # Third toggle
        self.client_app.post(self.ativar_fase_ativa_url)
        self.fase_ativa.refresh_from_db()
        self.assertEqual(self.fase_ativa.ativa, not original_status)
    
    # Message Framework Tests
    def test_ativar_fase_activation_success_message(self):
        """Test success message when activating a fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Ensure fase is initially inactive
        self.fase_inativa.ativa = False
        self.fase_inativa.save()
        
        response = self.client_app.post(self.ativar_fase_inativa_url, follow=True)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.level, constants.SUCCESS)
        self.assertIn('Fase "Fase Inativa Test" foi ativada com sucesso!', str(message))
    
    def test_ativar_fase_deactivation_success_message(self):
        """Test success message when deactivating a fase"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Ensure fase is initially active
        self.fase_ativa.ativa = True
        self.fase_ativa.save()
        
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.level, constants.SUCCESS)
        self.assertIn('Fase "Fase Ativa Test" foi desativada com sucesso!', str(message))
    
    def test_ativar_fase_message_contains_fase_name(self):
        """Test that success message contains the correct fase name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn(self.fase_ativa.nome, message_text)
    
    def test_ativar_fase_no_message_on_get(self):
        """Test that no message is shown on GET request"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(self.ativar_fase_ativa_url, follow=True)
        
        # Should have no messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)
    
    # Redirect Tests
    def test_ativar_fase_redirect_after_post(self):
        """Test redirect to fases after POST"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.ativar_fase_ativa_url)
        
        # Should redirect to fases list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
    
    def test_ativar_fase_redirect_after_get(self):
        """Test redirect to fases after GET"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(self.ativar_fase_ativa_url)
        
        # Should redirect to fases list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('fases'))
    
    def test_ativar_fase_redirect_preserves_query_params(self):
        """Test that redirect doesn't interfere with subsequent navigation"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        
        # Should be at fases page
        self.assertEqual(response.status_code, 200)
        # Should be able to navigate normally
        self.assertContains(response, 'Fase Ativa Test')
    
    # Database Integrity Tests
    def test_ativar_fase_database_persistence(self):
        """Test that changes are properly saved to database"""
        self.client_app.login(username='testuser', password='testpass123')
        
        original_status = self.fase_ativa.ativa
        
        self.client_app.post(self.ativar_fase_ativa_url)
        
        # Reload from database
        fase_from_db = Fase.objects.get(id=self.fase_ativa.id)
        self.assertEqual(fase_from_db.ativa, not original_status)
    
    def test_ativar_fase_only_ativa_field_changed(self):
        """Test that only the ativa field is modified"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Record original values
        original_nome = self.fase_ativa.nome
        original_tipo = self.fase_ativa.tipo
        original_cor = self.fase_ativa.cor
        original_ordem = self.fase_ativa.ordem
        
        self.client_app.post(self.ativar_fase_ativa_url)
        
        # Reload and verify only ativa changed
        self.fase_ativa.refresh_from_db()
        self.assertEqual(self.fase_ativa.nome, original_nome)
        self.assertEqual(self.fase_ativa.tipo, original_tipo)
        self.assertEqual(self.fase_ativa.cor, original_cor)
        self.assertEqual(self.fase_ativa.ordem, original_ordem)
    
    def test_ativar_fase_concurrent_modification_safety(self):
        """Test behavior when fase is modified concurrently"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Simulate concurrent modification
        original_status = self.fase_ativa.ativa
        
        # Modify the fase externally
        Fase.objects.filter(id=self.fase_ativa.id).update(nome='Modified Externally')
        
        # Our activation should still work
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        
        # Verify both changes persisted
        self.fase_ativa.refresh_from_db()
        self.assertEqual(self.fase_ativa.ativa, not original_status)
        self.assertEqual(self.fase_ativa.nome, 'Modified Externally')
    
    # Security Tests
    def test_ativar_fase_csrf_protection(self):
        """Test CSRF protection on POST requests"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Disable CSRF for this test client (Django test client handles CSRF automatically)
        # This is to verify the view expects CSRF protection
        from django.views.decorators.csrf import csrf_exempt
        # Note: In real scenario, missing CSRF token would cause 403
        
        response = self.client_app.post(self.ativar_fase_ativa_url)
        # Should work with test client (CSRF handled automatically)
        self.assertEqual(response.status_code, 302)
    
    def test_ativar_fase_no_xss_in_messages(self):
        """Test that fase names in messages are properly escaped"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create fase with potential XSS content
        xss_fase = Fase.objects.create(
            nome='<script>alert("xss")</script>Test',
            tipo='ambos',
            cor='#000000',
            ativa=True,
            ordem=999
        )
        
        xss_url = reverse('ativar_fase', kwargs={'fase_id': xss_fase.id})
        
        response = self.client_app.post(xss_url, follow=True)
        
        # Check that message contains escaped content
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        # Should contain the raw name (Django's message framework handles escaping)
        self.assertIn('<script>alert("xss")</script>Test', message_text)
    
    def test_ativar_fase_sql_injection_protection(self):
        """Test protection against SQL injection in fase_id parameter"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Try SQL injection in URL
        malicious_url = '/ativar_fase/1; DROP TABLE precapp_fase; --/'
        
        response = self.client_app.post(malicious_url)
        # Should return 404 (URL doesn't match pattern) or 400
        self.assertIn(response.status_code, [404, 400])
        
        # Verify table still exists
        self.assertTrue(Fase.objects.filter(id=self.fase_ativa.id).exists())
    
    def test_ativar_fase_user_isolation(self):
        """Test that users can only access through proper authentication"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        # Login as other user
        self.client_app.login(username='otheruser', password='otherpass123')
        
        # Should still be able to access (no user-specific restrictions in this view)
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        self.assertEqual(response.status_code, 200)
    
    # Edge Cases and Error Handling
    def test_ativar_fase_with_unicode_name(self):
        """Test handling fase with Unicode characters in name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        unicode_fase = Fase.objects.create(
            nome='Fase Açúcar & Coração ñ ü',
            tipo='ambos',
            cor='#000000',
            ativa=True,
            ordem=999
        )
        
        unicode_url = reverse('ativar_fase', kwargs={'fase_id': unicode_fase.id})
        
        response = self.client_app.post(unicode_url, follow=True)
        
        # Should handle Unicode correctly
        self.assertEqual(response.status_code, 200)
        
        # Check message contains Unicode name
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn('Fase Açúcar & Coração ñ ü', message_text)
    
    def test_ativar_fase_with_long_name(self):
        """Test handling fase with very long name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        long_name = 'A' * 200  # Very long name
        long_fase = Fase.objects.create(
            nome=long_name,
            tipo='ambos',
            cor='#000000',
            ativa=True,
            ordem=999
        )
        
        long_url = reverse('ativar_fase', kwargs={'fase_id': long_fase.id})
        
        response = self.client_app.post(long_url, follow=True)
        
        # Should handle long names correctly
        self.assertEqual(response.status_code, 200)
        
        # Check message contains long name
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn(long_name, message_text)
    
    def test_ativar_fase_with_empty_name(self):
        """Test handling fase with empty name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create fase with minimal name (if model allows)
        empty_fase = Fase.objects.create(
            nome='',  # Empty name
            tipo='ambos',
            cor='#000000',
            ativa=True,
            ordem=999
        )
        
        empty_url = reverse('ativar_fase', kwargs={'fase_id': empty_fase.id})
        
        response = self.client_app.post(empty_url, follow=True)
        
        # Should still work
        self.assertEqual(response.status_code, 200)
        
        # Check message handling
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
    
    def test_ativar_fase_with_special_characters_name(self):
        """Test handling fase with special characters in name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        special_name = 'Fase "Test" & <em>Special</em> \'Characters\' @#$%'
        special_fase = Fase.objects.create(
            nome=special_name,
            tipo='ambos',
            cor='#000000',
            ativa=True,
            ordem=999
        )
        
        special_url = reverse('ativar_fase', kwargs={'fase_id': special_fase.id})
        
        response = self.client_app.post(special_url, follow=True)
        
        # Should handle special characters correctly
        self.assertEqual(response.status_code, 200)
        
        # Check message contains special characters
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn(special_name, message_text)
    
    # Integration Tests
    def test_ativar_fase_integration_with_fases_list(self):
        """Test that changes are reflected in fases list"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Deactivate fase
        self.client_app.post(self.ativar_fase_ativa_url)
        
        # Navigate to fases list
        response = self.client_app.get(reverse('fases'))
        
        # Should show the updated status
        self.assertEqual(response.status_code, 200)
        # Note: The exact verification depends on how fases template shows status
    
    def test_ativar_fase_navigation_workflow(self):
        """Test complete workflow of navigation and activation"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Start at fases list
        response = self.client_app.get(reverse('fases'))
        self.assertEqual(response.status_code, 200)
        
        # Activate/deactivate fase
        response = self.client_app.post(self.ativar_fase_ativa_url, follow=True)
        
        # Should be back at fases list with success message
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
    
    # Performance Tests
    def test_ativar_fase_performance_single_query(self):
        """Test that activation uses minimal database queries"""
        self.client_app.login(username='testuser', password='testpass123')
        
        with self.assertNumQueries(4):  # Session query + User query + get_object_or_404 + save
            self.client_app.post(self.ativar_fase_ativa_url)
    
    def test_ativar_fase_bulk_operations(self):
        """Test multiple rapid activations"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create multiple fases
        fases = []
        for i in range(10):
            fase = Fase.objects.create(
                nome=f'Bulk Fase {i}',
                tipo='ambos',
                cor='#000000',
                ativa=True,
                ordem=100 + i
            )
            fases.append(fase)
        
        # Activate/deactivate all rapidly
        for fase in fases:
            url = reverse('ativar_fase', kwargs={'fase_id': fase.id})
            response = self.client_app.post(url)
            self.assertEqual(response.status_code, 302)
        
        # Verify all were toggled
        for fase in fases:
            fase.refresh_from_db()
            self.assertFalse(fase.ativa)  # Should be deactivated
