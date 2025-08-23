"""
Core Business Flow Integration Tests

This module contains integration tests for the most critical daily business work        # Cr        # Create clients with different profiles using valid CPFs
        cliente_priority = Cliente.objects.create(
            cpf='12345678909',  # Valid CPF
            nome='Maria Silva Santos',
            nascimento=date(1960, 3, 15),  # 65 years old - priority
            prioridade=True
        )
        
        cliente_normal = Cliente.objects.create(
            cpf='98765432100',  # Valid CPF  
            nome='João Oliveira',
            nascimento=date(1985, 8, 22),  # 39 years old - normal
            prioridade=False
        )ith different profiles using valid CPFs
        cliente_priority = Cliente.objects.create(
            cpf='12345678909',  # Valid CPF
            nome='Maria Silva Santos',
            nascimento=date(1960, 3, 15),  # 65 years old - priority
            prioridade=True
        )
        
        cliente_normal = Cliente.objects.create(
            cpf='98765432100',  # Valid CPF  
            nome='João Oliveira',
            nascimento=date(1985, 8, 22),  # 39 years old - normal
            prioridade=False
        )precatorios system. These tests validate complete end-to-e        # Step        # Step 3: Prepare precatorio creation data with proper CNJ format
        precatorio_data = {
            'cnj': '5555555-55.2024.8.26.0200',
            'orcamento': '2024',
            'origem': '9876543-21.2022.8.26.0001',  # Valid CNJ format, 25 chars
            'valor_de_face': '200000.00',
            'ultima_atualizacao': '200000.00',
            'data_ultima_atualizacao': '15/08/2024',
            'percentual_contratuais_assinado': '25.0',
            'percentual_contratuais_apartado': '0.0',
            'percentual_sucumbenciais': '15.0',
            'credito_principal': 'pendente',precatorio creation data with proper CNJ format
        precatorio_data = {
            'cnj': '5555555-55.2024.8.26.0200',
            'orcamento': '2024',
            'origem': '9876543-21.2022.8.26.0001',  # Valid CNJ format, 25 chars
            'valor_de_face': '200000.00',
            'ultima_atualizacao': '200000.00',
            'data_ultima_atualizacao': '15/08/2024',
            'percentual_contratuais_assinado': '25.0',
            'percentual_contratuais_apartado': '0.0',
            'percentual_sucumbenciais': '15.0',
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        }at
users perform regularly.

Test Coverage:
- Complete Precatorio Lifecycle (P001-P005)
- Document Creation Workflows (R001, A001, A002)
- Client-Precatorio Integration (C001, C002, P007)
- Phase Management Basics (CU001, CU006)
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from datetime import date, timedelta
from decimal import Decimal

from precapp.models import (
    Precatorio, Cliente, Alvara, Requerimento, 
    Fase, FaseHonorariosContratuais, TipoDiligencia, Diligencias
)
from precapp.forms import PrecatorioForm, ClienteForm, AlvaraSimpleForm, RequerimentoForm


class IntegrationTestDataFactory:
    """Factory for creating comprehensive, realistic test data"""
    
    @classmethod
    def create_complete_scenario(cls):
        """Create a complete test scenario with all relationships"""
        # Create user for authentication
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create phases for different document types
        fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True,
            ordem=1
        )
        
        fase_requerimento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True,
            ordem=1
        )
        
        fase_ambos = Fase.objects.create(
            nome='Cancelado',
            tipo='ambos',
            cor='#95A5A6',
            ativa=True,
            ordem=2
        )
        
        # Create honorários phases
        fase_honorarios_1 = FaseHonorariosContratuais.objects.create(
            nome='Aguardando Pagamento',
            descricao='Honorários aguardando pagamento',
            cor='#FFA500',
            ativa=True,
            ordem=1
        )
        
        fase_honorarios_2 = FaseHonorariosContratuais.objects.create(
            nome='Parcialmente Pago',
            descricao='Honorários parcialmente pagos',
            cor='#FFC107',
            ativa=True,
            ordem=2
        )
        
        # Create precatorio with realistic data and proper CNJ format
        precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='9876543-21.2022.8.26.0001',  # Valid CNJ format, 25 chars
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente',
            valor_de_face=150000.00,
            ultima_atualizacao=150000.00,
            data_ultima_atualizacao=date(2023, 6, 15),
            percentual_contratuais_assinado=30.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0
        )
        
        # Create clients with different profiles
        cliente_priority = Cliente.objects.create(
            cpf='12345678909',
            nome='Maria Silva Santos',
            nascimento=date(1960, 3, 15),  # 65 years old - priority
            prioridade=True
        )
        
        cliente_regular = Cliente.objects.create(
            cpf='11144477735',
            nome='João Pedro Oliveira',
            nascimento=date(1985, 8, 20),  # 40 years old - regular
            prioridade=False
        )
        
        # Create diligencia types
        tipo_urgente = TipoDiligencia.objects.create(
            nome='Urgente',
            cor='#dc3545',
            ativo=True
        )
        
        return {
            'user': user,
            'precatorio': precatorio,
            'cliente_priority': cliente_priority,
            'cliente_regular': cliente_regular,
            'fase_alvara': fase_alvara,
            'fase_requerimento': fase_requerimento,
            'fase_ambos': fase_ambos,
            'fase_honorarios_1': fase_honorarios_1,
            'fase_honorarios_2': fase_honorarios_2,
            'tipo_urgente': tipo_urgente,
        }


class CoreBusinessFlowTests(TestCase):
    """Integration tests for core business workflows"""
    
    def setUp(self):
        """Set up comprehensive test data for all workflows"""
        self.test_data = IntegrationTestDataFactory.create_complete_scenario()
        self.user = self.test_data['user']
        self.client_app = Client()
        
    def assert_complete_flow_integrity(self, workflow_context):
        """
        Comprehensive assertions that validate complete workflow integrity
        
        Args:
            workflow_context: Dictionary containing objects to validate
        """
        # Verify database consistency
        if 'precatorio' in workflow_context:
            precatorio = workflow_context['precatorio']
            # Ensure precatorio exists and has proper relationships
            self.assertTrue(Precatorio.objects.filter(cnj=precatorio.cnj).exists())
            
        if 'cliente' in workflow_context:
            cliente = workflow_context['cliente']
            # Ensure cliente exists and relationships are intact
            self.assertTrue(Cliente.objects.filter(cpf=cliente.cpf).exists())
            
        if 'alvara' in workflow_context:
            alvara = workflow_context['alvara']
            # Ensure alvara relationships are correct
            self.assertEqual(alvara.precatorio, workflow_context.get('precatorio'))
            self.assertEqual(alvara.cliente, workflow_context.get('cliente'))
            
        if 'requerimento' in workflow_context:
            requerimento = workflow_context['requerimento']
            # Ensure requerimento relationships are correct
            self.assertEqual(requerimento.precatorio, workflow_context.get('precatorio'))
            self.assertEqual(requerimento.cliente, workflow_context.get('cliente'))

    def test_flow_P001_create_precatorio_link_existing_client(self):
        """
        FLOW P001: Create precatorio + immediately link existing client
        
        WORKFLOW:
        1. User logs in
        2. Navigate to novo precatorio
        3. Fill precatorio form with valid data
        4. Submit and create precatorio
        5. Navigate to precatorio detail
        6. Search and link existing client
        7. Verify relationship is established
        8. Verify data integrity across modules
        """
        # Step 1: User authentication
        login_success = self.client_app.login(username='testuser', password='testpass123')
        self.assertTrue(login_success, "User should be able to log in")
        
        # Step 2: Navigate to novo precatorio page
        response = self.client_app.get(reverse('novo_precatorio'))
        self.assertEqual(response.status_code, 200, "Novo precatorio page should be accessible")
        
        # Step 3: Fill and submit precatorio form with proper CNJ format
        precatorio_data = {
            'cnj': '5555555-55.2024.8.26.0200',
            'orcamento': '2024',
            'origem': '9876543-21.2022.8.26.0001',  # Valid CNJ format, 25 chars
            'valor_de_face': '200000.00',
            'ultima_atualizacao': '200000.00',
            'data_ultima_atualizacao': '15/08/2024',
            'percentual_contratuais_assinado': '25.0',
            'percentual_contratuais_apartado': '0.0',
            'percentual_sucumbenciais': '15.0',
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        }
        
        # Step 4: Submit precatorio creation
        response = self.client_app.post(reverse('novo_precatorio'), data=precatorio_data)
        
        # Debug: Check if form has errors
        if response.status_code == 200:
            if 'form' in response.context and response.context['form'].errors:
                self.fail(f"Precatorio form validation failed: {response.context['form'].errors}")
            elif 'form' in response.context:
                self.fail(f"Precatorio form returned 200 but no errors found. Form is valid: {response.context['form'].is_valid()}")
            else:
                self.fail("Precatorio form returned 200 but no form in context")
        
        self.assertEqual(response.status_code, 302, "Precatorio creation should redirect")
        
        # Verify precatorio was created
        created_precatorio = Precatorio.objects.get(cnj='5555555-55.2024.8.26.0200')
        self.assertIsNotNone(created_precatorio, "Precatorio should be created in database")
        
        # Step 5: Navigate to precatorio detail
        response = self.client_app.get(reverse('precatorio_detalhe', args=[created_precatorio.cnj]))
        self.assertEqual(response.status_code, 200, "Precatorio detail page should be accessible")
        
        # Step 6: Link existing client using proper form fields
        existing_client = self.test_data['cliente_priority']
        link_data = {
            'link_cliente': '1',  # Button name to trigger client linking
            'cpf': existing_client.cpf  # CPF field expected by ClienteSearchForm
        }
        
        response = self.client_app.post(
            reverse('precatorio_detalhe', args=[created_precatorio.cnj]), 
            data=link_data
        )
        
        # Debug: Check if client linking form has errors
        if response.status_code == 200:
            # Check for Django messages (errors, warnings)
            messages = list(get_messages(response.wsgi_request))
            if messages:
                message_texts = [str(msg) for msg in messages]
                self.fail(f"Client linking returned 200 with messages: {message_texts}")
            
            if 'form' in response.context and hasattr(response.context['form'], 'errors') and response.context['form'].errors:
                self.fail(f"Client linking form validation failed: {response.context['form'].errors}")
            else:
                # Check what data was actually sent
                self.fail(f"Client linking returned 200 but no form errors detected")
        
        self.assertEqual(response.status_code, 302, "Client linking should redirect")
        
        # Step 7: Verify relationship is established
        created_precatorio.refresh_from_db()
        self.assertIn(existing_client, created_precatorio.clientes.all(), 
                     "Client should be linked to precatorio")
        
        # Step 8: Verify complete integrity
        workflow_context = {
            'precatorio': created_precatorio,
            'cliente': existing_client
        }
        self.assert_complete_flow_integrity(workflow_context)
        
        # Verify success message was displayed
        response = self.client_app.get(reverse('precatorio_detalhe', args=[created_precatorio.cnj]))
        self.assertContains(response, existing_client.nome, 
                           msg_prefix="Client should appear in precatorio detail view")

    def test_flow_P002_create_precatorio_create_new_client_link(self):
        """
        FLOW P002: Create precatorio + create new client + link
        
        WORKFLOW:
        1. User logs in
        2. Navigate to novo precatorio
        3. Create precatorio
        4. Navigate to precatorio detail
        5. Create new client directly from precatorio detail
        6. Verify automatic linking
        7. Verify complete integration
        """
        # Step 1: Authentication
        self.client_app.login(username='testuser', password='testpass123')
        
        # Step 2-3: Create precatorio (simplified) with proper CNJ format
        precatorio_data = {
            'cnj': '6666666-66.2024.8.26.0300',
            'orcamento': '2024',
            'origem': '8765432-10.2023.8.26.0002',  # Valid CNJ format, 25 chars
            'valor_de_face': '300000.00',
            'ultima_atualizacao': '300000.00',
            'data_ultima_atualizacao': '20/08/2024',
            'percentual_contratuais_assinado': '20.0',
            'percentual_contratuais_apartado': '5.0',
            'percentual_sucumbenciais': '25.0',
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        }
        
        self.client_app.post(reverse('novo_precatorio'), data=precatorio_data)
        created_precatorio = Precatorio.objects.get(cnj='6666666-66.2024.8.26.0300')
        
        # Step 4: Navigate to precatorio detail
        response = self.client_app.get(reverse('precatorio_detalhe', args=[created_precatorio.cnj]))
        self.assertEqual(response.status_code, 200)
        
        # Step 5: Create new client from precatorio detail
        new_client_data = {
            'create_cliente': '1',
            'cpf': '52998224725',  # Unique valid CPF, different from data factory
            'nome': 'Ana Carolina Ferreira',
            'nascimento': '1975-04-12',  # ISO format instead of DD/MM/YYYY
            'prioridade': False
        }
        
        response = self.client_app.post(
            reverse('precatorio_detalhe', args=[created_precatorio.cnj]),
            data=new_client_data
        )
        self.assertEqual(response.status_code, 302, "Client creation should redirect")
        
        # Step 6: Verify automatic linking
        created_client = Cliente.objects.get(cpf='52998224725')  # Valid CPF
        created_precatorio.refresh_from_db()
        
        self.assertIn(created_client, created_precatorio.clientes.all(),
                     "New client should be automatically linked to precatorio")
        
        # Step 7: Verify complete integration
        workflow_context = {
            'precatorio': created_precatorio,
            'cliente': created_client
        }
        self.assert_complete_flow_integrity(workflow_context)

    def test_flow_A001_create_alvara_from_precatorio_detail(self):
        """
        FLOW A001: Create alvara from precatorio detail page
        
        WORKFLOW:
        1. Setup precatorio with linked client
        2. Navigate to precatorio detail
        3. Fill alvara creation form
        4. Submit alvara with both regular and honorários phases
        5. Verify alvara creation and relationships
        6. Verify phase assignments work correctly
        """
        # Step 1: Setup precatorio with linked client
        precatorio = self.test_data['precatorio']
        cliente = self.test_data['cliente_priority']
        precatorio.clientes.add(cliente)
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Step 2: Navigate to precatorio detail
        response = self.client_app.get(reverse('precatorio_detalhe', args=[precatorio.cnj]))
        self.assertEqual(response.status_code, 200)
        
        # Step 3-4: Create alvara with both phase types
        alvara_data = {
            'create_alvara': '1',
            'cliente_cpf': cliente.cpf,
            'tipo': 'prioridade',
            'valor_principal': '50000.00',
            'honorarios_contratuais': '15000.00',
            'honorarios_sucumbenciais': '7500.00',
            'fase': self.test_data['fase_alvara'].id,
            'fase_honorarios_contratuais': self.test_data['fase_honorarios_1'].id
        }
        
        response = self.client_app.post(
            reverse('precatorio_detalhe', args=[precatorio.cnj]),
            data=alvara_data
        )
        self.assertEqual(response.status_code, 302, "Alvara creation should redirect")
        
        # Step 5: Verify alvara creation and relationships
        created_alvara = Alvara.objects.get(
            precatorio=precatorio,
            cliente=cliente,
            valor_principal=50000.00
        )
        
        self.assertEqual(created_alvara.tipo, 'prioridade')
        self.assertEqual(float(created_alvara.honorarios_contratuais), 15000.00)
        self.assertEqual(float(created_alvara.honorarios_sucumbenciais), 7500.00)
        
        # Step 6: Verify phase assignments
        self.assertEqual(created_alvara.fase, self.test_data['fase_alvara'])
        self.assertEqual(created_alvara.fase_honorarios_contratuais, 
                        self.test_data['fase_honorarios_1'])
        
        # Verify complete integrity
        workflow_context = {
            'precatorio': precatorio,
            'cliente': cliente,
            'alvara': created_alvara
        }
        self.assert_complete_flow_integrity(workflow_context)

    def test_flow_R001_create_requerimento_from_precatorio_detail(self):
        """
        FLOW R001: Create requerimento from precatorio detail page
        
        WORKFLOW:
        1. Setup precatorio with linked client
        2. Navigate to precatorio detail
        3. Fill requerimento creation form
        4. Submit requerimento with proper phase
        5. Verify requerimento creation and relationships
        6. Verify phase filtering works correctly
        """
        # Step 1: Setup
        precatorio = self.test_data['precatorio']
        cliente = self.test_data['cliente_regular']
        precatorio.clientes.add(cliente)
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Step 2: Navigate to precatorio detail
        response = self.client_app.get(reverse('precatorio_detalhe', args=[precatorio.cnj]))
        self.assertEqual(response.status_code, 200)
        
        # Step 3-4: Create requerimento
        requerimento_data = {
            'create_requerimento': '1',
            'cliente_cpf': cliente.cpf,
            'pedido': 'acordo principal',
            'valor': '25000.00',
            'desagio': '10.5',
            'fase': self.test_data['fase_requerimento'].id
        }
        
        response = self.client_app.post(
            reverse('precatorio_detalhe', args=[precatorio.cnj]),
            data=requerimento_data
        )
        self.assertEqual(response.status_code, 302, "Requerimento creation should redirect")
        
        # Step 5: Verify requerimento creation
        created_requerimento = Requerimento.objects.get(
            precatorio=precatorio,
            cliente=cliente,
            pedido='acordo principal'
        )
        
        self.assertEqual(float(created_requerimento.valor), 25000.00)
        self.assertEqual(float(created_requerimento.desagio), 10.5)
        self.assertEqual(created_requerimento.fase, self.test_data['fase_requerimento'])
        
        # Step 6: Verify requerimento doesn't have honorários phase
        self.assertIsNone(getattr(created_requerimento, 'fase_honorarios_contratuais', None),
                         "Requerimento should not have honorários phase")
        
        # Verify complete integrity
        workflow_context = {
            'precatorio': precatorio,
            'cliente': cliente,
            'requerimento': created_requerimento
        }
        self.assert_complete_flow_integrity(workflow_context)

    def test_flow_C001_create_client_link_to_existing_precatorio(self):
        """
        FLOW C001: Create client + immediately link to existing precatorio
        
        WORKFLOW:
        1. Setup existing precatorio 
        2. Navigate to precatorio detail page
        3. Use "create client" feature from precatorio detail (automatic linking)
        4. Verify client creation
        5. Verify automatic precatorio linking
        6. Verify relationship integrity
        """
        # Step 1: Setup and navigate
        precatorio = self.test_data['precatorio']
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('precatorio_detalhe', args=[precatorio.cnj]))
        self.assertEqual(response.status_code, 200)
        
        # Step 2-3: Create client using precatorio detail page (automatic linking)
        client_data = {
            'create_cliente': '1',  # This tells the view to handle client creation with linking
            'cpf': '01000006301',  # Valid CPF generated for C001
            'nome': 'Carlos Eduardo Santos',
            'nascimento': '1970-12-25',  # ISO format
            'prioridade': False,
        }
        
        response = self.client_app.post(reverse('precatorio_detalhe', args=[precatorio.cnj]), data=client_data)
        self.assertEqual(response.status_code, 302, "Client creation should redirect")
        
        # Step 4: Verify client creation
        created_client = Cliente.objects.get(cpf='01000006301')  # Valid CPF for C001
        self.assertEqual(created_client.nome, 'Carlos Eduardo Santos')
        
        # Step 5: Verify automatic precatorio linking
        precatorio.refresh_from_db()
        self.assertIn(created_client, precatorio.clientes.all(),
                     "Client should be automatically linked to specified precatorio")
        
        # Step 6: Verify complete integrity
        workflow_context = {
            'precatorio': precatorio,
            'cliente': created_client
        }
        self.assert_complete_flow_integrity(workflow_context)

    def test_flow_P007_link_multiple_clients_to_single_precatorio(self):
        """
        FLOW P007: Link multiple clients to single precatorio
        
        WORKFLOW:
        1. Create precatorio
        2. Link first client
        3. Link second client
        4. Verify multiple relationships
        5. Create documents for different clients
        6. Verify complex relationship integrity
        """
        # Step 1: Use existing precatorio
        precatorio = self.test_data['precatorio']
        client1 = self.test_data['cliente_priority']
        client2 = self.test_data['cliente_regular']
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Step 2: Link first client
        link_data1 = {
            'link_cliente': '1',
            'cpf': client1.cpf
        }
        
        response = self.client_app.post(
            reverse('precatorio_detalhe', args=[precatorio.cnj]),
            data=link_data1
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 3: Link second client
        link_data2 = {
            'link_cliente': '1',
            'cpf': client2.cpf
        }
        
        response = self.client_app.post(
            reverse('precatorio_detalhe', args=[precatorio.cnj]),
            data=link_data2
        )
        self.assertEqual(response.status_code, 302)
        
        # Step 4: Verify multiple relationships
        precatorio.refresh_from_db()
        linked_clients = precatorio.clientes.all()
        
        self.assertIn(client1, linked_clients, "First client should be linked")
        self.assertIn(client2, linked_clients, "Second client should be linked")
        self.assertEqual(linked_clients.count(), 2, "Should have exactly 2 linked clients")
        
        # Step 5: Create documents for different clients
        # Create alvara for client1
        alvara_data = {
            'create_alvara': '1',
            'cliente_cpf': client1.cpf,
            'tipo': 'prioridade',
            'valor_principal': '30000.00',
            'honorarios_contratuais': '9000.00',
            'honorarios_sucumbenciais': '4500.00',
            'fase': self.test_data['fase_alvara'].id
        }
        
        self.client_app.post(
            reverse('precatorio_detalhe', args=[precatorio.cnj]),
            data=alvara_data
        )
        
        # Create requerimento for client2
        requerimento_data = {
            'create_requerimento': '1',
            'cliente_cpf': client2.cpf,
            'pedido': 'prioridade doença',
            'valor': '15000.00',
            'desagio': '8.0',
            'fase': self.test_data['fase_requerimento'].id
        }
        
        self.client_app.post(
            reverse('precatorio_detalhe', args=[precatorio.cnj]),
            data=requerimento_data
        )
        
        # Step 6: Verify complex relationship integrity
        alvara = Alvara.objects.get(precatorio=precatorio, cliente=client1)
        requerimento = Requerimento.objects.get(precatorio=precatorio, cliente=client2)
        
        self.assertEqual(alvara.cliente, client1)
        self.assertEqual(requerimento.cliente, client2)
        self.assertEqual(alvara.precatorio, precatorio)
        self.assertEqual(requerimento.precatorio, precatorio)
        
        # P007 specific integrity checks (multiple clients scenario)
        # Verify basic relationships
        self.assertEqual(alvara.precatorio, precatorio)
        self.assertEqual(requerimento.precatorio, precatorio)
        self.assertEqual(alvara.cliente, client1)
        self.assertEqual(requerimento.cliente, client2)
        
        # Verify both clients are linked to the precatorio
        self.assertIn(client1, precatorio.clientes.all())
        self.assertIn(client2, precatorio.clientes.all())
        self.assertEqual(precatorio.clientes.count(), 2)
        
        # Verify both clients appear in precatorio detail
        response = self.client_app.get(reverse('precatorio_detalhe', args=[precatorio.cnj]))
        self.assertContains(response, client1.nome)
        self.assertContains(response, client2.nome)

    def test_flow_integration_complete_business_scenario(self):
        """
        COMPREHENSIVE FLOW: Complete business scenario integration
        
        This test simulates a complete real-world scenario:
        1. Create precatorio
        2. Link multiple clients
        3. Create multiple alvarás and requerimentos
        4. Update phases
        5. Create diligencias
        6. Verify complete system integration
        """
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create comprehensive scenario
        precatorio = self.test_data['precatorio']
        client1 = self.test_data['cliente_priority']
        client2 = self.test_data['cliente_regular']
        
        # Link both clients
        precatorio.clientes.add(client1, client2)
        
        # Create multiple documents
        alvara1 = Alvara.objects.create(
            precatorio=precatorio,
            cliente=client1,
            valor_principal=40000.00,
            honorarios_contratuais=12000.00,
            honorarios_sucumbenciais=6000.00,
            tipo='prioridade',
            fase=self.test_data['fase_alvara'],
            fase_honorarios_contratuais=self.test_data['fase_honorarios_1']
        )
        
        alvara2 = Alvara.objects.create(
            precatorio=precatorio,
            cliente=client2,
            valor_principal=25000.00,
            honorarios_contratuais=7500.00,
            honorarios_sucumbenciais=3750.00,
            tipo='ordem cronológica',
            fase=self.test_data['fase_alvara']
        )
        
        requerimento1 = Requerimento.objects.create(
            precatorio=precatorio,
            cliente=client1,
            valor=20000.00,
            desagio=12.0,
            pedido='acordo principal',
            fase=self.test_data['fase_requerimento']
        )
        
        # Create diligencia
        diligencia = Diligencias.objects.create(
            cliente=client1,
            tipo=self.test_data['tipo_urgente'],
            data_final=date.today() + timedelta(days=7),
            urgencia='alta',
            criado_por=self.user.username,
            descricao='Verificar documentação do precatório'
        )
        
        # Verify complete integration by accessing precatorio detail page
        response = self.client_app.get(reverse('precatorio_detalhe', args=[precatorio.cnj]))
        self.assertEqual(response.status_code, 200)
        
        # Verify all elements appear correctly
        self.assertContains(response, precatorio.cnj)
        self.assertContains(response, client1.nome)
        self.assertContains(response, client2.nome)
        
        # Verify that documents were created successfully (check database instead of display)
        self.assertEqual(Alvara.objects.filter(precatorio=precatorio).count(), 2)
        self.assertEqual(Requerimento.objects.filter(precatorio=precatorio).count(), 1)
        self.assertEqual(Diligencias.objects.filter(cliente=client1).count(), 1)
        
        # Verify client detail integration
        response = self.client_app.get(reverse('cliente_detail', args=[client1.cpf]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, precatorio.cnj)
        self.assertContains(response, diligencia.descricao)
        
        # Verify complete database integrity
        workflow_context = {
            'precatorio': precatorio,
            'cliente': client1,
            'alvara': alvara1,
            'requerimento': requerimento1
        }
        self.assert_complete_flow_integrity(workflow_context)
        
        # Verify relationships are bidirectional
        self.assertIn(client1, precatorio.clientes.all())
        self.assertIn(client2, precatorio.clientes.all())
        self.assertIn(precatorio, client1.precatorios.all())
        self.assertIn(precatorio, client2.precatorios.all())
        
        # Verify document counts
        self.assertEqual(precatorio.alvara_set.count(), 2)
        self.assertEqual(precatorio.requerimento_set.count(), 1)
        self.assertEqual(client1.diligencias.count(), 1)
