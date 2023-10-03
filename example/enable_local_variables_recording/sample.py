from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.exception.ext import enable_local_variables_recording

enable_local_variables_recording()


def create_tracer():
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    return tracer_provider.get_tracer("my.tracer.name")


def raise_exception(text_arg, int_arg):
    bool_var = True
    raise Exception(f"exception: {text_arg}, {int_arg}, {bool_var}")


tracer = create_tracer()

try:
    with tracer.start_as_current_span("example for enable_local_variables_recording"):
        raise_exception("hello", 1234)
except Exception:
    pass
