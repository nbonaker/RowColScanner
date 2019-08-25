from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
import string

import sys
import config
import kconfig
from pickle_util import PickleUtil
from phrases import Phrases
import os
import zipfile
import numpy as np
import time

from widgets import VerticalSeparator, HorizontalSeparator, myQLabel


# noinspection PyArgumentList,PyAttributeOutsideInit
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, screen_res):
        super(MainWindow, self).__init__()

        self.screen_res = screen_res
        # Load User Preferences

    def init_ui(self):

        self.mainWidget = MainKeyboardWidget(self, self.key_chars, self.screen_res)
        self.mainWidget.init_ui()
        self.setCentralWidget(self.mainWidget)

        # SimulatedUser Layout Menu Actions
        self.default_layout_action = QtWidgets.QAction('&Alphabetical', self, checkable=True)
        self.default_layout_action.triggered.connect(lambda: self.layout_change_event('default'))

        self.sorted_layout_action = QtWidgets.QAction('&Frequency Sorted', self, checkable=True)
        self.sorted_layout_action.triggered.connect(lambda: self.layout_change_event('sorted'))

        # Word Location Action
        self.top_word_action = QtWidgets.QAction('&Top (Default)', self, checkable=True)
        self.top_word_action.triggered.connect(lambda: self.word_change_event('top'))

        self.bottom_word_action = QtWidgets.QAction('&Bottom', self, checkable=True)
        self.bottom_word_action.triggered.connect(lambda: self.word_change_event('bottom'))

        # Phrase Prompts Action
        self.phrase_prompts_action = QtWidgets.QAction('&Study Mode', self, checkable=True)
        self.phrase_prompts_action.triggered.connect(self.phrase_prompts_event)

        exit_action = QtWidgets.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        # exit_action.triggered.connect(QtWidgets.qApp.quit)
        exit_action.triggered.connect(self.closeEvent)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_action)

        # View Menu Actions
        view_menu = menubar.addMenu('&View')
        keyboard_menu = view_menu.addMenu('&Keybaord Layout')
        keyboard_menu.addAction(self.default_layout_action)
        keyboard_menu.addAction(self.sorted_layout_action)

        word_menu = view_menu.addMenu('&Word Prediction Location')
        word_menu.addAction(self.top_word_action)
        word_menu.addAction(self.bottom_word_action)

        # Tools Menu Actions
        self.log_data_action = QtWidgets.QAction('&Data Logging', self, checkable=True)
        self.log_data_action.triggered.connect(self.log_data_event)

        self.compress_data_action = QtWidgets.QAction('&Compress Data', self, checkable=False)
        self.compress_data_action.triggered.connect(self.compress_data_event)

        # Help Menu Actions
        help_action = QtWidgets.QAction('&Help', self)
        help_action.setStatusTip('Nomon help')
        help_action.triggered.connect(self.help_event)

        about_action = QtWidgets.QAction('&About', self)
        about_action.setStatusTip('Application information')
        about_action.triggered.connect(self.about_event)

        tools_menu = menubar.addMenu('&Tools')
        tools_menu.addAction(self.phrase_prompts_action)
        tools_menu.addAction(self.log_data_action)
        tools_menu.addAction(self.compress_data_action)


        self.setWindowTitle('Row Column Scanner')

        self.icon = QtGui.QIcon(os.path.join("icons/", 'rowcol.png'))
        self.setWindowIcon(self.icon)
        self.setGeometry(self.screen_res[0] * 0.05, self.screen_res[1] * 0.0675, self.screen_res[0] * 0.9,
                         self.screen_res[1] * 0.85)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        self.show()
        self.window_size = (self.size().width(), self.size().height())

        self.check_filemenu()

    def check_filemenu(self):
        def switch(unit, mode):
            if mode == unit.isChecked():
                pass
            else:
                unit.toggle()

        # check layout
        switch(self.default_layout_action, self.key_config == "default")
        switch(self.sorted_layout_action, self.key_config == "sorted")

        # check word count
        switch(self.top_word_action, self.words_first)
        switch(self.bottom_word_action, not self.words_first)

        # check log data
        switch(self.log_data_action, self.is_write_data)

        switch(self.phrase_prompts_action, self.phrase_prompts)

    def phrase_prompts_event(self):
        if self.phrase_prompts:
            phrase_status = False
        else:
            phrase_status = True

        if self.phrases is None:
            self.phrases = Phrases("resources/comm2.dev")

        self.phrase_prompts = phrase_status
        if phrase_status == True:
            self.phrases.sample()
            self.update_phrases(self.typed_versions[-1], "")

            self.is_write_data = True
            choice_dict = {"time": time.time(), "undo": False, "backspace": False, "typed": "", "target": self.phrases.cur_phrase}
            self.params_handle_dict['choice'].append(choice_dict)


            self.mainWidget.cb_pause.setChecked(True)
            self.top_word_action.trigger()
            self.sorted_layout_action.trigger()

            self.mainWidget.cb_pause.setEnabled(False)
            self.mainWidget.speed_slider_label.setStyleSheet('QLabel { color: grey }')
            self.mainWidget.sldLabel.setStyleSheet('QLabel { color: grey }')

            self.mainWidget.extra_delay_label.setStyleSheet('QLabel { color: grey }')
            self.mainWidget.extra_sldLabel.setStyleSheet('QLabel { color: grey }')

            self.default_layout_action.setEnabled(False)
            self.sorted_layout_action.setEnabled(False)
            self.bottom_word_action.setEnabled(False)
            self.top_word_action.setEnabled(False)
            self.log_data_action.setEnabled(False)

        else:
            self.typed_versions.append("")
            self.left_context = ""
            self.context = ""
            self.typed = ""
            self.lm_prefix = ""
            self.mainWidget.text_box.setText("")

            self.mainWidget.cb_pause.setEnabled(True)
            self.mainWidget.speed_slider.setEnabled(True)
            self.mainWidget.extra_delay_slider.setEnabled(True)

            self.default_layout_action.setEnabled(True)
            self.sorted_layout_action.setEnabled(True)
            self.top_word_action.setEnabled(True)
            self.bottom_word_action.setEnabled(True)
            self.log_data_action.setEnabled(True)

            self.mainWidget.speed_slider_label.setStyleSheet('QLabel { color: black }')
            self.mainWidget.sldLabel.setStyleSheet('QLabel { color: black }')
            self.mainWidget.extra_delay_label.setStyleSheet('QLabel { color: black }')
            self.mainWidget.extra_sldLabel.setStyleSheet('QLabel { color: black }')

            self.mainWidget.error_label.setStyleSheet("color: rgb(0, 0, 0);")
            self.mainWidget.wpm_label.setStyleSheet("color: rgb(0, 0, 0);")

        self.check_filemenu()
        self.update_phrases("", "")

    def word_change_event(self, location):
        if location == 'top':
            self.words_first = True
        elif location == 'bottom':
            self.words_first = False

        self.check_filemenu()
        self.generate_layout()

        self.mainWidget = MainKeyboardWidget(self, self.key_chars, self.screen_res)
        self.mainWidget.init_ui()
        self.setCentralWidget(self.mainWidget)

    def layout_change_event(self, layout):
        message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Change SimulatedUser Layout",
                                            "This will change the clock "
                                            "layout to <b>" + layout + "</b"
                                                                       "> order. <b>NOTICE:</b> You "
                                                                       "will have to restart Nomon for"
                                                                       " these changes to take effect",
                                            QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok)
        message_box.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        message_box.setWindowIcon(self.icon)

        self.key_config = layout

        self.check_filemenu()
        self.generate_layout()

        self.mainWidget = MainKeyboardWidget(self, self.key_chars, self.screen_res)
        self.mainWidget.init_ui()
        self.setCentralWidget(self.mainWidget)

    def log_data_event(self):
        message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Data Logging Consent", "We would like to save "
                                  "some data regarding your clicking time relative to Noon to help us improve Nomon. "
                                  "All data collected is anonymous and only your click times will be saved. <b> Do you"
                                  " consent to allowing us to log click timing data locally?</b> (Note: you can change"
                                  " your preference anytime in the Tools menu).")
        message_box.addButton(QtWidgets.QMessageBox.Yes)
        message_box.addButton(QtWidgets.QMessageBox.No)
        message_box.setDefaultButton(QtWidgets.QMessageBox.Yes)
        message_box.setWindowIcon(self.icon)

        reply = message_box.exec_()
        
        if reply == QtWidgets.QMessageBox.No:
            self.is_write_data = False
        elif reply == QtWidgets.QMessageBox.Yes:
            self.is_write_data = True
        self.check_filemenu()

    def compress_data_event(self):
        self.save_data()
        data_save_path, _ = os.path.split(self.data_path)
        data_zip_path = os.path.join(data_save_path, "row_col_data.zip")
        zf = zipfile.ZipFile(data_zip_path, "w")
        for dirname, subdirs, files in os.walk(self.data_path):
            sub_dirname = dirname[len(self.data_path):]

            zf.write(dirname, sub_dirname)
            for filename in files:
                file_path = os.path.join(dirname, filename)
                sub_file_path = file_path[len(self.data_path):]
                zf.write(file_path, sub_file_path)
        zf.close()

        message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Data Compression", "We have compressed your data into a ZIP"
                                                                           " archive accessible in the location"
                                                                           "listed under \"Details\". Please press \""
                                                                           "Show Details\", and email the "
                                                                           "ZIP archive to the listed email address. We"
                                                                           " greatly appreciate your willingness to "
                                                                           "help us make Row Column Scanner better!")
        message_box.setDetailedText("File Path: \n" + data_save_path + "\n\n Email: \nnomonstudy@gmail.com")
        message_box.addButton(QtWidgets.QMessageBox.Ok)
        message_box.setWindowIcon(self.icon)

        reply = message_box.exec_()

    def about_event(self):
        # noinspection PyTypeChecker
        QtWidgets.QMessageBox.question(self, 'About Nomon', " Copyright 2019 Nicholas Bonaker, Keith Vertanen,"
                                                            " Emli-Mari Nel, Tamara Broderick. This file is part of "
                                                            "the Nomon software. Nomon is free software: you can "
                                                            "redistribute it and/or modify it under the terms of the "
                                                            "MIT License reproduced below.\n\n "
                                                            "Permission is hereby granted, free of charge, to any "
                                                            "person obtaining a copy of this software and associated"
                                                            " documentation files (the \"Software\"), to deal in the"
                                                            " Software without restriction, including without "
                                                            "limitation the rights to use, copy, modify, merge, "
                                                            "publish, distribute, sublicense, and/or sell copies of the"
                                                            " Software,and to permit persons to whom the Software is"
                                                            " furnished to do so, subject to the following conditions: "
                                                            "The above copyright notice and this permission notice"
                                                            " shall be included in all copies or substantial portions"
                                                            " of the Software. \n\n "
                                                            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY"
                                                            "OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT"
                                                            " LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS"
                                                            " FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO"
                                                            " EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE"
                                                            " LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,"
                                                            " WHETHER IN AN ACTION OF CONTRACT, TORT OR"
                                                            " OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION"
                                                            " WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS"
                                                            " IN THE SOFTWARE.\n\n"
                                                            " <https://opensource.org/licenses/mit-license.html>",
                                       QtWidgets.QMessageBox.Ok)

    def help_event(self):
        self.launch_help()

    def retrain_event(self):
        self.launch_retrain()

    def resizeEvent(self, event):
        self.environment_change = True
        self.in_pause = True
        # for clock in self.mainWidget.clocks:
        #     clock.redraw_text = True
        #     clock.calculate_clock_size()
        # QtCore.QTimer.singleShot(100, self.init_clocks)
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.window_size = (self.size().width(), self.size().height())
        self.in_pause = False


