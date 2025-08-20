from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from .models import Precatorio, Cliente, Alvara, Requerimento, Fase, FaseHonorariosContratuais, TipoDiligencia, Diligencias
from .forms import (
    PrecatorioForm, ClienteForm, PrecatorioSearchForm, 
    ClienteSearchForm, RequerimentoForm, ClienteSimpleForm, 
    AlvaraSimpleForm, FaseForm, FaseHonorariosContratuaisForm, TipoDiligenciaForm,
    DiligenciasForm, DiligenciasUpdateForm
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
    total_diligencias = Diligencias.objects.count()
    total_tipos_diligencia = TipoDiligencia.objects.filter(ativo=True).count()
    
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
    
    # Get diligencias statistics
    diligencias_pendentes = Diligencias.objects.filter(concluida=False).count()
    diligencias_concluidas = Diligencias.objects.filter(concluida=True).count()
    diligencias_atrasadas = Diligencias.objects.filter(
        concluida=False,
        data_final__lt=timezone.now().date()
    ).count()
    diligencias_urgentes = Diligencias.objects.filter(
        concluida=False,
        urgencia='alta'
    ).count()
    
    # Get recent activity
    recent_precatorios = Precatorio.objects.prefetch_related('clientes').order_by('cnj')[:5]
    recent_alvaras = Alvara.objects.select_related('cliente', 'precatorio').order_by('-id')[:5]
    recent_requerimentos = Requerimento.objects.select_related('cliente', 'precatorio').order_by('-id')[:5]
    recent_diligencias = Diligencias.objects.select_related('cliente', 'tipo').order_by('-data_criacao')[:5]
    
    context = {
        'total_precatorios': total_precatorios,
        'total_clientes': total_clientes,
        'total_alvaras': total_alvaras,
        'total_requerimentos': total_requerimentos,
        'total_diligencias': total_diligencias,
        'total_tipos_diligencia': total_tipos_diligencia,
        'total_valor_precatorios': total_valor_precatorios,
        'valor_alvaras': valor_alvaras,
        'total_valor_requerimentos': total_valor_requerimentos,
        'diligencias_pendentes': diligencias_pendentes,
        'diligencias_concluidas': diligencias_concluidas,
        'diligencias_atrasadas': diligencias_atrasadas,
        'diligencias_urgentes': diligencias_urgentes,
        'recent_precatorios': recent_precatorios,
        'recent_alvaras': recent_alvaras,
        'recent_requerimentos': recent_requerimentos,
        'recent_diligencias': recent_diligencias,
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
    precatorios = Precatorio.objects.all().prefetch_related('requerimento_set', 'requerimento_set__fase')
    
    # Apply filters based on GET parameters
    cnj_filter = request.GET.get('cnj', '').strip()
    origem_filter = request.GET.get('origem', '').strip()
    credito_principal_filter = request.GET.get('credito_principal', '')
    honorarios_contratuais_filter = request.GET.get('honorarios_contratuais', '')
    honorarios_sucumbenciais_filter = request.GET.get('honorarios_sucumbenciais', '')
    tipo_requerimento_filter = request.GET.get('tipo_requerimento', '')
    requerimento_deferido_filter = request.GET.get('requerimento_deferido', '')
    
    if cnj_filter:
        precatorios = precatorios.filter(cnj__icontains=cnj_filter)
    
    if origem_filter:
        precatorios = precatorios.filter(origem__icontains=origem_filter)
    
    if credito_principal_filter:
        precatorios = precatorios.filter(credito_principal=credito_principal_filter)
    
    if honorarios_contratuais_filter:
        precatorios = precatorios.filter(honorarios_contratuais=honorarios_contratuais_filter)
    
    if honorarios_sucumbenciais_filter:
        precatorios = precatorios.filter(honorarios_sucumbenciais=honorarios_sucumbenciais_filter)
    
    # Filter by tipo de requerimento and deferimento status
    # These filters should work together - if both are selected, we need requerimentos that match BOTH conditions
    if tipo_requerimento_filter and requerimento_deferido_filter:
        # For "sem_acordo", we need special handling in combined filters
        if tipo_requerimento_filter == 'sem_acordo':
            # Handle these cases by applying individual filters sequentially
            # Apply the "sem" filter first
            precatorios_com_acordo = Requerimento.objects.filter(
                pedido__in=['acordo principal', 'acordo honorários contratuais', 'acordo honorários sucumbenciais']
            ).values_list('precatorio__cnj', flat=True).distinct()
            precatorios = precatorios.exclude(cnj__in=precatorios_com_acordo)
            
            # Then apply the deferimento filter to the remaining precatorios
            if requerimento_deferido_filter == 'deferido':
                precatorios_deferidos = Requerimento.objects.filter(
                    fase__nome='Deferido'
                ).values_list('precatorio__cnj', flat=True).distinct()
                precatorios = precatorios.filter(cnj__in=precatorios_deferidos)
            elif requerimento_deferido_filter == 'nao_deferido':
                precatorios_nao_deferidos = Requerimento.objects.exclude(
                    fase__nome='Deferido'
                ).values_list('precatorio__cnj', flat=True).distinct()
                precatorios = precatorios.filter(cnj__in=precatorios_nao_deferidos)
        else:
            # Combined filter: find requerimentos that match both tipo AND deferimento status
            requerimento_query = Requerimento.objects.all()
            
            # Apply tipo filter (only acordo now)
            if tipo_requerimento_filter == 'acordo':
                requerimento_query = requerimento_query.filter(pedido__in=['acordo principal', 'acordo honorários contratuais', 'acordo honorários sucumbenciais'])
            
            # Apply deferimento filter
            if requerimento_deferido_filter == 'deferido':
                requerimento_query = requerimento_query.filter(fase__nome='Deferido')
            elif requerimento_deferido_filter == 'nao_deferido':
                requerimento_query = requerimento_query.exclude(fase__nome='Deferido')
            
            # Get precatorios that have requerimentos matching BOTH conditions
            precatorios_combined = requerimento_query.values_list('precatorio__cnj', flat=True).distinct()
            precatorios = precatorios.filter(cnj__in=precatorios_combined)
        
    else:
        # Apply filters individually when only one is selected
        if tipo_requerimento_filter == 'acordo':
            # Show only precatorios that have requerimentos with acordo pedidos
            precatorios_com_acordo = Requerimento.objects.filter(
                pedido__in=['acordo principal', 'acordo honorários contratuais', 'acordo honorários sucumbenciais']
            ).values_list('precatorio__cnj', flat=True).distinct()
            precatorios = precatorios.filter(cnj__in=precatorios_com_acordo)
        elif tipo_requerimento_filter == 'sem_acordo':
            # Show precatorios that have NO acordo requerimentos (may have other types or none at all)
            precatorios_com_acordo = Requerimento.objects.filter(
                pedido__in=['acordo principal', 'acordo honorários contratuais', 'acordo honorários sucumbenciais']
            ).values_list('precatorio__cnj', flat=True).distinct()
            precatorios = precatorios.exclude(cnj__in=precatorios_com_acordo)
        
        if requerimento_deferido_filter == 'deferido':
            # Show only precatorios that have at least one requerimento with 'Deferido' phase
            precatorios_deferidos = Requerimento.objects.filter(
                fase__nome='Deferido'
            ).values_list('precatorio__cnj', flat=True).distinct()
            precatorios = precatorios.filter(cnj__in=precatorios_deferidos)
        elif requerimento_deferido_filter == 'nao_deferido':
            # Show only precatorios that have requerimentos that are NOT 'Deferido'
            # This includes requerimentos with any other fase or no fase at all
            precatorios_nao_deferidos = Requerimento.objects.exclude(
                fase__nome='Deferido'
            ).values_list('precatorio__cnj', flat=True).distinct()
            precatorios = precatorios.filter(cnj__in=precatorios_nao_deferidos)
    
    # Calculate summary statistics
    total_precatorios = precatorios.count()
    
    # Calculate counts for different payment statuses
    pendentes_principal = precatorios.filter(credito_principal='pendente').count()
    quitados_principal = precatorios.filter(credito_principal='quitado').count()
    parciais_principal = precatorios.filter(credito_principal='parcial').count()
    vendidos_principal = precatorios.filter(credito_principal='vendido').count()
    
    # Calculate prioritarios count (precatorios with prioridade requerimentos)
    prioritarios_cnjs = Requerimento.objects.filter(
        pedido__in=['prioridade idade', 'prioridade doença']
    ).values_list('precatorio__cnj', flat=True).distinct()
    prioritarios = precatorios.filter(cnj__in=prioritarios_cnjs).count()
    
    context = {
        'precatorios': precatorios,
        'total_precatorios': total_precatorios,
        'pendentes_principal': pendentes_principal,
        'quitados_principal': quitados_principal,
        'parciais_principal': parciais_principal,
        'vendidos_principal': vendidos_principal,
        'prioritarios': prioritarios,
        # Include current filter values to maintain state in form
        'current_cnj': cnj_filter,
        'current_origem': origem_filter,
        'current_credito_principal': credito_principal_filter,
        'current_honorarios_contratuais': honorarios_contratuais_filter,
        'current_honorarios_sucumbenciais': honorarios_sucumbenciais_filter,
        'current_tipo_requerimento': tipo_requerimento_filter,
        'current_requerimento_deferido': requerimento_deferido_filter,
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
    requerimento_form = RequerimentoForm(precatorio=precatorio)
    cliente_form = ClienteSimpleForm()
    alvara_form = AlvaraSimpleForm(precatorio=precatorio)
    
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
            client_search_form = ClienteSearchForm(request.POST)  # This creates the form with POST data
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
            # Note: client_search_form now contains the POST data and any validation errors
        
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
            requerimento_form = RequerimentoForm(request.POST, precatorio=precatorio)
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
            alvara_form = AlvaraSimpleForm(request.POST, precatorio=precatorio)
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
                
                # Handle fase_honorarios_contratuais field properly (ForeignKey)
                fase_honorarios_id = request.POST.get('fase_honorarios_contratuais')
                if fase_honorarios_id:
                    try:
                        fase_honorarios = FaseHonorariosContratuais.objects.get(id=fase_honorarios_id)
                        alvara.fase_honorarios_contratuais = fase_honorarios
                    except FaseHonorariosContratuais.DoesNotExist:
                        messages.error(request, 'Fase Honorários Contratuais selecionada não existe.')
                        return redirect('precatorio_detalhe', precatorio_cnj=precatorio.cnj)
                else:
                    alvara.fase_honorarios_contratuais = None
                
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
        'fases_honorarios_contratuais': FaseHonorariosContratuais.objects.filter(ativa=True).order_by('nome'),
    }
    
    return render(request, 'precapp/precatorio_detail.html', context)


@login_required
def clientes_view(request):
    """View to display all clients with filtering support"""
    clientes = Cliente.objects.all().prefetch_related(
        'precatorios', 
        'precatorios__requerimento_set', 
        'precatorios__requerimento_set__fase'
    )
    
    # Apply filters based on GET parameters
    nome_filter = request.GET.get('nome', '').strip()
    cpf_filter = request.GET.get('cpf', '').strip()
    idade_filter = request.GET.get('idade', '').strip()
    prioridade_filter = request.GET.get('prioridade', '')
    requerimento_prioridade_filter = request.GET.get('requerimento_prioridade', '')
    precatorio_filter = request.GET.get('precatorio', '').strip()
    
    if nome_filter:
        clientes = clientes.filter(nome__icontains=nome_filter)
    
    if cpf_filter:
        clientes = clientes.filter(cpf__icontains=cpf_filter)
    
    # Filter by age
    if idade_filter:
        try:
            idade = int(idade_filter)
            from datetime import date
            from dateutil.relativedelta import relativedelta
            
            # Calculate the birth year range for clients of the specified age
            today = date.today()
            # For someone to be X years old today, they must have been born between:
            # - (today - X+1 years + 1 day) and (today - X years)
            min_birth_date = today - relativedelta(years=idade+1, days=-1)
            max_birth_date = today - relativedelta(years=idade)
            
            clientes = clientes.filter(
                nascimento__gte=min_birth_date,
                nascimento__lte=max_birth_date
            )
        except ValueError:
            # If idade_filter is not a valid integer, ignore the filter
            pass

    if prioridade_filter in ['true', 'false']:
        prioridade_bool = prioridade_filter == 'true'
        clientes = clientes.filter(prioridade=prioridade_bool)
    
    # Filter by requerimento prioridade (based on Deferido/Não Deferido status)
    if requerimento_prioridade_filter:
        if requerimento_prioridade_filter == 'deferido':
            # Find clientes that have priority requerimentos with 'Deferido' phase
            clientes_deferidos = Requerimento.objects.filter(
                pedido__in=['prioridade idade', 'prioridade doença'],
                fase__nome='Deferido'
            ).values_list('cliente__cpf', flat=True).distinct()
            clientes = clientes.filter(cpf__in=clientes_deferidos)
        elif requerimento_prioridade_filter == 'nao_deferido':
            # Find clientes that have priority requerimentos that are NOT 'Deferido'
            clientes_nao_deferidos = Requerimento.objects.filter(
                pedido__in=['prioridade idade', 'prioridade doença']
            ).exclude(
                fase__nome='Deferido'
            ).values_list('cliente__cpf', flat=True).distinct()
            clientes = clientes.filter(cpf__in=clientes_nao_deferidos)
        elif requerimento_prioridade_filter == 'sem_requerimento':
            # Find clientes that have NO priority requerimentos at all
            clientes_com_requerimentos = Requerimento.objects.filter(
                pedido__in=['prioridade idade', 'prioridade doença']
            ).values_list('cliente__cpf', flat=True).distinct()
            clientes = clientes.exclude(cpf__in=clientes_com_requerimentos)
    
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
        'current_idade': idade_filter,
        'current_prioridade': prioridade_filter,
        'current_requerimento_prioridade': requerimento_prioridade_filter,
        'current_precatorio': precatorio_filter,
    }
    
    return render(request, 'precapp/cliente_list.html', context)


@login_required
def cliente_detail_view(request, cpf):
    """View to display and edit a specific client and manage precatorio relationships"""
    cliente = get_object_or_404(Cliente, cpf=cpf)
    
    # Get all precatorios associated with this client
    associated_precatorios = cliente.precatorios.all().order_by('cnj')
    
    # Get all diligencias for this client
    diligencias = cliente.diligencias.all().select_related('tipo').order_by('-data_criacao')
    diligencias_pendentes = diligencias.filter(concluida=False)
    diligencias_concluidas = diligencias.filter(concluida=True)
    
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
        'diligencias': diligencias,
        'diligencias_pendentes': diligencias_pendentes,
        'diligencias_concluidas': diligencias_concluidas,
        'total_diligencias': diligencias.count(),
        'total_pendentes': diligencias_pendentes.count(),
        'total_concluidas': diligencias_concluidas.count(),
    }
    
    return render(request, 'precapp/cliente_detail.html', context)


