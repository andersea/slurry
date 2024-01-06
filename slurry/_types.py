from typing import Any, Awaitable, Protocol, Tuple, TypeVar, Union, runtime_checkable

from .sections import abc

PipelineSection = Union["AsyncIterableWithAcloseableIterator[Any]", "abc.Section", Tuple["PipelineSection", ...]]

_T_co = TypeVar("_T_co", covariant=True)

@runtime_checkable
class SupportsAclose(Protocol):
    def aclose(self) -> Awaitable[object]: ...

@runtime_checkable
class AcloseableAsyncIterator(SupportsAclose, Protocol[_T_co]):
    def __anext__(self) -> Awaitable[_T_co]: ...
    def __aiter__(self) -> "AcloseableAsyncIterator[_T_co]": ...

@runtime_checkable
class AsyncIterableWithAcloseableIterator(Protocol[_T_co]):
    def __aiter__(self) -> AcloseableAsyncIterator[_T_co]: ...
