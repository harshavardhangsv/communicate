#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from irtokz import tokenize_ind
from mapper import mapper
from collections import OrderedDict
from get_tam import get_tam
from run_rulebased_parser import run_rulebased_parser
import operator
import MySQLdb
import os
import sqlite3
import subprocess
import random
import operator
from wxconv import wxConvert
from generation import generate_sentence

PRATYAYA_OPTIONS_FILE = "./json_files/pratyaya_options"
VIBHAKTI_ZERO_OPTIONS_FILE = "./json_files/vibhakti_zero_options"

import sys
reload(sys)
sys.setdefaultencoding("utf8")


def connect_db():
    conn = MySQLdb.connect(host="localhost", user="root", passwd="ltrc@iiit", db="communicator_tool", charset="utf8mb4")
    conn.autocommit(True)
    return conn.cursor()


def insert_into_chl_conversion(input_text, parser_words, chl_text):
    cursor = connect_db()
    cursor.execute("insert into CHL_CONVERSION (input_text, parser_words, chl_text) values (%s, %s, %s)", (input_text, parser_words, chl_text))
    return cursor.lastrowid


def update_modified_parser_words_conversion(dbid, modified_parser_words, chl_text):
    cursor = connect_db()
    cursor.execute("update CHL_CONVERSION set modified_parser_words = %s, chl_text = %s where id = %s ", (modified_parser_words, chl_text, int(dbid)))
    return cursor.lastrowid


def save_modified_words(uni, dbid):
    all_words = []
    for i in uni:
        all_words.append(i["words"])
    cursor = connect_db()
    cursor.execute("update CHL_CONVERSION set modified_parser_words = %s where id = %s ", (json.dumps(all_words), int(dbid)))
    return "Success"


def save_feedback(dbid, feedback):
    cursor = connect_db()
    cursor.execute("update CHL_CONVERSION set feedback = %s where id = %s ", (feedback, int(dbid)))
    return dbid


def get_feedbacks():
    cursor = connect_db()
    rid = cursor.execute("select * from CHL_CONVERSION where feedback != \"\"")
    return json.dumps(cursor.fetchall())


def update_count(pratyaya, drel, change):
    cursor = connect_db()
    cursor.execute("select * from POSTPOSITION_RELATIONS WHERE postposition = %s and drel = %s LIMIT 1", (pratyaya, drel))
    rows = cursor.fetchall()
    if len(rows) == 1:
        count = rows[0][4]
        modified_count = count + change
        cursor.execute("update POSTPOSITION_RELATIONS SET count = %s WHERE postposition = %s and drel = %s", (modified_count, pratyaya, drel))
    else:
        print "not present in database"


def options_sort(input_dic):
    dic2list = []
    for rel, attrs in input_dic.iteritems():
        dic2list.append((rel, attrs["name"], attrs["count"]))
    dic2list.sort(key=operator.itemgetter(2), reverse=True)
    result_dic = OrderedDict()
    for eachitem in dic2list:
        result_dic[eachitem[0]] = {"name": eachitem[1], "count": eachitem[2]}
    return result_dic


def change_weights_pratyaya_options(new_relation_weight):
    pratyaya_options = OrderedDict()
    with open(PRATYAYA_OPTIONS_FILE) as fp:
        pratyaya_options = json.loads(fp.read(), object_pairs_hook=OrderedDict)
    prev_drel = new_relation_weight["prev_drel"]
    next_drel = new_relation_weight["next_drel"]
    pratyaya = new_relation_weight["pratyaya_value"]
    if pratyaya != "":
        update_count(pratyaya, prev_drel, change=-5)
        update_count(pratyaya, next_drel, change=10)
    else:
        update_count("0", prev_drel, change=-5)
        update_count("0" ,next_drel, change=10)
        vib_zero_options = OrderedDict()
    return "DONE"


