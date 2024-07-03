#!/usr/bin/env python
import re
import subprocess
import os


def generate_sentence(user_csv, typ="."):
    #print user_csv
    english_sent = []
    os.chdir("/home/harsha/communicator_server_gamma/create-hindi-parser/chl_to_dmrs/")
    user_csv[0].append(typ)
    with open("experiment.csv", "w") as fq:
        fq.write("\n".join([",".join(i) for i in user_csv]))
    dev_output = subprocess.check_output(["sh", "convert_user_to_dev_csv.sh", "experiment.csv", "experiment_dev.csv"])
    english_output = subprocess.check_output(["sh", "run.sh", "experiment_dev.csv"])
    english_sent.extend([ i for i in english_output.split("\n") if len(i.split(" ")) > 1])
    print "QWEQWE", list(set(english_sent))
    os.chdir("/home/harsha/communicator_server_gamma/")    
    return list(set(english_sent))


def main():
    pass


if __name__ == "__main__":
    main()
