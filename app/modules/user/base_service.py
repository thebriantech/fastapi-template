"""
User services — identical logic, parameterised by model class.

Each database backend gets the same register/delete operations so you can
compare behaviour side-by-side from Swagger UI.
"""

from __future__ import annotations

from app.utils.status_code import StatusCode
from app.modules.auth.utils import get_password_hash


class UserService:
    """
    Generic user service for any async ``BaseDocument`` subclass.

    Instantiate once per backend:

        pg_service = UserService(UserPg, "PostgreSQL", logger)
    """

    def __init__(self, model, backend_label: str, logger):
        self.model = model
        self.label = backend_label
        self.logger = logger

    async def user_register(self, data: dict = None):
        try:
            hashed_password = get_password_hash(data["password"])
            user = await self.model.find_one({"username": data["username"]})
            if user["status"] and len(user["result"]) != 0:
                self.logger.error(f"[{self.label}] Username {data['username']} already exists")
                status = StatusCode.ITEM_EXIST_ERROR.response()
                status["content"]["detail"] = f"Username {data['username']} already exists"
                return status
            await self.model.insert_one({
                "username": data["username"],
                "user_group": data["user_group"],
                "email": data["email"],
                "hashed_password": hashed_password,
            })
            self.logger.success(f"[{self.label}] Register success")
            status = StatusCode.SUCCESS.response()
            status["content"]["detail"] = {
                "backend": self.label,
                "message": "Register success",
            }
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status

    async def user_delete(self, username: str = None):
        try:
            user = await self.model.find_one({"username": username})
            if not user["status"]:
                self.logger.error(f"[{self.label}] Username {username} does not exist")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.response()
                status["content"]["detail"] = f"Username {username} does not exist"
                return status
            result = await self.model.delete_one({"username": username})
            if not result["status"]:
                self.logger.error(f"[{self.label}] {result.get('error', 'Unknown error')}")
                status = StatusCode.UNKNOWN_ERROR.response()
                status["content"]["detail"] = result.get("error", "Unknown error")
                return status
            self.logger.success(f"[{self.label}] Delete user {username} success")
            status = StatusCode.SUCCESS.response()
            status["content"]["detail"] = f"Delete user {username} success"
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status
