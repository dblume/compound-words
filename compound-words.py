#!/usr/bin/env python
#
# Looks for other interesting compound words like
# "pen-island" and "penis-land".
#
# See: http://ucrel.lancs.ac.uk/bncfreq/flists.html for source data.
import os
import time
from argparse import ArgumentParser
import urllib
import zipfile

__author__ = "David Blume"
__license__ = "WTFPL"

nouns = set()
other_words = set()
minimum_num_sources = 60
max_words_to_check = 20000


def set_v_print(verbose):
    """
    Defines the function v_print.
    It prints if verbose is true, otherwise, it does nothing.
    See: http://stackoverflow.com/questions/5980042
    :param verbose: A bool to determine if v_print will print its args.
    """
    global v_print
    if verbose:
        def v_print(*s):
            print ' '.join([i.encode('utf8') for i in s])
    else:
        v_print = lambda *s: None


def process_variants(f, word_set):
    count = 0
    while True:
        last_pos = f.tell()
        line = f.readline()
        parts = line.strip().split('\t')
        if len(parts) > 3 and parts[0] == '@':
            if parts[2].isalpha():
                word_set.add(parts[2].lower())
                count += 1
        else:
            f.seek(last_pos)
            break
    return count


def add_to_set(f, parts, word_set):
    count = 0
    if parts[2] == ':':
        word_set.add(parts[0].lower())
        count += 1  # Use this noun.
    elif parts[2] == '%':
        # Have to read in the variants that start with @
        count += process_variants(f, word_set)
    return count


def process_line(f, line):
    count = 0
    parts = line.strip().split('\t')
    if len(parts) > 3 and parts[0].isalpha() and int(parts[4]) >= minimum_num_sources:
        if parts[1] == 'NoC':  # Maybe consider or parts[1] == 'NoP'
            count += add_to_set(f, parts, nouns)
        elif parts[1] == 'Adj':
            count += add_to_set(f, parts, other_words)
    return count


def main():
    start_time = time.time()
    count = 0

    # If you didn't get the datafile beforehand, we'll try now.
    if not os.path.isfile('1_1_all_fullalpha.txt'):
        v_print('1_1_all_fullalpha.txt not found, so extracting it...')
        if not os.path.isfile('1_1_all_fullalpha.zip'):
            v_print('1_1_all_fullalpha.zip not found, so downloading it...')
            testfile = urllib.URLopener()
            testfile.retrieve('http://ucrel.lancs.ac.uk/bncfreq/lists/1_1_all_fullalpha.zip', '1_1_all_fullalpha.zip')
        with zipfile.ZipFile('1_1_all_fullalpha.zip') as zf:
            zf.extract('1_1_all_fullalpha.txt')

    # First, makes sets of all the nouns and other interesting words
    with open('1_1_all_fullalpha.txt', 'rb') as f:
        line = f.readline()
        while line != '':
            count += process_line(f, line)
            line = f.readline()
            if count > max_words_to_check:
                break

    # If you set minimum_num_sources too low, you get things that are not words.
    for word in ('a', 'ad', 'ap', 'dr', 'st', 'co', 'pa', 'go', 'ba'):
        if word in nouns:
            nouns.remove(word)
        if word in other_words:
            other_words.remove(word)

    # Find the words that terminate in other words, or that begin with other words.
    # example: "island" terminates in "land", and "penis" starts with "pen".
    e_subwords = set()
    b_subwords = set()
    for word in nouns:
        l = len(word) - 1
        for i in range(1, l):
            esubword = word[i:]
            bsubword = word[:i]
            if esubword in nouns:
                e_subwords.add((bsubword, esubword))
            if i > 1 and bsubword in nouns:
                b_subwords.add((bsubword, esubword))
            if i > 1 and bsubword in other_words:
                b_subwords.add((bsubword, esubword))

    for word in other_words:
        l = len(word) - 1
        for i in range(1, l):
            esubword = word[i:]
            bsubword = word[:i]
            if esubword in nouns:
                e_subwords.add((bsubword, esubword))
            if i > 1 and bsubword in nouns:
                b_subwords.add((bsubword, esubword))
            if i > 1 and bsubword in other_words:
                b_subwords.add((bsubword, esubword))

    doublet_count = 0
    doublets = []
    for etuple in e_subwords:
        for btuple in b_subwords:
            if etuple[0] == btuple[1]:
                doublets.append("%s-%s, %s-%s" % (btuple[0], btuple[1]+etuple[1], btuple[0]+btuple[1], etuple[1]))
                doublet_count += 1

    for doublet in sorted(doublets):
        print doublet

    v_print("Count was %d. There were %d doublets." % (count, doublet_count))
    if not line:
        v_print('Processed all the words in the wordlist.')
    else:
        v_print("Got as far as \"%s\" in the word list" % (repr(line)))
    v_print("Done.  That took %1.2fs." % (time.time() - start_time))


if __name__ == '__main__':
    parser = ArgumentParser(description='Just a template sample.')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    set_v_print(args.verbose)
    main()
