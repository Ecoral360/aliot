from aliot import alive_iot as iot
import time

projectId = '7ae63621-b0f9-4996-a742-6f9bdce715b4'

iot.ObjConnecteAlive.set_url("ws://localhost:8881")
my_iot = iot.ObjConnecteAlive(key="67b30495-afe7-4638-896e-ebec02fa5562")

@my_iot.on_recv(1)
def allumerLumiere(data):
  print(data)
  print("LIGHT ON")

@my_iot.main_loop()
def main():
  pass
  #my_iot.send(projectId, 'logs', i)


my_iot.begin()
