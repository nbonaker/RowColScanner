# import os
# vocab_file = open("resources/vocab_100k", 'r')
# vocab_text = vocab_file.read()
# vocab_file.close()
#
# words = vocab_text.split()
# num_words = len(words)
#
# chars = list("abcdefghijklmnopqrstuvwxyz\'")
# char_counts = [0 for i in range(len(chars))]
# for word_num, word in enumerate(words):
#     for letter in word:
#         char_counts[chars.index(letter)] += 1
#
# print(char_counts)
#
# sorted_chars = [x for _,x in sorted(zip(char_counts, chars))[::-1]]
# print(sorted_chars)

import numpy as np

x = np.zeros((5, 6))
for row_num, row in enumerate(x):
    for col_num, _ in enumerate(row):
         x[row_num][col_num] = row_num + col_num
print(x)
sorted_indicies = []
for i in range(x.size):
    arg_min_index = np.unravel_index(x.argmin(), x.shape)
    sorted_indicies += [arg_min_index]
    x[arg_min_index] = float("inf")

print(sorted_indicies)
