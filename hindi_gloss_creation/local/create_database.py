#!/usr/bin/env python
from __future__ import print_function
import re
import sqlite3
from collections import defaultdict
from itertools import izip
from wxconv import WXC


CONCEPT_DICTIONARY_PATH = '/home/harsha/19thDec2016/concept_dictionary.txt'
SYNSET_PATH = '/home/harsha/19thDec2016/English_Hindi_Linked_Synsets'

POS_MAPPING = {'ADJECTIVE': 'adj', 'ADVERB': 'adv', 'NOUN': 'n', 'VERB': 'v'}

#def dprint(d):
#    for (k, v) in d.iteritems():
#        print k, ':', 
#        if type(v) == str:
#            print v
#        elif type(v) == list:
#            print ", ".join(v)
#        elif type(v) == dict:
#            dprint(d)
#

def main():
    """
        FIRST, We Will do InMEMORY mapping, If everything goes perfectly then we will move this to sqlite database
    """
    wordxgloss, wordxenglish, conv = defaultdict(list), defaultdict(list), WXC(order="utf2wx")
    with open(SYNSET_PATH) as fp:
        for eachline in fp:
            eachline = eachline.strip()
            if not eachline: continue
            parts = eachline.split("\t")
            pos, english_words, hindi_words_utf, english_gloss = parts[2], parts[3].split(","), parts[4].split(","), parts[7]
            #hindi_words_wx = [converter.convert(i) for i in hindi_words_utf]
            for hindi_word in hindi_words_utf:
                wordxgloss[(pos, hindi_word)].append(english_gloss)
                wordxenglish[(pos, hindi_word)].append(english_words)

    with open("hindiwordXenglishgloss", "w") as fq:
        for (pos, hindi_word) in wordxgloss.iterkeys():
            for index, (english_gloss, english_words) in enumerate(izip(wordxgloss[(pos, hindi_word)], wordxenglish[(pos, hindi_word)])):
                fq.write("{}_{}, {}, {}, {}, {}\n".format(hindi_word, index+1, hindi_word, pos, ":".join(english_words), english_gloss))
        
    
if __name__ == "__main__":
    main()

