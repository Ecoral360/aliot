from typing import Union

import msgpack
from threading import Thread
import schedule
import json
import time
import websocket
from aliot.utils import Style

style_print = Style.style_print


class URLNotDefinedException(Exception):
    """Exception raised when a new ObjConnecte instance is created and __URL is not defined"""


_no_value = object()


class ObjConnecte:
    __URL = ''

    # nb de request max par interval (en ms)
    __bottleneck_capacity = {"max send": 10,
                             "interval": 1000, "sleep interval": 0.5}

    @classmethod
    def set_url(cls, url: str):
        cls.__URL = url

    def __new__(cls, *args, **kwargs):
        if not cls.__URL:
            raise URLNotDefinedException(
                "You must define a URL before creating an ObjConnecte, call ObjConnecte.set_url(url) with your url before creating any instance of that class"
            )
        return super().__new__(cls)

    def __init__(self, key: str):
        if not isinstance(key, str):
            raise ValueError("the value of id_ must be a string")
        self.__key = key
        self.__URL %= key
        self.__protocols = {}
        self.__running = False
        self.ws: websocket.WebSocketApp = None
        self.__main_loop = None
        self.__repeats = 0
        self.__last_send = 0

    @property
    def protocols(self):
        return self.__protocols.copy()

    @property
    def connected(self):
        return self.__running

    @connected.setter
    def connected(self, value: bool):
        self.__running = value
        if not value:
            self.ws.close()

    def on_recv(self, id_protocol: int, log_reception: bool = True, send_result: bool = False):
        def inner(func):
            def wrapper(*args, **kwargs):
                if log_reception:
                    print(f"The protocol: {id_protocol!r} was called with the arguments: "
                          f"{args}")
                result = func(*args, **kwargs)
                if (send_result):
                    self.send(result)

            self.__protocols[id_protocol] = wrapper
            return wrapper

        return inner

    def main_loop(self, repetitions=None):
        def inner(main_loop_func):
            def wrapper():
                while not self.connected:
                    pass
                if repetitions is not None:
                    for _ in range(repetitions):
                        if not self.connected:
                            break
                        main_loop_func()
                else:
                    while self.connected:
                        main_loop_func()

            self.__main_loop = wrapper
            return wrapper

        return inner

    def send(self, data: dict):
        """
        TODO refactor the incomming data to the format understood by the server
        """

        if time.time() - self.__last_send > self.__bottleneck_capacity["interval"]:
            self.__repeats = 0

        if self.__repeats > self.__bottleneck_capacity["max send"]:
            time.sleep(self.__bottleneck_capacity["sleep interval"])

        if self.connected:
            self.ws.send(json.dumps(data))
            self.__repeats += 1
            self.__last_send = time.time()

    def execute_protocol(self, msg):
        must_have_keys = "protocol_id", "params"

        if not all(key in msg for key in must_have_keys):
            print("the message received does not have a valid structure")
            return

        msg_protocol_id = msg["protocol_id"]
        protocol = self.protocols.get(msg_protocol_id)

        if protocol is None:
            if self.connected:
                self.connected = False
            style_print(
                f"&c[ERROR] the protocol with the id {msg_protocol_id!r} is not implemented")

            # magic of python
            style_print("&l[CLOSED]")
        else:
            protocol(*msg["params"])

    def on_message(self, ws, message):
        msgs = json.loads(message)
        if isinstance(msgs, list):
            for msg in msgs:
                self.execute_protocol(msg)
        else:
            self.execute_protocol(msgs)

    def on_error(self, ws, error):
        style_print(f"&c[ERROR]{error!r}")
        if isinstance(error, ConnectionResetError):
            style_print("&eWARNING: if you didn't see the '&a[CONNECTED]'&e, "
                        "message verify that you are using the right key")

    def on_close(self, ws):
        self.__running = False
        style_print("&l[CLOSED]")

    def on_open(self, ws):
        """
        TODO trouver quoi mettre ici
        """
        if self.__main_loop is None:
            self.ws.close()
            raise NotImplementedError("You must define a main loop")

        Thread(target=self.__main_loop, daemon=True).start()

        self.__running = True
        style_print("&a[CONNECTED]")

    def begin(self, enable_trace: bool = False):
        style_print("&9[CONNECTING]...")
        websocket.enableTrace(enable_trace)
        self.ws = websocket.WebSocketApp(self.__URL,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()

    def __repr__(self):
        return f"connection_key: {self.__key}"
