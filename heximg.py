'''
No license for now
'''

import sys
import os
import struct
from array import array

FMT_LINEAR = 0
FMT_NES = 1
FMT_SNES = 2
FMT_MODE7 = 3

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
            QSystemTrayIcon, QIcon, QPalette, QColor,
            QValidator
        )
        from PyQt4.QtGui import QStyleOptionProgressBarV2 as QStyleOptionProgressBar
        pyqt_version = 4
    except ImportError:
        print("Couldn't import Qt dependencies. "
              "Make sure you installed the PyQt4 package.")
        sys.exit(-1)


def divceil(numerator, denominator):
    # Reverse floor division for ceil
    return -(-numerator // denominator)


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
        for i in range(16, 256):
            self.col_palette.append(QColor(i, i, i))

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
        self.palette_area.mousePressEvent = self.palette_viewer_clicked

        self.palette_scroller = QScrollArea()
        self.palette_scroller.setWidget(self.palette_area)

        self.address_offset = HexSpinBox(0, 1000000000, init=1179648, step=64, func=self.update_image)
        self.address_fine_offset = HexSpinBox(0, 1023, func=self.update_image)
        self.image_length = SpinBox(16, 65536, init=1024, step=16, func=self.update_image)
        self.scale = SpinBox(1, 32, init=8, step=1, func=self.update_image_lite)
        self.width_s = SpinBox(8, 512, init=8, func=self.update_image)
        self.height_s = SpinBox(16, 32727, init=1300, func=self.update_image)

        # List out formats in (label, bpp, format)
        self.formats = [('1bpp', 1, FMT_LINEAR),
                        ('2bpp', 2, FMT_LINEAR),
                        ('4bpp', 4, FMT_LINEAR),
                        ('8bpp', 8, FMT_LINEAR),
                        ('NES 1bpp', 1, FMT_NES),
                        ('NES 2bpp', 2, FMT_NES),
                        ('SNES 2bpp', 2, FMT_SNES),
                        ('SNES 3bpp', 3, FMT_SNES),
                        ('SNES 4bpp', 4, FMT_SNES),
                        ('SNES 8bpp', 8, FMT_SNES),
                        ('SNES Mode7', 8, FMT_MODE7)]

        self.format = QComboBox()
        self.format.addItems([x[0] for x in self.formats])
        self.format.setCurrentIndex(8)
        self.format.currentIndexChanged.connect(self.update_image)

        self.palette_offset = HexSpinBox(0, 1000000000, init=1352640, step=32, func=self.update_palette_viewer)
        self.palette_fine_offset = HexSpinBox(0, 31, func=self.update_palette_viewer)
        self.palette_length = SpinBox(0, 16384, init=4096, step=32, func=self.update_palette_viewer)
        self.palette_scale = SpinBox(2, 32, init=8, func=self.update_palette_viewer)
        self.palette_scroller.setMinimumWidth(16*self.palette_scale.value() + 20)
        self.palette_scroller.setMaximumWidth(16*self.palette_scale.value() + 20)
        self.palette_selection = HexSpinBox(0, 1000000000, init=0, step=32, func=self.update_palette_selection)

        self.endian = QCheckBox()
        self.endian.stateChanged.connect(self.update_image)

        sidebar = QVBoxLayout()
        sidebar.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        image_settings = QGroupBox('Image Viewer')
        image_settings_form = QFormLayout()
        image_settings_form.addRow('Address', self.address_offset)
        image_settings_form.addRow('Offset', self.address_fine_offset)
        image_settings_form.addRow('Length', self.image_length)
        image_settings_form.addRow('Width', self.width_s)
        image_settings_form.addRow('Height', self.height_s)
        image_settings_form.addRow('Format', self.format)
        image_settings_form.addRow('Scale', self.scale)
        image_settings_form.addRow('Flip endian', self.endian)
        image_settings.setLayout(image_settings_form)

        palette_settings = QGroupBox('Palette Viewer')
        palette_settings_form = QFormLayout()
        palette_settings_form.addRow('Address', self.palette_offset)
        palette_settings_form.addRow('Offset', self.palette_fine_offset)
        palette_settings_form.addRow('Length', self.palette_length)
        palette_settings_form.addRow('Scale', self.palette_scale)
        palette_settings_form.addRow('Selected', self.palette_selection)
        palette_settings.setLayout(palette_settings_form)

        colorbox = QGridLayout()
        colorbox.setSpacing(0)
        self.colors = []
        for i in range(len(self.col_palette)):
            self.colors.append(QPushButton())
            self.colors[-1].setStyleSheet('background-color: ' + self.col_palette[i].name())
            self.colors[-1].setFocusPolicy(QtCore.Qt.NoFocus)
            self.colors[-1].setMaximumSize(12, 16)
            self.colors[-1].clicked.connect(self.s_color_picker(i))
            colorbox.addWidget(self.colors[-1], i//16, i % 16, 1, 1)

        btn_load = QPushButton('Load ROM')
        btn_load.clicked.connect(self.load_file)

        sidebar.addWidget(image_settings)
        sidebar.addWidget(palette_settings)
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

    def palette_viewer_clicked(self, event):
        scale = self.palette_scale.value()
        row = event.pos().y() // scale
        self.palette_selection.setValue(self.palette_offset.value()+self.palette_fine_offset.value()+row*32)

    def update_palette_selection(self):
        start = self.palette_selection.value()
        viewer = self.palette_offset.value()+self.palette_fine_offset.value()
        width = 16
        if start in range(viewer, viewer+self.palette_length.value()-512):
            row = (start - viewer)//32
            for i in range(256):
                color = QColor.fromRgb(self.palette_qimage.pixel(i % width, row + (i//width)))
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

        format = self.formats[self.format.currentIndex()]
        bpp = format[1]
        offset = int(self.address_offset.value()+self.address_fine_offset.value())
        scale = int(self.scale.value())
        length = min(len(self.ROM) - offset, int(self.image_length.value()))
        px_length = divceil(length*8, bpp)
        width = int(self.width_s.value())
        if format[2]:  # Quantize width for tiled formats
            width = divceil(width, 8)*8
        # Maximum height for QPixmap is 32,767
        height_overall = divceil(px_length, width)
        height_overall_tiles = (height_overall // 8)
        #self.image_columns = divceil(height_overall * scale, int(self.height_s.value()))
        self.image_columns = divceil(height_overall_tiles * scale, self.height_s.value()//8)
        height = divceil(height_overall_tiles, self.image_columns) * 8
        col_length = (height * width * bpp) // 8
        self.image_qimages = []

        layout = self.image_area.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            layout.removeWidget(widget)
            widget.setParent(None)

        for col in range(self.image_columns):
            byterange = range(offset + col*col_length, min(offset + (col+1)*col_length, len(self.ROM)))
            qimage = self.create_image(format, width, height, byterange)
            self.image_qimages.append(qimage)
            pixmap = QtGui.QPixmap.fromImage(qimage)
            pixmap_scaled = pixmap.scaled(pixmap.size() * scale)
            label = QLabel()
            label.setPixmap(pixmap_scaled)
            layout.addWidget(label)
        self.image_area.resize((pixmap_scaled.width()+layout.spacing())*self.image_columns, pixmap_scaled.height())

        self.address_offset.setSingleStep(2*width)

    def create_image(self, format, width, height, byterange):
        bpp = format[1]  # Bits per px
        img = QtGui.QImage(width, height, QtGui.QImage.Format_Indexed8)
        img.setColorTable([c.rgba() for c in self.col_palette])
        imgbits = img.bits()
        imgbits.setsize(img.byteCount())
        if format[2] == FMT_LINEAR:
            self._create_image_linear(imgbits, byterange, bpp)
        elif format[2] == FMT_MODE7:
            self._create_image_mode7(imgbits, width, byterange)
        elif format[2] == FMT_SNES:
            self._create_image_snes(imgbits, width, byterange, bpp)
        elif format[2] == FMT_NES:
            self._create_image_nes(imgbits, width, byterange, bpp)
        return img

    def _create_image_linear(self, imgbits, byterange, bpp):
        mask = int(2**(bpp)-1)  # Bitmask form
        bitrange = range(8//bpp)
        if not self.endian.isChecked():
            bitrange = reversed(bitrange)
        ptr = 0
        for i in byterange:
            byte = self.ROM[i]
            for j in bitrange:
                offset = j*bpp
                bits = byte >> offset & mask
                imgbits[ptr] = struct.pack('B', bits)
                ptr += 1

    def _create_image_nes(self, imgbits, width, byterange, planes):
        '''
        Graphics are stored in 8x8 tiles
        Colour bits are segregated by "plane"
        Bytes 0-7 contain plane 0
        Bytes 8-15 contain plane 1
        '''
        bytes_per_tile = planes*8
        ptr = 0
        x_tile = 0
        tile = array('B', range(64))
        # i now has a 32 step size
        for i in range(byterange.start, byterange.stop, bytes_per_tile):
            bytes = self.ROM[i:i+bytes_per_tile]
            t_ptr = 0
            for j in range(0, 8):
                for x in reversed(range(8)):
                    tile[t_ptr] = (bytes[j] >> x & 1)
                    t_ptr += 1
            if planes == 2:
                t_ptr = 0
                for j in range(8, 16):
                    for x in reversed(range(8)):
                        tile[t_ptr] |= (bytes[j] >> x & 1) << 1
                        t_ptr += 1

            if width == 8:
                imgbits[ptr:ptr+64] = tile  # struct.pack('B', tile)
                ptr += 64
            else:
                for y in range(8):
                    imgbits[ptr+(y*width):ptr+(y*width)+8] = tile[y*8:y*8+8]
                ptr += 8  # move along one tile's width
                x_tile += 1
                if x_tile >= width//8:
                    ptr += width*7  # move to the start of the next row
                    x_tile = 0

    def _create_image_snes(self, imgbits, width, byterange, planes):
        '''
        Graphics are stored in 8x8 tiles
        Colour bits are segregated by "plane"
        Bytes 0,2,4,6,8,10,12,14 contain plane 0 (LSB of each pixel?)
        Bytes 1,3,5,7,9,11,13,15 contain plane 1
        Bytes 16,18,...,30 make up plane 2
        Bytes 17,19,...,31 make up plane 3
        Bytes 32,34,...,46 plane 4
        Bytes 33,35,...,47 plane 5
        Bytes 48,50,...,62 plane 6
        Bytes 49,51,...,63 plane 7 (MSB of each pixel?)
        '''
        bytes_per_tile = planes*8
        ptr = 0
        x_tile = 0
        tile = array('B', range(64))
        # i now has a 32 step size
        for i in range(byterange.start, byterange.stop, bytes_per_tile):
            bytes = self.ROM[i:i+bytes_per_tile]
            t_ptr = 0
            for j in range(0, 16, 2):
                for x in reversed(range(8)):
                    tile[t_ptr] = (bytes[j] >> x & 1) | ((bytes[j+1] >> x & 1) << 1)
                    t_ptr += 1
            t_ptr = 0
            if planes == 3:
                for j in range(16, 24, 1):
                    for x in reversed(range(8)):
                        tile[t_ptr] |= ((bytes[j] >> x & 1) << 2)
                        t_ptr += 1
            elif planes >= 4:
                for j in range(16, 32, 2):
                    for x in reversed(range(8)):
                        tile[t_ptr] |= ((bytes[j] >> x & 1) << 2) | ((bytes[j+1] >> x & 1) << 3)
                        t_ptr += 1
            if planes == 8:
                t_ptr = 0
                for j in range(32, 48, 2):
                    for x in reversed(range(8)):
                        tile[t_ptr] |= ((bytes[j] >> x & 1) << 4) | ((bytes[j+1] >> x & 1) << 5) \
                            | ((bytes[j+16] >> x & 1) << 6) | ((bytes[j+17] >> x & 1) << 7)
                        t_ptr += 1

            if width == 8:
                imgbits[ptr:ptr+64] = tile  # struct.pack('B', tile)
                ptr += 64
            else:
                for y in range(8):
                    imgbits[ptr+(y*width):ptr+(y*width)+8] = tile[y*8:y*8+8]
                ptr += 8  # move along one tile's width
                x_tile += 1
                if x_tile >= width//8:
                    ptr += width*7  # move to the start of the next row
                    x_tile = 0

    def _create_image_mode7(self, imgbits, width, byterange):
        # Each byte is a pixel. Only catch is it's tiled.
        ptr = 0
        x_tile = 0
        tile = array('B', range(64))
        # i now has a 32 step size
        for i in range(byterange.start, byterange.stop, 64):
            tile = self.ROM[i:i+64]
            if width == 8:
                imgbits[ptr:ptr+64] = tile  # struct.pack('B', tile)
                ptr += 64
            else:
                for y in range(8):
                    imgbits[ptr+(y*width):ptr+(y*width)+8] = tile[y*8:y*8+8]
                ptr += 8  # move along one tile's width
                x_tile += 1
                if x_tile >= width//8:
                    ptr += width*7  # move to the start of the next row
                    x_tile = 0

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


class HexSpinBox(QSpinBox):
    def __init__(self, min=0, max=99, init=0, step=1, func=None):
        super().__init__()
        self.setRange(min, max)
        self.setValue(init)
        self.setSingleStep(step)
        self.valueChanged.connect(func)
        self.setButtonSymbols(QtGui.QAbstractSpinBox.PlusMinus)

    def valueFromText(self, text):
        if text[:2] == '0x':
            return int(text[2:], 16)
        else:
            return int(text)

    def validate(self, input, pos):
        if input == '':
            return QValidator.Intermediate, input, pos
        if input[0].lower() == 'x':
            input = '0' + input
            pos += 1
        if input[:2] == '0x':
            hex = input[2:]
            if hex == '':
                return QValidator.Intermediate, input, pos
            try:
                i = int(hex, 16)
                input = '0x' + input[2:].upper()
                return QValidator.Acceptable, input, pos
            except:
                pass
        else:
            try:
                i = int(input)
                return QValidator.Acceptable, input, pos
            except:
                pass
        return QValidator.Invalid, input, pos

    def textFromValue(self, v):
        return '0x{:02X}'.format(v)


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

