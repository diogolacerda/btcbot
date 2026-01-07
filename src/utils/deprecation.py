"""Utility decorators for marking deprecated code."""

import warnings
from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F", bound=Callable[..., object])


def deprecated(message: str, version: str | None = None) -> Callable[[F], F]:
    """Decorator to mark functions/methods as deprecated.

    Args:
        message: Deprecation message explaining the alternative.
        version: Version when this will be removed (optional).

    Returns:
        Decorator function.

    Example:
        @deprecated("Use StrategyRepository instead", version="2.0")
        def old_method():
            pass
    """

    def decorator(func: F) -> F:
        def wrapper(*args: object, **kwargs: object) -> object:
            version_msg = f" (will be removed in version {version})" if version else ""
            warnings.warn(
                f"DEPRECATED: {func.__name__} - {message}{version_msg}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
