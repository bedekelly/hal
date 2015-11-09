"""
handlers.py: Define a list of 'handler' pairs for each type of message we might
             receive.
"""
import requests
import json
import re
import csv
import wikipedia
import warnings
from .api_keys import X_MASHAPE_KEY, PLACES_API_KEY
from .utils import COUNTRY_CODES
from operator import itemgetter
from urllib.parse import quote_plus

EMAIL = "bedekelly97@gmail.com"

# Avoid polluting our server logs with messages about the API calls we make.
warnings.simplefilter("ignore")


def basic_match(text, prefixes):
    """
    Basic-match against prefixes. Useful for if your only tests
    involve things like "define x", "synonyms for x" etc.
    """
    text = text.strip().lower()
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix)+1:].strip("'\"?")
            return True, text
    else:
        return False, text


def is_synonym(text):
    """Test if the message is asking for synonyms for a word."""
    return basic_match(
        text,
        ["synonyms of", "synonyms for", "other words for",
         "other words", "synonyms", "what are some other words for"])


def synonyms(orig_text, word):
    """Fetch and return a list of synonyms for `word` from the WordsAPI."""
    headers = {
        "X-Mashape-Key": X_MASHAPE_KEY,        
        "Accept": "application/json"
    }
    url = ("https://wordsapiv1.p.mashape.com/words/{}/synonyms"
           "").format(word.strip("\""))
    data = json.loads(requests.get(url, headers=headers).text)
    return word + ", synonyms:\n" + ", ".join(data["synonyms"])


def is_definition(text):
    """Test if the message is asking for a word's definition."""
    return basic_match(
        text,
        ["define", "definition of", "definition", "meaning of",
         "meaning"])
    

def definition(orig_text, word):
    """
    Return a word's definition or a helpful error message if it can't be found.
    """
    if word == "recursion":
        return "recursion, noun: see recursion(1)"  # ;)
    headers = {
        "X-Mashape-Key": X_MASHAPE_KEY,
        "Accept": "application/json"
    }
    url = "https://wordsapiv1.p.mashape.com/words/{}".format(word)
    data = json.loads(requests.get(url, headers=headers).text)
    try:
        results = data["results"]
    except KeyError:
        # We might have got no results for a plural: try with the singular.
        try:
            # TODO: add an actual NLTK-stemming call here, instead of just 
            # trying to remove the end character.
            url = "https://wordsapiv1.p.mashape.com/words/{}".format(word[:-1])
            data = json.loads(requests.get(url, headers=headers).text)
            results = data["results"]
        except KeyError:
            return "Sorry, couldn't define that word! :("
    resp = []
    for i, r in enumerate(results):
        resp.append(("{}. {}, {w[partOfSpeech]}: {w[definition]}"
                     "").format(i, word, w=r))
    return '\n'.join(resp)

    
trans_pats = ("translate \"?(.+?)\"? to (\w+)",
              "what is \"?(.+?)\"? in (\w+)\??")
transs = [re.compile(p) for p in trans_pats]
def is_translate(text):
    """
    Test whether 'text' wants us to translate something to a language.
    """
    text = text.lower().strip()
    for trans in transs:
        match = trans.search(text)
        if match:
            break
    else:
        return False, text
    phrase, language = match.groups()
    return True, (phrase, language)


def translate(orig_text, request):
    """
    Translate the relevant parts of `request` from English to the
    specified language.
    """
    phrase, language = [x.strip.lower() for x in (phrase, language)]
    url = "http://mymemory.translated.net/api/get?q={}&langpair=en|{}&de={}"
    url = url.format(phrase, COUNTRY_CODES[language], EMAIL)
    data = json.loads(requests.get(url).text)
    try:
        if "INVALID TARGET" in data["responseData"]["translatedText"]:
            raise ValueError
        return "English: {}\n{}: {}".format(
            phrase,
            language.title(),
            data["responseData"]["translatedText"]
        )
    except Exception as e:  # Not just ValueError - could be network problems.
        print(e)
        return "Sorry, couldn't translate that! :("


summary_pats = ("tell me about \"?(.+)\"?",
                "describe \"?(.+)\"?",
                "what is (?:a )?\"?(.+)\"?\??",
                "who is (?:a )?\"?(.+)\"?\??",
                "who was (?:a )?\"?(.+)\"?\??",
                "where is (?:a )?\"?(.+)\"?\??")