@login_required
def alvaras_view(request):
    """View to display all alvarás with filtering support"""
    alvaras = Alvara.objects.all().select_related('precatorio', 'cliente', 'fase', 'fase_honorarios_contratuais').order_by('-id')
    
    # Get available fases for alvara
    available_fases = Fase.get_fases_for_alvara()
    # Get available fases for honorários contratuais
    available_fases_honorarios = FaseHonorariosContratuais.objects.all().order_by('nome')
    
    # Apply filters based on GET parameters
    nome_filter = request.GET.get('nome', '').strip()
    precatorio_filter = request.GET.get('precatorio', '').strip()
    tipo_filter = request.GET.get('tipo', '').strip()
    fase_filter = request.GET.get('fase', '').strip()
    fase_honorarios_filter = request.GET.get('fase_honorarios', '').strip()
    
    if nome_filter:
        alvaras = alvaras.filter(cliente__nome__icontains=nome_filter)
    
    if precatorio_filter:
        alvaras = alvaras.filter(precatorio__cnj__icontains=precatorio_filter)
    
    if tipo_filter:
        alvaras = alvaras.filter(tipo=tipo_filter)  # Exact match for dropdown
    
    if fase_filter:
        alvaras = alvaras.filter(fase__nome=fase_filter)  # Exact match for dropdown
        
    if fase_honorarios_filter:
        alvaras = alvaras.filter(fase_honorarios_contratuais__nome=fase_honorarios_filter)  # Exact match for dropdown
    
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
        'current_fase_honorarios': fase_honorarios_filter,
        # Include available options for dropdowns
        'available_fases': available_fases,
        'available_fases_honorarios': available_fases_honorarios,
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


