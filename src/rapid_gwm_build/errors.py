"""Custom exceptions for rmb."""


class RMBError(Exception):
    """Base exception for all rmb errors."""


class ConfigError(RMBError):
    """Error in YAML configuration parsing or validation."""


class BuildError(RMBError):
    """Error during node build execution."""


class ValidationError(RMBError):
    """Error during config/graph validation (no build attempted)."""
