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
    QPushButton, QSizePolicy, QWidget)

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
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.nameLabel.sizePolicy().hasHeightForWidth())
        self.nameLabel.setSizePolicy(sizePolicy1)
        self.nameLabel.setAlignment(Qt.AlignLeading|Qt.AlignVCenter)

        self.itemLayout.addWidget(self.nameLabel)

        self.overflowMenuButton = QPushButton(chatItemFrame)
        self.overflowMenuButton.setObjectName(u"overflowMenuButton")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.overflowMenuButton.sizePolicy().hasHeightForWidth())
        self.overflowMenuButton.setSizePolicy(sizePolicy2)
        self.overflowMenuButton.setMinimumSize(QSize(24, 24))
        self.overflowMenuButton.setMaximumSize(QSize(24, 24))
        self.overflowMenuButton.setFocusPolicy(Qt.NoFocus)
        self.overflowMenuButton.setFlat(True)

        self.itemLayout.addWidget(self.overflowMenuButton)


        self.retranslateUi(chatItemFrame)

        QMetaObject.connectSlotsByName(chatItemFrame)
    # setupUi

    def retranslateUi(self, chatItemFrame):
        self.nameLabel.setText(QCoreApplication.translate("ChatItem", u"Chat name", None))
        self.overflowMenuButton.setText(QCoreApplication.translate("ChatItem", u"\u22ef", None))
#if QT_CONFIG(tooltip)
        self.overflowMenuButton.setToolTip(QCoreApplication.translate("ChatItem", u"More options", None))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

