"""
views.py: Expose a single API endpoint for Twilio to POST to.
"""

from . import app
from .utils import get_last_message, twiml_response
from .generator import gen_response


@app.route("/api/v1.0/received", methods=["POST"])
def recieved():
    """Generate and return a response to the POST'ed message."""
    message = get_last_message()
    print("Message received:", message)
    return twiml_response(gen_response(message))
