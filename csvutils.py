#!/usr/bin/env python
import re
import os
import sys
try:
    import simplejson as json
except ImportError:
    import json


def json_to_userCSV(chl):
    '''
        CSV FORMAT:
            ladakA_0,cammaca_se,cAvala_0,KA_0_sakawA_hE,.
            ladakA_1,cammaca_1,cAvala_1,KA_1
            1,2,3,4
            n,n,massn,v,
            yes,yes,,,
            [m sg a],[n sg -],[n sg a],,
            4:k1,4:k3,4:k2,,        
    '''
    words = chl['words']
    chl_result = chl['chl_result']
    lines = [0, 0, 0, 0, 0, 0, 0]
    lines[0] = ""
    lines[1] = ",".join([ words[int(k)]['word'] for k, v in chl_result.iteritems() ])
    lines[2] = ",".join([ str(i) for i in range(1, len(chl_result)+1) ])
    lines[3] = ",".join([ words[int(k)]['finer_tag']  for k, v in chl_result.iteritems() ])
    #lines[4] = ",".join([ words[int(k)]['definite'] for k,v in chl_result.iteritems() ])
    lines[4] = ",".join([ "yes" for k,v in chl_result.iteritems() ])
    lines[5] = ",".join([ '[' + words[int(k)]['fs_list'].replace(',', ' ')  + ']' for k, v in chl_result.iteritems() ]) 
    lines[6] = ",".join([]) 
    return "\n".join(lines)
    
     
def main():
    with open('sample') as fp:
        l = json.loads(fp.read())
    for i in l:
        print json_to_userCSV(i)


if __name__ == "__main__":
    main()
