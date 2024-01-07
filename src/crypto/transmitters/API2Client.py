import sys, ccxt, typing, asyncio
sys.dont_write_bytecode = True
import src.connector as con
from src.crypto.logic import LogicLink

# selenium importi
from selenium.webdriver import (Chrome, Firefox, Safari, Edge,
                                ChromeOptions, FirefoxOptions, SafariOptions, EdgeOptions,
                                ChromeService, FirefoxService, SafariService, EdgeService)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

# za typehinte
#if typing.TYPE_CHECKING:
from ccxt.base.types import Ticker
#from selenium.webdriver.Chrome.webdriver import WebDriver

class PriceRequester:
    def __init__(self) -> None:
        # self podatki
        self.webdriver: Firefox | Safari | Edge | Chrome = None
        self.driverValidation = True
        self.exchange: ccxt.binance = None
        self.infLoop: bool = True
        
    async def _start_selenium_instance(self) -> bool:#| WebDriver
        # podpora za use webdriverje
        filter: dict[str, tuple[typing.Callable]] = {
            "chrome" : (Chrome, ChromeService, ChromeOptions),
            "firefox" : (Firefox, FirefoxService, FirefoxOptions),
            "safari" : (Safari, SafariService, SafariOptions),
            "edge" : (Edge, EdgeService, EdgeOptions)
        }
        
        # konfiguracija & podatki filtra
        _config: dict[str, str | list[str]] = con.read_shared("config")["general"]["selenium"]
        _webdriver: tuple[typing.Callable] = filter.get(_config["webdriver"].lower())
        
        if _webdriver:
            # zaženemo Service
            try:
                driver_service: ChromeService | SafariService | FirefoxService | EdgeService = _webdriver[1](executable_path=_config["path"])
            except Exception as error:
                print("PriceRequester >> Invalid driver PATH provided. Stopping.")
                return False
            
            # zaženemo Options + argumente
            driver_options: ChromeOptions | SafariOptions | FirefoxOptions | EdgeOptions = _webdriver[2]()
            [driver_options.add_argument(option) for option in _config["arguments"]]

            try:
                # začetek dejanskega clienta
                client: Firefox | Safari | Edge | Chrome = _webdriver[0](service=driver_service, options=driver_options, keep_alive=True)
            except Exception as error:
                print(f"PriceRequester >> Failed to start selenium driver. {type(error).__name__}: {error}")
                return False
            
            try:
                # povezava na internetno stran & čakanje da se naloži
                client.get(_config["url"])
                wait = WebDriverWait(client, timeout=60)
                wait.until(expected_conditions.visibility_of_element_located((By.XPATH, _config["XPATH"])))
                return client

            except Exception as error:
                # napaka povezave na internetno stran
                print(f"PriceRequester >> Failed to connect to the page. {type(error).__name__}: {error}")
                return False
        else:
            # napaka v konfiguraciji
            print("PriceRequester >> Failed to find right driver, please check configuration file.")
            return False

    async def _kill_selenium_instance(self) -> None:
        return self.webdriver.close()

    def selenium_requester(self) -> str | None:
        try:
            # returnamo string (value) od XPATH elementa
            return self.webdriver.find_element(By.XPATH, con.read_shared("config")["general"]["selenium"]["XPATH"]).text
        except Exception as error:
            # napaka
            print(f"API2Client >> Selenium request failed. {type(error).__name__}: {error}")
            return
        
    def ccxt_requester(self) -> Ticker | None:
        try:
            # returnamo TICKER (podatke) direktno iz BinanceAPI z ccxt lib
            return self.exchange.fetch_ticker(con.read_shared("config")["general"]["symbol"])
        except Exception as error:
            # napaka
            print(f"API2Client >> CCXT request failed. {type(error).__name__}: {error}")
            return
     
    async def start(self) -> None:
        # asyncio loop za taske
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        
        # glavni inf loop, ki je lahko ustavljen z self.infLoop = False
        while self.infLoop:
            
            # če je interval večji ali enak 5, se uporab ccxt requester
            if interval := con.read_shared("interval") >= 5:
                if response := self.ccxt_requester():
                    loop.create_task(LogicLink().run(data=response))
            
            # če je interval manjši, se uporab selenium requester
            else:
                # če selenium obstaja, naredimo request
                if self.webdriver:
                    if response := self.selenium_requester():
                        loop.create_task(LogicLink().run(data=response))
                
                # drugače zaženemo selenium če ni prisiljno ugasnjen
                else:
                    if self.driverValidation:
                        #če starter vrne client, ga shranimo
                        if status := await loop.create_task(self._start_selenium_instance()):
                            self.webdriver = status
                        # drgač pa konča selenium in ga prisiljno ugasne
                        else:
                            self.driverValidation = False

            # spimo kolkr je določen interval
            await asyncio.sleep(interval)

        # na self.infLoop = False, returnamo False in končamo TASK
        else:
            return False
                        
                        
