import datetime
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="BIST Twin Range Toplu Tarayıcı", layout="wide")

st.title("🚀 BIST Twin Range Filter - Toplu Sinyal ve Durum Tarayıcı")
st.markdown("Tüm BIST hisselerini tek ekranda listeleyin, güncel durumlarını görün ve dışarı aktarın.")

# Genişletilmiş BIST Hisse Listesi (.IS uzantılı)
bist_all_stocks = [
    "THYAO.IS", "GARAN.IS", "EREGL.IS", "ASELS.IS", "KCHOL.IS", "AKBNK.IS",
    "ISCTR.IS", "BIMAS.IS", "PGSUS.IS", "SASA.IS", "TUPRS.IS", "PETKM.IS",
    "AKCNS.IS", "ALARK.IS", "ARCLK.IS", "ASTOR.IS", "ENKAI.IS", "FROTO.IS",
    "GESAN.IS", "GUBRF.IS", "KRDMD.IS", "ODAS.IS", "SAHOL.IS", "SISE.IS",
    "TAVHL.IS", "TOASO.IS", "YKBNK.IS", "BRSAN.IS", "FZLGY.IS"
]

col1, col2 = st.columns(2)
with col1:
    selection_mode = st.radio("Hisse Seçimi:", ["Tüm Listeyi Tara", "Özel Seçim Yap"], horizontal=True)

if selection_mode == "Özel Seçim Yap":
    selected_stocks = st.multiselect("Hisseleri Seçin:", options=bist_all_stocks, default=["THYAO.IS", "EREGL.IS", "ASELS.IS"])
else:
    selected_stocks = bist_all_stocks

# TradingView ile birebir uyumlu EMA (SMA başlangıçlı)
def tv_ema(arr, length):
    alpha = 2.0 / (length + 1)
    res = np.zeros_like(arr, dtype=float)
    if len(arr) < length:
        return res
    res[length - 1] = np.mean(arr[:length])
    for i in range(length, len(arr)):
        res[i] = alpha * arr[i] + (1.0 - alpha) * res[i - 1]
    return res

def analyze_stock(symbol):
    try:
        df = yf.download(symbol, period="max", interval="1d", progress=False)
        if df.empty or len(df) < 60:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
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
        df['Is_Long_Trend'] = df['Close'] > df['TRF']

        # Son durumu al
        current_trend = "AL" if df['Is_Long_Trend'].iloc[-2] else "SAT" # Canlı bar hariç kapanmış son gün
        
        # Son sinyal tarihini ve fiyatını bul
        sig_date = "-"
        sig_price = 0.0
        
        for i in range(len(df)-2, 59, -1):
            if df['Long'].iloc[i] or df['Short'].iloc[i]:
                sig_date = str(df.index[i].date())
                sig_price = round(df['Close'].iloc[i], 2)
                break

        return {
            'Hisse': symbol.replace('.IS', ''),
            'Güncel Fiyat': round(df['Close'].iloc[-2], 2),
            'Durum': current_trend,
            'Sinyal Tarihi': sig_date,
            'Sinyal Fiyatı': sig_price
        }
    except Exception as e:
        return None

if st.button("Toplu Taramayı Başlat 🔍", type="primary"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(selected_stocks)
    for idx, symbol in enumerate(selected_stocks):
        status_text.text(f"Taranıyor ({idx+1}/{total}): {symbol}...")
        res = analyze_stock(symbol)
        if res:
            results.append(res)
        progress_bar.progress((idx + 1) / total)

    status_text.text("Tarama tamamlandı!")
    progress_bar.empty()

    if results:
        res_df = pd.DataFrame(results)
        st.success(f"Toplam **{len(res_df)}** hisse başarıyla tarandı:")
        
        # Ekranda göster
        st.dataframe(res_df, use_container_width=True)

        # Dışarı aktarma (CSV İndir) butonu
        csv_data = res_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Listeyi CSV (Excel) Olarak İndir",
            data=csv_data,
            file_name="bist_twin_range_listesi.csv",
            mime="text/csv"
        )
    else:
        st.warning("Tarama sırasında veri alınamadı.")
