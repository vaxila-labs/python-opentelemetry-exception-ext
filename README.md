# OpenTelemetry extension for exception
[![PyPI version](https://badge.fury.io/py/opentelemetry-exception-ext.svg)](https://badge.fury.io/py/opentelemetry-exception-ext)

This repository contains a set of utilities for OpenTelemetry's exception for Python.

# Installation

```bash
pip install opentelemetry-exception-ext
```

# Usage

## Add local variables to attributes of exception's event

```python
from opentelemetry.exception.ext import enable_local_variables_recording

enable_local_variables_recording()
```

When exception is raised, OpenTelemetry automatically creates an event for exception.  
`enable_local_variables_recording()` adds local variables and its function information to the event's attributes automatically by decorating `Span.record_exception()`.  
This helps you find the situation where exception happened.

Attributes will be added like below.

```js
{
    "name": "example for enable_local_variables_recording",
    ...,
    "status": {
        "status_code": "ERROR",
        "description": "Exception: exception: hello, 1234, True"
    },
    "events": [
        {
            "name": "exception",
            "attributes": {
                "exception.type": "Exception",
                "exception.message": "exception: hello, 1234, True",
                "exception.stacktrace": "Traceback (most recent call last) ...",
                "exception.escaped": "False",
                "local.var.text_arg": "hello",  // <= Added value for `text_arg`
                "local.var.int_arg": 1234,  // <= Added value for `int_arg`
                "local.var.bool_var": true,  // <= Added value for `bool_var`
                "local.function.filename": "/path/to/enable_local_variables_recording/sample.py",  // <= Added value for filename
                "local.function.name": "raise_exception",  // <= Added value for function name
                "local.function.lineno": 16  // <= Added value for line number of the file
            }
        }
    ]
}
```

You can see example [here](example/enable_local_variables_recording).

:warning: When using pre-fork server like Gunicorn, you should call `enable_local_variables_recording()` before fork to not run same thing multiple times.
