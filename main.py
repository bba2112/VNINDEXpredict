from sqlalchemy import BigInteger, DateTime, Float, String, create_engine, text
from vnstock import Listing, Quote, register_user
import pandas as pd
import time
import os
register_user(api_key="vnstock_7eacb460af93237c84ccc9f00a33e729")



# SQL Server config
SQL_SERVER = "localhost"
SQL_DB = "StockDB"
TABLE_NAME = "stocks"

# Data range
START_DATE = "2024-01-01"
END_DATE = pd.Timestamp.today().strftime("%Y-%m-%d")


# 1) Lay danh sach ma HOSE
listing = Listing(source="VCI")
hose_df = listing.symbols_by_exchange(exchange="HOSE")
symbols = hose_df["symbol"].dropna().astype(str).unique().tolist()

print("So ma HOSE:", len(hose_df))
print(hose_df.head())


# 2) Kiem tra ket noi SQL Server (chua insert du lieu)
engine = create_engine(
    f"mssql+pyodbc://@{SQL_SERVER}/{SQL_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1 AS ok"))
    print("SQL connected:", result.scalar())


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def run_once(engine, symbols):
    BATCH_SLEEP_SECONDS = 270
    end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
    BATCH_SIZE = 19
    inserted_total = 0
    batch_count = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx, batch_symbols in enumerate(chunked(symbols, BATCH_SIZE), start=66): #batch hien tai 66
        print(f"\n=== Batch {batch_idx}/{batch_count}: {len(batch_symbols)} ma ===")

        frames = []
        for symbol in batch_symbols:
            try:
                quote = Quote(symbol=symbol, source="VCI")
                raw = quote.history(start=START_DATE, end=end_date, interval="1D")
                if raw is None or raw.empty:
                    print(f"{symbol}: khong co du lieu")
                    continue

                df = raw[["time", "open", "high", "low", "close", "volume"]].copy()
                df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.normalize()
                for col in ["open", "high", "low", "close"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
                df["symbol"] = symbol

                df = df[["time", "open", "high", "low", "close", "volume", "symbol"]]
                df = df.dropna(subset=["time"])
                frames.append(df)

                print(f"{symbol}: {len(df)} rows")
            except Exception as exc:
                print(f"{symbol}: loi -> {exc}")

        if not frames:
            print("Batch nay khong co du lieu de insert.")
            if batch_idx < batch_count:
                print(f"Nghi {BATCH_SLEEP_SECONDS} giay truoc batch tiep theo...")
                time.sleep(BATCH_SLEEP_SECONDS)
            continue

        batch_data = pd.concat(frames, ignore_index=True)
        batch_data["time"] = pd.to_datetime(batch_data["time"], errors="coerce").dt.normalize()
        batch_data = batch_data.drop_duplicates(subset=["symbol", "time"])

        symbol_params = {f"s{i}": s for i, s in enumerate(batch_symbols)}
        in_clause = ", ".join(f":s{i}" for i in range(len(batch_symbols)))

        existing_query = text(
            f"""
            SELECT [symbol], CAST([time] AS date) AS [time]
            FROM dbo.{TABLE_NAME}
            WHERE [symbol] IN ({in_clause})
              AND [time] >= :start_date
              AND [time] <= :end_date
            """
        )

        existing_keys = pd.read_sql(
            existing_query,
            engine,
            params={
                **symbol_params,
                "start_date": pd.to_datetime(START_DATE),
                "end_date": pd.to_datetime(end_date),
            },
        )

        if not existing_keys.empty:
            existing_keys["time"] = pd.to_datetime(existing_keys["time"], errors="coerce").dt.normalize()
            merged = batch_data.merge(
                existing_keys.drop_duplicates(subset=["symbol", "time"]).assign(_exists=1),
                on=["symbol", "time"],
                how="left",
            )
            to_insert = merged[merged["_exists"].isna()].drop(columns=["_exists"])
        else:
            to_insert = batch_data

        to_insert = to_insert.drop_duplicates(subset=["symbol", "time"])

        if to_insert.empty:
            print("Batch nay khong co dong moi (da ton tai).")
            if batch_idx < batch_count:
                print(f"Nghi {BATCH_SLEEP_SECONDS} giay truoc batch tiep theo...")
                time.sleep(BATCH_SLEEP_SECONDS)
            continue

        to_insert.to_sql(
            TABLE_NAME,
            engine,
            if_exists="append",
            index=False,
            dtype={
                "time": DateTime(),
                "open": Float(),
                "high": Float(),
                "low": Float(),
                "close": Float(),
                "volume": BigInteger(),
                "symbol": String(50),
            },
            chunksize=200,
        )

        inserted_total += len(to_insert)
        print(f"Batch {batch_idx}: da insert {len(to_insert)} dong moi")

        if batch_idx < batch_count:
            print(f"Nghi {BATCH_SLEEP_SECONDS} giay truoc batch tiep theo...")
            time.sleep(BATCH_SLEEP_SECONDS)

    print(f"\nTong so dong moi da insert: {inserted_total}")


SLEEP_SECONDS = 90

while True:
    print("\n========== RUN START ==========")
    try:
        run_once(engine, symbols)
    except Exception as exc:
        print(f"Run loi: {exc}")
    print(f"Sleep {SLEEP_SECONDS} giay...\n")
    time.sleep(SLEEP_SECONDS)