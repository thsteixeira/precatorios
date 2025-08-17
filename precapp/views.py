from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .models import Precatorio, Cliente, Alvara, Requerimento, Fase
from .forms import (
    PrecatorioForm, ClienteForm, PrecatorioSearchForm, 
    ClienteSearchForm, RequerimentoForm, ClienteSimpleForm, 
    AlvaraSimpleForm, FaseForm
)

# Authentication Views
def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                # Redirect to next URL if provided, otherwise to home
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Credenciais inválidas.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.info(request, 'Você foi desconectado com sucesso.')
    return redirect('login')

# Create your views here.

@login_required
def home_view(request):
    """Home view with dashboard statistics"""
    from django.db.models import Sum, Count
    
    # Get counts for dashboard
    total_precatorios = Precatorio.objects.count()
    total_clientes = Cliente.objects.count()
    total_alvaras = Alvara.objects.count()
    total_requerimentos = Requerimento.objects.count()
    
    # Get financial statistics - using correct field names
    total_valor_precatorios = Precatorio.objects.aggregate(total=Sum('valor_de_face'))['total'] or 0
    total_valor_alvaras = Alvara.objects.aggregate(
        principal=Sum('valor_principal'),
        contratuais=Sum('honorarios_contratuais'),
        sucumbenciais=Sum('honorarios_sucumbenciais')
    )
    
    valor_alvaras = (
        (total_valor_alvaras['principal'] or 0) + 
        (total_valor_alvaras['contratuais'] or 0) + 
        (total_valor_alvaras['sucumbenciais'] or 0)
    )
    
    total_valor_requerimentos = Requerimento.objects.aggregate(total=Sum('valor'))['total'] or 0
    
    # Get recent activity
    recent_precatorios = Precatorio.objects.prefetch_related('clientes').order_by('cnj')[:5]
    recent_alvaras = Alvara.objects.select_related('cliente', 'precatorio').order_by('-id')[:5]
    recent_requerimentos = Requerimento.objects.select_related('cliente', 'precatorio').order_by('-id')[:5]
    
    context = {
        'total_precatorios': total_precatorios,
        'total_clientes': total_clientes,
        'total_alvaras': total_alvaras,
        'total_requerimentos': total_requerimentos,
        'total_valor_precatorios': total_valor_precatorios,
        'valor_alvaras': valor_alvaras,
        'total_valor_requerimentos': total_valor_requerimentos,
        'recent_precatorios': recent_precatorios,
        'recent_alvaras': recent_alvaras,
        'recent_requerimentos': recent_requerimentos,
    }
    
    return render(request, 'precapp/home.html', context)

@login_required
def novoPrec_view(request):
    """View to create a new Precatorio"""
    if request.method == 'POST':
        form = PrecatorioForm(request.POST)
        if form.is_valid():
            precatorio = form.save()
            messages.success(request, f'Precatório {precatorio.cnj} criado com sucesso!')
            return redirect('precatorios')  # Redirect to the list view after successful creation
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = PrecatorioForm()
    
    return render(request, 'precapp/novo_precatorio.html', {'form': form})
    

@login_required
def precatorio_view(request):
    """View to display all precatorios with filtering support"""
    precatorios = Precatorio.objects.all()
    
    # Apply filters based on GET parameters
    cnj_filter = request.GET.get('cnj', '').strip()
    origem_filter = request.GET.get('origem', '').strip()
    quitado_filter = request.GET.get('quitado', '')
    prioridade_filter = request.GET.get('prioridade', '')
    
    if cnj_filter:
        precatorios = precatorios.filter(cnj__icontains=cnj_filter)
    
    if origem_filter:
        precatorios = precatorios.filter(origem__icontains=origem_filter)
    
    if quitado_filter in ['true', 'false']:
        quitado_bool = quitado_filter == 'true'
        precatorios = precatorios.filter(quitado=quitado_bool)
    
    if prioridade_filter in ['true', 'false']:
        prioridade_bool = prioridade_filter == 'true'
        precatorios = precatorios.filter(prioridade_deferida=prioridade_bool)
    
    # Calculate summary statistics
    total_precatorios = precatorios.count()
    quitados = precatorios.filter(quitado=True).count()
    pendentes = precatorios.filter(quitado=False).count()
    prioritarios = precatorios.filter(prioridade_deferida=True).count()
    
    context = {
        'precatorios': precatorios,
        'total_precatorios': total_precatorios,
        'quitados': quitados,
        'pendentes': pendentes,
        'prioritarios': prioritarios,
        # Include current filter values to maintain state in form
        'current_cnj': cnj_filter,
        'current_origem': origem_filter,
        'current_quitado': quitado_filter,
        'current_prioridade': prioridade_filter,
    }
    
    return render(request, 'precapp/precatorio_list.html', context)

