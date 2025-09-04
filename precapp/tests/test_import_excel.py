"""
Test cases for import_excel management command.
Tests the functionality of importing Excel files with the 2026 format.
"""

import os
import tempfile
from io import StringIO
from unittest.mock import patch, MagicMock

import pandas as pd
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from precapp.models import Tipo, Cliente, Precatorio


class ImportExcelCommandTest(TestCase):
    """Test cases for the import_excel management command."""

    def setUp(self):
        """Set up test data."""
        # Create a test Tipo
        self.test_tipo = Tipo.objects.create(
            nome='Test Tipo',
            descricao='Test description',
            cor='#007bff',
            ordem=1,
            ativa=True
        )

    def create_test_dataframe(self, data=None):
        """Create a test DataFrame with 2026 format."""
        if data is None:
            data = {
                'origem': ['Test Origin'],
                'tipo': ['Test Tipo'],
                'cnj': ['1234567-89.2026.8.26.0001'],
                'orcamento': [2026],
                'destacado': [0.1],
                'nome': ['João Silva'],  # Changed from 'autor' to 'nome'
                'cpf': ['12345678909'],
                'nascimento': ['01/01/1990'],
                'valor_face': [10000.0]
            }
        return pd.DataFrame(data)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_import_basic_functionality(self, mock_exists, mock_excel_file):
        """Test basic import functionality."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock ExcelFile
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        # Mock pd.read_excel to return our test data
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.create_test_dataframe()
            
            # Capture output
            out = StringIO()
            
            # Run the command
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Check that objects were created
            self.assertEqual(Cliente.objects.count(), 1)
            self.assertEqual(Precatorio.objects.count(), 1)
            
            # Check client data
            cliente = Cliente.objects.first()
            self.assertEqual(cliente.nome, 'João Silva')
            self.assertEqual(cliente.cpf, '12345678909')
            
            # Check precatorio data
            precatorio = Precatorio.objects.first()
            self.assertEqual(precatorio.cnj, '1234567-89.2026.8.26.0001')
            self.assertEqual(precatorio.orcamento, 2026)
            self.assertEqual(precatorio.tipo, self.test_tipo)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_import_with_null_nascimento(self, mock_exists, mock_excel_file):
        """Test import with null nascimento field."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'],
            'tipo': ['Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0002'],
            'orcamento': [2026],
            'destacado': [0.1],
            'nome': ['Maria Santos'],  # Changed from 'autor' to 'nome'
            'cpf': ['98765432100'],
            'nascimento': [None],  # Null birth date
            'valor_face': [15000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.create_test_dataframe(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Check that objects were created
            self.assertEqual(Cliente.objects.count(), 1)
            cliente = Cliente.objects.first()
            self.assertEqual(cliente.nome, 'Maria Santos')
            self.assertIsNone(cliente.nascimento)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_import_with_blank_orcamento(self, mock_exists, mock_excel_file):
        """Test import with blank orcamento field."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'],
            'tipo': ['Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0003'],
            'orcamento': [None],  # Blank budget
            'destacado': [0.1],
            'nome': ['Pedro Costa'],  # Changed from 'autor' to 'nome'
            'cpf': ['11111111111'],
            'nascimento': ['15/05/1985'],
            'valor_face': [20000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.create_test_dataframe(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Check that objects were created
            self.assertEqual(Precatorio.objects.count(), 1)
            precatorio = Precatorio.objects.first()
            self.assertIsNone(precatorio.orcamento)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_import_creates_new_tipo(self, mock_exists, mock_excel_file):
        """Test that import creates new Tipo if not found."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'],
            'tipo': ['New Tipo'],  # This tipo doesn't exist
            'cnj': ['1234567-89.2026.8.26.0004'],
            'orcamento': [2026],
            'destacado': [0.2],
            'nome': ['Ana Lima'],  # Changed from 'autor' to 'nome'
            'cpf': ['22222222222'],
            'nascimento': ['20/12/1995'],
            'valor_face': [25000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.create_test_dataframe(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Check that new Tipo was created (import command creates tipos as needed)
            self.assertTrue(Tipo.objects.filter(nome='New Tipo').exists())
            new_tipo = Tipo.objects.get(nome='New Tipo')
            self.assertTrue(new_tipo.ativa)
            
            # Check that precatorio uses the new tipo
            precatorio = Precatorio.objects.first()
            self.assertIsNotNone(precatorio)
            self.assertEqual(precatorio.tipo, new_tipo)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_dry_run_functionality(self, mock_exists, mock_excel_file):
        """Test dry run functionality."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.create_test_dataframe()
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', '--dry-run', stdout=out, verbosity=2)
            
            # Check that no objects were created
            self.assertEqual(Cliente.objects.count(), 0)
            self.assertEqual(Precatorio.objects.count(), 0)
            
            # Check that output mentions dry run
            output = out.getvalue()
            self.assertIn('DRY RUN', output)

    def test_missing_file_error(self):
        """Test error handling for missing file."""
        with self.assertRaises(CommandError):
            call_command('import_excel', '--file', 'nonexistent_file.xlsx')

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_empty_dataframe_handling(self, mock_exists, mock_excel_file):
        """Test handling of empty Excel file."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            # Mock an empty DataFrame with proper columns
            empty_df = pd.DataFrame(columns=['origem', 'tipo', 'cnj', 'orcamento', 'destacado', 'nome', 'cpf', 'nascimento', 'valor_face'])
            mock_read_excel.return_value = empty_df
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Should handle gracefully without creating objects
            self.assertEqual(Cliente.objects.count(), 0)
            self.assertEqual(Precatorio.objects.count(), 0)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_cpf_cleaning_and_validation(self, mock_exists, mock_excel_file):
        """Test CPF cleaning removes dots, dashes and validates correctly."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'],
            'tipo': ['Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0005'],
            'orcamento': [2026],
            'destacado': [0.1],
            'nome': ['João Silva'],
            'cpf': ['111.444.777-35'],  # Valid CPF with dots and dashes
            'nascimento': ['01/01/1990'],
            'valor_face': [10000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.create_test_dataframe(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Check that client was created with cleaned CPF
            self.assertEqual(Cliente.objects.count(), 1)
            cliente = Cliente.objects.first()
            self.assertEqual(cliente.cpf, '11144477735')  # Should be cleaned
            self.assertEqual(cliente.nome, 'João Silva')

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_cnpj_in_cpf_field_handling(self, mock_exists, mock_excel_file):
        """Test handling of CNPJ value in CPF field - should work but log warning."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'],
            'tipo': ['Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0006'],
            'orcamento': [2026],
            'destacado': [0.1],
            'nome': ['Empresa ABC Ltda'],
            'cpf': ['05.883.557/0001-31'],  # CNPJ in CPF field
            'nascimento': [None],
            'valor_face': [50000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.create_test_dataframe(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Check that client was created with cleaned CNPJ
            self.assertEqual(Cliente.objects.count(), 1)
            cliente = Cliente.objects.first()
            self.assertEqual(cliente.cpf, '05883557000131')  # Should be cleaned CNPJ
            self.assertEqual(cliente.nome, 'Empresa ABC Ltda')
            
            # Verify both Cliente and Precatorio were created
            self.assertEqual(Precatorio.objects.count(), 1)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_invalid_cpf_length_acceptance(self, mock_exists, mock_excel_file):
        """Test that invalid CPF/CNPJ lengths are now rejected (validation implemented)."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin', 'Test Origin 2'],
            'tipo': ['Test Tipo', 'Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0007', '1234567-89.2026.8.26.0008'],
            'orcamento': [2026, 2026],
            'destacado': [0.1, 0.1],
            'nome': ['Invalid User 1', 'Invalid User 2'],
            'cpf': ['12345', '123456789012345'],  # Too short (5) and too long (15)
            'nascimento': [None, None],
            'valor_face': [10000.0, 15000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # With validation: Invalid CPF lengths are now rejected
            self.assertEqual(Cliente.objects.count(), 0)  # No clients created
            self.assertEqual(Precatorio.objects.count(), 2)  # But precatorios still created
            
            # Check that error messages are in output
            output = out.getvalue()
            self.assertIn('Invalid document', output)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_empty_cpf_handling(self, mock_exists, mock_excel_file):
        """Test handling of empty/null CPF values."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin', 'Test Origin 2'],
            'tipo': ['Test Tipo', 'Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0009', '1234567-89.2026.8.26.0010'],
            'orcamento': [2026, 2026],
            'destacado': [0.1, 0.1],
            'nome': ['User Without CPF', 'User With Empty CPF'],
            'cpf': [None, ''],  # Null and empty CPF
            'nascimento': [None, None],
            'valor_face': [10000.0, 15000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # No clients should be created due to missing CPF
            self.assertEqual(Cliente.objects.count(), 0)
            # But precatorios should still be created
            self.assertEqual(Precatorio.objects.count(), 2)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_mixed_cpf_cnpj_formats(self, mock_exists, mock_excel_file):
        """Test handling of mixed CPF and CNPJ formats in the same import."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'] * 4,
            'tipo': ['Test Tipo'] * 4,
            'cnj': [
                '1234567-89.2026.8.26.0011',
                '1234567-89.2026.8.26.0012', 
                '1234567-89.2026.8.26.0013',
                '1234567-89.2026.8.26.0014'
            ],
            'orcamento': [2026] * 4,
            'destacado': [0.1] * 4,
            'nome': [
                'João Silva',           # Valid CPF
                'Maria Santos',         # Valid CPF with formatting
                'Empresa ABC',          # Valid CNPJ with formatting
                'Empresa XYZ'           # Valid CNPJ
            ],
            'cpf': [
                '11144477735',              # Valid CPF (11 digits)
                '12345678909',              # Different valid CPF
                '11.222.333/0001-81',       # Valid formatted CNPJ (14 digits)
                '12345678000195'            # Different valid CNPJ
            ],
            'nascimento': ['01/01/1990', '15/05/1985', None, None],
            'valor_face': [10000.0, 15000.0, 50000.0, 75000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # All clients should be created
            self.assertEqual(Cliente.objects.count(), 4)
            self.assertEqual(Precatorio.objects.count(), 4)
            
            # Check individual clients
            joao = Cliente.objects.get(nome='João Silva')
            self.assertEqual(joao.cpf, '11144477735')
            
            maria = Cliente.objects.get(nome='Maria Santos')
            self.assertEqual(maria.cpf, '12345678909')
            
            empresa_abc = Cliente.objects.get(nome='Empresa ABC')
            self.assertEqual(empresa_abc.cpf, '11222333000181')
            
            empresa_xyz = Cliente.objects.get(nome='Empresa XYZ')
            self.assertEqual(empresa_xyz.cpf, '12345678000195')

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_cpf_whitespace_handling(self, mock_exists, mock_excel_file):
        """Test handling of CPF/CNPJ with extra whitespace."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'] * 3,
            'tipo': ['Test Tipo'] * 3,
            'cnj': [
                '1234567-89.2026.8.26.0015',
                '1234567-89.2026.8.26.0016',
                '1234567-89.2026.8.26.0017'
            ],
            'orcamento': [2026] * 3,
            'destacado': [0.1] * 3,
            'nome': ['User 1', 'User 2', 'User 3'],
            'cpf': [
                '  111.444.777-35  ',       # Valid CPF with leading/trailing spaces
                '\t123.456.789-09\n',       # Different valid CPF with tabs and newlines
                ' 11.222.333/0001-81 '      # Valid CNPJ with spaces
            ],
            'nascimento': [None] * 3,
            'valor_face': [10000.0] * 3
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # All clients should be created with cleaned CPF/CNPJ
            self.assertEqual(Cliente.objects.count(), 3)
            
            users = Cliente.objects.all().order_by('nome')
            self.assertEqual(users[0].cpf, '11144477735')    # User 1 - cleaned CPF
            self.assertEqual(users[1].cpf, '12345678909')    # User 2 - cleaned CPF  
            self.assertEqual(users[2].cpf, '11222333000181')  # User 3 - cleaned CNPJ

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_invalid_cnj_validation(self, mock_exists, mock_excel_file):
        """Test that invalid CNJ numbers are rejected during import."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'] * 3,
            'tipo': ['Test Tipo'] * 3,
            'cnj': [
                '123456-89.2026.8.26.0001',    # Invalid: only 6 digits instead of 7
                '1234567.89.2026.8.26.0002',   # Invalid: missing dash
                '1234567-89.1900.8.26.0003'    # Invalid: year too old (1900)
            ],
            'orcamento': [2026] * 3,
            'destacado': [0.1] * 3,
            'nome': ['João Silva', 'Maria Santos', 'Pedro Costa'],
            'cpf': ['11144477735', '11144477735', '11144477735'],  # Valid CPF
            'nascimento': ['01/01/1990'] * 3,
            'valor_face': [10000.0] * 3
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # No precatorios should be created due to invalid CNJ
            self.assertEqual(Precatorio.objects.count(), 0)
            # No clients should be created either since the rows failed processing
            self.assertEqual(Cliente.objects.count(), 0)
            
            # Check that error messages are in output
            output = out.getvalue()
            self.assertIn('Invalid CNJ', output)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_invalid_origem_cnj_validation(self, mock_exists, mock_excel_file):
        """Test that invalid CNJ numbers in origem field are rejected."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['123456-89.2026.8.26.0001'],  # Invalid CNJ in origem field (too short)
            'tipo': ['Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0001'],    # Valid CNJ
            'orcamento': [2026],
            'destacado': [0.1],
            'nome': ['João Silva'],
            'cpf': ['11144477735'],  # Valid CPF
            'nascimento': ['01/01/1990'],
            'valor_face': [10000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # No objects should be created due to invalid origem CNJ
            self.assertEqual(Precatorio.objects.count(), 0)
            self.assertEqual(Cliente.objects.count(), 0)
            
            # Check that error message mentions origem CNJ
            output = out.getvalue()
            self.assertIn('Invalid origem CNJ', output)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_invalid_cpf_validation(self, mock_exists, mock_excel_file):
        """Test that invalid CPF numbers are rejected during import."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'] * 4,
            'tipo': ['Test Tipo'] * 4,
            'cnj': [
                '1234567-89.2026.8.26.0001',
                '1234567-89.2026.8.26.0002',
                '1234567-89.2026.8.26.0003',
                '1234567-89.2026.8.26.0004'
            ],
            'orcamento': [2026] * 4,
            'destacado': [0.1] * 4,
            'nome': ['Invalid User 1', 'Invalid User 2', 'Invalid User 3', 'Invalid User 4'],
            'cpf': [
                '12345678901',      # Invalid CPF check digits
                '11111111111',      # Invalid CPF (all same digits)
                '12345',            # Too short (5 digits)
                '123456789012345'   # Too long (15 digits)
            ],
            'nascimento': ['01/01/1990'] * 4,
            'valor_face': [10000.0] * 4
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Precatorios should be created (they don't depend on CPF validation)
            self.assertEqual(Precatorio.objects.count(), 4)
            # But no clients should be created due to invalid CPF
            self.assertEqual(Cliente.objects.count(), 0)
            
            # Check that error messages are in output
            output = out.getvalue()
            self.assertIn('Invalid CPF', output)
            self.assertIn('Invalid document', output)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_invalid_cnpj_validation(self, mock_exists, mock_excel_file):
        """Test that invalid CNPJ numbers are rejected during import."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'] * 3,
            'tipo': ['Test Tipo'] * 3,
            'cnj': [
                '1234567-89.2026.8.26.0001',
                '1234567-89.2026.8.26.0002',
                '1234567-89.2026.8.26.0003'
            ],
            'orcamento': [2026] * 3,
            'destacado': [0.1] * 3,
            'nome': ['Empresa A', 'Empresa B', 'Empresa C'],
            'cpf': [
                '12345678000190',      # Invalid CNPJ check digits
                '11111111111111',      # Invalid CNPJ (all same digits)
                '123456789'            # Too short (only 9 digits - should trigger "Invalid document")
            ],
            'nascimento': [None] * 3,
            'valor_face': [50000.0] * 3
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Precatorios should be created (they don't depend on CNPJ validation)
            self.assertEqual(Precatorio.objects.count(), 3)
            # But no clients should be created due to invalid CNPJ
            self.assertEqual(Cliente.objects.count(), 0)
            
            # Check that error messages are in output
            output = out.getvalue()
            self.assertIn('Invalid CNPJ', output)
            self.assertIn('Invalid document', output)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_valid_cpf_cnpj_validation_passes(self, mock_exists, mock_excel_file):
        """Test that valid CPF and CNPJ numbers pass validation during import."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['Test Origin'] * 2,
            'tipo': ['Test Tipo'] * 2,
            'cnj': [
                '1234567-89.2026.8.26.0001',
                '1234567-89.2026.8.26.0002'
            ],
            'orcamento': [2026] * 2,
            'destacado': [0.1] * 2,
            'nome': ['João Silva', 'Empresa ABC Ltda'],
            'cpf': [
                '11144477735',         # Valid CPF
                '11222333000181'       # Valid CNPJ
            ],
            'nascimento': ['01/01/1990', None],
            'valor_face': [10000.0, 50000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Both precatorios and clients should be created
            self.assertEqual(Precatorio.objects.count(), 2)
            self.assertEqual(Cliente.objects.count(), 2)
            
            # Check that the clients were created with correct data
            joao = Cliente.objects.get(nome='João Silva')
            self.assertEqual(joao.cpf, '11144477735')
            
            empresa = Cliente.objects.get(nome='Empresa ABC Ltda')
            self.assertEqual(empresa.cpf, '11222333000181')
            
            # Check that no error messages are in output
            output = out.getvalue()
            self.assertNotIn('Invalid CPF', output)
            self.assertNotIn('Invalid CNPJ', output)
            self.assertNotIn('Invalid CNJ', output)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_valid_cnj_validation_passes(self, mock_exists, mock_excel_file):
        """Test that valid CNJ numbers pass validation during import."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['1234567-89.2022.8.26.0001'],  # Valid origem CNJ
            'tipo': ['Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0001'],     # Valid main CNJ
            'orcamento': [2026],
            'destacado': [0.1],
            'nome': ['João Silva'],
            'cpf': ['11144477735'],  # Valid CPF
            'nascimento': ['01/01/1990'],
            'valor_face': [10000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Both precatorio and client should be created
            self.assertEqual(Precatorio.objects.count(), 1)
            self.assertEqual(Cliente.objects.count(), 1)
            
            # Check precatorio data
            precatorio = Precatorio.objects.first()
            self.assertEqual(precatorio.cnj, '1234567-89.2026.8.26.0001')
            self.assertEqual(precatorio.origem, '1234567-89.2022.8.26.0001')
            
            # Check that no error messages are in output
            output = out.getvalue()
            self.assertNotIn('Invalid CNJ', output)
            self.assertNotIn('Invalid origem CNJ', output)

    @patch('precapp.management.commands.import_excel.pd.ExcelFile')
    @patch('precapp.management.commands.import_excel.os.path.exists')
    def test_short_origem_field_not_validated(self, mock_exists, mock_excel_file):
        """Test that short origem fields (non-CNJ) are not validated as CNJ."""
        mock_exists.return_value = True
        mock_file_instance = MagicMock()
        mock_file_instance.sheet_names = ['2026']
        mock_excel_file.return_value = mock_file_instance
        
        data = {
            'origem': ['TJSP'],  # Short origem, should not be validated as CNJ
            'tipo': ['Test Tipo'],
            'cnj': ['1234567-89.2026.8.26.0001'],
            'orcamento': [2026],
            'destacado': [0.1],
            'nome': ['João Silva'],
            'cpf': ['11144477735'],
            'nascimento': ['01/01/1990'],
            'valor_face': [10000.0]
        }
        
        with patch('precapp.management.commands.import_excel.pd.read_excel') as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(data)
            
            out = StringIO()
            call_command('import_excel', '--file', 'dummy_file.xlsx', stdout=out, verbosity=2)
            
            # Should be created successfully - short origem not validated as CNJ
            self.assertEqual(Precatorio.objects.count(), 1)
            self.assertEqual(Cliente.objects.count(), 1)
            
            # Check precatorio data
            precatorio = Precatorio.objects.first()
            self.assertEqual(precatorio.origem, 'TJSP')
            
            # Check that no error messages are in output
            output = out.getvalue()
            self.assertNotIn('Invalid', output)
