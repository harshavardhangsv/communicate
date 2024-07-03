#!/usr/bin/python -t
# -*- coding:utf-8 -*-

import re
import json
import sqlite3
from collections import defaultdict
import operator


def get_treebank(database='database.db'):
    conn = sqlite3.connect(database)
    conn.text_factory = str
    c = conn.cursor()
    rows = c.execute("SELECT * FROM Treebank").fetchall()
    return rows


def print_sentences(rows, given_vibhaktis):

    for given_vibhakti in given_vibhaktis:
        result = list()
        for eachrow in rows:
            rid = eachrow[0]
            conll_sent = eachrow[3]
            lines = conll_sent.split('\n')
            drels = [ eachline.split("\t")[-3] for eachline in lines]
            words = [ eachline.split("\t")[1] for eachline in lines]
            parent_word_indices = [ int(eachline.split("\t")[-4]) - 1 for eachline in lines]
            indices = [ int(eachline.split("\t")[0]) - 1 for eachline in lines]
            index = 0
            while index < len(drels):
                vibhakti = ''
                incrementer = 1
                eachdrel = drels[index]
                if eachdrel == 'lwg__psp':
                    if ( index + 3 < len(drels) and drels[index+1] == 'lwg__psp' and drels[index+2] == 'lwg__psp' and
                            drels[index+3] == 'lwg__psp' and parent_word_indices[index] == parent_word_indices[index+1] and
                            parent_word_indices[index+1] == parent_word_indices[index+2] and parent_word_indices[index+2] == parent_word_indices[index+3]):
                        vibhakti += '_'.join(words[index:index+4])
                        incrementer = 4
                    elif ( index + 2 < len(drels) and drels[index+1] == 'lwg__psp' and drels[index+2] == 'lwg__psp' and
                            parent_word_indices[index] == parent_word_indices[index+1] and
                            (parent_word_indices[index+1] == parent_word_indices[index+2] or parent_word_indices[index+2] == indices[index+1])):
                        vibhakti += '_'.join(words[index:index+3])
                        incrementer = 3
                    elif ( index + 1 < len(drels) and drels[index+1] == 'lwg__psp' and parent_word_indices[index] == parent_word_indices[index+1] ):
                        vibhakti += '_'.join(words[index:index+2])
                        incrementer = 2
                    else:
                        vibhakti += words[index]
                    if vibhakti.strip() == given_vibhakti.strip():
                        result.append(conll_sent)
                index += incrementer
        with open('temp/'+given_vibhakti, 'w') as fq:
            fq.write('\n\n'.join(result))

def main():
    '''Main Function'''
    rows = get_treebank()
    given_vibhaktis = list()
    with open('all_postpositions') as fp:
        lines = fp.read().split('\n')
        for i in ['समय']:
            given_vibhaktis.append(i)
    print_sentences(rows, given_vibhaktis)


if __name__ == '__main__':
    main()

