from config.constants import MAX_PRIORITY, MIN_PRIORITY, TERMINAL_STATUSES, VALID_STATUSES
from database import db
from utils.helpers import format_date, utcnow


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="pending")
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref=db.backref("tasks", cascade="all, delete-orphan"))
    category = db.relationship("Category", backref="tasks")

    def to_dict(self, include_overdue=False, include_relations=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": format_date(self.created_at),
            "updated_at": format_date(self.updated_at),
            "due_date": format_date(self.due_date),
            "tags": self.tags.split(",") if self.tags else [],
        }
        if include_overdue:
            data["overdue"] = self.is_overdue()
        if include_relations:
            data["user_name"] = self.user.name if self.user else None
            data["category_name"] = self.category.name if self.category else None
        return data

    def validate_status(self, new_status):
        return new_status in VALID_STATUSES

    def validate_priority(self, priority):
        return isinstance(priority, int) and MIN_PRIORITY <= priority <= MAX_PRIORITY

    def is_overdue(self):
        return bool(
            self.due_date
            and self.due_date < utcnow()
            and self.status not in TERMINAL_STATUSES
        )
