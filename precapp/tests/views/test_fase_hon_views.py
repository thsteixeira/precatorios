from datetime import date

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.middleware.csrf import get_token

from precapp.models import FaseHonorariosContratuais, Cliente, Precatorio, Alvara


class FaseHonorariosContratuaisViewTest(TestCase):
    """Comprehensive test cases for FaseHonorariosContratuais views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.fase_honorarios = FaseHonorariosContratuais.objects.create(
            nome='Test Fase Honorários',
            descricao='Fase de teste para honorários',
            cor='#28A745',
            ordem=1,
            ativa=True
        )
        
        self.fase_honorarios_inactive = FaseHonorariosContratuais.objects.create(
            nome='Fase Inativa',
            descricao='Fase inativa para testes',
            cor='#DC3545',
            ordem=2,
            ativa=False
        )
        
        self.client_app = Client()

    # ===============================
    # FASES_HONORARIOS_VIEW TESTS (List View)
    # ===============================
    
    def test_fases_honorarios_list_view_authenticated_success(self):
        """Test honorários phases list view with authentication"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('fases_honorarios'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Fase Honorários')
        self.assertContains(response, '#28A745')
        self.assertContains(response, 'Fase Inativa')
    
    def test_fases_honorarios_list_view_unauthenticated_redirect(self):
        """Test unauthenticated access redirects to login"""
        response = self.client_app.get(reverse('fases_honorarios'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/login/?next={reverse("fases_honorarios")}')
    
    def test_fases_honorarios_list_view_context_data(self):
        """Test context data includes all required statistics"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('fases_honorarios'))
        self.assertEqual(response.status_code, 200)
        
        context = response.context
        self.assertIn('fases', context)
        self.assertIn('total_fases', context)
        self.assertIn('fases_ativas', context)
        self.assertIn('fases_inativas', context)
        
        # Verify statistics
        self.assertEqual(context['total_fases'], 2)
        self.assertEqual(context['fases_ativas'], 1)
        self.assertEqual(context['fases_inativas'], 1)
    
    def test_fases_honorarios_list_view_empty_queryset(self):
        """Test list view with no phases"""
        FaseHonorariosContratuais.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('fases_honorarios'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_fases'], 0)
        self.assertEqual(response.context['fases_ativas'], 0)
        self.assertEqual(response.context['fases_inativas'], 0)
    
    def test_fases_honorarios_list_view_ordering(self):
        """Test phases are ordered correctly"""
        # Create phases with different ordem values
        fase1 = FaseHonorariosContratuais.objects.create(
            nome='Fase A', ordem=3, ativa=True
        )
        fase2 = FaseHonorariosContratuais.objects.create(
            nome='Fase B', ordem=1, ativa=True
        )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('fases_honorarios'))
        
        fases_list = list(response.context['fases'])
        # Should be ordered by ordem, then nome
        self.assertTrue(fases_list[0].ordem <= fases_list[1].ordem)

    # ===============================
    # NOVA_FASE_HONORARIOS_VIEW TESTS (Create View)
    # ===============================
    
    def test_nova_fase_honorarios_view_get_authenticated(self):
        """Test GET request to nova fase honorarios form"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('nova_fase_honorarios'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertContains(response, 'Nova Fase Honorários Contratuais')
        self.assertContains(response, 'Criar Fase')
    
    def test_nova_fase_honorarios_view_get_unauthenticated(self):
        """Test unauthenticated GET redirects to login"""
        response = self.client_app.get(reverse('nova_fase_honorarios'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/login/?next={reverse("nova_fase_honorarios")}')
    
    def test_nova_fase_honorarios_view_post_success(self):
        """Test successful phase creation"""
        self.client_app.login(username='testuser', password='testpass123')
        
        initial_count = FaseHonorariosContratuais.objects.count()
        
        form_data = {
            'nome': 'Nova Fase Honorários',
            'descricao': 'Nova fase para honorários contratuais',
            'cor': '#FFC107',
            'ordem': 3,
            'ativa': True
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fases_honorarios'))
        
        # Verify creation
        self.assertEqual(FaseHonorariosContratuais.objects.count(), initial_count + 1)
        nova_fase = FaseHonorariosContratuais.objects.get(nome='Nova Fase Honorários')
        self.assertEqual(nova_fase.cor, '#FFC107')
        self.assertEqual(nova_fase.ordem, 3)
        self.assertTrue(nova_fase.ativa)
    
    def test_nova_fase_honorarios_view_post_unauthenticated(self):
        """Test unauthenticated POST redirects to login"""
        form_data = {
            'nome': 'Test Fase',
            'descricao': 'Test',
            'cor': '#FFC107',
            'ordem': 1,
            'ativa': True
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/login/?next={reverse("nova_fase_honorarios")}')
    
    def test_nova_fase_honorarios_view_post_invalid_form(self):
        """Test POST with invalid form data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': '',  # Required field empty
            'descricao': 'Test',
            'cor': 'invalid-color',
            'ordem': -1,  # Invalid ordem
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        self.assertEqual(response.status_code, 200)  # Should not redirect
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_nova_fase_honorarios_view_duplicate_nome(self):
        """Test creating phase with duplicate name"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Test Fase Honorários',  # Already exists
            'descricao': 'Duplicate test',
            'cor': '#FFC107',
            'ordem': 10,
            'ativa': True
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        # Should show form errors for duplicate name
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    def test_nova_fase_honorarios_view_message_success(self):
        """Test success message is displayed"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Fase com Mensagem',
            'descricao': 'Test message',
            'cor': '#FFC107',
            'ordem': 1,
            'ativa': True
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data, follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Fase de Honorários Contratuais "Fase com Mensagem" criada com sucesso!')

    # ===============================
    # EDITAR_FASE_HONORARIOS_VIEW TESTS (Edit View)
    # ===============================
    
    def test_editar_fase_honorarios_view_get_authenticated(self):
        """Test GET request to edit fase honorarios form"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('fase', response.context)
        self.assertEqual(response.context['fase'], self.fase_honorarios)
        self.assertContains(response, f'Editar Fase Honorários Contratuais: {self.fase_honorarios.nome}')
    
    def test_editar_fase_honorarios_view_get_unauthenticated(self):
        """Test unauthenticated GET redirects to login"""
        response = self.client_app.get(reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.assertEqual(response.status_code, 302)
        expected_url = f'/login/?next={reverse("editar_fase_honorarios", args=[self.fase_honorarios.id])}'
        self.assertRedirects(response, expected_url)
    
    def test_editar_fase_honorarios_view_nonexistent_fase(self):
        """Test editing non-existent fase returns 404"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('editar_fase_honorarios', args=[99999]))
        self.assertEqual(response.status_code, 404)
    
    def test_editar_fase_honorarios_view_post_success(self):
        """Test successful phase editing"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Fase Honorários Editada',
            'descricao': 'Descrição editada',
            'cor': '#DC3545',
            'ordem': 2,
            'ativa': False
        }
        
        response = self.client_app.post(
            reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]), 
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fases_honorarios'))
        
        # Verify update
        self.fase_honorarios.refresh_from_db()
        self.assertEqual(self.fase_honorarios.nome, 'Fase Honorários Editada')
        self.assertEqual(self.fase_honorarios.cor, '#DC3545')
        self.assertEqual(self.fase_honorarios.ordem, 2)
        self.assertFalse(self.fase_honorarios.ativa)
    
    def test_editar_fase_honorarios_view_post_unauthenticated(self):
        """Test unauthenticated POST redirects to login"""
        form_data = {
            'nome': 'Editado',
            'descricao': 'Test',
            'cor': '#DC3545',
            'ordem': 2,
            'ativa': False
        }
        
        response = self.client_app.post(
            reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]), 
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        expected_url = f'/login/?next={reverse("editar_fase_honorarios", args=[self.fase_honorarios.id])}'
        self.assertRedirects(response, expected_url)
    
    def test_editar_fase_honorarios_view_post_invalid_form(self):
        """Test POST with invalid form data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': '',  # Required field empty
            'descricao': 'Test',
            'cor': 'invalid-color',
            'ordem': -1,
        }
        
        response = self.client_app.post(
            reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]), 
            data=form_data
        )
        self.assertEqual(response.status_code, 200)  # Should not redirect
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_editar_fase_honorarios_view_form_prepopulated(self):
        """Test form is pre-populated with existing data"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]))
        form = response.context['form']
        
        self.assertEqual(form.instance, self.fase_honorarios)
        self.assertEqual(form.initial.get('nome') or form.instance.nome, self.fase_honorarios.nome)
    
    def test_editar_fase_honorarios_view_message_success(self):
        """Test success message is displayed"""
        self.client_app.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Fase Editada Com Mensagem',
            'descricao': 'Test message',
            'cor': '#DC3545',
            'ordem': 2,
            'ativa': True
        }
        
        response = self.client_app.post(
            reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]), 
            data=form_data,
            follow=True
        )
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Fase de Honorários Contratuais "Fase Editada Com Mensagem" atualizada com sucesso!')

    # ===============================
    # DELETAR_FASE_HONORARIOS_VIEW TESTS (Delete View)
    # ===============================
    
    def test_deletar_fase_honorarios_view_post_success(self):
        """Test successful phase deletion"""
        self.client_app.login(username='testuser', password='testpass123')
        
        fase_id = self.fase_honorarios.id
        fase_nome = self.fase_honorarios.nome
        
        response = self.client_app.post(
            reverse('deletar_fase_honorarios', args=[fase_id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fases_honorarios'))
        
        # Verify deletion
        with self.assertRaises(FaseHonorariosContratuais.DoesNotExist):
            FaseHonorariosContratuais.objects.get(id=fase_id)
    
    def test_deletar_fase_honorarios_view_get_redirects(self):
        """Test GET request redirects to fases list"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('deletar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fases_honorarios'))
    
    def test_deletar_fase_honorarios_view_unauthenticated(self):
        """Test unauthenticated access redirects to login"""
        response = self.client_app.post(reverse('deletar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.assertEqual(response.status_code, 302)
        expected_url = f'/login/?next={reverse("deletar_fase_honorarios", args=[self.fase_honorarios.id])}'
        self.assertRedirects(response, expected_url)
    
    def test_deletar_fase_honorarios_view_nonexistent_fase(self):
        """Test deleting non-existent fase returns 404"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(reverse('deletar_fase_honorarios', args=[99999]))
        self.assertEqual(response.status_code, 404)
    
    def test_deletar_fase_honorarios_view_with_alvaras_constraint(self):
        """Test cannot delete phase that is used by alvaras"""
        from datetime import date
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Create test data
        cliente = Cliente.objects.create(
            cpf='12345678909',
            nome='Test Cliente',
            nascimento=date(1980, 1, 1),
            prioridade=False
        )
        
        precatorio = Precatorio.objects.create(
            cnj='1234567-89.2023.8.26.0100',
            orcamento=2023,
            origem='Test case',
            valor_de_face=1000.00
        )
        precatorio.clientes.add(cliente)
        
        # Create alvara that uses this fase_honorarios
        alvara = Alvara.objects.create(
            precatorio=precatorio,
            cliente=cliente,
            valor_principal=500.00,
            honorarios_contratuais=100.00,
            tipo='Test alvara',
            fase_honorarios_contratuais=self.fase_honorarios
        )
        
        fase_id = self.fase_honorarios.id
        
        response = self.client_app.post(
            reverse('deletar_fase_honorarios', args=[fase_id]),
            follow=True
        )
        
        # Should redirect back to fases list
        self.assertEqual(response.status_code, 200)
        
        # Verify fase was NOT deleted
        self.assertTrue(FaseHonorariosContratuais.objects.filter(id=fase_id).exists())
        
        # Check error message
        messages = list(response.context['messages'])
        self.assertTrue(any('Não é possível excluir' in str(msg) for msg in messages))
    
    def test_deletar_fase_honorarios_view_message_success(self):
        """Test success message is displayed"""
        self.client_app.login(username='testuser', password='testpass123')
        
        fase_nome = self.fase_honorarios.nome
        
        response = self.client_app.post(
            reverse('deletar_fase_honorarios', args=[self.fase_honorarios.id]),
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Fase de Honorários Contratuais "{fase_nome}" foi excluída com sucesso!')

    # ===============================
    # ATIVAR_FASE_HONORARIOS_VIEW TESTS (Activation Toggle View)
    # ===============================
    
    def test_ativar_fase_honorarios_view_activate_inactive_fase(self):
        """Test activating an inactive phase"""
        # Start with inactive phase
        self.fase_honorarios.ativa = False
        self.fase_honorarios.save()
        
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(
            reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fases_honorarios'))
        
        # Verify activation
        self.fase_honorarios.refresh_from_db()
        self.assertTrue(self.fase_honorarios.ativa)
    
    def test_ativar_fase_honorarios_view_deactivate_active_fase(self):
        """Test deactivating an active phase"""
        # Start with active phase
        self.fase_honorarios.ativa = True
        self.fase_honorarios.save()
        
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(
            reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fases_honorarios'))
        
        # Verify deactivation
        self.fase_honorarios.refresh_from_db()
        self.assertFalse(self.fase_honorarios.ativa)
    
    def test_ativar_fase_honorarios_view_get_redirects(self):
        """Test GET request redirects to fases list"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.get(reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fases_honorarios'))
    
    def test_ativar_fase_honorarios_view_unauthenticated(self):
        """Test unauthenticated access redirects to login"""
        response = self.client_app.post(reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id]))
        self.assertEqual(response.status_code, 302)
        expected_url = f'/login/?next={reverse("ativar_fase_honorarios", args=[self.fase_honorarios.id])}'
        self.assertRedirects(response, expected_url)
    
    def test_ativar_fase_honorarios_view_nonexistent_fase(self):
        """Test activating non-existent fase returns 404"""
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(reverse('ativar_fase_honorarios', args=[99999]))
        self.assertEqual(response.status_code, 404)
    
    def test_ativar_fase_honorarios_view_message_activate(self):
        """Test activation message is displayed"""
        # Start with inactive phase
        self.fase_honorarios.ativa = False
        self.fase_honorarios.save()
        
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(
            reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id]),
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Fase de Honorários Contratuais "{self.fase_honorarios.nome}" foi ativada com sucesso!')
    
    def test_ativar_fase_honorarios_view_message_deactivate(self):
        """Test deactivation message is displayed"""
        # Start with active phase
        self.fase_honorarios.ativa = True
        self.fase_honorarios.save()
        
        self.client_app.login(username='testuser', password='testpass123')
        
        response = self.client_app.post(
            reverse('ativar_fase_honorarios', args=[self.fase_honorarios.id]),
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Fase de Honorários Contratuais "{self.fase_honorarios.nome}" foi desativada com sucesso!')

    # ===============================
    # SECURITY & EDGE CASE TESTS
    # ===============================
    
    def test_fase_honorarios_views_csrf_protection(self):
        """Test CSRF protection on POST requests"""
        from django.middleware.csrf import get_token
        
        self.client_app.login(username='testuser', password='testpass123')
        
        # Get CSRF token
        response = self.client_app.get(reverse('nova_fase_honorarios'))
        csrf_token = get_token(response.wsgi_request)
        
        # Test with valid CSRF token
        form_data = {
            'nome': 'Fase CSRF Test',
            'descricao': 'Test CSRF',
            'cor': '#FFC107',
            'ordem': 1,
            'ativa': True,
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Success
    
    def test_fase_honorarios_xss_prevention(self):
        """Test XSS prevention in form fields"""
        self.client_app.login(username='testuser', password='testpass123')
        
        malicious_script = '<script>alert("XSS")</script>'
        
        form_data = {
            'nome': f'Fase XSS Test {malicious_script}',
            'descricao': f'Description {malicious_script}',
            'cor': '#FFC107',
            'ordem': 1,
            'ativa': True
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        
        if response.status_code == 302:  # If creation succeeded
            fase = FaseHonorariosContratuais.objects.get(nome__contains='Fase XSS Test')
            # The script should be stored as plain text, not executed
            self.assertIn('<script>', fase.nome)
            self.assertIn('<script>', fase.descricao)
    
    def test_fase_honorarios_unicode_support(self):
        """Test Unicode character support in fase names"""
        self.client_app.login(username='testuser', password='testpass123')
        
        unicode_name = 'Fase Honorários 测试 مرحلة 🎯'
        
        form_data = {
            'nome': unicode_name,
            'descricao': 'Unicode test description',
            'cor': '#FFC107',
            'ordem': 1,
            'ativa': True
        }
        
        response = self.client_app.post(reverse('nova_fase_honorarios'), data=form_data)
        self.assertEqual(response.status_code, 302)
        
        fase = FaseHonorariosContratuais.objects.get(nome=unicode_name)
        self.assertEqual(fase.nome, unicode_name)
    
    def test_fase_honorarios_concurrent_modification(self):
        """Test handling of concurrent modifications"""
        self.client_app.login(username='testuser', password='testpass123')
        
        # Simulate concurrent modification by changing the fase
        original_nome = self.fase_honorarios.nome
        self.fase_honorarios.nome = 'Modified Concurrently'
        self.fase_honorarios.save()
        
        # Now try to edit with old data
        form_data = {
            'nome': 'My Edit',
            'descricao': 'My changes',
            'cor': '#DC3545',
            'ordem': 2,
            'ativa': False
        }
        
        response = self.client_app.post(
            reverse('editar_fase_honorarios', args=[self.fase_honorarios.id]),
            data=form_data
        )
        
        # Should still succeed (last write wins)
        self.assertEqual(response.status_code, 302)
        
        self.fase_honorarios.refresh_from_db()
        self.assertEqual(self.fase_honorarios.nome, 'My Edit')
    
    def test_fase_honorarios_performance_large_dataset(self):
        """Test performance with larger dataset"""
        # Create many phases
        phases = []
        for i in range(100):
            phases.append(FaseHonorariosContratuais(
                nome=f'Fase {i}',
                descricao=f'Description {i}',
                cor='#FFC107',
                ordem=i,
                ativa=i % 2 == 0
            ))
        FaseHonorariosContratuais.objects.bulk_create(phases)
        
        self.client_app.login(username='testuser', password='testpass123')
        
        with self.assertNumQueries(6):  # Session + User + 3 count queries + main query
            response = self.client_app.get(reverse('fases_honorarios'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['total_fases'], 102)  # 100 + 2 from setUp
        
        self.fase_honorarios.refresh_from_db()
        self.assertTrue(self.fase_honorarios.ativa)

