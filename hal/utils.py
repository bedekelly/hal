from flask import request
from urllib.parse import parse_qs
from twilio.twiml import Response

def get_last_message():
    data = request.get_data().decode()
    d = parse_qs(data)
    body = d["Body"].pop()
    return body

    
def twiml_response(text):
    r = Response()
    r.message(text)
    return str(r)