# FASE HONORÁRIOS CONTRATUAIS MANAGEMENT VIEWS
# ===============================

@login_required
def fases_honorarios_view(request):
    """View to list all honorários contratuais phases"""
    fases = FaseHonorariosContratuais.objects.all().order_by('nome')
    
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
    
    return render(request, 'precapp/fases_honorarios_list.html', context)


@login_required
def nova_fase_honorarios_view(request):
    """View to create a new honorários contratuais phase"""
    if request.method == 'POST':
        form = FaseHonorariosContratuaisForm(request.POST)
        if form.is_valid():
            fase = form.save()
            messages.success(request, f'Fase de Honorários Contratuais "{fase.nome}" criada com sucesso!')
            return redirect('fases_honorarios')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = FaseHonorariosContratuaisForm()
    
    context = {
        'form': form,
        'title': 'Nova Fase Honorários Contratuais',
        'submit_text': 'Criar Fase'
    }
    return render(request, 'precapp/fase_honorarios_form.html', context)


@login_required
def editar_fase_honorarios_view(request, fase_id):
    """View to edit an existing honorários contratuais phase"""
    fase = get_object_or_404(FaseHonorariosContratuais, id=fase_id)
    
    if request.method == 'POST':
        form = FaseHonorariosContratuaisForm(request.POST, instance=fase)
        if form.is_valid():
            fase = form.save()
            messages.success(request, f'Fase de Honorários Contratuais "{fase.nome}" atualizada com sucesso!')
            return redirect('fases_honorarios')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = FaseHonorariosContratuaisForm(instance=fase)
    
    context = {
        'form': form,
        'fase': fase,
        'title': f'Editar Fase Honorários Contratuais: {fase.nome}',
        'submit_text': 'Salvar Alterações'
    }
    return render(request, 'precapp/fase_honorarios_form.html', context)


