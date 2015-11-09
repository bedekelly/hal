"""
utils.py: Some miscellaneous utilities for use in the app.
"""

from flask import request
from urllib.parse import parse_qs
from twilio.twiml import Response


def get_last_message():
    """Fetch and return the text of the last message sent to us."""
    data = request.get_data().decode()
    d = parse_qs(data)
    body = d["Body"].pop()
    return body

    
def twiml_response(text):
    """Return a formatted TwiML response with our message text."""
    r = Response()
    r.message(text)
    return str(r)


def get_country_codes(filename):
    """Return the mapping of country-name to country-code."""
    codes = []
    with open(filename) as codes_file:
        rows = codes_file.readlines()
    for row in rows:
        l = row.split()
        codes.append((l[0].lower(), l[2].lower()))
    return dict(codes)

    
COUNTRY_CODES = get_country_codes("static/countrycodes.csv")
