# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'chat_panel.ui'
##
## Created by: Qt User Interface Compiler version 6.x
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QMetaObject, QCoreApplication, Qt, QSize, QRect
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QTextEdit, QVBoxLayout, QWidget,
)


class Ui_ChatPanel(object):
    def setupUi(self, ChatPanel):
        if not ChatPanel.objectName():
            ChatPanel.setObjectName(u"ChatPanel")
        ChatPanel.resize(800, 600)
        self.panelLayout = QVBoxLayout(ChatPanel)
        self.panelLayout.setSpacing(0)
        self.panelLayout.setObjectName(u"panelLayout")
        self.panelLayout.setContentsMargins(0, 0, 0, 0)
        self.statusBar = QLabel(ChatPanel)
        self.statusBar.setObjectName(u"statusBar")

        self.panelLayout.addWidget(self.statusBar)

        self.scrollArea = QScrollArea(ChatPanel)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(True)
        self.messageContainer = QWidget()
        self.messageContainer.setObjectName(u"messageContainer")
        self.messageContainer.setGeometry(QRect(0, 0, 798, 500))
        self.messageLayout = QVBoxLayout(self.messageContainer)
        self.messageLayout.setSpacing(10)
        self.messageLayout.setObjectName(u"messageLayout")
        self.messageLayout.setContentsMargins(10, 10, 10, 10)
        self.scrollArea.setWidget(self.messageContainer)

        self.panelLayout.addWidget(self.scrollArea)

        self.inputFrame = QFrame(ChatPanel)
        self.inputFrame.setObjectName(u"inputFrame")
        self.inputFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.inputFrame.setFrameShadow(QFrame.Shadow.Plain)
        self.inputLayout = QHBoxLayout(self.inputFrame)
        self.inputLayout.setObjectName(u"inputLayout")
        self.inputLayout.setContentsMargins(10, 10, 10, 10)
        self.messageInput = QTextEdit(self.inputFrame)
        self.messageInput.setObjectName(u"messageInput")
        self.messageInput.setMaximumSize(QSize(16777215, 100))

        self.inputLayout.addWidget(self.messageInput)

        self.sendButton = QPushButton(self.inputFrame)
        self.sendButton.setObjectName(u"sendButton")

        self.inputLayout.addWidget(self.sendButton)


        self.panelLayout.addWidget(self.inputFrame)


        self.retranslateUi(ChatPanel)

        QMetaObject.connectSlotsByName(ChatPanel)
    # setupUi

    def retranslateUi(self, ChatPanel):
        self.statusBar.setText(QCoreApplication.translate("ChatPanel", u"Ready", None))
        self.messageInput.setPlaceholderText(QCoreApplication.translate("ChatPanel", u"Type a message...", None))
        self.sendButton.setText(QCoreApplication.translate("ChatPanel", u"Send", None))
    # retranslateUi
