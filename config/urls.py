from django.contrib import admin
from django.urls import path
from app.views import (
    IndexView, MateriaisView, ServicosView, DetalheServicoView, 
    PedidosView, CategoriasView, UnidadesMedidaView,FornecedoresView,
    ReceberPedidoView,HistoricoMovimentacoesView,DashboardView,CancelarPedidoView,
    RegistrarConsumoView,DetalhePedidoView,ConcluirServicoView
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='index'),
    path('materiais/', MateriaisView.as_view(), name='materiais'),
    path('servicos/', ServicosView.as_view(), name='servicos'),
    path('pedidos/', PedidosView.as_view(), name='pedidos'),
    path('categorias/', CategoriasView.as_view(), name='categorias'), 
    path('unidades/', UnidadesMedidaView.as_view(), name='unidades'),
    path('historico/movimentacoes/', HistoricoMovimentacoesView.as_view(), name='historico_movimentacoes'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'), 
    path('fornecedores/', FornecedoresView.as_view(), name='fornecedores'),
    

    path('pedidos/receber/<int:pedido_id>/', ReceberPedidoView.as_view(), name='receber_pedido'),
    path('servicos/consumir/<int:servico_id>/', RegistrarConsumoView.as_view(), name='registrar_consumo'),
    path('pedidos/cancelar/<int:pedido_id>/', CancelarPedidoView.as_view(), name='cancelar_pedido'),

    path('pedidos/detalhe/<int:pedido_id>/', DetalhePedidoView.as_view(), name='detalhe_pedido'),
    path('servico/detalhe/<int:id>/', DetalheServicoView.as_view(), name='detalhe_servico'),



    path('servicos/concluir/<int:servico_id>/', ConcluirServicoView.as_view(), name='concluir_servico'),
    
]












