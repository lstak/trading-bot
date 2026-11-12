import os

import matplotlib.pyplot as plt
import polars as pl
from dotenv import load_dotenv
from ib_async import IB, Stock
from matplotlib.figure import Figure

load_dotenv()

# Yahoo-style symbol suffix -> (IB primary exchange, currency)
EXCHANGES = {
    "": ("NASDAQ", "USD"),
    "DE": ("IBIS", "EUR"),  # Xetra
    "AS": ("AEB", "EUR"),  # Euronext Amsterdam
    "PA": ("SBF", "EUR"),  # Euronext Paris
    "BR": ("ENEXT.BE", "EUR"),  # Euronext Brussels
    "L": ("LSE", "GBP"),  # London
}


def make_contract(symbol: str) -> Stock:
    """Turn a symbol like 'VWCE.DE' into an IB stock contract."""
    ticker, _, suffix = symbol.partition(".")
    if suffix not in EXCHANGES:
        raise ValueError(f"Unknown exchange suffix in {symbol!r}")
    exchange, currency = EXCHANGES[suffix]
    return Stock(ticker, "SMART", currency, primaryExchange=exchange)


def fetch_bars(
    ib: IB,
    symbol: str,
    endDateTime: str = "",
    durationStr: str = "30 D",
    barSizeSetting: str = "1 hour",
    whatToShow: str = "TRADES",
    useRTH: bool = True,
) -> pl.DataFrame:
    """Fetch historical bars for a symbol as a Polars DataFrame."""
    contract = make_contract(symbol)
    if not ib.qualifyContracts(contract):
        raise ValueError(f"Could not find contract for {symbol!r}")

    bars = ib.reqHistoricalData(
        contract,
        endDateTime=endDateTime,
        durationStr=durationStr,
        barSizeSetting=barSizeSetting,
        whatToShow=whatToShow,
        useRTH=useRTH,
    )
    if not bars:
        raise ValueError(f"Could not find bar data for {symbol!r}")
    return pl.DataFrame(bars).with_columns(pl.col("date").cast(pl.Datetime(time_zone="UTC")))


def clean_bars(df: pl.DataFrame) -> pl.DataFrame:
    """Clean a DataFrame of bars by dropping the open, high and low columns."""
    return df.drop("open", "high", "low")


def add_ema(df: pl.DataFrame, period: int = 9) -> pl.DataFrame:
    """Add an exponential moving average of close as column ema_{period}."""
    return df.with_columns(
        pl.col("close").ewm_mean(span=period,
                                 adjust=False).alias(f"ema_{period}")
    )


# Fixed series colors: close first, then each EMA column in order
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]


def plot_ema(df: pl.DataFrame, title: str = "") -> Figure:
    """Plot close and every ema_* column against date."""
    columns = ["close", *[c for c in df.columns if c.startswith("ema_")]]
    fig, ax = plt.subplots(figsize=(11, 5.5), layout="constrained")
    for column, color in zip(columns, SERIES_COLORS):
        ax.plot(df["date"], df[column], color=color, linewidth=2, label=column)
        # Label each line at its last value
        ax.annotate(
            column,
            (df["date"][-1], df[column][-1]),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            color="#444441",
        )

    ax.set_title(title, loc="left", color="#1f1f1e")
    ax.legend(loc="upper left", frameon=False)
    ax.grid(axis="y", color="#e5e4e0", linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(colors="#6b6a64", length=0)
    return fig


def main():

    # Connect to TWS or IB Gateway
    ib = IB()
    ib.connect(
        os.environ['IBG_HOST'],
        int(os.environ['IBG_PORT']),
        clientId=int(os.environ['IBG_CLIENT_ID']),
    )
    print("Connected")

    symbol = "VWCE.DE"

    df = fetch_bars(
        ib=ib,
        symbol=symbol,
        durationStr="1 Y",
        barSizeSetting="1 day"
    )
    df = clean_bars(df)
    df = add_ema(df, period=9)
    df = add_ema(df, period=30)
    print(df)

    # Disconnect when done
    ib.disconnect()

    plot_ema(df, title=symbol)
    plt.show()


if __name__ == "__main__":
    main()