@login_required
def precatorio_detalhe_view(request, precatorio_cnj):
    """View to display and edit a single precatorio and manage client relationships"""
    precatorio = get_object_or_404(Precatorio, cnj=precatorio_cnj)
    
    # Get all clients associated with this precatorio via many-to-many relationship
    associated_clientes = precatorio.clientes.all().order_by('nome')
    
    # Get all alvarás associated with this precatorio
    alvaras = Alvara.objects.filter(precatorio=precatorio).select_related('cliente').order_by('-id')
    
    # Get all requerimentos associated with this precatorio
    requerimentos = Requerimento.objects.filter(precatorio=precatorio).select_related('cliente').order_by('-id')
    
    # Initialize forms
    precatorio_form = None
    client_search_form = ClienteSearchForm()
    requerimento_form = RequerimentoForm()
    cliente_form = ClienteSimpleForm()
    alvara_form = AlvaraSimpleForm()
    
    if request.method == 'POST':
        if 'edit_precatorio' in request.POST:
            # Handle precatorio editing
            precatorio_form = PrecatorioForm(request.POST, instance=precatorio)
            if precatorio_form.is_valid():
                precatorio_form.save()
                messages.success(request, f'Precatório {precatorio.cnj} atualizado com sucesso!')
                return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
        
        elif 'link_cliente' in request.POST:
            # Handle client linking
            client_search_form = ClienteSearchForm(request.POST)
            if client_search_form.is_valid():
                cpf = client_search_form.cleaned_data['cpf']
                try:
                    cliente = Cliente.objects.get(cpf=cpf)
                    if cliente in associated_clientes:
                        messages.warning(request, f'O cliente {cliente.nome} já está vinculado ao precatório {precatorio.cnj}.')
                    else:
                        # Add the client to the precatorio
                        precatorio.clientes.add(cliente)
                        messages.success(request, f'Cliente {cliente.nome} vinculado com sucesso ao precatório {precatorio.cnj}!')
                        return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
                except Cliente.DoesNotExist:
                    messages.error(request, f'Cliente com CPF {cpf} não encontrado. Verifique se o CPF está correto e se o cliente está cadastrado.')
            else:
                messages.error(request, 'Por favor, corrija os erros no CPF.')
        
        elif 'unlink_cliente' in request.POST:
            # Handle client unlinking
            cliente_cpf = request.POST.get('cliente_cpf')
            try:
                cliente = Cliente.objects.get(cpf=cliente_cpf)
                if cliente in associated_clientes:
                    precatorio.clientes.remove(cliente)
                    messages.success(request, f'Cliente {cliente.nome} desvinculado do precatório {precatorio.cnj}.')
                    return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
                else:
                    messages.error(request, 'Este cliente não está vinculado a este precatório.')
            except Cliente.DoesNotExist:
                                    messages.error(request, 'Cliente não encontrado.')
                    
        elif 'create_requerimento' in request.POST:
            # Handle requerimento creation
            requerimento_form = RequerimentoForm(request.POST)
            if requerimento_form.is_valid():
                cpf = requerimento_form.cleaned_data['cliente_cpf']
                # Remove dots and dashes, keep only numbers
                cpf_numbers = ''.join(filter(str.isdigit, cpf))
                try:
                    cliente = Cliente.objects.get(cpf=cpf_numbers)
                    # Create the requerimento
                    requerimento = requerimento_form.save(commit=False)
                    requerimento.precatorio = precatorio
                    requerimento.cliente = cliente
                    requerimento.save()
                    messages.success(request, f'Requerimento criado com sucesso para {cliente.nome}!')
                    return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
                except Cliente.DoesNotExist:
                    messages.error(request, f'Cliente com CPF {cpf} não encontrado. Verifique se o CPF está correto e se o cliente está cadastrado.')
            else:
                messages.error(request, 'Por favor, corrija os erros no formulário do requerimento.')
                
        elif 'create_cliente' in request.POST:
            # Handle client creation
            cliente_form = ClienteSimpleForm(request.POST)
            if cliente_form.is_valid():
                cliente = cliente_form.save()
                # Automatically link the new client to this precatorio
                precatorio.clientes.add(cliente)
                messages.success(request, f'Cliente {cliente.nome} criado e vinculado com sucesso ao precatório!')
                return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
            else:
                messages.error(request, 'Por favor, corrija os erros no formulário do cliente.')
                
        elif 'create_alvara' in request.POST:
            # Handle alvara creation
            alvara_form = AlvaraSimpleForm(request.POST)
            if alvara_form.is_valid():
                cpf = alvara_form.cleaned_data['cliente_cpf']
                # Remove dots and dashes, keep only numbers
                cpf_numbers = ''.join(filter(str.isdigit, cpf))
                try:
                    cliente = Cliente.objects.get(cpf=cpf_numbers)
                    # Create the alvara
                    alvara = alvara_form.save(commit=False)
                    alvara.precatorio = precatorio
                    alvara.cliente = cliente
                    alvara.save()
                    messages.success(request, f'Alvará criado com sucesso para {cliente.nome}!')
                    return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
                except Cliente.DoesNotExist:
                    messages.error(request, f'Cliente com CPF {cpf} não encontrado. Verifique se o CPF está correto e se o cliente está cadastrado.')
            else:
                messages.error(request, 'Por favor, corrija os erros no formulário do alvará.')
        
        elif 'update_alvara' in request.POST:
            # Handle alvara update
            alvara_id = request.POST.get('alvara_id')
            try:
                alvara = get_object_or_404(Alvara, id=alvara_id, precatorio=precatorio)
                # Update the alvara fields
                alvara.valor_principal = float(request.POST.get('valor_principal', alvara.valor_principal))
                alvara.honorarios_contratuais = float(request.POST.get('honorarios_contratuais', alvara.honorarios_contratuais))
                alvara.honorarios_sucumbenciais = float(request.POST.get('honorarios_sucumbenciais', alvara.honorarios_sucumbenciais))
                alvara.tipo = request.POST.get('tipo', alvara.tipo)
                
                # Handle fase field properly (ForeignKey)
                fase_id = request.POST.get('fase')
                if fase_id:
                    try:
                        fase = Fase.objects.get(id=fase_id)
                        alvara.fase = fase
                    except Fase.DoesNotExist:
                        messages.error(request, 'Fase selecionada não existe.')
                        return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
                else:
                    alvara.fase = None
                
                alvara.save()
                messages.success(request, f'Alvará do cliente {alvara.cliente.nome} atualizado com sucesso!')
                return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
            except Alvara.DoesNotExist:
                messages.error(request, 'Alvará não encontrado.')
            except (ValueError, TypeError) as e:
                messages.error(request, f'Erro nos dados fornecidos: {str(e)}')
            except Exception as e:
                messages.error(request, f'Erro inesperado: {str(e)}')
        
        elif 'delete_alvara' in request.POST:
            # Handle alvara deletion
            alvara_id = request.POST.get('alvara_id')
            try:
                alvara = get_object_or_404(Alvara, id=alvara_id, precatorio=precatorio)
                cliente_nome = alvara.cliente.nome
                alvara.delete()
                messages.success(request, f'Alvará do cliente {cliente_nome} excluído com sucesso!')
                return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
            except Alvara.DoesNotExist:
                messages.error(request, 'Alvará não encontrado.')
        
        elif 'update_requerimento' in request.POST:
            # Handle requerimento update
            requerimento_id = request.POST.get('requerimento_id')
            try:
                requerimento = get_object_or_404(Requerimento, id=requerimento_id, precatorio=precatorio)
                # Update the requerimento fields
                requerimento.valor = float(request.POST.get('valor', requerimento.valor))
                requerimento.desagio = float(request.POST.get('desagio', requerimento.desagio))
                requerimento.pedido = request.POST.get('pedido', requerimento.pedido)
                
                # Handle fase field properly (ForeignKey)
                fase_id = request.POST.get('fase')
                if fase_id:
                    try:
                        fase = Fase.objects.get(id=fase_id)
                        requerimento.fase = fase
                    except Fase.DoesNotExist:
                        messages.error(request, 'Fase selecionada não existe.')
                        return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
                else:
                    requerimento.fase = None
                
                requerimento.save()
                messages.success(request, f'Requerimento do cliente {requerimento.cliente.nome} atualizado com sucesso!')
                return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
            except Requerimento.DoesNotExist:
                messages.error(request, 'Requerimento não encontrado.')
            except (ValueError, TypeError) as e:
                messages.error(request, f'Erro nos dados fornecidos: {str(e)}')
            except Exception as e:
                messages.error(request, f'Erro inesperado: {str(e)}')
        
        elif 'delete_requerimento' in request.POST:
            # Handle requerimento deletion
            requerimento_id = request.POST.get('requerimento_id')
            try:
                requerimento = get_object_or_404(Requerimento, id=requerimento_id, precatorio=precatorio)
                cliente_nome = requerimento.cliente.nome
                requerimento.delete()
                messages.success(request, f'Requerimento do cliente {cliente_nome} excluído com sucesso!')
                return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
            except Requerimento.DoesNotExist:
                messages.error(request, 'Requerimento não encontrado.')
    else:
        # Initialize precatorio form for editing if requested
        if 'edit' in request.GET:
            precatorio_form = PrecatorioForm(instance=precatorio)
    
    context = {
        'precatorio': precatorio,
        'form': precatorio_form,
        'client_search_form': client_search_form,
        'cliente_form': cliente_form,
        'alvara_form': alvara_form,
        'requerimento_form': requerimento_form,
        'is_editing': request.method == 'POST' and 'edit_precatorio' in request.POST or 'edit' in request.GET,
        'clientes': associated_clientes,
        'associated_clientes': associated_clientes,
        'alvaras': alvaras,
        'requerimentos': requerimentos,
        'alvara_fases': Fase.get_fases_for_alvara(),
        'requerimento_fases': Fase.get_fases_for_requerimento(),
    }
    
    return render(request, 'precapp/precatorio_detail.html', context)


