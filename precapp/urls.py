from django.urls import path

from .views import (
    novoPrec_view, home_view, precatorio_view, precatorio_detalhe_view, delete_precatorio_view,
    clientes_view, cliente_detail_view, novo_cliente_view, delete_cliente_view,
    alvaras_view, delete_alvara_view,
    requerimento_list_view, login_view, logout_view,
    fases_view, nova_fase_view, editar_fase_view, deletar_fase_view, ativar_fase_view,
    fases_honorarios_view, nova_fase_honorarios_view, editar_fase_honorarios_view, 
    deletar_fase_honorarios_view, ativar_fase_honorarios_view, customizacao_view,
    tipos_precatorio_view, novo_tipo_precatorio_view, editar_tipo_precatorio_view,
    deletar_tipo_precatorio_view, ativar_tipo_precatorio_view,
    tipos_pedido_requerimento_view, novo_tipo_pedido_requerimento_view, editar_tipo_pedido_requerimento_view,
    deletar_tipo_pedido_requerimento_view, ativar_tipo_pedido_requerimento_view,
    tipos_diligencia_view, novo_tipo_diligencia_view, editar_tipo_diligencia_view,
    deletar_tipo_diligencia_view, ativar_tipo_diligencia_view,
    nova_diligencia_view, editar_diligencia_view, deletar_diligencia_view, marcar_diligencia_concluida_view,
    diligencias_list_view, update_priority_by_age, import_excel_view, export_precatorios_excel, export_clientes_excel,
    download_precatorio_file,
    contas_bancarias_view, nova_conta_bancaria_view, editar_conta_bancaria_view, deletar_conta_bancaria_view,
    novo_recebimento_view, listar_recebimentos_view, editar_recebimento_view, deletar_recebimento_view
)

