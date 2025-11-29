import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Crypto Bot 3000", page_icon="🚀")

st.title("🚀 Black Chpok ")
st.write("KobyGenBot_v1")

# --- PARAMETRI STRATEGIE ---
strategies = {
    "SOL-USD": {"sma": 100, "target_hour": 17, "sl": "2%"},
    "ETH-USD": {"sma": 50,  "target_hour": 17, "sl": "2%"},
    "XRP-USD": {"sma": 100, "target_hour": 17, "sl": "2%"}
}

# --- PULSANTE DI SCANSIONE ---
if st.button("📡 SCANSIONA MERCATO ADESSO"):
    
    current_hour = datetime.now(timezone.utc).hour
    st.info(f"🕒 Orario attuale (UTC): {datetime.now(timezone.utc).strftime('%H:%M')}")
    
    # Barra di progresso
    progress_bar = st.progress(0)
    step = 0
    
    for ticker, params in strategies.items():
        step += 1
        progress_bar.progress(int(step / len(strategies) * 100))
        
        # 1. Scarico Dati
        try:
            data = yf.download(ticker, period="1mo", interval="1h", progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data = data.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index(level=1)
                
            # 2. Indicatori
            sma_val = params['sma']
            data['SMA'] = data['Close'].rolling(window=sma_val).mean()
            
            last_candle = data.iloc[-1]
            last_price = last_candle['Close']
            last_sma = last_candle['SMA']
            
            # 3. Logica
            trend_ok = last_price > last_sma
            hour_ok = (current_hour == params['target_hour'])
            
            # 4. Determinazione Colore e Segnale
            diff_percent = ((last_price - last_sma) / last_sma) * 100
            
            st.subheader(f"🪙 {ticker}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Prezzo", f"${last_price:.4f}")
            col2.metric(f"SMA {sma_val}", f"${last_sma:.4f}", f"{diff_percent:.2f}%")
            
            if hour_ok:
                if trend_ok:
                    st.success(f"🚀 BUY NOW! (Stop Loss: -{params['sl']})")
                else:
                    st.warning("⛔ FLAT (Ora giusta, Trend sbagliato)")
            else:
                hours_left = params['target_hour'] - current_hour
                if hours_left < 0: hours_left += 24
                st.info(f"⏳ ATTENDI (Mancano {hours_left}h)")
                
            st.divider()
            
        except Exception as e:
            st.error(f"Errore su {ticker}: {e}")
            
    progress_bar.empty()
    st.caption("Nota: I segnali sono validi solo alla chiusura della candela oraria delle 17:00 UTC.")