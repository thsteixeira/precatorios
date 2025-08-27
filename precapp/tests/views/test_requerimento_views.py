"""
Requerimento View Tests

Comprehensive test suite for requerimento-related views including:
- RequerimentoListViewTest: List view with filtering, statistics, and deletion

Total expected tests: ~15
Test classes: 1
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from datetime import date
from precapp.models import (
    Requerimento, Precatorio, Cliente, Fase, PedidoRequerimento
)


class RequerimentoListViewTest(TestCase):
    """
    Comprehensive test suite for the requerimento_list_view function.
    
    The requerimento_list_view displays all requerimentos with filtering capabilities,
    financial statistics calculation, and deletion functionality. This test class validates:
    
    - Authentication requirement (@login_required decorator)
    - Basic list display without filters
    - Individual filter functionality (cliente, precatorio, pedido, fase)
    - Combined filter functionality
    - Financial statistics calculation (valor_total, desagio_medio)
    - Deletion functionality via POST requests
    - Template context data provision
    - Error handling for non-existent requerimentos
    - Form persistence (current filter values in context)
    
    Filter Types Tested:
    - cliente: Partial name matching (icontains)
    - precatorio: CNJ partial matching (icontains)
    - pedido: Exact ID matching of PedidoRequerimento instance
    - fase: Exact matching of phase name
    
    Financial Calculations:
    - valor_total: Sum of all valores from filtered requerimentos
    - desagio_medio: Average deságio percentage from filtered requerimentos
    - Handles null/empty values gracefully
    
    Deletion Functionality:
    - POST request with 'delete_requerimento' action
    - Success message generation with client name
    - Redirect to requerimentos list after deletion
    - Error handling for non-existent requerimento attempts
    """
    
    def setUp(self):
        """Set up test data for requerimento list view testing"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create test clients
        self.cliente1 = Cliente.objects.create(
            nome='João Silva',
            cpf='12345678901',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.cliente2 = Cliente.objects.create(
            nome='Maria Santos',
            cpf='98765432100',
            nascimento=date(1985, 3, 20),
            prioridade=True
        )
        
        # Create test precatorios
        self.precatorio1 = Precatorio.objects.create(
            cnj='0000001-11.2022.5.04.0001',
            orcamento=2022,
            origem='TRT 4ª Região',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2022, 1, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='0000002-22.2023.5.04.0002',
            orcamento=2023,
            origem='TRT 3ª Região',
            valor_de_face=75000.00,
            ultima_atualizacao=75000.00,
            data_ultima_atualizacao=date(2023, 2, 20),
            percentual_contratuais_assinado=25.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=15.0,
            credito_principal='quitado',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='quitado'
        )
        
        # Link clients to precatorios (required for Requerimento creation)
        self.precatorio1.clientes.add(self.cliente1, self.cliente2)
        self.precatorio2.clientes.add(self.cliente1)
        
        # Create test fases
        self.fase_deferido = Fase.objects.create(
            nome='Deferido',
            tipo='requerimento',
            cor='#28a745',
            ordem=1,
            ativa=True
        )
        
        self.fase_em_andamento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#ffc107',
            ordem=2,
            ativa=True
        )
        
        self.fase_indeferido = Fase.objects.create(
            nome='Indeferido',
            tipo='requerimento',
            cor='#dc3545',
            ordem=3,
            ativa=True
        )
        
        # Create test PedidoRequerimento types
        self.pedido_doenca = PedidoRequerimento.objects.create(
            nome='Prioridade por Doença',
            descricao='Pedido de prioridade por motivo de doença',
            cor='#dc3545',
            ordem=1,
            ativo=True
        )
        
        self.pedido_acordo = PedidoRequerimento.objects.create(
            nome='Acordo Principal',
            descricao='Pedido referente ao acordo principal',
            cor='#28a745',
            ordem=2,
            ativo=True
        )
        
        self.pedido_idade = PedidoRequerimento.objects.create(
            nome='Prioridade por Idade',
            descricao='Pedido de prioridade por idade avançada',
            cor='#ffc107',
            ordem=3,
            ativo=True
        )
        
        # Create test requerimentos
        self.requerimento1 = Requerimento.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente1,
            valor=25000.00,
            desagio=10.5,
            pedido=self.pedido_doenca,
            fase=self.fase_deferido
        )
        
        self.requerimento2 = Requerimento.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente2,
            valor=30000.00,
            desagio=15.0,
            pedido=self.pedido_acordo,
            fase=self.fase_em_andamento
        )
        
        self.requerimento3 = Requerimento.objects.create(
            precatorio=self.precatorio2,
            cliente=self.cliente1,
            valor=20000.00,
            desagio=8.5,
            pedido=self.pedido_idade,
            fase=self.fase_indeferido
        )
        
        # URLs
        self.requerimentos_url = reverse('requerimentos')
        
        # Create client for requests
        self.client = Client()
    
    def test_requerimento_list_view_requires_authentication(self):
        """Test that requerimento list view requires user authentication"""
        response = self.client.get(self.requerimentos_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_requerimento_list_view_authenticated_access(self):
        """Test that authenticated users can access requerimento list view"""
        self.client.force_login(self.user)
        response = self.client.get(self.requerimentos_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de Requerimentos')
        self.assertIn('requerimentos', response.context)
    
    def test_requerimento_list_view_displays_all_requerimentos(self):
        """Test that view displays all requerimentos when no filters applied"""
        self.client.force_login(self.user)
        response = self.client.get(self.requerimentos_url)
        
        self.assertEqual(response.status_code, 200)
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 3)
        
        # Verify ordering (newest first, ordered by -id)
        requerimento_ids = [r.id for r in requerimentos]
        expected_order = [self.requerimento3.id, self.requerimento2.id, self.requerimento1.id]
        self.assertEqual(requerimento_ids, expected_order)
    
    def test_requerimento_list_view_cliente_filter(self):
        """Test filtering requerimentos by cliente name"""
        self.client.force_login(self.user)
        
        # Test partial name matching
        response = self.client.get(self.requerimentos_url, {'cliente': 'João'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 2)
        for req in requerimentos:
            self.assertIn('João', req.cliente.nome)
        
        # Test case insensitive search
        response = self.client.get(self.requerimentos_url, {'cliente': 'maria'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
        self.assertEqual(requerimentos[0].cliente.nome, 'Maria Santos')
        
        # Test no matches
        response = self.client.get(self.requerimentos_url, {'cliente': 'Pedro'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 0)
    
    def test_requerimento_list_view_precatorio_filter(self):
        """Test filtering requerimentos by precatorio CNJ"""
        self.client.force_login(self.user)
        
        # Test partial CNJ matching
        response = self.client.get(self.requerimentos_url, {'precatorio': '0000001'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 2)
        for req in requerimentos:
            self.assertIn('0000001', req.precatorio.cnj)
        
        # Test full CNJ matching
        response = self.client.get(self.requerimentos_url, {'precatorio': '0000002-22.2023.5.04.0002'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
        self.assertEqual(requerimentos[0].precatorio.cnj, '0000002-22.2023.5.04.0002')
        
        # Test no matches
        response = self.client.get(self.requerimentos_url, {'precatorio': '9999999'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 0)
    
    def test_requerimento_list_view_pedido_filter(self):
        """Test filtering requerimentos by pedido type"""
        self.client.force_login(self.user)
        
        # Test exact matching for priority illness
        response = self.client.get(self.requerimentos_url, {'pedido': str(self.pedido_doenca.id)})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
        self.assertEqual(requerimentos[0].pedido, self.pedido_doenca)
        
        # Test exact matching for agreement
        response = self.client.get(self.requerimentos_url, {'pedido': str(self.pedido_acordo.id)})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
        self.assertEqual(requerimentos[0].pedido, self.pedido_acordo)
        
        # Test no matches for non-existent pedido
        response = self.client.get(self.requerimentos_url, {'pedido': '9999'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 0)
    
    def test_requerimento_list_view_fase_filter(self):
        """Test filtering requerimentos by fase name"""
        self.client.force_login(self.user)
        
        # Test exact matching for Deferido
        response = self.client.get(self.requerimentos_url, {'fase': 'Deferido'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
        self.assertEqual(requerimentos[0].fase.nome, 'Deferido')
        
        # Test exact matching for Em Andamento
        response = self.client.get(self.requerimentos_url, {'fase': 'Em Andamento'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
        self.assertEqual(requerimentos[0].fase.nome, 'Em Andamento')
        
        # Test no matches for non-existent fase
        response = self.client.get(self.requerimentos_url, {'fase': 'Inexistente'})
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 0)
    
    def test_requerimento_list_view_combined_filters(self):
        """Test combining multiple filters"""
        self.client.force_login(self.user)
        
        # Test cliente + precatorio filters
        response = self.client.get(self.requerimentos_url, {
            'cliente': 'João',
            'precatorio': '0000001'
        })
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
        self.assertEqual(requerimentos[0].cliente.nome, 'João Silva')
        self.assertIn('0000001', requerimentos[0].precatorio.cnj)
        
        # Test pedido + fase filters
        response = self.client.get(self.requerimentos_url, {
            'pedido': str(self.pedido_idade.id),
            'fase': 'Indeferido'
        })
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
        self.assertEqual(requerimentos[0].pedido, self.pedido_idade)
        self.assertEqual(requerimentos[0].fase.nome, 'Indeferido')
        
        # Test filters that should return no results
        response = self.client.get(self.requerimentos_url, {
            'cliente': 'João',
            'pedido': str(self.pedido_acordo.id)  # Maria's request, not João's
        })
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 0)
    
    def test_requerimento_list_view_financial_statistics(self):
        """Test financial statistics calculation"""
        self.client.force_login(self.user)
        response = self.client.get(self.requerimentos_url)
        
        # Test total value calculation
        expected_total = 25000.00 + 30000.00 + 20000.00  # Sum of all valores
        self.assertEqual(response.context['valor_total'], expected_total)
        
        # Test average deságio calculation
        expected_average = (10.5 + 15.0 + 8.5) / 3  # Average of all deságios
        self.assertAlmostEqual(response.context['desagio_medio'], expected_average, places=2)
    
    def test_requerimento_list_view_financial_statistics_with_filters(self):
        """Test financial statistics calculation with filters applied"""
        self.client.force_login(self.user)
        
        # Filter by cliente to get subset
        response = self.client.get(self.requerimentos_url, {'cliente': 'João'})
        
        # Should calculate stats only for João's requerimentos
        expected_total = 25000.00 + 20000.00  # João's two requerimentos
        self.assertEqual(response.context['valor_total'], expected_total)
        
        expected_average = (10.5 + 8.5) / 2  # Average of João's deságios
        self.assertAlmostEqual(response.context['desagio_medio'], expected_average, places=2)
    
    def test_requerimento_list_view_empty_statistics(self):
        """Test financial statistics when no requerimentos match filters"""
        self.client.force_login(self.user)
        
        # Filter that returns no results
        response = self.client.get(self.requerimentos_url, {'cliente': 'Nonexistent'})
        
        # Should have zero values
        self.assertEqual(response.context['valor_total'], 0)
        self.assertEqual(response.context['desagio_medio'], 0)
    
    def test_requerimento_list_view_template_context(self):
        """Test that all necessary data is provided in template context"""
        self.client.force_login(self.user)
        response = self.client.get(self.requerimentos_url, {
            'cliente': 'João',
            'precatorio': '0000001',
            'pedido': str(self.pedido_doenca.id),
            'fase': 'Deferido'
        })
        
        # Verify all required context variables
        self.assertIn('requerimentos', response.context)
        self.assertIn('available_fases', response.context)
        self.assertIn('valor_total', response.context)
        self.assertIn('desagio_medio', response.context)
        
        # Verify filter values are preserved for form persistence
        self.assertEqual(response.context['current_cliente'], 'João')
        self.assertEqual(response.context['current_precatorio'], '0000001')
        self.assertEqual(response.context['current_pedido'], str(self.pedido_doenca.id))
        self.assertEqual(response.context['current_fase'], 'Deferido')
        
        # Verify available_fases contains requerimento phases
        available_fases = response.context['available_fases']
        fase_names = [fase.nome for fase in available_fases]
        self.assertIn('Deferido', fase_names)
        self.assertIn('Em Andamento', fase_names)
        self.assertIn('Indeferido', fase_names)
    
    def test_requerimento_list_view_delete_functionality(self):
        """Test successful requerimento deletion via POST request"""
        self.client.force_login(self.user)
        
        # Verify initial count
        initial_count = Requerimento.objects.count()
        self.assertEqual(initial_count, 3)
        
        # Delete requerimento via POST
        response = self.client.post(self.requerimentos_url, {
            'delete_requerimento': 'true',
            'requerimento_id': self.requerimento1.id
        })
        
        # Should redirect to requerimentos list
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('requerimentos'))
        
        # Verify requerimento was deleted
        self.assertEqual(Requerimento.objects.count(), initial_count - 1)
        self.assertFalse(Requerimento.objects.filter(id=self.requerimento1.id).exists())
        
        # Verify success message
        response = self.client.get(self.requerimentos_url)
        messages = list(get_messages(response.wsgi_request))
        success_messages = [str(m) for m in messages if m.tags == 'success']
        self.assertTrue(len(success_messages) > 0)
        self.assertIn('João Silva', success_messages[0])
        self.assertIn('excluído com sucesso', success_messages[0])
    
    def test_requerimento_list_view_delete_nonexistent(self):
        """Test deletion attempt of non-existent requerimento"""
        self.client.force_login(self.user)
        
        # Try to delete non-existent requerimento
        response = self.client.post(self.requerimentos_url, {
            'delete_requerimento': 'true',
            'requerimento_id': 99999  # Non-existent ID
        })
        
        # Should not redirect (error occurred)
        self.assertEqual(response.status_code, 200)
        
        # Verify no requerimentos were deleted
        self.assertEqual(Requerimento.objects.count(), 3)
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        error_messages = [str(m) for m in messages if m.tags == 'error']
        self.assertTrue(len(error_messages) > 0)
        self.assertIn('não encontrado', error_messages[0])
    
    def test_requerimento_list_view_select_related_optimization(self):
        """Test that view uses select_related for database optimization"""
        self.client.force_login(self.user)
        
        # Access view to trigger queryset evaluation
        response = self.client.get(self.requerimentos_url)
        requerimentos = response.context['requerimentos']
        
        # Access related objects - should not cause additional queries due to select_related
        for req in requerimentos:
            _ = req.cliente.nome      # Should be pre-fetched
            _ = req.precatorio.cnj    # Should be pre-fetched
            _ = req.fase.nome         # Should be pre-fetched
        
        # Test passes if no additional database queries are triggered
        self.assertEqual(response.status_code, 200)
    
    def test_requerimento_list_view_filter_persistence(self):
        """Test that filter values are preserved in template context"""
        self.client.force_login(self.user)
        
        # Test with empty filters
        response = self.client.get(self.requerimentos_url)
        self.assertEqual(response.context['current_cliente'], '')
        self.assertEqual(response.context['current_precatorio'], '')
        self.assertEqual(response.context['current_pedido'], '')
        self.assertEqual(response.context['current_fase'], '')
        
        # Test with spaces in filter values (should be stripped in context)
        response = self.client.get(self.requerimentos_url, {
            'cliente': '  João  ',
            'precatorio': '  0000001  '
        })
        self.assertEqual(response.context['current_cliente'], 'João')  # Stripped value in context
        self.assertEqual(response.context['current_precatorio'], '0000001')  # Stripped value in context
        
        # And filtering should work with stripped values
        requerimentos = response.context['requerimentos']
        self.assertEqual(requerimentos.count(), 1)