@login_required
def deletar_fase_honorarios_view(request, fase_id):
    """View to delete a honorários contratuais phase"""
    fase = get_object_or_404(FaseHonorariosContratuais, id=fase_id)
    
    if request.method == 'POST':
        fase_nome = fase.nome
        
        # Check if fase is being used by any alvara
        alvaras_using_fase = Alvara.objects.filter(fase_honorarios_contratuais=fase)
        if alvaras_using_fase.exists():
            messages.error(
                request, 
                f'Não é possível excluir a fase de honorários contratuais "{fase_nome}" pois ela está sendo usada por {alvaras_using_fase.count()} alvará(s). '
                'Altere a fase desses alvarás primeiro.'
            )
            return redirect('fases_honorarios')
        
        fase.delete()
        messages.success(request, f'Fase de Honorários Contratuais "{fase_nome}" foi excluída com sucesso!')
        return redirect('fases_honorarios')
    
    # If not POST, redirect to fases list
    return redirect('fases_honorarios')


@login_required
def ativar_fase_honorarios_view(request, fase_id):
    """View to activate/deactivate a honorários contratuais phase"""
    fase = get_object_or_404(FaseHonorariosContratuais, id=fase_id)
    
    if request.method == 'POST':
        fase.ativa = not fase.ativa
        fase.save()
        
        status_text = "ativada" if fase.ativa else "desativada"
        messages.success(request, f'Fase de Honorários Contratuais "{fase.nome}" foi {status_text} com sucesso!')
    
    return redirect('fases_honorarios')


