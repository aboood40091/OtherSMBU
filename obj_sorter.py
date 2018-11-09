#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Object Sorter
# Copyright © 2018 AboodXD

import json, os, re, sys

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QPalette, QPixmap
from PyQt5 import QtWidgets


class Object(QtWidgets.QListWidgetItem):
    def __init__(self, file, path, text):
        with open(os.path.join(path, file), "r") as inf:
            self.jsonData = json.load(inf)

        with open(os.path.join(path, self.jsonData["colls"]), "rb") as inf:
            self.collData = inf.read()

        with open(os.path.join(path, self.jsonData["meta"]), "rb") as inf:
            self.indexfile = inf.read()

        with open(os.path.join(path, self.jsonData["objlyt"]), "rb") as inf:
            self.deffile = inf.read()

        self.img = QPixmap(os.path.join(path, self.jsonData["img"]))
        self.nml = QPixmap(os.path.join(path, self.jsonData["nml"]))

        super().__init__(QIcon(self.img), text)

    def save(self, path, i):
        self.jsonData["colls"] = "object%d.colls" % i
        self.jsonData["meta"] = "object%d.meta" % i
        self.jsonData["objlyt"] = "object%d.objlyt" % i
        self.jsonData["img"] = "object%d.png" % i
        self.jsonData["nml"] = "object%d_nml.png" % i

        self.img.save(os.path.join(path, self.jsonData["img"]))
        self.nml.save(os.path.join(path, self.jsonData["nml"]))

        with open(os.path.join(path, self.jsonData["colls"]), "wb") as out:
            out.write(self.collData)

        with open(os.path.join(path, self.jsonData["meta"]), "wb") as out:
            out.write(self.indexfile)

        with open(os.path.join(path, self.jsonData["objlyt"]), "wb") as out:
            out.write(self.deffile)

        with open(os.path.join(path, "object%d.json" % i), "w") as out:
            json.dump(self.jsonData, out)


class ObjectPickerWidget(QtWidgets.QListWidget):
    def __init__(self):
        super().__init__()

        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setFlow(QtWidgets.QListView.TopToBottom)
        self.setIconSize(QSize(120,120))
        self.setGridSize(QSize(130,130))
        self.setMovement(QtWidgets.QListView.Static)
        self.setBackgroundRole(QPalette.BrightText)
        self.setWrapping(False)
        self.setMinimumWidth(260)

    def moveUp(self):
        currentRow = self.currentRow()
        if currentRow:
            currentItem = self.takeItem(currentRow)
            self.insertItem(currentRow - 1, currentItem)
            self.setCurrentRow(currentRow - 1)

    def moveDown(self):
        currentRow = self.currentRow()
        if currentRow != self.count() - 1:
            currentItem = self.takeItem(currentRow)
            self.insertItem(currentRow + 1, currentItem)
            self.setCurrentRow(currentRow + 1)

    def addObjects(self, folder):
        files = os.listdir(folder)
        files.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)])

        for file in files:
            if file[-5:] == ".json":
                self.addItem(Object(file, folder, os.path.splitext(file)[0]))

    def saveFolderAs(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Folder to save the objects to")
        if not folder:
            return

        for i in range(self.count()):
            self.item(i).save(folder, i)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Object Sorter - By AboodXD")
        self.clearList()

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&Folder')

        openFolder = QtWidgets.QAction("&Open Folder", self)
        openFolder.triggered.connect(self.openFolder)
        fileMenu.addAction(openFolder)

        fileMenu.addSeparator()

        saveFolderAs = QtWidgets.QAction("&Save Folder As", self)
        saveFolderAs.triggered.connect(self.saveFolderAs)
        fileMenu.addAction(saveFolderAs)

    def openFolder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Open Folder containing objects")
        if not folder:
            return

        self.clearList()
        self.objPicker.addObjects(folder)

    def saveFolderAs(self):
        self.objPicker.saveFolderAs()

    def clearList(self):
        widget = QtWidgets.QWidget()
        self.objPicker = ObjectPickerWidget()
        self.moveUpButton = QtWidgets.QPushButton()
        self.moveUpButton.setText("Move\nUp")
        self.moveUpButton.clicked.connect(self.objPicker.moveUp)

        self.moveDownButton = QtWidgets.QPushButton()
        self.moveDownButton.setText("Move\nDown")
        self.moveDownButton.clicked.connect(self.objPicker.moveDown)

        buttonLayout = QtWidgets.QVBoxLayout()
        buttonLayout.addWidget(self.moveUpButton)
        buttonLayout.addWidget(self.moveDownButton)

        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(self.objPicker)
        layout.addLayout(buttonLayout)

        widget.setLayout(layout)
        self.setCentralWidget(widget)


if __name__ == '__main__':
    app = QtWidgets.QApplication([sys.argv[0]])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    app.deleteLater()
