import datetime
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="BIST Twin Range Detaylı Sinyal Tarayıcı", layout="wide")

st.title("🚀 BIST Twin Range Geçmiş Sinyal ve Zaman Tarayıcısı")
st.markdown(
    "Seçtiğiniz tarih aralığında ve saat periyodunda (1s, 4s, 5dk vb.) "
    "hisselerin ürettiği tüm **AL (Long)** ve **SAT (Short)** sinyallerini saat bazlı listeleyin."
)

# 1. BIST Hisse Havuzu Tanımları
bist_all_stocks = [
    "THYAO.IS", "GARAN.IS", "EREGL.IS", "ASELS.IS", "KCHOL.IS", "AKBNK.IS",
    "ISCTR.IS", "BIMAS.IS", "PGSUS.IS", "SASA.IS", "HEKTS.IS", "TUPRS.IS",
    "PETKM.IS", "AKCNS.IS", "ALARK.IS", "ARCLK.IS", "ASTOR.IS", "ENKAI.IS",
    "FOOLS", "FROTO.IS", "GESAN.IS", "GUBRF.IS", "KRDMD.IS", "ODAS.IS",
    "SAHOL.IS", "SISE.IS", "TAVHL.IS", "TOASO.IS", "YKBNK.IS"
]

# Kullanıcı Arayüzü Parametreleri
col1, col2, col3 = st.columns(3)

with col1:
    # Zaman periyodu seçimi (TradingView menünüzdeki dakikalık/saatlik aralıklar)
    interval_map = {
        "1 Dakika (1m)": "1m",
        "5 Dakika (5m)": "5m",
        "15 Dakika (15m)": "15m",
        "30 Dakika (30m)": "30m",
        "1 Saat (60m)": "60m",
        "1 Gün (1d)": "1d"
    }
    selected_label = st.selectbox("Zaman Dilimi (Periyot)", options=list(interval_map.keys()), index=4)
    selected_interval = interval_map[selected_label]

with col2:
    default_start = datetime.date.today() - datetime.timedelta(days=14)
    start_date = st.date_input("Başlangıç Tarihi", value=default_start)

with col3:
    end_date = st.date_input("Bitiş Tarihi", value=datetime.date.today())

# Hisse Seçim Parametresi (İstediğinizi seçin veya tümünü seçin)
st.markdown("---")
selection_mode = st.radio("Hisse Seçim Yöntemi:", ["Özel Hisse Seç", "Tüm Listeyi Tara (BIST)"], horizontal=True)

if selection_mode == "Özel Hisse Seç":
    selected_stocks = st.multiselect(
        "Taranmasını istediğiniz hisseleri seçin:",
        options=bist_all_stocks,
        default=["THYAO.IS", "GARAN.IS", "EREGL.IS"]
    )
else:
    selected_stocks = bist_all_stocks

# Twin Range Hesaplama Fonksiyonu (Tüm geçmiş mumlardaki kesişimleri yakalar)
def calculate_all_signals(df, symbol):
    if len(df) < 55:
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
        if pd.isna(r):
            r = 0
        if i > 0:
            prev = filt[-1]
            if val > prev:
                f = prev if (val - r < prev) else (val - r)
            else:
                f = prev if (val + r > prev) else (val + r)
        filt.append(f)

    df['TRF'] = filt
    
    # Tüm kesişim (crossover/crossunder) noktalarını tespit et
    df['Long'] = (df['Close'] > df['TRF']) & (df['Close'].shift(1) <= df['TRF'].shift(1))
    df['Short'] = (df['Close'] < df['TRF']) & (df['Close'].shift(1) >= df['TRF'].shift(1))

    signal_rows = []
    for idx, row in df.iterrows():
        sig_type = None
        if row['Long']:
            sig_type = "🟢 BUY (AL)"
        elif row['Short']:
            sig_type = "🔴 SELL (SAT)"
            
        if sig_type:
            signal_rows.append({
                'Hisse': symbol.replace('.IS', ''),
                'Tarih / Saat': str(idx),
                'Fiyat': round(row['Close'], 2),
                'Sinyal': sig_type
            })
            
    return pd.DataFrame(signal_rows)

if st.button("Geçmiş Sinyalleri Taramayı Başlat 🔍", type="primary"):
    if not selected_stocks:
        st.warning("Lütfen en az bir hisse seçin!")
    else:
        all_signals = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        total = len(selected_stocks)
        for idx, symbol in enumerate(selected_stocks):
            status_text.text(f"Taranıyor ({idx+1}/{total}): {symbol}...")
            try:
                df = yf.download(symbol, start=start_date, end=end_date, interval=selected_interval, progress=False)
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    sig_df = calculate_all_signals(df, symbol)
                    if not sig_df.empty:
                        all_signals.append(sig_df)
            except Exception as e:
                continue
            
            progress_bar.progress((idx + 1) / total)

        status_text.text("Tarama tamamlandı!")
        progress_bar.empty()

        if all_signals:
            final_df = pd.concat(all_signals, ignore_index=True)
            # Tarihe göre ters sırala (en güncel en üstte)
            final_df = final_df.sort_values(by="Tarih / Saat", ascending=False)
            st.success(f"Seçilen aralıkta toplam **{len(final_df)}** adet sinyal (AL/SAT) tespit edildi.")
            st.dataframe(final_df, use_container_width=True)
        else:
            st.warning("Seçilen tarih aralığında ve periyotta hiçbir AL/SAT sinyali bulunamadı.")
