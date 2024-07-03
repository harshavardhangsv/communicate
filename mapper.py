# !/usr/bin/env python
# -*- coding: utf-8 -*-

import json, os
import copy
from collections import OrderedDict


KARAKA_RELATIONS = ['k1', 'k2', 'k3', 'k4', 'k4a', 'k5', 'k7', 'k7p', 'k7t']


class Node(object):

    '''Creates nodes for words'''

    def __init__(self, data):
        self.data = copy.deepcopy(data)
        self.node_index = None
        self.left = None
        self.right = None
        self.pratyaya = None
        self.ln = None
        self.rn = None
        self.assigned = False
        self.chl_value = None
        self.rel_name = None
        self.attached = None
        self.conjunction_index = -1


    def __repr__(self):
        relation_mapping = get_relation_mapping()
        if self.pratyaya:
            return self.data['word_utf8'] + ' ' + self.pratyaya.data['word_utf8'] + relation_mapping['with_postposition'][self.data['drel']]['tag']
        else:
            return self.data['word_utf8'] + ' ' + relation_mapping['without_postposition'][self.data['drel']]['tag']


def prepend_OrderedDict(input_dic, newkey, newvalue):
    input_dic_list = []
    for key, value in input_dic.iteritems():
        input_dic_list.append((key, value))
    input_dic_list.insert(0, (newkey, newvalue))
    result_dic = OrderedDict()
    for i in input_dic_list:
        result_dic[i[0]] = i[1]
    return result_dic


def get_relation_mapping():
    with open(os.environ['COMMUNICATOR_SERVER'] + '/json_files/relation_mapping') as fp:
        return json.loads(fp.read())


def myprint(chl):
    relation_mapping = get_relation_mapping()
    for index, eachnode in enumerate(chl):
        if not eachnode.assigned:
            #print eachnode.attached,
            print eachnode.chl_value,
            #if eachnode.data['drel'] == 'nmod__adj': eachnode.data['drel'] = 'nmod__adj1'
            if eachnode.pratyaya:
                #print eachnode.pratyaya.attached,
                print eachnode.pratyaya.chl_value + relation_mapping['with_postposition'][eachnode.data['drel']]['tag'],
            else:
                print relation_mapping['without_postposition'][eachnode.data['drel']]['tag'],
    print


def create_result(chl):
    result = {}
    relation_mapping = get_relation_mapping()
    for index, eachnode in enumerate(chl):
        if not eachnode.assigned:
            #if eachnode.data['drel'] == 'nmod__adj': eachnode.data['drel'] = 'nmod__adj1'
            result[index] = {}
            result[index]['conjunction_index'] = eachnode.conjunction_index
            result[index]['propernoun'] = eachnode.data['propernoun']
            result[index]['brackets'] = eachnode.brackets
            result[index]['prakriti'] = eachnode.chl_value
            result[index]['prakriti_attached'] = eachnode.attached
            result[index]['pratyaya_value'] = ''
            if eachnode.rel_name:
                result[index]['prakriti_tag'] = eachnode.rel_name
            else:
                result[index]['prakriti_tag'] = ''

            result[index]['prakriti_options'] = OrderedDict()   #prakriti options for compound noun
            if len(eachnode.attached) > 2:
                for i in xrange(0, len(eachnode.attached)):
                    if i == 0:
                        result[index]['prakriti_options']['split'+str(i)] = {'name': 'split all'}
                    else:
                        result[index]['prakriti_options']['split'+str(i)] = {'name': 'split at ' + str(i)}
            else:
                result[index]['prakriti_options']['split0'] = {'name': 'split'}

            result[index]['pratyaya_options'] = getoptions(eachnode)
            if eachnode.pratyaya:
                try:
                    relation_map = relation_mapping['with_postposition'][eachnode.data['drel']]['tag']
                except KeyError:
                    relation_map = eachnode.data['drel']
                if eachnode.data['pos_tag'] == 'VM' and eachnode.data['tam_utf8'] not in ['०', '']:
                    result[index]['pratyaya'] = eachnode.data['tam_utf8'] + '_' + eachnode.pratyaya.chl_value + relation_map
                elif eachnode.data['pos_tag'] == 'PRP' and eachnode.data['tam_utf8'] not in ['०', '']:
                    result[index]['pratyaya'] = eachnode.data['tam_utf8'] + '_' + eachnode.pratyaya.chl_value + relation_map
                else:
                    result[index]['pratyaya'] = eachnode.pratyaya.chl_value + relation_map
                result[index]['pratyaya_value'] = eachnode.pratyaya.chl_value
                result[index]['pratyaya_attached'] = eachnode.pratyaya.attached
            else:
                try:
                    relation_map = relation_mapping['with_postposition'][eachnode.data['drel']]['tag']
                except KeyError:
                    relation_map = eachnode.data['drel']
                if eachnode.data['pos_tag'] == 'VM' and eachnode.data['tam_utf8'] not in ['०', '']:
                    result[index]['pratyaya'] = eachnode.data['tam_utf8'] + relation_map
                elif eachnode.data['pos_tag'] == 'PRP' and eachnode.data['tam_utf8'] not in ['०', '']:
                    result[index]['pratyaya'] = eachnode.data['tam_utf8'] + relation_map
                else:
                    try:
                        result[index]['pratyaya'] = relation_mapping['without_postposition'][eachnode.data['drel']]['tag']
                    except KeyError:
                        result[index]['pratyaya'] = eachnode.data['drel']
    #print result
    return result


