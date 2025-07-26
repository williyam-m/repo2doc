from enum import Enum
from rest_framework import status

class API_KEY_NAME(str, Enum):
    CODE = 'code'
    DOCUMENTATION = 'documentation'
    ERROR = 'error'
    DETAIL = 'detail'
    MESSAGE = 'message'
    RAW_CONTENT = 'raw_content'
    PATH = 'path'


class ErrorMessages(str, Enum):
    MISSING_CODE = "Missing code in request"
    INVALID_MODEL_CONFIG = "No valid model configuration found"
    INTERNAL_SERVER_ERROR = "Something went wrong"
    INVALID_FILE_TYPE = "Invalid file type. Please upload a zip file."
    FILE_NOT_FOUND = "File not found"

class SuccessMessages(str, Enum):
    DOCUMENTATION_GENERATED = "Documentation generated successfully"
