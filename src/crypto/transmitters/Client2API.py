import sys, ccxt, typing, asyncio
sys.dont_write_bytecode = True
import src.connector as con
from ccxt.base.types import Order

class Market:
    def __init__(self) -> None:
        self.config: dict[str, typing.Any] = con.read_shared("config")
        self.exchange: ccxt.binance = con.read_shared("binance")
        self.symbol: str = self.config["general"]["symbol"]
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

    async def _handle_open_order(self, order: Order, **kwargs) -> dict:
        # shranmo kopijo originala
        _order: Order = order

        while order.status != "open":
            await asyncio.sleep(2.5)
            order = self.exchange.fetch_order(_order.id)
        else:
            if order.status == "rejected":
                print(f"[{order.side.capitalize()}] > Order with id {order.id} was rejected by the exchange.")
                return
            else:
                print(f"[{order.side.capitalize()}] > Transaction successful. {order.filled}/{order.amount} ID: {order.id}")

                transaction_db: list[dict[str, typing.Any]] = con.read_shared("transaction_db")

                if order.side == "buy":
                    transaction_db.append({
                        "id" : order.id,
                        "quantity" : order.filled,
                        "price" : kwargs["price"]
                    })
                else:
                    transaction: str = kwargs["transaction"]
                    transaction_db.remove(transaction)
                
                con.write_shared("transaction_db", transaction_db)
    
    async def sell(self, current_price: float, buy_transaction: dict[str, typing.Any] = None, quantity: float = None) -> bool:
        if quantity:
            order: Order = self.exchange.create_limit_sell_order(self.symbol, quantity, current_price-1)
        elif buy_transaction:
            order: Order = self.exchange.create_limit_sell_order(self.symbol, buy_transaction["quantity"], current_price-1)
        
        if order:
            self.loop.create_task(self._handle_open_order(order, transaction=buy_transaction))
            return True
        
        return False

    async def buy(self, quantity_in_precent: float, current_price: float) -> bool:
        balance: float = await self.get_balance()
        quantity: float = (balance / 100) * quantity_in_precent

        if quantity:
            order: Order = self.exchange.create_limit_buy_order(self.symbol, quantity, current_price+1)

        if order:
            self.loop.create_task(self._handle_open_order(order, price=current_price))
            return True

        return False

    async def get_balance(self) -> float:
        return self.exchange.fetch_balance()["free"]["BTC"]
