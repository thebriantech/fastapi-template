from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv
from .schemas import LoginRequest
from ..services import AuthService
from app.utils.status_code import StatusCode
from app.logs import LogHandler
from ..permissions import access_control

router = APIRouter(prefix="/auth", tags=["Authentication"])


@cbv(router)
class AuthRouter:
    logger = LogHandler.get_logger("auth")
    auth_service = AuthService(logger)

    @router.post("/login")
    @access_control(open=True)
    async def user_login(
            self,
            request: Request,
            login_request: LoginRequest
        ):
        """
        Authenticates a user and returns a JWT access token.

        Args:
            request (Request): The incoming request.
            login_request (LoginRequest): The login credentials.

        Returns:
            JSONResponse: Access token on success, error details on failure.
        """
        self.logger.info("====User Login====")
        result = await self.auth_service.user_login(login_request.model_dump())
        self.logger.info(f"Login result: {result}")
        return JSONResponse(
            status_code=result["http_code"],
            content=result["content"],
            headers={"WWW-Authenticate": "Bearer"}
        )

    @router.get("/check-login")
    @access_control()
    async def check_login(
            self,
            request: Request
        ):
        """
        Validates the current user's authentication token.

        Args:
            request (Request): The incoming request with authorization header.

        Returns:
            JSONResponse: Confirmation that the user is logged in.
        """
        status = StatusCode.SUCCESS.response()
        status["content"]["detail"] = "You are logged in"
        return JSONResponse(
            status_code=status["http_code"],
            content=status["content"],
            headers={"WWW-Authenticate": "Bearer"}
        )
