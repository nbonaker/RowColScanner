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
from pickle_util import PickleUtil

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
        # get user data before initialization
        # self.gen_data_handel()
        #
        # self.up_handel = PickleUtil(os.path.join(self.user_handel, 'user_preferences.p'))
        # user_preferences = self.up_handel.safe_load()
        # if user_preferences is None:
        #     first_load = True
        #     user_preferences = ['default', 1, False, 'alpha', 'off', 12, True]
        #     self.up_handel.safe_save(user_preferences)
        # else:
        #     first_load = False

        self.font_scale = 1

        self.key_chars = kconfig.key_chars
        self.num_words = 3
        self.speed = config.default_rotate_ind
        self.sound_set = True

        self.key_chars = kconfig.key_chars


        self.lm_prefix = ""
        self.left_context = ""
        self.typed_versions = []

        self.cwd = os.getcwd()
        self.gen_data_handel()

        lm_path = os.path.join(os.path.join(self.cwd, 'resources'), 'lm_word_medium.kenlm')
        vocab_path = os.path.join(os.path.join(self.cwd, 'resources'), 'vocab_100k')

        self.lm = LanguageModel(lm_path, vocab_path)

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
        self.key_layout = np.array(self.key_chars)
        closest_square = int(np.ceil(np.sqrt(len(self.key_layout) + self.num_words)))
        num_vacancies = np.square(closest_square) - len(self.key_layout) - self.num_words

        self.key_layout = np.concatenate((self.key_layout, np.array([kconfig.word_char for i in range(self.num_words)])))
        self.key_layout = np.concatenate((self.key_layout, np.zeros(num_vacancies)))
        self.key_layout = np.reshape(self.key_layout, (closest_square, closest_square))

        empty_index = np.sum(np.where(self.key_layout != '0.0', 1, 0), axis=1).tolist().index(0)
        self.key_layout = self.key_layout[:empty_index]

        self.key_rows_num = len(self.key_layout)
        self.key_cols_nums = np.sum(np.where(self.key_layout != '0.0', 1, 0), axis=1).tolist()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Space:
            self.on_press()

    def change_speed(self, value):
        self.speed = value
        
    def toggle_sound_button(self, value):
        self.sound_set = value
        self.mainWidget.sldLabel.setFocus()

    def draw_words(self):
        self.words_li = self.lm.get_words(self.left_context, self.lm_prefix, self.num_words)

    def on_timer(self):
        if self.focusWidget() == self.mainWidget.text_box:
            self.mainWidget.sldLabel.setFocus()  # focus on not toggle-able widget to allow keypress event

        if self.row_scan:
            self.row_scan_num += 1
            if self.row_scan_num >= self.key_rows_num:
                self.row_scan_num = 0
        elif self.col_scan:
            self.col_scan_num += 1
            if self.col_scan_num >= self.key_cols_nums[self.row_scan_num]:
                self.col_scan_num = 0

        self.mainWidget.highlight_grid()

    def on_press(self):
        if self.sound_set:
            self.play()
        if self.row_scan:
            self.row_scan = False
            self.col_scan = True
        elif self.col_scan:
            self.make_selection()

    def make_selection(self):
        self.winner = self.key_layout[self.row_scan_num][self.col_scan_num]

        self.draw_typed()

        self.draw_words()
        self.mainWidget.update_grid()
        print(self.winner)


        self.col_scan = False
        self.row_scan = True
        self.row_scan_num = -1
        self.col_scan_num = -1

    def draw_typed(self):
        previous_text = self.mainWidget.text_box.toPlainText()
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
                self.mainWidget.text_box.setText("<span style='color:#000000;'>" + self.typed_versions[-1] + "</span>")
        elif self.winner == kconfig.mybad_char:
            if len(self.typed_versions) > 1:
                self.typed_versions = self.typed_versions[:-1]
                self.mainWidget.text_box.setText("<span style='color:#000000;'>" + self.typed_versions[-1] + "</span>")
        else:
            self.typed_versions += [previous_text + new_text]
            if new_text in kconfig.break_chars:
                new_text = new_text + ' '
                if previous_text[-1] == " ":
                    previous_text = previous_text[:-1]
            if new_text[-1] == " ":
                new_text = new_text[:-1]+"_"
            self.mainWidget.text_box.setText(
                "<span style='color:#000000;'>" + previous_text + "</span><span style='color:#00dd00;'>"
                + new_text + "</span>")
        self.mainWidget.text_box.update()
        self.update_prefixes()

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

    def closeEvent(self, event):
        print("CLOSING THRU CLOSEEVENT")
        self.quit(event)
        # self.deleteLater()

    def quit(self, event=None):
        self.close()


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
