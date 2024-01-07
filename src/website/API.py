import logging, flask, flask_socketio, typing, datetime, time, asyncio, sys
sys.dont_write_bytecode = True
import src.connector as con
from engineio.async_drivers import threading

if True:
    from src.system.colors import C, CNone

class MainWebsite:
    def __init__(self) -> None:
        # initializitamo flask in socketio
        self.app = flask.Flask(__name__)
        self.socketio = flask_socketio.SocketIO(self.app, namespace="/")
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        # beremo iz shared podatkov
        self.sandbox: bool = con.read_shared("sandbox")
        self.c: C | CNone = con.read_shared("colors")
        self.config: dict = con.read_shared("config")
    	
        # datetime za sandbox
        self.last_time: datetime.date = datetime.datetime.now()

        # route na root (/) ki naloži html scripto
        @self.app.route("/")
        def main_route() -> str:
            return flask.render_template("main.html")
        
        # socket connect
        @self.socketio.on("connect")
        def connect() -> None:
            print("SOCKET >> New client connected to the tracker!")
        
        # socket disconnect
        @self.socketio.on("disconnect")
        def disconnect() -> None:
            print("SOCKET >> Client disconnected from the tracker!")

        # na socket error, zapiše napako
        @self.socketio.on_error_default
        def default_error_handler(error) -> None:
            print(f"SOCKET >> Error: {type(error).__name__}: {error}")

    # funkcija ki nardi update preko socket povezave
    def make_update(self, action: typing.Literal["sell_event", "buy_event", "update_price"], y_price: int | float, x_time: datetime.datetime) -> None:
        try:
            if not self.sandbox:
                # normalen emit, brez sandbox moda
                try:
                    self.socketio.emit(action, {"y": y_price, "x" : int(time.mktime(x_time.timetuple())) * 1000}, namespace='/')
                except Exception as error:
                    print(f"ERROR @MainWebsite.make_update: {type(error).__name__}: {error}")
            
            else:
                # ce je posodobitev cene, zamaknemo za x sekund
                if action == "update_price":
                    self.last_time = self.last_time + datetime.timedelta(seconds=self.config["general"]["sandbox"]["interval"])
                    self.socketio.emit(action, {"y": y_price, "x" : int(time.mktime(self.last_time.timetuple())) * 1000}, namespace='/')
                
                # drugi eventi pa ostanjeo
                else:
                    self.socketio.emit(action, {"y": y_price, "x" : int(time.mktime(self.last_time.timetuple())) * 1000}, namespace='/')
    
        except Exception as error:
            print(f"{self.c.Red}ERROR{self.c.R} @MainWebsite.make_update: {type(error).__name__}: {error}")

    # funkcijas ki zažene celoten web server v async loopu
    def start(self) -> None:
        #kill logger
        log: logging.Logger = logging.getLogger("werkzeug")
        log.setLevel(logging.FATAL)

        # blocking zažetek
        self.loop.run_until_complete(self.socketio.run(self.app, host=self.config["local-tracking"]["host"], port=self.config["local-tracking"]["port"], debug=False, use_reloader=False))
        

        



