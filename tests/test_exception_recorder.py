from datetime import datetime
import pytest
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.exception.ext import (
    enable_local_variables_recording,
    disable_local_variables_recording,
)
from opentelemetry.exception.ext._internal.exception_recorder import ExceptionRecorder


@pytest.fixture(scope="function")
def fixture_function():
    enable_local_variables_recording()
    yield
    disable_local_variables_recording()


def test_enable_local_variables_recording(fixture_function):
    span = create_exception_raised_span("hello exception")

    events = span.events
    assert len(events) == 1
    assert "exception" in events[0].name

    attributes_keys = events[0].attributes.keys()
    assert "local.var.test_arg" in attributes_keys
    assert "local.var.test_value" in attributes_keys
    assert "hello exception" == events[0].attributes["local.var.test_arg"]

    assert "local.function.filename" in attributes_keys
    assert "local.function.name" in attributes_keys
    assert "local.function.lineno" in attributes_keys


def test_enable_local_variables_recording_with_recordable(fixture_function):
    def recordable(_exception, key, _value):
        if key == "test_value":
            return False
        return True

    enable_local_variables_recording(recordable=recordable)

    span = create_exception_raised_span("hello exception")

    events = span.events
    assert len(events) == 1
    assert "exception" in events[0].name
    assert "local.var.test_arg" in events[0].attributes.keys()
    assert "local.var.test_value" not in events[0].attributes.keys()
    assert "hello exception" == events[0].attributes["local.var.test_arg"]


# fmt: off
params = {
    "call with arguments": (
        lambda span, exc, attr: span.record_exception(exc, attr), True
    ),
    "call with attributes as keyword": (
        lambda span, exc, attr: span.record_exception(exc, attributes=attr), True
    ),
    "call with keyword arguments": (
        lambda span, exc, attr: span.record_exception(exception=exc, attributes=attr), True
    ),
    "call without attributes": (
        lambda span, exc, attr: span.record_exception(exc), False
    ),
    "call with keyword but no attributes": (
        lambda span, exc, attr: span.record_exception(exception=exc), False
    ),
    "call with None attributes": (
        lambda span, exc, attr: span.record_exception(exc, None, 123), False
    ),
}
# fmt: on


@pytest.mark.parametrize("record_fn,use_attributes", params.values(), ids=list(params.keys()))
def test_enable_local_variables_recording_with_different_arguments(
    fixture_function, record_fn, use_attributes
):
    span = create_span()
    exception = create_exception()
    attributes = {"dummy_attribute": "foo"}
    record_fn(span, exception, attributes)

    events = span.events
    assert len(events) == 1
    assert "exception" in events[0].name

    attributes_keys = events[0].attributes.keys()
    assert "local.var.test_arg" in attributes_keys
    if use_attributes:
        assert "dummy_attribute" in attributes_keys


def test_enable_local_variables_recording_with_multiple_times_no_multiple_decoration(
    fixture_function,
):
    recorded_keys = []

    def recordable(_exception, key, _value):
        recorded_keys.append(key)
        return True

    ExceptionRecorder.enable_local_variables_recording(recordable=recordable)
    ExceptionRecorder.enable_local_variables_recording(recordable=recordable)

    span = create_exception_raised_span("hello exception")

    assert recorded_keys == ["test_arg", "test_value"]

    events = span.events
    assert len(events) == 1
    assert "exception" in events[0].name


params = {
    "record str as str": ("hello", "hello"),
    "record bool as bool": (True, True),
    "record bytes as decoded str": (b"\x01\x02", "\x01\x02"),
    "record int as int": (123, 123),
    "record float as float": (123.45, 123.45),
    "record object as str": (datetime(2001, 2, 3, 4, 5, 6), "2001-02-03 04:05:06"),
    "record list as str": ([1, 2, 3], "[1, 2, 3]"),
    "record dict as str": ({"a": "b"}, "{'a': 'b'}"),
}


@pytest.mark.parametrize("test_arg,expected", params.values(), ids=list(params.keys()))
def test_enable_local_variables_recording_with_params(fixture_function, test_arg, expected):
    span = create_exception_raised_span(test_arg)
    events = span.events
    assert len(events) == 1
    assert "exception" in events[0].name
    assert "local.var.test_arg" in events[0].attributes.keys()
    assert "local.var.test_value" in events[0].attributes.keys()
    assert expected == events[0].attributes["local.var.test_arg"]


def create_exception_raised_span(test_arg):
    tracer_provider = TracerProvider()
    tracer = tracer_provider.get_tracer("my.tracer.name")
    s = None
    try:
        with tracer.start_as_current_span("hello") as span:
            s = span
            raise_exception(test_arg)
    except Exception:
        pass

    return s


def create_span() -> Span:
    tracer_provider = TracerProvider()
    tracer = tracer_provider.get_tracer("my.tracer.name")
    return tracer.start_span("hello")


def create_exception():
    try:
        raise_exception("hello")
    except Exception as exception:
        return exception


def raise_exception(test_arg):
    test_value = 1
    raise Exception("exception + " + str(test_arg) + str(test_value))
