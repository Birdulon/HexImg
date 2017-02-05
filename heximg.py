'''
No license for now
'''

import sys
import os
import struct

pyqt_version = 0
skip_pyqt5 = True  # "PYQT4" in os.environ

if not skip_pyqt5:
    try:
        from PyQt5 import QtGui, QtCore
        from PyQt5.QtGui import QIcon, QPalette, QColor
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QFormLayout,
            QGridLayout, QHBoxLayout, QVBoxLayout,
            QAbstractItemView, QHeaderView, QListWidget,
            QListWidgetItem, QTabWidget, QTableWidget,
            QTableWidgetItem, QFrame, QScrollArea,
            QStackedWidget, QWidget, QCheckBox, QComboBox,
            QDoubleSpinBox, QGroupBox, QLineEdit,
            QPushButton, QRadioButton, QSpinBox,
            QStyleOptionButton, QToolButton, QProgressBar,
            QDialog, QColorDialog, QDialogButtonBox,
            QFileDialog, QInputDialog, QMessageBox,
            QAction, QActionGroup, QLabel, QMenu, QStyle,
            QSystemTrayIcon, QStyleOptionProgressBar
        )
        pyqt_version = 5
    except ImportError:
        print("Couldn't import Qt5 dependencies. "
              "Make sure you installed the PyQt5 package.")
if pyqt_version is 0:
    try:
        import sip
        sip.setapi('QVariant', 2)
        from PyQt4 import QtGui, QtCore
        from PyQt4.QtGui import (
            QApplication, QMainWindow, QFormLayout,
            QGridLayout, QHBoxLayout, QVBoxLayout,
            QAbstractItemView, QHeaderView, QListWidget,
            QListWidgetItem, QTabWidget, QTableWidget,
            QTableWidgetItem, QFrame, QScrollArea,
            QStackedWidget, QWidget, QCheckBox,
            QComboBox, QDoubleSpinBox, QGroupBox,
            QLineEdit, QPushButton, QRadioButton,
            QSpinBox, QStyleOptionButton, QToolButton,
            QProgressBar, QDialog, QColorDialog,
            QDialogButtonBox, QFileDialog, QInputDialog,
            QMessageBox, QAction, QActionGroup,
            QLabel, QMenu, QStyle,
            QSystemTrayIcon, QIcon, QPalette, QColor
        )
        from PyQt4.QtGui import QStyleOptionProgressBarV2 as QStyleOptionProgressBar
        pyqt_version = 4
    except ImportError:
        print("Couldn't import Qt dependencies. "
              "Make sure you installed the PyQt4 package.")
        sys.exit(-1)


