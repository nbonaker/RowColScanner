#!/usr/bin/python

# This is an example script to run the WordPredictor class and get
# a list of words that begins with the prefix and a each of the valid 
# character in the character list appened to it. For example, given
# a prefix 'a' and if the chracters in the vocabulary are [a,b,c], it 
# will return a list of words that begin with 'aa', 'ab' and 'ac'.

import os, sys
import numpy as np
import kconfig

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from predictor import WordPredictor


class LanguageModel():
    def __init__(self, lm_filename, vocab_filename):
        self.lm_filename = lm_filename
        self.vocab_filename = vocab_filename

        self.word_predictor = WordPredictor(lm_filename, vocab_filename)

        # Define how many predictions you want for each character
        # By default it is set to 0 and will return all possible
        # words
        self.num_predictions = 3
        self.min_log_prob = -float("inf")

        # The default vocab_id is ''
        self.vocab_id = ''

    def get_words(self, context, prefix, num_words):
        self.context = context
        self.prefix = prefix
        # print("prefix: ", prefix, ", context: ", context)

        word_preds = []
        word_probs = []

        lm_results = self.word_predictor.get_words_with_context(prefix, context, self.vocab_id, self.num_predictions, self.min_log_prob)
        flattened_results = [freq for sublist in lm_results for freq in sublist]
        flattened_results.sort(key=lambda x: -x[1])
        return [word[0] for word in flattened_results][:num_words]


def main():

    LM = LanguageModel('../keyboard/resources/lm_word_medium.kenlm', '../keyboard/resources/vocab_100k')
    print(LM.get_words("", "", list("abcdefghijklmnopqrstuvwxyz' ")))

    # # Provide the name and path of a language model and the vocabulary
    # lm_filename = '../resources/lm_word_medium.kenlm'
    # vocab_filename = '../resources/vocab_100k'
    #
    # # Create an instance of the WordPredictor class
    # word_predictor = WordPredictor(lm_filename, vocab_filename)
    #
    # prefix = ''
    # context = ''
    #
    # # Define how many predictions you want for each character
    # # By default it is set to 0 and will return all possible
    # # words
    # num_predictions = 3
    # min_log_prob = -float('inf')
    #
    # # The default vocab_id is ''
    # vocab_id = ''

    # word_list = word_predictor.get_words_with_context(prefix, context, vocab_id, num_predictions, min_log_prob)

    # Call the print_suggestions method to print all the words
    # word_predictor.print_suggestions(word_list)
    # self.words_li, self.word_freq_li, self.key_freq_li, self.top_freq, self.tot_freq, self.prefix


if __name__ == "__main__":
    main()
