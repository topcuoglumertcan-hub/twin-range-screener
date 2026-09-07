import datetime
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="BIST Twin Range Sinyal Tarayıcı", layout="wide")

st.title("🚀 BIST Twin Range Sinyal Tarayıcı")
st.markdown("Seçtiğiniz tarih aralığına ve periyoda göre AL/SAT sinyallerini listeleyin.")

bist_all_stocks = [
    "THYAO.IS", "GARAN.IS", "EREGL.IS", "ASELS.IS", "KCHOL.IS", "AKBNK.IS",
    "ISCTR.IS", "BIMAS.IS", "PGSUS.IS", "SASA.IS", "TUPRS.IS", "PETKM.IS"
]

col1, col2, col3 = st.columns(3)

with col1:
    interval_map = {
        "1 Saat (60m)": "60m",
        "2 Saat (120m)": "120m",
        "4 Saat (240m)": "240m",
        "1 Gün (1d)": "1d"
    }
    selected_label = st.selectbox("Zaman Dilimi", options=list(interval_map.keys()), index=0)
    selected_interval = interval_map[selected_label]

with col2:
    start_date = st.date_input("Başlangıç Tarihi", value=datetime.date.today() - datetime.timedelta(days=30))

with col3:
    end_date = st.date_input("Bitiş Tarihi", value=datetime.date.today())

selected_stocks = st.multiselect("Hisseler:", options=bist_all_stocks, default=["THYAO.IS"])

def calculate_signals(df, symbol, start_d, end_d):
    if df.empty or len(df) < 55:
        return pd.DataFrame()
    
    per1, mult1 = 27, 1.6
    per2, mult2 = 55, 2.0
    x = df['Close']

    wper1 = per1 * 2 - 1
    avrng1 = (x - x.shift(1)).abs().ewm(span=per1, adjust=False).mean()
    smrng1 = avrng1.ewm(span=wper1, adjust=False).mean() * mult1

    wper2 = per2 * 2 - 1
    avrng2 = (x - x.shift(1)).abs().ewm(span=per2, adjust=False).mean()
    smrng2 = avrng2.ewm(span=wper2, adjust=False).mean() * mult2

    smrng = (smrng1 + smrng2) / 2

    filt = []
    f = x.iloc[0]
    x_val = x.values
    smrng_val = smrng.values

    for i in range(len(x)):
        val = x_val[i]
        r = smrng_val[i]
        if pd.isna(r): r = 0
        if i > 0:
            prev = filt[-1]
            if val > prev:
                f = prev if (val - r < prev) else (val - r)
            else:
                f = prev if (val + r > prev) else (val + r)
        filt.append(f)

    df['TRF'] = filt
    df['Long'] = (df['Close'] > df['TRF']) & (df['Close'].shift(1) <= df['TRF'].shift(1))
    df['Short'] = (df['Close'] < df['TRF']) & (df['Close'].shift(1) >= df['TRF'].shift(1))

    signal_rows = []
    for idx, row in df.iterrows():
        # Tarih filtresini pandas index üzerinden tam uygula
        row_date = pd.to_datetime(idx).date()
        if start_d <= row_date <= end_d:
            sig = None
            if row['Long']: sig = "🟢 BUY (AL)"
            elif row['Short']: sig = "🔴 SELL (SAT)"
            
            if sig:
                signal_rows.append({
                    'Hisse': symbol.replace('.IS', ''),
                    'Tarih / Saat': str(idx),
                    'Fiyat': round(row['Close'], 2),
                    'Sinyal': sig
                })
    return pd.DataFrame(signal_rows)

if st.button("Taramayı Başlat 🔍", type="primary"):
    all_signals = []
    for symbol in selected_stocks:
        try:
            # Matematiksel hesap için yeterli geçmişi çekip, sonuçta kullanıcı tarihini filtreleyeceğiz
            df = yf.download(symbol, period="max", interval=selected_interval, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                sig_df = calculate_signals(df, symbol, start_date, end_date)
                if not sig_df.empty:
                    all_signals.append(sig_df)
        except Exception as e:
            st.error(f"Hata {symbol}: {e}")

    if all_signals:
        final_df = pd.concat(all_signals, ignore_index=True)
        final_df = final_df.sort_values(by="Tarih / Saat", ascending=False)
        st.success(f"Seçilen tarih aralığında toplam {len(final_df)} sinyal bulundu:")
        st.dataframe(final_df, use_container_width=True)
    else:
        st.warning("Seçilen tarih aralığında bu periyotta hiçbir AL/SAT sinyali bulunamadı.")
