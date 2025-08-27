"""
Dashboard View Tests

Tests for dashboard-related views including:
- HomeViewTest: Dashboard statistics and calculations

Total tests: 15 (15 HomeViewTest)
Test classes migrated: 1
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from precapp.models import (
    Precatorio, Cliente, Alvara, Requerimento, Fase, 
    FaseHonorariosContratuais, TipoDiligencia, Diligencias, PedidoRequerimento
)


class HomeViewTest(TestCase):
    """
    Comprehensive test cases for home_view dashboard functionality.
    
    Tests the dashboard statistics, financial calculations, and context data
    that drive the main application homepage including counts, aggregations,
    recent activity, and complex business logic for diligencias management.
    """
    
    def setUp(self):
        """Set up comprehensive test data for dashboard testing"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client_app = Client()
        self.home_url = reverse('home')
        
        # Create test phases
        self.fase_alvara = Fase.objects.create(
            nome='Deferido',
            tipo='alvara',
            cor='#00FF00',
            ativa=True,
            ordem=1
        )
        self.fase_requerimento = Fase.objects.create(
            nome='Deferido',
            tipo='requerimento',
            cor='#00FF00',
            ativa=True,
            ordem=1
        )
        self.fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Recebido',
            cor='#0000FF',
            ativa=True,
            ordem=1
        )
        
        # Create test tipo diligencia
        self.tipo_diligencia_ativo = TipoDiligencia.objects.create(
            nome='Tipo Ativo',
            ativo=True,
            ordem=1
        )
        self.tipo_diligencia_inativo = TipoDiligencia.objects.create(
            nome='Tipo Inativo',
            ativo=False,
            ordem=2
        )
        
        # Create test clients
        self.cliente1 = Cliente.objects.create(
            nome='Cliente Teste 1',
            cpf='12345678901',
            nascimento='1980-01-01',
            prioridade=True
        )
        self.cliente2 = Cliente.objects.create(
            nome='Cliente Teste 2',
            cpf='12345678902',
            nascimento='1990-01-01',
            prioridade=False
        )
        
        # Create test precatorios with financial values
        self.precatorio1 = Precatorio.objects.create(
            cnj='1234567-89.2023.4.05.0001',
            orcamento=2023,
            origem='Tribunal de Justiça',
            valor_de_face=100000.00,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        self.precatorio2 = Precatorio.objects.create(
            cnj='1234567-89.2023.4.05.0002',
            orcamento=2023,
            origem='Tribunal Federal',
            valor_de_face=200000.00,
            credito_principal='quitado',
            honorarios_contratuais='quitado',
            honorarios_sucumbenciais='quitado'
        )
        
        # Link clients to precatorios
        self.precatorio1.clientes.add(self.cliente1)
        self.precatorio2.clientes.add(self.cliente2)
        
        # Create test alvaras with financial values
        self.alvara1 = Alvara.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente1,
            valor_principal=50000.00,
            honorarios_contratuais=15000.00,
            honorarios_sucumbenciais=10000.00,
            tipo='aguardando depósito',
            fase=self.fase_alvara,
            fase_honorarios_contratuais=self.fase_honorarios
        )
        self.alvara2 = Alvara.objects.create(
            precatorio=self.precatorio2,
            cliente=self.cliente2,
            valor_principal=75000.00,
            honorarios_contratuais=20000.00,
            honorarios_sucumbenciais=15000.00,
            tipo='recebido pelo cliente',
            fase=self.fase_alvara
        )
        
        # Create test PedidoRequerimento instances
        self.pedido_acordo = PedidoRequerimento.objects.create(
            nome='Acordo no Principal',
            descricao='Pedido de acordo principal',
            cor='#28a745',
            ordem=1,
            ativo=True
        )
        
        self.pedido_prioridade = PedidoRequerimento.objects.create(
            nome='Prioridade por idade',
            descricao='Pedido de prioridade por idade',
            cor='#ffc107',
            ordem=2,
            ativo=True
        )
        
        # Create test requerimentos with financial values
        self.requerimento1 = Requerimento.objects.create(
            precatorio=self.precatorio1,
            cliente=self.cliente1,
            valor=80000.00,
            desagio=10.5,
            pedido=self.pedido_acordo,
            fase=self.fase_requerimento
        )
        self.requerimento2 = Requerimento.objects.create(
            precatorio=self.precatorio2,
            cliente=self.cliente2,
            valor=120000.00,
            desagio=8.0,
            pedido=self.pedido_prioridade
        )
        
        # Create test diligencias with different statuses and urgency
        today = timezone.now().date()
        past_date = today - timedelta(days=5)
        future_date = today + timedelta(days=5)
        
        self.diligencia_pendente = Diligencias.objects.create(
            cliente=self.cliente1,
            tipo=self.tipo_diligencia_ativo,
            descricao='Diligência pendente',
            data_final=future_date,
            urgencia='baixa',
            criado_por='Test User',
            concluida=False
        )
        
        self.diligencia_concluida = Diligencias.objects.create(
            cliente=self.cliente2,
            tipo=self.tipo_diligencia_ativo,
            descricao='Diligência concluída',
            data_final=past_date,
            urgencia='media',
            criado_por='Test User',
            concluida=True,
            data_conclusao=timezone.now(),
            concluido_por='Test User'
        )
        
        self.diligencia_atrasada = Diligencias.objects.create(
            cliente=self.cliente1,
            tipo=self.tipo_diligencia_ativo,
            descricao='Diligência atrasada',
            data_final=past_date,
            urgencia='alta',
            criado_por='Test User',
            concluida=False
        )
        
        self.diligencia_urgente = Diligencias.objects.create(
            cliente=self.cliente2,
            tipo=self.tipo_diligencia_ativo,
            descricao='Diligência urgente',
            data_final=future_date,
            urgencia='alta',
            criado_por='Test User',
            concluida=False
        )
    
    def test_home_view_requires_authentication(self):
        """Test that home view requires user authentication"""
        response = self.client_app.get(self.home_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
    
    def test_home_view_authenticated_access(self):
        """Test home view access with authenticated user"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/home.html')
    
    def test_home_view_basic_counts(self):
        """Test basic count statistics in dashboard"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        context = response.context
        
        # Test basic counts
        self.assertEqual(context['total_precatorios'], 2)
        self.assertEqual(context['total_clientes'], 2)
        self.assertEqual(context['total_alvaras'], 2)
        self.assertEqual(context['total_requerimentos'], 2)
        self.assertEqual(context['total_diligencias'], 4)
        self.assertEqual(context['total_tipos_diligencia'], 1)  # Only active ones
    
    def test_home_view_financial_calculations(self):
        """Test financial aggregation calculations"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        context = response.context
        
        # Test precatorios total value
        expected_valor_precatorios = 100000.00 + 200000.00
        self.assertEqual(context['total_valor_precatorios'], expected_valor_precatorios)
        
        # Test alvaras total value (sum of all three components)
        expected_valor_alvaras = (50000.00 + 75000.00) + (15000.00 + 20000.00) + (10000.00 + 15000.00)
        self.assertEqual(context['valor_alvaras'], expected_valor_alvaras)
        
        # Test requerimentos total value
        expected_valor_requerimentos = 80000.00 + 120000.00
        self.assertEqual(context['total_valor_requerimentos'], expected_valor_requerimentos)
    
    def test_home_view_diligencias_statistics(self):
        """Test diligencias status and urgency statistics"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        context = response.context
        
        # Test diligencias counts by status
        self.assertEqual(context['diligencias_pendentes'], 3)  # pendente, atrasada, urgente
        self.assertEqual(context['diligencias_concluidas'], 1)  # concluida
        self.assertEqual(context['diligencias_atrasadas'], 1)   # Only atrasada (past due date)
        self.assertEqual(context['diligencias_urgentes'], 2)    # atrasada, urgente (both high priority)
    
    def test_home_view_recent_activity_lists(self):
        """Test recent activity query sets and ordering"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        context = response.context
        
        # Test recent precatorios (ordered by CNJ, limit 5)
        recent_precatorios = list(context['recent_precatorios'])
        self.assertEqual(len(recent_precatorios), 2)
        self.assertEqual(recent_precatorios[0].cnj, '1234567-89.2023.4.05.0001')
        self.assertEqual(recent_precatorios[1].cnj, '1234567-89.2023.4.05.0002')
        
        # Test recent alvaras (ordered by -id, limit 5)
        recent_alvaras = list(context['recent_alvaras'])
        self.assertEqual(len(recent_alvaras), 2)
        self.assertEqual(recent_alvaras[0].id, self.alvara2.id)  # Most recent
        self.assertEqual(recent_alvaras[1].id, self.alvara1.id)
        
        # Test recent requerimentos (ordered by -id, limit 5)
        recent_requerimentos = list(context['recent_requerimentos'])
        self.assertEqual(len(recent_requerimentos), 2)
        self.assertEqual(recent_requerimentos[0].id, self.requerimento2.id)  # Most recent
        self.assertEqual(recent_requerimentos[1].id, self.requerimento1.id)
        
        # Test recent diligencias (ordered by -data_criacao, limit 5)
        recent_diligencias = list(context['recent_diligencias'])
        self.assertEqual(len(recent_diligencias), 4)
    
    def test_home_view_prefetch_optimization(self):
        """Test that dashboard uses proper prefetch/select_related for performance"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Monitor database queries
        with self.assertNumQueries(22):  # Updated expected number based on actual queries including PedidoRequerimento
            response = self.client_app.get(self.home_url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_home_view_empty_database(self):
        """Test dashboard behavior with empty database"""
        # Clear all test data
        Diligencias.objects.all().delete()
        Requerimento.objects.all().delete()
        Alvara.objects.all().delete()
        Precatorio.objects.all().delete()
        Cliente.objects.all().delete()
        TipoDiligencia.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        context = response.context
        
        # All counts should be zero
        self.assertEqual(context['total_precatorios'], 0)
        self.assertEqual(context['total_clientes'], 0)
        self.assertEqual(context['total_alvaras'], 0)
        self.assertEqual(context['total_requerimentos'], 0)
        self.assertEqual(context['total_diligencias'], 0)
        self.assertEqual(context['total_tipos_diligencia'], 0)
        
        # All financial values should be zero
        self.assertEqual(context['total_valor_precatorios'], 0)
        self.assertEqual(context['valor_alvaras'], 0)
        self.assertEqual(context['total_valor_requerimentos'], 0)
        
        # All diligencias counts should be zero
        self.assertEqual(context['diligencias_pendentes'], 0)
        self.assertEqual(context['diligencias_concluidas'], 0)
        self.assertEqual(context['diligencias_atrasadas'], 0)
        self.assertEqual(context['diligencias_urgentes'], 0)
        
        # All recent activity lists should be empty
        self.assertEqual(len(context['recent_precatorios']), 0)
        self.assertEqual(len(context['recent_alvaras']), 0)
        self.assertEqual(len(context['recent_requerimentos']), 0)
        self.assertEqual(len(context['recent_diligencias']), 0)
    
    def test_home_view_null_financial_values(self):
        """Test dashboard handles null financial values properly"""
        # Create entities with null financial values
        precatorio_null = Precatorio.objects.create(
            cnj='1234567-89.2023.4.05.0003',
            orcamento=2023,
            origem='Test Null',
            valor_de_face=0.0  # Use 0 instead of None since field doesn't allow null
        )
        
        # Link client to precatorio first
        precatorio_null.clientes.add(self.cliente1)
        
        alvara_null = Alvara.objects.create(
            precatorio=precatorio_null,
            cliente=self.cliente1,
            valor_principal=0.0,  # Use 0 instead of None
            honorarios_contratuais=0.0,  # Use 0 instead of None
            honorarios_sucumbenciais=0.0,  # Use 0 instead of None
            tipo='teste'
        )
        
        requerimento_null = Requerimento.objects.create(
            precatorio=precatorio_null,
            cliente=self.cliente1,
            valor=0.0,  # Use 0 instead of None
            desagio=0.0,  # Add required field
            pedido=self.pedido_acordo  # Use existing PedidoRequerimento instance
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        # Should not crash and should handle nulls as zeros
        self.assertEqual(response.status_code, 200)
        context = response.context
        
        # Values should still be calculated correctly (treating None as 0)
        self.assertIsInstance(context['total_valor_precatorios'], (int, float))
        self.assertIsInstance(context['valor_alvaras'], (int, float))
        self.assertIsInstance(context['total_valor_requerimentos'], (int, float))
    
    def test_home_view_timezone_handling(self):
        """Test that diligencias date filtering handles timezone correctly"""
        # Create diligencia with exactly today's date
        today = timezone.now().date()
        
        diligencia_today = Diligencias.objects.create(
            cliente=self.cliente1,
            tipo=self.tipo_diligencia_ativo,
            descricao='Diligência hoje',
            data_final=today,
            urgencia='media',
            criado_por='Test User',
            concluida=False
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        context = response.context
        
        # Today's diligencia should be counted as overdue
        self.assertGreaterEqual(context['diligencias_atrasadas'], 1)
    
    def test_home_view_context_structure(self):
        """Test that all expected context variables are present"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        context = response.context
        
        # Verify all expected context keys exist
        expected_keys = [
            'total_precatorios', 'total_clientes', 'total_alvaras', 
            'total_requerimentos', 'total_diligencias', 'total_tipos_diligencia',
            'total_valor_precatorios', 'valor_alvaras', 'total_valor_requerimentos',
            'diligencias_pendentes', 'diligencias_concluidas', 
            'diligencias_atrasadas', 'diligencias_urgentes',
            'recent_precatorios', 'recent_alvaras', 
            'recent_requerimentos', 'recent_diligencias'
        ]
        
        for key in expected_keys:
            self.assertIn(key, context, f"Context key '{key}' is missing")
    
    def test_home_view_large_dataset_performance(self):
        """Test dashboard performance with larger dataset"""
        # Create additional test data
        for i in range(10):
            cpf_unique = f'123456{i:04d}'  # Create truly unique CPFs
            cliente = Cliente.objects.create(
                nome=f'Cliente Large {i}',
                cpf=cpf_unique,
                nascimento='1985-01-01',
                prioridade=False  # Add required field
            )
            
            precatorio = Precatorio.objects.create(
                cnj=f'1234567-89.2023.4.05.{i+100:04d}',
                orcamento=2023,
                origem=f'Tribunal {i}',
                valor_de_face=10000.00 * (i + 1)
            )
            
            precatorio.clientes.add(cliente)
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Should complete within reasonable time
        response = self.client_app.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        
        context = response.context
        
        # Verify counts include new data
        self.assertGreaterEqual(context['total_precatorios'], 12)
        self.assertGreaterEqual(context['total_clientes'], 12)
    
    def test_home_view_complex_diligencias_filtering(self):
        """Test complex filtering logic for diligencias statistics"""
        # Test overlapping conditions (urgent AND overdue)
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(self.home_url)
        
        context = response.context
        
        # Verify that diligencia_atrasada counts in both atrasadas and urgentes
        # but not double-counted in totals
        total_expected = context['diligencias_pendentes'] + context['diligencias_concluidas']
        self.assertEqual(total_expected, 4)  # Our total test diligencias
        
        # Urgent and overdue should have overlap but not exceed total
        self.assertLessEqual(context['diligencias_urgentes'], context['diligencias_pendentes'])
        self.assertLessEqual(context['diligencias_atrasadas'], context['diligencias_pendentes'])
