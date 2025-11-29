import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Crypto Bot Direct", page_icon="⚡")

st.title("⚡ Crypto Scanner (Direct API)")
st.write("Connessione diretta ai server pubblici di Binance")

# --- PARAMETRI STRATEGIE ---
# Usiamo i simboli "raw" di Binance (senza slash)
strategies = {
    "SOLUSDT": {"name": "SOL/USDT", "sma": 100, "target_hour": 17, "sl": "2%"},
    "ETHUSDT": {"name": "ETH/USDT", "sma": 50,  "target_hour": 17, "sl": "2%"},
    "XRPUSDT": {"name": "XRP/USDT", "sma": 100, "target_hour": 17, "sl": "2%"}
}

# --- FUNZIONE DIRETTA (Senza librerie esterne) ---
def get_binance_data_direct(symbol, interval='1h', limit=200):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    
    try:
        # Chiamata HTTP diretta (come aprire una pagina web)
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Binance restituisce una lista di liste. La convertiamo in DataFrame.
        # Colonne: Open time, Open, High, Low, Close, Volume, ...
        df = pd.DataFrame(data, columns=[
            'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 
            'CloseTime', 'QuoteAssetVolume', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'
        ])
        
        # Pulizia e formattazione
        df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('Date', inplace=True)
        
        # Convertiamo le stringhe in numeri (Binance manda stringhe per precisione)
        cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[cols] = df[cols].apply(pd.to_numeric)
        
        return df[cols]
        
    except Exception as e:
        st.error(f"Errore connessione per {symbol}: {e}")
        return None

# --- INTERFACCIA ---
st.sidebar.header("Controllo")
auto_refresh = st.sidebar.toggle("🔴 Aggiornamento Automatico (30s)", value=False)
manual_refresh = st.sidebar.button("🔄 Aggiorna Adesso")

placeholder = st.empty()

def scansione_mercato():
    with placeholder.container():
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        
        st.info(f"🕒 Orario UTC: {now_utc.strftime('%H:%M:%S')} (Candela delle {current_hour}:00)")
        
        cols = st.columns(3)
        
        for i, (symbol, params) in enumerate(strategies.items()):
            col = cols[i]
            
            # Scarico Dati
            data = get_binance_data_direct(symbol)
            
            if data is not None:
                # Calcoli
                sma_val = params['sma']
                data['SMA'] = data['Close'].rolling(window=sma_val).mean()
                
                last_price = data.iloc[-1]['Close']
                last_sma = data.iloc[-1]['SMA']
                
                # Logica
                trend_ok = last_price > last_sma
                hour_ok = (current_hour == params['target_hour'])
                
                if last_sma > 0:
                    diff_percent = ((last_price - last_sma) / last_sma) * 100
                else:
                    diff_percent = 0
                
                # Visualizzazione
                with col:
                    st.subheader(params['name'])
                    st.metric(
                        label="Prezzo",
                        value=f"${last_price:.4f}",
                        delta=f"{diff_percent:.2f}% vs SMA"
                    )
                    
                    st.caption(f"SMA {sma_val}: ${last_sma:.4f}")
                    
                    if hour_ok:
                        if trend_ok:
                            st.success(f"🚀 **BUY**\nSL: -{params['sl']}")
                        else:
                            st.warning("⛔ **FLAT**")
                    else:
                        hours_left = params['target_hour'] - current_hour
                        if hours_left < 0: hours_left += 24
                        st.info(f"⏳ **ATTENDI** (-{hours_left}h)")

# --- LOOP ---
if auto_refresh:
    scansione_mercato()
    time.sleep(30)
    st.rerun()
else:
    scansione_mercato()

st.sidebar.markdown("---")
st.sidebar.caption("Dati diretti da Binance Public API.")
