from django.urls import path

from .views import (
    novoPrec_view, home_view, precatorio_view, precatorio_detalhe_view, delete_precatorio_view,
    clientes_view, cliente_detail_view, novo_cliente_view, delete_cliente_view,
    alvaras_view, alvara_detail_view, delete_alvara_view,
    requerimento_list_view, login_view, logout_view
)

urlpatterns = [
    # Authentication URLs
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Main application URLs
    path('', home_view, name='home'),
    path('precatorios/novo/', novoPrec_view, name='novo_precatorio'),
    path('precatorios/', precatorio_view, name='precatorios'),
    path('precatorios/<str:precatorio_cnj>/', precatorio_detalhe_view, name='precatorio_detalhe'),
    path('precatorios/<str:precatorio_cnj>/delete/', delete_precatorio_view, name='delete_precatorio'),
    path('clientes/', clientes_view, name='clientes'),
    path('clientes/novo/', novo_cliente_view, name='novo_cliente'),
    path('clientes/<str:cpf>/', cliente_detail_view, name='cliente_detail'),
    path('clientes/<str:cpf>/delete/', delete_cliente_view, name='delete_cliente'),
    path('alvaras/', alvaras_view, name='alvaras'),
    path('alvara/<int:alvara_id>/', alvara_detail_view, name='alvara_detail'),
    path('alvara/<int:alvara_id>/delete/', delete_alvara_view, name='delete_alvara'),
    path('requerimentos/', requerimento_list_view, name='requerimentos'),
]
