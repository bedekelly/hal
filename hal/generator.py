from .handlers import handlers

def parse(text):
    for test, fn in handlers:
        is_type, useful_data = test(text)
        if is_type:
            return fn(text, useful_data)
    else:
        return None


def gen_response(message):
    response = parse(message)
    if response is None:
        return "Sorry, I didn't understand that message!"
    return response