def rearrange(sentence):
    len_words = len(sentence["pos_tag"])
    words = [{} for index in range(0, len_words)]
    for key, value in sentence.iteritems():
        if key not in ["chunk_head", "chunk"]:
            for index in range(0, len_words):
                words[index][key] = value[index]
    return words


def include_brackets(words, sentence_index, open_brackets_list, close_brackets_list):
    for word_index, eachword in enumerate(words):
        eachword["open_bracket"] = 0
        eachword["close_bracket"] = 0
        scope_less_open_brackets_list = [ [j, k] for i, j, k in open_brackets_list ]
        scope_less_close_brackets_list = [ [j, k] for i, j, k in close_brackets_list ]
        if [sentence_index, word_index] in scope_less_open_brackets_list:
            eachword["open_bracket"] += scope_less_open_brackets_list.count([sentence_index, word_index])
        if [sentence_index, word_index] in scope_less_close_brackets_list:
            eachword["close_bracket"] += scope_less_close_brackets_list.count([sentence_index, word_index])
    return words


def include_proper_nouns(words, sentence_index, proper_noun_list):
    for word_index, eachword in enumerate(words):
        eachword["propernoun"] = False
        if [sentence_index, word_index] in proper_noun_list:
            eachword["propernoun"] = True
    return words


def change_tams(words):
    for eachword in words:
        pos_tag = eachword["pos_tag"]
        tam_utf8 = eachword["tam_utf8"]
        word_utf8 = eachword["word_utf8"]
        if pos_tag == "VM" and tam_utf8 != "०":
            eachword["tam_utf8"] = word_utf8[len(word_utf8)-len(tam_utf8):]
            #print word_utf8, tam_utf8
    return words


def change_chl(dbid, output):
    modified_output = []
    all_chl_text = []
    modified_allwords = []
    dbid = int(dbid)
    for each_sent_output in output:
        words = each_sent_output["words"]
        chl_result, words, chl_text = mapper(words)
        modified_output.append({"chl_result": chl_result, "words": words})
        modified_allwords.append(words)
        all_chl_text.append(chl_text)

    mdbid = update_modified_parser_words_conversion(dbid, json.dumps(modified_allwords), "\n".join(all_chl_text))
    return dbid, modified_output


def create_dummy_output(user_text, open_brackets_list, close_brackets_list, proper_noun_list):
    user_text = user_text.strip()
    sentences = user_text.split("\n")
    allwords = []
    all_chl_text = []
    output = []
    for sent_index, each_sentence in enumerate(sentences):
        tok = tokenize_ind(lang="hin")
        tokenized_sent = tok.tokenize(each_sentence)
        sentence = dict()
        tokens = tokenized_sent.split(" ")
        sentence["word_utf8"] = tokens
        sentence["drel"] = ["-" for i in range(0, len(tokens))]
        sentence["pos_tag"] = ["-" for i in range(0, len(tokens))]
        sentence["tam"] = ["-" for i in range(0, len(tokens))]
        sentence["tam_utf8"] = ["-" for i in range(0, len(tokens))]
        sentence["root"] = ["-" for i in range(0, len(tokens))]
        sentence["word"] = ["-" for i in range(0, len(tokens))]
        sentence["root_utf8"] = ["-" for i in range(0, len(tokens))]
        sentence["rhead"] = [-1 for i in range(0, len(tokens))]

        words = rearrange(sentence)
        words = include_brackets(words, sent_index, open_brackets_list, close_brackets_list)
        words = include_proper_nouns(words, sent_index, proper_noun_list)
        words = get_tam(words, each_sentence)
        chl_result, words, chl_text = mapper(words)
        allwords.append(words)
        output.append({"chl_result": chl_result, "words": words})
        all_chl_text.append(chl_text)

    dbid = insert_into_chl_conversion("\n".join(sentences), json.dumps(allwords), "\n".join(all_chl_text))
    return dbid, output


