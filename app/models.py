
from django.db import models
from django.db.models import Sum, F


class Categoria(models.Model):
    nome = models.CharField(max_length=50, verbose_name="Nome da Categoria")
    def __str__(self):
        return self.nome    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

class UnidadeMedida(models.Model):
    nome = models.CharField(max_length=10, verbose_name="Unidade de Medida")
    def __str__(self):
        return self.nome
    class Meta:
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"

class Material(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Material")
    quantidade_estoque = models.PositiveIntegerField(default=0, verbose_name="Estoque Atual")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário") 
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria")
    unidade_medida = models.ForeignKey(UnidadeMedida, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unidade")

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.upper() 
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
    
    def validar_estoque(self):
        return self.quantidade_estoque >= 0

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"

class Servico(models.Model):
    STATUS_CHOICES = [
        ('PLANEJADO', 'Planejado'),
        ('EXECUCAO', 'Em Execução'),
        ('CONCLUIDO', 'Concluído'),
    ]
    nome = models.CharField(max_length=100, verbose_name="Nome do Serviço/Projeto")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANEJADO', verbose_name="Status")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição do Serviço")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"


class ItemServicoNecessario(models.Model):

    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, verbose_name="Serviço")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="Material Necessário")
    quantidade_necessaria = models.PositiveIntegerField(verbose_name="Quantidade Necessária")

    def __str__(self):
        return f"{self.material.nome} para {self.servico.nome}"
    
    class Meta:
        verbose_name = "Item Necessário"
        verbose_name_plural = "Itens Necessários"
        unique_together = ('servico', 'material')

class Fornecedor(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Fornecedor")
    contato = models.CharField(max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

class PedidoCompra(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('RECEBIDO', 'Recebido'),
        ('CANCELADO', 'Cancelado'),
    ]

    fornecedor = models.ForeignKey(
        'Fornecedor',             
        on_delete=models.SET_NULL,  
        null=True,
        blank=True,
        verbose_name="Fornecedor"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', verbose_name="Status do Pedido")

    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    
    valor_total_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Total Estimado")
    @property
    def get_status_badge_class(self):
        if self.status == 'RECEBIDO':
            return 'success' # Retorna a classe 'badge-success'
        elif self.status == 'CANCELADO':
            return 'danger' # Retorna a classe 'badge-danger'
        else:
            return 'warning'

    def __str__(self):

        fornecedor_nome = self.fornecedor.nome if self.fornecedor else "Sem Fornecedor"
        return f"Pedido #{self.id} - Fornecedor: {fornecedor_nome} - Status: {self.status}"
    
    def confirmar_compra(self):
        if self.status == 'PENDENTE':
            self.status = 'RECEBIDO'
            self.save()
            return True
        return False
    
    def calcular_total(self):
        total = self.itens.aggregate(
            total=Sum(F('quantidade_pedida') * F('preco_estimado_unitario'))
        )['total'] or 0

        self.valor_total_estimado = total
        self.save()

    class Meta:
        verbose_name = "Pedido de Compra"
        verbose_name_plural = "Pedidos de Compra"

class ItemPedido(models.Model):

    pedido = models.ForeignKey(PedidoCompra, on_delete=models.CASCADE, verbose_name="Pedido de Compra")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="Material Solicitado")
    quantidade_pedida = models.PositiveIntegerField(verbose_name="Quantidade Pedida")
    preco_estimado_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário Estimado")

    def __str__(self):
        return f"{self.material.nome} ({self.quantidade_pedida})"
    
    @property
    def preco_unitario(self):
        return self.preco_estimado_unitario

    @property
    def total_item(self):
        """Calcula o total para este item do pedido."""
        return self.quantidade_pedida * self.preco_estimado_unitario
    
    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
        unique_together = ('pedido', 'material')

class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA_MANUAL', 'Saída Manual'),
        ('CONSUMO', 'Consumo por Serviço'), 
    ]
    material = models.ForeignKey(Material, on_delete=models.PROTECT, verbose_name="Material Movimentado")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Movimentação")
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade")
    data_movimentacao = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora")
    referencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referência (Pedido/Ajuste)")

    def __str__(self):
        return f"{self.tipo} de {self.quantidade} unidades de {self.material.nome}"

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"


class RegistroConsumo(models.Model):

    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, verbose_name="Serviço")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, verbose_name="Material Consumido")
    quantidade_consumida = models.PositiveIntegerField(verbose_name="Quantidade Consumida")
    data_consumo = models.DateTimeField(auto_now_add=True, verbose_name="Data do Consumo")

    def __str__(self):
        return f"Consumo de {self.quantidade_consumida} em {self.servico.nome}"

    class Meta:
        verbose_name = "Registro de Consumo"
        verbose_name_plural = "Registros de Consumo"
