import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, NoReturn, ParamSpec, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class BreakerError(Exception):
    def __init__(
        self,
        message: str,
        func_name: str,
        block_time: datetime,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time
        if cause:
            self.__cause__ = cause


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] | None = None,
    ):
        self._validate_args(critical_count, time_to_recover)
        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on or Exception
        self._fail_count = 0
        self._blocked_until: datetime | None = None
        self._func_name = ""

    def __call__(self, func: Callable[P, R_co]) -> Callable[P, R_co]:
        self._func_name = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._check_blocked()
            try:
                result = func(*args, **kwargs)
            except self.triggers_on as err:
                self._handle_error(err)
            self._reset_fail_count()
            return result

        return wrapper

    def _check_blocked(self) -> None:
        if self._blocked_until is None:
            return
        now = datetime.now(UTC)
        if now < self._blocked_until:
            raise BreakerError(
                TOO_MUCH,
                self._func_name,
                self._blocked_until,
            )
        self._blocked_until = None
        self._fail_count = 0

    def _reset_fail_count(self) -> None:
        self._fail_count = 0

    def _handle_error(self, err: Exception) -> NoReturn:
        self._fail_count += 1
        if self._fail_count < self.critical_count:
            raise err
        block_start = datetime.now(UTC)
        self._blocked_until = block_start + timedelta(seconds=self.time_to_recover)
        raise BreakerError(TOO_MUCH, self._func_name, block_start, err) from err

    def _validate_args(self, critical_count: int, time_to_recover: int) -> None:
        errors: list[ValueError] = []
        if critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)


def get_comments(post_id: int) -> Any:
    response = urlopen(
        f"https://jsonplaceholder.typicode.com/comments?postId={post_id}"
    )
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
