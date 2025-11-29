import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="KobyGenBot Real-Time", page_icon="⚡")

st.title("⚡ Crypto Scanner (Dati Binance)")
st.write("exchange n.1 al mondo")

# --- PARAMETRI STRATEGIE ---
# Nota: Su Binance i simboli sono "COIN/USDT"
strategies = {
    "SOL/USDT": {"sma": 100, "target_hour": 17, "sl": "2%"},
    "ETH/USDT": {"sma": 50,  "target_hour": 17, "sl": "2%"},
    "XRP/USDT": {"sma": 100, "target_hour": 17, "sl": "2%"}
}

# --- FUNZIONE PER SCARICARE DA BINANCE ---
# Questa funzione si collega a Binance e scarica le ultime candele
def get_binance_data(symbol, timeframe='1h', limit=200):
    try:
        exchange = ccxt.binance()
        # Scarica le candele (Open, High, Low, Close, Volume)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Trasforma i dati grezzi in una Tabella leggibile (DataFrame)
        data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        data['Date'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('Date', inplace=True)
        return data
    except Exception as e:
        return None

# --- BARRA LATERALE (CONTROLLI) ---
st.sidebar.header("Pannello di Controllo")
auto_refresh = st.sidebar.toggle("🔴 Aggiornamento Automatico (30s)", value=False)
manual_refresh = st.sidebar.button("🔄 Aggiorna Adesso")

# Contenitore vuoto che verrà riempito dai dati
placeholder = st.empty()

def scansione_mercato():
    with placeholder.container():
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        
        st.info(f"🕒 Orario UTC: {now_utc.strftime('%H:%M:%S')} (Candela delle {current_hour}:00)")
        
        # Creiamo 3 colonne per visualizzare le 3 crypto affiancate
        cols = st.columns(3)
        
        for i, (ticker, params) in enumerate(strategies.items()):
            col = cols[i]
            
            # 1. Scarico Dati da Binance
            data = get_binance_data(ticker)
            
            if data is not None:
                # 2. Calcolo Indicatori
                sma_val = params['sma']
                data['SMA'] = data['Close'].rolling(window=sma_val).mean()
                
                # Ultima candela CHIUSA (per la media) e prezzo ATTUALE (real-time)
                # Nota: .iloc[-1] è la candela corrente (ancora aperta), .iloc[-2] è l'ultima chiusa
                last_price = data.iloc[-1]['Close'] 
                last_sma = data.iloc[-1]['SMA']
                
                # 3. Logica Trading
                trend_ok = last_price > last_sma
                hour_ok = (current_hour == params['target_hour'])
                
                # Calcolo distanza percentuale dalla media
                if last_sma > 0:
                    diff_percent = ((last_price - last_sma) / last_sma) * 100
                else:
                    diff_percent = 0
                
                # Visualizzazione nella colonna
                with col:
                    # Nome pulito (togliamo /USDT per estetica)
                    clean_name = ticker.replace("/USDT", "")
                    st.subheader(f"{clean_name}")
                    
                    # Colore dinamico del prezzo (Verde se sopra media, Rosso se sotto)
                    st.metric(
                        label="Prezzo Attuale",
                        value=f"${last_price:.4f}",
                        delta=f"{diff_percent:.2f}% vs SMA"
                    )
                    
                    st.write(f"SMA {sma_val}: **${last_sma:.4f}**")
                    
                    if hour_ok:
                        if trend_ok:
                            st.success(f"🚀 **BUY NOW!**\nSL: -{params['sl']}")
                        else:
                            st.warning("⛔ **FLAT**\n(No Trend)")
                    else:
                        hours_left = params['target_hour'] - current_hour
                        if hours_left < 0: hours_left += 24
                        st.info(f"⏳ **ATTENDI**\n(-{hours_left}h)")
            else:
                col.error(f"Errore connessione Binance per {ticker}")

# --- ESECUZIONE ---
if auto_refresh:
    scansione_mercato()
    time.sleep(30) # Aggiorna ogni 30 secondi (più veloce di prima)
    st.rerun()
else:
    scansione_mercato()

st.sidebar.markdown("---")
st.sidebar.caption("Dati forniti in tempo reale da Binance API (via ccxt).")
