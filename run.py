#!/usr/bin/env python3

"""
Hal is a simple Flask app to host a single API endpoint. This endpoint is POSTed to by Twilio,
and should return a TwiML representation of the response to send the user. The heavy lifting is
all in the response generation, like it should be. :)
"""

from hal import app
app.run(debug=True, port=9090)

