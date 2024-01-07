import sys, typing, datetime, asyncio
sys.dont_write_bytecode = True
import src.connector as con

if True:
    from typing import TypeAlias
    from ccxt.base.types import Ticker
    #from src.crypto.transmitters.sandbox import MarketSimulator
    #from src.crypto.transmitters.Client2API import Market
    #from src.website.API import MainWebsite

Numeric: TypeAlias = float | int
Index: TypeAlias = int

class Math:
    def __init__(self) -> None:
        self.INFINITY: float = float("inf")
        self.nINFINITY: float = float("-inf")
        self.PI: float = 3.14159265359

    # izračuna davek glede na ceno. podpora: DDV (15%), market (0.1%), instant (0.5%)
    def calculate_fee(self, price: Numeric, type: typing.Literal["intant", "normal", "DDV"] = "normal") -> float:
        return price * (0.1 if type == "normal" else 0.5 if type == "instant" else 15) / 100

    # izračuna procent med dvema cenama
    def difference_between_prices_in_percent(self, previous: Numeric, current: Numeric) -> float:
        try:
            return ((current - previous) / previous) * 100
        except ZeroDivisionError:
            return 0

    # izračuna raliko mode dvema cenama
    def difference_between_prices_in_eur(self, buy: Numeric, sell: Numeric) -> float:
        return sell - buy
    
    # sortira list številk po velikosti ("sort_highest", "sort_lowest")
    def sort_list(self, prices: list[Numeric], option: typing.Literal["sort_highest", "sort_lowest"]) -> list[Numeric] | None:
        if option == "sort_highest":
            return sorted(prices, reverse=True)
        elif option == "sort_lowest":
            return sorted(prices)
        return
    
    # NOTE: Update needed
    def resolve_precentage(self, decrease: float) -> int:
        return 20
        
        if decrease > -0.3:
            return 30
        elif decrease > -0.4:
            return 40
        elif decrease > -0.5:
            return 60
        elif decrease > -0.6:
            return 80
        else:
            return 100
    
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
        info: list[Numeric] = sequence[-15:-1]
        status: int = 0

        for num in info[::-1]:
            if info[0] > num:
                status -= 1
            elif info[0] < num:
                status += 1

        if status > 0:
            return "rise"
        else:
            return "fall"
        
    def find_last_point(self, sequence: list[Numeric]) -> Index:
        true_indexes: list[Index] = self.remove_duplicates(sequence)
        status: str = self.graph_status(sequence)
        modified_list: list[Numeric] = [i for j, i in enumerate(sequence) if j in true_indexes]
        
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
        self.database: dict[str, list[Numeric] | Numeric | None] = con.read_shared("logic_db")
        self.interval: int = con.read_shared("interval")
        self.market = con.read_shared("market") #: Market | MarketSimulator
        self.requester = con.read_shared("price_requester")

        self.d_tracker: dict[str, Numeric] = con.read_shared("daily_tracker")
        self.h_tracker: list[dict[str, float | str]] = con.read_shared("hourly_tracker")
        self.website_tracking= con.read_shared("trackingWebsite")#: MainWebsite | None
    
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

        # posodobitev za graf (hourly)
        if self.interval == 15:
            self.h_tracker.append({"name" : "update_price", "y" : self.price, "x" : self.current_time})

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
            #print("SAVE", name)
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
        price_db: list[float] = self.database.get("priceDB")


        # 150 cen = 37,5min: 15s * 150 / 60s - min da bot začne kupovat
        if (db_len := len(price_db)) > 300:
            
            if db_len > 1500:
                self.database["priceDB"].pop(0)

            status: str = math.graph_status(price_db)
            
            # cene
            highest_price: float = max(price_db)
            lowest_price: float = min(price_db)
            previous_price: float | None = self.database.get("lastPrice")

            # indexi
            last_point_index: Index = math.find_last_point(price_db)
            highest_point_index: Index = price_db.index(highest_price)
            lowest_point_index: Index = price_db.index(lowest_price)

            # procenti
            #p_overall_difference: float = math.difference_between_prices_in_percent(price_db[0], self.price)
            #p_overall_highPoint2now_difference: float = math.difference_between_prices_in_percent(highest_price, self.price)
            #p_overall_lowPoint2now_difference: float = math.difference_between_prices_in_percent(lowest_price, self.price)
            #p_overall_lastPoint2now_difference: float = math.difference_between_prices_in_percent(price_db[last_point_index], self.price)

            if previous_price:
                p_previous2now_difference: float = math.difference_between_prices_in_percent(previous_price, self.price)
                self.database["precentDB"].append(p_previous2now_difference)

            checking_point_difference_percent = None

            # zdej pa logika za buy transakcije
            # najprej morm ugotovit ce market pada in ali se bolj splača uzet zadnjo ceno al najvišjo..
            if status == "fall":
                checking_point_index: int = last_point_index if last_point_index - 100 > highest_point_index else highest_point_index
                checking_point_difference_percent: float = math.difference_between_prices_in_percent(price_db[checking_point_index], self.price)

                buy_db: dict[str, Numeric] = self.database.get("buy")
                
                # če je padl za 10%, vse sell
                if checking_point_difference_percent <= -10:
                    for transaction in self.transactions:
                        self.loop.create_task(self.market.sell(self.price, transaction))
                    return

                elif checking_point_difference_percent <= -2:
                    self.loop.create_task(self.market.buy(self.price, math.resolve_precentage(checking_point_difference_percent)))
                    return

                # če je za 0.3% padl, postane zanimiv in pregleduje..
                elif checking_point_difference_percent <= -0.3:
                    # če je to prvič, samo shranmo, drugače primerjamo
                    if previous_precent := buy_db.get("%"):
                        # če je procent nižji (pada), zamenjamo
                        if previous_precent > checking_point_difference_percent:
                            print(f"CENA SE JE ZMANJŠALA {checking_point_difference_percent}")
                            self.database["buy"]["%"] = checking_point_difference_percent
                            self.database["buy"]["counter"] = 0
                        
                        # drugače se je povečal in shranmo +1 v counter..
                        else:
                            self.database["buy"]["counter"] += 1

                        # če je counter > x (se povečuje, kupmo) in resetiramo
                        if buy_db.get("counter") >= 4:
                            self.loop.create_task(self.market.buy(self.price, math.resolve_precentage(previous_precent)))

                            # reset
                            self.database["buy"]["counter"] = 0
                            self.database["buy"]["%"] = None
                    else:
                        self.database["buy"]["%"] = checking_point_difference_percent

                #print(f"LOGIC EVENT > Price {self.price}; Status: {status}; Last Point: {last_point_index}; Fall Precentage: {checking_point_difference_percent}")

            if self.transactions:
                for transaction in self.transactions:
                    buy_price: float = transaction.get("price")
                    difference_in_precent: float = math.difference_between_prices_in_percent(buy_price, self.price)
                    transaction_data: dict[str, typing.Any] = transaction.get("data")

                    if difference_in_precent >= 0.4:
                        #status == "rise" and 
                        if (previous_precent := transaction_data.get("%")):
                            if difference_in_precent > previous_precent:
                                print(f"CENA SE JE POVEČALA: {difference_in_precent}")
                                transaction["data"]["counter"] = 0
                            else:
                                transaction["data"]["counter"] += 1
                        else:
                            transaction["data"]["%"] = difference_in_precent

                        if transaction_data.get("counter") >= 3:
                            self.loop.create_task(self.market.sell(self.price, transaction))
                            transaction["data"]["counter"] = 0

        # na koncu shran in zažene trackerje
        self.trackers()
        self.save_all()

        if self.sandbox:
            self.requester.ready = True


