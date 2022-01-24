### ALIOT!

#### What is Aliot?

Before everything else, aliot is a fancy websocket written in python that aims to facilitate iot focused
exchanges between a server and a client

#### Installation

1. create a python virtual environment
    - run the command `py -m venv venv`
2. add aliot in a folder in your project (replace $FOLDER in the command by the name of your folder)
3. run the command `pip install ./$FOLDER`

#### Creating my first Aliot program

1. create an object ObjConnecte

#### Creating an endpoint (or, like we call it here, a protocol)

1. Create a function that takes some parameters

    ```py
    # my function will take money ($) and give cookies for every 2$ received
    def give_cookies_for_money(money: int):
        return {"cookies": money // 2}
    ```

2. Register your function as a protocol by decorating it with the `on_recv` decorator
   in your ObjConnecte that you created for your project and pass the id of your protocol in the
   argument of the decorator

    ```py
    # here, I chose that my function will be protocol 34
    @my_iot.on_recv(action_id=34)
    def give_cookies_for_money(money: int):
        return {"cookies": money // 2}
    ```

3. As of now, my function `give_cookies_for_money` doesn't return anything to the server, if I want to
   send back my cookies, I have to ways:

    1. use the function `my_iot.send()`

    ```py
    @my_iot.on_recv(action_id=34)
    def give_cookies_for_money(money: int):
        my_iot.send({"cookies": money // 2})
    ```

    2. set the convenience parameter `send_result` to True in the decorator

    ```py
    @my_iot.on_recv(action_id=34, send_result=True)
    def give_cookies_for_money(money: int):
        return {"cookies": money // 2}
    ```

    3. You're all set! Now repeat and enjoy! 🎉
