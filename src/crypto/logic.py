import sys, typing, datetime, asyncio
sys.dont_write_bytecode = True
import src.connector as con
from ccxt.base.types import Ticker

if typing.TYPE_CHECKING:
    from .transmitters.sandbox import MarketSimulator, RequesterSimulator
    from .transmitters.Client2API import Market
    from .transmitters.API2Client import PriceRequester
    from src.website.API import MainWebsite

Numeric: typing.TypeAlias = float | int
Index: typing.TypeAlias = int

class Math:
    def __init__(self) -> None:
        self.INFINITY: float = float("inf")
        self.nINFINITY: float = float("-inf")
        self.PI: float = 3.14159265359

    # izračuna procent med dvema cenama
    def difference_between_prices_in_percent(self, previous: Numeric, current: Numeric) -> float:
        try:
            return ((current - previous) / previous) * 100
        except ZeroDivisionError:
            return 0

    # NOTE: Update needed
    def resolve_precentage(self, decrease: float) -> int:
        return round(decrease * 5)
    
    # odstrani podvojene indexe
    def remove_duplicates(self, sequence: list[Numeric]) -> list[Index]:
        result: list[Index] = []
        last: int = int(sequence[0])

        for index in range(1, len(sequence) - 1):
            if int(sequence[index]) > last or int(sequence[index]) < last:
                result.append(index)
            last = int(sequence[index])
        return result

    # določi status grafa (pada, narašča)
    def graph_status(self, sequence: list[Numeric]) -> str:
        info: list[Numeric] = sequence[-25:-2]
        previous: Numeric = sequence[-1]
        status: Numeric = 0

        for num in info[::-1]:
            status += self.difference_between_prices_in_percent(previous, num)
            previous = num

        return "rise" if status < 0 else "fall"

    # najde zadnjo najvišjo/najnižjo točko
    def find_last_point(self, sequence: list[Numeric]) -> Index:
        true_indexes: list[Index] = self.remove_duplicates(sequence)
        modified_list: list[Numeric] = [i for j, i in enumerate(sequence) if j in true_indexes]
        
        status: str = self.graph_status(modified_list)
        
        previous_price: Numeric = modified_list[-1]
        previous_precent: float = 0
        change_counter: int = 0

        for i in range(len(modified_list) - 1, -1, -1):
            current_price: Numeric = modified_list[i]
            precent: float = self.difference_between_prices_in_percent(modified_list[-1], current_price)

            if status == "fall":
                if precent < previous_precent:
                    previous_precent = precent
                    change_counter = 0
                else:
                    if previous_price < current_price:
                        change_counter += 1
            else:
                if precent > previous_precent:
                    previous_precent = precent
                    change_counter = 0
                else:
                    if previous_price > current_price:
                        change_counter += 1
            
            previous_price = current_price

            if change_counter >= 10:
                batch: list[Numeric] = modified_list[i:-1]
                if status == "fall":
                    return true_indexes[modified_list.index(min(batch), i)]
                else:
                    return true_indexes[modified_list.index(max(batch), i)]

math = Math()

class LogicLink:
    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.current_time: datetime.date = datetime.datetime.now()
        
        self.config: dict[str, typing.Any] = con.read_shared("config")
        self.sandbox: bool = self.config["general"]["sandbox"]["status"]

        self.transactions: list[dict[str, typing.Any]] = con.read_shared("transaction_db")
        self.saved_transactions: list[dict[str, typing.Any]] = con.read_shared("saved_transactions")
        self.database: dict[str, list[Numeric] | Numeric | None] = con.read_shared("logic_db")
        self.interval: int = con.read_shared("interval")
        self.market: Market | MarketSimulator = con.read_shared("market")
        self.requester: RequesterSimulator | PriceRequester = con.read_shared("price_requester")

        self.d_tracker: dict[str, Numeric] = con.read_shared("daily_tracker")
        self.h_tracker: list[dict[str, float | str]] = con.read_shared("hourly_tracker")
        self.website_tracking: MainWebsite | None= con.read_shared("trackingWebsite")
    
    def trackers(self) -> None:
        # najvišja cena 
        if self.price > self.d_tracker.get("highest"):
            self.d_tracker["highest"] = self.price

        #najnižja cena
        if self.price < self.d_tracker.get("lowest"):
            self.d_tracker["lowest"] = self.price

        # posodobitev na internetni strani (local)
        if self.website_tracking:
            self.website_tracking.make_update(action="update_price", y_price=self.price, x_time=self.current_time)

    def save_all(self) -> None:
        structure: dict[str, typing.Any] = {
            "transaction_db": self.transactions,
            "logic_db": self.database,
            "daily_tracker": self.d_tracker,
            "hourly_tracker": self.h_tracker,
            "interval" : self.interval
        }
        # shranjevanje sprememb
        for name, var in structure.items():
            con.write_shared(name, var)

    async def run(self, data: str | dict[str, str | float | dict] | Ticker) -> None:
        # shranm ceu event slucajn ce ga bom pol rabu
        self._data: str | dict[str, str | float | dict] | Ticker = data
        
        # poiščem trenuntno ceno
        if isinstance(data, str):
            self.price = float(data)
        else:
            if data.get("info"):
                self.price = float(data.get("info").get("lastPrice"))
            else:
                self.price = float(data.get("lastPrice"))

        if not self.price:
            return

        self.database["priceDB"].append(self.price)
        self.trackers()

        # 300 cen - min da bot začne kupovat
        if (db_len := len(self.database.get("priceDB"))) > 300:
            
            if db_len > 500:
                self.database["priceDB"].pop(0)

            price_db: list[float] = self.database.get("priceDB")
            
            status: str = math.graph_status(price_db)
            last_point_index: Index = math.find_last_point(price_db)
            self.database["lastPrice"] = self.price

            # zdej pa logika za buy transakcije
            if status == "fall":
                checking_point_index: int = price_db.index(max(price_db[-240:]))
                checking_point_difference_percent: float = math.difference_between_prices_in_percent(price_db[checking_point_index], self.price)

                # TRACKER
                self.website_tracking.make_update(action="high_event", y_price=price_db[checking_point_index], x_time=price_db[last_point_index])