# TIPO DILIGENCIA VIEWS
# ===============================

@login_required
def tipos_diligencia_view(request):
    """View to list all diligence types"""
    tipos = TipoDiligencia.objects.all().order_by('nome')
    
    # Add diligencias count for each tipo
    for tipo in tipos:
        tipo.diligencias_count = tipo.diligencias_set.count()
    
    # Statistics
    total_tipos = tipos.count()
    tipos_ativos = tipos.filter(ativo=True).count()
    tipos_inativos = tipos.filter(ativo=False).count()
    
    # Get count of total diligencias using the reverse relationship
    total_diligencias = sum(tipo.diligencias_set.count() for tipo in tipos)
    
    context = {
        'tipos_diligencia': tipos,  # Changed from 'tipos' to match template
        'total_tipos': total_tipos,
        'tipos_ativos': tipos_ativos,
        'tipos_inativos': tipos_inativos,
        'total_diligencias': total_diligencias,
    }
    
    return render(request, 'precapp/tipos_diligencia_list.html', context)


@login_required
def novo_tipo_diligencia_view(request):
    """View to create a new diligence type"""
    if request.method == 'POST':
        form = TipoDiligenciaForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            messages.success(request, f'Tipo de Diligência "{tipo.nome}" criado com sucesso!')
            return redirect('tipos_diligencia')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = TipoDiligenciaForm()
    
    context = {
        'form': form,
        'title': 'Novo Tipo de Diligência',
        'action': 'Criar'
    }
    
    return render(request, 'precapp/tipo_diligencia_form.html', context)


