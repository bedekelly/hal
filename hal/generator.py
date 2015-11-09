"""
generator.py: Handle generating and returning a response to the incoming text.
"""

from .handlers import handlers

def parse(text):
    """
    Run through each "handler", testing whether the incoming message matches
    the type of message that handler deals with. If so, run the handler's
    main function with any useful data that its 'test' function picked out.
    """
    for test, fn in handlers:
        is_type, useful_data = test(text)
        if is_type:
            return fn(text, useful_data)
    else:
        return None


def gen_response(message):
    """Generate a response by parsing the message, or returning a default."""
    response = parse(message)
    if response is None:
        response = "Sorry, I didn't understand that message!"
    return response
