import os
import types as pytypes
from threading import Lock
from typing import Callable, Union
from opentelemetry.sdk.trace import Span
from opentelemetry.util import types

LOCAL_VARIABLE_ATTRIBUTE_KEY_PREFIX = "local.var."
LOCAL_VARIABLE_FUNCTION_ATTRIBUTE_KEY_PREFIX = "local.function."
VALID_ATTR_VALUE_TYPES = (bool, str, bytes, int, float)

Recordable = Callable[[Exception, str, any], bool]


class ExceptionRecorder:
    __original_record_exception_func = None
    __lock = Lock()

    @classmethod
    def enable_local_variables_recording(
        cls, project_path: str = None, recordable: Recordable = None
    ) -> None:
        cls.disable_local_variables_recording()

        with cls.__lock:
            cls.__original_record_exception_func = Span.record_exception

            decorator = ExceptionRecorderDecorator(project_path=project_path, recordable=recordable)
            Span.record_exception = decorator.decorate_method(Span.record_exception)

    @classmethod
    def disable_local_variables_recording(cls) -> None:
        with cls.__lock:
            if not cls.__original_record_exception_func:
                return

            Span.record_exception = cls.__original_record_exception_func
            cls.__original_record_exception_func = None


class ExceptionRecorderDecorator:
    def __init__(self, project_path: str = None, recordable: Recordable = None):
        if not project_path:
            try:
                project_path = os.getcwd()
            # pylint: disable=broad-exception-caught
            except Exception:
                project_path = None

        self.__project_path = project_path

        self.__recordable = recordable
        if self.__recordable is None:
            self.__recordable = lambda exception, key, val: True

    def decorate_method(self, method: Callable) -> Callable:
        def decorate(*original_args, **kwargs):
            args = list(original_args)
            try:
                if len(args) > 1:
                    exception: Exception = args[1]
                    attributes: types.Attributes = {}
                    if len(args) > 2:
                        attributes = args[2]
                    else:
                        args.append(None)
                    local_vars = self.__create_local_variable_attributes(exception)
                    local_vars.update(attributes)
                    args[2] = local_vars
            # pylint: disable=broad-exception-caught
            except Exception:
                args = original_args

            return method(*args, **kwargs)

        return decorate

    def __create_local_variable_attributes(self, exception: Exception) -> dict:
        traceback = self.__last_matched_traceback(exception)
        if not traceback:
            return {}

        attributes = {}
        frame = traceback.tb_frame
        for name, value in frame.f_locals.items():
            if not self.__recordable(exception, name, value):
                continue
            if isinstance(value, VALID_ATTR_VALUE_TYPES):
                attributes[LOCAL_VARIABLE_ATTRIBUTE_KEY_PREFIX + name] = value
            else:
                attributes[LOCAL_VARIABLE_ATTRIBUTE_KEY_PREFIX + name] = str(value)
        attributes.update(self.__create_frame_info_attributes(frame))

        return attributes

    def __last_matched_traceback(self, exception: Exception) -> Union[pytypes.TracebackType, None]:
        traceback = exception.__traceback__
        last_matched = None

        while traceback:
            filename = traceback.tb_frame.f_code.co_filename
            if self.__project_path in filename:
                last_matched = traceback
            traceback = traceback.tb_next

        return last_matched

    def __create_frame_info_attributes(self, frame: pytypes.FrameType):
        return {
            LOCAL_VARIABLE_FUNCTION_ATTRIBUTE_KEY_PREFIX + "filename": frame.f_code.co_filename,
            LOCAL_VARIABLE_FUNCTION_ATTRIBUTE_KEY_PREFIX + "name": frame.f_code.co_name,
            LOCAL_VARIABLE_FUNCTION_ATTRIBUTE_KEY_PREFIX + "lineno": frame.f_lineno,
        }


def enable_local_variables_recording(
    project_path: str = None, recordable: Recordable = None
) -> None:
    """
    Enable recording local variables when exception raised.

    Args:
        project_path (str):
            Path to the project to identify exception's traceback is in project or site-packages.
        recordable (exception, variable_name, variable_value) -> bool:
            A function to determine whether to record the local variable.
    """
    ExceptionRecorder.enable_local_variables_recording(project_path, recordable)


def disable_local_variables_recording() -> None:
    """
    Disable recording local variables when exception raised.
    """
    ExceptionRecorder.disable_local_variables_recording()
