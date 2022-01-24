from typing import Union, List

import msgpack
from threading import Thread
import schedule
import json, requests, time, websocket
from aliot.aliot.utils import Style

style_print = Style.style_print


class URLNotDefinedException(Exception):
    """Exception raised when a new ObjConnecte instance is created and __URL is not defined"""


_no_value = object()


class ObjConnecteAlive:
    __URL = ''

    # nb de request max par interval (en ms)
    __bottleneck_capacity = {"max_send": 30,
                             "interval": 500, "sleep_interval": 0.2}

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
        self.__protocols = {}
        self.__listeners = {}
        self.__broadcast_listeners = {}
        self.__running = False
        self.ws: websocket.WebSocketApp = None
        self.__main_loop = None
        self.__repeats = 0
        self.__last_freeze = 0

    @property
    def protocols(self):
        return self.__protocols.copy()

    @property
    def listeners(self):
        return self.__listeners.copy()

    @property
    def broadcast_listeners(self):
        return self.__broadcast_listeners.copy()

    @property
    def connected(self):
        return self.__running

    @connected.setter
    def connected(self, value: bool):
        self.__running = value
        if not value:
            self.ws.close()

    def on_recv(self, action_id: int, log_reception: bool = True, send_result: bool = False):
        def inner(func):
            def wrapper(*args, **kwargs):
                if log_reception:
                    print(f"The protocol: {action_id!r} was called with the arguments: "
                          f"{args}")
                result = func(*args, **kwargs)
                if (send_result):
                    self.send(result)

            self.__protocols[action_id] = wrapper
            return wrapper

        return inner

    def listen(self, projectId: str, fields: List[str]):
        def inner(func):
            def wrapper(fields: dict):
                result = func(fields)

            if projectId not in self.__listeners:
                self.__listeners[projectId] = []
            self.__listeners[projectId].append({
                'func': wrapper,
                'fields': fields
            })
            return wrapper

        return inner

    def listen_broadcast(self, projectId: str):
        def inner(func):
            def wrapper(fields: dict):
                result = func(fields)

            if projectId not in self.__listeners:
                self.__broadcast_listeners[projectId] = []
            self.__broadcast_listeners[projectId] = wrapper
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

    def send_update(self, projectId: str, id: str,  value):
        self.sendEvent('send_update', {
                       'projectId': projectId, 'id': id, 'value': value
                       })

    def broadcast(self, projectId: str, data: dict):
        self.sendEvent('broadcast', {
                       'projectId': projectId, 'data': data
                       })

    def update(self, projectId: str, fields: dict):
        self.sendEvent('update', {
                       'projectId': projectId,
                       'fields': fields,
                       })

    def get_doc(self, projectId):
        res = requests.post('http://localhost:8000/api/iot/aliot/getDoc', { 'projectId': projectId, 'objectId': self.__key})
        if res.status_code == 201:
            return json.loads(res.text) if res.text else None
        elif res.status_code == 403:
            style_print(f"&c[ERROR] while getting the document, request was Forbidden due to permission errors or project missing.")
        elif res.status_code == 500:
            style_print(f"&c[ERROR] while getting the document, something went wrong with the ALIVECode's servers, please try again.")
        else:
            style_print(f"&c[ERROR UNKNOWN] while getting the document, please try again.")


    def get_field(self, projectId, field: str):
        res = requests.post('http://localhost:8000/api/iot/aliot/getField', { 'projectId': projectId, 'objectId': self.__key, 'field': field})
        if res.status_code == 201:
            return json.loads(res.text) if res.text else None
        elif res.status_code == 403:
            style_print(f"&c[ERROR] while getting the field {field}, request was Forbidden due to permission errors or project missing.")
        elif res.status_code == 500:
            style_print(f"&c[ERROR] while getting the field ${field}, something went wrong with the ALIVECode's servers, please try again.")
        else:
            style_print(f"&c[ERROR UNKNOWN] while getting the field {field}, please try again.")


    def send_route(self, routePath: str, data: dict):
        projectId, routePath = routePath.split("/")
        self.sendEvent('send_route', {
            'projectId': projectId,
            'routePath': routePath,
            'data': data
        })

    def sendEvent(self, event: str, data: dict):

        """
        if self.__last_freeze and time.time() - self.__last_freeze > self.__bottleneck_capacity["interval"]:
            self.__repeats = 0
            self.__last_freeze = None
            style_print(f"&2[RESUMING]")


        if self.__repeats > self.__bottleneck_capacity["max_send"]:
            style_print(f"&6[WARNING] You are sending more than {self.__bottleneck_capacity['max_send']} requests in under {self.__bottleneck_capacity['interval']}ms. Sending of data slowed down.")
            
            if self.__last_freeze is None:
                self.__last_freeze = time.time()

            time.sleep(self.__bottleneck_capacity["sleep_interval"])

        """
        if self.connected:
            self.ws.send(json.dumps({'event': event, 'data': data}, default=str))
            self.__repeats += 1

    def execute_protocol(self, msg):
        must_have_keys = "id", "value"
        if not all(key in msg for key in must_have_keys):
            print("the message received does not have a valid structure")
            return

        msg_id = msg["id"]
        protocol = self.protocols.get(msg_id)

        if protocol is None:
            if self.connected:
                self.connected = False
            style_print(
                f"&c[ERROR] the protocol with the id {msg_id!r} is not implemented")

            # magic of python
            style_print("&l[CLOSED]")
        else:
            protocol(msg["value"])

    def execute_listen(self, projectId: str, fields: dict):
        projectListeners = self.listeners.get(projectId)
        if projectListeners:
            for listener in projectListeners:
                fieldsToReturn = dict(filter(lambda el: el[0] in listener['fields'], fields.items()))
                if len(fieldsToReturn) > 0:
                    listener["func"](fieldsToReturn)


    def execute_broadcast(self, projectId: str, data: dict):
        listener = self.broadcast_listeners.get(projectId)
        if listener:
            listener(data)


    def on_message(self, ws, message):
        msg = json.loads(message)

        if msg['event'] == "action":
            if isinstance(msg['data'], list):
                for m in msg['data']:
                    self.execute_protocol(m)
            else:
                self.execute_protocol(msg)
        elif msg['event'] == "listen":
            self.execute_listen(msg['data']['projectId'], msg['data']['fields'])
        elif msg['event'] == 'broadcast':
            self.execute_broadcast(msg['data']['projectId'], msg['data']['data'])
        

    def on_error(self, ws, error):
        style_print(f"&c[ERROR]{error!r}")
        if isinstance(error, ConnectionResetError):
            style_print("&eWARNING: if you didn't see the '&a[CONNECTED]'&e, "
                        "message verify that you are using the right key")

    def on_close(self, ws):
        self.__running = False
        style_print("&l[CLOSED]")

    def on_open(self, ws):
        # Register IoTObject on ALIVEcode
        self.ws.send(json.dumps(
            {'event': 'connect_object', 'data': {'id': self.__key}}))

        if self.__main_loop is None:
            self.ws.close()
            raise NotImplementedError("You must define a main loop")

        Thread(target=self.__main_loop, daemon=True).start()

        time.sleep(2)

        # Register listeners on ALIVEcode
        for projectId, projectListeners in self.listeners.items():
            fields = sorted(set([f for listener in projectListeners for f in listener['fields']]))
            self.ws.send(json.dumps(
                {'event': 'listen', 'data': {'projectId': projectId, 'fields': fields}}))
        
        time.sleep(0.5)
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
