import random, logging, sys, flask
sys.dont_write_bytecode = True

class API:
    #@app.route("/")
    def index() -> str:
        return flask.render_template("index.html")

    #@app.route("/get_data")
    def get_data() -> flask.Response:
        price: float = random.uniform(40000, 41000)
        return flask.jsonify(price=price)
    
    def start(self, host: str ="0.0.0.0", port: int = 1111, debug: bool = False) -> None:
        self.app = flask.Flask(__name__)
        log: logging.Logger = logging.getLogger("werkzeug")
        log.setLevel(logging.WARNING)
        self.app.run(host=host, port=port, debug=debug)
