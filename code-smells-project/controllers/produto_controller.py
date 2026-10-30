from config.constants import CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from models import produto_model
from utils.exceptions import NotFoundError, ValidationError


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _validar_produto(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    descricao = dados.get("descricao", "")
    categoria = dados.get("categoria", "geral")

    if not isinstance(nome, str) or not isinstance(descricao, str):
        raise ValidationError("Nome e descrição devem ser texto")
    if not _eh_numero(preco) or not _eh_numero(estoque):
        raise ValidationError("Preço e estoque devem ser numéricos")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))
    return nome, descricao, preco, int(estoque), categoria


def _obter_ou_404(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def listar():
    return produto_model.listar_todos()


def buscar(produto_id):
    return _obter_ou_404(produto_id)


def criar(dados):
    nome, descricao, preco, estoque, categoria = _validar_produto(dados)
    return {"id": produto_model.criar(nome, descricao, preco, estoque, categoria)}


def atualizar(produto_id, dados):
    _obter_ou_404(produto_id)
    nome, descricao, preco, estoque, categoria = _validar_produto(dados)
    produto_model.atualizar(produto_id, nome, descricao, preco, estoque, categoria)


def deletar(produto_id):
    _obter_ou_404(produto_id)
    produto_model.deletar(produto_id)


def _converter_preco(valor, rotulo):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{rotulo} deve ser numérico") from None


def pesquisar(args):
    return produto_model.pesquisar(
        termo=args.get("q", ""),
        categoria=args.get("categoria"),
        preco_min=_converter_preco(args.get("preco_min"), "preco_min"),
        preco_max=_converter_preco(args.get("preco_max"), "preco_max"),
    )
