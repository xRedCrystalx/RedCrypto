import ccxt, sys, asyncio, typing
sys.dont_write_bytecode = True
import src.connector as con
from src.crypto.transmitters.API2Client import PriceRequester
from src.crypto.transmitters.Client2API import Market
from src.crypto.transmitters.sandbox import RequesterSimulator, MarketSimulator


class CryptoMain:
    def __init__(self) -> None:
        self.c: con.C | con.CNone = con.read_shared("colors")
        self.config: dict = con.read_shared("config")
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.crypto_task: asyncio.Task = None
    
    async def runner(self) -> None:
        # če je sandbox = True, zaženemo sandbox mode
        if con.read_shared("config")["general"]["sandbox"]["status"]:
            print(f"{self.c.Gray}{"SANDBOX MODE IS ENABLED":-^45}{self.c.R}")
            
            # initializira requesterja in market ter ga shrani
            requester: RequesterSimulator = RequesterSimulator()
            con.write_shared("price_requester", requester)

            market: MarketSimulator = MarketSimulator()
            con.write_shared("market", market)

            # zažene requesterja v novem TASKu
            await requester.start()

        
        # drugače začnemo normalno
        else:
            self.binance = ccxt.binance({
                "enableRateLimit" : True,
                "apiKey" : self.config["binance"]["API-key"],
                "secret" : self.config["binance"]["API-secret"]
            })

            con.write_shared("binance", self.binance)
            
            # initializira requesterja in market ter ga shrani
            requester: PriceRequester = PriceRequester()
            con.write_shared("price_requester", requester)

            market: Market = Market()
            con.write_shared("market", market)
            
            # zažene requesterja v novem TASKu
            self.crypto_task: asyncio.Task = self.loop.create_task(requester.start())

        #await con.terminate()

    
    def start(self) -> None:
        asyncio.run(self.runner())

    def stop(self) -> None:
        if self.crypto_task:
            self.crypto_task.cancel()