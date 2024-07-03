#!/usr/bin/env python
# -*- coding: utf-8 -*-


#   from flask import redirect, url_for
import json
import requests
import urllib3
#   from converter_indic import wxConvert
from wxconv import wxConvert
from irtokz import tokenize_ind


def ilmtApi(first, last, text):
    pool = urllib3.PoolManager()
    url = 'http://api.ilmt.iiit.ac.in/hin/pan/%s/%s' % (first, last)
    method = 'POST'
    headers = {'Content-Type':'application/x-www-form-urlencoded', 'charset':'UTF-8'}
    data = pool.urlopen(method, url, headers = headers, body = text).data
    return json.loads(data)


def set_postposition(words):
    with open('json_files/postpositions_list') as fp:
        postpositions = fp.read().split('\n')
    l = len(words)
    index = 0
    while index < l:
        increment = 1
        print words[index]['word_utf8']
        if words[index]['word_utf8'] in postpositions:
            if index + 1 < l and words[index]['word_utf8'] + '_' + words[index+1]['word_utf8'] in postpositions:
                if index + 2 < l and words[index]['word_utf8'] + '_' + words[index+1]['word_utf8'] + '_' + words[index+2]['word_utf8'] in postpositions:
                    words[index]['drel'] = 'lwg__psp'
                    words[index+1]['drel'] = 'lwg__psp'
                    words[index+2]['drel'] = 'lwg__psp'
                    words[index]['rhead'] = index-1
                    words[index+1]['rhead'] = index-1
                    words[index+2]['rhead'] = index-1
                    increment = 3
                else:
                    words[index]['drel'] = 'lwg__psp'
                    words[index+1]['drel'] = 'lwg__psp'
                    words[index]['rhead'] = index-1
                    words[index+1]['rhead'] = index-1
                    increment = 2
            else:
                words[index]['drel'] = 'lwg__psp'
                words[index]['rhead'] = index-1
                increment = 1
        index += increment
    return words


def get_tam(words, hin_input):
    '''make an call to ilmt api and get pick one morph for the given sentence'''
    converter = wxConvert(order="wx2utf")
    result = ilmtApi('1', '8', 'input=%s' % (hin_input.encode('utf8')))
    pickone_morph = result['pickonemorph-8'].strip()
    index  = 0
    for eachline in pickone_morph.split('\n')[1:-1]:
        if '((' in eachline or '))' in eachline:
            continue
        else:
            #print eachline
            pos_tag = eachline.split('\t')[2]
            fs_list = eachline.split('\t')[3]
            tam = fs_list.split('\'')[1].split(',')[-1]
            root = fs_list.split('\'')[1].split(',')[0]
            #if pos_tag in ['VM', 'VAUX'] and tam not in ['', '0']:
            #    pos_tag = 'VM'
            words[index]['pos_tag'] = pos_tag
            words[index]['root'] = root
            words[index]['tam'] = tam
            words[index]['root_utf8'] = converter.convert(root)
            words[index]['tam_utf8'] = converter.convert(tam)
            index += 1
    words = set_postposition(words)
    #print json.dumps(words, indent=4)
    return words


def main():
    words = [{'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': '' },{'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': ''},{'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': ''},{'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': ''}, {'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': ''}]
    hin_input = "राम ने खाना खाया |"
    get_tam(words, hin_input)


if __name__ == "__main__":
    main()

