import pandas as pd
import numpy as np
import ta  # Библиотека для технических индикаторов


# Функция для вычисления RSI
def calculate_rsi(df, window):
    df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=window).rsi()
    return df


# Функция для оценки сигналов RSI и расчет вероятности low+high
def evaluate_rsi_signals(df, buy_threshold, sell_threshold):
    results_rsi = {1: [], 2: [], 3: [], 4: [], 5: []}
    results_low_high = {1: [], 2: [], 3: [], 4: [], 5: []}

    for i in range(len(df) - 5):
        if pd.isna(df['RSI'].iloc[i]):
            continue

        current_price = df['close'].iloc[i]

        # Рассчитываем вероятность для базовых сценариев (low+high)
        for n in results_low_high.keys():
            future_high = df['high'].iloc[i + n]
            future_low = df['low'].iloc[i + n]
            if (future_high - current_price) / current_price >= 0.0006:
                results_low_high[n].append(1)  # Успешное превышение high
            else:
                results_low_high[n].append(0)

            if (current_price - future_low) / current_price >= 0.0006:
                results_low_high[n].append(1)  # Успешное превышение low
            else:
                results_low_high[n].append(0)

        # Проверка сигналов RSI
        if df['RSI'].iloc[i] < buy_threshold:  # Сигнал на покупку
            for n in results_rsi.keys():
                future_high = df['high'].iloc[i + n]
                if (future_high - current_price) / current_price >= 0.0006:
                    results_rsi[n].append(1)  # Успешный сигнал на покупку
                else:
                    results_rsi[n].append(0)  # Неудачный сигнал

        elif df['RSI'].iloc[i] > sell_threshold:  # Сигнал на продажу
            for n in results_rsi.keys():
                future_low = df['low'].iloc[i + n]
                if (current_price - future_low) / current_price >= 0.0006:
                    results_rsi[n].append(1)  # Успешный сигнал на продажу
                else:
                    results_rsi[n].append(0)  # Неудачный сигнал

    # Вероятности сигналов RSI и базовая вероятность (low+high)
    probabilities_rsi = {k: np.mean(v) * 100 for k, v in results_rsi.items() if len(v) > 0}
    probabilities_low_high = {k: np.mean(v) * 100 for k, v in results_low_high.items() if len(v) > 0}

    return probabilities_rsi, probabilities_low_high


# Основная функция для генерации статистики по различным параметрам RSI
def generate_rsi_statistics(df):
    stats = {}

    # Перебор различных окон для расчета RSI (например, от 5 до 30)
    rsi_windows = [14]

    # Пороговые значения для покупки и продажи
    buy_thresholds = [30]
    sell_thresholds = [70]

    for window in rsi_windows:
        df = calculate_rsi(df, window)

        for buy_threshold in buy_thresholds:
            for sell_threshold in sell_thresholds:
                key = f"RSI_window_{window}_buy_{buy_threshold}_sell_{sell_threshold}"
                rsi_probs, low_high_probs = evaluate_rsi_signals(df, buy_threshold, sell_threshold)

                # Подсчет привнесенной вероятности RSI
                advantage_rsi = {}
                for k in rsi_probs.keys():
                    if low_high_probs[k] > 0:  # Избегаем деления на ноль
                        advantage_rsi[k] = rsi_probs[k] / low_high_probs[k]
                    else:
                        advantage_rsi[k] = 0

                stats[key] = {
                    'RSI': rsi_probs,
                    'LowHigh': low_high_probs,
                    'Advantage_RSI': advantage_rsi
                }

    return stats


# Функция для отображения статистики в виде таблицы
def display_statistics_table(stats, timeframe):
    print(f"Timeframe: {timeframe}")
    print(f"{'Parameters':<40} {'1 Candle':<10} {'2 Candles':<10} {'3 Candles':<10} {'4 Candles':<10} {'5 Candles':<10}")
    print("=" * 75)

    for params, data in stats.items():
        print(f"RSI Probabilities for {params}")
        row_rsi = f"{'RSI':<40}"
        row_low_high = f"{'Low+High':<40}"
        row_advantage = f"{'Advantage RSI':<40}"

        for n in range(1, 6):
            row_rsi += f"{data['RSI'].get(n, 0):<10.2f} "
            row_low_high += f"{data['LowHigh'].get(n, 0):<10.2f} "
            row_advantage += f"{data['Advantage_RSI'].get(n, 0):<10.2f} "

        print(row_rsi)
        print(row_low_high)
        print(row_advantage)
        print("-" * 75)


# Список таймфреймов и их соответствующие файлы (добавьте свои файлы)
timeframes = {
    "1m": 'btc.csv',
    "3m": 'btc3m.csv', #укажите здесь названия своих датасетов в определенный таймфрейм
    "5m": 'btc5m.csv',
    "15m": 'btc15min.csv',
    "30m": 'btc30min.csv',
    "1h": 'btc1h.csv',
    "2h": 'btc2h.csv',
    "4h": 'btc4h.csv',
    "6h": 'btc6h.csv',
    "12h": 'btc12h.csv',
    "1d": 'btc1d.csv'
}

# Цикл по каждому таймфрейму
for timeframe, file_name in timeframes.items():
    try:
        # Загрузка данных для текущего таймфрейма
        df = pd.read_csv(file_name)

        # Генерация статистики по RSI для данного таймфрейма
        rsi_stats = generate_rsi_statistics(df)

        # Отображение статистики
        display_statistics_table(rsi_stats, timeframe)
    except FileNotFoundError:
        print(f"Файл {file_name} не найден.")
