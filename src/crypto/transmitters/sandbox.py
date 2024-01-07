import sys, json, asyncio, typing, uuid
sys.dont_write_bytecode = True
import src.connector as con
from src.crypto.logic import LogicLink

if True:
    from src.website.API import MainWebsite

class RequesterSimulator:
    def __init__(self) -> None:
        self.infLoop: bool = True
        self.ready: bool = True
        self.config: dict[str, typing.Any] = con.read_shared("config")
    
    def read_file(self, path: str) -> list[str]:
        try:
            # odpremo file
            with open(path, "r", encoding="utf-8") as file:
                # vrnemo evente list[str]
                return file.readlines()
        except Exception as error:
            print(f"ERROR @RequesterSimulator.read_file: {type(error).__name__}: {error}")

    def get_price(self, events: list[str]) -> dict[str, typing.Any]:
        # to je dejansko generator, ki skipa evente (15s, 60s...) in jih yielda v končnen rezultat
        for index in range(0, len(events), self.config["general"]["sandbox"]["interval"] // 5):
            yield json.loads(events[index].replace("'", '"'))
        
    
    async def start(self) -> None:
        # asyncio loop za taske
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        
        _events: list[str] = self.read_file(self.config["general"]["sandbox"]["events_path"]) 
        events_function: typing.Callable = self.get_price(_events)

        input("Are you ready? (Click enter)")
        
        # glavni inf loop, ki je lahko ustavljen z self.infLoop = False
        while self.infLoop:
            # naredi nov task 
            while self.ready:
                #vzamemo naslenji value in ga pošljemo v logiko
                event: dict[str, typing.Any] = next(events_function)
                tasks = loop.create_task(LogicLink().run(event))

                CURRENT_MARKET_PRICE = con.read_shared("CURRENT_MARKET_PRICE")
                CURRENT_MARKET_PRICE: float = event.get("lastPrice")
                con.write_shared("CURRENT_MARKET_PRICE", CURRENT_MARKET_PRICE)

                #print(f"[SANDBOX] > New price event: {event}")
                self.ready = False
            
            await asyncio.sleep(0.2)

        # na self.infLoop = False, returnamo False in končamo TASK
        else:
            return False
        

# UPDATE NEEDED
class MarketSimulator:
    def __init__(self) -> None:
        self.tracker: MainWebsite | None = con.read_shared("trackingWebsite")

    async def sell(self, current_price: float, buy_transaction: dict[str, typing.Any], **OVERFLOW) -> bool:
        transaction_db: list[dict[str, typing.Any]] = con.read_shared("transaction_db")
        
        quantity: float = buy_transaction["quantity"]
        price: float = current_price * quantity
    
        print(f"[SELL] > Sold {quantity:.8f} btc for {price:.2f}€. Profit: {price-buy_transaction["quantity_eur"]:.2f}")
        
        if self.tracker:
            self.tracker.make_update("sell_event", y_price=current_price, x_time=None)
        
        WALLET: float = con.read_shared("WALLET")
        transaction_db.remove(buy_transaction)

        #print(transaction_db)
        
        con.write_shared("transaction_db", transaction_db)
        con.write_shared("WALLET", WALLET+price)

        return True

    async def buy(self, current_price: float, quantity_in_precent: float, **OVERFLOW) -> bool:
        WALLET = con.read_shared("WALLET")

        quantity = ((WALLET / current_price) / 100) * quantity_in_precent
        if quantity == 0:
            return
  
        price: float = current_price * quantity

        print(f"[BUY]  > Bought {quantity:.8f} btc for {price:.2f}€.")
        if self.tracker:
            self.tracker.make_update("buy_event", y_price=current_price, x_time=None)

        transaction_db: list[dict[str, typing.Any]] = con.read_shared("transaction_db")
        transaction_db.append({
            "id" : uuid.uuid4(),
            "quantity" : quantity,
            "price" : current_price,
            "quantity_eur" : price,
            "data" : {
                "%" : None,
                "counter" : 0
            }
        })

       # print(transaction_db)

        con.write_shared("WALLET", WALLET-price)
        con.write_shared("transaction_db", transaction_db)
        return True
    
