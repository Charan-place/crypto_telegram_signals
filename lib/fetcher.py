import ccxt.async_support as ccxt
import pandas as pd
from lib.config import EXCHANGE_ID, CANDLES


async def fetch_ohlcv(symbol: str, timeframe: str) -> pd.DataFrame | None:
    exchange = getattr(ccxt, EXCHANGE_ID)({
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    try:
        raw = await exchange.fetch_ohlcv(symbol, timeframe, limit=CANDLES)
        if not raw:
            return None
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        print(f"[fetch] {symbol} {timeframe}: {e}")
        return None
    finally:
        await exchange.close()
