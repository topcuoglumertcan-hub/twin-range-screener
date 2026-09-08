import datetime
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="BIST Günlük Sinyal Tarayıcı", layout="wide")

st.title("🚀 BIST Twin Range Günlük Sinyal Tarayıcı")
st.markdown("TradingView ile %100 matematiksel uyumlu kapanış bazlı **AL** ve **SAT** sinyali tarayıcısı.")

bist_all_stocks = [
    "THYAO.IS", "GARAN.IS", "EREGL.IS", "ASELS.IS", "KCHOL.IS", "AKBNK.IS",
    "ISCTR.IS", "BIMAS.IS", "PGSUS.IS", "SASA.IS", "TUPRS.IS", "PETKM.IS",
    "AKCNS.IS", "ALARK.IS", "ARCLK.IS", "ASTOR.IS", "ENKAI.IS", "FROTO.IS",
    "GESAN.IS", "GUBRF.IS", "KRDMD.IS", "ODAS.IS", "SAHOL.IS", "SISE.IS",
    "TAVHL.IS", "TOASO.IS", "YKBNK.IS"
]

col1, col2, col3 = st.columns(3)

with col1:
    selected_interval = "1d"
    st.info("Zaman Dilimi: **1 Gün (1d)**")

with col2:
    start_date = st.date_input("Başlangıç Tarihi", value=datetime.date.today() - datetime.timedelta(days=90))

with col3:
    end_date = st.date_input("Bitiş Tarihi", value=datetime.date.today())

selection_mode = st.radio("Hisse Seçim Yöntemi:", ["Özel Hisse Seç", "Tüm Listeyi Tara"], horizontal=True)

if selection_mode == "Özel Hisse Seç":
    selected_stocks = st.multiselect("Hisseler:", options=bist_all_stocks, default=["ASELS.IS"])
else:
    selected_stocks = bist_all_stocks

# TradingView'in ta.ema fonksiyonunun birebir Python karşılığı (SMA başlangıçlı)
def tv_ema(arr, length):
    alpha = 2.0 / (length + 1)
    res = np.zeros_like(arr, dtype=float)
    if len(arr) < length:
        return res
    res[length - 1] = np.mean(arr[:length])
    for i in range(length, len(arr)):
        res[i] = alpha * arr[i] + (1.0 - alpha) * res[i - 1]
    return res

def calculate_daily_signals(df, symbol, start_d, end_d):
    if df.empty or len(df) < 60:
        return pd.DataFrame()
    
    per1, mult1 = 27, 1.6
    per2, mult2 = 55, 2.0
    x = df['Close'].values
    
    diff = np.abs(np.diff(x, prepend=x[0]))
    
    wper1 = per1 * 2 - 1
    avrng1 = tv_ema(diff, per1)
    smrng1 = tv_ema(avrng1, wper1) * mult1

    wper2 = per2 * 2 - 1
    avrng2 = tv_ema(diff, per2)
    smrng2 = tv_ema(avrng2, wper2) * mult2

    smrng = (smrng1 + smrng2) / 2

    filt = np.zeros_like(x)
    f = x[0]
    for i in range(len(x)):
        val = x[i]
        r = smrng[i]
        if np.isnan(r): r = 0
        if i > 0:
            prev = filt[i-1]
            if val > prev:
                f = prev if (val - r < prev) else (val - r)
            else:
                f = prev if (val + r > prev) else (val + r)
        filt[i] = f

    df['TRF'] = filt
    df['Long'] = (df['Close'] > df['TRF']) & (df['Close'].shift(1) <= df['TRF'].shift(1))
    df['Short'] = (df['Close'] < df['TRF']) & (df['Close'].shift(1) >= df['TRF'].shift(1))

    signal_rows = []
    # Isınma payı bırakılarak tarama yapılır
    for i in range(60, len(df) - 1):
        idx = df.index[i]
        row = df.iloc[i]
        row_date = pd.to_datetime(idx).date()
        
        sig = None
        if row['Long']: sig = "🟢 BUY (AL)"
        elif row['Short']: sig = "🔴 SELL (SAT)"
        
        if sig:
            signal_rows.append({
                'Hisse': symbol.replace('.IS', ''),
                'Tarih': str(row_date),
                'Kapanış Fiyatı': round(row['Close'], 2),
                'Sinyal': sig
            })
            
    res_df = pd.DataFrame(signal_rows)
    if not res_df.empty:
        res_df['Tarih_dt'] = pd.to_datetime(res_df['Tarih']).dt.date
        tol_start = start_d - datetime.timedelta(days=1)
        tol_end = end_d + datetime.timedelta(days=1)
        res_df = res_df[(res_df['Tarih_dt'] >= tol_start) & (res_df['Tarih_dt'] <= tol_end)]
        res_df = res_df.drop(columns=['Tarih_dt'])
        
    return res_df

if st.button("Günlük Sinyalleri Taramayı Başlat 🔍", type="primary"):
    all_signals = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(selected_stocks)
    for idx, symbol in enumerate(selected_stocks):
        status_text.text(f"Taranıyor ({idx+1}/{total}): {symbol}...")
        try:
            df = yf.download(symbol, period="max", interval=selected_interval, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                sig_df = calculate_daily_signals(df, symbol, start_date, end_date)
                if not sig_df.empty:
                    all_signals.append(sig_df)
        except Exception as e:
            continue
        progress_bar.progress((idx + 1) / total)

    status_text.text("Tarama tamamlandı!")
    progress_bar.empty()

    if all_signals:
        final_df = pd.concat(all_signals, ignore_index=True)
        final_df = final_df.sort_values(by="Tarih", ascending=False)
        st.success(f"Seçilen aralıkta toplam **{len(final_df)}** adet sinyal bulundu:")
        st.dataframe(final_df, use_container_width=True)
    else:
        st.warning("Seçilen tarih aralığında sinyal bulunamadı.")
