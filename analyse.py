#!/usr/bin/env python3
import csv
import json
import os
import pickle
from collections import defaultdict
from functools import partial
from operator import is_not

import pandas as pd
import scipy as sp
from nltk import bigrams
from nltk.corpus import stopwords
from nltk.probability import FreqDist, ConditionalFreqDist
from nltk.tokenize import TweetTokenizer
from scipy.stats import norm

import argparse

parser = argparse.ArgumentParser(description='Analyse output from twitter live stream API.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-i', '--input', dest='input', default='./sample.json', help='The source path')
parser.add_argument('-o', '--output', dest='output', default='.', help='The destination directory')
parser.add_argument('--log', dest='log', default=False, action='store_true', help='Whether to store a log')

args = parser.parse_args()

INFILE = args.input
OUTFILE = args.output

def get_tweet_data_from_text(line):
    try:
        data = json.loads(line)
        data['text']
        if data['lang'].startswith('en'):
            return data
    except:
        return None


all_stopwords = set(
    stopwords.words('english') + [':', 'rt', '.', '…', ',', '"', "'", '!', '&', '?', '...', '’', '-', '“',
                                  '‘', '”', '..', '️', 'â', 'u', '*', ';', '(', ')', '/', 'y', ])

# sentiment dictionary taken from http://link.springer.com/article/10.3758%2Fs13428-012-0314-x,
# as used in https://www.csc.ncsu.edu/faculty/healey/tweet_viz/
valences = pd.read_csv('BRM-emot-submit.csv')
valences = {v[1]: pd.np.array([norm.pdf(v[2], v[2], sp.sqrt(v[3])), v[2]]) for v in valences.values}


def get_valence(token):
    try:
        return valences[token]
    except KeyError:
        return None


def get_tweet_valence(tweet):
    vals = list(filter(partial(is_not, None), (get_valence(token) for token in tweet)))
    if len(vals) > 1:
        this_valences = pd.np.vstack(vals)
        this_valences /= pd.np.sum(this_valences, axis=0)[0]
        return pd.np.sum(this_valences[:, 0] * this_valences[:, 1])
    else:
        return ''


data_out = pd.DataFrame()

hillary_words = ['hillary', 'hilary', 'clinton', 'hillaryclinton']
trump_words = ['donald', 'trump', 'donaldtrump']
hombres_words = ['hombres', 'ombres', 'hambres']

with open(INFILE) as f, open(os.path.join(OUTFILE, 'data.csv'), 'w') as f_out:
    tweet_rich_data = filter(partial(is_not, None), map(get_tweet_data_from_text, f))  # map the info-getting function,
    # and filter objects not equal to None.
    # tweet_rich_data = list(tweet_rich_data)
    wrtr = csv.DictWriter(f_out,
                          ['tweet_id', 'created_at', 'geo_x', 'geo_y', 'user', 'text', 'has_hillary', 'has_trump',
                           'has_hombres', 'sentiment'])
    wrtr.writeheader()
    this_lines = []

    tknzr = TweetTokenizer()
    unigrams_dist = FreqDist()
    bigrams_dist = FreqDist()
    bigrams_cond_dist = ConditionalFreqDist()
    this_lot_bigrams = []
    users = dict()
    users_freq = FreqDist()
    com = defaultdict(lambda: defaultdict(int))
    for tweet_i, tweet in enumerate(tweet_rich_data):
        tokens = tknzr.tokenize(tweet['text'].lower())
        stop_tokens = [token for token in tokens if token not in all_stopwords]
        unigrams_dist.update(tokens)
        this_bigrams = list(bigrams(stop_tokens))
        this_lot_bigrams += this_bigrams
        bigrams_dist.update(this_bigrams)

        for i in range(len(stop_tokens) - 1):
            for j in range(i + 1, len(stop_tokens)):
                w1, w2 = sorted([stop_tokens[i], stop_tokens[j]])
                if w1 != w2:
                    com[w1][w2] += 1

        this_tweet = {'tweet_id': tweet['id_str'],
                      'created_at': tweet['created_at'],
                      'user': tweet['user']['id_str'],
                      'text': tweet['text'].lower(),
                      'geo_x': '',
                      'geo_y': '',
                      'sentiment': get_tweet_valence(stop_tokens),
                      'has_hillary': 0 + any(
                          any(token.lstrip('#@').startswith(hillary_word) for token in stop_tokens) for hillary_word in
                          hillary_words),
                      'has_trump': 0 + any(
                          any(token.lstrip('#@').startswith(trump_word) for token in stop_tokens) for trump_word in
                          trump_words),
                      'has_hombres': 0 + any(
                          any(token.lstrip('#@').startswith(hombres_word) for token in stop_tokens) for hombres_word in
                          hombres_words)}
        try:
            this_tweet['geo_x'] = tweet['geo']['coordinates'][0]
            this_tweet['geo_y'] = tweet['geo']['coordinates'][1]
        except:
            pass

        users[tweet['user']['id_str']] = tweet['user']
        users_freq[tweet['user']['id_str']] += 1
        this_lines.append(this_tweet)
        if (tweet_i + 1) % 100 == 0:
            print('%d tweets' % (tweet_i+1))
        if (tweet_i + 1) % 1000 == 0:
            wrtr.writerows(this_lines)
            this_lines = []
        # if (tweet_i + 1) % 100000 == 0:
        #     bigrams_cond_dist += ConditionalFreqDist(this_lot_bigrams)
        #     this_lot_bigrams = []

    wrtr.writerows(this_lines)
    bigrams_cond_dist += ConditionalFreqDist(this_lot_bigrams)

print('read file')

for word in all_stopwords:
    try:
        unigrams_dist.pop(word)
    except KeyError:
        pass

with open(os.path.join(OUTFILE, 'unigrams.pickle'), 'wb+') as f:
    f.write(pickle.dumps(unigrams_dist))

with open(os.path.join(OUTFILE, 'bigrams.pickle'), 'wb+') as f:
    f.write(pickle.dumps(bigrams_dist))

with open(os.path.join(OUTFILE, 'bigrams_cond.pickle'), 'wb+') as f:
    f.write(pickle.dumps(bigrams_cond_dist))


# Now make pretty images
from wordcloud import WordCloud, ImageColorGenerator
from scipy.misc import imread
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
republican_mask = imread('Republicanlogo.svg.png')
democrat_mask = imread('DemocraticLogo.png')

wc_trump = WordCloud(background_color="white", max_words=2000, mask=republican_mask, max_font_size=40, random_state=42)
wc_clinton = WordCloud(background_color="white", max_words=2000, mask=democrat_mask, max_font_size=40, random_state=42)

trump_freqs = bigrams_cond_dist['trump'].most_common(100)
clinton_freqs = bigrams_cond_dist['clinton'].most_common(100)

wc_trump.generate_from_frequencies(trump_freqs)
wc_clinton.generate_from_frequencies(clinton_freqs)



trump_image_colors = ImageColorGenerator(republican_mask)
clinton_image_colors = ImageColorGenerator(democrat_mask)

plt.imshow(wc_trump.recolor(color_func=trump_image_colors))
plt.axis("off")
plt.savefig('trump.png')


plt.figure()
plt.imshow(wc_clinton.recolor(color_func=clinton_image_colors))
plt.axis("off")
plt.savefig('clinton.png')