def rule_based_analyze(user_text, open_brackets_list, close_brackets_list, proper_noun_list, chnk_html, chunking_output, compoundnouns, complexpredicates):
    user_text = user_text.strip()
    sentences = user_text.split("\n")
    output = []
    allwords = []
    all_chl_text = []
    ilparser_sentences = []
    for sent_index, sentence in enumerate(sentences):
        words = run_rulebased_parser(sentence, chnk_html, sent_index, open_brackets_list, close_brackets_list, chunking_output, proper_noun_list, compoundnouns, complexpredicates)
        words = include_brackets(words, sent_index, open_brackets_list, close_brackets_list)
        words = include_proper_nouns(words, sent_index, proper_noun_list)
        chl_result, words, chl_text = mapper(words)
        allwords.append(words)
        output.append({"chl_result": chl_result, "words": words})
        all_chl_text.append(chl_text)

    dbid = insert_into_chl_conversion("\n".join(sentences), json.dumps(allwords), "\n".join(all_chl_text))
    return dbid, output, "\n\n".join(ilparser_sentences)


def get_chunks(hin_input, tokenizer_output):
    """running the chunking module sent by roja ma"am"""
    os.chdir(os.environ["COMMUNICATOR_SERVER"] + "/HINDI_POS_CHUNKER/POSTagger/")

    tokenized_text = "\n".join([" ".join(i) for i in tokenizer_output])
    #print tokenized_text
    with open("temp_in", "w") as fq:
        fq.write(tokenized_text)
    pos_tagging = subprocess.check_output(["sh", "runTagger.sh", "temp_in"])
    os.chdir("../Chunker/")
    with open("temp_in", "w") as fq:
        fq.write(pos_tagging)
    chunking = subprocess.check_output(["sh", "runChunker.sh", "temp_in"])
    os.chdir("../../")
    #   print chunking
    chunking = chunking.strip()
    chunking_output = []
    for sentenceid, each_sent_chunk in enumerate(chunking.split("\n\n")):
        sent_chunk = {}
        for index, each_tag in enumerate(each_sent_chunk.split("\n")):
            each_tag = each_tag.strip().split("\t")[-1]
            placement = each_tag.split("-")[0]
            if placement == "B":
                present_chunk_start_index = index
                sent_chunk[present_chunk_start_index] = [present_chunk_start_index]
            elif placement == "I":
                sent_chunk[present_chunk_start_index].append(index)
            else:
                print "not B, I"
        chunking_output.append(sent_chunk)
    return chunking_output


def get_wordxgloss(word, tag):
    lite3_conn = sqlite3.connect("/home/harsha/communicator_server_gamma/gloss.db")
    #lite3_conn.text_factory = "str"
    lite3_cur = lite3_conn.cursor()
    lite3_cur.execute("SELECT * FROM gloss WHERE hindi_word_utf=? AND pos=?", (word, tag))
    resp = lite3_cur.fetchall()
    gloss_result = {}
    for i in resp:
        gloss_result[i[1]] = [i[-2].split(":")[0], i[-1].split(";")[0]]
    return gloss_result


def get_all_sense_gloss(uni, dbid):
    result = []
    pos_map = {'n': 'NOUN', 'v': 'VERB', 'adj': 'ADJECTIVE', 'avy': 'EMPHATIC', 'punc': 'PUNC', 'pn': 'pron', 'adv': 'ADVERB', 'unk': 'UNKNOWN'}
    for uni_index, each_sent in enumerate(uni):
        for word_index in each_sent['chl_result'].iterkeys():
            if each_sent['words'][int(word_index)]['propernoun'] == False:
                word = each_sent['words'][int(word_index)]
                # uni[uni_index]['chl_result'][word_index]['gloss'] = get_wordxgloss(word['root_utf8'], word['finer_tag'])
                uni[uni_index]['chl_result'][word_index]['gloss'] = get_wordxgloss(word['root_utf8'], pos_map[word['finer_tag']])
    # update datbase with gloss
    return uni, dbid


