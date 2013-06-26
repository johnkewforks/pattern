#### PATTERN | FR ##################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2013 University of Antwerp, Belgium
# Copyright (c) 2013 St. Lucas University College of Art & Design, Antwerp.
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################
# French linguistical tools using fast regular expressions.

import os
import sys

try:
    MODULE = os.path.dirname(os.path.abspath(__file__))
except:
    MODULE = ""

sys.path.insert(0, os.path.join(MODULE, "..", "..", "..", ".."))

# Import parser base classes.
from pattern.text import (
    Lexicon, Spelling, Parser as _Parser, ngrams, pprint, commandline,
    PUNCTUATION
)
# Import parse tree base classes.
from pattern.text.tree import (
    Tree, Text, Sentence, Slice, Chunk, PNPChunk, Chink, Word, table,
    SLASH, WORD, POS, CHUNK, PNP, REL, ANCHOR, LEMMA, AND, OR
)
# Import sentiment analysis base classes.
from pattern.text import (
    Sentiment, NOUN, VERB, ADJECTIVE, ADVERB
)
# Import verb tenses.
from pattern.text import (
    INFINITIVE, PRESENT, PAST, FUTURE, CONDITIONAL,
    FIRST, SECOND, THIRD,
    SINGULAR, PLURAL, SG, PL,
    INDICATIVE, IMPERATIVE, SUBJUNCTIVE,
    IMPERFECTIVE, PERFECTIVE, PROGRESSIVE,
    IMPERFECT, PRETERITE,
    PARTICIPLE, GERUND
)
# Import inflection functions.
from pattern.text.fr.inflect import (
    pluralize, singularize, NOUN, VERB, ADJECTIVE,
    verbs, conjugate, lemma, lexeme, tenses,
    predicative, attributive
)
# Import all submodules.
from pattern.text.fr import inflect

sys.path.pop(0)

#--- FRENCH PARSER ---------------------------------------------------------------------------------
# The French parser is based on Lefff (Lexique des Formes Fléchies du Français).
# Benoît Sagot, Lionel Clément, Érice Villemonte de la Clergerie, Pierre Boullier.
# The Lefff 2 syntactic lexicon for French: architecture, acquisition.
# http://alpage.inria.fr/~sagot/lefff-en.html

# For words in Lefff that can have different part-of-speech tags,
# we used Lexique to find the most frequent POS-tag:
# http://www.lexique.org/

ABBREVIATIONS = set((
    u"av.", u"boul.", u"C.-B.", u"c.-à-d.", u"ex.", u"éd.", u"fig.", u"I.-P.-E.", u"J.-C.", 
    u"Ltee.", u"Ltée.", u"M.", u"Me.","Mlle.", u"Mlles.", u"MM.", u"N.-B.", u"N.-É.", u"p.", 
    u"S.B.E.", u"Ste.", u"T.-N.", u"t.a.b."
))

# While contractions in English are optional, 
# they are required in French:
replacements = {
       "l'": "l' ",  # le/la
       "c'": "c' ",  # ce
       "d'": "d' ",  # de
       "j'": "j' ",  # je
       "m'": "m' ",  # me
       "n'": "n' ",  # ne
      "qu'": "qu' ", # que
       "s'": "s' ",  # se
       "t'": "t' ",  # te
   "jusqu'": "jusqu' ",
  "lorsqu'": "lorsqu' ",
  "puisqu'": "puisqu' ",
    # Same rule for Unicode apostrophe, see also Parser.find_tokens():
    ur"(l|c|d|j|m|n|qu|s|t|jusqu|lorsqu|puisqu)’": u"\\1&rsquo; "
}
replacements.update(((k.upper(), v.upper()) for k, v in replacements.items()))

def find_lemmata(tokens):
    """ Annotates the tokens with lemmata for plural nouns and conjugated verbs,
        where each token is a [word, part-of-speech] list.
    """
    for token in tokens:
        word, pos, lemma = token[0], token[1], token[0]
        if pos.startswith(("DT", "PR", "WP")):
            lemma = singularize(word, pos=pos)
        if pos.startswith(("RB", "IN")) and (word.endswith(("'", u"’")) or word == "du"):
            lemma = singularize(word, pos=pos)
        if pos.startswith(("JJ",)):
            lemma = predicative(word)
        if pos == "NNS":
            lemma = singularize(word)
        if pos.startswith(("VB", "MD")):
            lemma = conjugate(word, INFINITIVE) or word
        token.append(lemma.lower())
    return tokens

class Parser(_Parser):

    def find_tokens(self, tokens, **kwargs):
        kwargs.setdefault("abbreviations", ABBREVIATIONS)
        kwargs.setdefault("replace", replacements)
        s = _Parser.find_tokens(self, tokens, **kwargs)
        s = [s.replace("&rsquo ;", u"’") if isinstance(s, unicode) else s for s in s]
        return s

    def find_lemmata(self, tokens, **kwargs):
        return find_lemmata(tokens)

lexicon = Lexicon(
        path = os.path.join(MODULE, "fr-lexicon.txt"), 
  morphology = os.path.join(MODULE, "fr-morphology.txt"), 
     context = os.path.join(MODULE, "fr-context.txt"),
    language = "fr"
)
parser = Parser(
     lexicon = lexicon,
     default = ("NN", "NNP", "CD"),
    language = "fr"
)
sentiment = Sentiment(
        path = os.path.join(MODULE, "fr-sentiment.xml"), 
      synset = None,
   negations = ("n'", "ne", "ni", "non", "pas", "rien", "sans", "aucun", "jamais"),
   modifiers = ("RB",),
   modifier  = lambda w: w.endswith("ment"),
   tokenizer = parser.find_tokens,
    language = "fr"
)

def tokenize(s, *args, **kwargs):
    """ Returns a list of sentences, where punctuation marks have been split from words.
    """
    return parser.find_tokens(s, *args, **kwargs)

def parse(s, *args, **kwargs):
    """ Returns a tagged Unicode string.
    """
    return parser.parse(s, *args, **kwargs)

def parsetree(s, *args, **kwargs):
    """ Returns a parsed Text from the given string.
    """
    return Text(parse(s, *args, **kwargs))

def split(s, token=[WORD, POS, CHUNK, PNP]):
    """ Returns a parsed Text from the given parsed string.
    """
    return Text(s, token)
    
def tag(s, tokenize=True, encoding="utf-8"):
    """ Returns a list of (token, tag)-tuples from the given string.
    """
    tags = []
    for sentence in parse(s, tokenize, True, False, False, False, encoding).split():
        for token in sentence:
            tags.append((token[0], token[1]))
    return tags

def polarity(s, **kwargs):
    """ Returns the sentence polarity (positive/negative) between -1.0 and 1.0.
    """
    return sentiment(s, **kwargs)[0]

def subjectivity(s, **kwargs):
    """ Returns the sentence subjectivity (objective/subjective) between 0.0 and 1.0.
    """
    return sentiment(s, **kwargs)[1]
    
def positive(s, threshold=0.1, **kwargs):
    """ Returns True if the given sentence has a positive sentiment (polarity >= threshold).
    """
    return polarity(s, **kwargs) >= threshold

#---------------------------------------------------------------------------------------------------
# python -m pattern.fr xml -s "C'est l'exception qui confirme la règle." -OTCL

if __name__ == "__main__":
    commandline(parse)