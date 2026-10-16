import re
import unicodedata
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from pymongo.errors import DuplicateKeyError
from app.db.mongo import now
from app.core.errors import require, DomainError
from app.models.documents import UserDocument

HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
DUMMY_HASH = HASHER.hash("unavailable-account-timing-placeholder")


def normalize_username(username):
    username = unicodedata.normalize("NFKC", username).strip().casefold()
    require(re.fullmatch(r"[a-z0-9_\-\u4e00-\u9fff]{3,40}", username) is not None, "用户名须为3..40位中英文、数字、下划线或短横线")
    return username


class AuthService:
    def __init__(self, db): self.db = db

    def register(self, username, password):
        username = normalize_username(username)
        require(10 <= len(password) <= 128, "密码须为10..128字符")
        record = {"username": username, "passwordHash": HASHER.hash(password), "createdAt": now(), "schemaVersion": 1, "sessionVersion": 1}
        record = UserDocument.model_validate(record).to_bson()
        try: self.db.users.insert_one(record)
        except DuplicateKeyError: raise DomainError("USERNAME_EXISTS", "用户名已存在", 409)
        return record

    def login(self, username, password):
        username = normalize_username(username)
        record = self.db.users.find_one({"username": username})
        try:
            HASHER.verify(record["passwordHash"] if record else DUMMY_HASH, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            raise DomainError("INVALID_CREDENTIALS", "用户名或密码错误", 401)
        require(record is not None, "用户名或密码错误", "INVALID_CREDENTIALS", 401)
        return record
