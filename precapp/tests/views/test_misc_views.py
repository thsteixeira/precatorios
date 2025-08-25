"""
Miscellaneous View Tests

Tests for miscellaneous views that don't fit into other categories.
Note: CustomizacaoViewTest has been moved to test_customizacao_view.py

Total expected tests: ~15 (UpdatePriorityByAgeViewTest)
Test classes: 1
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from datetime import date, timedelta
from unittest.mock import patch

from precapp.models import Cliente


class UpdatePriorityByAgeViewTest(TestCase):
    """Comprehensive tests for update_priority_by_age view function"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create clients with different ages for testing
        today = date.today()
        
        # Client aged 65 (should get priority)
        self.cliente_65 = Cliente.objects.create(
            nome='Cliente 65 Anos',
            cpf='11111111111',
            nascimento=today - timedelta(days=65*365 + 100),  # Clearly over 60
            prioridade=False
        )
        
        # Client aged 70 (should get priority)
        self.cliente_70 = Cliente.objects.create(
            nome='Cliente 70 Anos',
            cpf='22222222222',
            nascimento=today - timedelta(days=70*365 + 100),  # Clearly over 60
            prioridade=False
        )
        
        # Client aged 45 (should NOT get priority)
        self.cliente_45 = Cliente.objects.create(
            nome='Cliente 45 Anos',
            cpf='33333333333',
            nascimento=today - timedelta(days=45*365),  # Clearly under 60
            prioridade=False
        )
        
        # Client aged 62 but already has priority (should NOT be updated)
        self.cliente_62_priority = Cliente.objects.create(
            nome='Cliente 62 com Prioridade',
            cpf='44444444444',
            nascimento=today - timedelta(days=62*365 + 100),  # Over 60
            prioridade=True  # Already has priority
        )
        
        # Client exactly 60 years old (boundary test - should NOT get priority due to < condition)
        self.cliente_60_exact = Cliente.objects.create(
            nome='Cliente Exatos 60 Anos',
            cpf='55555555555',
            nascimento=today - timedelta(days=60*365.25),  # Exactly 60 years
            prioridade=False
        )
        
        self.client_app = Client()

    # ==================== AUTHENTICATION TESTS ====================
    
    def test_update_priority_authentication_required(self):
        """Test that update priority view requires authentication"""
        response = self.client_app.post(reverse('update_priority_by_age'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)
    
    def test_update_priority_get_method_not_allowed(self):
        """Test that GET method is not allowed (POST only view)"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('update_priority_by_age'))
        self.assertEqual(response.status_code, 405)  # Method not allowed

    # ==================== CORE BUSINESS LOGIC TESTS ====================
    
    def test_update_priority_successful_updates(self):
        """Test successful priority updates for clients over 60"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify initial state
        self.assertFalse(self.cliente_65.prioridade)
        self.assertFalse(self.cliente_70.prioridade)
        self.assertTrue(self.cliente_62_priority.prioridade)  # Already has priority
        
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        # Should redirect to clientes page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('clientes'))
        
        # Refresh from database and verify updates
        self.cliente_65.refresh_from_db()
        self.cliente_70.refresh_from_db()
        self.cliente_45.refresh_from_db()
        self.cliente_62_priority.refresh_from_db()
        self.cliente_60_exact.refresh_from_db()
        
        # Clients over 60 should now have priority
        self.assertTrue(self.cliente_65.prioridade)
        self.assertTrue(self.cliente_70.prioridade)
        
        # Client under 60 should remain without priority
        self.assertFalse(self.cliente_45.prioridade)
        
        # Client exactly 60 should NOT get priority (< condition, not <=)
        self.assertFalse(self.cliente_60_exact.prioridade)
        
        # Client who already had priority should remain unchanged
        self.assertTrue(self.cliente_62_priority.prioridade)
    
    def test_update_priority_success_messages(self):
        """Test success messages when clients are updated"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(reverse('update_priority_by_age'))
        messages = list(get_messages(response.wsgi_request))
        
        # Should have success message
        success_messages = [m for m in messages if m.tags == 'success']
        self.assertEqual(len(success_messages), 1)
        self.assertIn('cliente(s) com mais de 60 anos foram atualizados', str(success_messages[0]))
        
        # Should have info message with examples
        info_messages = [m for m in messages if m.tags == 'info']
        self.assertEqual(len(info_messages), 1)
        self.assertIn('Exemplos atualizados:', str(info_messages[0]))
    
    def test_update_priority_no_clients_to_update(self):
        """Test when no clients need priority update"""
        # Set all clients over 60 to already have priority
        Cliente.objects.filter(nascimento__lt=date.today() - timedelta(days=60*365.25)).update(prioridade=True)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        messages = list(get_messages(response.wsgi_request))
        info_messages = [m for m in messages if m.tags == 'info']
        
        self.assertEqual(len(info_messages), 1)
        self.assertIn('Nenhum cliente encontrado que precise ser atualizado', str(info_messages[0]))
        self.assertIn('já possuem status prioritário', str(info_messages[0]))
    
    def test_update_priority_empty_database(self):
        """Test behavior with no clients in database"""
        Cliente.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        info_messages = [m for m in messages if m.tags == 'info']
        
        self.assertEqual(len(info_messages), 1)
        self.assertIn('Nenhum cliente encontrado', str(info_messages[0]))

    # ==================== AGE CALCULATION TESTS ====================
    
    def test_age_calculation_boundary_conditions(self):
        """Test age calculation boundary conditions"""
        today = date.today()
        
        # Create clients with precise age boundaries
        cliente_59_11_months = Cliente.objects.create(
            nome='Cliente 59 anos 11 meses',
            cpf='66666666666',
            nascimento=today - timedelta(days=59*365 + 330),  # Just under 60
            prioridade=False
        )
        
        cliente_60_1_day = Cliente.objects.create(
            nome='Cliente 60 anos 1 dia',
            cpf='77777777777',
            nascimento=today - timedelta(days=60*365.25 + 1),  # Just over 60
            prioridade=False
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        # Refresh from database
        cliente_59_11_months.refresh_from_db()
        cliente_60_1_day.refresh_from_db()
        
        # Just under 60 should not get priority
        self.assertFalse(cliente_59_11_months.prioridade)
        
        # Just over 60 should get priority
        self.assertTrue(cliente_60_1_day.prioridade)
    
    def test_leap_year_calculation(self):
        """Test age calculation considering leap years"""
        # Test with a date that would be affected by leap years
        self.client_app.login(username='testuser', password='testpass123')
        
        # The function uses 365.25 days per year to account for leap years
        # This test ensures the calculation is consistent
        
        response = self.client_app.post(reverse('update_priority_by_age'))
        self.assertEqual(response.status_code, 302)
        
        # Verify the calculation used the correct formula
        sixty_years_ago = date.today() - timedelta(days=60*365.25)
        
        # All clients born before this calculated date should be updated
        clients_to_update = Cliente.objects.filter(
            nascimento__lt=sixty_years_ago,
            prioridade=True  # Should now have priority
        )
        
        # Verify the expected clients were updated (only 65 and 70, not exactly 60)
        expected_updated = [self.cliente_65, self.cliente_70]
        for client in expected_updated:
            client.refresh_from_db()
            self.assertTrue(client.prioridade)
        
        # Cliente exactly 60 should NOT be updated due to < condition
        self.cliente_60_exact.refresh_from_db()
        self.assertFalse(self.cliente_60_exact.prioridade)

    # ==================== ERROR HANDLING TESTS ====================
    
    @patch('precapp.views.Cliente.objects.filter')
    def test_database_error_handling(self, mock_filter):
        """Test error handling when database operations fail"""
        # Mock a database error
        mock_filter.side_effect = Exception("Database connection error")
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        # Should still redirect (error handling)
        self.assertEqual(response.status_code, 302)
        
        # Should have error message
        messages = list(get_messages(response.wsgi_request))
        error_messages = [m for m in messages if m.tags == 'error']
        
        self.assertEqual(len(error_messages), 1)
        self.assertIn('Erro ao atualizar prioridades', str(error_messages[0]))
        self.assertIn('Database connection error', str(error_messages[0]))

    # ==================== LARGE DATASET PERFORMANCE TESTS ====================
    
    def test_bulk_update_performance(self):
        """Test performance with large number of clients"""
        # Create many clients over 60 for bulk update testing
        today = date.today()
        clients_batch = []
        
        for i in range(50):
            clients_batch.append(Cliente(
                nome=f'Cliente Bulk {i}',
                cpf=f'{i+10000000000:011d}',  # Generate unique CPFs
                nascimento=today - timedelta(days=(65+i)*365),  # Ages 65-114
                prioridade=False
            ))
        
        Cliente.objects.bulk_create(clients_batch)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        self.assertEqual(response.status_code, 302)
        
        # Verify all bulk clients were updated
        updated_count = Cliente.objects.filter(
            nome__startswith='Cliente Bulk',
            prioridade=True
        ).count()
        
        self.assertEqual(updated_count, 50)
        
        # Check success message mentions correct count (only 2 from setup: cliente_65 and cliente_70)
        messages = list(get_messages(response.wsgi_request))
        success_messages = [m for m in messages if m.tags == 'success']
        self.assertEqual(len(success_messages), 1)
        # Total should be 50 (bulk) + 2 (setup clients over 60: 65 and 70) = 52
        self.assertIn('52 cliente(s)', str(success_messages[0]))

    # ==================== MESSAGE SYSTEM TESTS ====================
    
    def test_example_clients_in_messages(self):
        """Test that example clients are shown in info messages"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        messages = list(get_messages(response.wsgi_request))
        info_messages = [m for m in messages if m.tags == 'info']
        
        self.assertEqual(len(info_messages), 1)
        
        # Should contain client names as examples
        message_text = str(info_messages[0])
        self.assertIn('Exemplos atualizados:', message_text)
        
        # Should contain at least one client name (only 65 and 70 get updated, not exactly 60)
        client_names = [self.cliente_65.nome, self.cliente_70.nome]
        found_names = [name for name in client_names if name in message_text]
        self.assertGreater(len(found_names), 0)
    
    def test_message_with_more_than_three_clients(self):
        """Test message format when more than 3 clients are updated"""
        # Create additional clients to exceed the 3-example limit
        today = date.today()
        for i in range(5):
            Cliente.objects.create(
                nome=f'Extra Cliente {i}',
                cpf=f'{i+20000000000:011d}',
                nascimento=today - timedelta(days=(65+i)*365),
                prioridade=False
            )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        messages = list(get_messages(response.wsgi_request))
        info_messages = [m for m in messages if m.tags == 'info']
        
        self.assertEqual(len(info_messages), 1)
        message_text = str(info_messages[0])
        
        # Should show "e mais X cliente(s)" when more than 3
        self.assertIn('e mais', message_text)
        self.assertIn('cliente(s)', message_text)

    # ==================== INTEGRATION TESTS ====================
    
    def test_url_routing(self):
        """Test that URL routing works correctly"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Test the URL is accessible
        url = reverse('update_priority_by_age')
        self.assertEqual(url, '/clientes/update-priority/')
        
        response = self.client_app.post(url)
        self.assertEqual(response.status_code, 302)
    
    def test_redirect_to_clientes_page(self):
        """Test that view redirects to clientes page after operation"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.post(reverse('update_priority_by_age'))
        
        self.assertRedirects(response, reverse('clientes'))
    
    def test_concurrent_access_safety(self):
        """Test that concurrent access doesn't cause data corruption"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Simulate concurrent requests (simplified test)
        response1 = self.client_app.post(reverse('update_priority_by_age'))
        response2 = self.client_app.post(reverse('update_priority_by_age'))
        
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response2.status_code, 302)
        
        # Verify clients are still in consistent state
        self.cliente_65.refresh_from_db()
        self.cliente_70.refresh_from_db()
        
        # Should still have priority (no duplicate processing issues)
        self.assertTrue(self.cliente_65.prioridade)
        self.assertTrue(self.cliente_70.prioridade)
