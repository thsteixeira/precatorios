"""
Test cases for setup_customization management command.
Tests the functionality of setting up system default data structures.
"""

from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.db import transaction
from unittest.mock import patch

from precapp.models import (
    Fase, FaseHonorariosContratuais, TipoDiligencia, 
    Tipo, PedidoRequerimento
)


class SetupCustomizationCommandTest(TestCase):
    """Test cases for the setup_customization management command."""

    def setUp(self):
        """Set up test environment."""
        # Ensure clean state for each test
        self.clear_all_data()

    def tearDown(self):
        """Clean up after each test."""
        self.clear_all_data()

    def clear_all_data(self):
        """Helper method to clear all relevant data."""
        Fase.objects.all().delete()
        FaseHonorariosContratuais.objects.all().delete()
        TipoDiligencia.objects.all().delete()
        Tipo.objects.all().delete()
        PedidoRequerimento.objects.all().delete()

    def test_setup_customization_basic_functionality(self):
        """Test basic setup functionality creates all default data."""
        # Verify initial empty state
        self.assertEqual(Fase.objects.count(), 0)
        self.assertEqual(FaseHonorariosContratuais.objects.count(), 0)
        self.assertEqual(TipoDiligencia.objects.count(), 0)
        self.assertEqual(Tipo.objects.count(), 0)
        self.assertEqual(PedidoRequerimento.objects.count(), 0)

        # Run the command
        out = StringIO()
        call_command('setup_customization', stdout=out, verbosity=2)

        # Verify all data was created
        self.assertEqual(Fase.objects.count(), 11)  # 4 requerimento + 7 alvara
        self.assertEqual(FaseHonorariosContratuais.objects.count(), 5)  # Updated from 4 to 5
        self.assertEqual(TipoDiligencia.objects.count(), 5)
        self.assertEqual(Tipo.objects.count(), 4)  # Updated from 3 to 4
        self.assertEqual(PedidoRequerimento.objects.count(), 4)

        # Check output contains success message
        output = out.getvalue()
        self.assertIn('Setting up system customization...', output)
        self.assertIn('System customization setup completed successfully!', output)

    def test_setup_customization_idempotent(self):
        """Test that running the command multiple times doesn't create duplicates."""
        # Run the command first time
        out1 = StringIO()
        call_command('setup_customization', stdout=out1, verbosity=2)

        # Verify initial counts
        initial_fase_count = Fase.objects.count()
        initial_honorarios_count = FaseHonorariosContratuais.objects.count()
        initial_diligencia_count = TipoDiligencia.objects.count()
        initial_tipo_count = Tipo.objects.count()
        initial_pedido_count = PedidoRequerimento.objects.count()

        # Run the command second time
        out2 = StringIO()
        call_command('setup_customization', stdout=out2, verbosity=2)

        # Verify counts haven't changed
        self.assertEqual(Fase.objects.count(), initial_fase_count)
        self.assertEqual(FaseHonorariosContratuais.objects.count(), initial_honorarios_count)
        self.assertEqual(TipoDiligencia.objects.count(), initial_diligencia_count)
        self.assertEqual(Tipo.objects.count(), initial_tipo_count)
        self.assertEqual(PedidoRequerimento.objects.count(), initial_pedido_count)

        # Check that second run mentions existing items
        output2 = out2.getvalue()
        self.assertIn('already exist', output2)

    def test_main_phases_creation(self):
        """Test creation of main workflow phases."""
        out = StringIO()
        call_command('setup_customization', stdout=out, verbosity=2)

        # Verify Requerimento phases
        requerimento_phases = Fase.objects.filter(tipo='requerimento').order_by('ordem')
        self.assertEqual(requerimento_phases.count(), 4)
        
        expected_req_names = [
            'Organizar Documentos',
            'Protocolado', 
            'Deferido',
            'Indeferido'
        ]
        actual_req_names = list(requerimento_phases.values_list('nome', flat=True))
        self.assertEqual(actual_req_names, expected_req_names)

        # Verify Alvará phases
        alvara_phases = Fase.objects.filter(tipo='alvara').order_by('ordem')
        self.assertEqual(alvara_phases.count(), 7)
        
        expected_alv_names = [
            'Aguardando Depósito Judicial',
            'Aguardando Atualização pela Contadoria',
            'Para manifestar de cálculos',
            'Cálculos impugnados',
            'Para informar conta',
            'Contas bancárias informadas',
            'Recebido Pelo Cliente'
        ]
        actual_alv_names = list(alvara_phases.values_list('nome', flat=True))
        self.assertEqual(actual_alv_names, expected_alv_names)

        # Verify Honorários phases
        honorarios_phases = FaseHonorariosContratuais.objects.all().order_by('ordem')
        self.assertEqual(honorarios_phases.count(), 5)
        
        expected_hon_names = [
            'Aguardando Depósito Judicial',
            'Aguardando Pagamento ao Cliente',
            'Cobrar Cliente',
            'Quitado parcialmente',
            'Quitado integralmente'
        ]
        actual_hon_names = list(honorarios_phases.values_list('nome', flat=True))
        self.assertEqual(actual_hon_names, expected_hon_names)

    def test_phases_attributes(self):
        """Test that phases are created with correct attributes."""
        call_command('setup_customization', verbosity=0)

        # Test a specific Requerimento phase
        organizar_docs = Fase.objects.get(nome='Organizar Documentos', tipo='requerimento')
        self.assertEqual(organizar_docs.descricao, 'Fase inicial para organização dos documentos necessários')
        self.assertEqual(organizar_docs.cor, '#17a2b8')
        self.assertTrue(organizar_docs.ativa)
        self.assertEqual(organizar_docs.ordem, 1)

        # Test a specific Alvará phase
        aguardando_deposito = Fase.objects.get(nome='Aguardando Depósito Judicial', tipo='alvara')
        self.assertEqual(aguardando_deposito.cor, '#d9ff00')
        self.assertTrue(aguardando_deposito.ativa)
        self.assertEqual(aguardando_deposito.ordem, 1)

        # Test a specific Honorários phase
        quitado_integral = FaseHonorariosContratuais.objects.get(nome='Quitado integralmente')
        self.assertEqual(quitado_integral.descricao, 'Honorários contratuais pagos integralmente')
        self.assertEqual(quitado_integral.cor, '#0004ff')
        self.assertTrue(quitado_integral.ativa)
        self.assertEqual(quitado_integral.ordem, 5)

    def test_diligencia_types_creation(self):
        """Test creation of diligence types."""
        call_command('setup_customization', verbosity=0)

        # Verify all diligence types were created
        diligencia_types = TipoDiligencia.objects.all().order_by('ordem')
        self.assertEqual(diligencia_types.count(), 5)

        expected_names = [
            'Propor repactuação',
            'Solicitar RG',
            'Solicitar contrato',
            'Cobrar honorários',
            'Executar honorários'
        ]
        actual_names = list(diligencia_types.values_list('nome', flat=True))
        self.assertEqual(actual_names, expected_names)

        # Test specific attributes
        propor_repactuacao = TipoDiligencia.objects.get(nome='Propor repactuação')
        self.assertEqual(propor_repactuacao.descricao, 'Propor nova negociação dos termos do acordo')
        self.assertEqual(propor_repactuacao.cor, '#007bff')
        self.assertEqual(propor_repactuacao.ordem, 1)

        executar_honorarios = TipoDiligencia.objects.get(nome='Executar honorários')
        self.assertEqual(executar_honorarios.cor, '#dc3545')
        self.assertEqual(executar_honorarios.ordem, 5)

    def test_precatorio_types_creation(self):
        """Test creation of precatory types."""
        call_command('setup_customization', verbosity=0)

        # Verify all precatory types were created
        tipos = Tipo.objects.all().order_by('ordem')
        self.assertEqual(tipos.count(), 4)  # Updated from 3 to 4

        expected_names = [
            'Descompressão',
            'URV',
            'Reclassificação',
            'Revisão de proventos'  # Added new type
        ]
        actual_names = list(tipos.values_list('nome', flat=True))
        self.assertEqual(actual_names, expected_names)

        # Test specific attributes
        descompressao = Tipo.objects.get(nome='Descompressão')
        self.assertEqual(descompressao.descricao, 'Precatórios oriundos de processos de descompressão salarial')
        self.assertEqual(descompressao.cor, '#007bff')
        self.assertTrue(descompressao.ativa)
        self.assertEqual(descompressao.ordem, 1)

        urv = Tipo.objects.get(nome='URV')
        self.assertEqual(urv.cor, '#28a745')
        self.assertTrue(urv.ativa)

    def test_request_types_creation(self):
        """Test creation of request types."""
        call_command('setup_customization', verbosity=0)

        # Verify all request types were created
        pedidos = PedidoRequerimento.objects.all().order_by('ordem')
        self.assertEqual(pedidos.count(), 4)

        expected_names = [
            'Expedição de Alvará',
            'Pedido de Atualização de Valores',
            'Execução dos Honorários Contratuais',
            'Cessão de Crédito'
        ]
        actual_names = list(pedidos.values_list('nome', flat=True))
        self.assertEqual(actual_names, expected_names)

        # Test specific attributes
        expedicao = PedidoRequerimento.objects.get(nome='Expedição de Alvará')
        self.assertEqual(expedicao.descricao, 'Pedido para expedição de alvará judicial de levantamento')
        self.assertEqual(expedicao.cor, '#007bff')
        self.assertTrue(expedicao.ativo)
        self.assertEqual(expedicao.ordem, 1)

        cessao = PedidoRequerimento.objects.get(nome='Cessão de Crédito')
        self.assertEqual(cessao.cor, '#6f42c1')
        self.assertEqual(cessao.ordem, 4)
        self.assertTrue(cessao.ativo)

    def test_partial_existing_data(self):
        """Test behavior when some data already exists."""
        # Create some existing data manually
        Tipo.objects.create(
            nome='Descompressão',
            descricao='Existing description',
            cor='#existing',
            ordem=999,
            ativa=False
        )
        
        TipoDiligencia.objects.create(
            nome='Solicitar RG',
            descricao='Existing diligencia',
            cor='#existing',
            ordem=999
        )

        # Run the command
        out = StringIO()
        call_command('setup_customization', stdout=out, verbosity=2)

        # Verify existing items weren't duplicated or modified
        descompressao = Tipo.objects.get(nome='Descompressão')
        self.assertEqual(descompressao.descricao, 'Existing description')  # Should keep existing
        self.assertEqual(descompressao.cor, '#existing')
        self.assertEqual(descompressao.ordem, 999)
        self.assertFalse(descompressao.ativa)

        solicitar_rg = TipoDiligencia.objects.get(nome='Solicitar RG')
        self.assertEqual(solicitar_rg.descricao, 'Existing diligencia')
        self.assertEqual(solicitar_rg.ordem, 999)

        # Verify new items were still created
        self.assertTrue(Tipo.objects.filter(nome='URV').exists())
        self.assertTrue(Tipo.objects.filter(nome='Reclassificação').exists())
        self.assertTrue(TipoDiligencia.objects.filter(nome='Propor repactuação').exists())

    def test_command_output_messages(self):
        """Test that command produces appropriate output messages."""
        out = StringIO()
        call_command('setup_customization', stdout=out, verbosity=2)
        
        output = out.getvalue()
        
        # Check for main section headers
        self.assertIn('=== CREATING MAIN PHASES ===', output)
        self.assertIn('=== CREATING TIPOS DE DILIGÊNCIA ===', output)
        self.assertIn('=== CREATING TIPOS DE PRECATÓRIO ===', output)
        self.assertIn('=== CREATING TIPOS DE PEDIDO REQUERIMENTO ===', output)

        # Check for creation confirmations
        self.assertIn('✓ Created Requerimento fase:', output)
        self.assertIn('✓ Created Alvará fase:', output)
        self.assertIn('✓ Created Honorários fase:', output)
        self.assertIn('✓ Created TipoDiligencia:', output)
        self.assertIn('✓ Created Tipo:', output)
        self.assertIn('✓ Created PedidoRequerimento:', output)

        # Check for summary sections
        self.assertIn('=== PHASES CREATION SUMMARY ===', output)

    def test_command_output_when_data_exists(self):
        """Test command output when data already exists."""
        # Run command first time
        call_command('setup_customization', verbosity=0)
        
        # Run command second time and capture output
        out = StringIO()
        call_command('setup_customization', stdout=out, verbosity=2)
        
        output = out.getvalue()
        
        # Should indicate that items already exist
        self.assertIn('All main phases already exist', output)
        self.assertIn('All diligencia types already exist', output)
        self.assertIn('All tipos de precatorio already exist', output)
        self.assertIn('All tipos de pedido requerimento already exist', output)

    @patch('precapp.management.commands.setup_customization.Fase.objects.get_or_create')
    def test_database_error_handling(self, mock_get_or_create):
        """Test error handling when database operations fail."""
        # Mock a database error
        mock_get_or_create.side_effect = Exception("Database error")
        
        # Command should raise the exception
        with self.assertRaises(Exception) as context:
            call_command('setup_customization', verbosity=0)
        
        self.assertIn("Database error", str(context.exception))

    def test_transaction_rollback_on_error(self):
        """Test that database transaction is rolled back on error."""
        # Create some initial data
        initial_count = Fase.objects.count()
        
        # Mock an error that occurs after some data is created
        with patch('precapp.management.commands.setup_customization.TipoDiligencia.objects.get_or_create') as mock_create:
            mock_create.side_effect = Exception("Simulated error")
            
            with self.assertRaises(Exception):
                call_command('setup_customization', verbosity=0)
            
            # Verify no partial data was committed
            self.assertEqual(Fase.objects.count(), initial_count)

    def test_color_codes_validity(self):
        """Test that all created items have valid color codes."""
        call_command('setup_customization', verbosity=0)
        
        # Test Fase colors
        for fase in Fase.objects.all():
            self.assertTrue(fase.cor.startswith('#'), f"Fase {fase.nome} has invalid color: {fase.cor}")
            self.assertEqual(len(fase.cor), 7, f"Fase {fase.nome} color should be 7 chars: {fase.cor}")
        
        # Test FaseHonorariosContratuais colors
        for fase in FaseHonorariosContratuais.objects.all():
            self.assertTrue(fase.cor.startswith('#'))
            self.assertEqual(len(fase.cor), 7)
        
        # Test TipoDiligencia colors
        for tipo in TipoDiligencia.objects.all():
            self.assertTrue(tipo.cor.startswith('#'))
            self.assertEqual(len(tipo.cor), 7)
        
        # Test Tipo colors
        for tipo in Tipo.objects.all():
            self.assertTrue(tipo.cor.startswith('#'))
            self.assertEqual(len(tipo.cor), 7)
        
        # Test PedidoRequerimento colors
        for pedido in PedidoRequerimento.objects.all():
            self.assertTrue(pedido.cor.startswith('#'))
            self.assertEqual(len(pedido.cor), 7)

    def test_ordem_values_consistency(self):
        """Test that ordem (order) values are sequential and consistent."""
        call_command('setup_customization', verbosity=0)
        
        # Test Requerimento phases ordem
        req_phases = Fase.objects.filter(tipo='requerimento').order_by('ordem')
        req_ordens = list(req_phases.values_list('ordem', flat=True))
        self.assertEqual(req_ordens, [1, 2, 3, 4])
        
        # Test Alvará phases ordem
        alv_phases = Fase.objects.filter(tipo='alvara').order_by('ordem')
        alv_ordens = list(alv_phases.values_list('ordem', flat=True))
        self.assertEqual(alv_ordens, [1, 2, 3, 4, 5, 6, 7])
        
        # Test Honorários phases ordem
        hon_phases = FaseHonorariosContratuais.objects.all().order_by('ordem')
        hon_ordens = list(hon_phases.values_list('ordem', flat=True))
        self.assertEqual(hon_ordens, [1, 2, 3, 4, 5])
        
        # Test TipoDiligencia ordem
        diligencia_types = TipoDiligencia.objects.all().order_by('ordem')
        dil_ordens = list(diligencia_types.values_list('ordem', flat=True))
        self.assertEqual(dil_ordens, [1, 2, 3, 4, 5])
        
        # Test Tipo ordem
        tipos = Tipo.objects.all().order_by('ordem')
        tipo_ordens = list(tipos.values_list('ordem', flat=True))
        self.assertEqual(tipo_ordens, [1, 2, 3, 4])  # Updated from [1, 2, 3] to [1, 2, 3, 4]
        
        # Test PedidoRequerimento ordem
        pedidos = PedidoRequerimento.objects.all().order_by('ordem')
        pedido_ordens = list(pedidos.values_list('ordem', flat=True))
        self.assertEqual(pedido_ordens, [1, 2, 3, 4])

    def test_all_items_active_by_default(self):
        """Test that all created items are active by default where applicable."""
        call_command('setup_customization', verbosity=0)
        
        # Test Fase items
        for fase in Fase.objects.all():
            self.assertTrue(fase.ativa, f"Fase {fase.nome} should be active")
        
        # Test FaseHonorariosContratuais items
        for fase in FaseHonorariosContratuais.objects.all():
            self.assertTrue(fase.ativa, f"FaseHonorariosContratuais {fase.nome} should be active")
        
        # Test Tipo items
        for tipo in Tipo.objects.all():
            self.assertTrue(tipo.ativa, f"Tipo {tipo.nome} should be active")
        
        # Test PedidoRequerimento items
        for pedido in PedidoRequerimento.objects.all():
            self.assertTrue(pedido.ativo, f"PedidoRequerimento {pedido.nome} should be active")

    def test_unique_names_within_categories(self):
        """Test that names are unique within each category."""
        call_command('setup_customization', verbosity=0)
        
        # Test Fase names uniqueness within tipo
        req_names = list(Fase.objects.filter(tipo='requerimento').values_list('nome', flat=True))
        self.assertEqual(len(req_names), len(set(req_names)), "Requerimento fase names should be unique")
        
        alv_names = list(Fase.objects.filter(tipo='alvara').values_list('nome', flat=True))
        self.assertEqual(len(alv_names), len(set(alv_names)), "Alvará fase names should be unique")
        
        # Test other model names uniqueness
        hon_names = list(FaseHonorariosContratuais.objects.values_list('nome', flat=True))
        self.assertEqual(len(hon_names), len(set(hon_names)), "Honorários fase names should be unique")
        
        dil_names = list(TipoDiligencia.objects.values_list('nome', flat=True))
        self.assertEqual(len(dil_names), len(set(dil_names)), "TipoDiligencia names should be unique")
        
        tipo_names = list(Tipo.objects.values_list('nome', flat=True))
        self.assertEqual(len(tipo_names), len(set(tipo_names)), "Tipo names should be unique")
        
        pedido_names = list(PedidoRequerimento.objects.values_list('nome', flat=True))
        self.assertEqual(len(pedido_names), len(set(pedido_names)), "PedidoRequerimento names should be unique")