class HexImg(QMainWindow):
    """
    Main GUI class
    """

    ROM = bytes(0)

    def __init__(self):
        QMainWindow.__init__(self, None)

        self.col_palette = [QColor(  0,  0,  0),
                            QColor(255,255,255),
                            QColor(255,  0,  0),
                            QColor(192,  0,  0),
                            QColor(128,  0,  0),
                            QColor( 64,  0,  0),
                            QColor(  0,255,  0),
                            QColor(  0,192,  0),
                            QColor(  0,128,  0),
                            QColor(  0, 64,  0),
                            QColor(  0,  0,255),
                            QColor(  0,  0,192),
                            QColor(  0,  0,128),
                            QColor(  0,  0, 64),
                            QColor(255,255,  0),
                            QColor(  0,255,255)]

        self.setWindowTitle('HexImg')

        self.main_area = QWidget()  # QLabel()
        self.main_area.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.main_area.setContentsMargins(0, 0, 0, 0)
        main_area_layout = QHBoxLayout()
        main_area_layout.setSpacing(16)
        main_area_layout.setContentsMargins(0, 0, 0, 0)
        self.main_area.setLayout(main_area_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.main_area)
        self.scroll_area.setMinimumSize(640, 640)

        sidebar = QVBoxLayout()
        sideform = QFormLayout()
        sideform.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        colorbox = QGridLayout()

        self.address_offset = QSpinBox()
        self.address_offset.setRange(0, 1023)
        self.address_offset.setSingleStep(1)
        self.address_offset.valueChanged.connect(self.update_image)

        self.pixel_size = QComboBox()
        for i in [1, 2, 4]:
            self.pixel_size.addItem(str(i))
        self.pixel_size.setCurrentIndex(2)
        self.pixel_size.currentIndexChanged.connect(self.update_image)

        self.scale = QSpinBox()
        self.scale.setRange(1, 32)
        self.scale.setSingleStep(1)
        self.scale.valueChanged.connect(self.update_image)

        self.width = QSpinBox()
        self.width.setRange(8, 512)
        self.width.setSingleStep(1)
        self.width.valueChanged.connect(self.update_image)

        sideform.addRow('Offset', self.address_offset)
        sideform.addRow('Width', self.width)
        sideform.addRow('Color bits', self.pixel_size)
        sideform.addRow('Scale', self.scale)
        sidebar.addLayout(sideform)

        self.colors = []
        for i in range(len(self.col_palette)):
            self.colors.append(QPushButton())
            self.colors[-1].setStyleSheet('background-color: ' + self.col_palette[i].name())
            self.colors[-1].setFocusPolicy(QtCore.Qt.NoFocus)
            self.colors[-1].clicked.connect(self.s_color_picker(i))
            colorbox.addWidget(self.colors[-1], i//2, i % 2, 1, 1)
        sidebar.addLayout(colorbox)

        btn_load = QPushButton('Load ROM')
        btn_load.clicked.connect(self.load_file)
        sidebar.addWidget(btn_load)

        layout = QHBoxLayout()
        layout.addWidget(self.scroll_area)
        layout.addLayout(sidebar)

        self.main_widget = QWidget(self)
        self.main_widget.setLayout(layout)
        self.setCentralWidget(self.main_widget)
        self.show()

    def load_file(self):
        caption = 'Choose ROM file'
        if pyqt_version is 5:
            filename = QFileDialog.getOpenFileName(caption=caption)[0]
        else:
            filename = QFileDialog.getOpenFileName(caption=caption)
        self.setWindowTitle('HexImg: %s' % filename)
        with open(filename, 'rb') as file1:
            self.ROM = file1.read()
        self.update_image()

    def update_image(self):
        if not self.ROM or len(self.ROM) < 1:
            return

        px_per_byte = 8//int(self.pixel_size.currentText())
        bx = 8//px_per_byte   # Bits per px
        bxm = int(2**(bx)-1)  # Bitmask form
        offset = int(self.address_offset.value())

        scale = int(self.scale.value())
        length = len(self.ROM) - offset
        px_length = px_per_byte * length
        width = int(self.width.value())
        # Maximum height for QPixmap is 32,767
        height_1 = -(-px_length // width)  # Reverse floor division for ceil
        columns = -(-(height_1 * scale) // 32767)
        height = -(-height_1 // columns)
        col_length = -(-length // columns)

        layout = self.main_area.layout()

        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            layout.removeWidget(widget)
            widget.setParent(None)

        for col in range(columns):
            if col == columns - 1:
                byterange = range(offset + col*col_length, len(self.ROM))
            else:
                byterange = range(offset + col*col_length, offset + (col+1)*col_length)

            pixmap = QtGui.QPixmap.fromImage(self._create_image_indexed(width, height, byterange, px_per_byte, bx, bxm))
            pixmap_scaled = pixmap.scaled(pixmap.size() * scale)
            label = QLabel()
            label.setPixmap(pixmap_scaled)
            layout.addWidget(label)
        self.main_area.resize((pixmap_scaled.width()+layout.spacing())*columns, pixmap_scaled.height())

    def _create_image_RGB(self, width, height, byterange, px_per_byte, bx, bxm):
        img = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
        ucharptr = img.bits()
        ucharptr.setsize(img.byteCount())

        ptr = 0
        for i in byterange:
            # Need to read part of each byte depending on palette size
            byte = self.ROM[i]
            for j in range(px_per_byte):
                offset = 8 - (j+1)*bx
                bits = byte >> offset & bxm
                color = self.col_palette[bits]
                ucharptr[ptr:ptr+4] = struct.pack('I', color.rgb())
                ptr += 4
        return img

    def _create_image_indexed(self, width, height, byterange, px_per_byte, bx, bxm):
        img = QtGui.QImage(width, height, QtGui.QImage.Format_Indexed8)
        img.setColorTable([c.rgba() for c in self.col_palette])
        ucharptr = img.bits()
        ucharptr.setsize(img.byteCount())

        ptr = 0
        for i in byterange:
            # Need to read part of each byte depending on palette size
            byte = self.ROM[i]
            for j in range(px_per_byte):
                offset = 8 - (j+1)*bx
                bits = byte >> offset & bxm
                ucharptr[ptr] = struct.pack('B', bits)
                ptr += 1
        return img

    def s_color_picker(self, key):
        return lambda: self.color_picker(key)

    def color_picker(self, key):
        current = self.col_palette[key]
        result = QColorDialog.getColor(current)
        if result.isValid() and result is not current:
            self.col_palette[key] = result
            self.colors[key].setStyleSheet('background-color: ' + result.name())
            self.update_image()


def main():
    app = QApplication(sys.argv)

    mainwindow = HexImg()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
