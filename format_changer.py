#!/usr/bin/python
import json
import wxconv
from collections import OrderedDict

def formatChanger(filePath):
    converter = wxconv.wxConvert(order='utf2wx')
    with open(filePath) as fp:
        verb_list = json.loads(fp.read(), object_pairs_hook=OrderedDict)
    for eachverb, tamList  in verb_list.iteritems():
        for eachtam, drelList in tamList.iteritems():
            print converter.convert(eachverb) + "+" + converter.convert(eachtam) + "\t" + "/".join(drelList.keys())


def main():
    formatChanger("../treebank/verb_pratyaya_options.json")


if __name__ == "__main__":
    main()

