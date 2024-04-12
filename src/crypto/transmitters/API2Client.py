import sys, ccxt, typing, asyncio
sys.dont_write_bytecode = True
import src.connector as con
from src.crypto.logic import LogicLink
from ccxt.base.types import Ticker


class PriceRequester:
    def __init__(self, exchange: ccxt.binance) -> None:
        self.exchange: ccxt.binance = exchange
        self.infLoop: bool = True
        
    def ccxt_requester(self) -> Ticker | None:
        try:
            # returnamo TICKER (podatke) direktno iz BinanceAPI z ccxt lib
            return self.exchange.fetch_ticker(con.read_shared("config")["general"]["symbol"])
        except Exception as error:
            print(f"API2Client >> CCXT request failed. {type(error).__name__}: {error}")
            return
     
    async def start(self) -> None:
        # asyncio loop za taske
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        
        # glavni inf loop, ki je lahko ustavljen z self.infLoop = False
        while self.infLoop:
            if response := self.ccxt_requester():
                loop.create_task(LogicLink().run(response))

            # spimo kolkr je določen interval
            await asyncio.sleep(con.read_shared("interval"))

        # na self.infLoop = False, returnamo False in končamo TASK
        else:
            return False
