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
            
            # Check that new Tipo was created (command creates several default tipos + our test tipo + the new one)
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
