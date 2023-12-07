import sys, ccxt, typing, asyncio
sys.dont_write_bytecode = True
import src.connector as con
from selenium.webdriver import (Chrome, Firefox, Safari, Edge,
                                ChromeOptions, FirefoxOptions, SafariOptions, EdgeOptions,
                                ChromeService, FirefoxService, SafariService, EdgeService)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

class E:
    def __init__(self, exchange: ccxt.binance) -> None:
        self.shared: con.SharedResource = con.shared
        self.webdriver: Firefox | Safari | Edge | Chrome = None
        self.infLoop = True
        self.driverValidiation = True
        self.exchange: ccxt.binance = exchange
        
    def _start_selenium_instance(self) -> None:
        filter: dict[str, tuple[typing.Callable]] = {
            "chrome" : (Chrome, ChromeService, ChromeOptions),
            "firefox" : (Firefox, FirefoxService, FirefoxOptions),
            "safari" : (Safari, SafariService, SafariOptions),
            "edge" : (Edge, EdgeService, EdgeOptions)
        }
        
        _config: dict[str, str | list[str]] = self.shared.config["general"]["selenium"]
        _webdriver: tuple[typing.Callable] = filter.get(_config["webdriver"].lower())
        
        if _webdriver:
            driver_service: ChromeService | SafariService | FirefoxService | EdgeService = _webdriver[1](executable_path=_config["path"])
            driver_options: ChromeOptions | SafariOptions | FirefoxOptions | EdgeOptions = _webdriver[2]()
            
            for option in _config["arguments"]:
                driver_options.add_argument(option)
            
            try:
                client: Firefox | Safari | Edge | Chrome = _webdriver[0](service=driver_service, options=driver_options, keep_alive=True)
            except Exception as error:
                self.driverValidiation = False
                print(f"API2Client >> Failed to start driver. {type(error).__name__}: {error}")
                return
            
            try:  
                client.get(_config["url"])
                
                wait = WebDriverWait(client, 60)
                wait.until(expected_conditions.visibility_of_element_located((By.XPATH, _config["XPATH"])))
            
                return client
            except Exception as error:
                self.driverValidiation = False
                print(f"API2Client >> Failed to connect to the page. {type(error).__name__}: {error}")
                
            

        else:
            self.driverValidiation = False
            print("API2Client >> Failed to find right driver, please check configuration file.")
            return

    def _kill_selenium_instance(self) -> None:
        return self.webdriver.close()

    def selenium_requester(self) -> str:
        try:
            return self.webdriver.find_element(By.XPATH, self.shared.config["general"]["selenium"]["XPATH"]).text
        except Exception as error:
            print(f"API2Client >> Selenium request failed. {type(error).__name__}: {error}")
            return
        
    def ccxt_requester(self) -> dict:
        try:
            return self.exchange.fetch_ticker(self.shared.config["general"]["symbol"])
        except Exception as error:
            print(f"API2Client >> CCXT request failed. {type(error).__name__}: {error}")
            return
        
    async def main(self) -> None:
        while self.infLoop:
            if self.shared.interval > 10:
                data: dict = self.ccxt_requester()
                # CALL LOGIC FUNCTION
            else:
                if self.webdriver:
                    data: str = self.selenium_requester()
                    # CALL LOGIC FUNCTION
                else:
                    if self.driverValidiation:
                        self._start_selenium_instance()
            
            await asyncio.sleep(self.shared.interval)
            
            