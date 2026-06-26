# Examples

Runnable Shiny for Python apps live in the
[`examples/`](https://github.com/StrategicProjects/dt2py/tree/main/examples)
directory. Run any with:

```bash
shiny run examples/app_extensions.py
```

| File | Shows |
| --- | --- |
| [`app.py`](https://github.com/StrategicProjects/dt2py/blob/main/examples/app.py) | Minimal table + selection event |
| [`app_config.py`](https://github.com/StrategicProjects/dt2py/blob/main/examples/app_config.py) | Number/date formatting, alignment, custom JS badge render |
| [`app_extensions.py`](https://github.com/StrategicProjects/dt2py/blob/main/examples/app_extensions.py) | Buttons, Select, Responsive, FixedHeader, RowGroup |
| [`app_serverside.py`](https://github.com/StrategicProjects/dt2py/blob/main/examples/app_serverside.py) | Server-side processing over 50,000 rows |
| [`app_proxy_inputs.py`](https://github.com/StrategicProjects/dt2py/blob/main/examples/app_proxy_inputs.py) | Proxy from Python + inline checkbox/button events |

All five have been verified rendering in a real browser via Shiny for Python.