@login_required
def clientes_view(request):
    """View to display all clients with filtering support"""
    clientes = Cliente.objects.all().prefetch_related('precatorios')
    
    # Apply filters based on GET parameters
    nome_filter = request.GET.get('nome', '').strip()
    cpf_filter = request.GET.get('cpf', '').strip()
    prioridade_filter = request.GET.get('prioridade', '')
    precatorio_filter = request.GET.get('precatorio', '').strip()
    
    if nome_filter:
        clientes = clientes.filter(nome__icontains=nome_filter)
    
    if cpf_filter:
        clientes = clientes.filter(cpf__icontains=cpf_filter)
    
    if prioridade_filter in ['true', 'false']:
        prioridade_bool = prioridade_filter == 'true'
        clientes = clientes.filter(prioridade=prioridade_bool)
    
    if precatorio_filter:
        clientes = clientes.filter(precatorios__cnj__icontains=precatorio_filter).distinct()
    
    # Calculate summary statistics
    total_clientes = clientes.count()
    clientes_com_prioridade = clientes.filter(prioridade=True).count()
    clientes_sem_prioridade = clientes.filter(prioridade=False).count()
    
    context = {
        'clientes': clientes,
        'total_clientes': total_clientes,
        'clientes_com_prioridade': clientes_com_prioridade,
        'clientes_sem_prioridade': clientes_sem_prioridade,
        # Include current filter values to maintain state in form
        'current_nome': nome_filter,
        'current_cpf': cpf_filter,
        'current_prioridade': prioridade_filter,
        'current_precatorio': precatorio_filter,
    }
    
    return render(request, 'precapp/cliente_list.html', context)


