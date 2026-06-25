# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'side_panel.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_SidePanel(object):
    def setupUi(self, SidePanel):
        if not SidePanel.objectName():
            SidePanel.setObjectName(u"SidePanel")
        SidePanel.resize(300, 600)
        self.panelLayout = QVBoxLayout(SidePanel)
        self.panelLayout.setSpacing(0)
        self.panelLayout.setObjectName(u"panelLayout")
        self.panelLayout.setContentsMargins(0, 0, 0, 0)
        self.themeLayout = QHBoxLayout()
        self.themeLayout.setObjectName(u"themeLayout")
        self.themeLayout.setContentsMargins(10, 10, 10, 4)
        self.themeButton = QPushButton(SidePanel)
        self.themeButton.setObjectName(u"themeButton")

        self.themeLayout.addWidget(self.themeButton)


        self.panelLayout.addLayout(self.themeLayout)

        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(6)
        self.headerLayout.setObjectName(u"headerLayout")
        self.headerLayout.setContentsMargins(10, 4, 10, 8)
        self.searchInput = QLineEdit(SidePanel)
        self.searchInput.setObjectName(u"searchInput")
        self.searchInput.setMinimumSize(QSize(0, 36))

        self.headerLayout.addWidget(self.searchInput)

        self.sortButton = QPushButton(SidePanel)
        self.sortButton.setObjectName(u"sortButton")
        self.sortButton.setMinimumSize(QSize(36, 36))
        self.sortButton.setMaximumSize(QSize(36, 36))

        self.headerLayout.addWidget(self.sortButton)

        self.newChatButton = QPushButton(SidePanel)
        self.newChatButton.setObjectName(u"newChatButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.newChatButton.sizePolicy().hasHeightForWidth())
        self.newChatButton.setSizePolicy(sizePolicy)
        self.newChatButton.setMinimumSize(QSize(36, 36))
        self.newChatButton.setMaximumSize(QSize(36, 36))
        font = QFont()
        font.setFamilies([u"Consolas"])
        font.setPointSize(20)
        self.newChatButton.setFont(font)

        self.headerLayout.addWidget(self.newChatButton)


        self.panelLayout.addLayout(self.headerLayout)

        self.chatList = QListWidget(SidePanel)
        self.chatList.setObjectName(u"chatList")
        self.chatList.setSpacing(2)

        self.panelLayout.addWidget(self.chatList)


        self.retranslateUi(SidePanel)

        QMetaObject.connectSlotsByName(SidePanel)
    # setupUi

    def retranslateUi(self, SidePanel):
        self.themeButton.setText(QCoreApplication.translate("SidePanel", u"Toggle Theme", None))
        self.searchInput.setPlaceholderText(QCoreApplication.translate("SidePanel", u"Search chats...", None))
#if QT_CONFIG(tooltip)
        self.sortButton.setToolTip(QCoreApplication.translate("SidePanel", u"Sort chats", None))
#endif // QT_CONFIG(tooltip)
        self.sortButton.setText(QCoreApplication.translate("SidePanel", u"\u2630", None))
#if QT_CONFIG(tooltip)
        self.newChatButton.setToolTip(QCoreApplication.translate("SidePanel", u"New Chat", None))
#endif // QT_CONFIG(tooltip)
        self.newChatButton.setText(QCoreApplication.translate("SidePanel", u"+", None))
        pass
    # retranslateUi

