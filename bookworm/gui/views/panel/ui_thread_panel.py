# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'thread_panel.ui'
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

class Ui_ThreadPanel(object):
    def setupUi(self, ThreadPanel):
        if not ThreadPanel.objectName():
            ThreadPanel.setObjectName(u"ThreadPanel")
        ThreadPanel.resize(300, 600)
        self.panelLayout = QVBoxLayout(ThreadPanel)
        self.panelLayout.setSpacing(0)
        self.panelLayout.setObjectName(u"panelLayout")
        self.panelLayout.setContentsMargins(0, 0, 0, 0)
        self.themeLayout = QHBoxLayout()
        self.themeLayout.setObjectName(u"themeLayout")
        self.themeLayout.setContentsMargins(10, 10, 10, 4)
        self.themeButton = QPushButton(ThreadPanel)
        self.themeButton.setObjectName(u"themeButton")

        self.themeLayout.addWidget(self.themeButton)


        self.panelLayout.addLayout(self.themeLayout)

        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(6)
        self.headerLayout.setObjectName(u"headerLayout")
        self.headerLayout.setContentsMargins(10, 4, 10, 8)
        self.searchInput = QLineEdit(ThreadPanel)
        self.searchInput.setObjectName(u"searchInput")
        self.searchInput.setMinimumSize(QSize(0, 36))

        self.headerLayout.addWidget(self.searchInput)

        self.sortButton = QPushButton(ThreadPanel)
        self.sortButton.setObjectName(u"sortButton")
        self.sortButton.setMinimumSize(QSize(36, 36))
        self.sortButton.setMaximumSize(QSize(36, 36))

        self.headerLayout.addWidget(self.sortButton)

        self.newThreadButton = QPushButton(ThreadPanel)
        self.newThreadButton.setObjectName(u"newThreadButton")
        self.newThreadButton.setMinimumSize(QSize(36, 36))
        self.newThreadButton.setMaximumSize(QSize(36, 36))

        self.headerLayout.addWidget(self.newThreadButton)


        self.panelLayout.addLayout(self.headerLayout)

        self.threadList = QListWidget(ThreadPanel)
        self.threadList.setObjectName(u"threadList")
        self.threadList.setSpacing(4)

        self.panelLayout.addWidget(self.threadList)


        self.retranslateUi(ThreadPanel)

        QMetaObject.connectSlotsByName(ThreadPanel)
    # setupUi

    def retranslateUi(self, ThreadPanel):
        self.themeButton.setText(QCoreApplication.translate("ThreadPanel", u"Toggle Theme", None))
        self.searchInput.setPlaceholderText(QCoreApplication.translate("ThreadPanel", u"Search threads...", None))
        self.sortButton.setText(QCoreApplication.translate("ThreadPanel", u"\u2630", None))
#if QT_CONFIG(tooltip)
        self.sortButton.setToolTip(QCoreApplication.translate("ThreadPanel", u"Sort threads", None))
#endif // QT_CONFIG(tooltip)
        self.newThreadButton.setText(QCoreApplication.translate("ThreadPanel", u"+", None))
#if QT_CONFIG(tooltip)
        self.newThreadButton.setToolTip(QCoreApplication.translate("ThreadPanel", u"New Thread", None))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