class MainKeyboardWidget(QtWidgets.QWidget):

    def __init__(self, parent, layout, screen_res):
        super(MainKeyboardWidget, self).__init__()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.parent = parent
        print(type(self.parent))
        self.layout = layout
        self.screen_res = screen_res
        self.size_factor = min(self.screen_res) / 1080.

    # noinspection PyUnresolvedReferences
    def init_ui(self):

        # generate slider for clock rotation speed
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.speed_slider.setRange(config.scale_min, config.scale_max)
        self.speed_slider.setValue(self.parent.speed)
        self.speed_slider_label = QtWidgets.QLabel('Scanning Speed:')

        self.speed_slider_label.setFont(config.top_bar_font[self.parent.font_scale])
        self.sldLabel = QtWidgets.QLabel(str(self.speed_slider.value()))
        self.sldLabel.setFont(config.top_bar_font[self.parent.font_scale])

        # generate slider for extra delay rotation speed
        self.extra_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.extra_delay_slider.setRange(config.extra_scale_min, config.extra_scale_max)
        self.extra_delay_slider.setValue(self.parent.pause_index)
        self.extra_delay_label = QtWidgets.QLabel('First Row Scan Speed:')

        self.extra_delay_label.setFont(config.top_bar_font[self.parent.font_scale])
        self.extra_sldLabel = QtWidgets.QLabel(str(self.extra_delay_slider.value()))
        self.extra_sldLabel.setFont(config.top_bar_font[self.parent.font_scale])

        # wpm label
        self.wpm_label = QtWidgets.QLabel("Words/Min: " + "----")
        self.wpm_label.setFont(config.top_bar_font[self.parent.font_scale])

        self.error_label = QtWidgets.QLabel("Error Rate: " + "----")
        self.error_label.setFont(config.top_bar_font[self.parent.font_scale])

        # generate learn, speak, talk checkboxes
        self.cb_sound = QtWidgets.QCheckBox('Sound', self)
        self.cb_pause = QtWidgets.QCheckBox('Pause', self)

        self.cb_sound.toggle()
        self.cb_pause.toggle()
        self.cb_sound.setFont(config.top_bar_font[self.parent.font_scale])
        self.cb_pause.setFont(config.top_bar_font[self.parent.font_scale])

        # generate label grid from layout
        self.layout_grid()

        self.text_box = QtWidgets.QTextEdit("", self)

        self.text_box.setFont(config.text_box_font[self.parent.font_scale])
        self.text_box.setMinimumSize(300, 100)
        self.text_box.setReadOnly(True)


        self.speed_slider.valueChanged[int].connect(self.change_scanning_value)
        self.extra_delay_slider.valueChanged[int].connect(self.change_extra_value)

        self.cb_sound.toggled[bool].connect(self.parent.toggle_sound_button)
        self.cb_pause.toggled[bool].connect(self.parent.toggle_pause_button)

        # layout slider and checkboxes
        top_hbox = QtWidgets.QHBoxLayout()
        top_hbox.addWidget(self.speed_slider_label, 1)
        top_hbox.addStretch(1)
        top_hbox.addWidget(self.speed_slider, 16)
        top_hbox.addStretch(1)
        top_hbox.addWidget(self.sldLabel, 1)
        top_hbox.addStretch(2)

        top_hbox.addWidget(self.extra_delay_label, 1)
        top_hbox.addStretch(1)
        top_hbox.addWidget(self.extra_delay_slider, 8)
        top_hbox.addStretch(1)
        top_hbox.addWidget(self.extra_sldLabel, 1)
        top_hbox.addStretch(2)

        # entry metrics vbox
        text_stat_vbox = QtWidgets.QVBoxLayout()
        text_stat_vbox.addWidget(self.wpm_label)
        text_stat_vbox.addWidget(self.error_label)

        top_hbox.addLayout(text_stat_vbox)
        top_hbox.addStretch(2)

        # top_hbox.addWidget(self.cb_talk, 1)
        top_hbox.addWidget(self.cb_sound, 1)
        top_hbox.addWidget(self.cb_pause, 1)
        top_hbox.addStretch(1)

        # stack layouts vertically
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setSpacing(0)
        self.vbox.addLayout(top_hbox)
        self.vbox.addStretch(1)

        self.splitter1 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter1.addWidget(self.text_box)
        self.splitter1.setSizes([1, 1])
        self.text_box.setMaximumHeight(160 * self.size_factor)
        self.vbox.addLayout(self.label_grid, 30)
        self.vbox.addWidget(HorizontalSeparator())
        self.vbox.addStretch(1)
        self.vbox.addWidget(self.splitter1, 10)
        self.setLayout(self.vbox)

        self.frame_timer = QtCore.QTimer()
        self.frame_timer.timeout.connect(self.parent.on_timer)
        self.frame_timer.start(config.ideal_wait_s * 1000)

        self.data_save_timer = QtCore.QTimer()
        self.data_save_timer.timeout.connect(self.parent.data_auto_save)
        self.data_save_timer.start(config.auto_save_time * 60000)

        # Tool Tips
        # noinspection PyCallByClass
        QtWidgets.QToolTip.setFont(QtGui.QFont('Monospace', 12))
        self.setToolTip("This is the Nomon Keyboard. To select an option, \n "
                        "find the clock immediately to its left. Press the \n"
                        "spacebar when the moving hand is near noon.")
        self.speed_slider_label.setToolTip("This slider scales the speed of clock rotation. Higher \nvalues correspond "
                                           "to the clock hand moving faster.")
        self.speed_slider.setToolTip("This slider scales the speed of clock rotation. Higher \n"
                                     "values correspond to the clock hand moving faster.")

        self.setMinimumWidth(800*self.size_factor)

    def paintEvent(self, e):
        self.text_box.setStyleSheet("background-color:;")
        self.splitter1.setStyleSheet("background-color:;")
        self.in_focus = True
        # for clock in self.clocks:
        #     clock.in_focus = True
        #     clock.redraw_text = True
        #     clock.update()

    def change_scanning_value(self, value):  # Change clock speed
        if self.parent.phrase_prompts:
            inc_dir = np.sign(value - self.parent.speed)
            value = self.parent.speed + inc_dir
            self.speed_slider.setValue(value)
            self.speed_slider.setEnabled(False)
            self.speed_slider_label.setStyleSheet('QLabel { color: grey }')
            self.sldLabel.setStyleSheet('QLabel { color: grey }')

        self.sldLabel.setText(str(self.speed_slider.value()))
        self.parent.change_speed(value)

        self.frame_timer.stop()
        self.frame_timer.start(config.period_li[self.parent.speed] * 1000)

    def change_extra_value(self, value):
        if self.parent.phrase_prompts:
            inc_dir = np.sign(value - self.parent.pause_index)
            value = self.parent.pause_index + inc_dir
            self.extra_delay_slider.setValue(value)
            self.extra_delay_slider.setEnabled(False)
            self.extra_delay_label.setStyleSheet('QLabel { color: grey }')
            self.extra_sldLabel.setStyleSheet('QLabel { color: grey }')

        self.extra_sldLabel.setText(str(self.extra_delay_slider.value()))
        self.parent.change_extra_delay(value)

    def layout_grid(self):
        self.label_grid = QtWidgets.QGridLayout()
        self.labels = []
        self.labels_by_row = []
        self.labels_word = []
        word_count = 0
        for row_num, row in enumerate(self.parent.key_layout):
            row_labels = []
            for col_num, text in enumerate(row):
                if text != '0.0':
                    label = myQLabel()
                    self.labels.append(label)
                    row_labels.append(label)

                    if text == kconfig.back_char:
                        text = "Backspace"
                    elif text == kconfig.clear_char:
                        text = "Clear"
                    elif text == kconfig.mybad_char:
                        text = "Undo"
                    elif text == " ":
                        text = "_"
                    elif text == kconfig.word_char:
                        if len(self.parent.words_li) > word_count:
                            text = self.parent.words_li[word_count]
                            self.labels_word.append(label)
                            word_count += 1
                        else:
                            text = ""

                    if text == "":
                        label.setText("")
                    else:
                        label.setText(" "+text)

                    self.label_grid.addWidget(label, 2*row_num+1, 2*col_num+1, 1, 1)
                self.label_grid.addWidget(HorizontalSeparator(), 2*row_num, 2*col_num+1)
                self.label_grid.addWidget(VerticalSeparator(), 2 * row_num+1, 2 * col_num)
            self.labels_by_row.append(row_labels)

        row_nums = len(self.parent.key_layout)
        col_nums = len(self.parent.key_layout[0])
        self.label_grid.addWidget(VerticalSeparator(), 0, 2*col_nums+2, 2*row_nums, 1)

    def update_grid(self):
        if len(self.parent.words_li) > 0:
            for label, text in zip(self.labels_word, self.parent.words_li):
                label.setText(" "+text)

                font = label.font()
                font.setPixelSize(70)
                label.setFont(font)
                label.update_font(-1)
                label.update()
        else:
            for label in self.labels_word:
                label.setText("")
                label.update()
                
    def highlight_grid(self):
        if self.parent.row_scan:
            for label in self.labels:
                if label in self.labels_by_row[self.parent.row_scan_num]:
                    label.setStyleSheet("border: 1px outset black; background-color:#aaaaff")
                else:
                    label.setStyleSheet("border: 1px outset black; background-color:")
        elif self.parent.col_scan:
            for label in self.labels:
                if label in self.labels_by_row[self.parent.row_scan_num]:
                    if self.labels_by_row[self.parent.row_scan_num].index(label) == self.parent.col_scan_num:
                        label.setStyleSheet("border: 1px outset black; background-color:#aa77ff")
                    else:
                        label.setStyleSheet("border: 1px outset black; background-color:#aaaaff")
                else:
                    label.setStyleSheet("border: 1px outset black; background-color:")

    def clear_layout(self, layout):
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child)

    def clear_layout_without_delete(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                layout.removeWidget(child.widget())
                layout.update()
            elif child.layout():
                self.clear_layout(child)