def weird_line(l, line, each_sent, chunks):
    converter = wxConvert()
    quasi = dict()
    comp = dict()
    for index in l:
        comp[index] = False
        quasi[index] = False
    print line
    for index, (head, chunk) in enumerate(chunks.iteritems()):
        head_index = int(head)
        if len(chunk) == 1:
            if each_sent["words"][head_index]["finer_tag"] in ["n", "pn", "adv"]:
                if each_sent["words"][head_index]["finer_tag"] == "pn":
                    line[index] = converter.convert(each_sent["words"][head_index]["root_utf8"]) + "_" +  each_sent["words"][head_index]["tam"]
                else:
                    line[index] = converter.convert(each_sent["words"][head_index]["root_utf8"]) + "_0"
            elif each_sent["words"][head_index]["finer_tag"] in ["v"]:
                if each_sent["words"][head_index]["word"] == "hE" and each_sent["words"][head_index]["tam"] == "": # hE special case
                    line[index] = converter.convert(each_sent["words"][head_index]["root_utf8"]) + "-" + "hE"
                else:
                    line[index] = converter.convert(each_sent["words"][head_index]["root_utf8"]) + "-" + each_sent["words"][head_index]["tam"]
            else:
                line[index] = converter.convert(each_sent["words"][head_index]["root_utf8"])
        else:
            prev_drel = each_sent["words"][chunk[0]]["drel"]
            prev_tag = each_sent["words"][chunk[0]]["finer_tag"]
            prev_tam = each_sent["words"][chunk[0]]["tam"]
            line[index] = converter.convert(each_sent["words"][chunk[0]]["root_utf8"])
            psp_flag = False
            for word_index in chunk[1:]:
                att = "?"
                print "prev_drel", prev_drel
                if prev_drel in ['pof__cn', 'pof']:
                    if prev_drel == "pof__cn":
                        comp[head_index] = True
                    att = "+"
                    line[index] += att + converter.convert(each_sent["words"][word_index]["root_utf8"])
                elif each_sent["words"][word_index]["drel"] in ["lwg__vaux", "lwg__psp", "lwg_vaux_cont"]:
                    if each_sent["words"][word_index]["drel"] == "lwg__psp":
                        psp_flag = True
                    if each_sent["words"][word_index]["drel"] == "lwg__vaux" and prev_tag == "v" and prev_drel not in ["lwg__vaux_cont", "lwg__vaux"]:
                        att = "-" + prev_tam  + "_"
                    else:
                        att = "_"
                    line[index] += att + each_sent["words"][word_index]["word"]
                elif each_sent["words"][word_index]["root_utf8"] in ["ही", "भी", "तक", "तो", "ना"]:
                    att = "*"
                    line[index] += att + each_sent["words"][word_index]["word"]
                else:
                    att = "~"
                    quasi[head_index] = True
                    line[index] += att + converter.convert(each_sent["words"][word_index]["root_utf8"])
                prev_drel = each_sent["words"][word_index]["drel"]
                prev_tag = each_sent["words"][word_index]["finer_tag"]
                prev_tam = each_sent["words"][word_index]["tam"]
                if each_sent["words"][word_index]["finer_tag"] == "v":
                    psp_flag = True
            if not psp_flag:
                line[index] += "_0"
    #print "line: ", line
    return line, quasi, comp


def chunking_correction(each_sent, chunks, mass, definite):
    remove_tuple_list = []
    for head_index in chunks:
        if each_sent["words"][int(head_index)]["rhead"] in chunks[head_index]:
            remove_tuple_list.append((head_index, str(each_sent["words"][int(head_index)]["rhead"])))
    for p, n in remove_tuple_list:
        chunks[n] = chunks[p]
        chunks.pop(p)
        mass[n] = mass[p]
        mass.pop(p)
        definite[n] = definite[p]
        definite.pop(p)
    chunks_sorted = OrderedDict(sorted(chunks.items(), key=lambda x: int(x[0])))
    #print chunks_sorted
    return chunks_sorted, mass, definite


