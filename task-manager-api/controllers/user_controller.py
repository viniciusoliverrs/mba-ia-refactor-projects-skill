import logging

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from config.constants import MIN_PASSWORD_LENGTH, VALID_ROLES
from config.settings import Settings
from database import db
from models.task import Task
from models.user import HASH_PREFIXES, User
from utils.exceptions import (
    AppError,
    AuthError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from utils.helpers import format_date, validate_email

logger = logging.getLogger(__name__)


def _generate_auth_token(user_id):
    serializer = URLSafeTimedSerializer(Settings.SECRET_KEY)
    return serializer.dumps({"user_id": user_id}, salt="task-manager-auth")


def list_users():
    rows = (
        db.session.query(User, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .all()
    )
    result = []
    for user, task_count in rows:
        user_data = user.to_dict()
        user_data["task_count"] = task_count
        result.append(user_data)
    return result


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    data = user.to_dict()
    tasks = Task.query.filter_by(user_id=user_id).all()
    data["tasks"] = [task.to_dict() for task in tasks]
    return data


def create_user(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not name:
        raise ValidationError("Nome é obrigatório")
    if not email:
        raise ValidationError("Email é obrigatório")
    if not password:
        raise ValidationError("Senha é obrigatória")
    if not validate_email(email):
        raise ValidationError("Email inválido")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError("Senha deve ter no mínimo 4 caracteres")

    if User.query.filter_by(email=email).first():
        raise ConflictError("Email já cadastrado")

    if role not in VALID_ROLES:
        raise ValidationError("Role inválido")

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        logger.info("Usuário criado: %s - %s", user.id, user.name)
        return user.to_dict()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao criar usuário: %s", exc)
        raise AppError("Erro ao criar usuário") from exc


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")

    if "name" in data:
        user.name = data["name"]

    if "email" in data:
        if not validate_email(data["email"]):
            raise ValidationError("Email inválido")
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            raise ConflictError("Email já cadastrado")
        user.email = data["email"]

    if "password" in data:
        if len(data["password"]) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Senha muito curta")
        user.set_password(data["password"])

    if "role" in data:
        if data["role"] not in VALID_ROLES:
            raise ValidationError("Role inválido")
        user.role = data["role"]

    if "active" in data:
        user.active = data["active"]

    try:
        db.session.commit()
        return user.to_dict()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao atualizar usuário %s: %s", user_id, exc)
        raise AppError("Erro ao atualizar") from exc


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    try:
        db.session.delete(user)
        db.session.commit()
        logger.info("Usuário deletado: %s", user_id)
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Erro ao deletar usuário %s: %s", user_id, exc)
        raise AppError("Erro ao deletar") from exc


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    tasks = Task.query.filter_by(user_id=user_id).all()
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "created_at": format_date(task.created_at),
            "due_date": format_date(task.due_date),
            "overdue": task.is_overdue(),
        }
        for task in tasks
    ]


def login(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")

    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthError("Credenciais inválidas")

    if not user.active:
        raise ForbiddenError("Usuário inativo")

    if not user.password.startswith(HASH_PREFIXES):
        user.set_password(password)
        db.session.commit()

    return {
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": _generate_auth_token(user.id),
    }

