import sys, ccxt, math, typing
sys.dont_write_bytecode = True
import src.connector as con

if typing.TYPE_CHECKING:
    from ccxt.base.types import Ticker

class Updater:
    def __init__(self):
        pass
    

class LogicLink:
    def __init__(self) -> None:
        #self.local_tracking: con.MainWebsite = con.read_shared("website")
        pass
    
    async def run(self, data: str | dict[str, str | float | dict] | Ticker) -> None:
        # price update
        if local_tracking := con.read_shared("website"):
            local_tracking.make_update(action="update_data", price=data.get("info").get("lastPrice"))
