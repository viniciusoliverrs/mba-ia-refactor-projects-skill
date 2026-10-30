from datetime import timedelta

from sqlalchemy import case, func

from config.constants import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    VALID_STATUSES,
)
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.exceptions import NotFoundError
from utils.helpers import calculate_percentage, format_date, utcnow


def get_summary_report():
    now = utcnow()
    total_users = db.session.query(func.count(User.id)).scalar() or 0
    total_categories = db.session.query(func.count(Category.id)).scalar() or 0

    status_counts = {status: 0 for status in VALID_STATUSES}
    for status, count in db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all():
        status_counts[status] = count

    total_tasks = sum(status_counts.values())

    priority_counts = {label: 0 for label in PRIORITY_LABELS.values()}
    for priority, count in db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all():
        label = PRIORITY_LABELS.get(priority)
        if label:
            priority_counts[label] = count

    all_tasks = Task.query.all()
    overdue_list = [
        {
            "id": task.id,
            "title": task.title,
            "due_date": format_date(task.due_date),
            "days_overdue": (now - task.due_date).days,
        }
        for task in all_tasks
        if task.is_overdue()
    ]

    seven_days_ago = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(Task.status == "done", Task.updated_at >= seven_days_ago).count()

    user_rows = (
        db.session.query(
            User.id,
            User.name,
            func.count(Task.id).label("total_tasks"),
            func.coalesce(func.sum(case((Task.status == "done", 1), else_=0)), 0).label("completed_tasks"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .all()
    )

    user_stats = [
        {
            "user_id": user_id,
            "user_name": user_name,
            "total_tasks": user_total,
            "completed_tasks": int(completed),
            "completion_rate": calculate_percentage(int(completed), user_total),
        }
        for user_id, user_name, user_total, completed in user_rows
    ]

    return {
        "generated_at": format_date(now),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": status_counts,
        "tasks_by_priority": priority_counts,
        "overdue": {
            "count": len(overdue_list),
            "tasks": overdue_list,
        },
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }


def get_user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    status_counts = {status: 0 for status in VALID_STATUSES}
    overdue = 0
    high_priority = 0

    for task in tasks:
        if task.status in status_counts:
            status_counts[task.status] += 1
        if task.priority <= HIGH_PRIORITY_THRESHOLD:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    done = status_counts["done"]
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": status_counts["pending"],
            "in_progress": status_counts["in_progress"],
            "cancelled": status_counts["cancelled"],
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": calculate_percentage(done, total),
        },
    }

