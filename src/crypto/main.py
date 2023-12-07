import ccxt, sys
sys.dont_write_bytecode = True

class CryptoMain:
    def __init__(self) -> None:
        self.binance = ccxt.binance()
    
    def start(self) -> None:
        ...