@login_required
def cliente_detail_view(request, cpf):
    """View to display and edit a specific client and manage precatorio relationships"""
    cliente = get_object_or_404(Cliente, cpf=cpf)
    
    # Get all precatorios associated with this client
    associated_precatorios = cliente.precatorios.all().order_by('cnj')
    
    # Initialize forms
    client_form = None
    search_form = PrecatorioSearchForm()
    
    if request.method == 'POST':
        if 'edit_client' in request.POST:
            # Handle client editing
            client_form = ClienteForm(request.POST, instance=cliente)
            if client_form.is_valid():
                client_form.save()
                messages.success(request, f'Cliente {cliente.nome} atualizado com sucesso!')
                return redirect('cliente_detail', cpf=cliente.cpf)
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
        
        elif 'link_precatorio' in request.POST:
            # Handle precatorio linking
            search_form = PrecatorioSearchForm(request.POST)
            if search_form.is_valid():
                cnj = search_form.cleaned_data['cnj']
                try:
                    precatorio = Precatorio.objects.get(cnj=cnj)
                    if precatorio in associated_precatorios:
                        messages.warning(request, f'O cliente {cliente.nome} já está vinculado ao precatório {cnj}.')
                    else:
                        # Add the client to the precatorio
                        precatorio.clientes.add(cliente)
                        messages.success(request, f'Cliente {cliente.nome} vinculado com sucesso ao precatório {cnj}!')
                        return redirect('cliente_detail', cpf=cliente.cpf)
                except Precatorio.DoesNotExist:
                    messages.error(request, f'Precatório com CNJ {cnj} não encontrado. Verifique se o número está correto.')
            else:
                messages.error(request, 'Por favor, corrija os erros no CNJ.')
        
        elif 'unlink_precatorio' in request.POST:
            # Handle precatorio unlinking
            precatorio_cnj = request.POST.get('precatorio_cnj')
            try:
                precatorio = Precatorio.objects.get(cnj=precatorio_cnj)
                if precatorio in associated_precatorios:
                    precatorio.clientes.remove(cliente)
                    messages.success(request, f'Cliente {cliente.nome} desvinculado do precatório {precatorio.cnj}.')
                    return redirect('cliente_detail', cpf=cliente.cpf)
                else:
                    messages.error(request, 'Este cliente não está vinculado a este precatório.')
            except Precatorio.DoesNotExist:
                messages.error(request, 'Precatório não encontrado.')
    else:
        # Initialize client form for editing if requested
        if 'edit' in request.GET:
            client_form = ClienteForm(instance=cliente)
    
    context = {
        'cliente': cliente,
        'client_form': client_form,
        'search_form': search_form,
        'associated_precatorios': associated_precatorios,
        'is_editing': request.method == 'POST' and 'edit_client' in request.POST or 'edit' in request.GET,
    }
    
    return render(request, 'precapp/cliente_detail.html', context)


