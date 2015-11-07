from flask import request
from urllib.parse import parseqs

def get_last_message():
    data = request.get_data()
    print(data)