def correct_fs_list(fs_list, cat, root):
    g,n,p = fs_list.split(",")
    if g == '': g = 'm'
    if n == '': n = 'sg'
    if p == '': p = 'u'
    if cat == 'pron':
        if root in ["mEM"]:
            p = 'u'
        elif root in ["vaha", "yaha"]:
            p = 'a'
        elif root in ["Apa"]:
            p = 'm'
        else:
            p = 'u'
    return g,n,p


def get_csv_from_uni(each_sent, mass, definite, chunks):
    #print 'QQQQQQQQQQQQQQQQQQQ', chunks
    places = []
    time = []
    rel_mapping = {"k7p": "sWAnavAcI", "ras-k1": "sk1"}
    with open("/home/harsha/communicator_server_gamma/create-hindi-parser/dics/hnd_place.txt") as fp:
        places.extend([i.split("\t")[0] for i in fp.read().split("\n")])
    with open("/home/harsha/communicator_server_gamma/create-hindi-parser/dics/hnd_time.txt") as fp:
        time.extend([i.split("\t")[0] for i in fp.read().split("\n")])
    chunks, mass, definite = chunking_correction(each_sent, chunks, mass, definite)
    result = [[],[],[],[],[],[],[],[],[]]
    converter = wxConvert()
    l = OrderedDict()
    for i, k in enumerate(chunks.keys()):
        l[int(k)] = i + 1    
    #print '------------------------------------------'
    #print l
    #print '------------------------------------------'
    result[0] = ["" for i in l]       
    result[0], quasi, comp = weird_line(l, result[0], each_sent, chunks)
    intra_drel_mapping = {"nmod__adj6": "saMKyA-viSeRaNa", "nmod__adj": "viSeRaNa"}
    for index, k in enumerate(chunks.keys()):
        if "~" not in result[0][index]:
            if each_sent["words"][int(k)]["finer_tag"] in ["pn"] and each_sent["words"][int(k)]["tam"] in ["0"]:
                print(each_sent["words"][int(k)])
                result[1].append(converter.convert(each_sent["words"][int(k)]["root_utf8"]))
            else:
                result[1].append(converter.convert(each_sent["words"][int(k)]["root_utf8"]) + '_1')
            result[6].append("")
        else:
            word_indices = chunks[k]
            temp_6 = ""
            chunk_head_index = word_indices.index(int(k))
            if each_sent["words"][int(word_indices[0])]["drel"] == "pof__cn":
                temp = converter.convert(each_sent["words"][int(word_indices[0])]["root_utf8"])
            else:
                temp = converter.convert(each_sent["words"][int(word_indices[0])]["root_utf8"]) + "_1"
                temp_6 += str(index+1) + '.' + str(chunk_head_index+1) + ':'  +  intra_drel_mapping[each_sent["words"][int(word_indices[0])]["drel"]]
            prev_drel = each_sent["words"][int(word_indices[0])]["drel"] 
            for ch_idex, word_index in enumerate(word_indices[1:]):
                pres_drel = each_sent["words"][int(word_index)]["drel"] 
                if int(word_index) != int(k) and each_sent["words"][int(word_index)]["drel"] in intra_drel_mapping.keys():
                        temp_6 += '~' + str(index+1) + '.' + str(chunk_head_index+1) + ':' + intra_drel_mapping[each_sent["words"][int(word_index)]["drel"]]
                if "nmod__adj" in prev_drel:
                    temp += '~' + converter.convert(each_sent["words"][int(word_index)]["root_utf8"])
                elif "pof__cn" in prev_drel:
                    temp += '+' + converter.convert(each_sent["words"][int(word_index)]["root_utf8"])
                if "nmod__adj" in pres_drel or int(word_index) == int(k):
                    temp += '_1'
                prev_drel = pres_drel
            result[1].append(temp)
            result[6].append(temp_6)
    result[2] = [str(i+1) for i in xrange(len(l))]
    for k in chunks.keys():
        if each_sent["words"][int(k)]["propernoun"]:
            result[3].append("propn")
        elif mass[k]:
            result[3].append("massn")
        elif quasi[int(k)] and comp[int(k)]:
            result[3].append("quasi_n")
        elif quasi[int(k)]:
            result[3].append("quasi_n")
        elif comp[int(k)]:
            result[3].append("compn")
        elif each_sent["words"][int(k)]["finer_tag"] == "pn":
            result[3].append("pron")
        elif converter.convert(each_sent["words"][int(k)]["root_utf8"]) in time:
            result[3].append("kAlavAcI")
        elif converter.convert(each_sent["words"][int(k)]["root_utf8"]) in places:
            result[3].append("sWAnavAcI")
        elif each_sent["words"][int(k)]["finer_tag"] == "unk":
            result[3].append("n")
        else:
            result[3].append(each_sent["words"][int(k)]["finer_tag"])
    result[4] = ["yes" if definite[k] else "" for k in chunks.keys()]
    for i, k in enumerate(chunks.keys()):
        if result[3][i] in ["n", "pron", "quasi_n", "propn"]:
            fs_list = correct_fs_list(each_sent["words"][int(k)]["fs_list"], result[3][i], converter.convert(each_sent["words"][int(k)]["root_utf8"]))
            result[5].append("[" + " ".join(fs_list) + "]")
        else:
            result[5].append("")
    #result[6] = ["" for i in l]
    for index, k in enumerate(chunks.keys()):
        if each_sent["words"][int(k)]["rhead"] not in [-1, "-1", "-"]:    
            #print int(each_sent["words"][int(k)]["rhead"])
            tmp = ""
            if "~" in result[0][index]:
                tmp += "".join(['~' for i in range(0, result[0][index].count('~'))])
            if each_sent["words"][int(k)]["drel"] in rel_mapping.keys():
                tmp += str(l[int(each_sent["words"][int(k)]["rhead"])])  + ":" + rel_mapping[each_sent["words"][int(k)]["drel"]]
            else:
                tmp += str(l[int(each_sent["words"][int(k)]["rhead"])])  + ":" + each_sent["words"][int(k)]["drel"]
            result[7].append(tmp)
        else:
            result[7].append("")
    result[8] = ["" for i in l]
    print '\n'.join(result)
    english_sent = generate_sentence(result)
    return result, english_sent


