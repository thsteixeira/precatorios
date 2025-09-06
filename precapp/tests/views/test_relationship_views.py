"""
Relationship View Tests

Tests for many-to-many relationship operations including:
- ManyToManyRelationshipTest: Client-Precatorio relationship management

Total expected tests: 5 (3 original + 2 new field integration tests)
Test classes migrated: 1
"""

from django.test import TestCase
from datetime import date

from precapp.models import Precatorio, Cliente


class ManyToManyRelationshipTest(TestCase):
    """Test many-to-many relationships between models"""
    
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
            honorarios_sucumbenciais='pendente',
            observacao='Precatório de teste para relacionamentos many-to-many'
        )
        
        self.precatorio2 = Precatorio.objects.create(
            cnj='7654321-12.2023.8.26.0200',
            orcamento=2023,
            origem='1234567-98.2022.8.26.0002',
            valor_de_face=75000.00,
            ultima_atualizacao=75000.00,
            data_ultima_atualizacao=date(2023, 2, 1),
            percentual_contratuais_assinado=12.0,
            percentual_contratuais_apartado=6.0,
            percentual_sucumbenciais=18.0,
            credito_principal='pendente',
            honorarios_contratuais='pendente',
            honorarios_sucumbenciais='pendente',
            observacao='Segundo precatório para testes de relacionamentos múltiplos'
        )
        
        self.cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='João Silva',
            nascimento=date(1980, 5, 15),
            prioridade=False,
            observacao='Cliente de teste para relacionamentos many-to-many'
        )
        
        self.cliente2 = Cliente.objects.create(
            cpf='98765432100',
            nome='Maria Santos',
            nascimento=date(1985, 3, 20),
            prioridade=True,
            observacao='Cliente prioritário para testes de múltiplos relacionamentos'
        )
    
    def test_cliente_precatorio_relationship(self):
        """Test linking cliente to precatorio"""
        self.cliente.precatorios.add(self.precatorio)
        
        # Verify relationship from both sides
        self.assertIn(self.precatorio, self.cliente.precatorios.all())
        self.assertIn(self.cliente, self.precatorio.clientes.all())
    
    def test_multiple_relationships(self):
        """Test multiple relationships"""
        # Link cliente to multiple precatorios
        self.cliente.precatorios.add(self.precatorio, self.precatorio2)
        
        # Link multiple clientes to one precatorio
        self.precatorio.clientes.add(self.cliente, self.cliente2)
        
        # Verify relationships
        self.assertEqual(self.cliente.precatorios.count(), 2)
        self.assertEqual(self.precatorio.clientes.count(), 2)
    
    def test_relationship_unlinking(self):
        """Test unlinking relationships"""
        # Create relationships
        self.cliente.precatorios.add(self.precatorio, self.precatorio2)
        self.cliente2.precatorios.add(self.precatorio)
        
        # Verify setup
        self.assertEqual(self.cliente.precatorios.count(), 2)
        self.assertIn(self.cliente2, self.precatorio.clientes.all())
        
        # Test unlinking one relationship doesn't affect others
        self.precatorio.clientes.remove(self.cliente)
        
        # Verify partial unlink worked
        self.assertNotIn(self.cliente, self.precatorio.clientes.all())
        self.assertIn(self.cliente2, self.precatorio.clientes.all())
        self.assertIn(self.precatorio2, self.cliente.precatorios.all())
    
    def test_new_fields_with_relationships(self):
        """Test that new observacao fields work correctly with relationships"""
        # Create relationships
        self.cliente.precatorios.add(self.precatorio, self.precatorio2)
        
        # Verify observacao fields are preserved
        linked_precatorio = self.cliente.precatorios.get(cnj=self.precatorio.cnj)
        self.assertEqual(
            linked_precatorio.observacao, 
            'Precatório de teste para relacionamentos many-to-many'
        )
        
        linked_cliente = self.precatorio.clientes.get(cpf=self.cliente.cpf)
        self.assertEqual(
            linked_cliente.observacao, 
            'Cliente de teste para relacionamentos many-to-many'
        )
        
        # Verify file field is accessible (should be None/False for test data)
        self.assertFalse(linked_precatorio.integra_precatorio)
    
    def test_relationship_integrity_with_new_fields(self):
        """Test that relationship integrity is maintained with new fields"""
        # Link with different observacao content
        self.precatorio.observacao = 'Observação atualizada para teste de integridade'
        self.precatorio.save()
        
        self.cliente.observacao = 'Cliente com observação atualizada'
        self.cliente.save()
        
        # Create relationship
        self.cliente.precatorios.add(self.precatorio)
        
        # Verify relationship works and fields are preserved
        self.assertIn(self.precatorio, self.cliente.precatorios.all())
        
        # Retrieve and verify field content
        retrieved_precatorio = self.cliente.precatorios.first()
        self.assertEqual(
            retrieved_precatorio.observacao, 
            'Observação atualizada para teste de integridade'
        )
        
        retrieved_cliente = self.precatorio.clientes.first()
        self.assertEqual(
            retrieved_cliente.observacao, 
            'Cliente com observação atualizada'
        )
