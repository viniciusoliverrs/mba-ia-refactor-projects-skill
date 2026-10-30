import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.helpers import format_date, utcnow

HASH_PREFIXES = ("scrypt:", "pbkdf2:")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Serializa o usuário sem jamais expor o hash de senha."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": format_date(self.created_at),
        }

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        if self.password and self.password.startswith(HASH_PREFIXES):
            return check_password_hash(self.password, pwd)
        legacy_md5 = hashlib.md5(pwd.encode()).hexdigest()
        return hmac.compare_digest(self.password or "", legacy_md5)

    def is_admin(self):
        return self.role == "admin"
