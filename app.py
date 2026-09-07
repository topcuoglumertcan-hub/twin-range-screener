import datetime
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="BIST Twin Range Detaylı Tarayıcı", layout="wide")

st.title("🚀 BIST Twin Range Geçmiş Sinyal ve Zaman Tarayıcı")
st.markdown(
    "Seçtiğiniz tarih aralığında ve periyotta (2 saatlik, 4 saatlik dahil) "
    "hisselerin ürettiği tüm **AL (Long)** ve **SAT (Short)** sinyallerini saat bazlı listeleyin."
)

# Borsa İstanbul Hisseleri Listesi
bist_all_stocks = [
    "ACSEL.IS", "ADEL.IS", "ADESE.IS", "ADGYO.IS", "AEFES.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS",
    "AKBNK.IS", "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFYE.IS", "AKGRT.IS", "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "AKSGY.IS",
    "ALARK.IS", "ALBRK.IS", "ALCAR.IS", "ALCTL.IS", "ALFAS.IS", "ALGYO.IS", "ALKIM.IS", "ALKLC.IS", "ALMAD.IS", "ALTNY.IS",
    "ANACM.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS", "ANSGR.IS", "ARASE.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARSAN.IS",
    "ASELS.IS", "ASTOR.IS", "ATAKP.IS", "ATATP.IS", "ATEKS.IS", "AVGYO.IS", "AVOD.IS", "AVPGY.IS", "AYCES.IS", "AYDEM.IS",
    "AYEN.IS", "AYES.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAKAB.IS", "BANVT.IS", "BARMA.IS", "BASCM.IS", "BASGZ.IS",
    "BERA.IS", "BEYAZ.IS", "BFREN.IS", "BIENY.IS", "BIGCH.IS", "BIMAS.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS", "BJKAS.IS",
    "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS", "BOBET.IS", "BORLS.IS", "BOSSA.IS", "BRISA.IS", "BRKS.IS", "BRYAT.IS",
    "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BURCE.IS", "BURVA.IS", "BVSAN.IS", "BYDNR.IS", "CANTE.IS", "CASA.IS", "CATES.IS",
    "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEOEM.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS",
    "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGI.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS",
    "DERHL.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS", "DGATE.IS", "DGGYO.IS", "DGNMO.IS", "DITAS.IS", "DMRGD.IS",
    "DMSAS.IS", "DNISI.IS", "DOAS.IS", "DOBUR.IS", "DOFER.IS", "DOGUB.IS", "DOHOL.IS", "DOKTA.IS", "EBEBK.IS", "ECILC.IS",
    "ECZYT.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS", "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKOS.IS", "EKSUN.IS",
    "ELITE.IS", "EMKEL.IS", "ENERY.IS", "ENKAI.IS", "ENSRI.IS", "EPLAS.IS", "ERBOS.IS", "ERCB.IS", "EREGL.IS", "ERSU.IS",
    "ESCAR.IS", "ESEN.IS", "ETILR.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FADE.IS", "FENER.IS", "FLAP.IS", "FMIZP.IS",
    "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "FROTO.IS", "GARAN.IS", "GARFA.IS", "GEDIK.IS", "GEDZA.IS", "GENIL.IS",
    "GENTS.IS", "GEREL.IS", "GESAN.IS", "GLBMD.IS", "GLCVY.IS", "GLRYH.IS", "GLYHO.IS", "GMTAS.IS", "GOKNR.IS", "GOLTS.IS",
    "GOODY.IS", "GOZDE.IS", "GRNYO.IS", "GRSEL.IS", "GSDDE.IS", "GSDHO.IS", "GSRAY.IS", "GUBRF.IS", "GWIND.IS", "GZNMI.IS",
    "HALKB.IS", "HATEK.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS", "HUBVC.IS", "HUNER.IS",
    "HURGZ.IS", "ICBCT.IS", "IDEAS.IS", "IDGYO.IS", "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "IMASM.IS",
    "INDES.IS", "INFO.IS", "INGRM.IS", "INTEM.IS", "INVEO.IS", "INVES.IS", "ISATR.IS", "ISBIR.IS", "ISCEN.IS", "ISCTR.IS",
    "ISDMR.IS", "ISFIN.IS", "ISGSY.IS", "ISGYO.IS", "ISKPL.IS", "ISKUR.IS", "ISMEN.IS", "ITTFH.IS", "IZENR.IS", "IZFAS.IS",
    "IZINV.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KAYSE.IS", "KBORU.IS",
    "KCAER.IS", "KCHOL.IS", "KENT.IS", "KERVT.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLKIM.IS", "KLSYN.IS",
    "KLVHL.IS", "KMPUR.IS", "KNFRT.IS", "KONTR.IS", "KONYA.IS", "KOPOL.IS", "KORDS.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS",
    "KRDMB.IS", "KRDMD.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS", "LIDFA.IS",
    "LKMNH.IS", "LOGO.IS", "LUKSK.IS", "MAALT.IS", "MAKTK.IS", "MANAS.IS", "MARKA.IS", "MARTI.IS", "MAVI.IS", "MEDTR.IS",
    "MEGAP.IS", "MEKAG.IS", "MENPA.IS", "MERCN.IS", "MERIT.IS", "MERKO.IS", "METUR.IS", "MGROS.IS", "MIATK.IS", "MHRGY.IS",
    "MMCAS.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MUDO.IS",
    "MZHLD.IS", "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS", "NUHCM.IS", "OBAMS.IS", "OBASE.IS",
    "ODAS.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OTTO.IS", "OYAKC.IS", "OYLUM.IS",
    "OYYAT.IS", "OZATD.IS", "OZGYO.IS", "OZKGY.IS", "OZLRD.IS", "OZRDN.IS", "PAKMD.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS",
    "PCILT.IS", "PEKGY.IS", "PENGD.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PINSU.IS", "PKART.IS", "PKENT.IS",
    "PNSUT.IS", "POLHO.IS", "POLTK.IS", "PRKME.IS", "PRZMA.IS", "PSDTC.IS", "QNBFB.IS", "QNBFL.IS", "QUAGR.IS", "RALYH.IS",
    "REEDR.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS", "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAHOL.IS", "SANKO.IS",
    "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGMN.IS", "SEGYO.IS", "SEKFK.IS", "SEKUR.IS", "SELEC.IS", "SELGD.IS",
    "SELVA.IS", "SEYKM.IS", "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SMART.IS", "SMRTG.IS", "SOKM.IS", "SONME.IS",
    "SRVGY.IS", "SUMAS.IS", "SUNTK.IS", "SUWEN.IS", "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS",
    "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TETMT.IS", "TEZOL.IS", "TGSAS.IS", "THYAO.IS", "TKFEN.IS", "TKNSA.IS", "TMPOL.IS",
    "TMSN.IS", "TOASO.IS", "TRGYO.IS", "TRILC.IS", "TSKB.IS", "TTKOM.IS", "TUPRS.IS", "ULKER.IS", "ULUUN.IS", "VAKBN.IS",
    "YKBNK.IS", "ZOREN.IS"
]