@login_required
def editar_tipo_diligencia_view(request, tipo_id):
    """View to edit an existing diligence type"""
    tipo = get_object_or_404(TipoDiligencia, id=tipo_id)
    
    if request.method == 'POST':
        # Check if this is an update from the dropdown form in list view
        if 'update_tipo' in request.POST:
            # Handle direct field updates from dropdown form
            nome = request.POST.get('nome')
            cor = request.POST.get('cor')
            descricao = request.POST.get('descricao', '')
            ativo = 'ativo' in request.POST
            
            if nome and cor:
                tipo.nome = nome
                tipo.cor = cor
                tipo.descricao = descricao
                tipo.ativo = ativo
                tipo.save()
                messages.success(request, f'Tipo de Diligência "{tipo.nome}" atualizado com sucesso!')
                return redirect('tipos_diligencia')
            else:
                messages.error(request, 'Nome e cor são campos obrigatórios.')
                return redirect('tipos_diligencia')
        else:
            # Handle regular form update
            form = TipoDiligenciaForm(request.POST, instance=tipo)
            if form.is_valid():
                tipo = form.save()
                messages.success(request, f'Tipo de Diligência "{tipo.nome}" atualizado com sucesso!')
                return redirect('tipos_diligencia')
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = TipoDiligenciaForm(instance=tipo)
    
    context = {
        'form': form,
        'tipo': tipo,
        'title': f'Editar Tipo: {tipo.nome}',
        'action': 'Atualizar'
    }
    
    return render(request, 'precapp/tipo_diligencia_form.html', context)


@login_required
def deletar_tipo_diligencia_view(request, tipo_id):
    """View to delete a diligence type"""
    tipo = get_object_or_404(TipoDiligencia, id=tipo_id)
    
    if request.method == 'POST':
        try:
            nome_tipo = tipo.nome
            tipo.delete()
            messages.success(request, f'Tipo de Diligência "{nome_tipo}" excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir tipo: {str(e)}')
        
        return redirect('tipos_diligencia')
    
    # Count related diligencias
    diligencias_count = tipo.diligencias.count() if hasattr(tipo, 'diligencias') else 0
    
    context = {
        'tipo': tipo,
        'diligencias_count': diligencias_count,
        'can_delete': diligencias_count == 0
    }
    
    return render(request, 'precapp/confirmar_delete_tipo_diligencia.html', context)


@login_required  
def ativar_tipo_diligencia_view(request, tipo_id):
    """View to toggle active status of a diligence type"""
    tipo = get_object_or_404(TipoDiligencia, id=tipo_id)
    
    if request.method == 'POST':
        # Handle POST from dropdown form
        ativo_value = request.POST.get('ativo', 'false')
        tipo.ativo = ativo_value.lower() == 'true'
    else:
        # Handle GET for backward compatibility
        ativo_param = request.GET.get('ativo', '').lower()
        if ativo_param == 'true':
            tipo.ativo = True
        elif ativo_param == 'false':
            tipo.ativo = False
        else:
            # Toggle if no parameter
            tipo.ativo = not tipo.ativo
    
    tipo.save()
    
    status = "ativado" if tipo.ativo else "desativado"
    messages.success(request, f'Tipo de Diligência "{tipo.nome}" {status} com sucesso!')
    
    return redirect('tipos_diligencia')


# CUSTOMIZAÇÃO PAGE
# ===============================

@login_required
def customizacao_view(request):
    """Central customization page for managing phases and diligence types"""
    # Get statistics for both phase types and diligence types
    fases_principais = Fase.objects.all()
    fases_honorarios = FaseHonorariosContratuais.objects.all()
    tipos_diligencia = TipoDiligencia.objects.all()
    
    context = {
        # Fases Principais stats
        'total_fases_principais': fases_principais.count(),
        'fases_principais_ativas': fases_principais.filter(ativa=True).count(),
        'fases_principais_inativas': fases_principais.filter(ativa=False).count(),
        
        # Fases Honorários stats
        'total_fases_honorarios': fases_honorarios.count(),
        'fases_honorarios_ativas': fases_honorarios.filter(ativa=True).count(),
        'fases_honorarios_inativas': fases_honorarios.filter(ativa=False).count(),
        
        # Tipos Diligência stats
        'total_tipos_diligencia': tipos_diligencia.count(),
        'tipos_diligencia_ativos': tipos_diligencia.filter(ativo=True).count(),
        'tipos_diligencia_inativos': tipos_diligencia.filter(ativo=False).count(),
        
        # Recent items (last 5 of each type)
        'recent_fases_principais': fases_principais.order_by('-criado_em')[:5],
        'recent_fases_honorarios': fases_honorarios.order_by('-criado_em')[:5],
        'recent_tipos_diligencia': tipos_diligencia.order_by('-criado_em')[:5],
    }
    
    return render(request, 'precapp/customizacao.html', context)