@login_required
def alvaras_view(request):
    """View to display all alvarás with filtering support"""
    alvaras = Alvara.objects.all().select_related('precatorio', 'cliente', 'fase').order_by('-id')
    
    # Get available fases for alvara
    available_fases = Fase.get_fases_for_alvara()
    
    # Apply filters based on GET parameters
    nome_filter = request.GET.get('nome', '').strip()
    precatorio_filter = request.GET.get('precatorio', '').strip()
    tipo_filter = request.GET.get('tipo', '').strip()
    fase_filter = request.GET.get('fase', '').strip()
    
    if nome_filter:
        alvaras = alvaras.filter(cliente__nome__icontains=nome_filter)
    
    if precatorio_filter:
        alvaras = alvaras.filter(precatorio__cnj__icontains=precatorio_filter)
    
    if tipo_filter:
        alvaras = alvaras.filter(tipo=tipo_filter)  # Exact match for dropdown
    
    if fase_filter:
        alvaras = alvaras.filter(fase__nome=fase_filter)  # Exact match for dropdown
    
    # Calculate summary statistics
    total_alvaras = alvaras.count()
    aguardando_deposito = alvaras.filter(tipo='aguardando depósito').count()
    deposito_judicial = alvaras.filter(tipo='depósito judicial').count()
    recebido_cliente = alvaras.filter(tipo='recebido pelo cliente').count()
    honorarios_recebidos = alvaras.filter(tipo='honorários recebidos').count()
    
    # Calculate total values
    total_valor_principal = sum([alvara.valor_principal for alvara in alvaras if alvara.valor_principal])
    total_honorarios_contratuais = sum([alvara.honorarios_contratuais for alvara in alvaras if alvara.honorarios_contratuais])
    total_honorarios_sucumbenciais = sum([alvara.honorarios_sucumbenciais for alvara in alvaras if alvara.honorarios_sucumbenciais])
    
    context = {
        'alvaras': alvaras,
        'total_alvaras': total_alvaras,
        'aguardando_deposito': aguardando_deposito,
        'deposito_judicial': deposito_judicial,
        'recebido_cliente': recebido_cliente,
        'honorarios_recebidos': honorarios_recebidos,
        'total_valor_principal': total_valor_principal,
        'total_honorarios_contratuais': total_honorarios_contratuais,
        'total_honorarios_sucumbenciais': total_honorarios_sucumbenciais,
        # Include current filter values to maintain state in form
        'current_nome': nome_filter,
        'current_precatorio': precatorio_filter,
        'current_tipo': tipo_filter,
        'current_fase': fase_filter,
        # Include available options for dropdowns
        'available_fases': available_fases,
    }
    
    return render(request, 'precapp/alvara_list.html', context)