def get_all_valid_nouns(user_text):
    converter = wxConvert(order="utf2wx")
    nouns = OrderedDict()
    for sent_index, sent in enumerate(user_text.split("\n")):
        utf2wx_txt = "\n".join([str(index + 1) + "\t" + converter.convert(word) + "\tunk" for index, word in enumerate(sent.split(" "))])
        with open(os.environ["COMMUNICATOR_SERVER"] + '/morph.in', "w") as fq:
            fq.write(utf2wx_txt)
        pickone_morph = subprocess.check_output(["sh", "run.sh", "morph.in"]).strip()
        print pickone_morph
        index = 0
        prev_word = ""
        words = [ converter.convert(word) for word in sent.split(" ")]
        if sent_index not in nouns.keys():
            nouns[sent_index] = OrderedDict()
        for eachline in pickone_morph.split('\n')[1:-1]:
            if '((' in eachline or '))' in eachline:
                continue
            elif eachline.split('\t')[1] == 'unk':
                continue
            else:
                pos_tag = eachline.split('\t')[2]
                fs_list = eachline.split('\t')[3]
                finer_tag = fs_list.split('\'')[1].split(',')[1] # if pos_tag != 'NNP' else 'n'
                print finer_tag
                #if finer_tag == 'n' and prev_word not in ["yaha", "vaha", "isa", "usa"]:
                if finer_tag == 'n' and prev_word not in ["yaha", "isa", "usa"]:
                    nouns[sent_index][index] = True
                else:
                    nouns[sent_index][index] = False
                prev_word = words[index]
                index += 1
        print nouns
    return nouns