@login_required
@require_http_methods(["POST"])
def update_priority_by_age(request):
    """Update priority status for clients over 60 years old"""
    from datetime import date, timedelta
    
    try:
        # Calculate date 60 years ago
        sixty_years_ago = date.today() - timedelta(days=60*365.25)
        
        # Find clients born before this date (older than 60) without priority
        clients_over_60 = Cliente.objects.filter(
            nascimento__lt=sixty_years_ago,
            prioridade=False
        )
        
        count_before = clients_over_60.count()
        
        if count_before > 0:
            # Update their priority status
            updated_count = clients_over_60.update(prioridade=True)
            
            messages.success(
                request, 
                f'✅ {updated_count} cliente(s) com mais de 60 anos foram atualizados para status prioritário.'
            )
            
            # Log some examples for transparency
            if updated_count > 0:
                examples = Cliente.objects.filter(
                    nascimento__lt=sixty_years_ago,
                    prioridade=True
                )[:3]
                
                example_names = [client.nome for client in examples]
                if len(example_names) > 0:
                    examples_text = ", ".join(example_names)
                    if updated_count > 3:
                        examples_text += f" e mais {updated_count - 3} cliente(s)"
                    
                    messages.info(
                        request,
                        f'Exemplos atualizados: {examples_text}'
                    )
        else:
            messages.info(
                request,
                '📋 Nenhum cliente encontrado que precise ser atualizado. Todos os clientes com mais de 60 anos já possuem status prioritário.'
            )
            
    except Exception as e:
        messages.error(
            request,
            f'❌ Erro ao atualizar prioridades: {str(e)}'
        )
    
    return redirect('clientes')


# ===== DILIGENCIA CRUD VIEWS =====

@login_required
def nova_diligencia_view(request, cpf):
    """Create a new diligencia for a specific client"""
    cliente = get_object_or_404(Cliente, cpf=cpf)
    
    if request.method == 'POST':
        form = DiligenciasForm(request.POST)
        if form.is_valid():
            diligencia = form.save(commit=False)
            diligencia.cliente = cliente
            # Automatically set the creator to the current logged-in user
            diligencia.criado_por = request.user.get_full_name() or request.user.username
            diligencia.save()
            messages.success(request, f'Diligência criada com sucesso para {cliente.nome}!')
            return redirect('cliente_detail', cpf=cliente.cpf)
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = DiligenciasForm()
    
    context = {
        'form': form,
        'cliente': cliente,
        'action': 'create'
    }
    
    return render(request, 'precapp/diligencia_form.html', context)


@login_required
def editar_diligencia_view(request, cpf, diligencia_id):
    """Edit an existing diligencia"""
    cliente = get_object_or_404(Cliente, cpf=cpf)
    diligencia = get_object_or_404(Diligencias, id=diligencia_id, cliente=cliente)
    
    if request.method == 'POST':
        form = DiligenciasForm(request.POST, instance=diligencia)
        if form.is_valid():
            # Save the form but preserve the original creator
            updated_diligencia = form.save(commit=False)
            # Ensure the creator is not changed during edit
            updated_diligencia.criado_por = diligencia.criado_por
            updated_diligencia.save()
            messages.success(request, f'Diligência atualizada com sucesso!')
            return redirect('cliente_detail', cpf=cliente.cpf)
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = DiligenciasForm(instance=diligencia)
    
    context = {
        'form': form,
        'cliente': cliente,
        'diligencia': diligencia,
        'action': 'edit'
    }
    
    return render(request, 'precapp/diligencia_form.html', context)


@login_required
def deletar_diligencia_view(request, cpf, diligencia_id):
    """Delete a diligencia"""
    cliente = get_object_or_404(Cliente, cpf=cpf)
    diligencia = get_object_or_404(Diligencias, id=diligencia_id, cliente=cliente)
    
    if request.method == 'POST':
        diligencia_nome = str(diligencia)
        diligencia.delete()
        messages.success(request, f'Diligência "{diligencia_nome}" excluída com sucesso!')
        return redirect('cliente_detail', cpf=cliente.cpf)
    
    context = {
        'diligencia': diligencia,
        'cliente': cliente,
        'total_diligencias': cliente.diligencias.count(),
        'pendentes_diligencias': cliente.diligencias.filter(concluida=False).count(),
        'concluidas_diligencias': cliente.diligencias.filter(concluida=True).count(),
    }
    
    return render(request, 'precapp/confirmar_delete_diligencia.html', context)


