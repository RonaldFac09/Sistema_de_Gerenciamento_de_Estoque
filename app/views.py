from datetime import datetime
from django.db import transaction
from django.db.models import Q

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.db.models import Sum, F 
from django.db.models.functions import ExtractMonth, ExtractYear
from .models import (
    Material, Categoria, UnidadeMedida, Servico, PedidoCompra, 
    ItemServicoNecessario, ItemPedido, MovimentacaoEstoque, RegistroConsumo,
    Fornecedor
)
class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'index.html')

    def post(self, request):
        pass

class MateriaisView(View):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('search', '')
        categoria_id_filter = request.GET.get('categoria', '') 
        materiais = Material.objects.all().order_by('nome') 

        if search_query:
            materiais = materiais.filter(nome__icontains=search_query) 

        if categoria_id_filter:
            materiais = materiais.filter(categoria_id=categoria_id_filter)
        
        todas_categorias = Categoria.objects.all().order_by('nome')
        
        context = {
            'materiais': materiais,
            'todas_categorias': todas_categorias, 
            'search_query': search_query, 
            'categoria_id_filter': categoria_id_filter, 
        }
        return render(request, 'materiais.html', context)


class CategoriasView(View):
    def get(self, request, *args, **kwargs):
        categorias = Categoria.objects.all()
        return render(request, 'categorias.html', {'categorias': categorias})


class UnidadesMedidaView(View):
    def get(self, request, *args, **kwargs):
        unidades = UnidadeMedida.objects.all()
        return render(request, 'unidades.html', {'unidades': unidades})


class ServicosView(View):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        
        servicos = Servico.objects.all().order_by('-data_criacao') 
        
        if search_query:
            servicos = servicos.filter(nome__icontains=search_query) 
        
        if status_filter:
            servicos = servicos.filter(status=status_filter)
        

        context = {
            'servicos': servicos,
            'search_query': search_query, 
            'status_filter': status_filter, 
        }
        return render(request, 'servicos.html', context)


class PedidosView(View):
    """Controla e exibe a lista de Pedidos de Compra com filtros."""
    def get(self, request, *args, **kwargs):
        fornecedor_id_filter = request.GET.get('fornecedor', '')
        month_filter = request.GET.get('mes', '')
        
        pedidos = PedidoCompra.objects.all().order_by('-data_criacao') 
        
        if fornecedor_id_filter:
            pedidos = pedidos.filter(fornecedor_id=fornecedor_id_filter)
        
        if month_filter and '-' in month_filter:
            try:
                mes, ano = map(int, month_filter.split('-'))
                pedidos = pedidos.filter(
                    data_criacao__month=mes, 
                    data_criacao__year=ano
                )
            except ValueError:
                pass 
        
        todas_fornecedores = Fornecedor.objects.all().order_by('nome')

        meses_com_dados = PedidoCompra.objects.annotate(
            mes_num=ExtractMonth('data_criacao'),
            ano_num=ExtractYear('data_criacao')
        ).values('mes_num', 'ano_num').distinct().order_by('ano_num', 'mes_num')
        
        nomes_meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        lista_meses_dropdown = []
        for item in meses_com_dados:
            mes_num = item['mes_num']
            ano_num = item['ano_num']
            
            valor_get = f"{mes_num}-{ano_num}" 
            texto_exibido = f"{nomes_meses.get(mes_num)} / {ano_num}" 
            
            lista_meses_dropdown.append({
                'value': valor_get,
                'name': texto_exibido
            })

        context = {
            'pedidos': pedidos,
            'todas_fornecedores': todas_fornecedores, 
            'lista_meses_dropdown': lista_meses_dropdown,
            'fornecedor_id_filter': fornecedor_id_filter,
            'month_filter': month_filter, 
        }
        return render(request, 'pedidos.html', context)

class DetalhePedidoView(View):

    def get(self, request, pedido_id):
        pedido = get_object_or_404(PedidoCompra, id=pedido_id)
        itens_do_pedido = pedido.itempedido_set.all() 
        
        context = {
            'pedido': pedido,
            'itens_do_pedido': itens_do_pedido
        }
        return render(request, 'detalhe_pedido.html', context)

class DetalheServicoView(View):
    def get(self, request, id, *args, **kwargs):
        servico = get_object_or_404(Servico, id=id)
        itens_necessarios = ItemServicoNecessario.objects.filter(servico=servico)
        lista_faltantes = []
        if servico.status != 'CONCLUIDO':
            for item in itens_necessarios:
                if item.material.quantidade_estoque < item.quantidade_necessaria:
                    faltante = {
                        'material': item.material.nome,
                        'necessario': item.quantidade_necessaria,
                        'estoque': item.material.quantidade_estoque,
                        'falta': item.quantidade_necessaria - item.material.quantidade_estoque
                    }
                    lista_faltantes.append(faltante)
        context = {
            'servico': servico,
            'itens_necessarios': itens_necessarios,
            'faltantes': lista_faltantes
        }
        return render(request, 'detalhe_servico.html', context)
    