sums = [re.compile(p) for p in summary_pats]
def is_summary(text):
    """Test whether our message wants a summary of something."""
    text = text.lower().strip()
    for s in sums:
        match = s.search(text)
        if match:
            topic, = match.groups()
            return True, topic.title()
    else:
        return False, text


def summary(orig_text, topic):
    """
    Use the fantastic Wikipedia API bindings to grab the first sentence
    of the relevant article (which is EASILY long enough).
    """
    if topic=="recursion":
        return "See \"recursion\"."
    try:
        s = wikipedia.summary(topic, sentences=1)
    except wikipedia.exceptions.DisambiguationError as e:
         for o in e.options:
            try:
                return wikipedia.summary(o, sentences=1)
            except wikipedia.exceptions.DisambiguationError as e:
                continue
         else:
            return "Sorry, couldn't find anything about \""+topic+"\""
    else:
        return s

        
currency_pats_ = ["([£$])(\d+(?:\.\d+)?) (?:(?:to|in) )?(\w+)",
        "(\d+(?:\.\d+)?) ?(\w+) (?:(?:to|in) )?(\w+)"]
currency_pats = [re.compile(p) for p in currency_pats_]
def is_currency(text):
    text = text.strip().lower()
    for p in pats:
        result = p.search(text)
        if result:
            return True, result.groups()
    else:
        return False, text


def currency(orig_text, groups):
    """Return a currency conversion as per the message's request."""
    a, b, to = groups
    if a in "£$€":
        from_ = a.replace("£", "GBP").replace("$", "USD").replace("€", "EUR")
        amount = b
    else:
        from_, amount = b, a
    from_ = from_.upper()
    to = to.upper()
    url = "http://google.com/finance/converter?a={}&from={}&to={}"
    url = url.format(amount, from_, to)
    data = requests.get(url).text
    # Yeah, I'm using regex to parse HTML. And what?
    s = re.search('<span class=bld>(.*?)</span>', data)
    try:
        return s.group(1)
    except AttributeError:
        return ("Sorry, couldn't convert! Try using the 3-letter code"
                " for both your currencies, like "
                "'convert 8 usd to gbp'.")


nearhere_pats_ = ("best (.*) near (.*)",
                  "best (.*) in (.*)",
                  "best (.*) around (.*)",
                  "good (.*) near (.*)",
                  "good (.*) in (.*)",
                  "good (.*) around (.*)",
                  "where are some (.*) near (.*)",
                  "where are some (.*) in (.*)",
                  "where are some (.*) around (.*)",
                  "locate (.*) near (.*)",
                  "locate (.*) in (.*)",
                  "locate (.*) around (.*)",
                  "(.*) near (.*)",
                  "(.*) in (.*)",
                  "(.*) around (.*)")
nearhere_pats = [re.compile(p) for p in nearhere_pats_]
def is_nearhere(text):
    """Test if the message wants to know about things in a location."""
    text = text.lower().strip()
    for s in nearhere_pats:
        r = s.search(text)
        if r:
            return True, r.groups()
    else:
        return False, text
        

def nearhere(orig_text, data):
    """Search for things in a given location using the Google Places API."""
    searchq = ' in '.join(data)
    url = ("https://maps.googleapis.com/maps/api/place/textsearch/json?"
           "query={}&key={}&language=en-GB".format(
               searchq, PLACES_API_KEY
           ))
    
    t = requests.get(url).text
    d = json.loads(t)
    results = d["results"]

    def addr(a):
        """Get the important bits from an address."""
        address = a.split(",")
        if "japan" in address[0].lower():
            return ','.join(address[-3:-1])
        else:
            return ','.join(address[:2])

    # Grab the top 3 places by rating.
    get_rating = lambda r: str(r.get("rating", "-"))
    results = sorted(results, key=get_rating, reverse=True)
    top3 = [(r["name"], get_rating(r), addr(r["formatted_address"]))
            for r in results[:3]]

    # Format the address sanely in our response.
    def format_triple(addr):
        return "{}:\n  Rating: {}\n  Address: {}\n".format(*addr)
    u = orig_text.title() + ":\n" + '\n\n'.join(map(format_triple, top3))
    return u

# `handlers` is the big deal here. It's a list of (function, function) pairs,
# where the first function tests whether a message falls into a particular
# category and, if so, the second function handles that message type and 
# returns the response we should send back.
handlers = [(is_definition, definition), (is_synonym, synonyms),
            (is_translate, translate), (is_summary, summary),
            (is_currency, currency), (is_nearhere, nearhere)]
