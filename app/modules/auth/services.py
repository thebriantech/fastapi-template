from .v1.schemas import LoginResponse
from app.modules.user.models import get_user_model
from app.utils.status_code import StatusCode
from .utils import verify_password, create_access_token


class AuthService:
    def __init__(self, logger):
        self.logger = logger

    async def user_login(self, user_data):
        try:
            UserModel = get_user_model()
            user = await UserModel.find_one({"username": user_data["username"]})
            if not user["status"] or len(user.get("result", [])) == 0:
                self.logger.error(f"Username {user_data['username']} does not exist")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.response()
                status["content"]["detail"] = f"Username {user_data['username']} does not exist"
                return status

            # Verify password
            stored_hash = user["result"].get("hashed_password", "")
            if not verify_password(user_data["password"], stored_hash):
                self.logger.error(f"Invalid password for {user_data['username']}")
                status = StatusCode.UNAUTHORIZED.response()
                status["content"]["detail"] = "Invalid username or password"
                return status

            access_token = create_access_token({"sub": user["result"]["username"]})

            self.logger.success("Login success")
            status = StatusCode.SUCCESS.response()
            login_response = LoginResponse(access_token=access_token)
            status["content"]["detail"] = login_response.model_dump()
            return status

        except Exception as e:
            self.logger.error(e)
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status
