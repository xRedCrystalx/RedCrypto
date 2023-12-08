import ccxt, sys, asyncio
sys.dont_write_bytecode = True
import src.connector as con

class CryptoMain:
    def __init__(self) -> None:
        self.c: con.C | con.CNone = con.read_shared("colors")
    
    async def runner(self) -> None:
        if con.read_shared("config")["general"]["sandbox"]:
            print(f"{self.c.Gray}{"SANDBOX MODE IS ENABLED":-^45}{self.c.R}")
            
        
        else:
            self.binance = ccxt.binance({
                "enableRateLimit" : True,
                "apiKey" : con.read_shared("config")["binance"]["API-key"],
                "secret" : con.read_shared("config")["binance"]["API-secret"]
            })
        
        await con.terminate()

    
    def start(self) -> None:
        asyncio.run(self.runner())