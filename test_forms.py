#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'precatorios.settings')
django.setup()

from precapp.forms import AlvaraForm, AlvaraSimpleForm, RequerimentoForm
from precapp.models import Fase

def test_form_querysets():
    print('=== TESTING FORM QUERYSETS ===')

    # Test AlvaraForm
    alvara_form = AlvaraForm()
    alvara_fases = alvara_form.fields['fase'].queryset
    print(f'AlvaraForm fase options ({len(alvara_fases)} total):')
    for fase in alvara_fases:
        print(f'  - {fase.nome} ({fase.tipo})')

    print()

    # Test AlvaraSimpleForm  
    alvara_simple_form = AlvaraSimpleForm()
    alvara_simple_fases = alvara_simple_form.fields['fase'].queryset
    print(f'AlvaraSimpleForm fase options ({len(alvara_simple_fases)} total):')
    for fase in alvara_simple_fases:
        print(f'  - {fase.nome} ({fase.tipo})')

    print()

    # Test RequerimentoForm
    req_form = RequerimentoForm()
    req_fases = req_form.fields['fase'].queryset
    print(f'RequerimentoForm fase options ({len(req_fases)} total):')
    for fase in req_fases:
        print(f'  - {fase.nome} ({fase.tipo})')

    print('\n=== VERIFICATION ===')
    alvara_count = len(alvara_fases)
    req_count = len(req_fases)
    
    print(f'✓ AlvaraForm has {alvara_count} fase options (expected: 6)')
    print(f'✓ RequerimentoForm has {req_count} fase options (expected: 7)')
    
    # Check if filtering is working
    if alvara_count == 6 and req_count == 7:
        print('✓ SUCCESS: Forms are properly filtering phases by tipo!')
    else:
        print('✗ ERROR: Form filtering is not working correctly!')
    
    return alvara_count == 6 and req_count == 7

if __name__ == '__main__':
    test_form_querysets()
