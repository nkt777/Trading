import pandas as pd
import ccxt
from datetime import datetime, timedelta

# Доступные таймфреймы
available_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w', '1M']

# Функция для загрузки данных с Bybit
def load_data(bybit, symbol, timeframe, start, end, limit=1000):
    print(f"Loading data for {symbol} with timeframe {timeframe} from {start} to {end}...")
    since = int(start.timestamp() * 1000)
    end_timestamp = int(end.timestamp() * 1000)
    all_data = []

    while since < end_timestamp:
        ohlcv = bybit.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        if not ohlcv:
            break
        data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('timestamp', inplace=True)
        all_data.append(data)
        since = int(data.index[-1].timestamp() * 1000) + (int(timeframe[:-1]) * 60000)  # Переход на следующий интервал

    if not all_data:
        print(f"No data loaded for the period from {start} to {end}.")
        return pd.DataFrame()

    all_data = pd.concat(all_data)
    print(f"Data loaded. Shape: {all_data.shape}")
    return all_data

# Основной блок выполнения
if __name__ == "__main__":
    bybit = ccxt.bybit({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    # Получаем входные данные от пользователя
    symbol = input("Введите валютную пару (например, BTC/USDT или BTCUSDT, 'обязательно посмотрите как она выглядит на Bybit'): ").strip()

    timeframe = input(f"Введите таймфрейм из доступных ({', '.join(available_timeframes)}): ").strip()
    while timeframe not in available_timeframes:
        print("Неверный таймфрейм.")
        timeframe = input(f"Введите таймфрейм из доступных ({', '.join(available_timeframes)}): ").strip()

    output_file = input("Введите имя файла для сохранения данных (например, data.csv, '.csv' тоже нужно написать): ").strip()

    # Определение дат для загрузки
    start_date = datetime(2022, 7, 1)
    end_date = datetime.now()

    all_data = []
    while start_date < end_date:
        next_month = start_date + timedelta(days=31)
        if next_month > end_date:
            next_month = end_date
        data = load_data(bybit, symbol, timeframe, start_date, next_month)
        if not data.empty:
            all_data.append(data)
        start_date = next_month

    if all_data:
        df_new = pd.concat(all_data)

        # Удаляем дубликаты по timestamp, оставляя только последнюю запись
        df_new = df_new[~df_new.index.duplicated(keep='last')]

        df_new.dropna(inplace=True)
        df_new.to_csv(output_file)
        print(f"Данные успешно сохранены в {output_file}")
    else:
        print("Не удалось загрузить данные за указанный период.")
