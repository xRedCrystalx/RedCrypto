import ccxt, sys, asyncio
sys.dont_write_bytecode = True
import src.connector as con
from src.crypto.transmitters.API2Client import PriceRequester
from src.crypto.transmitters.sandbox import RequesterSimulator

class CryptoMain:
    def __init__(self) -> None:
        self.c: con.C | con.CNone = con.read_shared("colors")
        self.config: dict = con.read_shared("config")
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    
    
    async def runner(self) -> None:
        # če je sandbox = True, zaženemo sandbox mode
        if con.read_shared("config")["general"]["sandbox"]:
            print(f"{self.c.Gray}{"SANDBOX MODE IS ENABLED":-^45}{self.c.R}")
            
            # initializira requesterja in ga shrani
            requester: RequesterSimulator = RequesterSimulator()
            con.write_shared("price_requester", requester)
            
            # zažene requesterja v novem TASKu
            self.loop.create_task(requester.start())
        
        # drugače začnemo normalno
        else:
            self.binance = ccxt.binance({
                "enableRateLimit" : True,
                "apiKey" : self.config["binance"]["API-key"],
                "secret" : self.config["binance"]["API-secret"]
            })
            con.write_shared("binance", self.binance)
            
            # initializira requesterja in ga shrani
            requester: PriceRequester = PriceRequester()
            con.write_shared("price_requester", requester)
            
            # zažene requesterja v novem TASKu
            self.loop.create_task(requester.start())

        #await con.terminate()

    
    def start(self) -> None:
        asyncio.run(self.runner())