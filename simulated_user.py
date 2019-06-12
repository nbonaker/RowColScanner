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
from keyboard import Keyboard
from kenlm_lm import LanguageModel
from phrases import Phrases
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


class SimulatedUser(Keyboard):

    def __init__(self, screen_res, app):
        super(SimulatedUser, self).__init__(screen_res, app)
        self.init_sim_data()

    def init_sim_data(self):
        # self.init_clocks()
        self.num_selections = 0
        self.sel_per_min = []

        self.num_chars = 0
        self.char_per_min = []

        self.num_words = 0

        self.num_presses = 0
        self.press_per_sel = []
        self.press_per_char = []
        self.press_per_word = []

        self.num_errors = 0
        self.error_rate_avg = []
        self.kde_errors = []
        self.kde_errors_avg = None

        # self.on_timer()
        self.is_winner = False
        self.winner_text = ""



def main():
    print("****************************\n****************************\n[Loading...]")

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    screen_res = (app.desktop().screenGeometry().width(), app.desktop().screenGeometry().height())

    # splash = StartWindow(screen_res, True)
    app.processEvents()
    ex = SimulatedUser(screen_res, app)

    # if first_load:
    #     ex.first_load = True
    #     welcome = Pretraining(screen_res, ex)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
