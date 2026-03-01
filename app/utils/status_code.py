from enum import Enum

class StatusCode(Enum):
    UNKNOWN_ERROR = {
        "http_code": 500,
        "content": {
            "code": "ERR_UNKNOWN",
            "description":"Some thing wrong in backend server please contact administrator"
        }
    }
    SUCCESS = {
        "http_code": 200,
        "content":{
            "code": "SUCCESS",
            "description": "Success"
        }
    }
    
    INSERT_ERROR = {
        "http_code": 400,
        "content": {
            "code": "AISS_00001",
            "description": "Error when insert or update cam"
        }
    }
    DB_ERROR = {
        "http_code": 400,
        "content": {
            "code": "AISS_00002",
            "description": "Insert record into database error"
        }
    }
    FIND_ITEM_ERROR = {
        "http_code": 400,
        "content": {
            "code": "AISS_00003",
            "description": "Find item in database error"
        }
    }
    ITEM_NOT_FOUND_ERROR = {
        "http_code": 400,
        "content": {
            "code": "AISS_00004",
            "description": "Does not found any item in database"
        }
    }
    INSTANCE_NOT_FOUND_ERROR = {
        "http_code": 400,
        "content": {
            "code": "AISS_00005",
            "description": "Instance not found"
        }
    }
    NOT_SUCCESS_ALL = {
        "http_code": 200,
        "content": {
            "code": "AISS_00006",
            "description": "Not Success All"
        }
    }
    NOT_SUCCESS = {
        "http_code": 400,
        "content": {
            "code": "AISS_00007",
            "description": "Not Success"
        }
    }
    RECEIVED = {
        "http_code": 200,
        "content":{
            "code": "AISS_00008",
            "description": "Received"
        }
    }
    ITEM_EXIST_ERROR = {
        "http_code": 400,
        "content": {
            "code": "AISS_00009",
            "description": "Item existed in database"
        }
    }

    UNAUTHORIZED =  {
        "http_code": 401,
        "content": {
            "code": "AISS_00010",
            "description": "Unauthorized"
        }
    }

    # Auth error codes used by permissions / access_control
    ERR_000001 = {
        "http_code": 400,
        "detail": "Invalid request: missing request object"
    }
    ERR_000002 = {
        "http_code": 401,
        "detail": "Missing authorization header"
    }
    ERR_000003 = {
        "http_code": 401,
        "detail": "Could not validate credentials"
    }
    ERR_000004 = {
        "http_code": 403,
        "detail": "Insufficient permissions: superuser required"
    }
    ERR_000005 = {
        "http_code": 401,
        "detail": "Token has expired"
    }