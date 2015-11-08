from . import app
from .utils import get_last_message, twiml_response
from .generator import gen_response


@app.route("/api/v1.0/received", methods=["GET", "POST"])
def recieved():
    message = get_last_message()
    return twiml_response(gen_response(message))