# ta class ne dela, ampak mam sam neke base funkcije k jih bom mogoče rabu v prihodosti
class FutureMath:
    def __find_points(self, history: list[Numeric], option: typing.Literal["lowest_points", "highest_points"]) -> list[Index] | None:
        points: list[Index] = []

        if option == "lowest_points":
            for i in range(1, len(history) - 1):
                if history[i-1] > history[i] < history[i+1]:
                    points.append(i)
            return points

        elif option == "highest_points":
            for i in range(1, len(history) - 1):
                if history[i-1] < history[i] > history[i+1]:
                    points.append(i)
            return points
        return None

    def compare_operator_sequence_filter(self, unfiltered: list[Numeric], skipping: bool = True) -> list[Index]:
        indexes: list[Index] = []
        skip: bool = False

        if skipping:
            for i in range(1, len(unfiltered) - 1):
                if not skip:
                    if (unfiltered[i-1] < unfiltered[i] > unfiltered[i+1]) or (unfiltered[i-1] > unfiltered[i] < unfiltered[i+1]):
                        indexes.append(i)
                        skip = True
                    skip = False
        else:
            for i in range(1, len(unfiltered) - 1):
                if (unfiltered[i-1] < unfiltered[i] > unfiltered[i+1]) or (unfiltered[i-1] > unfiltered[i] < unfiltered[i+1]):
                    indexes.append(i)
        
        return indexes

    def precent_sequence_filter(self, unfiltered: list[Numeric], precentage: Numeric) -> list[Numeric]:
        last: int = unfiltered[0]
        indexes: list[Index] = []
        
        for index, price in enumerate(unfiltered.copy()):
            precent: float = self.difference_between_prices_in_percent(last, price)
            new_precent: float | None = self.difference_between_prices_in_percent(price, unfiltered[inx]) if (inx := index+1 if index+1 != len(unfiltered) else None) else None
            
            if new_precent:
                if precent > precentage or precent < -1 * precentage and new_precent < precent if precent > 0 else new_precent > precent:
                    last = price
                    indexes.append(index)

        return indexes
""":
POPRAV get_chart_point_indexes

min 0.47% - +inf

class Order(TypedDict):
    info: Dict[str, Any]
    id: Str
    clientOrderId: Str
    datetime: Str
    timestamp: Int
    lastTradeTimestamp: Int
    lastUpdateTimestamp: Int
    status: Str
    symbol: Str
    type: Str
    timeInForce: Str
    side: OrderSide
    price: Num
    average: Num
    amount: Num
    filled: Num
    remaining: Num
    stopPrice: Num
    takeProfitPrice: Num
    stopLossPrice: Num
    cost: Num
    trades: List[Trade]
    fee: Fee


"""