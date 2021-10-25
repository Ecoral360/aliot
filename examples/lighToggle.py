from aliot import alive_iot as iot
import time

projectId = '73f799b7-1019-4f8e-8205-872cf1fac1ff'

iot.ObjConnecteAlive.set_url("ws://localhost:8881")
my_iot = iot.ObjConnecteAlive(key="9df35697-c76a-428d-bce6-7b74e375202d")


@my_iot.on_recv(id_protocol=1)
def activateLight(value):
    print("ON")

@my_iot.on_recv(id_protocol=20)
def activateLight(value):
    print("OFF")

lightIsOn = False
@my_iot.on_recv(id_protocol=30)
def activateLight(value):
    global lightIsOn
    if lightIsOn:
      print("OFF")
      lightIsOn = False
      my_iot.send(projectId, 'toggleButton', 'Light is off')
    else:
      print("ON")
      lightIsOn = True
      my_iot.send(projectId, 'toggleButton', 'Light is on')

my_iot.begin()
