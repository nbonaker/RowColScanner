#!/usr/bin/python

######################################
#    Copyright 2009 Tamara Broderick
#    This file is part of Nomon Keyboard.
#
#    Nomon Keyboard is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Nomon Keyboard is distributed in the hope that it will be useful,dfg
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Nomon Keyboard.  If not, see <http://www.gnu.org/licenses/>.
######################################

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
# from matplotlib import pyplot as plt

# from mainWindow import MainWindow
# import dtree
# from keyboard import Keyboard
from kenlm_lm import LanguageModel
from phrases import Phrases
from pickle_util import PickleUtil
from scipy import stats

import sys
import os
# import string
import kconfig
import config
from appdirs import user_data_dir
import pathlib


# sys.path.insert(0, os.path.realpath('../KernelDensityEstimation'))

class Time():
    def __init__(self):
        self.cur_time = 0

    def time(self):
        return self.cur_time

    def set_time(self, t):
        self.cur_time = t


class SimulatedUser:
    def __init__(self, cwd=os.getcwd(), job_num=None, sub_call=False):


        self.job_num = job_num

        self.key_chars = kconfig.key_chars
        self.key_chars_sorted = kconfig.key_chars_sorted

        if not sub_call:
            self.key_config = "sorted"
            # self.key_config = "default"

            self.num_word_preds = 7
            self.words_first = True
            # self.words_first = False

            self.speed = config.default_rotate_ind
            self.scanning_delay = config.period_li[self.speed]
            self.start_scan_delay = config.pause_length
            self.reaction_delay = 0

            self.kernel_handle = PickleUtil("resources/kde_kernel.p")
            self.kde_kernel = self.kernel_handle.safe_load()
        self.sound_set = True
        self.pause_set = True

        self.lm_prefix = ""
        self.left_context = ""
        self.typed_versions = [""]

        self.cwd = cwd
        self.working_dir = cwd
        self.gen_data_dir()

        self.time = Time()
        self.prev_time = 0

        self.num_presses = 0

        self.last_press_time = self.time.time()
        self.last_update_time = self.time.time()

        lm_path = os.path.join(os.path.join(self.cwd, 'resources'), 'lm_word_medium.kenlm')
        vocab_path = os.path.join(os.path.join(self.cwd, 'resources'), 'vocab_100k')

        self.lm = LanguageModel(lm_path, vocab_path)

        self.phrase_prompts = True
        if self.phrase_prompts:
            self.phrases = Phrases("resources/all_lower_nopunc.txt")
        else:
            self.phrases = None

        # determine keyboard positions
        # set up file handle for printing useful stuff
        # set up "typed" text
        self.typed = ""
        self.context = ""
        self.old_context_li = [""]
        self.last_add_li = [0]
        # set up "talked" text

        # check for speech
        # talk_fid = open(self.talk_file, 'wb')
        # write words

        self.row_scan = True
        self.row_scan_num = -2
        self.col_scan = False
        self.col_scan_num = -1

        self.draw_words()
        self.generate_layout()
        self.update_layout()
        self.generate_timing_map()

    def init_sim_data(self):
        # self.init_clocks()
        self.num_selections = 0
        self.sel_per_min = []

        self.num_chars = 0
        self.char_per_min = []

        self.num_words = 0

        self.num_presses = 0
        self.press_per_char = []
        self.press_per_word = []

        self.num_errors = 0
        self.error_rate_avg = []

        # self.on_timer()
        self.is_winner = False
        self.winner_text = ""

    def parameter_metrics(self, parameters, num_clicks=100, trials=10, attribute=None):
        self.init_sim_data()
        # Load parameters or use defaults

        if "words_first" in parameters:
            self.words_first = parameters["words_first"]
        else:
            self.words_first = True

        if "order" in parameters:
            self.key_config = parameters["order"]
        else:
            self.key_config = "default"

        if "num_words" in parameters:
            self.num_word_preds = parameters["num_words"]
        else:
            self.num_word_preds = 7

        if "delay" in parameters:
            self.start_scan_delay = parameters["delay"]
        else:
            self.start_scan_delay = config.pause_length

        if "click_dist" in parameters:
            self.kde_kernel = parameters["click_dist"]
        else:
            pass

        self.draw_words()
        self.generate_layout()
        self.update_layout()
        self.generate_timing_map()

        self.gen_data_dir()
        for trial in range(trials):
            self.__init__(sub_call=True)

            while self.num_presses < num_clicks:
                text = self.phrases.sample()
                self.reset_context()
                self.type_text(text, verbose=False)
                print(round(self.num_presses/num_clicks*100), " %")
                self.typed = ""  # reset tracking and context for lm -- new sentence
                self.num_words += len(text.split(" "))

            print("selections per minute: ", self.num_selections / (self.time.time() / 60))
            print("characters per minute: ", self.num_chars / (self.time.time() / 60))
            print("presses per character: ", self.num_presses / self.num_chars)
            print("presses per word: ", self.num_presses / self.num_words)
            print("error rate: ", self.num_errors / self.num_selections)

            self.update_sim_averages(trials)

            self.num_selections = 0
            self.num_chars = 0
            self.num_words = 0
            self.num_errors = 0

        self.save_simulation_data(attribute=attribute)

    def type_text(self, text, verbose=True):
        self.target_text = text
        while len(self.target_text) > 0:
            target_item, self.target_text = self.next_target(self.target_text)
            self.make_selection(target_item, verbose=verbose)

        self.num_chars += len(text)

        words = text.split(" ")
        if "" in words:
            words.remove("")
        self.num_words += len(words)

    def next_target(self, text):
        words = text.split(" ")
        if "" in words:
            words.remove("")

        if len(words) > 1:
            remaining_words = ""
            for word in words[1:]:
                if remaining_words != "":
                    remaining_words += " "
                remaining_words += word
            first_word = words[0]
        else:
            remaining_words = ""
            first_word = words[0]

        target_word = self.lm_prefix + first_word + " "

        if target_word in self.words_li:
            index_2d = np.array(np.where(self.key_map == target_word)).T[0]
            # print(index_2d)
            return index_2d, remaining_words

        target_letter = text[0]

        index_2d = np.array(np.where(self.key_map == target_letter)).T[0]

        return index_2d, text[1:]

    def update_sim_averages(self, num_trials):

        time_int = self.time.time() - self.prev_time
        self.prev_time = float(self.time.time())

        self.sel_per_min += [self.num_selections / (time_int / 60)]

        self.char_per_min += [self.num_chars / (time_int / 60)]

        self.press_per_char += [self.num_presses / self.num_chars]

        self.press_per_word += [self.num_presses / self.num_words]

        self.error_rate_avg += [self.num_errors / self.num_selections]

    def generate_layout(self):
        if self.key_config == "sorted":
            self.keys_list = np.array(self.key_chars_sorted)
            closest_square = int(np.ceil(np.sqrt(len(self.keys_list) + self.num_word_preds)))

            self.key_freq_map = np.zeros((closest_square, closest_square))
            for row_num, row in enumerate(self.key_freq_map):
                for col_num, _ in enumerate(row):
                    self.key_freq_map[row_num][col_num] = row_num + col_num
        else:
            self.keys_list = np.array(self.key_chars)
            closest_square = int(np.ceil(np.sqrt(len(self.keys_list) + self.num_word_preds)))

            self.key_freq_map = np.zeros((closest_square, closest_square))
            for row_num, row in enumerate(self.key_freq_map):
                for col_num, _ in enumerate(row):
                    self.key_freq_map[row_num][col_num] = row_num * closest_square + col_num

        self.key_layout = np.empty((closest_square, closest_square), dtype=str)

        for word in range(self.num_word_preds):  # fill words first
            if self.words_first:
                word_index = np.unravel_index(word, (closest_square, closest_square))
            else:
                word_index = np.unravel_index(closest_square**2 - self.num_word_preds + word,
                                              (closest_square, closest_square))

            self.key_layout[word_index] = kconfig.word_char
            self.key_freq_map[word_index] = float("inf")

        sorted_indicies = []
        for i in range(len(self.keys_list)):
            arg_min_index = np.unravel_index(self.key_freq_map.argmin(), self.key_freq_map.shape)
            sorted_indicies += [arg_min_index]
            self.key_freq_map[arg_min_index] = float("inf")

        sorted_indicies.reverse()
        for key in self.keys_list:
            lowest_index = sorted_indicies.pop()
            self.key_layout[lowest_index] = key

        # print(self.key_layout)
        empty_row_counts = np.sum(np.where(self.key_layout != '', 1, 0), axis=1).tolist()
        if 0 in empty_row_counts:
            empty_index = empty_row_counts.index(0)
            self.key_layout = np.delete(self.key_layout, (empty_index), axis=0)

        self.key_rows_num = len(self.key_layout)
        self.key_cols_nums = np.sum(np.where(self.key_layout != '', 1, 0), axis=1).tolist()

        # shift empty cells

        for row_num, row in enumerate(self.key_layout):
            if "" in row:
                row_list = row.tolist()
                row_list.sort(key = lambda x: 2 if x == "" else 1)
                self.key_layout[row_num] = np.array(row_list)

    def generate_timing_map(self):
        self.timing_map = []
        for row in range(len(self.key_layout)):
            if row == 0:
                row_offset = 0
            else:
                row_offset = self.scanning_delay*row + self.start_scan_delay
            self.timing_map += [[row_offset + i * self.scanning_delay for i in range(len(self.key_layout[row]))]]

        self.timing_map = np.array(self.timing_map)
        print(self.timing_map)

    def draw_words(self):
        self.words_li = self.lm.get_words(self.left_context, self.lm_prefix, self.num_word_preds)
        self.words_li = [word+" " for word in self.words_li]

    def update_layout(self):
        self.key_map = np.array(self.key_layout, dtype=object)

        for word_num, (row, col) in enumerate(np.array(np.where(self.key_layout == kconfig.word_char)).T):
            if word_num < len(self.words_li):
                self.key_map[row][col] = self.words_li[word_num]
            else:
                self.key_map[row, col] = ""
        # print(self.key_map)

    def make_selection(self, index_2d, verbose=True):
        selection_time = self.timing_map[index_2d[0], index_2d[1]]

        if self.timing_map[min(index_2d[0]+1, self.key_rows_num - 1), 0] < self.reaction_delay:
            selection_time += self.timing_map[-1][0] + self.scanning_delay

        # noinspection PyProtectedMember
        if isinstance(self.kde_kernel, stats.kde.gaussian_kde):
            press_times = self.kde_kernel.resample(2)[0]
        elif isinstance(self.kde_kernel, stats._distn_infrastructure.rv_frozen):
            press_times = [t + self.scanning_delay/2 for t in self.kde_kernel.rvs(size=2)]

        else:
            raise(TypeError("Unknown Click Time Distribution Type"))

        error = False

        if press_times[0] < 0:
            index_2d[0] -= 1

            if index_2d[0] < 0:
                index_2d[0] = self.key_rows_num - 1

            error = True

        elif press_times[0] >= self.scanning_delay:
            index_2d[0] += 1

            if index_2d[0] == self.key_rows_num:
                index_2d[0] = 0

            error = True

        if press_times[1] < 0:
            index_2d[1] -= 1

            if index_2d[1] == -1:
                index_2d[1] = self.key_cols_nums[index_2d[0]] - 1

            error = True

        elif press_times[1] >= self.scanning_delay:
            index_2d[1] += 1

            if index_2d[1] == self.key_cols_nums[index_2d[0]]:
                index_2d[1] = index_2d[0]

            error = True

        if error:
            if verbose:
                print("ERROR")
            self.num_errors += 1

        self.winner = self.key_map[index_2d[0], index_2d[1]]
        selection_time += sum(press_times)

        if verbose:

            print(">>> Index " + str(index_2d) + " selected in " + str(round(selection_time, 2)) + " seconds")
            print("    Typed \"" + self.winner + "\"")

        self.num_presses += 2
        self.num_selections += 1
        self.time.set_time(self.time.time()+selection_time)


        self.draw_typed()
        self.draw_words()
        self.update_layout()

    def draw_typed(self):
        if len(self.typed_versions) > 0:
            previous_text = self.typed_versions[-1]
        else:
            previous_text = ""

        if len(self.winner) > 1:
            new_text = self.winner
            new_text = new_text[len(self.lm_prefix):]
        else:
            new_text = self.winner

        if self.winner == kconfig.back_char:
            if self.typed_versions[-1] != '':
                self.typed_versions += [previous_text[:-1]]
        elif self.winner == kconfig.mybad_char:
            if len(self.typed_versions) > 1:
                self.typed_versions = self.typed_versions[:-1]
        elif self.winner == kconfig.clear_char:
            if len(self.typed_versions) > 1:
                self.typed_versions += [" "]
        else:
            self.typed_versions += [previous_text + new_text]

        self.update_prefixes()

    def reset_context(self):
        self.left_context = ""
        self.context = ""
        self.typed = ""
        self.lm_prefix = ""
        self.typed_versions = [""]

    def update_prefixes(self):
        cur_text = self.typed_versions[-1]

        for bc in kconfig.break_chars:
            if bc in cur_text:
                cur_text = cur_text.split(bc)[-1]

        cur_text_words = cur_text.split(" ")
        # print(cur_text_words)
        if cur_text_words[-1] == '' or cur_text_words[-1] in kconfig.break_chars:
            self.lm_prefix = ""
            self.left_context = cur_text
        else:
            self.lm_prefix = cur_text_words[-1]
            self.left_context = cur_text[:(-len(self.lm_prefix) - 1)]

    def save_simulation_data(self, attribute=None):
        if attribute is not None:
            data_file = os.path.join(self.data_loc, "sorted_" + str(int(self.key_config == "sorted"))
                                     + "_nwords_" + str(self.num_word_preds)
                                     + "_wf_" + str(int(self.words_first)) +
                                     "_delay_" + str(round(self.start_scan_delay, 2)) +
                                     "_atr_" + str(attribute) + ".p")
        else:
            data_file = os.path.join(self.data_loc, "sorted_"+str(int(self.key_config == "sorted"))
                                    +"_nwords_"+str(self.num_word_preds)
                                    +"_wf_"+str(int(self.words_first)) +
                                    "_delay_"+str(round(self.start_scan_delay, 2))+".p")

        data_handel = PickleUtil(data_file)

        data_dict = dict()
        data_dict["order"] = self.key_config
        data_dict["words_first"] = self.words_first
        data_dict["num_words"] = self.num_word_preds
        data_dict["delay"] = self.start_scan_delay
        data_dict["errors"] = self.error_rate_avg
        data_dict["selections"] = self.sel_per_min
        data_dict["characters"] = self.char_per_min
        data_dict["presses_char"] = self.press_per_char
        data_dict["presses_word"] = self.press_per_word

        if attribute is not None:
            data_dict["attribute"] = attribute
        data_handel.safe_save(data_dict)

    def gen_data_dir(self):
        if self.job_num is not None:
            if not os.path.exists(os.path.join(self.working_dir, "sim_data")):
                try:
                    os.mkdir(os.path.join(self.working_dir, "sim_data"))
                except FileExistsError:
                    pass

            if not os.path.exists(os.path.join(os.path.join(self.working_dir, "sim_data"), str(self.job_num))):
                try:
                    os.mkdir(os.path.join(os.path.join(self.working_dir, "sim_data"), str(self.job_num)))
                except FileExistsError:
                    pass
            self.data_loc = os.path.join(os.path.join(self.working_dir, "sim_data"), str(self.job_num))
        else:
            dist_found = False
            highest_user_num = 0
            if not os.path.exists(os.path.join(self.working_dir, "sim_data")):
                try:
                    os.mkdir(os.path.join(self.working_dir, "sim_data"))
                except FileExistsError:
                    pass

            try:
                os.mkdir(os.path.join(os.path.join(self.working_dir, "sim_data"), str(highest_user_num+1)))
            except FileExistsError:
                pass
            self.data_loc = os.path.join(os.path.join(self.working_dir, "sim_data"), str(highest_user_num+1))


def main():
    print("****************************\n****************************\n[Loading...]")

    words_first_range = [True, False]
    order_range = ["sorted", "default"]
    order_range = ["sorted"]
    num_words_range = np.arange(0, 20, 1).tolist()
    print(num_words_range)

    parameters_dict = dict()
    for wf in words_first_range:
        for kc in order_range:
            for nw in num_words_range:
                parameters_dict["order"] = kc
                parameters_dict["words_first"] = wf
                parameters_dict["num_words"] = nw
                parameters_dict["delay"] = 0
                SU = SimulatedUser(job_num=1)
                SU.parameter_metrics(parameters_dict, 500, 20)


    # SU = SimulatedUser(job_num=1)
    # SU.parameter_metrics(dict())
    # handel = PickleUtil("sim_data/1/sorted_0_nwords_6_wf_1.p")
    # data = handel.safe_load()
    # print(data)


if __name__ == "__main__":
    main()
