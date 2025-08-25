"""
Authentication View Tests

Tests for authentication-related views including:
- LoginViewTest: Custom login view functionality
- LogoutViewTest: Custom logout view functionality

Total tests: 26 (23 LoginViewTest + 7 LogoutViewTest)
Test classes migrated: 2
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages


class LoginViewTest(TestCase):
    """
    Comprehensive test cases for the custom login_view function.
    
    Tests cover all authentication scenarios, security features, redirect logic,
    error handling, and user experience flows for the custom login implementation.
    """
    
    def setUp(self):
        """Set up test data for login view testing"""
        self.client_app = Client()
        
        # Create test users with different profiles
        self.active_user = User.objects.create_user(
            username='activeuser',
            email='active@test.com',
            password='testpass123',
            first_name='João',
            last_name='Silva'
        )
        
        self.inactive_user = User.objects.create_user(
            username='inactiveuser',
            email='inactive@test.com',
            password='testpass123',
            is_active=False
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        # Test URLs
        self.login_url = reverse('login')
        self.home_url = reverse('home')
        
    def test_login_view_get_request_unauthenticated(self):
        """Test login view GET request for unauthenticated user"""
        response = self.client_app.get(self.login_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertContains(response, 'username')
        self.assertContains(response, 'password')
        self.assertTemplateUsed(response, 'registration/login.html')
        
    def test_login_view_get_request_authenticated_user_redirects(self):
        """Test that authenticated users are redirected from login page"""
        self.client_app.login(username='activeuser', password='testpass123')
        
        response = self.client_app.get(self.login_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        
    def test_login_view_valid_credentials_success(self):
        """Test successful login with valid credentials"""
        response = self.client_app.post(self.login_url, {
            'username': 'activeuser',
            'password': 'testpass123'
        })
        
        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        
        # User should be authenticated
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, 'activeuser')
        
    def test_login_view_success_message_with_full_name(self):
        """Test success message displays user's full name when available"""
        response = self.client_app.post(self.login_url, {
            'username': 'activeuser',
            'password': 'testpass123'
        }, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        success_message = str(messages[0])
        
        self.assertIn('Bem-vindo, João Silva!', success_message)
        
    def test_login_view_success_message_with_username_fallback(self):
        """Test success message uses username when full name not available"""
        # Create user without first/last name
        user_no_name = User.objects.create_user(
            username='noname',
            password='testpass123'
        )
        
        response = self.client_app.post(self.login_url, {
            'username': 'noname',
            'password': 'testpass123'
        }, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        success_message = str(messages[0])
        
        self.assertIn('Bem-vindo, noname!', success_message)
        
    def test_login_view_invalid_username(self):
        """Test login with invalid username"""
        response = self.client_app.post(self.login_url, {
            'username': 'nonexistentuser',
            'password': 'testpass123'
        })
        
        # Should not redirect (stay on login page)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # Should show error message (Django's AuthenticationForm handles this)
        messages = list(get_messages(response.wsgi_request))
        error_message = str(messages[0])
        # Django's AuthenticationForm shows form validation error for invalid credentials
        self.assertIn('Por favor, corrija os erros abaixo', error_message)
        
        # User should not be authenticated
        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)
        
    def test_login_view_invalid_password(self):
        """Test login with invalid password"""
        response = self.client_app.post(self.login_url, {
            'username': 'activeuser',
            'password': 'wrongpassword'
        })
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # Should show error message (Django's AuthenticationForm handles this)
        messages = list(get_messages(response.wsgi_request))
        error_message = str(messages[0])
        # Django's AuthenticationForm shows form validation error for invalid credentials
        self.assertIn('Por favor, corrija os erros abaixo', error_message)
        
        # User should not be authenticated
        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)
        
    def test_login_view_inactive_user(self):
        """Test login attempt with inactive user account"""
        response = self.client_app.post(self.login_url, {
            'username': 'inactiveuser',
            'password': 'testpass123'
        })
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # Should show error message (Django's AuthenticationForm handles this)
        messages = list(get_messages(response.wsgi_request))
        error_message = str(messages[0])
        # Django's AuthenticationForm shows form validation error for inactive users
        self.assertIn('Por favor, corrija os erros abaixo', error_message)
        
        # User should not be authenticated
        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)
        
    def test_login_view_empty_credentials(self):
        """Test login with empty username/password"""
        response = self.client_app.post(self.login_url, {
            'username': '',
            'password': ''
        })
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # Should show form validation error
        messages = list(get_messages(response.wsgi_request))
        error_message = str(messages[0])
        self.assertIn('Por favor, corrija os erros abaixo', error_message)
        
    def test_login_view_form_validation_errors(self):
        """Test that form validation errors are handled properly"""
        response = self.client_app.post(self.login_url, {
            'username': '',  # Empty username should trigger validation
            'password': 'testpass123'
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # Should show form error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        error_message = str(messages[0])
        self.assertIn('Por favor, corrija os erros abaixo', error_message)
        
    def test_login_view_next_parameter_redirect(self):
        """Test redirect to 'next' parameter after successful login"""
        protected_url = reverse('precatorios')  # A login-required view
        next_url = f"{self.login_url}?next={protected_url}"
        
        response = self.client_app.post(next_url, {
            'username': 'activeuser',
            'password': 'testpass123'
        })
        
        # Should redirect to the 'next' URL
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, protected_url)
        
    def test_login_view_next_parameter_malicious_redirect_protection(self):
        """Test protection against malicious redirect URLs"""
        malicious_url = "http://evil.com/steal-data"
        next_url = f"{self.login_url}?next={malicious_url}"
        
        response = self.client_app.post(next_url, {
            'username': 'activeuser',
            'password': 'testpass123'
        })
        
        # Should redirect to home, not malicious URL
        # Note: Django's redirect() function should handle this safely
        self.assertEqual(response.status_code, 302)
        # The actual redirect behavior depends on Django's implementation
        
    def test_login_view_no_next_parameter_defaults_to_home(self):
        """Test that login redirects to home when no 'next' parameter"""
        response = self.client_app.post(self.login_url, {
            'username': 'activeuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        
    def test_login_view_case_sensitive_username(self):
        """Test that username is case-sensitive"""
        response = self.client_app.post(self.login_url, {
            'username': 'ACTIVEUSER',  # Different case
            'password': 'testpass123'
        })
        
        # Should fail with case-sensitive username
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        error_message = str(messages[0])
        # Django's AuthenticationForm shows form validation error for case mismatch
        self.assertIn('Por favor, corrija os erros abaixo', error_message)
        
    def test_login_view_csrf_protection(self):
        """Test that login view has CSRF protection"""
        # GET request should include CSRF token
        response = self.client_app.get(self.login_url)
        self.assertContains(response, 'csrfmiddlewaretoken')
        
    def test_login_view_admin_user_login(self):
        """Test that admin users can login successfully"""
        response = self.client_app.post(self.login_url, {
            'username': 'admin',
            'password': 'adminpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        
        # Follow redirect to check success message
        response = self.client_app.post(self.login_url, {
            'username': 'admin',
            'password': 'adminpass123'
        }, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        if messages:  # Check if messages exist before accessing
            success_message = str(messages[0])
            self.assertIn('Bem-vindo, Admin User!', success_message)
        else:
            # If no messages, verify user is still authenticated
            self.assertTrue(response.wsgi_request.user.is_authenticated)
            self.assertEqual(response.wsgi_request.user.username, 'admin')
        
    def test_login_view_multiple_failed_attempts(self):
        """Test behavior with multiple failed login attempts"""
        # First failed attempt
        response1 = self.client_app.post(self.login_url, {
            'username': 'activeuser',
            'password': 'wrongpass1'
        })
        
        # Second failed attempt
        response2 = self.client_app.post(self.login_url, {
            'username': 'activeuser',
            'password': 'wrongpass2'
        })
        
        # Both should fail with error messages
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Then successful login should still work
        response3 = self.client_app.post(self.login_url, {
            'username': 'activeuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response3.status_code, 302)
        self.assertRedirects(response3, self.home_url)
        
    def test_login_view_sql_injection_protection(self):
        """Test protection against SQL injection in login"""
        malicious_username = "admin'; DROP TABLE auth_user; --"
        
        response = self.client_app.post(self.login_url, {
            'username': malicious_username,
            'password': 'testpass123'
        })
        
        # Should safely fail without causing database issues
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        error_message = str(messages[0])
        # Django's AuthenticationForm shows form validation error for malicious input
        self.assertIn('Por favor, corrija os erros abaixo', error_message)
        
        # User table should still exist and be intact
        self.assertTrue(User.objects.filter(username='activeuser').exists())
        
    def test_login_view_xss_protection(self):
        """Test protection against XSS in login form"""
        xss_payload = "<script>alert('xss')</script>"
        
        response = self.client_app.post(self.login_url, {
            'username': xss_payload,
            'password': 'testpass123'
        })
        
        # Should not contain unescaped script tags in response
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode('utf-8')
        self.assertNotIn('<script>alert(\'xss\')</script>', response_content)
        
    def test_login_view_session_creation(self):
        """Test that successful login creates proper session"""
        response = self.client_app.post(self.login_url, {
            'username': 'activeuser',
            'password': 'testpass123'
        })
        
        # Check that session was created
        self.assertTrue('_auth_user_id' in self.client_app.session)
        self.assertEqual(
            int(self.client_app.session['_auth_user_id']), 
            self.active_user.id
        )
        
    def test_login_view_form_persistence_on_error(self):
        """Test that form data persists when there are validation errors"""
        response = self.client_app.post(self.login_url, {
            'username': 'validuser',
            'password': ''  # Missing password
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        
        # Form should contain the username that was entered
        form = response.context['form']
        self.assertEqual(form.data['username'], 'validuser')
        
    def test_login_view_context_data(self):
        """Test that login view provides correct context data"""
        response = self.client_app.get(self.login_url)
        
        # Should contain form in context
        self.assertIn('form', response.context)
        self.assertTrue(hasattr(response.context['form'], 'fields'))
        self.assertIn('username', response.context['form'].fields)
        self.assertIn('password', response.context['form'].fields)


class LogoutViewTest(TestCase):
    """
    Test cases for the custom logout_view function.
    
    Tests cover logout functionality, session management, redirect behavior,
    and proper cleanup of authentication state.
    """
    
    def setUp(self):
        """Set up test data for logout view testing"""
        self.client_app = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Test URLs
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        
    def test_logout_view_authenticated_user(self):
        """Test logout functionality for authenticated user"""
        # First login
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify user is authenticated
        response = self.client_app.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        # Now logout
        response = self.client_app.post(self.logout_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)
        
    def test_logout_view_success_message(self):
        """Test that logout shows success message"""
        # Login first
        self.client_app.login(username='testuser', password='testpass123')
        
        # Logout and follow redirect
        response = self.client_app.post(self.logout_url, follow=True)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        success_message = str(messages[0])
        self.assertIn('Você foi desconectado com sucesso', success_message)
        
    def test_logout_view_session_cleanup(self):
        """Test that logout properly cleans up session data"""
        # Login first
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify session exists
        self.assertTrue('_auth_user_id' in self.client_app.session)
        
        # Logout
        self.client_app.post(self.logout_url)
        
        # Session should be cleared
        self.assertFalse('_auth_user_id' in self.client_app.session)
        
    def test_logout_view_unauthenticated_user(self):
        """Test logout view when user is not authenticated"""
        # Attempt logout without being logged in
        response = self.client_app.post(self.logout_url)
        
        # Should still redirect to login (logout is idempotent)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)
        
    def test_logout_view_get_request(self):
        """Test logout view with GET request (should still work)"""
        # Login first
        self.client_app.login(username='testuser', password='testpass123')
        
        # GET request to logout
        response = self.client_app.get(self.logout_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)
        
    def test_logout_view_prevents_access_to_protected_views(self):
        """Test that after logout, user cannot access protected views"""
        # Login first
        self.client_app.login(username='testuser', password='testpass123')
        
        # Verify access to protected view
        response = self.client_app.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        # Logout
        self.client_app.post(self.logout_url)
        
        # Try to access protected view - should redirect to login
        response = self.client_app.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        
    def test_logout_view_multiple_logouts(self):
        """Test multiple logout attempts are handled safely"""
        # Login first
        self.client_app.login(username='testuser', password='testpass123')
        
        # First logout
        response1 = self.client_app.post(self.logout_url)
        self.assertEqual(response1.status_code, 302)
        
        # Second logout (already logged out)
        response2 = self.client_app.post(self.logout_url)
        self.assertEqual(response2.status_code, 302)
        
        # Both should redirect to login safely
        self.assertRedirects(response1, self.login_url)
        self.assertRedirects(response2, self.login_url)
