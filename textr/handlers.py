"""
handlers.py: define handlers for each different request type.
"""
import requests
import json
import re


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
    headers = {
        "X-Mashape-Key":
          "5Cbc4Mg5HWmshLg3MzgnmPAVdldfp1Slg68jsnDSr7RqfbYiS9",
        "Accept": "application/json"
    }
    url = "https://wordsapiv1.p.mashape.com/words/{}".format(word)
    data = json.loads(requests.get(url, headers=headers).text)
    results = data["results"]
    first, *more, last = results

    resp = []
    for i, r in enumerate(results):
        resp.append(("{}. {}, {w[partOfSpeech]}: {w[definition]}"
                     "").format(i, word, w=r))
    return '\n'.join(resp)


trans = re.compile("translate (\w+) to (\w+)")
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
    phrase, language = requests
    phrase = phrase.strip("\"")
    url = ("http://mymemory.translated.net/api/get?q="
           "{}&langpair=en|{}".format(phrase, language[:2]))
    
    
handlers = [(is_definition, definition), (is_synonym, synonyms),
            (is_translate, translate)]
