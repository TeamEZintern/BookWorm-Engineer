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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QWidget)

class Ui_ThreadItem(object):
    def setupUi(self, threadItemFrame):
        if not threadItemFrame.objectName():
            threadItemFrame.setObjectName(u"threadItemFrame")
        threadItemFrame.resize(280, 28)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(threadItemFrame.sizePolicy().hasHeightForWidth())
        threadItemFrame.setSizePolicy(sizePolicy)
        threadItemFrame.setMinimumSize(QSize(0, 28))
        threadItemFrame.setMaximumSize(QSize(16777215, 28))
        threadItemFrame.setFrameShape(QFrame.StyledPanel)
        threadItemFrame.setFrameShadow(QFrame.Plain)
        self.itemLayout = QHBoxLayout(threadItemFrame)
        self.itemLayout.setSpacing(0)
        self.itemLayout.setObjectName(u"itemLayout")
        self.itemLayout.setContentsMargins(10, 0, 10, 0)
        self.nameLabel = QLabel(threadItemFrame)
        self.nameLabel.setObjectName(u"nameLabel")
        self.nameLabel.setAlignment(Qt.AlignLeading|Qt.AlignVCenter)

        self.itemLayout.addWidget(self.nameLabel)


        self.retranslateUi(threadItemFrame)

        QMetaObject.connectSlotsByName(threadItemFrame)
    # setupUi

    def retranslateUi(self, threadItemFrame):
        self.nameLabel.setText(QCoreApplication.translate("ThreadItem", u"Thread name", None))
        pass
    # retranslateUi

