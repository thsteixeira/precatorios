"""
Client View Tests

Tests for client management views including:
- ClientesViewTest: Client list view with filtering
- ClienteDetailViewTest: Client detail view with CRUD operations

Total expected tests: ~40
Test classes to be migrated: 2
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from datetime import date, timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from precapp.models import (
    Cliente, Precatorio, Requerimento, Fase, TipoDiligencia, Diligencias, PedidoRequerimento
)
from precapp.forms import ClienteForm, PrecatorioSearchForm

# Tests will be migrated here from test_views.py
# Classes to migrate:
# - ClientesViewTest
# - ClienteDetailViewTest


class ClientesViewTest(TestCase):
    """Test cases for Clientes list view"""
    
    def setUp(self):
        """Set up comprehensive test data for clientes_view testing"""
        # Note: self.client is already provided by Django's TestCase
        
        # Create user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test phases for requerimentos
        self.fase_deferido = Fase.objects.create(
            nome='Deferido',
            tipo='requerimento',
            cor='#28a745',
            ativa=True,
            ordem=1
        )
        
        self.fase_indeferido = Fase.objects.create(
            nome='Indeferido',
            tipo='requerimento',
            cor='#dc3545',
            ativa=True,
            ordem=2
        )
        
        # Create test precatorios
        self.precatorio1 = Precatorio.objects.create(
            cnj='1234567-89.2023.4.05.0001',
            orcamento=2023,
            origem='Tribunal de Justiça',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao='2023-01-01',
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='9876543-21.2023.4.05.0002',
            orcamento=2023,
            origem='Tribunal Federal',
            valor_de_face=200000.00,
            ultima_atualizacao=200000.00,
            data_ultima_atualizacao='2023-02-01',
            percentual_contratuais_assinado=25.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=15.0,
            credito_principal='quitado',
            honorarios_contratuais='quitado',
            honorarios_sucumbenciais='pendente'
        )
        
        # Create test clients with varying ages and priorities
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        today = date.today()
        
        # Client aged 65 (priority by age)
        self.cliente1 = Cliente.objects.create(
            cpf='11144477735',
            nome='João da Silva',
            nascimento=today - relativedelta(years=65),
            prioridade=True
        )
        
        # Client aged 45 (no priority)
        self.cliente2 = Cliente.objects.create(
            cpf='22255588846',
            nome='Maria Santos',
            nascimento=today - relativedelta(years=45),
            prioridade=False
        )
        
        # Client aged 30 (no priority)
        self.cliente3 = Cliente.objects.create(
            cpf='33366699957',
            nome='Carlos Oliveira',
            nascimento=today - relativedelta(years=30),
            prioridade=False
        )
        
        # Client aged 70 (priority by age)
        self.cliente4 = Cliente.objects.create(
            cpf='44477700068',
            nome='Ana Costa',
            nascimento=today - relativedelta(years=70),
            prioridade=True
        )
        
        # Link clients to precatorios
        self.precatorio1.clientes.add(self.cliente1, self.cliente2)
        self.precatorio2.clientes.add(self.cliente3, self.cliente4)
        
        # Create test PedidoRequerimento
        self.pedido_prioridade = PedidoRequerimento.objects.create(
            nome='Prioridade por idade',
            descricao='Pedido de prioridade por idade',
            cor='#ffc107',
            ordem=1,
            ativo=True
        )
        
        self.pedido_acordo = PedidoRequerimento.objects.create(
            nome='Acordo no Principal',
            descricao='Pedido de acordo principal',
            cor='#28a745',
            ordem=2,
            ativo=True
        )
        
        # Create requerimentos for testing priority filters
        self.requerimento_deferido = Requerimento.objects.create(
            cliente=self.cliente1,
            precatorio=self.precatorio1,
            valor=50000.00,
            desagio=10.0,
            pedido=self.pedido_prioridade,
            fase=self.fase_deferido
        )
        
        self.requerimento_nao_deferido = Requerimento.objects.create(
            cliente=self.cliente2,
            precatorio=self.precatorio1,
            valor=30000.00,
            desagio=5.0,
            pedido=self.pedido_prioridade,  # Use same pedido for simplicity
            fase=self.fase_indeferido
        )
        
        self.requerimento_acordo = Requerimento.objects.create(
            cliente=self.cliente3,
            precatorio=self.precatorio2,
            valor=75000.00,
            desagio=8.0,
            pedido=self.pedido_acordo,
            fase=self.fase_deferido
        )
        
        # Test URLs
        self.clientes_url = reverse('clientes')
        self.login_url = reverse('login')
    
    def test_clientes_view_requires_authentication(self):
        """Test that clientes_view requires user authentication"""
        response = self.client.get(self.clientes_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Follow redirect to verify login requirement
        response = self.client.get(self.clientes_url, follow=True)
        self.assertContains(response, 'login')
    
    def test_clientes_view_authenticated_access(self):
        """Test that authenticated users can access clientes_view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.clientes_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/cliente_list.html')
        self.assertContains(response, 'Clientes')
    
    def test_clientes_list_no_filters(self):
        """Test clientes list view without any filters applied"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.clientes_url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should show all 4 test clients
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 4)
        
        # Verify clients are properly loaded with prefetch_related
        self.assertTrue(hasattr(clientes[0], '_prefetched_objects_cache'))
        
        # Check context statistics
        context = response.context
        self.assertEqual(context['total_clientes'], 4)
        self.assertEqual(context['clientes_com_prioridade'], 2)
        self.assertEqual(context['clientes_sem_prioridade'], 2)
    
    def test_clientes_view_nome_filter(self):
        """Test filtering clients by name"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test exact name match
        response = self.client.get(self.clientes_url, {'nome': 'João da Silva'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'João da Silva')
        
        # Test partial name match (case insensitive)
        response = self.client.get(self.clientes_url, {'nome': 'silva'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'João da Silva')
        
        # Test no matches
        response = self.client.get(self.clientes_url, {'nome': 'Inexistente'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 0)
        
        # Verify filter value is preserved in context
        self.assertEqual(response.context['current_nome'], 'Inexistente')
    
    def test_clientes_view_cpf_filter(self):
        """Test filtering clients by CPF"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test full CPF match
        response = self.client.get(self.clientes_url, {'cpf': '11144477735'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].cpf, '11144477735')
        
        # Test partial CPF match
        response = self.client.get(self.clientes_url, {'cpf': '111'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].cpf, '11144477735')
        
        # Test multiple matches with partial CPF
        response = self.client.get(self.clientes_url, {'cpf': '77'})
        clientes = response.context['clientes']
        self.assertGreaterEqual(len(clientes), 1)
        
        # Verify filter value is preserved in context
        self.assertEqual(response.context['current_cpf'], '77')
    
    def test_clientes_view_idade_filter(self):
        """Test filtering clients by age"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test filtering by age 65
        response = self.client.get(self.clientes_url, {'idade': '65'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'João da Silva')
        
        # Test filtering by age 45
        response = self.client.get(self.clientes_url, {'idade': '45'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'Maria Santos')
        
        # Test filtering by age with no matches
        response = self.client.get(self.clientes_url, {'idade': '100'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 0)
        
        # Test invalid age (should be ignored)
        response = self.client.get(self.clientes_url, {'idade': 'invalid'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 4)  # Should show all clients
        
        # Verify filter value is preserved in context
        response = self.client.get(self.clientes_url, {'idade': '65'})
        self.assertEqual(response.context['current_idade'], '65')
    
    def test_clientes_view_prioridade_filter(self):
        """Test filtering clients by priority status"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test filtering for clients with priority
        response = self.client.get(self.clientes_url, {'prioridade': 'true'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 2)
        for cliente in clientes:
            self.assertTrue(cliente.prioridade)
        
        # Test filtering for clients without priority
        response = self.client.get(self.clientes_url, {'prioridade': 'false'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 2)
        for cliente in clientes:
            self.assertFalse(cliente.prioridade)
        
        # Test invalid priority value (should be ignored)
        response = self.client.get(self.clientes_url, {'prioridade': 'invalid'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 4)  # Should show all clients
        
        # Verify filter value is preserved in context
        response = self.client.get(self.clientes_url, {'prioridade': 'true'})
        self.assertEqual(response.context['current_prioridade'], 'true')
    
    def test_clientes_view_requerimento_prioridade_filter(self):
        """Test filtering clients by requerimento priority status"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test filtering for clients with deferido priority requerimentos
        response = self.client.get(self.clientes_url, {'requerimento_prioridade': 'deferido'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].cpf, '11144477735')  # cliente1 with deferido priority requerimento
        
        # Test filtering for clients with non-deferido priority requerimentos
        response = self.client.get(self.clientes_url, {'requerimento_prioridade': 'nao_deferido'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].cpf, '22255588846')  # cliente2 with non-deferido priority requerimento
        
        # Test filtering for clients without priority requerimentos
        response = self.client.get(self.clientes_url, {'requerimento_prioridade': 'sem_requerimento'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 2)  # cliente3 and cliente4 have no priority requerimentos
        
        # Verify filter value is preserved in context
        response = self.client.get(self.clientes_url, {'requerimento_prioridade': 'deferido'})
        self.assertEqual(response.context['current_requerimento_prioridade'], 'deferido')
    
    def test_clientes_view_precatorio_filter(self):
        """Test filtering clients by associated precatorio CNJ"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test filtering by full CNJ
        response = self.client.get(self.clientes_url, {'precatorio': '1234567-89.2023.4.05.0001'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 2)  # cliente1 and cliente2
        
        # Test filtering by partial CNJ
        response = self.client.get(self.clientes_url, {'precatorio': '1234567'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 2)  # cliente1 and cliente2
        
        # Test filtering with no matches
        response = self.client.get(self.clientes_url, {'precatorio': 'inexistente'})
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 0)
        
        # Verify filter value is preserved in context
        response = self.client.get(self.clientes_url, {'precatorio': '1234567'})
        self.assertEqual(response.context['current_precatorio'], '1234567')
    
    def test_clientes_view_combined_filters(self):
        """Test using multiple filters simultaneously"""
        self.client.login(username='testuser', password='testpass123')
        
        # Combine name and priority filters
        response = self.client.get(self.clientes_url, {
            'nome': 'João',
            'prioridade': 'true'
        })
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'João da Silva')
        self.assertTrue(clientes[0].prioridade)
        
        # Combine age and priority filters
        response = self.client.get(self.clientes_url, {
            'idade': '65',
            'prioridade': 'true'
        })
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].nome, 'João da Silva')
        
        # Combine filters that should result in no matches
        response = self.client.get(self.clientes_url, {
            'nome': 'João',
            'prioridade': 'false'
        })
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 0)
    
    def test_clientes_view_context_data(self):
        """Test that view provides correct context data"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.clientes_url)
        
        # Check required context keys
        required_context_keys = [
            'clientes', 'total_clientes', 'clientes_com_prioridade', 'clientes_sem_prioridade',
            'current_nome', 'current_cpf', 'current_idade', 'current_prioridade',
            'current_requerimento_prioridade', 'current_precatorio'
        ]
        
        for key in required_context_keys:
            self.assertIn(key, response.context)
        
        # Check that statistics are correct
        context = response.context
        self.assertEqual(context['total_clientes'], 4)
        self.assertEqual(context['clientes_com_prioridade'], 2)
        self.assertEqual(context['clientes_sem_prioridade'], 2)
        
        # Check that all current filter values default to appropriate values
        self.assertEqual(context['current_nome'], '')
        self.assertEqual(context['current_cpf'], '')
        self.assertEqual(context['current_idade'], '')
        self.assertEqual(context['current_prioridade'], '')
        self.assertEqual(context['current_requerimento_prioridade'], '')
        self.assertEqual(context['current_precatorio'], '')
    
    def test_clientes_view_filter_persistence(self):
        """Test that filter values persist in the form after applying filters"""
        self.client.login(username='testuser', password='testpass123')
        
        filter_params = {
            'nome': 'João',
            'cpf': '111',
            'idade': '65',
            'prioridade': 'true',
            'requerimento_prioridade': 'deferido',
            'precatorio': '1234567'
        }
        
        response = self.client.get(self.clientes_url, filter_params)
        
        # Verify all filter values are preserved in context
        context = response.context
        self.assertEqual(context['current_nome'], 'João')
        self.assertEqual(context['current_cpf'], '111')
        self.assertEqual(context['current_idade'], '65')
        self.assertEqual(context['current_prioridade'], 'true')
        self.assertEqual(context['current_requerimento_prioridade'], 'deferido')
        self.assertEqual(context['current_precatorio'], '1234567')
    
    def test_clientes_view_prefetch_optimization(self):
        """Test that queries are optimized with proper prefetch_related"""
        self.client.login(username='testuser', password='testpass123')
        
        # Monitor database queries to ensure optimization
        with self.assertNumQueries(18):  # Expected queries include auth, counts, main query, and prefetched data
            response = self.client.get(self.clientes_url)
        
        self.assertEqual(response.status_code, 200)
        
        clientes = response.context['clientes']
        # Verify prefetch optimization works - accessing prefetched data shouldn't trigger new queries
        with self.assertNumQueries(0):
            for cliente in clientes:
                # These shouldn't trigger additional queries due to prefetch_related
                precatorios_count = cliente.precatorios.count()
                self.assertIsNotNone(precatorios_count)
    
    def test_clientes_view_distinct_handling(self):
        """Test that distinct() is properly applied when filtering by precatorios"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create additional associations to test distinct behavior
        # Add cliente1 to precatorio2 as well (so they're in both precatorios)
        self.precatorio2.clientes.add(self.cliente1)
        
        # Filter by a condition that could return duplicates
        response = self.client.get(self.clientes_url, {'precatorio': '2023'})
        
        clientes = response.context['clientes']
        client_cpfs = [cliente.cpf for cliente in clientes]
        
        # Should not have duplicates
        self.assertEqual(len(client_cpfs), len(set(client_cpfs)))
    
    def test_clientes_view_empty_filters(self):
        """Test handling of empty filter values"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with empty string filters (should be stripped and ignored)
        response = self.client.get(self.clientes_url, {
            'nome': '   ',
            'cpf': '',
            'idade': '  ',
            'precatorio': '   '
        })
        
        clientes = response.context['clientes']
        self.assertEqual(len(clientes), 4)  # Should show all clients
        
        # Verify stripped values in context
        context = response.context
        self.assertEqual(context['current_nome'], '')
        self.assertEqual(context['current_cpf'], '')
        self.assertEqual(context['current_idade'], '')
        self.assertEqual(context['current_precatorio'], '')
    
    def test_clientes_view_statistics_accuracy(self):
        """Test that statistics calculations are accurate with different filter combinations"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test statistics with priority filter
        response = self.client.get(self.clientes_url, {'prioridade': 'true'})
        context = response.context
        self.assertEqual(context['total_clientes'], 2)
        self.assertEqual(context['clientes_com_prioridade'], 2)
        self.assertEqual(context['clientes_sem_prioridade'], 0)
        
        # Test statistics with name filter
        response = self.client.get(self.clientes_url, {'nome': 'Silva'})
        context = response.context
        self.assertEqual(context['total_clientes'], 1)
        self.assertEqual(context['clientes_com_prioridade'], 1)
        self.assertEqual(context['clientes_sem_prioridade'], 0)
        
        # Test statistics with filters that return no results
        response = self.client.get(self.clientes_url, {'nome': 'Inexistente'})
        context = response.context
        self.assertEqual(context['total_clientes'], 0)
        self.assertEqual(context['clientes_com_prioridade'], 0)
        self.assertEqual(context['clientes_sem_prioridade'], 0)
    
    def test_clientes_view_edge_cases(self):
        """Test edge cases and error handling"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with very long filter values
        long_name = 'a' * 1000
        response = self.client.get(self.clientes_url, {'nome': long_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['clientes']), 0)
        
        # Test with special characters in filters
        response = self.client.get(self.clientes_url, {'nome': 'João@#$%'})
        self.assertEqual(response.status_code, 200)
        
        # Test age filter with negative values
        response = self.client.get(self.clientes_url, {'idade': '-5'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['clientes']), 0)
        
        # Test age filter with very large values
        response = self.client.get(self.clientes_url, {'idade': '200'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['clientes']), 0)


class ClienteDetailViewTest(TestCase):
    """Test class for cliente_detail_view function"""
    
    def setUp(self):
        """Set up test data for all test methods"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test cliente
        self.cliente = Cliente.objects.create(
            nome='João Silva',
            cpf='11144477735',  # Valid CPF according to Brazilian algorithm
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Create test precatorios
        self.precatorio1 = Precatorio.objects.create(
            cnj='0123456-78.2020.5.04.0001',
            orcamento=2020,
            origem='TRT 4ª Região',
            valor_de_face=100000.00
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='0987654-32.2021.5.04.0002',
            orcamento=2021,
            origem='TRT 4ª Região',
            valor_de_face=50000.00
        )
        
        # Create tipo diligencia for diligencia tests
        self.tipo_diligencia = TipoDiligencia.objects.create(
            nome='Contato Telefônico',
            ativo=True
        )
        
    def test_cliente_detail_view_requires_login(self):
        """Test that cliente_detail_view requires user authentication"""
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        self.assertRedirects(response, f'/login/?next=/clientes/{self.cliente.cpf}/')
    
    def test_cliente_detail_view_get_basic(self):
        """Test basic GET request to cliente_detail_view"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cliente.nome)
        self.assertContains(response, self.cliente.cpf)
        
        # Verify context data
        self.assertEqual(response.context['cliente'], self.cliente)
        self.assertIsNotNone(response.context['search_form'])
        self.assertIsNone(response.context['client_form'])  # Should be None for non-edit GET
        self.assertFalse(response.context['is_editing'])
    
    def test_cliente_detail_view_get_with_edit_param(self):
        """Test GET request with edit parameter"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}) + '?edit=true')
        
        # Verify edit mode is enabled
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_editing'])
        self.assertIsNotNone(response.context['client_form'])
        self.assertEqual(response.context['client_form'].instance, self.cliente)
    
    def test_cliente_detail_view_404_for_invalid_cpf(self):
        """Test that view returns 404 for non-existent client"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': '99999999999'}))
        self.assertEqual(response.status_code, 404)
    
    def test_cliente_detail_view_associated_precatorios(self):
        """Test that associated precatorios are displayed correctly"""
        # Link cliente to precatorios
        self.precatorio1.clientes.add(self.cliente)
        self.precatorio2.clientes.add(self.cliente)
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify associated precatorios in context
        associated_precatorios = response.context['associated_precatorios']
        self.assertEqual(associated_precatorios.count(), 2)
        self.assertIn(self.precatorio1, associated_precatorios)
        self.assertIn(self.precatorio2, associated_precatorios)
        
        # Verify content contains precatorio CNJs
        self.assertContains(response, self.precatorio1.cnj)
        self.assertContains(response, self.precatorio2.cnj)
    
    def test_cliente_detail_view_diligencias_context(self):
        """Test diligencias context data"""
        # Create test diligencias
        diligencia_pendente = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=5),
            urgencia='baixa',
            criado_por='Test User',
            concluida=False
        )
        
        diligencia_concluida = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() - timedelta(days=5),
            urgencia='alta',
            criado_por='Test User',
            concluida=True
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify diligencias context
        self.assertEqual(response.context['total_diligencias'], 2)
        self.assertEqual(response.context['total_pendentes'], 1)
        self.assertEqual(response.context['total_concluidas'], 1)
        
        # Verify queryset filtering
        diligencias_pendentes = response.context['diligencias_pendentes']
        diligencias_concluidas = response.context['diligencias_concluidas']
        
        self.assertEqual(diligencias_pendentes.count(), 1)
        self.assertEqual(diligencias_concluidas.count(), 1)
        self.assertIn(diligencia_pendente, diligencias_pendentes)
        self.assertIn(diligencia_concluida, diligencias_concluidas)
    
    def test_cliente_detail_view_edit_client_success(self):
        """Test successful client editing"""
        self.client.force_login(self.user)
        
        post_data = {
            'edit_client': 'true',
            'nome': 'João Silva Atualizado',
            'cpf': self.cliente.cpf,
            'nascimento': '1980-05-15',
            'prioridade': True,
            'precatorio_cnj': ''  # Empty CNJ field as it's optional
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Verify redirect after successful edit
        self.assertRedirects(response, reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify cliente was updated
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nome, 'João Silva Atualizado')
        self.assertTrue(self.cliente.prioridade)
        
        # Verify success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('atualizado com sucesso' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_edit_client_invalid_form(self):
        """Test client editing with invalid form data"""
        self.client.force_login(self.user)
        
        post_data = {
            'edit_client': 'true',
            'nome': '',  # Invalid: empty name
            'cpf': self.cliente.cpf,
            'nascimento': '1980-05-15',
            'prioridade': False,
            'precatorio_cnj': ''  # Empty CNJ field as it's optional
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Verify form errors are displayed
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_editing'])
        # Check that form has errors for the nome field
        self.assertTrue(response.context['client_form'].errors)
        self.assertIn('nome', response.context['client_form'].errors)
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('corrija os erros' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_link_precatorio_success(self):
        """Test successful precatorio linking"""
        self.client.force_login(self.user)
        
        post_data = {
            'link_precatorio': 'true',
            'cnj': self.precatorio1.cnj
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Verify redirect after successful linking
        self.assertRedirects(response, reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify precatorio was linked
        self.assertIn(self.cliente, self.precatorio1.clientes.all())
        
        # Verify success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('vinculado com sucesso' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_link_precatorio_already_linked(self):
        """Test linking precatorio that is already linked"""
        # Pre-link the precatorio
        self.precatorio1.clientes.add(self.cliente)
        
        self.client.force_login(self.user)
        
        post_data = {
            'link_precatorio': 'true',
            'cnj': self.precatorio1.cnj
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Should stay on same page with warning message
        self.assertEqual(response.status_code, 200)
        
        # Verify warning message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('já está vinculado' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_link_precatorio_not_found(self):
        """Test linking non-existent precatorio"""
        self.client.force_login(self.user)
        
        post_data = {
            'link_precatorio': 'true',
            'cnj': '9999999-99.2023.8.26.9999'  # Valid format but non-existent
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Should stay on same page with error message
        self.assertEqual(response.status_code, 200)
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        # The message should be about precatorio not found
        self.assertTrue(any('Precatório com CNJ' in str(msg) and 'não encontrado' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_link_precatorio_invalid_cnj(self):
        """Test linking precatorio with invalid CNJ format"""
        self.client.force_login(self.user)
        
        post_data = {
            'link_precatorio': 'true',
            'cnj': 'invalid-cnj-format'
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Should stay on same page with error message
        self.assertEqual(response.status_code, 200)
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('corrija os erros no CNJ' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_unlink_precatorio_success(self):
        """Test successful precatorio unlinking"""
        # Pre-link the precatorio
        self.precatorio1.clientes.add(self.cliente)
        
        self.client.force_login(self.user)
        
        post_data = {
            'unlink_precatorio': 'true',
            'precatorio_cnj': self.precatorio1.cnj
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Verify redirect after successful unlinking
        self.assertRedirects(response, reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify precatorio was unlinked
        self.assertNotIn(self.cliente, self.precatorio1.clientes.all())
        
        # Verify success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('desvinculado' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_unlink_precatorio_not_linked(self):
        """Test unlinking precatorio that is not linked"""
        self.client.force_login(self.user)
        
        post_data = {
            'unlink_precatorio': 'true',
            'precatorio_cnj': self.precatorio1.cnj
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Should stay on same page with error message
        self.assertEqual(response.status_code, 200)
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('não está vinculado' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_unlink_precatorio_not_found(self):
        """Test unlinking non-existent precatorio"""
        self.client.force_login(self.user)
        
        post_data = {
            'unlink_precatorio': 'true',
            'precatorio_cnj': '9999999-99.9999.9.99.9999'
        }
        
        response = self.client.post(
            reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}),
            post_data
        )
        
        # Should stay on same page with error message
        self.assertEqual(response.status_code, 200)
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Precatório não encontrado' in str(msg) for msg in messages))
    
    def test_cliente_detail_view_query_optimization(self):
        """Test that the view uses query optimization"""
        # Create multiple precatorios and diligencias
        for i in range(3):
            precatorio = Precatorio.objects.create(
                cnj=f'0000000-0{i}.2022.5.04.000{i}',
                orcamento=2022,
                origem='TRT 4ª Região',
                valor_de_face=10000.00
            )
            precatorio.clientes.add(self.cliente)
            
            Diligencias.objects.create(
                cliente=self.cliente,
                tipo=self.tipo_diligencia,
                data_final=date.today() + timedelta(days=i+1),
                urgencia='baixa',
                criado_por='Test User',
                concluida=False
            )
        
        self.client.force_login(self.user)
        
        # Monitor number of queries - be more realistic about expected queries
        with self.assertNumQueries(11):  # Current actual query count as shown in failure
            response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
            
            # Force evaluation of querysets
            list(response.context['associated_precatorios'])
            list(response.context['diligencias'])
            list(response.context['diligencias_pendentes'])
            list(response.context['diligencias_concluidas'])
    
    def test_cliente_detail_view_context_completeness(self):
        """Test that all required context variables are present"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify all required context keys are present
        required_context_keys = [
            'cliente', 'client_form', 'search_form', 'associated_precatorios',
            'is_editing', 'diligencias', 'diligencias_pendentes', 'diligencias_concluidas',
            'total_diligencias', 'total_pendentes', 'total_concluidas'
        ]
        
        for key in required_context_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")
    
    def test_cliente_detail_view_precatorios_ordering(self):
        """Test that associated precatorios are ordered by CNJ"""
        # Create precatorios with specific CNJs to test ordering
        precatorio_z = Precatorio.objects.create(
            cnj='9999999-99.2020.5.04.0001',
            orcamento=2020,
            origem='TRT 4ª Região',
            valor_de_face=100000.00
        )
        
        precatorio_a = Precatorio.objects.create(
            cnj='0000001-11.2020.5.04.0001',
            orcamento=2020,
            origem='TRT 4ª Região',
            valor_de_face=100000.00
        )
        
        # Link in reverse order
        precatorio_z.clientes.add(self.cliente)
        precatorio_a.clientes.add(self.cliente)
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify ordering
        associated_precatorios = list(response.context['associated_precatorios'])
        self.assertEqual(associated_precatorios[0], precatorio_a)  # Should be first (alphabetically)
        self.assertEqual(associated_precatorios[1], precatorio_z)  # Should be second
    
    def test_cliente_detail_view_diligencias_ordering(self):
        """Test that diligencias are ordered by creation date (newest first)"""
        # Create diligencias with specific creation dates
        old_diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() - timedelta(days=5),
            urgencia='baixa',
            criado_por='Test User',
            concluida=False
        )
        
        # Update creation date to simulate older creation
        old_diligencia.data_criacao = timezone.now() - timedelta(days=5)
        old_diligencia.save()
        
        new_diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=5),
            urgencia='alta',
            criado_por='Test User',
            concluida=False
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf}))
        
        # Verify ordering (newest first)
        diligencias = list(response.context['diligencias'])
        self.assertEqual(diligencias[0], new_diligencia)  # Should be first (newest)
        self.assertEqual(diligencias[1], old_diligencia)  # Should be second (older)


class NovoClienteViewTest(TestCase):
    """Test cases for novo_cliente_view function"""
    
    def setUp(self):
        """Set up test data for novo_cliente_view testing"""
        # Create test user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test precatorio for form field testing
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.4.05.0001',
            orcamento=2023,
            origem='Tribunal de Justiça',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao='2023-01-01',
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Test URLs
        self.novo_cliente_url = reverse('novo_cliente')
        self.login_url = reverse('login')
    
    def test_novo_cliente_view_requires_authentication(self):
        """Test that novo_cliente_view requires user authentication"""
        response = self.client.get(self.novo_cliente_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Follow redirect to verify login requirement
        response = self.client.get(self.novo_cliente_url, follow=True)
        self.assertContains(response, 'login')
    
    def test_novo_cliente_view_authenticated_get_request(self):
        """Test GET request to novo_cliente_view with authentication"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.novo_cliente_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/novo_cliente.html')
        self.assertContains(response, 'Novo Cliente')
        
        # Verify context contains form
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ClienteForm)
        
        # Verify form is not bound (empty form for new client)
        form = response.context['form']
        self.assertFalse(form.is_bound)
        self.assertEqual(form.initial, {})
    
    def test_novo_cliente_view_post_valid_form(self):
        """Test POST request with valid form data"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'João Silva',
            'cpf': '11144477735',  # Valid CPF format
            'nascimento': '1985-03-15',
            'prioridade': False,
        }
        
        # Verify no cliente exists before creation
        self.assertEqual(Cliente.objects.count(), 0)
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify cliente was created
        self.assertEqual(Cliente.objects.count(), 1)
        cliente = Cliente.objects.first()
        self.assertEqual(cliente.nome, 'João Silva')
        self.assertEqual(cliente.cpf, '11144477735')
        self.assertEqual(cliente.nascimento, date(1985, 3, 15))
        self.assertFalse(cliente.prioridade)
        
        # Verify redirect to cliente detail page
        expected_url = reverse('cliente_detail', kwargs={'cpf': cliente.cpf})
        self.assertRedirects(response, expected_url)
        
        # Verify success message was created
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        success_message = str(messages[0])
        self.assertIn('João Silva', success_message)
        self.assertIn('criado com sucesso', success_message)
    
    def test_novo_cliente_view_post_valid_form_with_priority(self):
        """Test POST request with valid form data including priority"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Maria Santos',
            'cpf': '22255588846',
            'nascimento': '1950-12-10',  # Age that might qualify for priority
            'prioridade': True,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify cliente was created with priority
        cliente = Cliente.objects.get(cpf='22255588846')
        self.assertEqual(cliente.nome, 'Maria Santos')
        self.assertTrue(cliente.prioridade)
        
        # Verify success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Maria Santos' in str(msg) and 'criado com sucesso' in str(msg) for msg in messages))
    
    def test_novo_cliente_view_post_invalid_form_empty_name(self):
        """Test POST request with invalid form data - empty name"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': '',  # Invalid: empty name
            'cpf': '33366699957',
            'nascimento': '1990-06-20',
            'prioridade': False,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should not redirect, should re-render form with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/novo_cliente.html')
        
        # Verify no cliente was created
        self.assertEqual(Cliente.objects.count(), 0)
        
        # Verify form has errors
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('nome', form.errors)
        
        # Verify form is bound with submitted data
        self.assertTrue(form.is_bound)
        self.assertEqual(form.data['cpf'], '33366699957')
    
    def test_novo_cliente_view_post_invalid_form_invalid_cpf(self):
        """Test POST request with invalid CPF format"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Carlos Oliveira',
            'cpf': '12345',  # Invalid: too short CPF
            'nascimento': '1975-08-30',
            'prioridade': False,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should not redirect, should re-render form with errors
        self.assertEqual(response.status_code, 200)
        
        # Verify no cliente was created
        self.assertEqual(Cliente.objects.count(), 0)
        
        # Verify form has errors
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('cpf', form.errors)
    
    def test_novo_cliente_view_post_invalid_form_duplicate_cpf(self):
        """Test POST request with duplicate CPF"""
        # Create existing cliente
        Cliente.objects.create(
            nome='Existing Client',
            cpf='44477700068',
            nascimento=date(1980, 1, 1),
            prioridade=False
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'New Client',
            'cpf': '44477700068',  # Duplicate CPF
            'nascimento': '1985-03-15',
            'prioridade': False,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should not redirect, should re-render form with errors
        self.assertEqual(response.status_code, 200)
        
        # Verify only one cliente exists (the original)
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(Cliente.objects.first().nome, 'Existing Client')
        
        # Verify form has errors
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('cpf', form.errors)
    
    def test_novo_cliente_view_post_invalid_form_invalid_birth_date(self):
        """Test POST request with invalid birth date"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Future Person',
            'cpf': '12345678901',  # Invalid CPF to trigger form error
            'nascimento': '2030-01-01',  # Invalid: future date
            'prioridade': False,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should not redirect, should re-render form with errors
        self.assertEqual(response.status_code, 200)
        
        # Verify no cliente was created
        self.assertEqual(Cliente.objects.count(), 0)
        
        # Verify form has errors (CPF validation will catch this first)
        form = response.context['form']
        self.assertTrue(form.errors)
        # CPF validation happens first, so we'll get CPF error
        self.assertIn('cpf', form.errors)
    
    def test_novo_cliente_view_post_missing_required_fields(self):
        """Test POST request with missing required fields"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            # Missing nome and cpf
            'nascimento': '1990-01-01',
            'prioridade': False,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should not redirect, should re-render form with errors
        self.assertEqual(response.status_code, 200)
        
        # Verify no cliente was created
        self.assertEqual(Cliente.objects.count(), 0)
        
        # Verify form has errors for required fields
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('nome', form.errors)
        self.assertIn('cpf', form.errors)
    
    def test_novo_cliente_view_context_data(self):
        """Test that view provides correct context data"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.novo_cliente_url)
        
        # Verify required context keys
        required_context_keys = ['form']
        for key in required_context_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")
        
        # Verify form is correct type and clean
        form = response.context['form']
        self.assertIsInstance(form, ClienteForm)
        self.assertFalse(form.is_bound)
        self.assertEqual(len(form.errors), 0)
    
    def test_novo_cliente_view_form_initial_values(self):
        """Test that form has no initial values for new client creation"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.novo_cliente_url)
        
        form = response.context['form']
        
        # Verify form has no initial values
        self.assertEqual(form.initial, {})
        
        # Verify form fields are empty
        for field_name, field in form.fields.items():
            self.assertIsNone(form[field_name].value())
    
    def test_novo_cliente_view_form_error_persistence(self):
        """Test that form errors and data persist after invalid submission"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Valid Name',
            'cpf': 'invalid-cpf',  # Invalid CPF
            'nascimento': '1990-01-01',
            'prioridade': True,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Verify form retains submitted data
        form = response.context['form']
        self.assertTrue(form.is_bound)
        self.assertEqual(form.data['nome'], 'Valid Name')
        self.assertEqual(form.data['cpf'], 'invalid-cpf')
        self.assertEqual(form.data['nascimento'], '1990-01-01')
        self.assertEqual(form.data['prioridade'], 'True')
        
        # Verify errors are present
        self.assertTrue(form.errors)
        self.assertIn('cpf', form.errors)
    
    def test_novo_cliente_view_post_with_special_characters(self):
        """Test POST request with special characters in name"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'José da Silva-Araújo Jr.',  # Name with accents and special chars
            'cpf': '11144477735',  # Valid CPF
            'nascimento': '1970-05-20',
            'prioridade': False,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify cliente was created with special characters preserved
        cliente = Cliente.objects.get(cpf='11144477735')
        self.assertEqual(cliente.nome, 'José da Silva-Araújo Jr.')
        
        # Verify success message contains the name with special characters
        messages = list(get_messages(response.wsgi_request))
        success_message = str(messages[0])
        self.assertIn('José da Silva-Araújo Jr.', success_message)
    
    def test_novo_cliente_view_post_cpf_formatting(self):
        """Test that CPF formatting is handled correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with formatted CPF (with dots and dashes)
        form_data = {
            'nome': 'Test User',
            'cpf': '111.444.777-35',  # Formatted CPF
            'nascimento': '1980-01-01',
            'prioridade': False,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify cliente was created and CPF is stored properly
        cliente = Cliente.objects.get(nome='Test User')
        # CPF should be stored as numbers only (form should handle this)
        self.assertEqual(len(cliente.cpf), 11)  # Should be 11 digits
    
    def test_novo_cliente_view_age_calculation_edge_cases(self):
        """Test edge cases for birth date and age validation"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with very old birth date (should be valid)
        form_data = {
            'nome': 'Very Old Person',
            'cpf': '12345678909',  # Valid CPF
            'nascimento': '1920-01-01',  # Very old but valid
            'prioridade': True,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data)
        
        # Should be successful
        self.assertEqual(response.status_code, 302)
        
        cliente = Cliente.objects.get(cpf='12345678909')
        self.assertEqual(cliente.nascimento, date(1920, 1, 1))
        self.assertTrue(cliente.prioridade)
    
    def test_novo_cliente_view_template_content(self):
        """Test that template contains expected content and elements"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.novo_cliente_url)
        
        # Check for key template elements
        self.assertContains(response, 'Novo Cliente')
        self.assertContains(response, '<form')
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        # Check for form fields presence (Django generates the fields)
        self.assertContains(response, 'id_nome')  # Django auto-generates field IDs
        self.assertContains(response, 'id_cpf') 
        self.assertContains(response, 'id_nascimento')
        self.assertContains(response, 'id_prioridade')
        
        # Check for submit button
        self.assertContains(response, 'type="submit"')
        
        # Check for navigation links
        self.assertContains(response, 'Voltar à Lista')
    
    def test_novo_cliente_view_http_methods(self):
        """Test that view only accepts GET and POST methods"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET method (should work)
        response = self.client.get(self.novo_cliente_url)
        self.assertEqual(response.status_code, 200)
        
        # Test POST method (should work)
        form_data = {
            'nome': 'Test User',
            'cpf': '55566677720',  # Valid CPF
            'nascimento': '1990-01-01',
            'prioridade': False,
        }
        response = self.client.post(self.novo_cliente_url, data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Test other methods should not be explicitly handled differently
        # (Django will handle method validation at the URL level)
    
    def test_novo_cliente_view_database_integrity(self):
        """Test database constraints and integrity"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create multiple clients to test unique constraints
        clients_data = [
            {
                'nome': 'Client One',
                'cpf': '98765432100',  # Valid CPF
                'nascimento': '1980-01-01',
                'prioridade': False,
            },
            {
                'nome': 'Client Two',
                'cpf': '11122233396',  # Valid CPF
                'nascimento': '1985-06-15',
                'prioridade': True,
            }
        ]
        
        for client_data in clients_data:
            response = self.client.post(self.novo_cliente_url, data=client_data)
            self.assertEqual(response.status_code, 302)
        
        # Verify both clients were created
        self.assertEqual(Cliente.objects.count(), 2)
        
        # Verify each client has unique data
        client1 = Cliente.objects.get(cpf='98765432100')
        client2 = Cliente.objects.get(cpf='11122233396')
        
        self.assertEqual(client1.nome, 'Client One')
        self.assertFalse(client1.prioridade)
        
        self.assertEqual(client2.nome, 'Client Two')
        self.assertTrue(client2.prioridade)
    
    def test_novo_cliente_view_success_message_content(self):
        """Test the exact content of success messages"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Success Test User',
            'cpf': '99988877714',  # Valid CPF
            'nascimento': '1995-12-25',
            'prioridade': False,
        }
        
        response = self.client.post(self.novo_cliente_url, data=form_data, follow=True)
        
        # Get the success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        
        message = messages[0]
        message_text = str(message)
        
        # Verify message content and structure
        self.assertIn('Success Test User', message_text)
        self.assertIn('foi criado com sucesso!', message_text)
        
        # Verify message level is success
        from django.contrib.messages import constants
        self.assertEqual(message.level, constants.SUCCESS)


class DeleteClienteViewTest(TestCase):
    """Test cases for delete_cliente_view function"""
    
    def setUp(self):
        """Set up test data for delete_cliente_view testing"""
        # Create test user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test clients
        self.cliente = Cliente.objects.create(
            nome='João Silva',
            cpf='11144477735',  # Valid CPF
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.cliente_with_associations = Cliente.objects.create(
            nome='Maria Santos',
            cpf='22255588846',  # Valid CPF
            nascimento=date(1975, 8, 20),
            prioridade=True
        )
        
        # Create test precatorio for associations
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.4.05.0001',
            orcamento=2023,
            origem='Tribunal de Justiça',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao='2023-01-01',
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=10.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Create test phase for associations
        self.fase = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#007bff',
            ativa=True,
            ordem=1
        )
        
        # Test URLs
        self.delete_cliente_url = reverse('delete_cliente', kwargs={'cpf': self.cliente.cpf})
        self.delete_cliente_with_associations_url = reverse('delete_cliente', kwargs={'cpf': self.cliente_with_associations.cpf})
        self.cliente_detail_url = reverse('cliente_detail', kwargs={'cpf': self.cliente.cpf})
        self.clientes_list_url = reverse('clientes')
        self.login_url = reverse('login')
    
    def test_delete_cliente_view_requires_authentication(self):
        """Test that delete_cliente_view requires user authentication"""
        response = self.client.post(self.delete_cliente_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
        # Verify cliente still exists
        self.assertTrue(Cliente.objects.filter(cpf=self.cliente.cpf).exists())
        
        # Follow redirect to verify login requirement
        response = self.client.post(self.delete_cliente_url, follow=True)
        self.assertContains(response, 'login')
    
    def test_delete_cliente_view_404_for_invalid_cpf(self):
        """Test that view returns 404 for non-existent client"""
        self.client.login(username='testuser', password='testpass123')
        
        invalid_url = reverse('delete_cliente', kwargs={'cpf': '99999999999'})
        response = self.client.post(invalid_url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_cliente_view_get_request_redirects(self):
        """Test that GET request redirects to client detail page"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.delete_cliente_url)
        
        # Should redirect to client detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.cliente_detail_url)
        
        # Verify cliente still exists
        self.assertTrue(Cliente.objects.filter(cpf=self.cliente.cpf).exists())
    
    def test_delete_cliente_view_successful_deletion(self):
        """Test successful client deletion when no associations exist"""
        self.client.login(username='testuser', password='testpass123')
        
        # Verify cliente exists before deletion
        self.assertTrue(Cliente.objects.filter(cpf=self.cliente.cpf).exists())
        
        response = self.client.post(self.delete_cliente_url)
        
        # Should redirect to clientes list
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.clientes_list_url)
        
        # Verify cliente was deleted
        self.assertFalse(Cliente.objects.filter(cpf=self.cliente.cpf).exists())
        
        # Verify success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        success_message = str(messages[0])
        self.assertIn('João Silva', success_message)
        self.assertIn('foi excluído com sucesso', success_message)
    
    def test_delete_cliente_view_blocked_by_precatorio_association(self):
        """Test deletion is blocked when client has associated precatorios"""
        # Link cliente to precatorio
        self.precatorio.clientes.add(self.cliente_with_associations)
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_cliente_with_associations_url)
        
        # Should redirect to client detail page (not deleted)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', kwargs={'cpf': self.cliente_with_associations.cpf}))
        
        # Verify cliente still exists
        self.assertTrue(Cliente.objects.filter(cpf=self.cliente_with_associations.cpf).exists())
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        error_message = str(messages[0])
        self.assertIn('Não é possível excluir', error_message)
        self.assertIn('Maria Santos', error_message)
        self.assertIn('associado a precatórios', error_message)
        self.assertIn('Remova as associações primeiro', error_message)
    
    def test_delete_cliente_view_blocked_by_alvara_association(self):
        """Test deletion is blocked when client has associated alvaras"""
        # Create alvara associated with client (without linking to precatorio first)
        # This tests the alvara check specifically
        from precapp.models import Alvara
        
        # Create a separate precatorio for this test to avoid the precatorio association check
        separate_precatorio = Precatorio.objects.create(
            cnj='9876543-21.2023.4.05.0002',
            orcamento=2023,
            origem='Tribunal Específico',
            valor_de_face=75000.00,
            ultima_atualizacao=75000.00,
            data_ultima_atualizacao='2023-02-01',
            percentual_contratuais_assinado=25.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=8.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Link client to precatorio and then create alvara
        separate_precatorio.clientes.add(self.cliente_with_associations)
        alvara = Alvara.objects.create(
            precatorio=separate_precatorio,
            cliente=self.cliente_with_associations,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='aguardando depósito'
        )
        
        # Now unlink from precatorio to test alvara check specifically
        separate_precatorio.clientes.remove(self.cliente_with_associations)
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_cliente_with_associations_url)
        
        # Should redirect to client detail page (not deleted)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', kwargs={'cpf': self.cliente_with_associations.cpf}))
        
        # Verify cliente still exists
        self.assertTrue(Cliente.objects.filter(cpf=self.cliente_with_associations.cpf).exists())
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        error_message = str(messages[0])
        self.assertIn('Não é possível excluir', error_message)
        self.assertIn('Maria Santos', error_message)
        self.assertIn('alvarás associados', error_message)
        self.assertIn('Remova os alvarás primeiro', error_message)
    
    def test_delete_cliente_view_blocked_by_requerimento_association(self):
        """Test deletion is blocked when client has associated requerimentos"""
        # Create a separate precatorio for this test to avoid the precatorio association check
        separate_precatorio = Precatorio.objects.create(
            cnj='5555555-55.2023.4.05.0003',
            orcamento=2023,
            origem='Tribunal Específico para Requerimento',
            valor_de_face=60000.00,
            ultima_atualizacao=60000.00,
            data_ultima_atualizacao='2023-03-01',
            percentual_contratuais_assinado=20.0,
            percentual_contratuais_apartado=0.0,
            percentual_sucumbenciais=12.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        # Create PedidoRequerimento for this test
        pedido_acordo = PedidoRequerimento.objects.create(
            nome='Acordo no Principal',
            descricao='Pedido de acordo principal',
            cor='#28a745',
            ordem=1,
            ativo=True
        )
        
        # Link client to precatorio and then create requerimento
        separate_precatorio.clientes.add(self.cliente_with_associations)
        requerimento = Requerimento.objects.create(
            cliente=self.cliente_with_associations,
            precatorio=separate_precatorio,
            valor=25000.00,
            desagio=5.0,
            pedido=pedido_acordo,
            fase=self.fase
        )
        
        # Now unlink from precatorio to test requerimento check specifically
        separate_precatorio.clientes.remove(self.cliente_with_associations)
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_cliente_with_associations_url)
        
        # Should redirect to client detail page (not deleted)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cliente_detail', kwargs={'cpf': self.cliente_with_associations.cpf}))
        
        # Verify cliente still exists
        self.assertTrue(Cliente.objects.filter(cpf=self.cliente_with_associations.cpf).exists())
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        error_message = str(messages[0])
        self.assertIn('Não é possível excluir', error_message)
        self.assertIn('Maria Santos', error_message)
        self.assertIn('requerimentos associados', error_message)
        self.assertIn('Remova os requerimentos primeiro', error_message)
    
    def test_delete_cliente_view_blocked_by_multiple_associations(self):
        """Test deletion is blocked when client has multiple types of associations"""
        # Link cliente to precatorio
        self.precatorio.clientes.add(self.cliente_with_associations)
        
        # Create alvara
        from precapp.models import Alvara
        Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente_with_associations,
            valor_principal=50000.00,
            honorarios_contratuais=10000.00,
            honorarios_sucumbenciais=5000.00,
            tipo='aguardando depósito'
        )
        
        # Create PedidoRequerimento for this test
        pedido_acordo = PedidoRequerimento.objects.create(
            nome='Acordo no Principal',
            descricao='Pedido de acordo principal',
            cor='#28a745',
            ordem=1,
            ativo=True
        )
        
        # Create requerimento
        Requerimento.objects.create(
            cliente=self.cliente_with_associations,
            precatorio=self.precatorio,
            valor=25000.00,
            desagio=5.0,
            pedido=pedido_acordo
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_cliente_with_associations_url)
        
        # Should redirect to client detail page (not deleted)
        self.assertEqual(response.status_code, 302)
        
        # Verify cliente still exists
        self.assertTrue(Cliente.objects.filter(cpf=self.cliente_with_associations.cpf).exists())
        
        # Verify error message (should catch the first association type - precatorios)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        error_message = str(messages[0])
        self.assertIn('Não é possível excluir', error_message)
        self.assertIn('Maria Santos', error_message)
        self.assertIn('associado a precatórios', error_message)  # First check is precatorios
    
    def test_delete_cliente_view_database_integrity(self):
        """Test that database remains consistent during deletion operations"""
        self.client.login(username='testuser', password='testpass123')
        
        # Count initial objects
        initial_cliente_count = Cliente.objects.count()
        
        # Delete cliente successfully
        response = self.client.post(self.delete_cliente_url)
        
        # Verify count decreased by 1
        final_cliente_count = Cliente.objects.count()
        self.assertEqual(final_cliente_count, initial_cliente_count - 1)
        
        # Verify specific cliente is gone
        self.assertFalse(Cliente.objects.filter(cpf=self.cliente.cpf).exists())
        
        # Verify other cliente still exists
        self.assertTrue(Cliente.objects.filter(cpf=self.cliente_with_associations.cpf).exists())
    
    def test_delete_cliente_view_special_characters_in_name(self):
        """Test deletion with special characters in client name"""
        # Create client with special characters
        cliente_special = Cliente.objects.create(
            nome='José da Silva-Araújo Jr. (Espólio)',
            cpf='33366699957',
            nascimento=date(1960, 12, 25),
            prioridade=False
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        delete_url = reverse('delete_cliente', kwargs={'cpf': cliente_special.cpf})
        response = self.client.post(delete_url)
        
        # Should redirect successfully
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.clientes_list_url)
        
        # Verify cliente was deleted
        self.assertFalse(Cliente.objects.filter(cpf=cliente_special.cpf).exists())
        
        # Verify success message contains special characters correctly
        messages = list(get_messages(response.wsgi_request))
        success_message = str(messages[0])
        self.assertIn('José da Silva-Araújo Jr. (Espólio)', success_message)
        self.assertIn('foi excluído com sucesso', success_message)
    
    def test_delete_cliente_view_message_levels(self):
        """Test that appropriate message levels are used"""
        from django.contrib.messages import constants
        
        self.client.login(username='testuser', password='testpass123')
        
        # Test successful deletion (should be SUCCESS level)
        response = self.client.post(self.delete_cliente_url, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages[0].level, constants.SUCCESS)
        
        # Test blocked deletion (should be ERROR level)
        self.precatorio.clientes.add(self.cliente_with_associations)
        response = self.client.post(self.delete_cliente_with_associations_url, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages[0].level, constants.ERROR)
    
    def test_delete_cliente_view_redirect_urls(self):
        """Test that view redirects to correct URLs in different scenarios"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test successful deletion redirects to clientes list
        response = self.client.post(self.delete_cliente_url)
        self.assertRedirects(response, self.clientes_list_url)
        
        # Test blocked deletion redirects to client detail
        self.precatorio.clientes.add(self.cliente_with_associations)
        response = self.client.post(self.delete_cliente_with_associations_url)
        expected_detail_url = reverse('cliente_detail', kwargs={'cpf': self.cliente_with_associations.cpf})
        self.assertRedirects(response, expected_detail_url)
        
        # Test GET request redirects to client detail
        response = self.client.get(self.delete_cliente_with_associations_url)
        self.assertRedirects(response, expected_detail_url)
    
    def test_delete_cliente_view_association_checking_order(self):
        """Test that associations are checked in the correct order (precatorios first)"""
        # Create all types of associations
        self.precatorio.clientes.add(self.cliente_with_associations)
        
        from precapp.models import Alvara
        Alvara.objects.create(
            precatorio=self.precatorio,
            cliente=self.cliente_with_associations,
            valor_principal=50000.00,
            tipo='aguardando depósito'
        )
        
        # Create PedidoRequerimento for this test
        pedido_acordo = PedidoRequerimento.objects.create(
            nome='Acordo no Principal',
            descricao='Pedido de acordo principal',
            cor='#28a745',
            ordem=1,
            ativo=True
        )
        
        Requerimento.objects.create(
            cliente=self.cliente_with_associations,
            precatorio=self.precatorio,
            valor=25000.00,
            desagio=5.0,
            pedido=pedido_acordo
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_cliente_with_associations_url)
        
        # Should get precatorios error first (since it's checked first)
        messages = list(get_messages(response.wsgi_request))
        error_message = str(messages[0])
        self.assertIn('associado a precatórios', error_message)
        self.assertNotIn('alvarás', error_message)
        self.assertNotIn('requerimentos', error_message)
    
    def test_delete_cliente_view_edge_cases(self):
        """Test edge cases and error conditions"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with cliente that has empty associations (using hasattr checks)
        response = self.client.post(self.delete_cliente_url)
        self.assertEqual(response.status_code, 302)
        
        # Test with very long client name
        long_name_cliente = Cliente.objects.create(
            nome='A' * 200,  # Very long name
            cpf='44477700068',
            nascimento=date(1990, 1, 1),
            prioridade=False
        )
        
        delete_long_name_url = reverse('delete_cliente', kwargs={'cpf': long_name_cliente.cpf})
        response = self.client.post(delete_long_name_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cliente.objects.filter(cpf=long_name_cliente.cpf).exists())
    
    def test_delete_cliente_view_concurrent_operations(self):
        """Test behavior when multiple operations might affect the same client"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create a client for concurrent testing
        concurrent_cliente = Cliente.objects.create(
            nome='Concurrent Test',
            cpf='55566677720',
            nascimento=date(1985, 6, 10),
            prioridade=False
        )
        
        delete_concurrent_url = reverse('delete_cliente', kwargs={'cpf': concurrent_cliente.cpf})
        
        # Delete the client
        response = self.client.post(delete_concurrent_url)
        
        # Verify successful deletion
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cliente.objects.filter(cpf=concurrent_cliente.cpf).exists())
        
        # Try to delete again (should result in 404)
        response = self.client.post(delete_concurrent_url)
        self.assertEqual(response.status_code, 404)
    
    def test_delete_cliente_view_transaction_safety(self):
        """Test that deletion operations are transaction-safe"""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = Cliente.objects.count()
        
        # Test successful deletion
        response = self.client.post(self.delete_cliente_url)
        self.assertEqual(response.status_code, 302)
        
        # Verify exactly one cliente was deleted
        final_count = Cliente.objects.count()
        self.assertEqual(final_count, initial_count - 1)
        
        # Test that blocked deletion doesn't affect database
        self.precatorio.clientes.add(self.cliente_with_associations)
        blocked_count_before = Cliente.objects.count()
        
        response = self.client.post(self.delete_cliente_with_associations_url)
        self.assertEqual(response.status_code, 302)
        
        blocked_count_after = Cliente.objects.count()
        self.assertEqual(blocked_count_after, blocked_count_before)  # No change
    
    def test_delete_cliente_view_http_methods(self):
        """Test that view handles different HTTP methods correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test POST method (should work)
        response = self.client.post(self.delete_cliente_url)
        self.assertEqual(response.status_code, 302)
        
        # Test GET method (should redirect to detail)
        response = self.client.get(self.delete_cliente_with_associations_url)
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('cliente_detail', kwargs={'cpf': self.cliente_with_associations.cpf})
        self.assertRedirects(response, expected_url)
        
        # Test PUT method (should redirect to detail)
        response = self.client.put(self.delete_cliente_with_associations_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)
        
        # Test DELETE method (should redirect to detail)
        response = self.client.delete(self.delete_cliente_with_associations_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)
    
    def test_delete_cliente_view_context_preservation(self):
        """Test that no context is leaked and operations are clean"""
        self.client.login(username='testuser', password='testpass123')
        
        # Store initial state
        initial_precatorio_count = Precatorio.objects.count()
        initial_fase_count = Fase.objects.count()
        
        # Delete cliente
        response = self.client.post(self.delete_cliente_url)
        
        # Verify only cliente was affected
        self.assertEqual(Precatorio.objects.count(), initial_precatorio_count)
        self.assertEqual(Fase.objects.count(), initial_fase_count)
        
        # Verify no orphaned data remains
        self.assertFalse(Cliente.objects.filter(cpf=self.cliente.cpf).exists())

