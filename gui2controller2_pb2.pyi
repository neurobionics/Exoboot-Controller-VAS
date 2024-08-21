from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Null(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class data_stream(_message.Message):
    __slots__ = ("logging_data",)
    LOGGING_DATA_FIELD_NUMBER: _ClassVar[int]
    logging_data: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, logging_data: _Optional[_Iterable[str]] = ...) -> None: ...