@login_required
def marcar_diligencia_concluida_view(request, cpf, diligencia_id):
    """Toggle diligencia completion status"""
    cliente = get_object_or_404(Cliente, cpf=cpf)
    diligencia = get_object_or_404(Diligencias, id=diligencia_id, cliente=cliente)
    
    if request.method == 'POST':
        # Save the original state from database before form processing
        # since ModelForm.is_valid() can modify the instance
        original_diligencia = Diligencias.objects.get(id=diligencia.id)
        was_completed_before = original_diligencia.concluida
        
        form = DiligenciasUpdateForm(request.POST, instance=diligencia)
        if form.is_valid():
            updated_diligencia = form.save(commit=False)
            
            # Handle concluido_por field automatically
            if updated_diligencia.concluida:
                # If marking as completed, set the current user as completer
                if not was_completed_before:  # Use saved state from database
                    updated_diligencia.concluido_por = request.user.get_full_name() or request.user.username
            else:
                # If marking as not completed (reopening), clear the completer
                updated_diligencia.concluido_por = None
            
            updated_diligencia.save()
            status = "concluída" if updated_diligencia.concluida else "reaberta"
            messages.success(request, f'Diligência marcada como {status}!')
            return redirect('cliente_detail', cpf=cliente.cpf)
        else:
            messages.error(request, 'Erro ao atualizar a diligência.')
    else:
        form = DiligenciasUpdateForm(instance=diligencia)
    
    # Calculate statistics for the client
    total_diligencias = cliente.diligencias.count()
    pendentes_diligencias = cliente.diligencias.filter(concluida=False).count()
    concluidas_diligencias = cliente.diligencias.filter(concluida=True).count()
    
    context = {
        'form': form,
        'diligencia': diligencia,
        'cliente': cliente,
        'total_diligencias': total_diligencias,
        'pendentes_diligencias': pendentes_diligencias,
        'concluidas_diligencias': concluidas_diligencias,
    }
    
    return render(request, 'precapp/diligencia_conclusao_form.html', context)


@login_required
def diligencias_list_view(request):
    """List all diligencias with filtering and search capabilities"""
    diligencias = Diligencias.objects.select_related('cliente', 'tipo').order_by('-data_criacao')
    
    # Filter parameters
    status_filter = request.GET.get('status', '')
    urgencia_filter = request.GET.get('urgencia', '')
    tipo_filter = request.GET.get('tipo', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if status_filter == 'pendente':
        diligencias = diligencias.filter(concluida=False)
    elif status_filter == 'concluida':
        diligencias = diligencias.filter(concluida=True)
    
    if urgencia_filter:
        diligencias = diligencias.filter(urgencia=urgencia_filter)
    
    if tipo_filter:
        diligencias = diligencias.filter(tipo_id=tipo_filter)
    
    if search_query:
        diligencias = diligencias.filter(
            Q(cliente__nome__icontains=search_query) |
            Q(cliente__cpf__icontains=search_query) |
            Q(tipo__nome__icontains=search_query) |
            Q(descricao__icontains=search_query)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(diligencias, 25)  # 25 diligencias per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_diligencias = Diligencias.objects.count()
    pendentes_diligencias = Diligencias.objects.filter(concluida=False).count()
    concluidas_diligencias = Diligencias.objects.filter(concluida=True).count()
    atrasadas_diligencias = Diligencias.objects.filter(
        concluida=False,
        data_final__lt=timezone.now().date()
    ).count()
    
    # Get filter options
    tipos_diligencia = TipoDiligencia.get_ativos()
    urgencia_choices = Diligencias.URGENCIA_CHOICES
    
    context = {
        'page_obj': page_obj,
        'diligencias': page_obj,
        'total_diligencias': total_diligencias,
        'pendentes_diligencias': pendentes_diligencias,
        'concluidas_diligencias': concluidas_diligencias,
        'atrasadas_diligencias': atrasadas_diligencias,
        'tipos_diligencia': tipos_diligencia,
        'urgencia_choices': urgencia_choices,
        'status_filter': status_filter,
        'urgencia_filter': urgencia_filter,
        'tipo_filter': tipo_filter,
        'search_query': search_query,
    }
    
    return render(request, 'precapp/diligencias_list.html', context)