bist_all_stocks = sorted(list(set([s.strip() for s in bist_all_stocks if len(s.strip()) > 3])))

# Arayüz Parametreleri
col1, col2, col3 = st.columns(3)

with col1:
    # 2 saat (120m) ve 4 saat (240m) eklenmiştir
    interval_map = {
        "1 Dakika (1m)": "1m",
        "5 Dakika (5m)": "5m",
        "15 Dakika (15m)": "15m",
        "30 Dakika (30m)": "30m",
        "1 Saat (60m)": "60m",
        "2 Saat (120m)": "120m",
        "4 Saat (240m)": "240m",
        "1 Gün (1d)": "1d"
    }
    selected_label = st.selectbox("Zaman Dilimi (Periyot)", options=list(interval_map.keys()), index=4)
    selected_interval = interval_map[selected_label]

with col2:
    default_start = datetime.date.today() - datetime.timedelta(days=7)
    start_date = st.date_input("Başlangıç Tarihi", value=default_start)

with col3:
    end_date = st.date_input("Bitiş Tarihi", value=datetime.date.today())

st.markdown("---")
selection_mode = st.radio("Hisse Seçim Yöntemi:", ["Özel Hisse Seç", "Tüm BIST Piyasasını Tara"], horizontal=True)

if selection_mode == "Özel Hisse Seç":
    selected_stocks = st.multiselect(
        "Taranmasını istediğiniz hisseleri seçin:",
        options=bist_all_stocks,
        default=["THYAO.IS", "GARAN.IS", "EREGL.IS"]
    )
else:
    selected_stocks = bist_all_stocks

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

if st.button("Taramayı Başlat 🔍", type="primary"):
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
            final_df = final_df.sort_values(by="Tarih / Saat", ascending=False)
            st.success(f"Seçilen aralıkta toplam **{len(final_df)}** adet sinyal tespit edildi.")
            st.dataframe(final_df, use_container_width=True)
        else:
            st.warning("Seçilen tarih aralığında ve periyotta hiçbir AL/SAT sinyali bulunamadı.")
