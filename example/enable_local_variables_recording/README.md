# Example for `enable_local_variables_recording()`

By running `enable_local_variables_recording.py`, you will see variables are added to the exception event's attributes.


```bash
python sample.py 
```

Above command will output OpenTelemetry's span which holds values of variables used in causal function in exception like below.

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
