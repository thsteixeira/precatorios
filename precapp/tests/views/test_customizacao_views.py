from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from datetime import datetime, timedelta

from precapp.models import Fase, FaseHonorariosContratuais, TipoDiligencia


class CustomizacaoViewTest(TestCase):
    """Comprehensive test cases for Customização dashboard view"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test data for Fases Principais
        self.fase_ativa_1 = Fase.objects.create(
            nome='Fase Ativa 1', 
            tipo='alvara', 
            cor='#FF0000', 
            ativa=True
        )
        self.fase_ativa_2 = Fase.objects.create(
            nome='Fase Ativa 2', 
            tipo='requerimento', 
            cor='#00FF00', 
            ativa=True
        )
        self.fase_inativa = Fase.objects.create(
            nome='Fase Inativa', 
            tipo='alvara', 
            cor='#0000FF', 
            ativa=False
        )
        
        # Create test data for Fases Honorários
        self.honorario_ativo_1 = FaseHonorariosContratuais.objects.create(
            nome='Honorários Ativo 1', 
            cor='#FFFF00', 
            ativa=True
        )
        self.honorario_ativo_2 = FaseHonorariosContratuais.objects.create(
            nome='Honorários Ativo 2', 
            cor='#FF00FF', 
            ativa=True
        )
        self.honorario_inativo = FaseHonorariosContratuais.objects.create(
            nome='Honorários Inativo', 
            cor='#00FFFF', 
            ativa=False
        )
        
        # Create test data for Tipos Diligência
        self.tipo_ativo_1 = TipoDiligencia.objects.create(
            nome='Tipo Ativo 1',
            descricao='Tipo ativo 1',
            cor='#123456',
            ativo=True,
            ordem=1
        )
        self.tipo_ativo_2 = TipoDiligencia.objects.create(
            nome='Tipo Ativo 2',
            descricao='Tipo ativo 2',
            cor='#654321',
            ativo=True,
            ordem=2
        )
        self.tipo_inativo = TipoDiligencia.objects.create(
            nome='Tipo Inativo',
            descricao='Tipo inativo',
            cor='#ABCDEF',
            ativo=False,
            ordem=3
        )
        
        self.client_app = Client()

    # ==================== AUTHENTICATION TESTS ====================
    
    def test_customizacao_view_authentication_required(self):
        """Test that customização view requires authentication"""
        response = self.client_app.get(reverse('customizacao'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)
    
    def test_customizacao_view_authenticated_access(self):
        """Test authenticated access to customização view"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Customização')
        self.assertTemplateUsed(response, 'precapp/customizacao.html')

    # ==================== STATISTICS TESTING - FASES PRINCIPAIS ====================
    
    def test_fases_principais_statistics(self):
        """Test fases principais statistics calculation"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_principais'], 3)
        self.assertEqual(context['fases_principais_ativas'], 2)
        self.assertEqual(context['fases_principais_inativas'], 1)
    
    def test_fases_principais_empty_state(self):
        """Test fases principais statistics with no data"""
        Fase.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_principais'], 0)
        self.assertEqual(context['fases_principais_ativas'], 0)
        self.assertEqual(context['fases_principais_inativas'], 0)
    
    def test_fases_principais_all_active(self):
        """Test fases principais statistics when all are active"""
        Fase.objects.filter(ativa=False).update(ativa=True)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_principais'], 3)
        self.assertEqual(context['fases_principais_ativas'], 3)
        self.assertEqual(context['fases_principais_inativas'], 0)
    
    def test_fases_principais_all_inactive(self):
        """Test fases principais statistics when all are inactive"""
        Fase.objects.filter(ativa=True).update(ativa=False)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_principais'], 3)
        self.assertEqual(context['fases_principais_ativas'], 0)
        self.assertEqual(context['fases_principais_inativas'], 3)

    # ==================== STATISTICS TESTING - FASES HONORÁRIOS ====================
    
    def test_fases_honorarios_statistics(self):
        """Test fases honorários statistics calculation"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_honorarios'], 3)
        self.assertEqual(context['fases_honorarios_ativas'], 2)
        self.assertEqual(context['fases_honorarios_inativas'], 1)
    
    def test_fases_honorarios_empty_state(self):
        """Test fases honorários statistics with no data"""
        FaseHonorariosContratuais.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_honorarios'], 0)
        self.assertEqual(context['fases_honorarios_ativas'], 0)
        self.assertEqual(context['fases_honorarios_inativas'], 0)
    
    def test_fases_honorarios_all_active(self):
        """Test fases honorários statistics when all are active"""
        FaseHonorariosContratuais.objects.filter(ativa=False).update(ativa=True)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_honorarios'], 3)
        self.assertEqual(context['fases_honorarios_ativas'], 3)
        self.assertEqual(context['fases_honorarios_inativas'], 0)
    
    def test_fases_honorarios_all_inactive(self):
        """Test fases honorários statistics when all are inactive"""
        FaseHonorariosContratuais.objects.filter(ativa=True).update(ativa=False)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_honorarios'], 3)
        self.assertEqual(context['fases_honorarios_ativas'], 0)
        self.assertEqual(context['fases_honorarios_inativas'], 3)

    # ==================== STATISTICS TESTING - TIPOS DILIGÊNCIA ====================
    
    def test_tipos_diligencia_statistics(self):
        """Test tipos diligência statistics calculation"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_tipos_diligencia'], 3)
        self.assertEqual(context['tipos_diligencia_ativos'], 2)
        self.assertEqual(context['tipos_diligencia_inativos'], 1)
    
    def test_tipos_diligencia_empty_state(self):
        """Test tipos diligência statistics with no data"""
        TipoDiligencia.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_tipos_diligencia'], 0)
        self.assertEqual(context['tipos_diligencia_ativos'], 0)
        self.assertEqual(context['tipos_diligencia_inativos'], 0)
    
    def test_tipos_diligencia_all_active(self):
        """Test tipos diligência statistics when all are active"""
        TipoDiligencia.objects.filter(ativo=False).update(ativo=True)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_tipos_diligencia'], 3)
        self.assertEqual(context['tipos_diligencia_ativos'], 3)
        self.assertEqual(context['tipos_diligencia_inativos'], 0)
    
    def test_tipos_diligencia_all_inactive(self):
        """Test tipos diligência statistics when all are inactive"""
        TipoDiligencia.objects.filter(ativo=True).update(ativo=False)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_tipos_diligencia'], 3)
        self.assertEqual(context['tipos_diligencia_ativos'], 0)
        self.assertEqual(context['tipos_diligencia_inativos'], 3)

    # ==================== RECENT ITEMS TESTING ====================
    
    def test_recent_fases_principais(self):
        """Test recent fases principais inclusion and ordering"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertIn('recent_fases_principais', context)
        recent_fases = context['recent_fases_principais']
        
        # Should have all 3 fases (less than 5 limit)
        self.assertEqual(len(recent_fases), 3)
        
        # Should be ordered by criado_em descending (most recent first)
        self.assertTrue(recent_fases[0].criado_em >= recent_fases[1].criado_em)
        self.assertTrue(recent_fases[1].criado_em >= recent_fases[2].criado_em)
    
    def test_recent_fases_honorarios(self):
        """Test recent fases honorários inclusion and ordering"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertIn('recent_fases_honorarios', context)
        recent_honorarios = context['recent_fases_honorarios']
        
        # Should have all 3 honorários (less than 5 limit)
        self.assertEqual(len(recent_honorarios), 3)
        
        # Should be ordered by criado_em descending (most recent first)
        self.assertTrue(recent_honorarios[0].criado_em >= recent_honorarios[1].criado_em)
        self.assertTrue(recent_honorarios[1].criado_em >= recent_honorarios[2].criado_em)
    
    def test_recent_tipos_diligencia(self):
        """Test recent tipos diligência inclusion and ordering"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertIn('recent_tipos_diligencia', context)
        recent_tipos = context['recent_tipos_diligencia']
        
        # Should have all 3 tipos (less than 5 limit)
        self.assertEqual(len(recent_tipos), 3)
        
        # Should be ordered by criado_em descending (most recent first)
        self.assertTrue(recent_tipos[0].criado_em >= recent_tipos[1].criado_em)
        self.assertTrue(recent_tipos[1].criado_em >= recent_tipos[2].criado_em)
    
    def test_recent_items_limit_enforcement(self):
        """Test that recent items are limited to 5 items each"""
        # Create additional items to test the 5-item limit
        for i in range(10):
            Fase.objects.create(
                nome=f'Extra Fase {i}',
                tipo='alvara',
                cor='#FFFFFF',
                ativa=True
            )
            FaseHonorariosContratuais.objects.create(
                nome=f'Extra Honorário {i}',
                cor='#FFFFFF',
                ativa=True
            )
            TipoDiligencia.objects.create(
                nome=f'Extra Tipo {i}',
                descricao=f'Extra tipo {i}',
                cor='#FFFFFF',
                ativo=True,
                ordem=10+i
            )
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        # Each recent list should be limited to 5 items
        self.assertEqual(len(context['recent_fases_principais']), 5)
        self.assertEqual(len(context['recent_fases_honorarios']), 5)
        self.assertEqual(len(context['recent_tipos_diligencia']), 5)
    
    def test_recent_items_empty_state(self):
        """Test recent items when no data exists"""
        Fase.objects.all().delete()
        FaseHonorariosContratuais.objects.all().delete()
        TipoDiligencia.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(len(context['recent_fases_principais']), 0)
        self.assertEqual(len(context['recent_fases_honorarios']), 0)
        self.assertEqual(len(context['recent_tipos_diligencia']), 0)

    # ==================== COMPREHENSIVE CONTEXT VALIDATION ====================
    
    def test_complete_context_data(self):
        """Test that all expected context variables are present"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        
        # Fases Principais context
        self.assertIn('total_fases_principais', context)
        self.assertIn('fases_principais_ativas', context)
        self.assertIn('fases_principais_inativas', context)
        self.assertIn('recent_fases_principais', context)
        
        # Fases Honorários context
        self.assertIn('total_fases_honorarios', context)
        self.assertIn('fases_honorarios_ativas', context)
        self.assertIn('fases_honorarios_inativas', context)
        self.assertIn('recent_fases_honorarios', context)
        
        # Tipos Diligência context
        self.assertIn('total_tipos_diligencia', context)
        self.assertIn('tipos_diligencia_ativos', context)
        self.assertIn('tipos_diligencia_inativos', context)
        self.assertIn('recent_tipos_diligencia', context)
    
    def test_context_data_types(self):
        """Test that context data has correct types"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        
        # Statistics should be integers
        self.assertIsInstance(context['total_fases_principais'], int)
        self.assertIsInstance(context['fases_principais_ativas'], int)
        self.assertIsInstance(context['fases_principais_inativas'], int)
        self.assertIsInstance(context['total_fases_honorarios'], int)
        self.assertIsInstance(context['fases_honorarios_ativas'], int)
        self.assertIsInstance(context['fases_honorarios_inativas'], int)
        self.assertIsInstance(context['total_tipos_diligencia'], int)
        self.assertIsInstance(context['tipos_diligencia_ativos'], int)
        self.assertIsInstance(context['tipos_diligencia_inativos'], int)
        
        # Recent items should be querysets
        self.assertTrue(hasattr(context['recent_fases_principais'], '__iter__'))
        self.assertTrue(hasattr(context['recent_fases_honorarios'], '__iter__'))
        self.assertTrue(hasattr(context['recent_tipos_diligencia'], '__iter__'))

    # ==================== PERFORMANCE AND STRESS TESTING ====================
    
    def test_performance_with_large_dataset(self):
        """Test customização view performance with large dataset"""
        # Create large numbers of each type
        fases_batch = []
        honorarios_batch = []
        tipos_batch = []
        
        for i in range(100):
            fases_batch.append(Fase(
                nome=f'Bulk Fase {i}',
                tipo='alvara',
                cor='#FFFFFF',
                ativa=i % 2 == 0
            ))
            honorarios_batch.append(FaseHonorariosContratuais(
                nome=f'Bulk Honorário {i}',
                cor='#FFFFFF',
                ativa=i % 2 == 0
            ))
            tipos_batch.append(TipoDiligencia(
                nome=f'Bulk Tipo {i}',
                descricao=f'Bulk tipo {i}',
                cor='#FFFFFF',
                ativo=i % 2 == 0,
                ordem=100+i
            ))
        
        Fase.objects.bulk_create(fases_batch)
        FaseHonorariosContratuais.objects.bulk_create(honorarios_batch)
        TipoDiligencia.objects.bulk_create(tipos_batch)
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        
        # Verify statistics calculation with large dataset
        self.assertEqual(context['total_fases_principais'], 103)  # 100 + 3 from setUp
        self.assertEqual(context['fases_principais_ativas'], 52)  # 50 + 2 from setUp
        self.assertEqual(context['fases_principais_inativas'], 51)  # 50 + 1 from setUp
        
        self.assertEqual(context['total_fases_honorarios'], 103)  # 100 + 3 from setUp
        self.assertEqual(context['fases_honorarios_ativas'], 52)  # 50 + 2 from setUp
        self.assertEqual(context['fases_honorarios_inativas'], 51)  # 50 + 1 from setUp
        
        self.assertEqual(context['total_tipos_diligencia'], 103)  # 100 + 3 from setUp
        self.assertEqual(context['tipos_diligencia_ativos'], 52)  # 50 + 2 from setUp
        self.assertEqual(context['tipos_diligencia_inativos'], 51)  # 50 + 1 from setUp
        
        # Verify recent items are still limited to 5
        self.assertEqual(len(context['recent_fases_principais']), 5)
        self.assertEqual(len(context['recent_fases_honorarios']), 5)
        self.assertEqual(len(context['recent_tipos_diligencia']), 5)

    # ==================== EDGE CASES AND ERROR HANDLING ====================
    
    def test_mixed_data_scenarios(self):
        """Test various mixed data scenarios"""
        # Scenario 1: Only fases principais exist
        FaseHonorariosContratuais.objects.all().delete()
        TipoDiligencia.objects.all().delete()
        
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        self.assertEqual(context['total_fases_principais'], 3)
        self.assertEqual(context['total_fases_honorarios'], 0)
        self.assertEqual(context['total_tipos_diligencia'], 0)
        
        # Recreate data for next scenario
        self.honorario_ativo_1 = FaseHonorariosContratuais.objects.create(
            nome='Honorários Ativo 1', 
            cor='#FFFF00', 
            ativa=True
        )
        self.honorario_ativo_2 = FaseHonorariosContratuais.objects.create(
            nome='Honorários Ativo 2', 
            cor='#FF00FF', 
            ativa=True
        )
        self.honorario_inativo = FaseHonorariosContratuais.objects.create(
            nome='Honorários Inativo', 
            cor='#00FFFF', 
            ativa=False
        )
        
        # Scenario 2: Only honorários exist
        Fase.objects.all().delete()
        
        response = self.client_app.get(reverse('customizacao'))
        context = response.context
        self.assertEqual(context['total_fases_principais'], 0)
        self.assertEqual(context['total_fases_honorarios'], 3)
        self.assertEqual(context['total_tipos_diligencia'], 0)
    
    def test_data_consistency_validation(self):
        """Test data consistency in statistics"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        context = response.context
        
        # Verify that active + inactive = total for each category
        self.assertEqual(
            context['fases_principais_ativas'] + context['fases_principais_inativas'],
            context['total_fases_principais']
        )
        self.assertEqual(
            context['fases_honorarios_ativas'] + context['fases_honorarios_inativas'],
            context['total_fases_honorarios']
        )
        self.assertEqual(
            context['tipos_diligencia_ativos'] + context['tipos_diligencia_inativos'],
            context['total_tipos_diligencia']
        )
    
    def test_template_rendering_with_context(self):
        """Test that template renders correctly with all context data"""
        self.client_app.login(username='testuser', password='testpass123')
        response = self.client_app.get(reverse('customizacao'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'precapp/customizacao.html')
        
        # Check that key statistics appear in rendered content
        content = response.content.decode()
        self.assertIn('Fases Principais', content)
        self.assertIn('Fases Honorários', content)
        self.assertIn('Tipos de Diligência', content)
