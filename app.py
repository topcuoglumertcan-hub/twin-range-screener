import pandas as pd
import numpy as np
import yfinance as yf

# 1. Kıvanç Özbilgiç - Twin Range Filter Orijinal Matematik Uyarlaması
def calculate_twin_range_filter(df, per1=27, mult1=1.6, per2=55, mult2=2.0):
    close = df['Close']
    
    # smoothrng fonksiyonu (Wilder / EMA tabanlı)
    def smoothrng(series, t, m):
        wper = int(t * 2 - 1)
        avrng = (series - series.shift(1)).abs().ewm(span=t, adjust=False).mean()
        return avrng.ewm(span=wper, adjust=False).mean() * m

    smrng1 = smoothrng(close, per1, mult1)
    smrng2 = smoothrng(close, per2, mult2)
    smrng = (smrng1 + smrng2) / 2

    # rngfilt ardışık döngü mantığı
    x = close.values
    r = smrng.values
    rngfilt = np.zeros(len(x))
    
    for i in range(len(x)):
        if i == 0:
            rngfilt[i] = x[i]
        else:
            prev = rngfilt[i-1]
            val = x[i]
            ri = r[i]
            if np.isnan(ri):
                rngfilt[i] = prev
            else:
                if val > prev:
                    rngfilt[i] = prev if (val - ri < prev) else (val - ri)
                else:
                    rngfilt[i] = prev if (val + ri > prev) else (val + ri)

    df['Filt'] = rngfilt
    str_val = df['Filt'] + smrng
    sts_val = df['Filt'] - smrng

    # FUB ve FLB ardışık hesaplama döngüsü
    fub = np.zeros(len(close))
    flb = np.zeros(len(close))
    c_val = close.values
    
    for i in range(len(close)):
        if i == 0:
            fub[i] = str_val.iloc[i] if not np.isnan(str_val.iloc[i]) else c_val[i]
            flb[i] = sts_val.iloc[i] if not np.isnan(sts_val.iloc[i]) else c_val[i]
        else:
            prev_fub = fub[i-1]
            prev_flb = flb[i-1]
            s_val = str_val.iloc[i]
            st_val = sts_val.iloc[i]
            c_prev = c_val[i-1]
            
            # FUB
            if np.isnan(s_val):
                fub[i] = prev_fub
            else:
                fub[i] = s_val if (s_val < prev_fub or c_prev > prev_fub) else prev_fub
                
            # FLB
            if np.isnan(st_val):
                flb[i] = prev_flb
            else:
                flb[i] = st_val if (st_val > prev_flb or c_prev < prev_flb) else prev_flb

    df['FUB'] = fub
    df['FLB'] = flb

    # TRF (Trend Range Filter) mantığı
    trf = np.zeros(len(close))
    for i in range(len(close)):
        if i == 0:
            trf[i] = fub[i]
        else:
            t_prev = trf[i-1]
            f_curr = fub[i]
            f_prev = fub[i-1]
            lb_curr = flb[i]
            lb_prev = flb[i-1]
            c_curr = c_val[i]
            
            if t_prev == f_prev and c_curr <= f_curr:
                trf[i] = f_curr
            elif t_prev == f_prev and c_curr >= f_curr:
                trf[i] = lb_curr
            elif t_prev == lb_prev and c_curr >= lb_curr:
                trf[i] = lb_curr
            elif t_prev == lb_prev and c_curr <= f_curr:
                trf[i] = f_curr
            else:
                trf[i] = f_curr

    df['TRF'] = trf
    df['Trend'] = np.where(close > df['TRF'], 'AL', 'SAT')
    
    # Kesişimler (Long / Short)
    df['Long'] = (close > df['TRF']) & (close.shift(1) <= df['TRF'].shift(1))
    df['Short'] = (close < df['TRF']) & (close.shift(1) >= df['TRF'].shift(1))
    
    return df

# 2. Tüm BIST Hisselerini Tarama Fonksiyonu
def scan_bist(ticker_list):
    results = []
    print(f"Toplam {len(ticker_list)} hisse taranıyor...")
    
    for symbol in ticker_list:
        try:
            yf_symbol = f"{symbol}.IS"
            df = yf.download(yf_symbol, period="6mo", interval="1d", progress=False)
            
            if df.empty or len(df) < 60:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = calculate_twin_range_filter(df)
            
            current_close = df['Close'].iloc[-1]
            current_trend = df['Trend'].iloc[-1]
            
            # Son sinyal tarihi ve fiyatı
            sig_date = "-"
            sig_price = "-"
            sig_type = "-"
            
            for i in range(len(df)-1, 0, -1):
                if df['Long'].iloc[i]:
                    sig_date = df.index[i].strftime('%Y-%m-%d')
                    sig_price = round(float(df['Close'].iloc[i]), 2)
                    sig_type = "AL"
                    break
                elif df['Short'].iloc[i]:
                    sig_date = df.index[i].strftime('%Y-%m-%d')
                    sig_price = round(float(df['Close'].iloc[i]), 2)
                    sig_type = "SAT"
                    break
            
            results.append({
                'Hisse': symbol,
                'Fiyat': round(float(current_close), 2),
                'Durum': current_trend,
                'Son Sinyal': sig_type,
                'Sinyal Tarihi': sig_date,
                'Sinyal Fiyatı': sig_price
            })
        except Exception as e:
            continue
            
    return pd.DataFrame(results)

# --- TEST LİSTESİ (Buraya 600 hissenin kodunu ekleyebilirsin) ---
bist_ornek = ['THYAO', 'ASELS', 'EREGL', 'KCHOL', 'GARAN', 'BIMAS', 'PGSUS', 'TUPRS', 'AKBNK', 'ISCTR']

# Taramayı çalıştır ve sonuçları göster
sonuc_df = scan_bist(bist_ornek)
print(sonuc_df.to_string(index=False))
import streamlit as st

st.title("BIST Twin Range Filter Tarayıcı")

# Eğer tarama bittiyse sonuçları ekrana basması için:
if 'sonuc_df' in locals() and not sonuc_df.empty:
    st.dataframe(sonuc_df, use_container_width=True)
else:
    st.info("Tarama yapılıyor veya liste bekleniyor...")
