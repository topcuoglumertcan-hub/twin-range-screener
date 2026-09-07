import datetime
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BIST Twin Range Screener", layout="wide"
)

st.title("🚀 BIST Twin Range Filter Bulut Tarayıcı")
st.markdown(
    "Seçtiğiniz tarih ve zaman aralığına (periyoda) göre BIST hisselerini tarayın"
    " ve sinyal verenleri bulun."
)

# Örnek BIST Hisse Listesi (İstediğiniz kadar ekleyebilirsiniz)
default_stocks = [
    "THYAO.IS",
    "GARAN.IS",
    "EREGL.IS",
    "ASELS.IS",
    "KCHOL.IS",
    "AKBNK.IS",
    "ISCTR.IS",
    "BIMAS.IS",
    "PGSUS.IS",
    "SASA.IS",
    "HEKTS.IS",
    "TUPRS.IS",
    "PETKM.IS",
]

# Kullanıcı Arayüzü Seçimleri
col1, col2, col3 = st.columns(3)

with col1:
  selected_interval = st.selectbox(
      "Zaman Dilimi (Periyot)",
      options=["1d", "60m", "30m", "15m", "5m"],
      index=0,
      help=(
          "1d: Günlük, 60m: 1 Saat, 30m: 30 Dakika, 15m/5m: Kısa periyotlar"
      ),
  )

with col2:
  # yfinance kısıtlamalarına göre kısa periyotlarda tarih aralığı dinamikleşir
  default_start = datetime.date.today() - datetime.timedelta(days=60)
  start_date = st.date_input("Başlangıç Tarihi", value=default_start)

with col3:
  end_date = st.date_input(
      "Bitiş Tarihi", value=datetime.date.today()
  )

# Twin Range Hesaplama Fonksiyonu (Pine Script Mantığı)
def calculate_trf(df, per1=27, mult1=1.6, per2=55, mult2=2):
  if len(df) < per2:
    return df

  x = df['Close']

  # Fast smooth range
  wper1 = per1 * 2 - 1
  avrng1 = (x - x.shift(1)).abs().ewm(span=per1, adjust=False).mean()
  smrng1 = avrng1.ewm(span=wper1, adjust=False).mean() * mult1

  # Slow smooth range
  wper2 = per2 * 2 - 1
  avrng2 = (x - x.shift(1)).abs().ewm(span=per2, adjust=False).mean()
  smrng2 = avrng2.ewm(span=wper2, adjust=False).mean() * mult2

  smrng = (smrng1 + smrng2) / 2

  # Range Filter Logic
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
  # Sinyal Koşulları
  df['Long'] = (df['Close'] > df['TRF']) & (
      df['Close'].shift(1) <= df['TRF'].shift(1)
  )
  df['Short'] = (df['Close'] < df['TRF']) & (
      df['Close'].shift(1) >= df['TRF'].shift(1)
  )

  return df


if st.button("Taramayı Başlat 🔍", type="primary"):
  results = []
  progress_bar = st.progress(0)
  status_text = st.empty()

  total = len(default_stocks)
  for idx, symbol in enumerate(default_stocks):
    status_text.text(
        f"Taranıyor ({idx+1}/{total}): {symbol} verileri indiriliyor..."
    )
    try:
      # Veriyi Yahoo Finance'den çek
      df = yf.download(
          symbol,
          start=start_date,
          end=end_date,
          interval=selected_interval,
          progress=False,
      )
      if df.empty or len(df) < 55:
        continue

      # MultiIndex sütun düzeltmesi (yfinance güncellemeleri için önlem)
      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

      # TRF Hesapla
      df = calculate_trf(df)

      # Son muma veya seçilen son tarihe göre sinyal kontrolü
      last_row = df.iloc[-1]
      prev_row = df.iloc[-2] if len(df) > 1 else last_row

      signal = "Nötr"
      if last_row['Long']:
        signal = "🟢 BUY (AL)"
      elif last_row['Short']:
        signal = "🔴 SELL (SAT)"

      results.append({
          'Hisse': symbol.replace('.IS', ''),
          'Son Fiyat': round(last_row['Close'], 2),
          'Sinyal Durumu': signal,
          'Tarih/Saat': str(df.index[-1]),
      })
    except Exception as e:
      continue

    progress_bar.progress((idx + 1) / total)

  status_text.text("Tarama tamamlandı!")
  progress_bar.empty()

  if results:
    res_df = pd.DataFrame(results)
    st.success(f"Toplam {len(res_df)} hisse başarıyla tarandı.")
    st.dataframe(res_df, use_container_width=True)
  else:
    st.warning("Seçilen kriterlere uygun sonuç bulunamadı.")
