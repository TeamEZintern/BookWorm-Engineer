# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'thread_item.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QSizePolicy,
    QWidget)

class Ui_ThreadItem(object):
    def setupUi(self, ThreadItem):
        if not ThreadItem.objectName():
            ThreadItem.setObjectName(u"ThreadItem")
        ThreadItem.resize(280, 32)
        ThreadItem.setMinimumSize(QSize(0, 32))
        ThreadItem.setMaximumSize(QSize(16777215, 32))
        self.itemLayout = QHBoxLayout(ThreadItem)
        self.itemLayout.setSpacing(0)
        self.itemLayout.setObjectName(u"itemLayout")
        self.itemLayout.setContentsMargins(14, 0, 10, 0)
        self.nameLabel = QLabel(ThreadItem)
        self.nameLabel.setObjectName(u"nameLabel")
        self.nameLabel.setAlignment(Qt.AlignLeading|Qt.AlignVCenter)

        self.itemLayout.addWidget(self.nameLabel)


        self.retranslateUi(ThreadItem)

        QMetaObject.connectSlotsByName(ThreadItem)
    # setupUi

    def retranslateUi(self, ThreadItem):
        self.nameLabel.setText("")
        pass
    # retranslateUi

