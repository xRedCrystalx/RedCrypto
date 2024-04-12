import sys, json, asyncio, typing, uuid
sys.dont_write_bytecode = True
import src.connector as con
from src.crypto.logic import LogicLink

if typing.TYPE_CHECKING:
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

    def get_price(self, events: list[str]) -> typing.Generator[dict[str, typing.Any], None, None]:
        # to je dejansko generator, ki skipa evente (15s, 60s...) in jih yielda v končnen rezultat
        for index in range(0, len(events), self.config["general"]["sandbox"]["interval"] // 5):
            yield json.loads(events[index].replace("'", '"'))

    async def start(self) -> None:
        # asyncio loop za taske
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        
        _events: list[str] = self.read_file(self.config["general"]["sandbox"]["events_path"]) 
        events_function: typing.Callable = self.get_price(_events)

        #input("Are you ready? (Click enter)")
        await asyncio.sleep(5)
        
        # glavni inf loop, ki je lahko ustavljen z self.infLoop = False
        while self.infLoop:
            # naredi nov task 
            while self.ready:
                try:
                    #vzamemo naslednji value in ga pošljemo v logiko
                    if event := next(events_function):
                        loop.create_task(LogicLink().run(event))
                except StopIteration:
                    print("Simulation finished.")
                    print(f"Total profit: {con.read_shared("PROFIT"):.2f}€ >> Saved transactions: {len(con.read_shared("saved_transactions"))}")
                except Exception as error:
                    print(f"ERROR async @RequesterSimulater.start: {type(error).__name__}: {error}")

                # shranmo v shared (sandbox)
                con.write_shared("CURRENT_MARKET_PRICE", event.get("lastPrice"))
                self.ready = False

            await asyncio.sleep(0.2)
        # na self.infLoop = False, returnamo False in končamo TASK
        else:
            return False

class MarketSimulator:
    def __init__(self) -> None:
        self.tracker: MainWebsite | None = con.read_shared("trackingWebsite")
        self.events: int = 0
    
    def calculate_fee(self, price: float, type: typing.Literal["intant", "normal", "DDV"] = "normal") -> float:
        return price * (0.1 if type == "normal" else 0.5 if type == "instant" else 15) / 100

    async def sell(self, current_price: float, buy_transaction: dict[str, typing.Any], actual: float, **OVERFLOW) -> bool:
        transaction_db: list[dict[str, typing.Any]] = con.read_shared("transaction_db")
        PROFIT: float = con.read_shared("PROFIT")
        
        quantity: float = buy_transaction["quantity"]
        price: float = current_price * quantity
        event_profit = self.calculate_fee(price, "normal")-buy_transaction["quantity_eur"]
    
        print(f"[SELL] > Sold {quantity:.8f} btc for {price:.2f}€. Profit: {event_profit:.2f} -> Increase: {actual:.5f}%")
        
        if self.tracker:
            self.tracker.make_update("sell_event", y_price=current_price, x_time=None)

        WALLET: float = con.read_shared("WALLET")
        transaction_db.remove(buy_transaction)

        con.write_shared("transaction_db", transaction_db)
        con.write_shared("WALLET", WALLET+event_profit)
        con.write_shared("PROFIT", PROFIT+event_profit)

        self.events += 1
        if self.events % 10 == 0:
            print(f"[DEBUG] > Profit after {self.events}th sell event: {PROFIT+event_profit:.2f} €.")

        return True

    async def buy(self, current_price: float, quantity_in_precent: float, actual: float, **OVERFLOW) -> bool:
        WALLET = con.read_shared("WALLET")

        quantity = ((WALLET / current_price) / 100) * quantity_in_precent
        if quantity == 0:
            return
  
        price: float = current_price * quantity
        event_price: float = self.calculate_fee(price, "normal")

        print(f"[BUY]  > Bought {quantity:.8f} btc for {price:.2f}€. -> Decrease: {actual:.5f}%")
        if self.tracker:
            self.tracker.make_update("buy_event", y_price=current_price, x_time=None)

        transaction_db: list[dict[str, typing.Any]] = con.read_shared("transaction_db")
        transaction_db.append({
            "id" : uuid.uuid4(),
            "quantity" : quantity,
            "price" : current_price,
            "quantity_eur" : event_price,
            "data" : {
                "%" : None,
                "counter" : 0,
                "last" : None,
                "life" : 7
            }
        })

        con.write_shared("WALLET", WALLET-price)
        con.write_shared("transaction_db", transaction_db)
        return True
    
