#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
""" 

"""
import os
import re
import sys
import csv
import logging

log = logging.getLogger(__name__)

def tokenize(str, delimiter):
    tokens = []
    j = 0
    str = str + delimiter
    quoted = False
    for i in xrange(len(str)):
        if str[i] == '"':
            quoted = not quoted
        if str[i] == delimiter and not quoted:
            tokens.append(str[j:i])
            j = i + 1
    return tokens

class Doc(object):

    def __init__(self, data_home, parent, leaf):
        f = open(os.path.join(data_home, "docs", parent, leaf))
        self.text = f.read().decode('utf-8')
        f.close()
        
        self.sentences = []
        f = open(os.path.join(data_home, "man_anns", parent, leaf,
                              "gatesentences.mpqa.2.0"))
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            l, r = row[1].split(',')
            l, r = int(l), int(r)
            self.sentences.append((l, r))
        f.close()

        self.annotations = []
        f = open(os.path.join(data_home, "man_anns", parent, leaf,
                             "gateman.mpqa.lre.2.0"))
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row[0].strip()[0] == '#': 
                continue
            l, r = row[1].split(',')
            l, r = int(l), int(r)
            ann = dict(left=l, right=r, type=row[3])
            if len(row) > 4:
                kv = tokenize(row[4].strip(), " ")
                meta = dict([t.split('=') for t in kv if len(t) > 0])
                ann.update(meta)
            self.annotations.append(ann)
        f.close()

    def sub_obj_sents(self):
        for l, r in self.sentences:
            c = 0
            for ann in self.annotations:
                if ann['left'] >= l and ann['right'] <= r:
                    if  ann['type'] == 'GATE_direct-subjective' and\
                        'intensity' in ann and\
                        ann['intensity'] not in ('low', 'neutral') and\
                        "insubstantial" not in ann:
                        c += 1
                    if  ann['type'] == 'GATE_expressive-subjectivity' and\
                        'intensity' in ann and\
                        ann['intensity'] not in ('low'):
                        c += 1
            if c > 0:
                yield self.text[l:r], "subjective"
            else:
                yield self.text[l:r], "objective"

def extract_sentences(data_home):
    docs_path = os.path.join(data_home, "docs")
    man_anns_path = os.path.join(data_home, "man_anns")
    docs = []
    for parent in os.listdir(docs_path):
        for leaf in os.listdir(os.path.join(docs_path, parent)):
            docs.append(Doc(data_home, parent, leaf))
    writer = csv.writer(sys.stdout, delimiter='\t')
    for doc in docs:
        for sent, label in doc.sub_obj_sents():
            writer.writerow([sent.encode('utf-8'), label])

if __name__ == "__main__":
    sys.exit(extract_sentences(sys.argv[1]))