# protection
#-----------------------------------------------------------------------------------------------------------------------------
                # če je padl za 10%, vse sell
                if checking_point_difference_percent <= -10:
                    for transaction in self.transactions:
                        await self.market.sell(self.price, transaction)
# buy logic
#-----------------------------------------------------------------------------------------------------------------------------
                # če je za 0.8% padl, postane zanimiv in pregleduje..
                elif checking_point_difference_percent <= -0.8:
                    if not (last_price := self.database["buy"].get("last")) or math.difference_between_prices_in_percent(last_price, self.price) <= -0.3:
                        if previous_precent := self.database["buy"].get("%"):
                            # če je procent nižji (pada), zamenjamo
                            if previous_precent > checking_point_difference_percent:
                                self.database["buy"]["%"] = checking_point_difference_percent
                                self.database["buy"]["low"] = self.price
                            
                            else:
                                if last_low_price := self.database["buy"].get("low"):
                                    last_low_difference_precent: float = math.difference_between_prices_in_percent(last_low_price, self.price)

                                    if last_low_difference_precent > 0.125:
                                        if len(self.transactions) < 10:
                                            await self.market.buy(self.price, math.resolve_precentage(1), actual=checking_point_difference_percent)
                                            self.database["buy"]["last"] = self.price

                                            self.database["buy"]["%"] = None
                                            self.database["buy"]["low"] = None
                                        #print(f"[LOG]  > Current %: {checking_point_difference_percent:.5f}")
                                else:
                                    self.database["buy"]["low"] = self.price
                        else:
                            self.database["buy"]["%"] = checking_point_difference_percent
                else:
                    self.database["buy"]["%"] = None
                    self.database["buy"]["low"] = None
                    self.database["buy"]["last"] = None
# sell logic
#-----------------------------------------------------------------------------------------------------------------------------
            else:
                checking_point_index: int = price_db.index(min(price_db[-240:]))
                checking_point_difference_percent: float = math.difference_between_prices_in_percent(price_db[checking_point_index], self.price)
                
                # TRACKER
                self.website_tracking.make_update(action="low_event", y_price=price_db[checking_point_index], x_time=price_db[last_point_index])

                for transaction in self.transactions.copy():
                    buy_price: float = transaction.get("price")
                    difference_in_precent: float = math.difference_between_prices_in_percent(buy_price, self.price)
                    transaction_data: dict[str, typing.Any] = transaction.get("data")

                    if difference_in_precent >= 1:
                        if (previous_precent := transaction_data.get("%")):
                            if difference_in_precent > previous_precent:
                                transaction["data"]["counter"] = 0
                                transaction["data"]["%"] = difference_in_precent
                                transaction["data"]["last"] = None
                            else:
                                if last_high_price := transaction["data"].get("last"):
                                    last_high_difference_precent: float = math.difference_between_prices_in_percent(last_high_price, self.price)

                                    if last_high_difference_precent < -0.01: # CHECK HERE
                                        #self.website_tracking.make_update("filtered_event", y_price=self.price, x_time=self.current_time)
                                        transaction["data"]["counter"] += 1
                                        transaction["data"]["last"] = self.price
                                else:
                                    transaction["data"]["last"] = self.price
                        else:
                            transaction["data"]["%"] = difference_in_precent

                        if transaction_data.get("counter") >= 3:
                            await self.market.sell(self.price, transaction, actual=difference_in_precent)

                    elif difference_in_precent <= -5:
                        self.saved_transactions.append(transaction)
                        self.transactions.remove(transaction)

                for transaction in con.read_shared("saved_transactions"):
                    buy_price: float = transaction.get("price")
                    difference_in_precent: float = math.difference_between_prices_in_percent(buy_price, self.price)
                    transaction_data: dict[str, typing.Any] = transaction.get("data")

                    if difference_in_precent >= 1:
                        await self.market.sell(self.price, transaction, actual=difference_in_precent)

        # na koncu shran in zažene trackerje
        self.save_all()
        
        if self.sandbox:
            self.requester.ready = True
        return
