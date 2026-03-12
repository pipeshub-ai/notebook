"""
Shared logging for the agent_example sample.

Simple console logger: prefixes lines with [INFO], [WARN], [ERROR].
Use logger.json(label, value) to pretty-print API responses or objects for debugging.
"""
import json


def _format_message(level: str, message: str, *args: object) -> None:
    """Print a single line prefixed by [LEVEL]."""
    prefix = f"[{level.upper()}]"
    if args:
        print(prefix, message, *args)
    else:
        print(prefix, message)


class _Logger:
    """Minimal logger used by all examples and src/index.py."""

    @staticmethod
    def info(message: str, *args: object) -> None:
        """Log an informational message. Extra args are printed after the message."""
        _format_message("INFO", message, *args)

    @staticmethod
    def warn(message: str, *args: object) -> None:
        """Log a warning."""
        _format_message("WARN", message, *args)

    @staticmethod
    def error(message: str, *args: object) -> None:
        """Log an error (does not raise; call sys.exit(1) in the caller if needed)."""
        _format_message("ERROR", message, *args)

    @staticmethod
    def json(label: str, value: object) -> None:
        """Log a label and a value; if value is not str, pretty-print as JSON (indent=2)."""
        formatted = json.dumps(value, indent=2, default=str) if not isinstance(value, str) else value
        print(f"[INFO] {label}\n{formatted}")


# Singleton used across the project
logger = _Logger()
