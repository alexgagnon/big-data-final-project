from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize, regexp_tokenize
from collections import Counter
# import spacy
# from polyglot.text import Text
# from gensim. import Dictionary

text = 'Earth Revovles around the Sun.'
tokens = word_tokenize(text)
for token in tokens:
    print(token)
