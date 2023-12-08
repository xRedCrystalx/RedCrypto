import sys, discord, typing, ccxt, os, asyncio, threading
sys.dont_write_bytecode = True
from src.system.colors import C, CNone
from discord.ext import commands

class SharedResource:
    def __init__(self) -> None:
        self.lock: threading.Lock = threading.Lock()
        
        #global
        self.path: str = None
        self.colors: C | CNone = None
        self.config: dict = None
        self.loop: asyncio.AbstractEventLoop = None

        # discord
        self.discord_bot: commands.Bot = None
        self.discord_notifications: list[dict[str, bool | str | float]] = []

        #crypto
        self.interval: int | float = 5
        self.transaction_db: dict = {}
        self.price_db: dict = {}

shared = SharedResource()

def read_shared(var: str) -> typing.Any:
    with shared.lock:
        try:
            return getattr(shared, var)
        except:
            return None
    
def update_shared(var: str, value: typing.Any, action: typing.Literal["replace", "add", "substract", "divide", "multiply", "append", "remove", "pop", "update"] = "replace", extra: typing.Any = None) -> bool:
    with shared.lock:
        try:
            shared_variable: typing.Any = getattr(shared, var)
        except:
            return False
        
        if isinstance(shared_variable, list):
            if action in ("replace", "append", "pop", "remove"):
                if action == "replace":
                    shared_variable = value
                    return True
                
                elif action == "append":
                    shared_variable.append(value)
                    return True
                
                elif action == "pop":
                    if isinstance(extra, int):
                        try:
                            shared_variable.pop(extra)
                            return True
                        except:
                            return False
                
                elif action == "remove":
                    try:
                        shared_variable.remove(value)
                        return True
                    except:
                        return False
            return False
        
        elif isinstance(shared_variable, dict):
            def path_loader(strPath: str) -> typing.Any:
                for path in strPath.split("."):
                    try:
                        shared_variable = shared_variable[path]
                    except:
                        return None
                return shared_variable
            
            if action in ("replace", "update", "pop"):
                if action == "replace":
                    if isinstance(extra, str):
                        shared_variable = path_loader(extra)
                        if shared_variable:
                            shared_variable = value
                            return True
                    else:
                        shared_variable = value
                        return True
                
                elif action == "update":
                    if isinstance(value, dict):
                        if isinstance(extra, str):
                            shared_variable = path_loader(extra)
                            if shared_variable:
                                shared_variable.update(value)
                                return True
                        else:
                            shared_variable.update(value)
                            return True
                    return False
                    
                elif action == "pop":
                    if isinstance(extra, str):
                        shared_variable = path_loader(extra)
                        if shared_variable:
                            try:
                                shared_variable.pop(value)
                                return True
                            except:
                                return False
                    else:
                        try:
                            shared_variable.pop(value)
                            return True
                        except:
                            return False
                    return False
        
        elif type(shared_variable) in (int, float):
            if action in ("replace", "add", "substract", "divide", "multiply"):
                if type(value) in (int, float):
                    if action == "replace":
                        shared_variable = value
                        return True
                    
                    elif action == "add":
                        shared_variable += value
                        return True
                        
                    elif action == "substract":
                        shared_variable -= value
                        return True

                    elif action == "divide":
                        shared_variable /= value
                        return True
                    
                    elif action == "multiply":
                        shared_variable *= value
                        return True
            return False
        
        elif isinstance(shared_variable, str):
            if action in ("replace", "add", "multiply"):
                if isinstance(value, str) or isinstance(value, None):
                    if action == "replace":
                        shared_variable = value
                        return True
                    
                    elif action == "add":
                        shared_variable += value
                        return True
                    
                    elif action == "multiply":
                        if isinstance(extra, int):
                            shared_variable *= extra
                            return True
            return False
                
        elif isinstance(shared_variable, bool):
            if action == "replace":
                shared_variable = value
                return True
            return False
        
        else:
            shared_variable = value
            return True

async def terminate() -> None:
    print(f"{shared.colors.Red}TERMINATING.{shared.colors.R}")

    if shared.discord_bot:
        try:
            # close connection with discord
            await shared.discord_bot.close()
        except Exception as error:
            print(error)
    
    try:
        # kill main loop and its tasks/threads
        shared.loop.close()
    except Exception as error:
        print(error)

    # system exit
    #sys.exit(0)