class ReceberPedidoView(View):

    def post(self, request, pedido_id):
        pedido = get_object_or_404(PedidoCompra, id=pedido_id)

        TIPO_MOVIMENTACAO = 'ENTRADA' 

        with transaction.atomic():
            if pedido.status == 'PENDENTE':
                pedido.status = 'RECEBIDO'
                pedido.save()

                itens_pedido = ItemPedido.objects.filter(pedido=pedido)
                for item in itens_pedido:
                    material = item.material
                    quantidade_recebida = item.quantidade_pedida
                
                    material.quantidade_estoque += quantidade_recebida
                    material.save()

                    MovimentacaoEstoque.objects.create(
                        material=material,
                        quantidade=quantidade_recebida,
                        tipo=TIPO_MOVIMENTACAO, 
                        
                        referencia=f"Pedido #{pedido.id}",
                        data_movimentacao=datetime.now()
                    )

        return redirect('pedidos')
    
class RegistrarConsumoView(View):

    def post(self, request, servico_id):
        servico = get_object_or_404(Servico, id=servico_id)

        if servico.status == 'EXECUCAO':
            return redirect('servicos') 

        with transaction.atomic():
            
            itens_necessarios = servico.itemserviconecessario_set.all()
            
            for item in itens_necessarios:
                material = item.material
                quantidade_consumida = item.quantidade_necessaria
                
                material.quantidade_estoque -= quantidade_consumida
                material.save() 
                
                RegistroConsumo.objects.create(
                    material=material,
                    quantidade_consumida=quantidade_consumida,
                    servico=servico,
                    data_consumo=datetime.now()
                )
                MovimentacaoEstoque.objects.create(
                    material=material,
                    quantidade=quantidade_consumida,
                    tipo='SAIDA', 
                    referencia=f"{servico.nome}", 
                    data_movimentacao=datetime.now()
                )
            servico.status = 'EXECUCAO'
            servico.save()

        return redirect('servicos')


class HistoricoMovimentacoesView(View):

    def get(self, request):

        movimentacoes = MovimentacaoEstoque.objects.filter(
            tipo='SAIDA'
        ).order_by('-data_movimentacao')
        
        context = {
            'movimentacoes': movimentacoes
        }
        return render(request, 'historico_movimentacoes.html', context)

class DashboardView(View):
    def get(self, request):
        
        # --- 1. Valor Total do Estoque ---
        # Calculo: Soma de (quantidade_estoque * preco_unitario)
        valor_total_estoque = Material.objects.annotate(
            valor_item=F('quantidade_estoque') * F('preco_unitario')
        ).aggregate(total=Sum('valor_item'))['total'] or 0.00
        # Alterei para 0.00 para formatar corretamente no template

        # --- 2. Projetos em Execução ---
        # **CORREÇÃO:** Usamos o status 'EM EXECUÇÃO' (padrão)
        # Se você usa 'EXECUCAO' sem espaço, use 'EXECUCAO'
        projetos_em_execucao = Servico.objects.filter(status='EM EXECUÇÃO').count() 

        # --- 3. Itens Críticos ---
        itens_criticos = Material.objects.filter(
            quantidade_estoque__lt=5 
        ).select_related('unidade_medida').order_by('quantidade_estoque')
        
        # --- 4. Últimas Movimentações (Melhoria para o Template) ---
        ultimas_movimentacoes = MovimentacaoEstoque.objects.select_related(
            'material'
        ).all().order_by('-data_movimentacao')[:5]

        # Garantir que o template do Dashboard use os campos certos:
        for mov in ultimas_movimentacoes:
            # O template dashboard.html está usando mov.referencia e mov.tipo
            # O campo 'tipo' (ENTRADA/SAIDA) e 'referencia' (Projeto/Pedido) já vêm do modelo MovimentacaoEstoque

            # Se o template dashboard.html estiver usando campos antigos como mov.tipo_movimentacao
            # precisamos renomear o atributo temporariamente aqui:
            mov.tipo_movimentacao = mov.tipo
            mov.origem_destino = mov.referencia
            
        context = {
            'valor_total_estoque': valor_total_estoque,
            'itens_criticos': itens_criticos,
            'total_itens_criticos': itens_criticos.count(),
            'projetos_em_execucao': projetos_em_execucao,
            'ultimas_movimentacoes': ultimas_movimentacoes
        }
        
        return render(request, 'dashboard.html', context)