@login_required
def delete_alvara_view(request, alvara_id):
    """View to delete a specific alvará"""
    alvara = get_object_or_404(Alvara, id=alvara_id)
    
    if request.method == 'POST':
        precatorio_cnj = alvara.precatorio.cnj
        cliente_nome = alvara.cliente.nome
        alvara.delete()
        messages.success(request, f'Alvará de {cliente_nome} foi excluído com sucesso!')
        return redirect('alvaras')
    
    # If GET request, redirect back to alvara detail
    return redirect('alvara_detail', alvara_id=alvara_id)


@login_required
def requerimento_list_view(request):
    """View to list all requerimentos with filtering"""
    requerimentos = Requerimento.objects.all().select_related('cliente', 'precatorio', 'fase').order_by('-id')
    
    # Get filter parameters
    cliente_filter = request.GET.get('cliente', '').strip()
    precatorio_filter = request.GET.get('precatorio', '').strip()
    pedido_filter = request.GET.get('pedido', '').strip()
    fase_filter = request.GET.get('fase', '').strip()
    
    # Apply filters
    if cliente_filter:
        requerimentos = requerimentos.filter(cliente__nome__icontains=cliente_filter)
    
    if precatorio_filter:
        requerimentos = requerimentos.filter(precatorio__cnj__icontains=precatorio_filter)
    
    if pedido_filter:
        requerimentos = requerimentos.filter(pedido=pedido_filter)
    
    if fase_filter:
        requerimentos = requerimentos.filter(fase__nome=fase_filter)
    
    # Get available phases for requerimentos
    from .models import Fase
    available_fases = Fase.get_fases_for_requerimento()
    
    # Calculate financial statistics based on filtered results
    valor_total = sum(r.valor for r in requerimentos if r.valor)
    desagio_medio = sum(r.desagio for r in requerimentos if r.desagio) / requerimentos.count() if requerimentos.count() > 0 else 0
    
    # Handle requerimento deletion
    if request.method == 'POST' and 'delete_requerimento' in request.POST:
        requerimento_id = request.POST.get('requerimento_id')
        try:
            requerimento = Requerimento.objects.get(id=requerimento_id)
            cliente_nome = requerimento.cliente.nome
            requerimento.delete()
            messages.success(request, f'Requerimento de {cliente_nome} foi excluído com sucesso!')
            return redirect('requerimentos')
        except Requerimento.DoesNotExist:
            messages.error(request, 'Requerimento não encontrado.')
    
    context = {
        'requerimentos': requerimentos,
        'available_fases': available_fases,
        'valor_total': valor_total,
        'desagio_medio': desagio_medio,
        # Current filter values for form persistence
        'current_cliente': cliente_filter,
        'current_precatorio': precatorio_filter,
        'current_pedido': pedido_filter,
        'current_fase': fase_filter,
    }
    return render(request, 'precapp/requerimento_list.html', context)


