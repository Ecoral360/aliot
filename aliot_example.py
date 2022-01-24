from aliot import iot


# DEPRECATED


iot.ObjConnecte.set_url("ws://127.0.0.1/iot?id=%s")
my_iot = iot.ObjConnecte(key="c0f69a36-d0bd-42b8-9748-e018f29a4eeb")


@my_iot.on_recv(action_id=10)
def respond(*params):
    print(params)


@my_iot.on_recv(action_id=20)
def respond2(*params):
    print(params)


@my_iot.on_recv(action_id=69, send_result=True)
def changer_couleur(colour):
    return {"msg": f"wow, what a nice colour: {colour}"}


@my_iot.main_loop(repetitions=10)
def main():
    pass


my_iot.begin()
