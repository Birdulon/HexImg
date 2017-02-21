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

from array import array


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

        self.image_area = QWidget()  # QLabel()
        self.image_area.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.image_area.setContentsMargins(0, 0, 0, 0)
        main_area_layout = QHBoxLayout()
        main_area_layout.setSpacing(16)
        main_area_layout.setContentsMargins(0, 0, 0, 0)
        self.image_area.setLayout(main_area_layout)

        self.image_scroller = QScrollArea()
        self.image_scroller.setWidget(self.image_area)
        self.image_scroller.setMinimumSize(640, 640)

        self.palette_area = QLabel()
        self.palette_area.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.palette_area.setContentsMargins(0, 0, 0, 0)
        pal_area_layout = QHBoxLayout()
        pal_area_layout.setSpacing(16)
        pal_area_layout.setContentsMargins(0, 0, 0, 0)
        self.palette_area.setLayout(pal_area_layout)
        self.palette_area.mousePressEvent = self.select_palette

        self.palette_scroller = QScrollArea()
        self.palette_scroller.setWidget(self.palette_area)

        self.address_offset = SpinBox(0, 1000000000, step=64, func=self.update_image)
        self.address_fine_offset = SpinBox(0, 1023, func=self.update_image)
        self.image_length = SpinBox(16, 65536, init=1024, step=16, func=self.update_image)
        self.scale = SpinBox(1, 32, init=8, step=1, func=self.update_image_lite)
        self.width_s = SpinBox(8, 512, init=8, func=self.update_image)
        self.height_s = SpinBox(16, 32727, init=1300, func=self.update_image)

        self.pixel_size = QComboBox()
        for i in [1, 2, 4]:
            self.pixel_size.addItem(str(i))
        self.pixel_size.setCurrentIndex(2)
        self.pixel_size.currentIndexChanged.connect(self.update_image)

        self.palette_offset = SpinBox(0, 1000000000, init=1352640, step=32, func=self.update_palette_viewer)
        self.palette_fine_offset = SpinBox(0, 31, func=self.update_palette_viewer)
        self.palette_length = SpinBox(0, 16384, init=4096, step=32, func=self.update_palette_viewer)
        self.palette_scale = SpinBox(2, 32, init=16, func=self.update_palette_viewer)
        self.palette_scroller.setMinimumWidth(16*self.palette_scale.value() + 20)
        self.palette_scroller.setMaximumWidth(16*self.palette_scale.value() + 20)

        self.endian = QCheckBox()
        self.endian.stateChanged.connect(self.update_image)

        sidebar = QVBoxLayout()
        sidebar.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        colorbox = QGridLayout()

        self.image_settings = QGroupBox('Image Viewer')
        image_settings_form = QFormLayout()
        image_settings_form.addRow('Address', self.address_offset)
        image_settings_form.addRow('Offset', self.address_fine_offset)
        image_settings_form.addRow('Length', self.image_length)
        image_settings_form.addRow('Width', self.width_s)
        image_settings_form.addRow('Height', self.height_s)
        image_settings_form.addRow('Color bits', self.pixel_size)
        image_settings_form.addRow('Scale', self.scale)
        image_settings_form.addRow('Flip endian', self.endian)
        self.image_settings.setLayout(image_settings_form)

        self.palette_settings = QGroupBox('Palette Viewer')
        palette_settings_form = QFormLayout()
        palette_settings_form.addRow('Address', self.palette_offset)
        palette_settings_form.addRow('Offset', self.palette_fine_offset)
        palette_settings_form.addRow('Length', self.palette_length)
        palette_settings_form.addRow('Scale', self.palette_scale)
        self.palette_settings.setLayout(palette_settings_form)

        self.colors = []
        for i in range(len(self.col_palette)):
            self.colors.append(QPushButton())
            self.colors[-1].setStyleSheet('background-color: ' + self.col_palette[i].name())
            self.colors[-1].setFocusPolicy(QtCore.Qt.NoFocus)
            self.colors[-1].clicked.connect(self.s_color_picker(i))
            colorbox.addWidget(self.colors[-1], i//2, i % 2, 1, 1)

        btn_load = QPushButton('Load ROM')
        btn_load.clicked.connect(self.load_file)

        sidebar.addWidget(self.image_settings)
        sidebar.addWidget(self.palette_settings)
        sidebar.addLayout(colorbox)
        sidebar.addWidget(btn_load)

        layout = QHBoxLayout()
        layout.addWidget(self.image_scroller)
        layout.addWidget(self.palette_scroller)
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
        self.update_palette_viewer()

    def select_palette(self, event):
        width = 16
        scale = self.palette_scale.value()
        row = event.pos().y() // scale
        for i in range(width):
            color = QColor.fromRgb(self.palette_qimage.pixel(i, row))
            self.update_color(i, color)
        self.update_image_lite()

    def update_palette_viewer(self):
        # Check for BGR555 palettes
        offset = self.palette_offset.value()+self.palette_fine_offset.value()
        if not self.ROM or len(self.ROM) < 1 or len(self.ROM) < offset:
            return
        width = 16
        length = int(self.palette_length.value())
        scale = self.palette_scale.value()
        self.palette_scroller.setMinimumWidth(width*scale + 20)
        self.palette_scroller.setMaximumWidth(width*scale + 20)
        height = 512  # int(self.height_s.value()) // scale
        self.palette_qimage = self._create_pal_image(offset, length)
        pixmap = QtGui.QPixmap.fromImage(self.palette_qimage)
        pixmap_scaled = pixmap.scaled(pixmap.size() * scale)
        self.palette_area.setPixmap(pixmap_scaled)
        self.palette_area.resize(pixmap_scaled.width(), pixmap_scaled.height())

    def _create_pal_image(self, offset, length):
        width = 16
        height = (length // 2) // width
        img = QtGui.QImage(width, height, QtGui.QImage.Format_RGB555)
        img.setColorTable([c.rgba() for c in self.col_palette])
        ucharptr = img.bits()
        ucharptr.setsize(img.byteCount())

        ptr = 0
        for i in range(offset, offset+length, 2):
            # Need to convert BGR555 to RGB555
            short = struct.unpack('<H', self.ROM[i:i+2])[0]
            red = short & 0x1F
            blue = (short >> 10) & 0x1F
            green5 = short & 0x3E0
            bits = (red << 10) | green5 | blue
            ucharptr[ptr:ptr+2] = struct.pack('H', bits)
            ptr += 2
        return img

    def update_image_lite(self):
        if not self.ROM or len(self.ROM) < 1:
            return
        # Only update palette and scaling
        scale = int(self.scale.value())
        layout = self.image_area.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            layout.removeWidget(widget)
            widget.setParent(None)

        for col in range(self.image_columns):
            qimage = self.image_qimages[col]
            qimage.setColorTable([c.rgba() for c in self.col_palette])
            pixmap = QtGui.QPixmap.fromImage(qimage)
            pixmap_scaled = pixmap.scaled(pixmap.size() * scale)
            label = QLabel()
            label.setPixmap(pixmap_scaled)
            layout.addWidget(label)
        self.image_area.resize((pixmap_scaled.width()+layout.spacing())*self.image_columns, pixmap_scaled.height())

    def update_image(self):
        if not self.ROM or len(self.ROM) < 1:
            return

        px_per_byte = 8//int(self.pixel_size.currentText())
        bx = 8//px_per_byte   # Bits per px
        bxm = int(2**(bx)-1)  # Bitmask form
        offset = int(self.address_offset.value()+self.address_fine_offset.value())

        scale = int(self.scale.value())
        length = min(len(self.ROM) - offset, int(self.image_length.value()))
        px_length = px_per_byte * length
        width = int(self.width_s.value())
        width = -(-width // 8)*8  # TODO: Restrict this quantisation to SNES mode
        # Maximum height for QPixmap is 32,767
        height_overall = -(-px_length // width)  # Reverse floor division for ceil
        height_overall_tiles = (height_overall // 8)
        #self.image_columns = -(-(height_overall * scale) // int(self.height_s.value()))
        self.image_columns = -(-(height_overall_tiles * scale) // (self.height_s.value()//8))
        height = (-(-height_overall_tiles // self.image_columns)) * 8
        col_length = height * width // px_per_byte  # -(-length // columns)

        self.image_qimages = []

        layout = self.image_area.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            layout.removeWidget(widget)
            widget.setParent(None)

        for col in range(self.image_columns):
            byterange = range(offset + col*col_length, min(offset + (col+1)*col_length, len(self.ROM)), 32)
            qimage = self._create_image_snes(width, height, byterange, px_per_byte, bx, bxm)
            self.image_qimages.append(qimage)
            pixmap = QtGui.QPixmap.fromImage(qimage)
            pixmap_scaled = pixmap.scaled(pixmap.size() * scale)
            label = QLabel()
            label.setPixmap(pixmap_scaled)
            layout.addWidget(label)
        self.image_area.resize((pixmap_scaled.width()+layout.spacing())*self.image_columns, pixmap_scaled.height())

        self.address_offset.setSingleStep(2*width)

    def _create_image(self, width, height, byterange, px_per_byte, bx, bxm):
        img = QtGui.QImage(width, height, QtGui.QImage.Format_Indexed8)
        img.setColorTable([c.rgba() for c in self.col_palette])
        ucharptr = img.bits()
        ucharptr.setsize(img.byteCount())

        ptr = 0
        if self.endian.isChecked():
            for i in byterange:
                # Need to read part of each byte depending on palette size
                #print(i)
                byte = self.ROM[i]
                for j in range(px_per_byte):
                    offset = j*bx
                    bits = byte >> offset & bxm
                    ucharptr[ptr] = struct.pack('B', bits)
                    ptr += 1
        else:
            for i in byterange:
                # Need to read part of each byte depending on palette size
                #print(i)
                byte = self.ROM[i]
                for j in reversed(range(px_per_byte)):
                    offset = j*bx
                    bits = byte >> offset & bxm
                    ucharptr[ptr] = struct.pack('B', bits)
                    ptr += 1
        return img

    def _create_image_snes(self, width, height, byterange, px_per_byte, bx, bxm):
        # Graphics are stored in 8x8 tiles
        # Colour bits are segregated by "plane"
        # Bytes 0,2,4,6,8,10,12,14 contain plane 0 (LSB of each pixel?)
        # Bytes 1,3,5,7,9,11,13,15 contain plane 1
        # Bytes 16,18,...,30 make up plane 2
        # Bytes 17,19,...,31 make up plane 3
        # Bytes 32,34,...,46 plane 4
        # Bytes 33,35,...,47 plane 5
        # Bytes 48,50,...,62 plane 6
        # Bytes 49,51,...,63 plane 7 (MSB of each pixel?)
        img = QtGui.QImage(width, height, QtGui.QImage.Format_Indexed8)
        img.setColorTable([c.rgba() for c in self.col_palette])
        ucharptr = img.bits()
        ucharptr.setsize(img.byteCount())
        planes = bx

        ptr = 0
        x_tile = 0
        tile = array('B', range(64))
        # i now has a 32 step size
        for i in byterange:
            bytes = self.ROM[i:i+32]
            t_ptr = 0
            for j in range(0, 16, 2):
                for x in reversed(range(8)):
                    tile[t_ptr] = bytes[j] >> x & 1 \
                                  | ((bytes[j+1] >> x & 1) << 1) \
                                  | ((bytes[j+16] >> x & 1) << 2) \
                                  | ((bytes[j+17] >> x & 1) << 3)
                    t_ptr += 1
            if width == 8:
                #print("Size of tile: %i" % len(tile))
                ucharptr[ptr:ptr+64] = tile  # struct.pack('B', tile)
                ptr += 64
            else:
                for y in range(8):
                    ucharptr[ptr+(y*width):ptr+(y*width)+8] = tile[y*8:(y+1)*8]
                ptr += 8  # move along one tile's width
                x_tile += 1
                if x_tile >= width//8:
                    ptr += width*7  # move to the start of the next row
                    x_tile = 0
        return img

    def s_color_picker(self, key):
        return lambda: self.color_picker(key)

    def color_picker(self, key):
        current = self.col_palette[key]
        result = QColorDialog.getColor(current)
        if result.isValid() and result is not current:
            self.update_color(key, result)
            self.update_image_lite()

    def update_color(self, key, color):
        self.col_palette[key] = color
        self.colors[key].setStyleSheet('background-color: ' + color.name())


def SpinBox(min=0, max=99, init=0, step=1, func=None):
    sb = QSpinBox()
    sb.setRange(min, max)
    sb.setValue(init)
    sb.setSingleStep(step)
    if func is not None:
        sb.valueChanged.connect(func)
    return sb


def main():
    app = QApplication(sys.argv)

    mainwindow = HexImg()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

