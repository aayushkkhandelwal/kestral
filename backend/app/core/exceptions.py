class DomainException(Exception):
    """Base class for all domain layer exceptions."""
    def __init__(self, message: str, error_code: str = "ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

AppException = DomainException

class EntityNotFoundException(DomainException):
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(f"{entity_name} with identifier '{identifier}' was not found.", "NOT_FOUND")
        self.entity_name = entity_name
        self.identifier = identifier

NotFoundException = EntityNotFoundException

class AuthenticationFailedException(DomainException):
    def __init__(self, message: str = "Invalid credentials or expired authentication session."):
        super().__init__(message, "UNAUTHORIZED")

UnauthorizedException = AuthenticationFailedException

class PermissionDeniedException(DomainException):
    def __init__(self, message: str = "You do not have permission to perform this forensic action."):
        super().__init__(message, "FORBIDDEN")

ForbiddenException = PermissionDeniedException

class DuplicateEntityException(DomainException):
    def __init__(self, entity_name: str, field: str, value: str):
        super().__init__(f"{entity_name} with {field}='{value}' already exists.", "CONFLICT")
        self.entity_name = entity_name
        self.field = field
        self.value = value

ConflictException = DuplicateEntityException

class ValidationException(DomainException):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")

class StorageException(DomainException):
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_ERROR")

class BusinessRuleException(DomainException):
    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_RULE_VIOLATION")

class EvidenceLockedException(DomainException):
    def __init__(self, evidence_id: str, case_count: int):
        super().__init__(
            f"Evidence '{evidence_id}' cannot be deleted because it is mapped to {case_count} active case(s).",
            "EVIDENCE_LOCKED"
        )
        self.evidence_id = evidence_id
        self.case_count = case_count
