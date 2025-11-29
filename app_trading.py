import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone

# --- НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="Крипто Бот Pro", page_icon="⚡")

st.title("⚡ Крипто Сканер (Дані Coinbase)")
st.write("Дані в реальному часі через публічні API Coinbase")

# --- ПАРАМЕТРИ СТРАТЕГІЙ ---
# Символи Coinbase: "SOL-USD", "ETH-USD", "XRP-USD"
strategies = {
    "SOL-USD": {"sma": 100, "target_hour": 17, "sl": "2%"},
    "ETH-USD": {"sma": 50,  "target_hour": 17, "sl": "2%"},
    "XRP-USD": {"sma": 100, "target_hour": 17, "sl": "2%"}
}

# --- ФУНКЦІЯ ОТРИМАННЯ ДАНИХ (COINBASE) ---
def get_coinbase_data(symbol, granularity=3600):
    # Granularity 3600 = 1 година (в секундах)
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
    params = {"granularity": granularity}
    
    try:
        # Headers необхідні для імітації браузера
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Якщо є помилка, зупиняємо і показуємо повідомлення
        if response.status_code != 200:
            st.error(f"Помилка API Coinbase ({response.status_code}): {response.text}")
            return None
            
        data = response.json()
        
        # Coinbase повертає: [time, low, high, open, close, volume]
        df = pd.DataFrame(data, columns=['timestamp', 'Low', 'High', 'Open', 'Close', 'Volume'])
        
        # Конвертуємо часову мітку
        df['Date'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('Date', inplace=True)
        
        # Сортуємо від старого до нового
        df = df.sort_index()
        
        return df
        
    except Exception as e:
        st.error(f"Виняток при з'єднанні {symbol}: {e}")
        return None

# --- ПАНЕЛЬ КЕРУВАННЯ ---
st.sidebar.header("Панель Керування")
auto_refresh = st.sidebar.toggle("🔴 Live Режим (30с)", value=False)
manual_refresh = st.sidebar.button("🔄 Оновити Дані")

placeholder = st.empty()

def scansione_mercato():
    with placeholder.container():
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        
        st.info(f"🕒 Час UTC: {now_utc.strftime('%H:%M:%S')} (Свічка H{current_hour})")
        
        cols = st.columns(3)
        
        for i, (symbol, params) in enumerate(strategies.items()):
            col = cols[i]
            
            # Завантаження Даних
            data = get_coinbase_data(symbol)
            
            if data is not None and not data.empty:
                # Розрахунки
                sma_val = params['sma']
                data['SMA'] = data['Close'].rolling(window=sma_val).mean()
                
                last_price = data.iloc[-1]['Close']
                last_sma = data.iloc[-1]['SMA']
                
                # Логіка
                trend_ok = last_price > last_sma
                hour_ok = (current_hour == params['target_hour'])
                
                if last_sma > 0:
                    diff_percent = ((last_price - last_sma) / last_sma) * 100
                else:
                    diff_percent = 0
                
                # Візуалізація
                with col:
                    clean_name = symbol.replace("-USD", "")
                    st.subheader(f"{clean_name}")
                    
                    st.metric(
                        label="Ціна",
                        value=f"${last_price:.4f}",
                        delta=f"{diff_percent:.2f}% до SMA"
                    )
                    
                    st.caption(f"SMA {sma_val}: ${last_sma:.4f}")
                    
                    if hour_ok:
                        if trend_ok:
                            st.success(f"🚀 **КУПУВАТИ!**\nSL (Стоп): -{params['sl']}")
                        else:
                            st.warning("⛔ **ФЛЕТ**\n(Немає тренду)")
                    else:
                        hours_left = params['target_hour'] - current_hour
                        if hours_left < 0: hours_left += 24
                        st.info(f"⏳ **ЧЕКАЙТЕ** (-{hours_left}год)")
            else:
                col.warning(f"Дані недоступні для {symbol}")

# --- ЦИКЛ ВИКОНАННЯ ---
if auto_refresh:
    scansione_mercato()
    time.sleep(30)
    st.rerun()
else:
    scansione_mercato()

st.sidebar.markdown("---")
st.sidebar.caption("Дані в реальному часі надані Coinbase Public API.")
