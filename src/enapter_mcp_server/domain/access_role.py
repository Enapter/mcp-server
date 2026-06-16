import enum


class AccessRole(enum.Enum):
    READONLY = "readonly"
    USER = "user"
    OWNER = "owner"
    INSTALLER = "installer"
    SYSTEM = "system"
    VENDOR = "vendor"
