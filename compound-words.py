#!/usr/bin/env python3
#
# Looks for other interesting compound words like
# "pen-island" and "penis-land".
#
# See: http://ucrel.lancs.ac.uk/bncfreq/flists.html for source data.
import os
import time
from argparse import ArgumentParser
import urllib.request
import zipfile

__author__ = "David Blume"
__license__ = "MIT"

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
    v_print = print if verbose else lambda *a, **k: None


def process_variants(f, word_set):
    count = 0
    while True:
        last_pos = f.tell()
        line = f.readline().decode('UTF-8')
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
    if (len(parts) > 3 and parts[0].isalpha() and
        int(parts[4]) >= minimum_num_sources):
        if parts[1] == 'NoC':  # Maybe consider or parts[1] == 'NoP'
            count += add_to_set(f, parts, nouns)
        elif parts[1] == 'Adj':
            count += add_to_set(f, parts, other_words)
    return count


def find_subwords(words, e_subwords, b_subwords):
    """Split each word in words into its constituent words, if any."""
    for word in words:
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


def get_source_words():
    """Populate the sets "nouns" and "other_words". """
    count = 0
    # If you didn't get the datafile beforehand, we'll try now.
    if not os.path.isfile('1_1_all_fullalpha.txt'):
        v_print('1_1_all_fullalpha.txt not found, so extracting it...')
        if not os.path.isfile('1_1_all_fullalpha.zip'):
            v_print('1_1_all_fullalpha.zip not found, so downloading it...')
            urllib.request.urlretrieve(
                'http://ucrel.lancs.ac.uk/bncfreq/lists/1_1_all_fullalpha.zip',
                filename='1_1_all_fullalpha.zip')
        with zipfile.ZipFile('1_1_all_fullalpha.zip') as zf:
            zf.extract('1_1_all_fullalpha.txt')

    # First, makes sets of all the nouns and other interesting words
    with open('1_1_all_fullalpha.txt', 'rb') as f:
        line = f.readline().decode('UTF-8')
        while line != '':
            count += process_line(f, line)
            line = f.readline().decode('UTF-8')
            if count > max_words_to_check:
                v_print('Only reading %d words.' % (max_words_to_check, ))
                break

    # If you set minimum_num_sources too low,
    # you get things that are not words.
    for word in ('a', 'ad', 'ap', 'dr', 'st', 'co',
                 'pa', 'go', 'ba', 'se', 'ch'):
        if word in nouns:
            nouns.remove(word)
        if word in other_words:
            other_words.remove(word)


def find_doublets():
    """Find the words that end with other words, or that begin with other words.
    example: "island" ends with "land", and "penis" starts with "pen". """
    e_subwords = set()
    b_subwords = set()
    find_subwords(nouns, e_subwords, b_subwords)
    find_subwords(other_words, e_subwords, b_subwords)

    doublet_count = 0
    doublets = []
    for etuple in e_subwords:
        for btuple in b_subwords:
            if etuple[0] == btuple[1]:
                doublets.append("%s-%s, %s-%s" % (btuple[0],
                                                  btuple[1]+etuple[1],
                                                  btuple[0]+btuple[1],
                                                  etuple[1]))
                doublet_count += 1

    for doublet in sorted(doublets):
        print(doublet)

    v_print("There were %d doublets." % (doublet_count, ))


def main():
    get_source_words()
    find_doublets()


if __name__ == '__main__':
    description = 'Finds word pairs that can also be made from another pair.'
    parser = ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print additional output')
    args = parser.parse_args()
    set_v_print(args.verbose)
    main()