urlpatterns = [
    # Authentication URLs
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Main application URLs
    path('', home_view, name='home'),
    path('precatorios/novo/', novoPrec_view, name='novo_precatorio'),
    path('precatorios/', precatorio_view, name='precatorios'),
    path('precatorios/import/', import_excel_view, name='import_excel'),
    path('precatorios/export/', export_precatorios_excel, name='export_precatorios_excel'),
    path('precatorios/<str:precatorio_cnj>/', precatorio_detalhe_view, name='precatorio_detalhe'),
    path('precatorios/<str:precatorio_cnj>/delete/', delete_precatorio_view, name='delete_precatorio'),
    path('precatorios/<str:precatorio_cnj>/download/', download_precatorio_file, name='download_precatorio_file'),
    path('clientes/', clientes_view, name='clientes'),
    path('clientes/export/', export_clientes_excel, name='export_clientes_excel'),
    path('clientes/update-priority/', update_priority_by_age, name='update_priority_by_age'),
    path('clientes/novo/', novo_cliente_view, name='novo_cliente'),
    path('clientes/<str:cpf>/', cliente_detail_view, name='cliente_detail'),
    path('clientes/<str:cpf>/delete/', delete_cliente_view, name='delete_cliente'),
    path('alvaras/', alvaras_view, name='alvaras'),
    path('alvara/<int:alvara_id>/delete/', delete_alvara_view, name='delete_alvara'),
    path('diligencias/', diligencias_list_view, name='diligencias_list'),
    path('requerimentos/', requerimento_list_view, name='requerimentos'),
    
    # Customization Page
    path('customizacao/', customizacao_view, name='customizacao'),
    
    # Phase Management URLs
    path('fases/', fases_view, name='fases'),
    path('fases/nova/', nova_fase_view, name='nova_fase'),
    path('fases/<int:fase_id>/editar/', editar_fase_view, name='editar_fase'),
    path('fases/<int:fase_id>/deletar/', deletar_fase_view, name='deletar_fase'),
    path('fases/<int:fase_id>/ativar/', ativar_fase_view, name='ativar_fase'),
    
    # Honorários Contratuais Phase Management URLs
    path('fases-honorarios/', fases_honorarios_view, name='fases_honorarios'),
    path('fases-honorarios/nova/', nova_fase_honorarios_view, name='nova_fase_honorarios'),
    path('fases-honorarios/<int:fase_id>/editar/', editar_fase_honorarios_view, name='editar_fase_honorarios'),
    path('fases-honorarios/<int:fase_id>/deletar/', deletar_fase_honorarios_view, name='deletar_fase_honorarios'),
    path('fases-honorarios/<int:fase_id>/ativar/', ativar_fase_honorarios_view, name='ativar_fase_honorarios'),
    
    # Tipo Precatório Management URLs
    path('tipos-precatorio/', tipos_precatorio_view, name='tipos_precatorio'),
    path('tipos-precatorio/novo/', novo_tipo_precatorio_view, name='novo_tipo_precatorio'),
    path('tipos-precatorio/<int:tipo_id>/editar/', editar_tipo_precatorio_view, name='editar_tipo_precatorio'),
    path('tipos-precatorio/<int:tipo_id>/deletar/', deletar_tipo_precatorio_view, name='deletar_tipo_precatorio'),
    path('tipos-precatorio/<int:tipo_id>/ativar/', ativar_tipo_precatorio_view, name='ativar_tipo_precatorio'),
    
    # Tipo Pedido Requerimento Management URLs
    path('tipos-pedido-requerimento/', tipos_pedido_requerimento_view, name='tipos_pedido_requerimento'),
    path('tipos-pedido-requerimento/novo/', novo_tipo_pedido_requerimento_view, name='novo_tipo_pedido_requerimento'),
    path('tipos-pedido-requerimento/<int:tipo_id>/editar/', editar_tipo_pedido_requerimento_view, name='editar_tipo_pedido_requerimento'),
    path('tipos-pedido-requerimento/<int:tipo_id>/deletar/', deletar_tipo_pedido_requerimento_view, name='deletar_tipo_pedido_requerimento'),
    path('tipos-pedido-requerimento/<int:tipo_id>/ativar/', ativar_tipo_pedido_requerimento_view, name='ativar_tipo_pedido_requerimento'),
    
    # Tipo Diligencia Management URLs
    path('tipos-diligencia/', tipos_diligencia_view, name='tipos_diligencia'),
    path('tipos-diligencia/novo/', novo_tipo_diligencia_view, name='novo_tipo_diligencia'),
    path('tipos-diligencia/<int:tipo_id>/editar/', editar_tipo_diligencia_view, name='editar_tipo_diligencia'),
    path('tipos-diligencia/<int:tipo_id>/deletar/', deletar_tipo_diligencia_view, name='deletar_tipo_diligencia'),
    path('tipos-diligencia/<int:tipo_id>/ativar/', ativar_tipo_diligencia_view, name='ativar_tipo_diligencia'),
    
    # ContaBancaria Management URLs
    path('contas-bancarias/', contas_bancarias_view, name='contas_bancarias'),
    path('contas-bancarias/nova/', nova_conta_bancaria_view, name='nova_conta_bancaria'),
    path('contas-bancarias/<int:conta_id>/editar/', editar_conta_bancaria_view, name='editar_conta_bancaria'),
    path('contas-bancarias/<int:conta_id>/deletar/', deletar_conta_bancaria_view, name='deletar_conta_bancaria'),
    
    # Recebimentos Management URLs
    path('alvaras/<int:alvara_id>/recebimentos/novo/', novo_recebimento_view, name='novo_recebimento'),
    path('alvaras/<int:alvara_id>/recebimentos/listar/', listar_recebimentos_view, name='listar_recebimentos'),
    path('recebimentos/<str:recebimento_id>/editar/', editar_recebimento_view, name='editar_recebimento'),
    path('recebimentos/<str:recebimento_id>/deletar/', deletar_recebimento_view, name='deletar_recebimento'),
    
    # Diligencia Management URLs (within client context)
    path('clientes/<str:cpf>/diligencias/nova/', nova_diligencia_view, name='nova_diligencia'),
    path('clientes/<str:cpf>/diligencias/<int:diligencia_id>/editar/', editar_diligencia_view, name='editar_diligencia'),
    path('clientes/<str:cpf>/diligencias/<int:diligencia_id>/deletar/', deletar_diligencia_view, name='deletar_diligencia'),
    path('clientes/<str:cpf>/diligencias/<int:diligencia_id>/concluir/', marcar_diligencia_concluida_view, name='marcar_diligencia_concluida'),
]
