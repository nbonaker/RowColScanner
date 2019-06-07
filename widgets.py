from __future__ import division
from PyQt5 import QtCore, QtGui, QtWidgets
import math
from numpy import array

class myQLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kargs):
        super(myQLabel, self).__init__(*args, **kargs)

        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                             QtWidgets.QSizePolicy.Ignored))

        self.setMinSize(14)
        # self.setMaximumHeight(40)

    def setMinSize(self, minfs):

        f = self.font()
        f.setPixelSize(minfs)
        br = QtGui.QFontMetrics(f).boundingRect(self.text())

        self.setMinimumSize(br.width(), br.height())

    def resizeEvent(self, event):
        super(myQLabel, self).resizeEvent(event)

        if not self.text():
            return

        # --- fetch current parameters ----

        f = self.font()
        cr = self.contentsRect()

        # --- iterate to find the font size that fits the contentsRect ---

        dw = event.size().width() - event.oldSize().width()  # width change
        dh = event.size().height() - event.oldSize().height()  # height change

        fs = max(f.pixelSize(), 1)
        while True:

            f.setPixelSize(fs)
            br = QtGui.QFontMetrics(f).boundingRect(self.text())

            if dw >= 0 and dh >= 0:  # label is expanding

                if br.height() <= cr.height()*0.8 and br.width() <= cr.width()*0.8:
                    fs += 1
                else:
                    f.setPixelSize(max(fs - 1, 1))  # backtrack
                    break

            else:  # label is shrinking

                if br.height() > cr.height()*0.8 or br.width() > cr.width()*0.8:
                    fs -= 1
                else:
                    break

            if fs < 1: break

        # --- update font size ---

        self.setFont(f)

    def update_font(self, sign):
        self.setMinSize(14)
        f = self.font()
        cr = self.contentsRect()

        # --- iterate to find the font size that fits the contentsRect ---

        dw = sign
        dh = sign

        fs = max(f.pixelSize(), 1)
        while True:

            f.setPixelSize(fs)
            br = QtGui.QFontMetrics(f).boundingRect(self.text())

            if dw >= 0 and dh >= 0:  # label is expanding

                if br.height() <= cr.height()*0.8 and br.width() <= cr.width()*0.8:
                    fs += 1
                else:
                    f.setPixelSize(max(fs - 1, 1))  # backtrack
                    break

            else:  # label is shrinking

                if br.height() > cr.height()*0.8 or br.width() > cr.width()*0.8:
                    fs -= 1
                else:
                    break

            if fs < 1: break

        # --- update font size ---

        self.setFont(f)

class VerticalSeparator(QtWidgets.QWidget):

    def __init__(self):
        super(VerticalSeparator, self).__init__()

        self.initUI()

    def initUI(self):
        self.setMinimumSize(1, 1)
        self.setMaximumWidth(1)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawLine(qp)
        qp.end()

    def drawLine(self, qp):
        # calculate size of histogram from available space
        size = self.size()
        w = size.width()
        h = size.height()

        pen = QtGui.QPen(QtGui.QColor(100, 100, 100), 1)
        qp.setPen(pen)
        qp.drawLine(w / 2, 0, w / 2, h)


class HorizontalSeparator(QtWidgets.QWidget):

    def __init__(self):
        super(HorizontalSeparator, self).__init__()

        self.initUI()

    def initUI(self):
        self.setMinimumSize(1, 1)
        self.setMaximumHeight(1)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawLine(qp)
        qp.end()

    def drawLine(self, qp):
        # calculate size of histogram from available space
        size = self.size()
        w = size.width()
        h = size.height()

        pen = QtGui.QPen(QtGui.QColor(100, 100, 100), 1)
        qp.setPen(pen)
        qp.drawLine(0, h / 2, w, h / 2)