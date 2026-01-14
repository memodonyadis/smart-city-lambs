import random
import gspread
import smtplib
from dataclasses import dataclass
from typing import Dict, Tuple, List
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from email.message import EmailMessage


GOOGLE_SHEET_ADI = "trafik-demo"
GEMINI_API_KEY = "AIzaSyBhOaFtBkMXsjXZd3wy762koFXvFT1wAqQ"
GMAIL_ADRES = "memodonyadis@gmail.com"
GMAIL_UYGULAMA_SIFRESI = "jedh gpez xomv kvom"
ALICI_MAIL = "hamosemina@gmail.com"

random.seed(42)
KOLLAR = ["K", "D", "G", "B"]


@dataclass
class KavsakDurumu:
    kuyruk: Dict[str, float]



def sinirla(x, alt, ust): return max(alt, min(ust, x))


def senaryo_gelisleri(t: int, senaryo: str):
    temel = {"K": 0.08, "D": 0.06, "G": 0.08, "B": 0.06}
    if senaryo == "sabah_yogunlugu":
        temel["K"], temel["G"] = 0.18, 0.18
    elif senaryo == "aksam_yogunlugu":
        temel["D"], temel["B"] = 0.18, 0.18
    elif senaryo == "olay_durumu" and 300 <= t <= 600:
        temel["D"] = 0.25
    return {k: max(0.0, v + random.uniform(-0.01, 0.01)) for k, v in temel.items()}


def kavsak_simulasyonu(yontem, senaryo, T=900):
    durum = KavsakDurumu(kuyruk={k: 0.0 for k in KOLLAR})
    toplam_bekleme = 0.0
    for t in range(T):
        gelis = senaryo_gelisleri(t, senaryo)
        for k in KOLLAR: durum.kuyruk[k] += gelis[k]
        toplam_bekleme += sum(durum.kuyruk.values())
        for k in KOLLAR: durum.kuyruk[k] = max(0.0, durum.kuyruk[k] - 0.35)
    return {"toplam_bekleme": toplam_bekleme}



def islemi_tamamla(rapor_metni):
    print("\n--- Analiz ve Gönderim Başlatıldı ---")
    try:

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client_sh = gspread.authorize(creds)
        sheet = client_sh.open(GOOGLE_SHEET_ADI).sheet1
        sheet.append_row([rapor_metni])
        print("✅ 1. Veriler Sheets'e eklendi.")


        client_ai = genai.Client(api_key=GEMINI_API_KEY)
        response = client_ai.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Bu trafik verilerini analiz et, anomali var mı belirt:\n{rapor_metni}"
        )
        analiz = response.text
        print("✅ 2. AI Analizi (Gemini 2.5) tamamlandı.")


        msg = EmailMessage()
        msg.set_content(f"Sistem Raporu:\n\n{analiz}")
        msg['Subject'] = 'Trafik Sistemi Otomatik Raporu'
        msg['From'] = GMAIL_ADRES
        msg['To'] = ALICI_MAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_ADRES, GMAIL_UYGULAMA_SIFRESI)
            smtp.send_message(msg)
        print("✅ 3. Rapor mail adresine gönderildi!")

    except Exception as e:
        print(f"❌ Entegrasyon Hatası: {e}")


def calistir():
    senaryolar = ["sabah_yogunlugu", "aksam_yogunlugu", "olay_durumu"]
    rapor_buffer = "=== TRAFİK ANALİZ SONUÇLARI ===\n"
    for s in senaryolar:
        res = kavsak_simulasyonu("sabit", s)
        satir = f"Senaryo: {s.title()} | Bekleme: {int(res['toplam_bekleme'])} sn\n"
        print(satir.strip())
        rapor_buffer += satir

    islemi_tamamla(rapor_buffer)


if __name__ == "__main__":
    calistir()