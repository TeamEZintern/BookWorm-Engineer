# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'thread_panel.ui'
##
## Created by: Qt User Interface Compiler version 6.x
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QMetaObject, QCoreApplication
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLineEdit, QListWidget, QPushButton,
    QVBoxLayout, QWidget,
)


class Ui_ThreadPanel(object):
    def setupUi(self, ThreadPanel):
        if not ThreadPanel.objectName():
            ThreadPanel.setObjectName(u"ThreadPanel")
        ThreadPanel.resize(300, 600)
        self.panelLayout = QVBoxLayout(ThreadPanel)
        self.panelLayout.setSpacing(0)
        self.panelLayout.setObjectName(u"panelLayout")
        self.panelLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setObjectName(u"headerLayout")
        self.headerLayout.setContentsMargins(10, 10, 10, 5)
        self.searchInput = QLineEdit(ThreadPanel)
        self.searchInput.setObjectName(u"searchInput")

        self.headerLayout.addWidget(self.searchInput)

        self.sortCombo = QComboBox(ThreadPanel)
        self.sortCombo.addItem("")
        self.sortCombo.addItem("")
        self.sortCombo.addItem("")
        self.sortCombo.setObjectName(u"sortCombo")

        self.headerLayout.addWidget(self.sortCombo)

        self.newThreadButton = QPushButton(ThreadPanel)
        self.newThreadButton.setObjectName(u"newThreadButton")

        self.headerLayout.addWidget(self.newThreadButton)


        self.panelLayout.addLayout(self.headerLayout)

        self.threadList = QListWidget(ThreadPanel)
        self.threadList.setObjectName(u"threadList")

        self.panelLayout.addWidget(self.threadList)


        self.retranslateUi(ThreadPanel)

        QMetaObject.connectSlotsByName(ThreadPanel)
    # setupUi

    def retranslateUi(self, ThreadPanel):
        self.searchInput.setPlaceholderText(QCoreApplication.translate("ThreadPanel", u"Search threads...", None))
        self.sortCombo.setItemText(0, QCoreApplication.translate("ThreadPanel", u"Date Modified", None))
        self.sortCombo.setItemText(1, QCoreApplication.translate("ThreadPanel", u"Date Created", None))
        self.sortCombo.setItemText(2, QCoreApplication.translate("ThreadPanel", u"Name", None))
        self.newThreadButton.setText(QCoreApplication.translate("ThreadPanel", u"+ New Thread", None))
    # retranslateUi
