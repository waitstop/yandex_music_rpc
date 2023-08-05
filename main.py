import os.path
import sys
import time
import webbrowser
from typing import Callable

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QSlider, QCheckBox
from ui_main_window import Ui_MainWindow
from pypresence import Presence
from pypresence.exceptions import PyPresenceException
from yandex_music import Client
from yandex_music.exceptions import NotFoundError, YandexMusicError
import configparser


def load_config(file_name: str = "config.txt") -> dict:
    config = configparser.ConfigParser()
    default_settings = {
        'delay': 5,
        'show_button': 'true'
    }
    if not os.path.exists(file_name):
        config['secret'] = {'yandex_oauth_token': ''}
        config['settings'] = default_settings
        with open(file_name, 'x') as f:
            config.write(f)
    else:
        config.read_file(open(file_name))
    return {**dict(config.items('secret')), **dict(config.items('settings'))}


def set_config(token: str, settings: dict, file_name: str = "config.txt") -> None:
    config = configparser.ConfigParser()
    config['secret'] = {'yandex_oauth_token': token}
    config['settings'] = settings
    with open(file_name, 'w') as f:
        config.write(f)


class WorkerSignals(QObject):
    finished = Signal()


class Worker(QRunnable):
    def __init__(self, work: Callable):
        super().__init__()
        self.signals = WorkerSignals()
        self.work = work

    def run(self):
        self.work()
        self.signals.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Loading cfg
        self.token: str = load_config()['yandex_oauth_token']
        self.delay: int = int(load_config()['delay'])
        self.show_button: bool = True if load_config()['show_button'].lower() == "true" else False

        # Set values to UI
        self.findChild(QLineEdit, 'token_input').setText(self.token)
        self.findChild(QSlider, "delay_slider").setValue(self.delay)
        self.findChild(QCheckBox, "checkBox").setChecked(self.show_button)
        self.findChild(QLabel, 'status_label').setText("ОК")

        self.RPC = Presence('980573087168876594', pipe=0)

        # Connecting to Yandex API
        try:
            self.client = Client(self.token).init()
        except Exception as er:
            print(str(er))
            self.findChild(QLabel, 'status_label').setText("Ошибка API Yandex.Music")

        # Connecting to Discord RPC
        self.connect_rpc()

        # Main update loop
        loop_worker = Worker(self.update_loop)
        QThreadPool.globalInstance().start(loop_worker)

    @staticmethod
    def open_gh_link():
        webbrowser.open("https://github.com/waitstop/yandex_music_rpc")

    @staticmethod
    def open_help():
        webbrowser.open("https://yandex-music.readthedocs.io/en/main/token.html")

    def slider_changed_value(self, value: int):
        self.delay = value
        self.findChild(QLabel, 'delay_label').setText(f'{value} сек.')

    def handle_save_btn(self):
        worker = Worker(self.save_update)
        QThreadPool.globalInstance().start(worker)

    def handle_checkbox(self, state: int):
        self.show_button = False if state == 0 else True

    def save_update(self):
        self.token = self.findChild(QLineEdit, "token_input").text()
        self.delay = self.findChild(QSlider, "delay_slider").value()
        self.show_button = self.findChild(QCheckBox, "checkBox").isChecked()

        set_config(self.token, {"delay": self.delay, "show_button": self.show_button})

        try:
            self.client = Client(self.token).init()
            self.update_rpc()
            self.findChild(QLabel, 'status_label').setText("ОК")
            time.sleep(self.delay)
        except YandexMusicError:
            self.findChild(QLabel, 'status_label').setText("Ошибка API Yandex.Music")
        except PyPresenceException:
            self.findChild(QLabel, 'status_label').setText("Ошибка RPC")
        except Exception:
            self.findChild(QLabel, 'status_label').setText("Неизвестная ошибка")

    def get_data(self) -> dict | Exception:
        try:
            queues = self.client.queues_list()
            last_queue = self.client.queue(queues[0].id)
            self.findChild(QLabel, 'status_label').setText("ОК")
        except Exception as er:
            self.findChild(QLabel, 'status_label').setText("Ошибка получения данных с Яндекс")
            return er
        last_track_id = last_queue.get_current_track()
        last_track = last_track_id.fetch_track()
        artists = ', '.join(last_track.artists_name())
        link = f'https://music.yandex.ru/album/{last_track_id.album_id}/track/{last_track_id.track_id}'
        title = last_track.title
        cover = last_track.get_cover_url()
        data = {'state': artists, 'details': title, 'large_image': cover, 'small_image': 'logo'}
        if self.show_button:
            data = {**data, 'buttons': [{"label": "Open in Yandex.Music", "url": link}]}
        return data

    def update_rpc(self) -> Exception | None:
        try:
            self.client = Client(self.token).init()
            self.RPC.update(**self.get_data())
            self.findChild(QLabel, 'status_label').setText("ОК")
        except NotFoundError as er:
            self.RPC.clear()
            self.findChild(QLabel, 'status_label').setText("Трек не найден")
            return er
        except YandexMusicError:
            self.findChild(QLabel, 'status_label').setText("Ошибка API Yandex.Music")
        except PyPresenceException as er:
            print(str(er))
            self.findChild(QLabel, 'status_label').setText("Ошибка RPC")
            return er
        except Exception as er:
            self.findChild(QLabel, 'status_label').setText("Неизвестная ошибка")
            return er

    def update_loop(self):
        while True:
            self.update_rpc()
            time.sleep(self.delay)

    def connect_rpc(self) -> Exception | None:
        try:
            self.RPC.connect()
            self.findChild(QLabel, 'status_label').setText("ОК")
        except PyPresenceException as er:
            self.findChild(QLabel, 'status_label').setText("Ошибка RPC")
            return er


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

    print("test")