class ConcluirServicoView(View):
    """Muda o status do serviço para CONCLUIDO."""
    def post(self, request, servico_id):
        # Garante que o método é POST (formulário)
        
        # 1. Recupera o serviço
        servico = get_object_or_404(Servico, pk=servico_id)

        # 2. Verifica se pode ser concluído (apenas se estiver EM EXECUÇÃO)
        if servico.status == 'EXECUCAO':
            # Usa transação para garantir a atomicidade (boa prática)
            try:
                with transaction.atomic():
                    servico.status = 'CONCLUIDO'
                    servico.save()
                    messages.success(request, f"Projeto '{servico.nome}' concluído com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao concluir o projeto: {e}")
        else:
            messages.warning(request, f"O projeto '{servico.nome}' não pode ser concluído, pois está em status '{servico.get_status_display()}'.")

        # 3. Redireciona de volta para a lista de serviços
        return redirect('servicos')

class FornecedoresView(ListView):
    model = Fornecedor
    template_name = 'fornecedores.html'
    context_object_name = 'fornecedores'

class CancelarPedidoView(View):
    def post(self, request, pedido_id):
        pedido = get_object_or_404(PedidoCompra, id=pedido_id)
        
        # Só permite cancelar se for PENDENTE
        if pedido.status == 'PENDENTE':
            pedido.status = 'CANCELADO'
            pedido.save()
            # Opcional: Adicionar mensagem de sucesso
            messages.success(request, f"Pedido #{pedido.id} foi cancelado com sucesso.")
        else:
            # Opcional: Adicionar mensagem de erro
            messages.error(request, f"O pedido #{pedido.id} não pôde ser cancelado, pois está com status {pedido.status}.")

        return redirect('pedidos') # Redireciona para a lista
class HistoricoMovimentacoesView(View):
    def get(self, request):
        
        # 1. INICIALIZAÇÃO E FILTRAGEM
        
        # Otimiza a consulta inicial
        movimentacoes = MovimentacaoEstoque.objects.select_related(
            'material', 'material__unidade_medida'
        ).all().order_by('-data_movimentacao')
        
        todas_categorias = Categoria.objects.all()
        
        search_query = request.GET.get('search')
        categoria_id_filter = request.GET.get('categoria')
        tipo_filter = request.GET.get('tipo') 

        filtros = Q()

        # Filtro por Busca (Nome do Material ou Referência)
        if search_query:
            filtros &= (
                Q(material__nome__icontains=search_query) | 
                Q(referencia__icontains=search_query)       
            )

        # Filtro por Categoria
        if categoria_id_filter:
            filtros &= Q(material__categoria__id=categoria_id_filter)
            
        # Filtro por Tipo (ENTRADA ou SAIDA)
        if tipo_filter:
            filtros &= Q(tipo=tipo_filter.upper()) 

        movimentacoes = movimentacoes.filter(filtros)
        
        # ---------------------------------------------------------------------
        # 2. LÓGICA DE TRATAMENTO DA REFERÊNCIA (FORNECEDOR vs. PROJETO)
        # Cria a variável 'referencia_final' que o template espera
        # ---------------------------------------------------------------------
        
        for mov in movimentacoes:
            
            if mov.tipo == 'ENTRADA':
                # ENTRADA: Tenta buscar o Fornecedor
                
                try:
                    # Tenta extrair o ID do pedido (assume formato: "Pedido #ID...")
                    referencia_parts = mov.referencia.split('#')
                    
                    # Pega o ID (última parte, remove o nome do fornecedor se houver)
                    pedido_id = int(referencia_parts[-1].split('(')[0].strip())
                    
                    # Busca o pedido e o Fornecedor
                    pedido = PedidoCompra.objects.select_related('fornecedor').get(id=pedido_id)
                    
                    # Define a referência final como apenas o nome do Fornecedor
                    mov.referencia_final = pedido.fornecedor.nome 
                    
                except Exception:
                    # Fallback: Se falhar (erro no formato, ID não encontrado), usa a referência original.
                    mov.referencia_final = mov.referencia 
            
            else:
                # SAÍDA: A referência é o nome do Serviço/Projeto. Usa a referência original.
                mov.referencia_final = mov.referencia

        # ---------------------------------------------------------------------
        # 3. CONTEXTO E RENDERIZAÇÃO
        # ---------------------------------------------------------------------

        context = {
            'movimentacoes': movimentacoes,
            'todas_categorias': todas_categorias,
            'search_query': search_query,
            'categoria_id_filter': categoria_id_filter,
            'tipo_filter': tipo_filter,
        }
        
        return render(request, 'historico_movimentacoes.html', context)