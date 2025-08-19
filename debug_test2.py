#!/usr/bin/env python
"""Debug script to test diligencia marking - corrected version"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'precatorios.settings')
django.setup()

from django.contrib.auth.models import User
from precapp.models import Cliente, TipoDiligencia, Diligencias
from precapp.forms import DiligenciasUpdateForm
from datetime import date, timedelta

# Create test data
user = User.objects.create_user(username='testuser', password='testpass123')

cliente = Cliente.objects.create(
    cpf='12345678909',
    nome='João Silva',
    nascimento=date(1980, 5, 15),
    prioridade=False
)

tipo_diligencia = TipoDiligencia.objects.create(
    nome='Documentação',
    cor='#007bff'
)

diligencia = Diligencias.objects.create(
    cliente=cliente,
    tipo=tipo_diligencia,
    data_final=date.today() + timedelta(days=7),
    criado_por='Test User',
    urgencia='alta'
)

print(f"Initial state:")
print(f"  concluida: {diligencia.concluida}")
print(f"  concluido_por: {diligencia.concluido_por}")

# Test form with our data
form_data = {
    'concluida': True,
    'descricao': 'Concluída com sucesso'
}

print(f"\nTesting form with data: {form_data}")
form = DiligenciasUpdateForm(data=form_data, instance=diligencia)
print(f"Form is valid: {form.is_valid()}")

if form.is_valid():
    # Save the original state BEFORE calling form.save(commit=False)
    # But the form might have already changed the instance during is_valid()
    # So we need to get the original state from the database
    original_diligencia = Diligencias.objects.get(id=diligencia.id)
    was_completed_before = original_diligencia.concluida
    print(f"was_completed_before (from DB): {was_completed_before}")
    
    updated_diligencia = form.save(commit=False)
    print(f"\nAfter form.save(commit=False):")
    print(f"  diligencia is updated_diligencia: {diligencia is updated_diligencia}")
    print(f"  diligencia.concluida: {diligencia.concluida}")
    print(f"  updated_diligencia.concluida: {updated_diligencia.concluida}")
    print(f"  updated_diligencia.concluido_por: {updated_diligencia.concluido_por}")
    
    # Use the CORRECTED logic
    if updated_diligencia.concluida:
        # If marking as completed, set the current user as completer
        if not was_completed_before:  # Use saved state from DB
            print(f"Setting concluido_por to user: {user.get_full_name() or user.username}")
            updated_diligencia.concluido_por = user.get_full_name() or user.username
        else:
            print("Diligencia was already completed, not setting concluido_por")
    else:
        # If marking as not completed (reopening), clear the completer
        updated_diligencia.concluido_por = None
        
    print(f"\nAfter corrected logic:")
    print(f"  updated_diligencia.concluido_por: {updated_diligencia.concluido_por}")
    
    updated_diligencia.save()
    
    print(f"\nAfter save:")
    print(f"  diligencia.concluida: {updated_diligencia.concluida}")
    print(f"  diligencia.concluido_por: {updated_diligencia.concluido_por}")
    
else:
    print(f"Form errors: {form.errors}")

print("\nCleaning up...")
diligencia.delete()
tipo_diligencia.delete() 
cliente.delete()
user.delete()
print("Done!")
