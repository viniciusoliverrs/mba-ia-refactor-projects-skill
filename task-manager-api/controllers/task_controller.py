import logging

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from config.constants import (
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    TERMINAL_STATUSES,
    VALID_STATUSES,
)
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.exceptions import AppError, NotFoundError, ValidationError
from utils.helpers import calculate_percentage, parse_date, serialize_tags, utcnow

logger = logging.getLogger(__name__)


def _validate_title(title):
    if not isinstance(title, str) or not title:
        raise ValidationError("Título é obrigatório")
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError("Título muito curto")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError("Título muito longo")
    return title


def _validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError("Status inválido")
    return status


def _validate_priority(priority):
    if not isinstance(priority, int) or isinstance(priority, bool) or priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError("Prioridade deve ser entre 1 e 5")
    return priority


def _ensure_user_exists(user_id):
    if user_id is not None:
        if not db.session.get(User, user_id):
            raise NotFoundError("Usuário não encontrado")


def _ensure_category_exists(category_id):
    if category_id is not None:
        if not db.session.get(Category, category_id):
            raise NotFoundError("Categoria não encontrada")


def _parse_due_date(due_date_str, error_message="Formato de data inválido. Use YYYY-MM-DD"):
    if not due_date_str:
        return None
    parsed = parse_date(due_date_str)
    if not parsed:
        raise ValidationError(error_message)
    return parsed


def list_tasks():
    tasks = (
        Task.query.options(joinedload(Task.user), joinedload(Task.category))
        .all()
    )
    return [task.to_dict(include_overdue=True, include_relations=True) for task in tasks]


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    return task.to_dict(include_overdue=True)


def create_task(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")

    title = _validate_title(data.get("title"))
    description = data.get("description", "")
    status = _validate_status(data.get("status", "pending"))
    priority = _validate_priority(data.get("priority", DEFAULT_PRIORITY))
    user_id = data.get("user_id")
    category_id = data.get("category_id")

    _ensure_user_exists(user_id)
    _ensure_category_exists(category_id)

    task = Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
        due_date=_parse_due_date(data.get("due_date")),
        tags=serialize_tags(data.get("tags")),
    )

    try:
        db.session.add(task)
        db.session.commit()
        logger.info("Task criada: %s - %s", task.id, task.title)
        return task.to_dict()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao criar task: %s", exc)
        raise AppError("Erro ao criar task") from exc


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")

    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")

    if "title" in data:
        task.title = _validate_title(data["title"])
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        task.status = _validate_status(data["status"])
    if "priority" in data:
        task.priority = _validate_priority(data["priority"])
    if "user_id" in data:
        _ensure_user_exists(data["user_id"])
        task.user_id = data["user_id"]
    if "category_id" in data:
        _ensure_category_exists(data["category_id"])
        task.category_id = data["category_id"]
    if "due_date" in data:
        task.due_date = _parse_due_date(data["due_date"], "Formato de data inválido") if data["due_date"] else None
    if "tags" in data:
        task.tags = serialize_tags(data["tags"])

    task.updated_at = utcnow()

    try:
        db.session.commit()
        logger.info("Task atualizada: %s", task.id)
        return task.to_dict()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao atualizar task %s: %s", task_id, exc)
        raise AppError("Erro ao atualizar") from exc


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task não encontrada")

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info("Task deletada: %s", task_id)
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao deletar task %s: %s", task_id, exc)
        raise AppError("Erro ao deletar") from exc


def _parse_optional_int(value, label):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError(f"{label} inválido") from exc


def search_tasks(args):
    query_text = args.get("q", "")
    status = args.get("status", "")
    priority = _parse_optional_int(args.get("priority"), "priority")
    user_id = _parse_optional_int(args.get("user_id"), "user_id")

    tasks_query = Task.query
    if query_text:
        tasks_query = tasks_query.filter(
            db.or_(
                Task.title.like(f"%{query_text}%"),
                Task.description.like(f"%{query_text}%"),
            )
        )
    if status:
        tasks_query = tasks_query.filter(Task.status == status)
    if priority is not None:
        tasks_query = tasks_query.filter(Task.priority == priority)
    if user_id is not None:
        tasks_query = tasks_query.filter(Task.user_id == user_id)

    return [task.to_dict() for task in tasks_query.all()]


def get_task_stats():
    status_rows = (
        db.session.query(Task.status, func.count(Task.id))
        .group_by(Task.status)
        .all()
    )
    counts_by_status = {status: 0 for status in VALID_STATUSES}
    for status, count in status_rows:
        counts_by_status[status] = count

    total = sum(counts_by_status.values())
    done = counts_by_status["done"]

    overdue_count = (
        Task.query.filter(
            Task.due_date.isnot(None),
            Task.due_date < utcnow(),
            Task.status.notin_(TERMINAL_STATUSES),
        ).count()
    )

    return {
        "total": total,
        "pending": counts_by_status["pending"],
        "in_progress": counts_by_status["in_progress"],
        "done": done,
        "cancelled": counts_by_status["cancelled"],
        "overdue": overdue_count,
        "completion_rate": calculate_percentage(done, total),
    }
