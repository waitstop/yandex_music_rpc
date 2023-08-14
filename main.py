import threading
import webbrowser
from tkinter import IntVar, StringVar

import customtkinter as ctk
from configparser import ConfigParser
import pystray
from PIL import Image
from os.path import exists

from pypresence import Presence

import handlers.yandex as yandex
from handlers.rpc import update_rpc


class TokenInput(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.token = StringVar(master, config["secret"]["yandex_oauth_token"])
        self.grid_columnconfigure(0, weight=1)
        self.input_label = ctk.CTkLabel(self,
                                        text="Яндекс.Музыка OAuth Токен",
                                        font=("Roboto Condensed", 16)
                                        )
        self.input_label.grid(row=0, column=0, pady=[15, 5], padx=10, sticky="w")

        self.input_help = ctk.CTkButton(self,
                                        text="Помощь",
                                        image=ctk.CTkImage(
                                            dark_image=Image.open("./img/help_icon.png"),
                                            size=(16, 16)),
                                        command=self.handle_help
                                        )
        self.input_help.grid(row=0, column=0, pady=[15, 5], padx=10, sticky="e")

        self.token_input = ctk.CTkEntry(self, border_width=0, textvariable=self.token, show="*")
        self.token_input.grid(row=1, column=0, sticky="ew", pady=15, padx=10)

    @staticmethod
    def handle_help():
        webbrowser.open(
            "https://github.com/waitstop/yandex_music_rpc#%D0%BA%D0%B0%D0%BA-%D0%BF%D0%BE%D0%BB%D1%83%D1%87%D0%B8%D1%82%D1%8C-%D1%82%D0%BE%D0%BA%D0%B5%D0%BD"
        )


class DelaySlider(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.delay = IntVar(master, int(config["settings"]["delay"]))

        self.grid_columnconfigure(0, weight=1)
        self.slider_label = ctk.CTkLabel(self,
                                         text="Задержка обновления треков",
                                         font=("Roboto Condensed", 16)
                                         )
        self.slider_label.grid(row=0, column=0, pady=[15, 5], padx=10, sticky="w")

        self.delay_slider = ctk.CTkSlider(self, from_=5, to=30, number_of_steps=5, command=self.slider_callback)
        self.delay_slider.grid(row=1, column=0, sticky="ew", pady=15, padx=10)

        self.delay_slider.set(int(self.delay.get()))

        self.slider_value_label = ctk.CTkLabel(self,
                                               textvariable=self.delay,
                                               font=("Roboto Condensed", 16)
                                               )
        self.slider_value_label.grid(row=0, column=0, pady=[15, 5], padx=10, sticky="e")

    def slider_callback(self, value):
        self.delay.set(int(value))


class StatusLabel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.status = StringVar(master, "OK")
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self,
                                  text="СТАТУС: ",
                                  font=("Roboto Condensed", 16)
                                  )
        self.statusLabel = ctk.CTkLabel(self,
                                        textvariable=self.status,
                                        font=("Roboto Condensed", 16, "bold")
                                        )
        self.label.grid(row=0, column=0, sticky="e", pady=5, padx=10)
        self.statusLabel.grid(row=0, column=1, sticky="w", pady=5, padx=10)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("./themes/NightTrain.json")
        self.iconbitmap("./img/yandex_icon.ico")

        self.title("Yandex.Music RPC")
        self.resizable(False, False)
        self.geometry("500x500")
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self,
                                  text="Yandex.Music Discord Integration",
                                  font=("Roboto Condensed", 20)
                                  )
        self.label.grid(row=0, column=0, sticky="ew", padx=25, pady=[25, 0])

        self.token_input = TokenInput(self)
        self.token_input.grid(row=1, column=0, sticky="ew", padx=25, pady=[25, 0])

        self.delay_slider = DelaySlider(self)
        self.delay_slider.grid(row=2, column=0, sticky="ew", padx=25, pady=[25, 0])

        self.save_btn = ctk.CTkButton(self,
                                      text="Обновить / Сохранить",
                                      font=("Roboto Condensed", 20),
                                      command=self.save_callback
                                      )
        self.save_btn.grid(row=3, column=0, sticky="ew", padx=25, pady=[25, 0], ipady=5)

        self.status_label = StatusLabel(self)
        self.status_label.grid(row=4, column=0, padx=25, pady=[25, 0])

    def save_callback(self):
        delay = self.delay_slider.delay.get()
        token = self.token_input.token.get()
        config["secret"]["yandex_oauth_token"] = token
        config["settings"]["delay"] = str(delay)
        with open("config.ini", "w") as file:
            config.write(file)


def on_window_close():
    app.withdraw()


def on_exit():
    icon.stop()
    app.quit()


def on_open():
    icon.update_menu()
    app.deiconify()


def update():
    data = yandex.get_data(config["secret"]["yandex_oauth_token"])
    app.status_label.status.set("ОК")
    update_rpc(data, rpc, app.status_label.status)
    app.after(int(config["settings"]["delay"])*1000, update)


def start_thread():
    thread = threading.Thread(target=update)
    thread.start()


if __name__ == '__main__':
    config = ConfigParser()
    if exists("config.ini"):
        config.read('config.ini')
    else:
        config["secret"] = {"yandex_oauth_token": ""}
        config["settings"] = {
            "delay": "5"
        }
        with open("config.ini", "x") as f:
            config.write(f)

    app = App()

    image = Image.open("./img/yandex_icon.png")
    menu = (
        pystray.MenuItem('Yandex.Music RPC', on_open, default=True, visible=False),
        pystray.MenuItem('Выход', on_exit)
    )
    icon = pystray.Icon("name", image, "Yandex.Music RPC", menu)

    icon.run_detached()

    app.protocol('WM_DELETE_WINDOW', on_window_close)

    rpc = Presence('980573087168876594', pipe=0)
    rpc.connect()
    start_thread()

    app.mainloop()

