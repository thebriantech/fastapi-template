import inspect
import jwt

from functools import wraps
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi.exceptions import HTTPException
from app.configs import ConfigManager
from app.modules.user.models import get_user_model
from app.logs import LogHandler
from app.utils.status_code import StatusCode


# Decorator for authentication
class access_control:
    def __init__(
            self,
            superuser: bool = False,
            open: bool = False
        ):
        """
        Args:
            superuser (bool, optional): Require superuser. Defaults to False.
            open (bool, optional): Skip auth entirely. Defaults to False.
        """
        self.token = None
        self.request = None
        self.open = open
        self.superuser = superuser
        self.logger = LogHandler.get_logger("auth")

    def __call__(self, func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if self.open:
                    return await func(*args, **kwargs)
                request = kwargs.get("request")
                if not request:
                    self.logger.error("Get None request")
                    raise HTTPException(
                        status_code=StatusCode.ERR_000001.value["http_code"],
                        detail=StatusCode.ERR_000001.value["detail"],
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                auth_str = request.headers.get("authorization")
                if auth_str is None:
                    raise HTTPException(
                        status_code=StatusCode.ERR_000002.value["http_code"],
                        detail=StatusCode.ERR_000002.value["detail"],
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                auth_strs = auth_str.split(" ")
                if len(auth_strs) != 2:
                    self.logger.error("Wrong bearer token format")
                    raise HTTPException(
                        status_code=StatusCode.ERR_000003.value["http_code"],
                        detail=StatusCode.ERR_000003.value["detail"],
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                elif auth_strs[0] != "Bearer":
                    self.logger.error("Wrong bearer token format the format must be 'Bearer {token}'")
                    raise HTTPException(
                        status_code=StatusCode.ERR_000003.value["http_code"],
                        detail=StatusCode.ERR_000003.value["detail"],
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    token = auth_strs[1]
                    valid = self.verify(token)
                    if not valid["status"]:
                        raise HTTPException(
                            status_code=valid["http_code"],
                            detail=valid["detail"],
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if self.open:
                    return func(*args, **kwargs)
                else:
                    request = kwargs.get("request")
                    if not request:
                        self.logger.error("Get None request")
                        raise HTTPException(
                            status_code=StatusCode.ERR_000001.value["http_code"],
                            detail=StatusCode.ERR_000001.value["detail"],
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                    auth_str = request.headers.get("authorization")
                    if auth_str is None:
                        raise HTTPException(
                            status_code=StatusCode.ERR_000002.value["http_code"],
                            detail=StatusCode.ERR_000002.value["detail"],
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                    auth_strs = auth_str.split(" ")
                    if len(auth_strs) != 2:
                        self.logger.error("Wrong bearer token format")
                        raise HTTPException(
                            status_code=StatusCode.ERR_000003.value["http_code"],
                            detail=StatusCode.ERR_000003.value["detail"],
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                    elif auth_strs[0] != "Bearer":
                        self.logger.error("Wrong bearer token format the format must be 'Bearer {token}'")
                        raise HTTPException(
                            status_code=StatusCode.ERR_000003.value["http_code"],
                            detail=StatusCode.ERR_000003.value["detail"],
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                    else:
                        token = auth_strs[1]
                        valid = self.verify(token)
                        if not valid["status"]:
                            raise HTTPException(
                                status_code=valid["http_code"],
                                detail=valid["detail"],
                                headers={"WWW-Authenticate": "Bearer"},
                            )
                        else:
                            return func(*args, **kwargs)
            return sync_wrapper

    def verify(self, token):
        try:
            payload = jwt.decode(token,
                                ConfigManager.config.auth_secret_key,
                                algorithms=[ConfigManager.config.auth_algorithm])
            username: str = payload.get("sub")
            if username is None:
                self.logger.error("Username is None")
                return {
                    "status": False,
                    "http_code": StatusCode.ERR_000003.value["http_code"],
                    "detail": StatusCode.ERR_000003.value["detail"]
                }
            UserModel = get_user_model()
            import asyncio
            import concurrent.futures
            coro = UserModel.find_one({"username": username})
            if inspect.isawaitable(coro):
                try:
                    asyncio.get_running_loop()
                    # Running inside an async context — run in a new thread
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, coro)
                        user = future.result(timeout=10)
                except RuntimeError:
                    # No running loop — run directly
                    user = asyncio.run(coro)
            else:
                user = coro
            if not user["status"] or len(user.get("result", [])) == 0:
                self.logger.error(f"Decoded username {username} but username does not exist")
                return {
                    "status": False,
                    "http_code": StatusCode.ERR_000003.value["http_code"],
                    "detail": StatusCode.ERR_000003.value["detail"]
                }
            if self.superuser and username != ConfigManager.config.superuser_username:
                self.logger.error(f"Decoded username {username} but this endpoint required superuser")
                return {
                    "status": False,
                    "http_code": StatusCode.ERR_000004.value["http_code"],
                    "detail": StatusCode.ERR_000004.value["detail"]
                }
            # Expiration is already verified by jwt.decode above (raises ExpiredSignatureError).
            return {
                "status": True,
                "username": username
            }
        except ExpiredSignatureError:
            self.logger.error("Expired token")
            return {
                "status": False,
                "http_code": StatusCode.ERR_000005.value["http_code"],
                "detail": StatusCode.ERR_000005.value["detail"]
            }
        except InvalidTokenError as e:
            self.logger.error(f"InvalidTokenError: {e}")
            return {
                "status": False,
                "http_code": StatusCode.ERR_000003.value["http_code"],
                "detail": StatusCode.ERR_000003.value["detail"]
            }
