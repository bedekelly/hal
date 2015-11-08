"""
handlers.py: define handlers for each different request type.
"""
import requests
import json
import re
import csv
import wikipedia
import warnings
from urllib.parse import quote_plus

PLACES_API_KEY = "AIzaSyDtwJ6pjQETAwVQfbiCgobjTtcZeHcRqUU"
EMAIL = "bedekelly97@gmail.com"
warnings.simplefilter("ignore")

def get_country_codes(filename):
    codes = []
    with open(filename) as codes_file:
        rows = codes_file.readlines()
    for row in rows:
        l = row.split()
        codes.append((l[0].lower(), l[2].lower()))
    return dict(codes)

    
COUNTRY_CODES = get_country_codes("static/countrycodes.csv")


def basic_match(text, prefixes):
    """
    Basic-match against prefixes. Useful for if your only tests
    involve things like "define x", "synonyms for x" etc.
    """
    text = text.strip().lower()
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix)+1:]
            return True, text
    else:
        return False, text


def is_synonym(text):
    """Test if 'text' wants synonyms for a word."""
    return basic_match(
        text,
        ["synonyms of", "synonyms for", "other words for",
         "other words", "synonyms",])


def synonyms(orig_text, word):
    """Return a list of synonyms for "word"."""
    headers = {
        "X-Mashape-Key":
          "5Cbc4Mg5HWmshLg3MzgnmPAVdldfp1Slg68jsnDSr7RqfbYiS9",
        "Accept": "application/json"
    }
    url = ("https://wordsapiv1.p.mashape.com/words/{}/synonyms"
           "").format(word.strip("\""))
    data = json.loads(requests.get(url, headers=headers).text)
    return word + ", synonyms:\n" + ", ".join(data["synonyms"])


def is_definition(text):
    """Test if 'text' wants a definition for a word."""
    return basic_match(
        text,
        ["define", "definition of", "definition", "meaning of",
         "meaning"])
    

def definition(orig_text, word):
    """
    Return a word's definition, or a helpful error message if none can
    be found.
    """
    if word == "recursion":
        return "recursion, noun: see recursion(1)"  # ;)
    headers = {
        "X-Mashape-Key":
          "5Cbc4Mg5HWmshLg3MzgnmPAVdldfp1Slg68jsnDSr7RqfbYiS9",
        "Accept": "application/json"
    }
    url = "https://wordsapiv1.p.mashape.com/words/{}".format(word)
    data = json.loads(requests.get(url, headers=headers).text)
    try:
        results = data["results"]
    except Exception as e:
        print(e)
        return "Sorry could't define that word :("
    first, *more, last = results

    resp = []
    for i, r in enumerate(results):
        resp.append(("{}. {}, {w[partOfSpeech]}: {w[definition]}"
                     "").format(i, word, w=r))
    return '\n'.join(resp)


trans = re.compile("translate \"?(.+)\"? to (\w+)")
def is_translate(text):
    """
    Test whether 'text' wants us to translate something to a language.
    """
    text = text.lower().strip()
    match = trans.search(text)
    if not match:
        return False, text
    phrase, language = match.groups()
    return True, (phrase, language)


def translate(orig_text, request):
    """Translate 'phrase' from English to 'language'."""
    phrase, language = request
    phrase = phrase
    url = ("http://mymemory.translated.net/api/get?q="
           "{}&langpair=en|{}&de={}".format(
               phrase, COUNTRY_CODES[language], EMAIL))
    data = json.loads(requests.get(url).text)
    try:
        if "INVALID TARGET" in data["responseData"]["translatedText"]:
            raise ValueError
        return "English: {}\n{}: {}".format(
            phrase,
            language.title(),
            data["responseData"]["translatedText"]
        )
    except Exception as e:
        print(e)
        return "Sorry, couldn't translate that! :("


summary_pats = ("tell me about \"?(.+)\"?",
                "describe \"?(.+)\"?",
                "what is (?:a )?\"?(.+)\"?\??")
sums = list(map(re.compile, summary_pats))
def is_summary(text):
    text = text.lower().strip()
    for s in sums:
        match = s.search(text)
        if match:
            topic, = match.groups()
            return True, topic.title()
    else:
        return False, text
           
def check_None(fn):
    def f(*args, **kwargs):
        r = fn(*args, **kwargs)
        if r is None or r.strip()=="":
            raise ValueError("OMFG IT RETURNS NONE HOW")
        return r
    return f

 
@check_None
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

        
pats = ["([£$])(\d+(?:\.\d+)?) (?:(?:to|in) )?(\w+)",
        "(\d+(?:\.\d+)?) ?(\w+) (?:(?:to|in) )?(\w+)"]
pats = list(map(re.compile, pats))
def is_currency(text):
    text = text.strip().lower()
    for p in pats:
        result = p.search(text)
        if result:
            return True, result.groups()
    else:
        return False, text


def currency(orig_text, groups):
    a, b, to = groups
    if a in "£$":
        from_ = a.replace("£", "GBP").replace("$", "USD")
        amount = b
    else:
        from_, amount = b, a
    from_ = from_.upper()
    to = to.upper()
    url = "http://google.com/finance/converter?a={}&from={}&to={}".format(
        amount, from_, to
    )
    data = requests.get(url).text
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
nearhere_pats = list(map(re.compile, nearhere_pats_))
def is_nearhere(text):
    text = text.lower().strip()
    for s in nearhere_pats:
        r = s.search(text)
        if r:
            return True, r.groups()
    else:
        return False, text
        

def nearhere(orig_text, data):
    print(data)
    return str(data)


# Store a list of (test_function, get_response_function) pairs.    
handlers = [(is_definition, definition), (is_synonym, synonyms),
            (is_translate, translate), (is_summary, summary),
            (is_currency, currency), (is_nearhere, nearhere)]
