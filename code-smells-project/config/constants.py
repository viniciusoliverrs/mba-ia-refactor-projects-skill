"""Constantes de domínio (antes espalhadas como magic numbers pelo código)."""

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
STATUS_PEDIDO = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)
