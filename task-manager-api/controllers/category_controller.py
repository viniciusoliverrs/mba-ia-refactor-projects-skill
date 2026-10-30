import logging

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from config.constants import DEFAULT_COLOR
from database import db
from models.category import Category
from models.task import Task
from utils.exceptions import AppError, NotFoundError, ValidationError
from utils.helpers import is_valid_color

logger = logging.getLogger(__name__)


def list_categories():
    rows = (
        db.session.query(Category, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .all()
    )
    result = []
    for category, task_count in rows:
        category_data = category.to_dict()
        category_data["task_count"] = task_count
        result.append(category_data)
    return result


def create_category(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")

    name = data.get("name")
    if not name:
        raise ValidationError("Nome é obrigatório")

    color = data.get("color", DEFAULT_COLOR)
    if not is_valid_color(color):
        raise ValidationError("Cor inválida")

    category = Category(
        name=name,
        description=data.get("description", ""),
        color=color,
    )

    try:
        db.session.add(category)
        db.session.commit()
        return category.to_dict()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao criar categoria: %s", exc)
        raise AppError("Erro ao criar categoria") from exc


def update_category(cat_id, data):
    category = db.session.get(Category, cat_id)
    if not category:
        raise NotFoundError("Categoria não encontrada")

    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")

    if "name" in data:
        if not data["name"]:
            raise ValidationError("Nome é obrigatório")
        category.name = data["name"]
    if "description" in data:
        category.description = data["description"]
    if "color" in data:
        if not is_valid_color(data["color"]):
            raise ValidationError("Cor inválida")
        category.color = data["color"]

    try:
        db.session.commit()
        return category.to_dict()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao atualizar categoria %s: %s", cat_id, exc)
        raise AppError("Erro ao atualizar") from exc


def delete_category(cat_id):
    category = db.session.get(Category, cat_id)
    if not category:
        raise NotFoundError("Categoria não encontrada")

    try:
        Task.query.filter_by(category_id=cat_id).update({"category_id": None})
        db.session.delete(category)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao deletar categoria %s: %s", cat_id, exc)
        raise AppError("Erro ao deletar") from exc
