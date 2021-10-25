from aliot import alive_iot as iot
import time

projectId = 'f436a155-05d1-4c77-9946-cf76b65e3463'

iot.ObjConnecteAlive.set_url("ws://localhost:8881")
my_iot = iot.ObjConnecteAlive(key="67b30495-afe7-4638-896e-ebec02fa5562")

i = 0;
@my_iot.main_loop(11)
def main():
  global i
  i += 100
  time.sleep(2)
  my_iot.send(projectId, 'logs', i)


my_iot.begin()