@login_required
def novo_cliente_view(request):
    """View to create a new client"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente {cliente.nome} foi criado com sucesso!')
            return redirect('cliente_detail', cpf=cliente.cpf)
    else:
        form = ClienteForm()
    
    context = {
        'form': form,
    }
    return render(request, 'precapp/novo_cliente.html', context)


@login_required
def delete_cliente_view(request, cpf):
    """View to delete a client"""
    cliente = get_object_or_404(Cliente, cpf=cpf)
    
    if request.method == 'POST':
        cliente_nome = cliente.nome
        
        # Check if cliente has associated precatorios
        if cliente.precatorios.exists():
            messages.error(request, f'Não é possível excluir o cliente {cliente_nome} pois ele está associado a precatórios. Remova as associações primeiro.')
            return redirect('cliente_detail', cpf=cpf)
        
        # Check if cliente has associated alvaras
        if hasattr(cliente, 'alvara_set') and cliente.alvara_set.exists():
            messages.error(request, f'Não é possível excluir o cliente {cliente_nome} pois ele possui alvarás associados. Remova os alvarás primeiro.')
            return redirect('cliente_detail', cpf=cpf)
        
        # Check if cliente has associated requerimentos
        if hasattr(cliente, 'requerimento_set') and cliente.requerimento_set.exists():
            messages.error(request, f'Não é possível excluir o cliente {cliente_nome} pois ele possui requerimentos associados. Remova os requerimentos primeiro.')
            return redirect('cliente_detail', cpf=cpf)
        
        cliente.delete()
        messages.success(request, f'Cliente {cliente_nome} foi excluído com sucesso!')
        return redirect('clientes')
    
    # If not POST, redirect to client detail
    return redirect('cliente_detail', cpf=cpf)


@login_required
def delete_precatorio_view(request, precatorio_cnj):
    """View to delete a precatório"""
    precatorio = get_object_or_404(Precatorio, cnj=precatorio_cnj)
    
    if request.method == 'POST':
        precatorio_cnj_display = precatorio.cnj
        
        # Check if precatorio has associated clientes
        if precatorio.clientes.exists():
            messages.error(request, f'Não é possível excluir o precatório {precatorio_cnj_display} pois ele possui clientes associados. Remova as associações primeiro.')
            return redirect('precatorio_detalhe', precatorio_cnj=precatorio_cnj)
        
        # Check if precatorio has associated alvaras
        if hasattr(precatorio, 'alvara_set') and precatorio.alvara_set.exists():
            messages.error(request, f'Não é possível excluir o precatório {precatorio_cnj_display} pois ele possui alvarás associados. Remova os alvarás primeiro.')
            return redirect('precatorio_detalhe', precatorio_cnj=precatorio_cnj)
        
        # Check if precatorio has associated requerimentos
        if hasattr(precatorio, 'requerimento_set') and precatorio.requerimento_set.exists():
            messages.error(request, f'Não é possível excluir o precatório {precatorio_cnj_display} pois ele possui requerimentos associados. Remova os requerimentos primeiro.')
            return redirect('precatorio_detalhe', precatorio_cnj=precatorio_cnj)
        
        precatorio.delete()
        messages.success(request, f'Precatório {precatorio_cnj_display} foi excluído com sucesso!')
        return redirect('precatorios')
    
    # If not POST, redirect to precatorio detail
    return redirect('precatorio_detalhe', precatorio_cnj=precatorio_cnj)


# ===============================
# FASE MANAGEMENT VIEWS
# ===============================

@login_required
def fases_view(request):
    """View to list all phases"""
    fases = Fase.objects.all().order_by('nome')
    
    # Statistics
    total_fases = fases.count()
    fases_ativas = fases.filter(ativa=True).count()
    fases_inativas = fases.filter(ativa=False).count()
    
    context = {
        'fases': fases,
        'total_fases': total_fases,
        'fases_ativas': fases_ativas,
        'fases_inativas': fases_inativas,
    }
    
    return render(request, 'precapp/fases_list.html', context)


@login_required
def nova_fase_view(request):
    """View to create a new phase"""
    if request.method == 'POST':
        form = FaseForm(request.POST)
        if form.is_valid():
            fase = form.save()
            messages.success(request, f'Fase "{fase.nome}" criada com sucesso!')
            return redirect('fases')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = FaseForm()
    
    context = {
        'form': form,
        'title': 'Nova Fase',
        'submit_text': 'Criar Fase'
    }
    return render(request, 'precapp/fase_form.html', context)


@login_required
def editar_fase_view(request, fase_id):
    """View to edit an existing phase"""
    fase = get_object_or_404(Fase, id=fase_id)
    
    if request.method == 'POST':
        form = FaseForm(request.POST, instance=fase)
        if form.is_valid():
            fase = form.save()
            messages.success(request, f'Fase "{fase.nome}" atualizada com sucesso!')
            return redirect('fases')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = FaseForm(instance=fase)
    
    context = {
        'form': form,
        'fase': fase,
        'title': f'Editar Fase: {fase.nome}',
        'submit_text': 'Salvar Alterações'
    }
    return render(request, 'precapp/fase_form.html', context)


@login_required
def deletar_fase_view(request, fase_id):
    """View to delete a phase"""
    fase = get_object_or_404(Fase, id=fase_id)
    
    if request.method == 'POST':
        fase_nome = fase.nome
        
        # Check if fase is being used by any alvara
        alvaras_using_fase = Alvara.objects.filter(fase=fase)
        if alvaras_using_fase.exists():
            messages.error(
                request, 
                f'Não é possível excluir a fase "{fase_nome}" pois ela está sendo usada por {alvaras_using_fase.count()} alvará(s). '
                'Altere a fase desses alvarás primeiro.'
            )
            return redirect('fases')
        
        # Check if fase is being used by any requerimento
        requerimentos_using_fase = Requerimento.objects.filter(fase=fase)
        if requerimentos_using_fase.exists():
            messages.error(
                request, 
                f'Não é possível excluir a fase "{fase_nome}" pois ela está sendo usada por {requerimentos_using_fase.count()} requerimento(s). '
                'Altere a fase desses requerimentos primeiro.'
            )
            return redirect('fases')
        
        fase.delete()
        messages.success(request, f'Fase "{fase_nome}" foi excluída com sucesso!')
        return redirect('fases')
    
    # If not POST, redirect to fases list
    return redirect('fases')


@login_required
def ativar_fase_view(request, fase_id):
    """View to activate/deactivate a phase"""
    fase = get_object_or_404(Fase, id=fase_id)
    
    if request.method == 'POST':
        fase.ativa = not fase.ativa
        fase.save()
        
        status_text = "ativada" if fase.ativa else "desativada"
        messages.success(request, f'Fase "{fase.nome}" foi {status_text} com sucesso!')
    
    return redirect('fases')

