import sys, typing, datetime, schedule, asyncio, requests, json
sys.dont_write_bytecode = True
import plotly.graph_objects as go
import src.connector as con

    
class HourlyReports:  
    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.loop.create_task(self.start())

    def create_report(data: list[dict[str, float | str]]) -> bytes | None:
        fig: go.Figure = go.Figure()
        fig.update_layout(template="plotly_dark", title="Hourly Report", xaxis_title="Time", yaxis_title="Price in EUR")
                    
        traces: dict[str, dict[str, list[typing.Any]]] = {
            "buy_event" : {
                "x" : [],
                "y" : []
            },
            "sell_event" : {
                "x" : [],
                "y" : []
            },
            "update_price" : {
                "x" : [],
                "y" : []
            }
        }
        
        for event in data:
            if (name := event.get("name")) == "buy_event":
                traces["buy_event"]["x"].append(event["x"])
                traces["buy_event"]["y"].append(event["y"])

            elif name == "sell_event":
                traces["sell_event"]["x"].append(event["x"])
                traces["sell_event"]["y"].append(event["y"])

            elif name == "update_price":
                traces["update_price"]["x"].append(event["x"])
                traces["update_price"]["y"].append(event["y"])
        
        fig.add_trace(go.Scatter(x=traces["update_price"]["x"], y=traces["update_price"]["y"], mode="lines+markers", name="Price Trace"))     
        fig.add_trace(go.Scatter(x=traces["buy_event"]["x"], y=traces["buy_event"]["y"], mode="markers", marker={"color": "red", "size" : 12}, name="Buy Event"))
        fig.add_trace(go.Scatter(x=traces["sell_event"]["x"], y=traces["sell_event"]["y"], mode="markers", marker={"color": "green", "size" : 12}, name="Sell Event", text=['A', 'B', 'C', 'D', 'E'], textposition="auto"))
        return img if (img := fig.to_image(format="png", engine="kaleido", width=1920, height=1080)) else None #width=3840, height=2160
    
    def send_to_discord(image_bytes: bytes) -> None:
        if not (webhook := con.read_shared("config")["local-tracking"]["webhook"]):
            raise ValueError("Webhook URL is not configured.")
        
        date: datetime.datetime = datetime.datetime.now()
        
        data: dict = {
            "embeds": [
                {
                    "title": f"Hourly Report {date.hour-1}:00 - {date.hour}:00 @ {date.strftime('%d.%m.%Y')}",
                    "color": 0x2B2D31,
                    "image": {
                        "url": "attachment://image.png"
                    },
                    "footer": {
                        "text": "RedCrypto"
                    },
                    "timestamp": date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"
                }
            ]
        }
        
        files: dict[str, str | bytes] = {
            "file": ("image.png", image_bytes, "image/png")
        }
        
        try:
            response: requests.Response = requests.post(webhook, data={"payload_json": json.dumps(data)}, files=files)
        except Exception as request_error:
            print(f"Error making request: {type(request_error).__name__}; {request_error}")

    def loader(self) -> None:
        if hourly := con.read_shared("hourly_tracker"):
            report: bytes | None = self.create_report(hourly)
            
            if report:
                self.send_to_discord(report)
                
            con.write_shared("hourly_tracker", [])
    
    async def start(self) -> None:
        schedule.every().hour.at(":00").do(self.loader)
        while True:
            schedule.run_pending()
            await asyncio.sleep(45)