import sys
import os
from tarfile import ExFileObject
import numpy
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import datetime
import gphoto2 as gp
from pathlib import Path
import pandas as pd

ROOT_PATH = Path.home() / 'Documents' / 'pic'


class PICWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle('Plant Image Capture')

        # GUI Init
        main_layout = QHBoxLayout()

        # Left pane / processed pane
        processed_box = QGroupBox('Processed')
        left_layout = QVBoxLayout()
        processed_box.setLayout(left_layout)

        self.proc_list = QListWidget()
        # self.proc_list.setStyleSheet('background-color: palette(window)')

        left_layout.addWidget(self.proc_list)

        # Centre pane / capture pane
        capture_box = QGroupBox('Capture')
        centre_layout = QVBoxLayout()
        centre_layout.setSpacing(16)
        centre_layout.setContentsMargins(16, 16, 16, 16)
        capture_box.setLayout(centre_layout)

        class ImageWidget(QLabel):
            def __init__(self, img):
                super(ImageWidget, self).__init__()
                self.setFrameStyle(QFrame.StyledPanel)
                self.pixmap = QPixmap(img)

            def paintEvent(self, event):
                size = self.size()
                painter = QPainter(self)
                point = QPoint(0, 0)
                scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
                # start painting the label from left upper corner
                point.setX((size.width() - scaledPix.width()) // 2)
                point.setY((size.height() - scaledPix.height()) // 2)
                painter.drawPixmap(point, scaledPix)

            def changePixmap(self, img):
                self.pixmap = QPixmap(img)
                self.repaint()

        # self.image_widget = ImageWidget(str(Path.home() / 'Documents/nppc.png'))
        self.image_widget = ImageWidget('nppc.png')
        self.image_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        data_input_layout = QGridLayout()
        policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        data_input_layout.setVerticalSpacing(4)

        usr_id_label = QLabel('User ID')
        usr_id_label.setSizePolicy(policy)
        data_input_layout.addWidget(usr_id_label, 0, 0)
        self.usr_id_input = QLineEdit()
        self.usr_id_input.textChanged.connect(self.text_changed_norm)
        self.usr_id_input.setPlaceholderText('e.g. kia5')
        data_input_layout.addWidget(self.usr_id_input, 1, 0)

        exp_id_label = QLabel('Experiment ID')
        exp_id_label.setSizePolicy(policy)
        data_input_layout.addWidget(exp_id_label, 0, 1)
        self.exp_id_input = QLineEdit()
        self.exp_id_input.textChanged.connect(self.text_changed_norm)
        self.exp_id_input.setPlaceholderText('e.g. AT025')
        data_input_layout.addWidget(self.exp_id_input, 1, 1)

        plant_id_label = QLabel('Plant ID')
        plant_id_label.setSizePolicy(policy)
        data_input_layout.addWidget(plant_id_label, 0, 2)
        self.plant_id_input = QLineEdit()
        self.plant_id_input.textChanged.connect(self.text_changed_norm)
        self.plant_id_input.setPlaceholderText('e.g. 351341')
        data_input_layout.addWidget(self.plant_id_input, 1, 2)

        image_id_label = QLabel('Image ID')
        image_id_label.setSizePolicy(policy)
        data_input_layout.addWidget(image_id_label, 0, 3)
        self.image_id_input = QLineEdit()
        self.image_id_input.textChanged.connect(self.text_changed_norm)
        self.image_id_input.setPlaceholderText('e.g. 1 or M')
        data_input_layout.addWidget(self.image_id_input, 1, 3)

        self.capture_btn_layout = QHBoxLayout()

        self.capture_btn = QPushButton('Capture')
        self.capture_btn.clicked.connect(self.capture_on_click_norm)
        self.capture_btn.setStyleSheet('background-color:red')
        self.capture_btn_layout.addWidget(self.capture_btn, 5)
        self.capture_btn.setMaximumHeight(50)
        self.capture_btn.setMaximumWidth(600)

        self.preview_btn = QPushButton('Preview')
        self.preview_btn.clicked.connect(self.preview_on_click)
        self.capture_btn_layout.addWidget(self.preview_btn, 1)
        self.preview_btn.setMaximumHeight(50)

        cap_sep = QFrame()
        cap_sep.setFrameShape(QFrame.Shape.VLine)
        # cap_sep.setFrameShadow(QFrame.Shadow.Sunken)
        cap_sep.setMaximumHeight(20)
        self.capture_btn_layout.addWidget(cap_sep, 1)

        self.rem_btn = QPushButton('Remove')
        self.rem_btn.setEnabled(False)
        self.capture_btn_layout.addWidget(self.rem_btn, 1)
        self.rem_btn.setMaximumHeight(50)

        self.load_btn = QPushButton('Load CSV')
        self.load_btn.clicked.connect(self.load_csv_on_click)
        self.capture_btn_layout.addWidget(self.load_btn, 1)
        self.load_btn.setMaximumHeight(50)

        centre_layout.addWidget(self.image_widget)
        si = QSpacerItem(20, 20)
        centre_layout.addSpacerItem(si)
        centre_layout.addLayout(data_input_layout)

        self.image_filename_label = QLabel('Image filename: ')
        self.image_filename_label.setSizePolicy(policy)
        # centre_layout.addWidget(self.image_filename_label)

        centre_layout.addLayout(self.capture_btn_layout)

        # Right pane / queue pane
        queue_box = QGroupBox('Queue')
        right_layout = QVBoxLayout()
        queue_box.setLayout(right_layout)
        self.queue_list = QListWidget()
        self.queue_list.itemSelectionChanged.connect(self.queue_changed)
        # self.queue_list.setStyleSheet('background-color: palette(window)')

        right_layout.addWidget(self.queue_list)

        # Finalising
        main_layout.addWidget(processed_box)
        main_layout.addWidget(capture_box, 1)
        main_layout.addWidget(queue_box)

        layout = QVBoxLayout()
        layout.addLayout(main_layout)
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

        self.setLayout(layout)

        # Variables
        self.captured = []
        self.filename = ''

        # Directory
        self.root = Path(ROOT_PATH)
        self.root.mkdir(exist_ok=True)

    def text_changed_queue(self, event):
        user_id = self.usr_id_input.text().lower().replace(' ', '_')
        image_id = self.image_id_input.text().upper().replace(' ', '_')
        filename = '{0}_{1}_{2}.jpg'.format(user_id, self.barcode, image_id)
        self.capture_btn.setText('Capture {}'.format(filename))

    def capture_on_click_queue(self):
        self.capture_btn_layout.setEnabled(False)
        user_id = self.usr_id_input.text().lower().replace(' ', '_')
        image_id = self.image_id_input.text().upper().replace(' ', '_')
        filename = '{0}_{1}_{2}.jpg'.format(user_id, self.barcode, image_id)
        self.capture_btn.setText('Capture {}'.format(filename))
        # experiment_id = self.exp_id_input.text().upper().replace(' ', '_')

        dir = self.root / self.out.lower()
        dir.mkdir(exist_ok=True)
        self.capture(dir, filename, user_id, self.out.lower(), self.barcode, image_id)
        self.capture_btn_layout.setEnabled(True)
        self.queue_list.selectedItems()[0].setBackground(QColor((128, 128, 128, 255)))

    def text_changed_norm(self, event):
        user_id = self.usr_id_input.text().lower().replace(' ', '_')
        experiment_id = self.exp_id_input.text().upper().replace(' ', '_')
        plant_id = self.plant_id_input.text().upper().replace(' ', '_')
        image_id = self.image_id_input.text().upper().replace(' ', '_')
        filename = '{0}_{1}_{2}_{3}.jpg'.format(experiment_id, plant_id, image_id, user_id)
        self.capture_btn.setText('Capture {}'.format(filename))

    def capture_on_click_norm(self):
        self.capture_btn_layout.setEnabled(False)
        user_id = self.usr_id_input.text().lower().replace(' ', '_')
        experiment_id = self.exp_id_input.text().upper().replace(' ', '_')
        plant_id = self.plant_id_input.text().upper().replace(' ', '_')
        image_id = self.image_id_input.text().upper().replace(' ', '_')
        filename = '{0}_{1}_{2}_{3}'.format(experiment_id, plant_id, image_id, user_id)

        dir = self.root / experiment_id.lower()
        dir.mkdir(exist_ok=True)
        self.capture(dir, filename, user_id, experiment_id, plant_id, image_id)
        self.capture_btn_layout.setEnabled(True)

    def preview_on_click(self):
        self.capture_btn_layout.setEnabled(False)
        self.preview()
        self.capture_btn_layout.setEnabled(True)

    def remove_on_click(self):
        pass

    def load_csv_on_click(self):
        try:
            fname = QFileDialog.getOpenFileName(self, 'Open CSV file', str(Path.home()), 'CSV File (*.csv)')[0]
            df = pd.read_csv(fname)
            if len(df) < 1:
                raise Exception

        except Exception:
            self.status_bar.showMessage('Load failed or row count less than 1.')
            return

        class ComboDialog(QDialog):
            def __init__(self, items):
                super().__init__()
                QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

                self.buttonBox = QDialogButtonBox(QBtn)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                self.layout = QVBoxLayout()
                self.combo_box = QComboBox()
                self.combo_box.addItems(items)

                self.layout.addWidget(self.combo_box)
                self.layout.addWidget(self.buttonBox)
                self.setLayout(self.layout)

            def get_val(self):
                return self.val

            def accept(self):
                self.val = self.combo_box.currentText()
                super().accept()

        cd = ComboDialog(list(df.columns))
        btn = cd.exec()

        if btn:
            val = cd.get_val()
            self.queue_list.clear()
            titles = list(df[val])
            for title in titles:
                QListWidgetItem(str(title), self.queue_list)

        else:
            self.status_bar.showMessage('Load aborted.')

        self.status_bar.showMessage(f'Successfully loaded CSV file {Path(fname).name}, images will be stored in folder {Path(fname).stem}')
        self.out = Path(fname).stem
        try:
            self.queue_list.setCurrentRow(0)
        except Exception:
            pass

        self.exp_id_input.setEnabled(False)
        self.plant_id_input.setEnabled(False)
        self.plant_id_input.setText('')

        self.usr_id_input.textChanged.disconnect(self.text_changed_norm)
        self.image_id_input.textChanged.disconnect(self.text_changed_norm)
        self.capture_btn.clicked.disconnect(self.capture_on_click_norm)

        self.usr_id_input.textChanged.connect(self.text_changed_queue)
        self.image_id_input.textChanged.connect(self.text_changed_queue)
        self.capture_btn.clicked.connect(self.capture_on_click_queue)

        self.load_btn.setEnabled(False)

    def queue_changed(self):
        try:
            selected = self.queue_list.selectedItems()
            self.barcode = selected[0].text()
            self.text_changed_queue(None)
        except:
            return

        # set capture button text

    def next_queue(self):
        # grey out top of queue
        # select next
        # populate text boxes
        pass

    def preview(self):
        # Check camera status
        try:
            camera = gp.Camera()
            camera.init()
        except gp.GPhoto2Error as e:
            self.status_bar.showMessage('Capture failed - GPhoto2 Error: {}'.format(str(e)))
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        camera.trigger_capture()

        images = []
        result = [None, None]
        images_captured = 0
        while (images_captured < 2):
            while (result[0] != gp.GP_EVENT_FILE_ADDED):
                result = camera.wait_for_event(100)

            images.append(result[1])
            result = [None, None]
            images_captured += 1

        camera_file_jpg = camera.file_get(images[0].folder, images[0].name, gp.GP_FILE_TYPE_NORMAL)
        # camera_file_nef = camera.file_get(images[1].folder, images[1].name, gp.GP_FILE_TYPE_NORMAL)

        camera_file_jpg.save(str(ROOT_PATH / 'preview.jpg'))
        self.image_widget.changePixmap(str(ROOT_PATH / 'preview.jpg'))
        QApplication.restoreOverrideCursor()
        return

    def capture(self, dir, filename, user_id, experiment_id, plant_id, image_id):
        # dir = image capture directory (not the root pic dir)
        # Check camera status
        try:
            camera = gp.Camera()
            camera.init()
        except gp.GPhoto2Error as e:
            self.status_bar.showMessage('Capture failed - GPhoto2 Error: {}'.format(str(e)))
            return

        # Check file doesn't already exist and check with user
        if Path.exists((dir / filename).with_suffix('.jpg')) or Path.exists((dir / filename).with_suffix('.nef')):
            query = 'At least one of the images you are trying to save already exists, ' + \
                    'are you sure you want to overwrite both of them? This is irreversable.'

            reply = QMessageBox.question(self, 'Files already exist', query, QMessageBox.Yes, QMessageBox.No)
            if not reply == QMessageBox.Yes:
                return

        # setup metadata collection
        img_dict = {}
        img_dict['image'] = [str(filename)]
        img_dict['user_id'] = [str(user_id)]
        img_dict['experiment_id'] = [str(experiment_id)]
        img_dict['plant_id'] = [str(plant_id)]
        img_dict['image_id'] = [str(image_id)]
        today = datetime.date.today()
        img_dict['date_taken'] = [today.strftime('%y-%m-%d')]

        # trigger image capture and collect both RAW and JPG filetypes
        QApplication.setOverrideCursor(Qt.WaitCursor)
        camera.trigger_capture()

        images = []
        result = [None, None]

        images_captured = 0

        while (images_captured < 2):
            while (result[0] != gp.GP_EVENT_FILE_ADDED):
                result = camera.wait_for_event(100)

            images.append(result[1])
            result = [None, None]
            images_captured += 1

        camera_file_jpg = camera.file_get(images[0].folder, images[0].name, gp.GP_FILE_TYPE_NORMAL)
        camera_file_nef = camera.file_get(images[1].folder, images[1].name, gp.GP_FILE_TYPE_NORMAL)

        jpgfile = (dir / filename).with_suffix('.jpg')
        neffile = (dir / filename).with_suffix('.nef')
        camera_file_jpg.save(str(jpgfile))
        camera_file_nef.save(str(neffile))
        self.image_widget.changePixmap(str((dir / filename).with_suffix('.jpg')))

        img_dict['file_jpeg'] = [str(Path(*jpgfile.parts[-2:]))]
        img_dict['file_nef'] = [str(Path(*neffile.parts[-2:]))]

        # add item to captured list
        QListWidgetItem(filename, self.proc_list)
        self.status_bar.showMessage('{} images saved'.format(filename))

        # save metadata to csv file by either adding to existing or creating new.
        img_dict = pd.DataFrame(data=img_dict)

        try:
            csv = pd.read_csv(str((dir / experiment_id).with_suffix('.csv')), dtype=str)
            csv = csv.append(img_dict, ignore_index=True, sort=False)
        except:
            csv = img_dict
        finally:
            csv.to_csv(str((dir / experiment_id).with_suffix('.csv')), index=False)

        QApplication.restoreOverrideCursor()


app = QApplication(sys.argv)
window = PICWindow()
window.show()
sys.exit(app.exec())
