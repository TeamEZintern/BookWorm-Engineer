# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'message_bubble.ui'
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
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_MessageBubble(object):
    def setupUi(self, MessageBubble):
        if not MessageBubble.objectName():
            MessageBubble.setObjectName(u"MessageBubble")
        MessageBubble.resize(400, 80)
        MessageBubble.setFrameShape(QFrame.StyledPanel)
        self.bubbleLayout = QVBoxLayout(MessageBubble)
        self.bubbleLayout.setSpacing(5)
        self.bubbleLayout.setObjectName(u"bubbleLayout")
        self.bubbleLayout.setContentsMargins(10, 10, 10, 10)
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(10)
        self.headerLayout.setObjectName(u"headerLayout")
        self.roleLabel = QLabel(MessageBubble)
        self.roleLabel.setObjectName(u"roleLabel")

        self.headerLayout.addWidget(self.roleLabel)

        self.timestampLabel = QLabel(MessageBubble)
        self.timestampLabel.setObjectName(u"timestampLabel")

        self.headerLayout.addWidget(self.timestampLabel)


        self.bubbleLayout.addLayout(self.headerLayout)

        self.contentContainer = QWidget(MessageBubble)
        self.contentContainer.setObjectName(u"contentContainer")
        self.contentLayout = QVBoxLayout(self.contentContainer)
        self.contentLayout.setSpacing(0)
        self.contentLayout.setObjectName(u"contentLayout")
        self.contentLayout.setContentsMargins(0, 0, 0, 0)

        self.bubbleLayout.addWidget(self.contentContainer)


        self.retranslateUi(MessageBubble)

        QMetaObject.connectSlotsByName(MessageBubble)
    # setupUi

    def retranslateUi(self, MessageBubble):
        self.roleLabel.setText("")
        self.timestampLabel.setText("")
        pass
    # retranslateUi

