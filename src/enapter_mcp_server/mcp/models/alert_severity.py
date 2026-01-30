import enum


class AlertSeverity(enum.StrEnum):
    """Represents the severity level of an alert.

    Attributes:
        INFO: Device may require user attention.
        WARNING: Device is operational but requires user attention.
        ERROR: Device is not operational due to error.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
