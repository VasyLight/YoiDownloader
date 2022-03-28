from pytube import YouTube
from better_ffmpeg_progress import FfmpegProcess
import pathlib

import sys
import re
import os
import subprocess
import qtmodern.styles
import qtmodern.windows

from PyQt5.QtCore import (
    Qt, QDir
)
from PyQt5.QtWidgets import (
    QApplication,
    QPlainTextEdit,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QDialog,
    QSpinBox,
    QHBoxLayout, QCheckBox, QTabWidget, QWidget, QDoubleSpinBox, QStackedWidget, QInputDialog, QLineEdit, QComboBox,
    QProgressBar, QFileDialog,
)

global yt
global file_size
global path


class MainWidget(QDialog):
    def __init__(self):
        super().__init__()

        # Process
        self.p = None  # Default empty value.

        self.lbl_url = QLabel('Ссылка на видео: ')
        self.lbl_url.setAlignment(Qt.AlignCenter)
        self.ptUrl = QPlainTextEdit(self)
        self.ptUrl.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.cb_quality = QComboBox()
        self.cb_quality.setHidden(True)

        self.dir = str(pathlib.Path().resolve()) + '\\download\\'

        self.path = QDir.homePath()
        self.output = ''
        self.mime_type = ''

        self.btnInit = QPushButton('Вперед', self)
        self.btnInit.pressed.connect(self.init)  # Запуск процесса

        self.btnDownload = QPushButton('Загрузить', self)
        self.btnDownload.setHidden(True)
        self.btnDownload.pressed.connect(self.download)

        self.cb_audioOnly = QCheckBox()
        self.lbl_audioOnly = QLabel('Только аудио')
        self.btn_choose_dir = QPushButton('Выбрать папку')
        self.btn_choose_dir.pressed.connect(self.get_path)

        self.btn_get_file = QPushButton('Открыть файл')
        self.btn_get_file.setHidden(True)
        self.btn_get_file.pressed.connect(self.evt_open_dir)

        self.btnInit.setStyleSheet('background-color:#c2fbd7;color:green;')
        self.btnDownload.setStyleSheet('background-color:#c2fbd7;color:green;')

        # Кнопка очистки лога
        self.btnClear = QPushButton('Новое видео', self)
        self.btnClear.setHidden(True)
        self.btnClear.pressed.connect(self.new_vid)
        # Progress bar
        self.lbl_bar = QLabel()
        self.lbl_bar.setHidden(True)
        self.bar = QProgressBar()
        self.bar.setHidden(True)
        # Log
        self.log = QPlainTextEdit(self)
        self.log.setReadOnly(True)
        self.log.setHidden(True)
        self.log.resize(450, 400)

        # Запускаем layout

        layout_plate = QVBoxLayout()  # Главный layout
        layout_checkboxes = QHBoxLayout()

        layout_plate.addWidget(self.lbl_url)
        layout_plate.addWidget(self.ptUrl)
        layout_plate.addWidget(self.cb_quality)
        layout_plate.addWidget(self.log, 0)
        layout_plate.addWidget(self.btnInit)
        layout_plate.addWidget(self.lbl_bar)
        layout_plate.addWidget(self.bar)
        layout_plate.addWidget(self.btnDownload)
        layout_plate.addWidget(self.btnClear, 0)
        layout_plate.addWidget(self.btn_get_file)

        layout_checkboxes.addWidget(self.lbl_audioOnly)
        layout_checkboxes.addWidget(self.cb_audioOnly)
        layout_checkboxes.addWidget(self.btn_choose_dir)
        layout_plate.addLayout(layout_checkboxes)

        layout_plate.setContentsMargins(70, 70, 70, 70)
        layout_plate.addSpacing(40)
        layout_plate.setSpacing(20)

        self.setLayout(layout_plate)

    def init(self):
        self.btnInit.setHidden(True)
        self.lbl_bar.setHidden(False)
        self.log.setHidden(False)
        self.btnDownload.setHidden(False)
        self.btnClear.setHidden(False)
        url = self.ptUrl.toPlainText()
        self.lbl_bar.setText('Заргузка данных..')
        global yt
        yt = YouTube(url)

        if not self.cb_audioOnly.isChecked():
            self.cb_quality.setHidden(False)

            for stream in yt.streams:
                if stream.resolution is not None:
                    mime_type = str(stream.mime_type.partition("/")[2])
                    res = str(stream.resolution)
                    itag = ' - ' + str(stream.itag)
                    have_audio = str(' / Есть аудио' if stream.includes_audio_track is True else ' / Нет аудио')
                    self.cb_quality.addItem('{0}{1}'.format(mime_type + have_audio, ' / ' + res) + itag)
        self.ptUrl.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.message(yt.title)

    def message(self, s):
        self.log.appendPlainText(s)

    def clear_log(self):
        self.log.clear()

    def get_path(self):
        self.path = QFileDialog().getExistingDirectory(
            caption="Выберите папку для сохранения файла",
            directory=QDir().homePath(),
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

        if self.path:
            self.dir = self.path

    def evt_open_dir(self):
        subprocess.Popen('explorer /select, ' + f"{self.dir + self.output}")
        print('explorer /select, ' + f"{self.dir + self.output}")

    def new_vid(self):
        self.btn_get_file.setHidden(True)
        self.btnClear.setStyleSheet('')
        self.lbl_audioOnly.setHidden(False)
        self.cb_audioOnly.setHidden(False)
        self.btnInit.setHidden(False)
        self.btnDownload.setHidden(True)
        self.cb_quality.clear()
        self.cb_quality.setHidden(True)
        self.log.clear()
        self.log.setHidden(True)
        self.bar.setHidden(True)
        self.lbl_bar.setHidden(True)
        self.ptUrl.clear()

    def update_progress(self, stream=None, chunk=None, bytes_remaining=None):
        global file_size

        percent = ((file_size - bytes_remaining)/file_size) * 100
        self.bar.setValue(round(percent, 0))

    def handle_progress_info(self, percentage, speed, eta, estimated_filesize):
        self.bar.setValue(round(percentage, 0))

    def merge_audio_and_video_download(self, url, audio, video, output):

        input_video = url + video
        input_audio = url + audio
        self.output = url + output

        process = FfmpegProcess(["ffmpeg", "-i", f"{input_video}", f"{input_audio}", "-c:v", "copy",
                                 "-c:a", "aac", f"{self.output}"])

        process.run(progress_handler=self.handle_progress_info)

    def download(self):
        global yt
        global file_size
        global path

        self.lbl_audioOnly.setHidden(True)
        self.cb_audioOnly.setHidden(True)
        self.btnDownload.setHidden(True)

        itag = self.cb_quality.currentText().partition("-")[2]
        # print(q)
        # f = self.cb_format.currentText()
        # print(f)
        url = self.ptUrl.toPlainText()

        yt = YouTube(url, on_progress_callback=self.update_progress)
        self.bar.setHidden(False)
        self.lbl_bar.setHidden(False)

        # Check for an appropriate name
        title = re.sub(r"[\\#%!'.?|@*/<>]", "", yt.title)

        if self.cb_audioOnly.isChecked():
            file_size = yt.streams.get_audio_only().filesize
            self.output = f"{title}" + '.' + 'mp3'

            self.lbl_bar.setText('Загрузка аудио: ' + f"{round(file_size / 1000000, 2)}" + 'Mb')
            yt.streams.get_audio_only().download(self.dir, filename=f"{title}" + '.' + 'mp3')
        else:
            file_size = yt.streams.get_by_itag(int(itag)).filesize

            have_an_audio = yt.streams.get_by_itag(int(itag)).audio_codec
            mime_type = str(yt.streams.get_by_itag(int(itag)).mime_type.partition("/")[2])

            quality = yt.streams.get_by_itag(int(itag)).resolution
            self.lbl_bar.setText('Загрузка видео: ' + f"{file_size / 1000000}" + 'Mb')

            if have_an_audio is None:
                video = f"{title}" + f"_{quality}" + '_video' + '.' + mime_type
                audio = f"{title}" + f"_{quality}" + '_audio' + '.' + mime_type
                output = f"{title}" + f"_{quality}" + '.' + mime_type

                yt.streams.get_by_itag(int(itag)).download(self.dir, filename=video)
                yt.streams.get_audio_only().download(self.dir, filename=audio)
                self.lbl_bar.setText('Совмещаем аудио и видео')
                self.bar.setValue(50)
                self.merge_audio_and_video_download(self.dir, audio, video, output)
                self.bar.setValue(100)
                self.lbl_bar.setText('Удаляем остатки')
                self.bar.setValue(0)
                os.remove(self.dir + video)
                os.remove(self.dir + audio)
                self.bar.setValue(100)
            else:
                self.output = f"{title}" + f"_{quality}" + '.' + mime_type
                yt.streams.get_by_itag(int(itag)).download(self.dir, filename=self.output)
                self.bar.setValue(100)

        self.btn_get_file.setHidden(False)
        self.btn_get_file.setStyleSheet('background-color:#c2fbd7;color:green;')
        self.btn_choose_dir.setHidden(True)
        self.lbl_bar.setText('Готово')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWidget()

    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(win)
    mw.show()

    sys.exit(app.exec_())
