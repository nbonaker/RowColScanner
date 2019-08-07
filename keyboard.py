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

from mainWindow import MainWindow
# import dtree
from kenlm_lm import LanguageModel
from phrases import Phrases
from pickle_util import PickleUtil
from text_stats import calc_MSD

import sys
import os
# import string
import kconfig
import config
import time
from appdirs import user_data_dir
import pathlib

# sys.path.insert(0, os.path.realpath('../KernelDensityEstimation'))

sys._excepthook = sys.excepthook


def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook

if kconfig.target_evt == kconfig.joy_evt:
    import pygame


class Keyboard(MainWindow):

    def __init__(self, screen_res, app):
        super(Keyboard, self).__init__(screen_res)

        self.app = app

        self.font_scale = 1

        self.key_chars = kconfig.key_chars
        self.key_chars_sorted = kconfig.key_chars_sorted
        self.key_config = "sorted"
        # self.key_config = "default"

        self.num_words = 7
        self.words_first = True
        # self.words_first = False

        self.sound_set = True
        self.pause_set = True

        self.lm_prefix = ""
        self.left_context = ""
        self.typed_versions = [""]

        self.cwd = os.getcwd()
        self.gen_data_handel()

        self.up_handel = PickleUtil(os.path.join(self.user_handel, 'user_preferences.p'))
        user_preferences = self.up_handel.safe_load()

        if user_preferences is None:
            user_preferences = ['sorted', config.default_rotate_ind, config.default_pause_ind, True]
            self.up_handel.safe_save(user_preferences)

        self.key_config, self.speed, self.pause_index, self.is_write_data = user_preferences

        self.scanning_delay = config.period_li[self.speed]
        self.extra_delay = config.pause_li[self.pause_index]

        self.params_handle_dict = {'speed': [], 'extra_delay': [], 'params': [], 'start': [], 'press': [], 'choice': []}
        self.num_presses = 0

        self.last_press_time = time.time()
        self.last_update_time = time.time()
        self.next_frame_time = time.time()

        self.params_handle_dict['params'].append([config.period_li[config.default_rotate_ind], config.theta0])
        self.params_handle_dict['start'].append(time.time())
        self.click_time_list = []

        lm_path = os.path.join(os.path.join(self.cwd, 'resources'), 'lm_word_medium.kenlm')
        vocab_path = os.path.join(os.path.join(self.cwd, 'resources'), 'vocab_100k')

        self.lm = LanguageModel(lm_path, vocab_path)

        self.phrase_prompts = False
        if self.phrase_prompts:
            self.phrases = Phrases("resources/comm2.dev")
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
        self.generate_layout()

        self.draw_words()

        self.wpm_data = []
        self.decay_avg_wpm = 0
        self.wpm_time = 0
        self.error_data = []
        self.decay_avg_error = 1

        self.row_scan = True
        self.row_scan_num = -2
        self.col_scan = False
        self.col_scan_num = -1

        self.init_ui()

        # animate

        self.on_timer()

    def gen_data_handel(self):
        self.cwd = os.getcwd()
        self.data_path = user_data_dir('data', 'RowCol')
        if os.path.exists(self.data_path):
            user_files = list(os.walk(self.data_path))
            users = user_files[0][1]
        else:
            pathlib.Path(self.data_path).mkdir(parents=True, exist_ok=True)
            # os.mkdir(data_path)
            user_files = None
            users = []
        input_method = 'text'
        if user_files is not None and len(users) != 0:
            message = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, "Load User Data", "You can either create a new user profile or "
                                                                             "load an existing user profile.")
            message.addButton(QtWidgets.QPushButton('Create New User'), QtWidgets.QMessageBox.YesRole)
            message.addButton(QtWidgets.QPushButton('Load Previous User'), QtWidgets.QMessageBox.NoRole)
            message.setDefaultButton(QtWidgets.QMessageBox.Yes)
            response = message.exec_()
            if response == 0:
                input_method = 'text'
            else:
                input_method = 'list'

        if input_method == 'text':
            valid_user_id = False
            input_text = "Please input a Number that will be used to save your user information"
            while not valid_user_id:
                num, ok = QtWidgets.QInputDialog.getInt(self, "User ID Number Input", input_text)
                if str(num) not in users:
                    valid_user_id = True
                else:
                    input_text = "The user ID you inputed already exists! \n please input a valid user ID or press " \
                                 "\"cancel\" to choose an existing one from a list"
                if ok == 0:
                    input_method = 'list'
                    break
            if input_method == 'text':
                self.user_id = num
                user_id_path = os.path.join(self.data_path, str(self.user_id))
                os.mkdir(user_id_path)

        if input_method == 'list':
            item, ok = QtWidgets.QInputDialog.getItem(self, "Select User ID", "List of save User IDs:", users, 0, False)
            self.user_id = item

        self.user_handel = os.path.join(self.data_path, str(self.user_id))
        user_id_files = list(os.walk(self.user_handel))
        user_id_calibrations = user_id_files[0][1]
        if len(user_id_calibrations) == 0:
            self.data_handel = os.path.join(self.user_handel, 'cal0')
            os.mkdir(self.data_handel)
            user_id_cal_files = None
            self.user_cal_num = 0
        else:
            user_id_cal_files = user_id_files[-1][2]
            self.data_handel = user_id_files[-1][0]
            self.user_cal_num = len(user_id_calibrations)-1
        if user_id_cal_files is not None:
            self.use_num = sum([1 if 'params_data' in file_name else 0 for file_name in user_id_cal_files])
        else:
            self.use_num = 0
        print(self.data_handel)

    def generate_layout(self):
        if self.key_config == "sorted":
            self.keys_list = np.array(self.key_chars_sorted)
            closest_square = int(np.ceil(np.sqrt(len(self.keys_list) + self.num_words)))

            self.key_freq_map = np.zeros((closest_square, closest_square))
            for row_num, row in enumerate(self.key_freq_map):
                for col_num, _ in enumerate(row):
                    self.key_freq_map[row_num][col_num] = row_num + col_num
        else:
            self.keys_list = np.array(self.key_chars)
            closest_square = int(np.ceil(np.sqrt(len(self.keys_list) + self.num_words)))

            self.key_freq_map = np.zeros((closest_square, closest_square))
            for row_num, row in enumerate(self.key_freq_map):
                for col_num, _ in enumerate(row):
                    self.key_freq_map[row_num][col_num] = row_num * closest_square + col_num

        self.key_layout = np.empty((closest_square, closest_square), dtype=str)

        for word in range(self.num_words):  # fill words first
            if self.words_first:
                word_index = np.unravel_index(word, (closest_square, closest_square))
            else:
                word_index = np.unravel_index(closest_square**2 - self.num_words + word,
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

        print(self.key_layout)
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

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Space:
            self.last_gap_time = time.time() - self.last_update_time
            self.last_press_time = time.time()
            self.save_click_time(self.last_press_time, self.last_gap_time, (self.row_scan_num, self.col_scan_num))

            self.on_press()

    def change_speed(self, value):
        old_rotate = config.period_li[self.speed]
        self.speed = value
        self.time_rotate = config.period_li[self.speed]
        self.params_handle_dict['speed'].append([time.time(), old_rotate, self.scanning_delay])

    def change_extra_delay(self, value):
        old_pause_length = config.pause_li[self.pause_index]
        self.pause_index = value
        self.extra_delay = config.pause_li[self.pause_index]
        self.params_handle_dict['extra_delay'].append([time.time(), old_pause_length, self.extra_delay])
        
    def toggle_sound_button(self, value):
        self.sound_set = value
        self.mainWidget.sldLabel.setFocus()

    def toggle_pause_button(self, value):
        self.pause_set = value
        self.mainWidget.sldLabel.setFocus()

    def draw_words(self):
        self.words_li = self.lm.get_words(self.left_context, self.lm_prefix, self.num_words)

    def on_timer(self):
        if self.focusWidget() == self.mainWidget.text_box:
            self.mainWidget.sldLabel.setFocus()  # focus on not toggle-able widget to allow keypress event

        cur_time = time.time()
        if cur_time >= self.next_frame_time:
            self.update_frame()

    def update_frame(self):
        self.last_update_time = time.time()

        if self.row_scan:
            self.row_scan_num += 1
            if self.row_scan_num >= self.key_rows_num:
                self.row_scan_num = 0

            if self.row_scan_num == 0 and self.pause_set:
                self.next_frame_time += (config.period_li[self.speed] + self.extra_delay)
            else:
                self.next_frame_time += config.period_li[self.speed]

        elif self.col_scan:
            self.next_frame_time += config.period_li[self.speed]

            self.col_scan_num += 1
            if self.col_scan_num >= self.key_cols_nums[self.row_scan_num]:
                self.col_scan_num = 0

        self.mainWidget.highlight_grid()

    def on_press(self):

        if self.wpm_time == 0:
            self.wpm_time = time.time()

        if self.phrase_prompts:
            self.mainWidget.speed_slider.setEnabled(False)
            self.mainWidget.extra_delay_slider.setEnabled(False)
            self.mainWidget.speed_slider_label.setStyleSheet('QLabel { color: grey }')
            self.mainWidget.sldLabel.setStyleSheet('QLabel { color: grey }')

            self.mainWidget.extra_delay_label.setStyleSheet('QLabel { color: grey }')
            self.mainWidget.extra_sldLabel.setStyleSheet('QLabel { color: grey }')

        if self.sound_set:
            self.play()
        if self.row_scan:
            self.row_scan = False
            self.col_scan = True
            self.next_frame_time = time.time()
            self.on_timer()

        elif self.col_scan:
            self.make_selection()
        self.num_presses += 1

    def save_click_time(self, last_press_time, last_gap_time, index):
        self.params_handle_dict['press'].append([last_press_time])
        self.click_time_list.append((last_gap_time, index))

    def make_selection(self):
        self.winner = self.key_layout[max(0, self.row_scan_num)][max(0, self.col_scan_num)]

        self.draw_typed()

        self.draw_words()
        self.mainWidget.update_grid()
        print(self.winner)

        self.col_scan = False
        self.row_scan = True
        self.row_scan_num = -1
        self.col_scan_num = -1

        self.next_frame_time = time.time()
        self.on_timer()

    def draw_typed(self):
        if len(self.typed_versions) > 0:
            previous_text = self.typed_versions[-1]
        else:
            previous_text = ""

        if "_" in previous_text:
            previous_text = previous_text.replace("_", " ")

        if self.winner == kconfig.word_char:
            new_text = self.mainWidget.labels_by_row[self.row_scan_num][self.col_scan_num].text()[1:] + ' '
            new_text = new_text[len(self.lm_prefix):]
        else:
            new_text = self.winner

        if self.winner == kconfig.back_char:
            # self.prefix = self.prefix[:-1]
            if self.typed_versions[-1] != '':
                self.typed_versions += [previous_text[:-1]]
                input_text = "<span style='color:#000000;'>" + self.typed_versions[-1] + "</span>"
                self.mainWidget.text_box.setText("<span style='color:#000000;'>" + self.typed_versions[-1] + "</span>")
            else:
                input_text = ""
        elif self.winner == kconfig.mybad_char:
            if len(self.typed_versions) > 1:
                self.typed_versions = self.typed_versions[:-1]
                input_text = "<span style='color:#000000;'>" + self.typed_versions[-1] + "</span>"
                self.mainWidget.text_box.setText("<span style='color:#000000;'>" + self.typed_versions[-1] + "</span>")
            else:
                input_text = ""
        elif self.winner == kconfig.clear_char:
            if len(self.typed_versions) > 1:
                self.typed_versions += [" "]
                self.mainWidget.text_box.setText("")
            input_text = ""
        else:
            self.typed_versions += [previous_text + new_text]
            if new_text in kconfig.break_chars:
                new_text = new_text + ' '
                if previous_text[-1] == " ":
                    previous_text = previous_text[:-1]
            if len(new_text) > 0 and new_text[-1] == " ":
                new_text = new_text[:-1]+"_"
                new_text = new_text[:-1]+"_"
            input_text = "<span style='color:#000000;'>" + previous_text + "</span><span style='color:#0000dd;'>" \
                         + new_text + "</span>"
            self.mainWidget.text_box.setText(
                "<span style='color:#000000;'>" + previous_text + "</span><span style='color:#0000dd;'>"
                + new_text + "</span>")
        self.mainWidget.text_box.update()
        self.update_prefixes()

        # write output
        if self.is_write_data:
            choice_dict = {"time": time.time(), "undo": self.winner == kconfig.mybad_char,
                           "backspace": self.winner == kconfig.back_char, "typed": self.typed_versions[-1]}
            if self.phrase_prompts:
                choice_dict["target"] = self.phrases.cur_phrase

            self.params_handle_dict['choice'].append(choice_dict)

        if self.phrase_prompts:
            self.update_phrases(self.typed_versions[-1], input_text)

    def text_stat_update(self, phrase, typed):

        _, cur_error = calc_MSD(phrase, typed)

        self.error_data = [cur_error] + self.error_data
        decaying_weights = np.power(0.8, np.arange(len(self.error_data)))
        decaying_weights /= np.sum(decaying_weights)

        decay_avg_error = sum(np.array(self.error_data)*decaying_weights)
        error_delta = decay_avg_error / (self.decay_avg_error + 0.000001)
        self.decay_avg_error = decay_avg_error

        self.wpm_data = [(len(typed.split(" "))-1) / (time.time() - self.wpm_time)*60] + self.wpm_data
        self.wpm_time = 0
        decaying_weights = np.power(0.8, np.arange(len(self.wpm_data)))
        decaying_weights /= np.sum(decaying_weights)

        decay_avg_wpm = sum(np.array(self.wpm_data) * decaying_weights)
        wpm_delta = decay_avg_wpm / (self.decay_avg_wpm + 0.000001)
        self.decay_avg_wpm = decay_avg_wpm

        if error_delta > 1:
            error_red = int(min(4, error_delta)*63)
            error_green = 0
        else:
            error_green = int(min(4, 1/error_delta) * 63)
            error_red = 0

        if wpm_delta < 1:
            wpm_red = int(min(4, wpm_delta)*63)
            wpm_green = 0
        else:
            wpm_green = int(min(4, 1/wpm_delta) * 63)
            wpm_red = 0


        self.mainWidget.error_label.setStyleSheet("color: rgb("+str(error_red)+", "+str(error_green)+", 0);")

        self.mainWidget.wpm_label.setStyleSheet("color: rgb(" + str(wpm_red) + ", " + str(wpm_green) + ", 0);")

        self.mainWidget.error_label.setText("Error Rate: " + str(round(decay_avg_error, 2)))
        self.mainWidget.wpm_label.setText("Words/Min: " + str(round(decay_avg_wpm, 2)))

    def reset_context(self):
        self.left_context = ""
        self.context = ""
        self.typed = ""
        self.lm_prefix = ""

    def update_phrases(self, cur_text, input_text):
        cur_phrase_typed, next_phrase = self.phrases.compare(cur_text)
        cur_phrase_highlighted = self.phrases.highlight(cur_text)

        if next_phrase:
            self.text_stat_update(self.phrases.cur_phrase, self.typed_versions[-1])

            self.typed_versions = ['']
            self.mainWidget.text_box.setText('')
            self.mainWidget.speed_slider.setEnabled(True)
            self.mainWidget.speed_slider_label.setStyleSheet('QLabel { color: blue }')
            self.mainWidget.sldLabel.setStyleSheet('QLabel { color: blue }')

            self.mainWidget.extra_delay_slider.setEnabled(True)
            self.mainWidget.extra_delay_label.setStyleSheet('QLabel { color: blue }')
            self.mainWidget.extra_sldLabel.setStyleSheet('QLabel { color: blue }')

            self.clear_text = False
            undo_text = 'Clear'

            self.phrases.sample()
            input_text = ""
            cur_phrase_highlighted = self.phrases.highlight("")
            self.reset_context()

            if self.is_write_data:
                choice_dict = {"time": time.time(), "undo": False, "backspace": False, "typed": "", "target": self.phrases.cur_phrase}
                self.params_handle_dict['choice'].append(choice_dict)


        self.mainWidget.text_box.setText(
            "<p>" + cur_phrase_highlighted + "<\p><p>" + input_text + "</span><\p>")

    def update_prefixes(self):
        cur_text = self.typed_versions[-1]

        for bc in kconfig.break_chars:
            if bc in cur_text:
                cur_text = cur_text.split(bc)[-1]

        cur_text_words = cur_text.split(" ")
        print(cur_text_words)
        if cur_text_words[-1] == '' or cur_text_words[-1] in kconfig.break_chars:
            self.lm_prefix = ""
            self.left_context = cur_text
        else:
            self.lm_prefix = cur_text_words[-1]
            self.left_context = cur_text[:(-len(self.lm_prefix) - 1)]

    def play(self):
        sound_file = "icons/bell.wav"
        QtMultimedia.QSound.play(sound_file)

    def data_auto_save(self):
        if len(self.click_time_list) > 0:
            print("auto saving data")
            self.save_data()

    def closeEvent(self, event):
        print("CLOSING THRU CLOSEEVENT")
        self.quit(event)
        # self.deleteLater()

    def quit(self, event=None):
        self.save_data()
        self.close()

    def save_data(self):
        user_preferences = [self.key_config, self.speed, self.pause_index, self.is_write_data]
        self.up_handel.safe_save(user_preferences)

        self.click_data_path = os.path.join(self.data_handel,
                                            'click_time_log_' + str(self.use_num) + '.p')
        self.params_data_path = os.path.join(self.data_handel,
                                             'params_data_use_num' + str(self.use_num) + '.p')
        print(self.params_data_path)
        PickleUtil(self.click_data_path).safe_save(
            {'user id': self.user_id, 'use_num': self.use_num, 'click time list': self.click_time_list,
             'rotate index': self.speed})
        PickleUtil(self.params_data_path).safe_save(self.params_handle_dict)

def main():
    print("****************************\n****************************\n[Loading...]")

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    screen_res = (app.desktop().screenGeometry().width(), app.desktop().screenGeometry().height())

    # splash = StartWindow(screen_res, True)
    app.processEvents()
    ex = Keyboard(screen_res, app)

    # if first_load:
    #     ex.first_load = True
    #     welcome = Pretraining(screen_res, ex)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
