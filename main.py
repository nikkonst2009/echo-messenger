from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from kivy.clock import Clock
import socket
from threading import Thread

Builder.load_string('''
<TabbedPanel>:
    do_default_tab: False
    
    TabbedPanelItem:
        text: 'Подключение'
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: 'Подключение к серверу'
            BoxLayout:
                orientation: 'horizontal'
                TextInput:
                    id: ip_input
                    hint_text: 'Введите IP сервера'
                TextInput:
                    id: port_input
                    hint_text: 'Введите порт'
            BoxLayout:
                orientation: 'horizontal'
                Button:
                    id: connect_button
                    text: 'Подключиться'
                    on_press: app.connect_to_server(ip_input.text, int(port_input.text))
                Button:
                    id: disconnect_button
                    text: 'Отключиться'
                    on_press: app.disconnect()
            Label:
                id: status
                text: 'Статус: Ожидание подключения.'

    TabbedPanelItem:
        text: 'Чат'
        BoxLayout:
            orientation: 'vertical'
            ScrollView:
                TextInput:
                    id: messages_list
                    text: 'Здесь будут все сообщения\\n'
                    readonly: True
                    background_color: (0.9, 0.9, 0.9, 1)
                    font_size: max(self.height * 0.25, 50)
                    multiline: True
            TextInput:
                id: username_input
                hint_text: 'Ваше имя пользователя'
                size_hint_y: 0.1
                font_size: self.height * 0.5
            TextInput:
                id: message_input
                hint_text: 'Введите сообщение'
                size_hint_y: 0.1
                font_size: self.height * 0.5
            Button:
                text: 'Отправить'
                size_hint_y: 0.1
                font_size: self.height * 0.5
                on_press: app.send_message(f"{username_input.text}: {message_input.text}")
''')

class SocketApp(App):
    def build(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.connected = False
        self.messages_list = ""
        return TabbedPanel()

    def connect_to_server(self, ip, port):
        try:
            # Обращаемся с сокетами, как с файлами!
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(2)
            self.root.ids.status.text = f"Статус: Подключение к серверу..."
            self.s.connect((ip, port))
            self.root.ids.status.text = f"Статус: Подключено к {ip}:{port}"
            
            response = self.s.recv(1024).decode()
            self.root.ids.status.text = f"Статус: Ответ от сервера: {response}"

            self.connected = True
            app.update_messages_list()
        except Exception as e:
            self.root.ids.status.text = f"Статус: Ошибка.\n{str(e)}. Попробуйте переподключиться"
            self.connected = False

    def send_message(self, message):
        try:
            self.s.sendall(message.encode("UTF-8"))
            self.root.ids.message_input.text = ''
            self.root.ids.status.text = f"Статус: Отправлено сообщение: {message}"
            app.update_messages_list()
        except Exception as e:
            self.root.ids.status.text = f"Статус: Ошибка: {str(e)}. Попробуйте переподключиться"
            self.connected = False

    def disconnect(self):
        self.running = False
        self.s.close()
        self.root.ids.status.text = f"Статус: Отключено от сети. Ожидание подключения"
        self.connected = False

    def update_messages_list(self):
        try:
            if not self.connected:
                return

            Thread(daemon=True, target=lambda: self.get_messages_list()).start()

            self.root.ids.messages_list.text = self.messages_list

        except socket.timeout:
            return
        except ConnectionResetError:
            self.connected = False
            self.root.ids.status.text = "Статус: Соединение разорвано"
        except Exception as e:
            print(f"Ошибка при получении сообщений: {str(e)}")
            self.connected = False
            self.root.ids.status.text = f"Статус: Ошибка: {str(e)}"

    def on_stop(self):
        self.running = False
        self.s.close()

    def get_messages_list(self):
        # Получаем данные от сервера
            data = self.s.recv(1024)
            if not data:
                self.messages_list = "Не удалось обновить список сообщений"
            else:
                self.messages_list = data.decode()

def update_messages_list(dt):
    app.update_messages_list()

if __name__ == '__main__':
    app = SocketApp()
    Clock.schedule_interval(update_messages_list, 1)
    app.run()
