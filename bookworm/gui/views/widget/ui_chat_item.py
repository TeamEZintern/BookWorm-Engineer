# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'chat_item.ui'
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

class Ui_ChatItem(object):
    def setupUi(self, chatItemFrame):
        if not chatItemFrame.objectName():
            chatItemFrame.setObjectName(u"chatItemFrame")
        chatItemFrame.resize(280, 28)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(chatItemFrame.sizePolicy().hasHeightForWidth())
        chatItemFrame.setSizePolicy(sizePolicy)
        chatItemFrame.setMinimumSize(QSize(0, 28))
        chatItemFrame.setMaximumSize(QSize(16777215, 28))
        chatItemFrame.setFrameShape(QFrame.StyledPanel)
        chatItemFrame.setFrameShadow(QFrame.Plain)
        self.itemLayout = QHBoxLayout(chatItemFrame)
        self.itemLayout.setSpacing(0)
        self.itemLayout.setObjectName(u"itemLayout")
        self.itemLayout.setContentsMargins(10, 0, 10, 0)
        self.nameLabel = QLabel(chatItemFrame)
        self.nameLabel.setObjectName(u"nameLabel")
        self.nameLabel.setAlignment(Qt.AlignLeading|Qt.AlignVCenter)

        self.itemLayout.addWidget(self.nameLabel)


        self.retranslateUi(chatItemFrame)

        QMetaObject.connectSlotsByName(chatItemFrame)
    # setupUi

    def retranslateUi(self, chatItemFrame):
        self.nameLabel.setText(QCoreApplication.translate("ChatItem", u"Chat name", None))
        pass
    # retranslateUi

