import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Crypto Bot Pro", page_icon="⚡")

st.title("⚡ Crypto Scanner (Dati Coinbase)")
st.write("Dati in tempo reale tramite API pubbliche Coinbase")

# --- PARAMETRI STRATEGIE ---
# Simboli Coinbase: "SOL-USD", "ETH-USD", "XRP-USD"
strategies = {
    "SOL-USD": {"sma": 100, "target_hour": 17, "sl": "2%"},
    "ETH-USD": {"sma": 50,  "target_hour": 17, "sl": "2%"},
    "XRP-USD": {"sma": 100, "target_hour": 17, "sl": "2%"}
}

# --- FUNZIONE DIRETTA COINBASE ---
def get_coinbase_data(symbol, granularity=3600):
    # Granularity 3600 = 1 ora (in secondi)
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
    params = {"granularity": granularity}
    
    try:
        # Headers necessari per simulare un browser ed evitare blocchi
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Se c'è un errore, ferma tutto e mostralo
        if response.status_code != 200:
            st.error(f"Errore API Coinbase ({response.status_code}): {response.text}")
            return None
            
        data = response.json()
        
        # Coinbase restituisce: [time, low, high, open, close, volume]
        # Attenzione all'ordine! Documentazione ufficiale: [time, low, high, open, close, volume]
        df = pd.DataFrame(data, columns=['timestamp', 'Low', 'High', 'Open', 'Close', 'Volume'])
        
        # Convertiamo timestamp
        df['Date'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('Date', inplace=True)
        
        # Ordiniamo dal più vecchio al più recente (Coinbase li dà al contrario)
        df = df.sort_index()
        
        return df
        
    except Exception as e:
        st.error(f"Eccezione connessione {symbol}: {e}")
        return None

# --- INTERFACCIA ---
st.sidebar.header("Pannello di Controllo")
auto_refresh = st.sidebar.toggle("🔴 Live Mode (30s)", value=False)
manual_refresh = st.sidebar.button("🔄 Aggiorna Dati")

placeholder = st.empty()

def scansione_mercato():
    with placeholder.container():
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        
        st.info(f"🕒 Orario UTC: {now_utc.strftime('%H:%M:%S')} (Candela H{current_hour})")
        
        cols = st.columns(3)
        
        for i, (symbol, params) in enumerate(strategies.items()):
            col = cols[i]
            
            # Scarico Dati
            data = get_coinbase_data(symbol)
            
            if data is not None and not data.empty:
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
                    clean_name = symbol.replace("-USD", "")
                    st.subheader(f"{clean_name}")
                    
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
            else:
                col.warning(f"Dati non disponibili per {symbol}")

# --- LOOP ---
if auto_refresh:
    scansione_mercato()
    time.sleep(30)
    st.rerun()
else:
    scansione_mercato()

st.sidebar.markdown("---")
st.sidebar.caption("Dati Real-Time forniti da Coinbase Public API.")
