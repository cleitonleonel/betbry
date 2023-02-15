import json
import requests
from threading import Thread
from websocket import WebSocketApp, \
    enableTrace
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL_BASE = 'https://www.betbry.com'
WSS_BASE = 'wss://www.betbry.com'

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504, 104],
    allowed_methods=["HEAD", "POST", "PUT", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)


result_dict = []
created = None


class Browser(object):

    def __init__(self):
        self.response = None
        self.headers = None
        self.session = requests.Session()

    def set_headers(self, headers=None):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.06"
        }
        if headers:
            for key, value in headers.items():
                self.headers[key] = value

    def get_headers(self):
        return self.headers

    def send_request(self, method, url, **kwargs):
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        return self.session.request(method, url, **kwargs)


class BetBryClientAPI(Browser):

    def __init__(self):
        super().__init__()
        self.ws = None
        self.message_recv = None
        self.message_recv_confirm = None
        self.is_connected = False
        self.preview = False
        self.trace_route = False

    def connect(self):
        enableTrace(self.trace_route)
        self.is_connected = True
        headers = self.get_headers()
        self.ws = WebSocketApp(f"{WSS_BASE}/listen?module=RowDouble",
                               header=headers,
                               on_open=self.on_open,
                               on_message=self.on_message,
                               on_pong=self.on_pong,
                               on_close=self.on_close,
                               )
        ws_thread = Thread(target=self.run, args=[])
        ws_thread.daemon = True
        ws_thread.start()

    def run(self):
        self.ws.run_forever(origin=URL_BASE,
                            host=URL_BASE.split("//")[1],
                            reconnect=2
                            )

    def send_message(self, message):
        self.ws.send(message)

    def on_message(self, ws, message):
        global result_dict
        global created
        if "FINISHED" in message:
            json_data = json.loads(json.loads(message).get("data"))
            if created != json_data.get("gameData")["data"]["term"]["created"]:
                result_data = {
                    "number": json_data.get("gameData")["data"]["term"]["number"],
                    "color": json_data.get("gameData")["data"]["term"]["color"],
                    "created": json_data.get("gameData")["data"]["term"]["created"]
                }
                if self.preview:
                    print(
                        f'COR: {json_data.get("gameData")["data"]["term"]["color"]}',
                        f'NÚMERO: {json_data.get("gameData")["data"]["term"]["number"]}'
                    )
                result_dict.append(result_data)

    def on_open(self, ws):
        message = '{"data":"switch-module","modules":["6O9QrLTu","rowDouble"]}'
        self.send_message(message)

    def on_close(self, ws, sts, msg):
        print(f"###CLOSED###")

    def get_status(self):
        if self.message_recv:
            return self.message_recv
        return self.message_recv

    def close(self):
        self.is_connected = False
        self.ws.close()

    @staticmethod
    def on_error(ws, error):
        return error

    @staticmethod
    def on_pong(ws, msg):
        ws.send("3")
