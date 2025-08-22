"""
Test cases for all forms in the precatorios application.
Contains all form-related tests migrated from the monolithic tests.py file.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date, timedelta

from precapp.models import (
    Fase, FaseHonorariosContratuais, Precatorio, Cliente, 
    Alvara, Requerimento, TipoDiligencia, Diligencias
)
from precapp.forms import (
    FaseForm, AlvaraSimpleForm, 
    RequerimentoForm, PrecatorioForm, ClienteForm, 
    TipoDiligenciaForm, DiligenciasForm, DiligenciasUpdateForm,
    validate_cnj, validate_currency
)


class FaseFormTest(TestCase):
    """Test cases for FaseForm"""
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'nome': 'Nova Fase',
            'descricao': 'Descrição da nova fase',
            'tipo': 'alvara',
            'cor': '#FF6B35',
            'ordem': 0,
            'ativa': True
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = FaseForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = FaseForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        fase = form.save()
        self.assertEqual(fase.nome, 'Nova Fase')
        self.assertEqual(fase.tipo, 'alvara')
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        incomplete_data = {'nome': 'Test'}
        form = FaseForm(data=incomplete_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)


class AlvaraFormTest(TestCase):
    """Test cases for AlvaraSimpleForm"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        # Link the cliente to the precatorio (required by new validation)
        self.precatorio.clientes.add(self.cliente)
        
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        self.fase_ambos = Fase.objects.create(
            nome='Cancelado',
            tipo='ambos',
            cor='#95A5A6',
            ativa=True
        )
        # Create a requerimento fase that should not appear in alvara forms
        self.fase_requerimento = Fase.objects.create(
            nome='Protocolado',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True
        )
        
        # Create fases honorários contratuais
        self.fase_honorarios_ativa = FaseHonorariosContratuais.objects.create(
            nome='Em Negociação',
            cor='#007BFF',
            ativa=True
        )
        self.fase_honorarios_inativa = FaseHonorariosContratuais.objects.create(
            nome='Inativa',
            cor='#6C757D',
            ativa=False
        )
    
    def test_alvara_simple_form_fase_filtering(self):
        """Test that AlvaraSimpleForm only shows alvara and ambos phases"""
        form = AlvaraSimpleForm(precatorio=self.precatorio)
        fase_queryset = form.fields['fase'].queryset
        
        # Should include alvara and ambos phases
        self.assertIn(self.fase_alvara, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include requerimento phases
        self.assertNotIn(self.fase_requerimento, fase_queryset)
    
    def test_alvara_simple_form_includes_honorarios_field(self):
        """Test that AlvaraSimpleForm includes fase_honorarios_contratuais field"""
        form = AlvaraSimpleForm(precatorio=self.precatorio)
        self.assertIn('fase_honorarios_contratuais', form.fields)
        
        # Test field properties
        honorarios_field = form.fields['fase_honorarios_contratuais']
        self.assertFalse(honorarios_field.required)  # Should be optional
    
    def test_alvara_simple_form_honorarios_filtering(self):
        """Test that AlvaraSimpleForm only shows active honorários phases"""
        form = AlvaraSimpleForm(precatorio=self.precatorio)
        honorarios_queryset = form.fields['fase_honorarios_contratuais'].queryset
        
        # Should include only active phases
        self.assertIn(self.fase_honorarios_ativa, honorarios_queryset)
        # Should NOT include inactive phases
        self.assertNotIn(self.fase_honorarios_inativa, honorarios_queryset)


class RequerimentoFormTest(TestCase):
    """Test cases for RequerimentoForm"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.cliente_cnpj = Cliente.objects.create(
            cpf='12345678000195',
            nome='Empresa Ltda',
            nascimento=date(2000, 1, 1),
            prioridade=False
        )
        
        # Link the clientes to the precatorio (required by new validation)
        self.precatorio.clientes.add(self.cliente)
        self.precatorio.clientes.add(self.cliente_cnpj)
        
        self.fase_requerimento = Fase.objects.create(
            nome='Em Andamento',
            tipo='requerimento',
            cor='#4ECDC4',
            ativa=True
        )
        self.fase_ambos = Fase.objects.create(
            nome='Cancelado',
            tipo='ambos',
            cor='#95A5A6',
            ativa=True
        )
        # Create an alvara fase that should not appear in requerimento forms
        self.fase_alvara = Fase.objects.create(
            nome='Aguardando Depósito',
            tipo='alvara',
            cor='#FF6B35',
            ativa=True
        )
        
        self.valid_form_data_cpf = {
            'cliente_cpf': '123.456.789-09',
            'pedido': 'prioridade doença',
            'valor': '25000.00',
            'desagio': '15.5',
            'fase': self.fase_requerimento.id
        }
        self.valid_form_data_cnpj = {
            'cliente_cpf': '12.345.678/0001-95',
            'pedido': 'prioridade idade',
            'valor': '40000.00',
            'desagio': '10.0',
            'fase': self.fase_requerimento.id
        }
    
    def test_requerimento_form_fase_filtering(self):
        """Test that RequerimentoForm only shows requerimento and ambos phases"""
        form = RequerimentoForm(precatorio=self.precatorio)
        fase_queryset = form.fields['fase'].queryset
        
        # Should include requerimento and ambos phases
        self.assertIn(self.fase_requerimento, fase_queryset)
        self.assertIn(self.fase_ambos, fase_queryset)
        # Should NOT include alvara phases
        self.assertNotIn(self.fase_alvara, fase_queryset)
    
    def test_valid_requerimento_form_cpf(self):
        form = RequerimentoForm(data=self.valid_form_data_cpf, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())

    def test_valid_requerimento_form_cnpj(self):
        form = RequerimentoForm(data=self.valid_form_data_cnpj, precatorio=self.precatorio)
        self.assertTrue(form.is_valid())

    def test_invalid_requerimento_form_document(self):
        # Invalid CPF
        invalid_data = self.valid_form_data_cpf.copy()
        invalid_data['cliente_cpf'] = '11111111111'
        form = RequerimentoForm(data=invalid_data, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)
        # Invalid CNPJ
        invalid_data_cnpj = self.valid_form_data_cnpj.copy()
        invalid_data_cnpj['cliente_cpf'] = '12345678000100'
        form = RequerimentoForm(data=invalid_data_cnpj, precatorio=self.precatorio)
        self.assertFalse(form.is_valid())
        self.assertIn('cliente_cpf', form.errors)


class PrecatorioFormTest(TestCase):
    """Test cases for PrecatorioForm"""
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'cnj': '1234567-89.2023.8.26.0100',
            'orcamento': '2023',
            'origem': '1234567-89.2022.8.26.0001',
            'valor_de_face': '100000.00',
            'ultima_atualizacao': '100000.00',
            'data_ultima_atualizacao': '2023-01-01',
            'percentual_contratuais_assinado': '10.0',
            'percentual_contratuais_apartado': '5.0',
            'percentual_sucumbenciais': '20.0',
            'credito_principal': 'pendente',
            'honorarios_contratuais': 'pendente',
            'honorarios_sucumbenciais': 'pendente'
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = PrecatorioForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = PrecatorioForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        precatorio = form.save()
        self.assertEqual(precatorio.cnj, '1234567-89.2023.8.26.0100')


class ClienteFormTest(TestCase):
    """Test cases for ClienteForm"""
    
    def setUp(self):
        """Set up test data"""
        self.precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='1234567-89.2022.8.26.0001',
            valor_de_face=100000.00,
            ultima_atualizacao=100000.00,
            data_ultima_atualizacao=date(2023, 1, 1),
            percentual_contratuais_assinado=10.0,
            percentual_contratuais_apartado=5.0,
            percentual_sucumbenciais=20.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente'
        )
        
        self.valid_form_data = {
            'cpf': '111.444.777-35',  # Valid CPF with correct check digits
            'nome': 'João Silva',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        self.valid_form_data_cpf = {
            'cpf': '111.444.777-35',
            'nome': 'João Silva',
            'nascimento': '1980-05-15',
            'prioridade': False
        }
        self.valid_form_data_cnpj = {
            'cpf': '12.345.678/0001-95',
            'nome': 'Empresa Ltda',
            'nascimento': '2000-01-01',
            'prioridade': False
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = ClienteForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = ClienteForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.nome, 'João Silva')
    
    def test_cpf_input_formats(self):
        """Test that CPF accepts both formatted and unformatted input"""
        # Test formatted CPF (with dots and dash)
        formatted_data = self.valid_form_data.copy()
        formatted_data['cpf'] = '123.456.789-09'
        form = ClienteForm(data=formatted_data)
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.cpf, '12345678909')  # Should be stored without formatting
        
        # Test unformatted CPF (numbers only)
        Cliente.objects.all().delete()  # Clear the previous client
        unformatted_data = self.valid_form_data.copy()
        unformatted_data['cpf'] = '98765432100'
        unformatted_data['nome'] = 'Maria Santos'
        form = ClienteForm(data=unformatted_data)
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.cpf, '98765432100')  # Should be stored as-is
        
    def test_document_validation_errors(self):
        # Invalid CPF length
        invalid_data = self.valid_form_data_cpf.copy()
        invalid_data['cpf'] = '123456789'
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        # Invalid CPF check digits
        invalid_data['cpf'] = '23902928334'
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cpf'][0])
        # CPF all same digits
        invalid_data['cpf'] = '11111111111'
        form = ClienteForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CPF inválido', form.errors['cpf'][0])
        # Invalid CNPJ length
        invalid_cnpj = self.valid_form_data_cnpj.copy()
        invalid_cnpj['cpf'] = '12345678'
        form = ClienteForm(data=invalid_cnpj)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        # Invalid CNPJ check digits
        invalid_cnpj['cpf'] = '12345678000100'
        form = ClienteForm(data=invalid_cnpj)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)
        self.assertIn('CNPJ inválido', form.errors['cpf'][0])


class TipoDiligenciaFormTest(TestCase):
    """Test cases for TipoDiligenciaForm"""
    
    def setUp(self):
        """Set up test form data"""
        self.valid_form_data = {
            'nome': 'Contato Cliente',
            'descricao': 'Entrar em contato com o cliente',
            'cor': '#28a745',
            'ordem': 0,
            'ativo': True
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = TipoDiligenciaForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form saving creates the object correctly"""
        form = TipoDiligenciaForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        tipo = form.save()
        self.assertEqual(tipo.nome, 'Contato Cliente')
        self.assertEqual(tipo.cor, '#28a745')
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        incomplete_data = {'descricao': 'Test'}
        form = TipoDiligenciaForm(data=incomplete_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_form_color_field(self):
        """Test color field widget and validation"""
        form = TipoDiligenciaForm()
        color_field = form.fields['cor']
        self.assertEqual(color_field.widget.input_type, 'color')
    
    def test_form_clean_cor_valid(self):
        """Test form accepts valid hex colors"""
        valid_colors = ['#FF0000', '#00ff00', '#0000FF', '#AbCdEf']
        for color in valid_colors:
            with self.subTest(color=color):
                data = self.valid_form_data.copy()
                data['cor'] = color
                form = TipoDiligenciaForm(data=data)
                self.assertTrue(form.is_valid(), f"Form should be valid for color {color}")
    
    def test_form_clean_cor_invalid(self):
        """Test form rejects invalid hex colors"""
        invalid_colors = ['invalid', '#FF', '#GGGGGG', 'red', '123456', '#1234567']
        for color in invalid_colors:
            with self.subTest(color=color):
                data = self.valid_form_data.copy()
                data['cor'] = color
                form = TipoDiligenciaForm(data=data)
                self.assertFalse(form.is_valid(), f"Form should be invalid for color {color}")
                self.assertIn('cor', form.errors)
    
    def test_form_optional_description(self):
        """Test that description field is optional"""
        data = self.valid_form_data.copy()
        data.pop('descricao')
        form = TipoDiligenciaForm(data=data)
        self.assertTrue(form.is_valid())
        tipo = form.save()
        self.assertEqual(tipo.descricao, '')


class DiligenciasFormTest(TestCase):
    """Test cases for DiligenciasForm"""
    
    def setUp(self):
        """Set up test data"""
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.tipo_ativo = TipoDiligencia.objects.create(
            nome='Ativo',
            cor='#007bff',
            ativo=True
        )
        
        self.tipo_inativo = TipoDiligencia.objects.create(
            nome='Inativo',
            cor='#6c757d',
            ativo=False
        )
        
        self.valid_form_data = {
            'tipo': self.tipo_ativo.id,
            'data_final': (date.today() + timedelta(days=7)).strftime('%d/%m/%Y'),
            'urgencia': 'media',
            'descricao': 'Teste de diligência'
        }
    
    def test_valid_form(self):
        """Test form with all valid data"""
        form = DiligenciasForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_form_save(self):
        """Test form saving (requires cliente to be set separately)"""
        form = DiligenciasForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        diligencia = form.save(commit=False)
        diligencia.cliente = self.cliente
        diligencia.criado_por = 'Test User'
        diligencia.save()
        
        self.assertEqual(diligencia.tipo, self.tipo_ativo)
        self.assertEqual(diligencia.cliente, self.cliente)
        self.assertEqual(diligencia.urgencia, 'media')
    
    def test_form_required_fields(self):
        """Test form with missing required fields"""
        incomplete_data = {'descricao': 'Test'}
        form = DiligenciasForm(data=incomplete_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tipo', form.errors)
        self.assertIn('data_final', form.errors)
    
    def test_form_tipo_filtering(self):
        """Test that form only shows active tipos"""
        form = DiligenciasForm()
        tipo_queryset = form.fields['tipo'].queryset
        
        self.assertIn(self.tipo_ativo, tipo_queryset)
        self.assertNotIn(self.tipo_inativo, tipo_queryset)
    
    def test_form_clean_data_final_future(self):
        """Test that data_final must be in the future"""
        past_data = self.valid_form_data.copy()
        past_date = (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
        past_data['data_final'] = past_date
        form = DiligenciasForm(data=past_data)
        self.assertFalse(form.is_valid())
        self.assertIn('data_final', form.errors)
        self.assertIn('passado', form.errors['data_final'][0])
    
    def test_form_clean_data_final_today(self):
        """Test that data_final can be today"""
        today_data = self.valid_form_data.copy()
        today_data['data_final'] = timezone.now().date().strftime('%Y-%m-%d')
        form = DiligenciasForm(data=today_data)
        self.assertTrue(form.is_valid())
    
    def test_form_brazilian_date_widget(self):
        """Test that form uses Brazilian date widget"""
        form = DiligenciasForm()
        data_final_widget = form.fields['data_final'].widget
        self.assertEqual(data_final_widget.__class__.__name__, 'BrazilianDateInput')
        self.assertIn('dd/mm/aaaa', data_final_widget.attrs.get('placeholder', ''))
    
    def test_form_optional_description(self):
        """Test that description field is optional"""
        data = self.valid_form_data.copy()
        data.pop('descricao')
        form = DiligenciasForm(data=data)
        self.assertTrue(form.is_valid())


class DiligenciasUpdateFormTest(TestCase):
    """Test cases for DiligenciasUpdateForm"""
    
    def setUp(self):
        """Set up test data"""
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False
        )
        
        self.tipo_diligencia = TipoDiligencia.objects.create(
            nome='Documentação',
            cor='#007bff'
        )
        
        self.diligencia = Diligencias.objects.create(
            cliente=self.cliente,
            tipo=self.tipo_diligencia,
            data_final=date.today() + timedelta(days=7),
            criado_por='Test User'
        )
    
    def test_form_mark_as_concluded(self):
        """Test marking diligencia as concluded"""
        form_data = {
            'concluida': True,
            'descricao': 'Diligência concluída com sucesso'
        }
        
        form = DiligenciasUpdateForm(data=form_data, instance=self.diligencia)
        self.assertTrue(form.is_valid())
        
        diligencia = form.save()
        self.assertTrue(diligencia.concluida)
        self.assertIsNotNone(diligencia.data_conclusao)
    
    def test_form_mark_as_not_concluded(self):
        """Test marking diligencia as not concluded"""
        # First mark as concluded
        self.diligencia.concluida = True
        self.diligencia.data_conclusao = timezone.now()
        self.diligencia.save()
        
        # Then mark as not concluded
        form_data = {
            'concluida': False,
            'descricao': 'Diligência reaberta'
        }
        
        form = DiligenciasUpdateForm(data=form_data, instance=self.diligencia)
        self.assertTrue(form.is_valid())
        
        diligencia = form.save()
        self.assertFalse(diligencia.concluida)
        self.assertIsNone(diligencia.data_conclusao)
    
    def test_form_auto_set_conclusion_date(self):
        """Test that conclusion date is auto-set when marking as concluded"""
        form_data = {
            'concluida': True
        }
        
        form = DiligenciasUpdateForm(data=form_data, instance=self.diligencia)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        self.assertIsNotNone(cleaned_data['data_conclusao'])
    
    def test_form_brazilian_datetime_widget(self):
        """Test that form uses Brazilian datetime widget"""
        form = DiligenciasUpdateForm()
        data_conclusao_widget = form.fields['data_conclusao'].widget
        self.assertEqual(data_conclusao_widget.__class__.__name__, 'BrazilianDateTimeInput')


