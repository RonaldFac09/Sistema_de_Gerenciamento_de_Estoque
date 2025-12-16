from django.contrib import admin
from .models import (
    Categoria, UnidadeMedida, MovimentacaoEstoque, RegistroConsumo, Material,
    ItemServicoNecessario, Servico, ItemPedido, PedidoCompra, Fornecedor 
)

# ----------------------------------------------------
# 1. ADMINS COM CLASSE E DECORADOR @admin.register
# ----------------------------------------------------

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade_estoque', 'preco_unitario', 'categoria', 'unidade_medida')
    search_fields = ('nome',)
    list_filter = ('categoria', 'unidade_medida')


class ItemServicoNecessarioInline(admin.TabularInline):
    model = ItemServicoNecessario
    extra = 1
    fields = ('material', 'quantidade_necessaria')
    autocomplete_fields = ['material'] 

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status')
    inlines = [ItemServicoNecessarioInline] 


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1 
    fields = ('material', 'quantidade_pedida', 'preco_estimado_unitario')
    autocomplete_fields = ['material']

@admin.register(PedidoCompra)
class PedidoCompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_criacao', 'fornecedor', 'status')
    fields = ('fornecedor', 'status') 
    inlines = [ItemPedidoInline]
    ordering = ('-data_criacao',) 
    list_filter = ('status', 'fornecedor')
    search_fields = ('fornecedor__nome', 'id')


# ----------------------------------------------------
# 3. REGISTROS SIMPLES (Garantir que sejam chamados por último)
# ----------------------------------------------------
admin.site.register(Categoria)
admin.site.register(UnidadeMedida)
admin.site.register(MovimentacaoEstoque)
admin.site.register(RegistroConsumo)

# NOTE: Fornecedor foi registrado aqui, mas vou movê-lo para o topo para evitar o conflito, 
# se for a causa do erro com o PedidoCompra.
admin.site.register(Fornecedor) # << Mantenha este registro

