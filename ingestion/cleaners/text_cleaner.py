"""Text cleaning and normalization utilities."""
import re

def clean_text(text):
    #Remove references like [1], [2], ...
    cleaned = re.sub(r'\[\d+\]', '', text)

    #Remove punctuation at the start of the string
    cleaned = re.sub(r'[^\w\s\.]', '', cleaned)
    return cleaned