#!/usr/bin/env python
# -*- coding: utf-8 -*-


#   from flask import redirect, url_for
import json
import requests
import urllib3
#from converter_indic import wxConvert
from wxconv import wxConvert
from bs4 import BeautifulSoup as bs
import os
import subprocess
from irtokz import tokenize_ind
from itertools import izip

def ilmtApi(first, last, text):
    pool = urllib3.PoolManager()
    url = 'http://api.ilmt.iiit.ac.in/hin/pan/%s/%s' % (first, last)
    method = 'POST'
    headers = {'Content-Type':'application/x-www-form-urlencoded', 'charset':'UTF-8'}
    data = pool.urlopen(method, url, headers = headers, body = text).data
    return json.loads(data)


def set_postposition(words):
    print(" ".join([ i['word'] for i in words]))
    with open('json_files/postpositions_list') as fp:
        postpositions = fp.read().split('\n')
    l = len(words)
    index = 1
    if len(words) <= 1:
        return words
    while index < l:
        increment = 1
        #print words[index]['word_utf8']
        if words[index]['word_utf8'] in postpositions:
            print words[index]['word_utf8']
            if index + 1 < l and words[index]['word_utf8'] + '_' + words[index+1]['word_utf8'] in postpositions:
                if index + 2 < l and words[index]['word_utf8'] + '_' + words[index+1]['word_utf8'] + '_' + words[index+2]['word_utf8'] in postpositions:
                    words[index]['drel'] = 'lwg__psp'
                    words[index+1]['drel'] = 'lwg__psp'
                    words[index+2]['drel'] = 'lwg__psp'
                    words[index]['rhead'] = words[index]['index']-1
                    words[index+1]['rhead'] =  words[index]['index']-1
                    words[index+2]['rhead'] =  words[index]['index']-1
                    increment = 3
                else:
                    words[index]['drel'] = 'lwg__psp'
                    words[index+1]['drel'] = 'lwg__psp'
                    words[index]['rhead'] = words[index]['index']-1
                    words[index+1]['rhead'] = words[index]['index']-1
                    increment = 2
            else:
                if words[index]['finer_tag'] != 'v':
                    words[index]['drel'] = 'lwg__psp'
                    words[index]['rhead'] = words[index]['index']-1
                    print index, words[index]['word_utf8']
                    increment = 1
        index += increment
    return words


def default(sentence):
    words = []
    tok = tokenize_ind(lang="hin")
    converter = wxConvert(order="utf2wx")
    tokenized_sent = tok.tokenize(sentence)
    for index, word_utf8 in enumerate(tokenized_sent.split(' ')):
        each_word = dict()
        each_word['index'] = index
        each_word['word_utf8'] = word_utf8
        each_word['word'] = converter.convert(word_utf8)
        each_word['root'] = '-'
        each_word['root_utf8'] = '-'
        each_word['drel'] = '-'
        each_word['rhead'] = '-'
        each_word['tam'] = '-'
        each_word['tam_utf8'] = '-'
        each_word['pos_tag'] = '-'
        each_word['finer_tag'] = '-'
        words.append(each_word)
    return words


def get_other_attributes(hin_input, chunking_output):
    converter = wxConvert(order="wx2utf")
    #result = ilmtApi('1', '8', 'input=%s' % (hin_input.encode('utf8')))
    #pickone_morph = result['pickonemorph-8'].strip()
    root_index = 0
    words = default(hin_input)
    utf2wx_txt = "\n".join([str(index + 1) + "\t" + each_word['word'] + "\tunk" for index, each_word in enumerate(words)])
    with open(os.environ['COMMUNICATOR_SERVER']+'/morph.in', "w") as fq:
        fq.write(utf2wx_txt)
    pickone_morph = subprocess.check_output(["sh", "run.sh", "morph.in"]).strip()
    print pickone_morph
    index = 0
    for eachline in pickone_morph.split('\n')[1:-1]:
        if '((' in eachline or '))' in eachline:
            continue
        else:
            pos_tag = eachline.split('\t')[2]
            fs_list = eachline.split('\t')[3]
            tam = fs_list.split('\'')[1].split(',')[-1]
            root = fs_list.split('\'')[1].split(',')[0]
            finer_tag = fs_list.split('\'')[1].split(',')[1] # if pos_tag != 'NNP' else 'n'
            words[index]['pos_tag'] = pos_tag
            words[index]['finer_tag'] = finer_tag
            gen, num, pers = fs_list.split('\'')[1].split(',')[2:5]
            if num == 'any':
                num = 'sg'
            if pers in ['any', '']:
                pers = '3'
            if gen in ['any', '']:
                gen = 'm'
            words[index]['fs_list'] = ",".join([gen, num, pers])
            if root == tam: # hE situation
                tam = ''
            words[index]['tam'] = tam
            words[index]['root_utf8'] = converter.convert(root)
            words[index]['tam_utf8'] = converter.convert(tam)
            index += 1
    for chunk_head, each_chunk in chunking_output.iteritems():
        main_verb_flag = 0
        main_verb_index = -1
        for index in each_chunk:
            if words[index]['finer_tag'] == 'v' and main_verb_flag == 0:
                words[index]['drel'] = 'root'
                words[index]['pos_tag'] = 'VM'
                main_verb_flag = 1
                main_verb_index = index
            elif words[index]['finer_tag'] == 'v' and main_verb_flag == 1:
                words[index]['drel'] = 'lwg__vaux'
                words[index]['pos_tag'] = 'VAUX'
                words[index]['rhead'] = main_verb_index
    for chunk_head, each_chunk in chunking_output.iteritems():
        print(each_chunk)
        if len(each_chunk) > 1:
            first = each_chunk[0]
            last = each_chunk[-1]
            words[first:last+1] = set_postposition(words[first:last+1])
        #print each_chunk
    #words = set_postposition(words)
    return words


