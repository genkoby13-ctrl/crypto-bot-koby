import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone

# --- НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="Крипто Бот Pro", page_icon="💎")

st.title("💎 Крипто Сканер Pro (Smart Money)")
st.write("Стратегія: Тренд + Час + Об'єм (Дані Coinbase)")

# --- ПАРАМЕТРИ СТРАТЕГІЙ (Оновлено для SUI!) ---
strategies = {
    "SUI-USD": {"sma": 100, "target_hour": 8,  "sl": "2%"}, # <-- NUOVI PARAMETRI SUI
    "SOL-USD": {"sma": 100, "target_hour": 17, "sl": "2%"},
    "ETH-USD": {"sma": 50,  "target_hour": 17, "sl": "2%"},
    "XRP-USD": {"sma": 100, "target_hour": 17, "sl": "2%"}
}

# --- ФУНКЦІЯ ОТРИМАННЯ ДАНИХ (COINBASE) ---
def get_coinbase_data(symbol, granularity=3600):
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
    params = {"granularity": granularity}
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            st.error(f"Помилка API ({response.status_code})")
            return None
        
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'Low', 'High', 'Open', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('Date', inplace=True)
        df = df.sort_index()
        return df
    except Exception as e:
        st.error(f"Помилка: {e}")
        return None

# --- ПАНЕЛЬ КЕРУВАННЯ ---
st.sidebar.header("Меню")
auto_refresh = st.sidebar.toggle("🔴 Авто-оновлення (30с)", value=False)
if st.sidebar.button("🔄 Оновити зараз"):
    st.rerun()

placeholder = st.empty()

def scansione_mercato():
    with placeholder.container():
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        
        st.info(f"🕒 Час UTC: {now_utc.strftime('%H:%M:%S')} (Свічка H{current_hour})")
        
        # 4 колонкам (SUI, SOL, ETH, XRP)
        cols = st.columns(len(strategies))
        
        for i, (symbol, params) in enumerate(strategies.items()):
            col = cols[i]
            
            data = get_coinbase_data(symbol)
            
            if data is not None and not data.empty:
                # Індикатори
                sma_val = params['sma']
                data['SMA'] = data['Close'].rolling(window=sma_val).mean()
                data['Vol_SMA'] = data['Volume'].rolling(window=20).mean()
                
                # Останні дані
                last_candle = data.iloc[-2] # Остання закрита свічка
                current_price = data.iloc[-1]['Close']
                
                price_sma = last_candle['SMA']
                last_vol = last_candle['Volume']
                vol_sma = last_candle['Vol_SMA']
                
                # Логіка Сигналу
                trend_ok = current_price > price_sma
                volume_ok = last_vol > vol_sma
                hour_ok = (current_hour == params['target_hour'])
                
                diff_percent = ((current_price - price_sma) / price_sma) * 100
                vol_change = ((last_vol - vol_sma) / vol_sma) * 100
                
                # Візуалізація
                with col:
                    clean_name = symbol.replace("-USD", "")
                    st.subheader(f"{clean_name}")
                    
                    st.metric("Ціна", f"${current_price:.4f}", f"{diff_percent:.2f}% SMA")
                    
                    # Цільовий час
                    target_h = params['target_hour']
                    st.caption(f"Час входу: {target_h}:00 UTC")
                    
                    vol_icon = "🔥" if volume_ok else "❄️"
                    st.write(f"Об'єм: {vol_icon} ({vol_change:+.0f}%)")
                    
                    if hour_ok:
                        if trend_ok and volume_ok:
                            st.success(f"🚀 **КУПУВАТИ!**\n(Smart Money)")
                            st.caption(f"SL: -{params['sl']}")
                        elif trend_ok and not volume_ok:
                            st.warning("⚠️ **ОБЕРЕЖНО**\n(Слабкий об'єм)")
                        else:
                            st.error("⛔ **ФЛЕТ**")
                    else:
                        hours_left = params['target_hour'] - current_hour
                        if hours_left < 0: hours_left += 24
                        st.info(f"⏳ **ЧЕКАЙТЕ**\n(-{hours_left}год)")
            else:
                col.warning("No Data")

# --- ЦИКЛ ---
if auto_refresh:
    scansione_mercato()
    time.sleep(30)
    st.rerun()
else:
    scansione_mercato()

st.sidebar.markdown("---")
st.sidebar.caption("Стратегія: Вхід тільки якщо Об'єм > Середнього.")