def getoptions(node):
    all_options = {}
    #print os.getcwd()
    with open('json_files/options') as fp:
        all_options = json.loads(fp.read(), object_pairs_hook=OrderedDict)
    with open('json_files/pratyaya_options') as fp:
        pratyaya_options = json.loads(fp.read(), object_pairs_hook=OrderedDict)
    with open('resource_files/postpositions') as fp:
        all_postpositions = fp.read().split('\n')
    with open('json_files/vibhakti_zero_options') as fp:
        vib_zero_options = json.loads(fp.read(), object_pairs_hook=OrderedDict)
    if node.pratyaya:
        try:
            return pratyaya_options[unicode(node.pratyaya.chl_value)]
        except KeyError:
            print node.pratyaya.chl_value

    #   adding options using POS tag for words with no pratyaya
    #options = all_options[node.data['pos_tag']]
    #   adding options using zero vibhakti list for words with no pratyaya
    options = vib_zero_options
    #print options
    #   Adding 'postposition' option to list of options by referring to resource file all_postpositions
    if node.data['word_utf8'] in all_postpositions:
        #options['lwg__psp'] = {'name': 'postposition', 'count':111111}
        options = prepend_OrderedDict(options, 'lwg__psp', {'name': 'postposition', 'count':11111})
    if node.data['drel'] == 'nmod__adj1':
        options = prepend_OrderedDict(options, 'nmod__adj6', {'name': 'Number', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj7', {'name': 'Quantifier', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj5', {'name': 'Ordinal', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj4', {'name': 'Demonstrator', 'count':11111})
    elif node.data['drel'] == 'nmod__adj7' or node.data['drel'] == 'nmod__adj8':
        options = prepend_OrderedDict(options, 'nmod__adj6', {'name': 'Number', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj5', {'name': 'Ordinal', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj1', {'name': 'Adjective', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj4', {'name': 'Demonstrator', 'count':11111})
    elif node.data['drel'] == 'nmod__adj6':
        options = prepend_OrderedDict(options, 'nmod__adj7', {'name': 'Quantifier', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj5', {'name': 'Ordinal', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj1', {'name': 'Adjective', 'count':11111})
        options = prepend_OrderedDict(options, 'nmod__adj4', {'name': 'Demonstrator', 'count':11111})
    if node.data['pos_tag'] in ['VM', 'VAUX']:
        options = prepend_OrderedDict(options, node.data['tam_utf8'] + 'TAM', {'name': node.data['tam_utf8'] + 'TAM', 'count': 111111})
    return options


def create_chl_text(chl):
    chl_text = ''
    relation_mapping = get_relation_mapping()
    for index, eachnode in enumerate(chl):
        if not eachnode.assigned:
            chl_text += eachnode.chl_value
            try:
                relation_map = relation_mapping['with_postposition'][eachnode.data['drel']]['tag']
            except KeyError:
                relation_map = eachnode.data['drel']
            if eachnode.pratyaya:
                chl_text +=  ' ' + eachnode.pratyaya.chl_value + relation_map
            else:
                if eachnode.data['pos_tag'] == 'VM':
                    chl_text += ' ' + eachnode.data['tam_utf8'] + relation_map
                else:
                    try:
                        chl_text += ' ' + relation_mapping['without_postposition'][eachnode.data['drel']]['tag']
                    except KeyError:
                        chl_text += ' ' + eachnode.data['drel']
        chl_text += ' '
    return chl_text


def create_nodes(words):
    result = [Node(i) for i in words]
    len_result = len(result)
    if len_result <= 1:     # if 0 or 1 element return
        return result
    for index, eachnode in enumerate(result):
        result[index].node_index = index
        result[index].attached = [index]
        result[index].brackets = {'open':eachnode.data['open_bracket'], 'close':eachnode.data['close_bracket']}
        if index == 0:
            result[index].ln = None
            result[index].rn = result[index+1]
        elif index == len_result - 1:
            result[index].ln = result[index-1]
            result[index].rn = None
        else:
            result[index].ln = result[index-1]
            result[index].rn = result[index+1]
        if result[index].data['pos_tag'] == 'VM':
            result[index].chl_value = result[index].data['root_utf8']
        elif result[index].data['pos_tag'] == 'PRP' and result[index].data['tam_utf8'] not in ['०', '']:
            result[index].chl_value = result[index].data['root_utf8']
        else:
            result[index].chl_value = result[index].data['word_utf8']

    return result


def get_startindex(chl):
    for index, current_node in enumerate(chl):
        if not current_node.assigned:
            return index
    print 'There is no start index'
    return -1


def get_endindex(chl):
    for index, current_node in enumerate(chl[::-1]):
        if not current_node.assigned:
            return len(chl) - 1 - index
    print 'There is no end index'
    return -1


def join_postposition(chl, end_index):    # consecutive lwg__psp lwg__psp
    prev_relation = ''
    prev_node = ''
    current_node = chl[end_index]
    while current_node:
        if current_node.data['drel'] == 'lwg__psp' and prev_relation == 'lwg__psp':
            #print prev_node.data['word_utf8'], current_node.data['word_utf8']
            current_node.brackets['open'] += prev_node.brackets['open']
            current_node.brackets['close'] += prev_node.brackets['close']
            current_node.right = prev_node
            current_node.chl_value = current_node.chl_value + '_' + prev_node.chl_value
            current_node.attached = current_node.attached + prev_node.attached
            current_node.rn = prev_node.rn
            if prev_node.rn:
                prev_node.rn.ln = prev_node.ln
            prev_node.assigned = True
        prev_node = current_node
        prev_relation = prev_node.data['drel']
        current_node = current_node.ln
    #myprint(chl)
    return chl


def join_compoundnouns(chl, start_index):  #join pof__cn rel word to its right word
    current_node = chl[start_index]
    while current_node:
        if current_node.data['drel'] == 'pof__cn':
            if current_node.rn:
                next_node = current_node.rn
                next_node.brackets['open'] += current_node.brackets['open']
                next_node.brackets['close'] += current_node.brackets['close']
                next_node.left = current_node
                next_node.chl_value = current_node.chl_value + '+' + next_node.chl_value
                next_node.attached = current_node.attached + next_node.attached
                next_node.ln = current_node.ln
                if current_node.ln:     #if starting of the sentence
                    current_node.ln.rn = current_node.rn
                current_node.assigned = True
                next_node.rel_name = 'Compound Noun'
            else:
                print 'not possible'
        current_node = current_node.rn
    #   myprint(chl)
    return chl


def join_reduplication(chl, start_index):   #join duplicated words using 'word' and 'pos_tags'
    prev_node = ''
    current_node = chl[start_index]
    while current_node:
        if prev_node != '':
            if prev_node.data['word_utf8'] == current_node.data['word_utf8']:
                if prev_node.data['pos_tag'] == current_node.data['pos_tag'] or current_node.data['pos_tag'] == 'RDP':
                    prev_node.brackets['open'] += current_node.brackets['open']
                    prev_node.brackets['close'] += current_node.brackets['close']
                    prev_node.right = current_node
                    prev_node.chl_value = prev_node.chl_value + '_' + current_node.chl_value
                    prev_node.attached = prev_node.attached + current_node.attached
                    prev_node.rn = current_node.rn
                    if current_node.rn:
                        current_node.rn.ln = current_node.ln
                    current_node.assigned = True
                    prev_node.rel_name = 'ReDuplication'
                else:
                    print 'words match but pos_tags did not match'
        prev_node = current_node
        current_node = current_node.rn
    #   myprint(chl)
    return chl


def join_auxillaryverbs(chl, end_index): #consecutive lwg__vaux/lwg__vaux_cont lwg__vaux/lwg_vaux_cont
    prev_relation = ''
    prev_node = ''
    current_node = chl[end_index]
    vaux_taglist = ['lwg__vaux', 'lwg__vaux_cont']
    while current_node:
        if current_node.data['drel'] in vaux_taglist and prev_relation in vaux_taglist:
            #print prev_node.data['word_utf8'], current_node.data['word_utf8']
            current_node.brackets['open'] += prev_node.brackets['open']
            current_node.brackets['close'] += prev_node.brackets['close']
            current_node.right = prev_node
            current_node.chl_value = current_node.chl_value + '_' + prev_node.chl_value
            current_node.attached = current_node.attached + prev_node.attached
            current_node.rn = prev_node.rn
            if prev_node.rn:
                prev_node.rn.ln = prev_node.ln
            prev_node.assigned = True
        prev_node = current_node
        prev_relation = prev_node.data['drel']
        current_node = current_node.ln
    #myprint(chl)
    return chl



def join_mainandauxverbs(chl, start_index):     # adding auxillary verbs to main verb's pratyaya
    current_node = chl[start_index]
    while current_node:
        if current_node.data['drel'] == 'lwg__vaux' or current_node.data['drel'] == 'lwg__vaux__cont':
            parent_index = current_node.data['rhead']
            print parent_index, "YES"
            parent_node = chl[parent_index]
            parent_node.brackets['open'] += current_node.brackets['open']
            parent_node.brackets['close'] += current_node.brackets['close']
            parent_node.pratyaya = current_node
            current_node.assigned = True
            if current_node.ln:
                current_node.ln.rn = current_node.rn
            if current_node.rn:
                current_node.rn.ln = current_node.ln
        current_node = current_node.rn
    return chl


def join_complexpredicate(chl, start_index):    #add 'pof' word to main verb
    current_node = chl[start_index]
    prev_node = ''
    while current_node:
        if prev_node != '':
             #   if prev_node.data['drel'] == 'pof' and ( current_node.data['drel'] == 'root' or current_node.data['drel'] == 'main') :
            #if prev_node.data['drel'] == 'pof' and current_node.data['pos_tag'] == 'VM':
            if prev_node.data['drel'] == 'pof':
                current_node.brackets['open'] += prev_node.brackets['open']
                current_node.brackets['close'] += prev_node.brackets['close']
                current_node.left = prev_node
                current_node.chl_value = prev_node.chl_value + '+' +current_node.chl_value
                current_node.attached = prev_node.attached + current_node.attached
                prev_node.assigned = True
                current_node.ln = prev_node.ln
                current_node.rel_name = 'Complex Predicate'
                if prev_node.ln:
                    prev_node.ln.rn = prev_node.rn
        prev_node = current_node
        current_node = current_node.rn
    return chl


def join_pratyaya(chl, start_index):    # adding 'lwg__psp' to pratyaya
    current_node = chl[start_index]
    while current_node:
        #print current_node.data['word_utf8'], current_node.assigned
        if current_node.data['drel'] == 'lwg__psp':
            parent_index = current_node.data['rhead']
            parent_node = chl[parent_index]
            parent_node.brackets['open'] += current_node.brackets['open']
            parent_node.brackets['close'] += current_node.brackets['close']
            parent_node.pratyaya = current_node
            current_node.assigned = True
            if current_node.ln:
                current_node.ln.rn = current_node.rn
            if current_node.rn:
                current_node.rn.ln = current_node.ln
        current_node = current_node.rn
    #myprint(chl)
    return chl


def noun_modifier(chl, start_index):
    '''splitting 'nmod__adj' to different relations'''
    current_node = chl[start_index]
    while current_node:
        #print current_node.data['drel'], current_node.data['pos_tag']
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'JJ':
            current_node.data['drel'] = 'nmod__adj1'
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'NN':
            current_node.data['drel'] = 'nmod__adj2'
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'NNP':
            current_node.data['drel'] = 'nmod__adj3'
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'DEM':
            current_node.data['drel'] = 'nmod__adj4'
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'QO':
            current_node.data['drel'] = 'nmod__adj5'
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'QO':
            current_node.data['drel'] = 'nmod__adj6'
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'QC':
            current_node.data['drel'] = 'nmod__adj7'
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'QF':
            current_node.data['drel'] = 'nmod__adj8'
        if current_node.data['drel'] == 'nmod__adj' and current_node.data['pos_tag'] == 'INTF':
            #print 'CAME'
            current_node.data['drel'] = 'nmod__adj9'
        current_node = current_node.rn
    return chl


def intensifier(chl, end_index):
    '''determing the number of intensifier'''
    current_node = chl[end_index]
    while current_node:
        if current_node.data['drel'] == 'jjmod__intf':
            rhead_index = current_node.data['rhead']
            if 'jjmod__intf' in chl[rhead_index].data['drel']:
                number = int(re.findall("\d+", chl[rhead_index].data['drel'])[0])
                current_node.data['drel'] == 'jjmod__intf' + str(number + 1)
            else:   #firstone
                current_node.data['drel'] == 'jjmod__intf1'
        current_node = current_node.ln
    return chl


def yaxi_wo(chl, start_index):  # yaxi/agara, wo  statements
    # first for loop to find yaxi
    yaxi_index = -1
    current_node = chl[start_index]
    yaxi_list = ['यदि', 'अगर']
    while current_node:
        if current_node.data['word_utf8'] in yaxi_list:
            yaxi_index = current_node.node_index
            break
        current_node = current_node.rn
    if yaxi_index == -1: return chl
    current_node = chl[start_index]
    while current_node:
        if current_node.data['word_utf8'] == 'तो':
            yaxi_node = chl[yaxi_index]
            current_node.left = yaxi_node
            yaxi_node.assigned = True
            yaxi_node.chl_value = '[ ' + yaxi_node.chl_value
            current_node.chl_value = yaxi_node.chl_value + '_' +  'तर्हि_conditional ]'
            if yaxi_node.ln:
                yaxi_node.ln.rn = yaxi_node.rn
            if yaxi_node.rn:
                yaxi_node.rn.ln = yaxi_node.ln
        current_node = current_node.rn
    return chl


def adv_relation(chl, start_index):  #adv -relation two occurences
    current_node = chl[start_index]
    while current_node:
        #print current_node.data['word_utf8'], current_node.assigned
        if current_node.data['drel'] == 'adv' and current_node.data['pos_tag'] == 'WQ':
            current_node.data['drel'] = 'adv2'
        current_node = current_node.rn
    return chl


def get_child(chl, start_index, conjunction_index):
    current_node = chl[start_index]
    child_indices = []
    while current_node:
        if current_node.data['rhead']  == conjunction_index:
            child_indices.append(current_node.data['index'])
        current_node = current_node.rn
    return child_indices


def conjunction_bn_words(chl, start_index):
    current_node = chl[start_index]
    conjunction_index = -1
    conjunction_list = ["Ora", "va", "yA"]
    while current_node:
        if current_node.data['drel'] in KARAKA_RELATIONS and current_node.data['word'] in conjunction_list:
            conjunction_index = current_node.data['index']
            child_indices = get_child(chl, start_index, conjunction_index)
            if len(child_indices) != 0:
                child_pratyaya = chl[child_indices[-1]].pratyaya
            for each_child_index in child_indices:
                chl[each_child_index].pratyaya = child_pratyaya
                chl[each_child_index].data['drel'] = chl[conjunction_index].data['drel']
                chl[each_child_index].conjunction_index = conjunction_index
            chl[conjunction_index].data['drel'] = 'conj'
        current_node = current_node.rn
    return chl


def mapper(words):

    '''Call all functions that are used for mapping'''

    chl = create_nodes(words)
    start_index = get_startindex(chl)
    end_index = get_endindex(chl)
    chl = join_postposition(chl, end_index)
    chl = join_compoundnouns(chl, start_index)
    start_index = get_startindex(chl)
    chl = join_reduplication(chl, start_index)
    end_index = get_endindex(chl)
    chl = join_auxillaryverbs(chl, end_index)
    start_index = get_startindex(chl)
    chl = join_mainandauxverbs(chl, start_index)
    start_index = get_startindex(chl)
    chl = join_complexpredicate(chl, start_index)
    start_index = get_startindex(chl)
    chl = yaxi_wo(chl, start_index)
    start_index = get_startindex(chl)
    end_index = get_endindex(chl)
    chl = intensifier(chl, end_index)
    chl = noun_modifier(chl, start_index)
    chl = join_pratyaya(chl, start_index)
    start_index = get_startindex(chl)
    chl = adv_relation(chl, start_index)
    start_index = get_startindex(chl)
    chl = conjunction_bn_words(chl, start_index)
    #myprint(chl)inte
    result = create_result(chl)
    chl_text = create_chl_text(chl)
    return result, words, chl_text


def main():
    '''Dummy Main'''
    print 'Something'


if __name__ == "__main__":
    main()