def get_drels_from_rulebased_parser(words, sentence_index, chnk_html, open_brackets_list, close_brackets_list):
    #create chunked_text
    converter = wxConvert(order="utf2wx")
    text = []
    for each_a in bs(chnk_html).div.find_all('a', attrs={"data-sid": str(sentence_index)}):
        try:
            if each_a['style']:
                if "none" not in each_a['style']:
                    text.append(converter.convert(each_a.text))
        except KeyError:
            text.append(converter.convert(each_a.text))
    #print open_brackets_list, close_brackets_list
    with open('./create-hindi-parser/tmp', 'w') as fq:
        fq.write(' '.join(text).replace('+', '_'))
    os.chdir('./create-hindi-parser')
    if len(open_brackets_list): # If it is complex sentences
        temp_output = subprocess.check_output(["sh", "run.sh", "tmp", "complex"])
        with open(os.environ['HOME_anu_tmp'] + '/tmp/tmp_tmp/2.1/scope.dat') as fp:
            save_remaining_facts = fp.read().split('\n')
            save_remaining_facts = [i for i in save_remaining_facts if "clause_type-chunk-clause_start-clause_end" not in i]
        new_facts = []
        for i, j in izip(open_brackets_list, close_brackets_list):  #   open_brackets_list = [ (scope_word, sid, wid),... ]
            if i[1] == sentence_index:
                new_facts.append('(clause_type-chunk-clause_start-clause_end conjunction ' + converter.convert(i[0]) + ' ' + str(j[2] + 1) + ' ' + str(i[2] + 1) + ')' )
            else:
                continue
        with open(os.environ['HOME_anu_tmp'] + '/tmp/tmp_tmp/2.1/scope.dat', 'w') as fq:
            fq.write("\n".join(new_facts + save_remaining_facts))
        output = subprocess.check_output(["sh", "get_rels_for_complex_sents.sh", "tmp"])
    else:
        temp_output = subprocess.check_output(["sh", "run.sh", "tmp", "complex"])
        output = subprocess.check_output(["sh", "get_rels_for_complex_sents.sh", "tmp"])
    print output
    os.chdir('../')
    for eachline in output.split('\n'):
        if 'rel_name-ids' in eachline:
            dum, drel, rhead, index = eachline.replace(")", "").split(" ")
            if len(drel.split("/")) == 1:
                words[int(index)-1]['drel'] = drel
                words[int(index)-1]['rhead'] = int(rhead) - 1
            #words[int(rhead)-1]['drel'] = 'root'
        if 'conjunction-components' in eachline:
            conj_list = eachline.replace(")", "").split(" ")[1:]
            conj_word_index = int(conj_list[0]) - 1
            for i in conj_list[1:]:
                words[int(i)-1]['rhead'] = conj_word_index
    return words


def creating_compound_nouns_for_proper_nouns(words, chunking_output, proper_noun_list, sentence_index):
    '''using chunking output and propernoun list, given by users, we should be able to create compound nouns'''
    for chunk_head, chunk in chunking_output[sentence_index].iteritems():
        if len(chunk) <= 1:
            continue
        prev_index = -10
        for word_index in chunk:
            if [int(sentence_index), int(word_index)] in proper_noun_list:
                if word_index - 1 == prev_index:
                    words[prev_index]['drel'] = 'pof__cn'
                prev_index = word_index
    return words


def run_rulebased_parser(hin_input, chnk_html, sentence_index, open_brackets_list, close_brackets_list, chunking_output, proper_noun_list, compoundnouns, complexpredicates):
    '''make an call to ilmt api and get pick one morph for the given sentence'''
    #print chunking_output
    #print proper_noun_list
    words = get_other_attributes(hin_input, chunking_output[sentence_index])
    words = creating_compound_nouns_for_proper_nouns(words, chunking_output, proper_noun_list, sentence_index)
    words = create_compoundnouns(words, compoundnouns, sentence_index)
    words = create_complexpredicates(words, complexpredicates, sentence_index)
    words = get_drels_from_rulebased_parser(words, sentence_index, chnk_html, open_brackets_list, close_brackets_list)
    return words


def create_compoundnouns(words, compoundnouns, sentence_index):
    try:
        print compoundnouns
        for each_index in compoundnouns[unicode(sentence_index)]:
            words[each_index]['drel'] = 'pof__cn'
            words[each_index]['rhead'] = each_index + 1
    except KeyError:
        print 'There are no compound nouns in sentence', sentence_index + 1, 'according to the user'
    return words


def create_complexpredicates(words, complexpredicates, sentence_index):
    try:
        print complexpredicates
        for each_index in complexpredicates[unicode(sentence_index)]:
            words[each_index]['drel'] = 'pof'
            words[each_index]['rhead'] = each_index + 1
    except KeyError:
        print 'There are no complexpredicates in sentence', sentence_index + 1, 'according to the user'
    return words


def get_boundary_marking(hin_input, chnk_html, sentence_index, open_brackets_list, close_brackets_list):
    words = get_other_attributes(hin_input)
    words = get_drels_from_rulebased_parser(words, sentence_index, chnk_html, open_brackets_list, close_brackets_list)
    return words


def main():
    words = [{'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': '' },{'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': ''},{'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': ''},{'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': ''}, {'root': '', 'tam': '', 'root_utf8': '', 'tam_utf8': ''}]
    hin_input = "राम ने खाना खाया |"
    get_tam(words, hin_input)


if __name__ == "__main__":
    main()

