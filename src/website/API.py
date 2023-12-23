import logging, sys, flask, flask_socketio, typing, datetime, time
sys.dont_write_bytecode = True
import src.connector as con

class MainWebsite:
    def __init__(self) -> None:
        # začnemo flask webserver pa sockets
        self.app = flask.Flask(__name__)
        self.socketio = flask_socketio.SocketIO(self.app)

    # naredimo route za webserver
    def setup_routes(self, sandbox: bool) -> None:
        @self.app.route("/")
        def main_route() -> str:
            return flask.render_template("sandbox.html") if sandbox else flask.render_template("main.html")
        
        @self.socketio.on("connect")
        def connect() -> None:
            pass
        
        @self.socketio.on("disconnect")
        def disconnect() -> None:
            pass
    
    # funkcija k pošilja update
    def make_update(self, action: typing.Literal["sell_event", "buy_event", "update_data"], y_price: int | float, x_time: datetime.datetime) -> None:
        try:
            self.socketio.emit(action, {"y": y_price, "x" : int(time.mktime(x_time.timetuple())) * 1000}, namespace='/')
        except Exception as error:
            print(f"ERROR @MainWebsite.make_update: {type(error).__name__}: {error}")

    # start funkcija
    def start(self) -> None:
        config: dict = con.read_shared("config")
        self.setup_routes(config["general"]["sandbox"])
        
        #kill logger
        log: logging.Logger = logging.getLogger("werkzeug")
        log.setLevel(logging.FATAL)

        try:
            self.socketio.run(self.app, host=config["local-tracking"]["host"], port=config["local-tracking"]["port"], debug=False)
        except Exception as error:
            print(error)



