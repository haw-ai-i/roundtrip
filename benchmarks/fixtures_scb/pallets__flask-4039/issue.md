Flask 2.0.0 Error Handler not called when Blueprint Name Contains a Period
When you have a blueprint, and it's name contains a `.` and it has error handlers registered, they are never called.

We have been using blueprints to help organize our application, and we have used `.` to help namespace the blueprint names. And we have registered error handlers on the blueprints. However, when an error occurs, they are never called.

Below is a simple example where you might have an app that has a UI and an API, and for UI errors you may have a custom error view, and for API errors you may want to return JSON.

```
from flask import Blueprint, Flask, jsonify

app = Flask(__name__)
ui = Blueprint("app.ui", __name__, url_prefix="/ui")
api = Blueprint("app.api", __name__, url_prefix="/api")


@ui.errorhandler(Exception)
def ui_error_handler(error):
    print("ui error handler called")
    return str(error)


@ui.get("/")
def ui_index():
    print("ui index called")
    raise Exception("this is an unhandled exception from the ui")


@api.errorhandler(Exception)
def api_error_handler(error):
    print("api error handler called")
    return jsonify(error=str(error))


@api.get("/")
def api_index():
    print("api index called")
    raise Exception("this is an unhandled exception from the api")


app.register_blueprint(ui)
app.register_blueprint(api)
```

Then when you run and do a get on one of the index endpoints you get:

```
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
api index called
[2021-05-13 13:14:48,849] ERROR in app: Exception on /api/ [GET]
Traceback (most recent call last):
  File "/lib/python3.9/site-packages/flask/app.py", line 2051, in wsgi_app
    response = self.full_dispatch_request()
  File "/lib/python3.9/site-packages/flask/app.py", line 1501, in full_dispatch_request
    rv = self.handle_user_exception(e)
  File "/lib/python3.9/site-packages/flask/app.py", line 1499, in full_dispatch_request
    rv = self.dispatch_request()
  File "/lib/python3.9/site-packages/flask/app.py", line 1485, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**req.view_args)
  File "app.py", line 29, in api_index
    raise Exception("this is an unhandled exception from the api")
Exception: this is an unhandled exception from the api
127.0.0.1 - - [13/May/2021 13:14:48] "GET /api/ HTTP/1.1" 500 -
```

You can see the `api index called` printed, but not the `api error handler called` printed which shows the error handler is never called.

Environment:

- Python version: 3.9
- Flask version: 2.0.0

