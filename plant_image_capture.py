import sys
import os
import numpy
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import datetime
import gphoto2 as gp
from pathlib import Path
import pandas as pd


ROOT_PATH = Path('Documents/pic/')
ROOT_PATH = Path.home() / ROOT_PATH

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
        #self.proc_list.setStyleSheet('background-color: palette(window)')

        left_layout.addWidget(self.proc_list)

        # Centre pane / capture pane
        capture_box = QGroupBox('Capture')
        centre_layout = QVBoxLayout()
        centre_layout.setSpacing(16)
        centre_layout.setContentsMargins(16,16, 16 , 16)
        capture_box.setLayout(centre_layout)

        class ImageWidget(QLabel):
            def __init__(self, img):
                super(ImageWidget, self).__init__()
                self.setFrameStyle(QFrame.StyledPanel)
                self.pixmap = QPixmap(img)

            def paintEvent(self, event):
                size = self.size()
                painter = QPainter(self)
                point = QPoint(0,0)
                scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
                # start painting the label from left upper corner
                point.setX((size.width() - scaledPix.width())/2)
                point.setY((size.height() - scaledPix.height())/2)
                painter.drawPixmap(point, scaledPix)

            def changePixmap(self, img):
                self.pixmap = QPixmap(img)
                self.repaint()

        
        self.image_widget = ImageWidget(str(Path.home() / 'Documents/nppc.png'))
        self.image_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        data_input_layout = QGridLayout()
        policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        data_input_layout.setVerticalSpacing(4)

        usr_id_label = QLabel('User ID')
        usr_id_label.setSizePolicy(policy)
        data_input_layout.addWidget(usr_id_label, 0, 0)
        self.usr_id_input = QLineEdit()
        self.usr_id_input.textChanged.connect(self.text_changed)
        self.usr_id_input.setPlaceholderText('e.g. kia5')
        data_input_layout.addWidget(self.usr_id_input, 1, 0)

        exp_id_label = QLabel('Experiment ID')
        exp_id_label.setSizePolicy(policy)
        data_input_layout.addWidget(exp_id_label, 0, 1)
        self.exp_id_input = QLineEdit()
        self.exp_id_input.textChanged.connect(self.text_changed)
        self.exp_id_input.setPlaceholderText('e.g. AT025')
        data_input_layout.addWidget(self.exp_id_input, 1, 1)

        plant_id_label = QLabel('Plant ID')
        plant_id_label.setSizePolicy(policy)
        data_input_layout.addWidget(plant_id_label, 0, 2)
        self.plant_id_input = QLineEdit()
        self.plant_id_input.textChanged.connect(self.text_changed)
        self.plant_id_input.setPlaceholderText('e.g. 351341')
        data_input_layout.addWidget(self.plant_id_input, 1, 2)

        image_id_label = QLabel('Image ID')
        image_id_label.setSizePolicy(policy)
        data_input_layout.addWidget(image_id_label, 0, 3)
        self.image_id_input = QLineEdit()
        self.image_id_input.textChanged.connect(self.text_changed)
        self.image_id_input.setPlaceholderText('e.g. 1 or M')
        data_input_layout.addWidget(self.image_id_input, 1, 3)

        self.capture_btn_layout = QHBoxLayout()

        self.preview_btn = QPushButton('Preview')
        self.preview_btn.clicked.connect(self.preview_on_click)
        self.capture_btn_layout.addWidget(self.preview_btn, 1)
        self.preview_btn.setMaximumHeight(50)

        self.capture_btn = QPushButton('Capture')
        self.capture_btn.clicked.connect(self.capture_on_click)
        self.capture_btn.setStyleSheet('background-color:red')
        self.capture_btn_layout.addWidget(self.capture_btn, 5)
        self.capture_btn.setMaximumHeight(50)
        self.capture_btn.setMaximumWidth(600)

        self.skip_btn = QPushButton('Skip')
        self.skip_btn.setEnabled(False)
        self.capture_btn_layout.addWidget(self.skip_btn, 1)
        self.skip_btn.setMaximumHeight(50)

        centre_layout.addWidget(self.image_widget)
        si = QSpacerItem(20, 20)
        centre_layout.addSpacerItem(si)
        centre_layout.addLayout(data_input_layout)

        self.image_filename_label = QLabel('Image filename: ')
        self.image_filename_label.setSizePolicy(policy)
        #centre_layout.addWidget(self.image_filename_label)

        centre_layout.addLayout(self.capture_btn_layout)

        # Right pane / queue pane
        queue_box = QGroupBox('Queue')
        right_layout = QVBoxLayout()
        queue_box.setLayout(right_layout)  
        self.queue_list = QListWidget()
        #self.queue_list.setStyleSheet('background-color: palette(window)')

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

    def text_changed(self, event):
        user_id = self.usr_id_input.text().lower().replace(' ', '_')
        experiment_id = self.exp_id_input.text().upper().replace(' ', '_')
        plant_id = self.plant_id_input.text().upper().replace(' ', '_')
        image_id = self.image_id_input.text().upper().replace(' ', '_')
        filename = '{0}_{1}_{2}_{3}.jpg'.format(experiment_id, plant_id, image_id, user_id)
        self.capture_btn.setText('Capture {}'.format(filename))

    def capture_on_click(self):
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

    def skip_on_click(self):
        pass

    def load_csv_on_click(self):
        pass

    def next_image(self):
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
        while(images_captured < 2):
            while(result[0] != gp.GP_EVENT_FILE_ADDED):
                result = camera.wait_for_event(100)
        
            images.append(result[1])
            result = [None, None]
            images_captured += 1
        
        camera_file_jpg = camera.file_get(images[0].folder, images[0].name, gp.GP_FILE_TYPE_NORMAL)
        #camera_file_nef = camera.file_get(images[1].folder, images[1].name, gp.GP_FILE_TYPE_NORMAL)

        camera_file_jpg.save('/tmp/preview.jpg')
        self.image_widget.changePixmap('/tmp/preview.jpg')
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
        
        while(images_captured < 2):
            while(result[0] != gp.GP_EVENT_FILE_ADDED):
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
