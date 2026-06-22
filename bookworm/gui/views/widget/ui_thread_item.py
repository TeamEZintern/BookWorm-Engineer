# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'thread_item.ui'
##
## Created by: Qt User Interface Compiler version 6.x
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QMetaObject
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Ui_ThreadItem(object):
    def setupUi(self, ThreadItem):
        if not ThreadItem.objectName():
            ThreadItem.setObjectName(u"ThreadItem")
        ThreadItem.resize(280, 28)
        self.itemLayout = QVBoxLayout(ThreadItem)
        self.itemLayout.setSpacing(0)
        self.itemLayout.setObjectName(u"itemLayout")
        self.itemLayout.setContentsMargins(8, 4, 8, 4)
        self.nameLabel = QLabel(ThreadItem)
        self.nameLabel.setObjectName(u"nameLabel")

        self.itemLayout.addWidget(self.nameLabel)


        self.retranslateUi(ThreadItem)

        QMetaObject.connectSlotsByName(ThreadItem)
    # setupUi

    def retranslateUi(self, ThreadItem):
        self.nameLabel.setText("")
    # retranslateUi
