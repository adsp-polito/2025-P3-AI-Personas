"""Shared progress bar helpers with a safe fallback when tqdm is unavailable."""

from __future__ import annotations

from typing import Generic, Iterable, Iterator, TypeVar

T = TypeVar("T")


class _NoOpProgress(Generic[T]):
    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        self._iterable = iterable

    def __enter__(self) -> "_NoOpProgress[T]":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def __iter__(self) -> Iterator[T]:
        if self._iterable is None:
            return iter(())
        return iter(self._iterable)

    def update(self, n: int = 1) -> None:
        _ = n

    def set_postfix(self, ordered_dict=None, refresh: bool = True, **kwargs) -> None:
        _ = ordered_dict, refresh, kwargs

    def set_postfix_str(self, s: str = "", refresh: bool = True) -> None:
        _ = s, refresh

    def close(self) -> None:
        return None


def progress_bar(iterable: Iterable[T] | None = None, **kwargs):
    """Return a tqdm progress bar when available, else a no-op stand-in."""

    try:
        from tqdm.auto import tqdm
    except ModuleNotFoundError:
        return _NoOpProgress(iterable)

    kwargs.setdefault("dynamic_ncols", True)
    return tqdm(iterable, **kwargs)


__all__ = ["progress_bar"]
