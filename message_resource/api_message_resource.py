from enum import Enum

class API_KEY_NAME(str, Enum):
    CODE = 'code'
    DOCUMENTATION = 'documentation'
    ERROR = 'error'
    DETAIL = 'detail'
    MESSAGE = 'message'


class ErrorMessages(str, Enum):
    MISSING_CODE = "Missing code in request"
    INVALID_MODEL_CONFIG = "No valid model configuration found"
    INTERNAL_SERVER_ERROR = "Something went wrong"

class SuccessMessages(str, Enum):
    DOCUMENTATION_GENERATED = "Documentation generated successfully"
