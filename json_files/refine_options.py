#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json


def main():
    '''GET OPTIONS dictionary and filter out some relations'''
    with open('./options') as fp:
        options = json.loads(fp.read())
    for pos_tag, relation_set in options.iteritems():
        if len(relation_set.keys()) > 20:
            print pos_tag



if __name__ == "__main__":
    main()

