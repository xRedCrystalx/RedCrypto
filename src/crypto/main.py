import ccxt, sys
sys.dont_write_bytecode = True

class CryptoMain:
    def __init__(self) -> None:
        pass
    
    def start(self) -> None:
        ...


binance = ccxt.binance()
symbol = "BTC/USDT"