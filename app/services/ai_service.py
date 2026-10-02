# -*- coding: utf-8 -*-
"""
Game Style Arts - Yapay Zeka Servisi (Groq)

AKILLI MODEL SEÇİMİ - ÖZET
--------------------------
1. Groq'taki modeller saatte bir kez listelenir (her istekte değil -> daha hızlı).
2. Sohbet edemeyen veya işimize yaramayan modeller elenir
   (ses, görüntü, güvenlik, TTS ve Arapça'ya özel 'allam' gibi).
3. Kalan her modele bir PUAN verilir:
     - Kalite puanı      (bilinen modeller tablosundan)
     - Hız puanı         (yoğun saatte daha önemli)
     - Token/kota sağlığı (Groq'un döndürdüğü kalan token/istek bilgisi)
     - Bağlam uyumu      (uzun sohbet geçmişi modele sığıyor mu?)
4. İstek ZAMANINA göre ağırlıklar değişir (Europe/Istanbul saati):
     - Gece (00-08)      -> en kaliteli model önde
     - Gündüz (08-18)    -> kalite ağırlıklı, dengeli
     - Akşam yoğun (18-24) -> hızlı ve kotası bol modeller önde
5. En yüksek puanlı İLK 5 model sırayla denenir.
   Limit (429) yiyen model, Groq'un söylediği süre kadar "soğumaya" alınır.
"""

import os
import re
import time
import threading
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Istanbul")
except Exception:  # zoneinfo/tzdata yoksa sunucu saatine düş
    _TZ = None

from groq import Groq

from config import config_dict


class AIServiceError(Exception):
    pass


# ---------------------------------------------------------------------------
# MODEL BİLGİ TABLOSU
# (desen, kalite 0-100, hız 0-100, bağlam penceresi token, düşünen model mi?)
# Desenler model id'sinin İÇİNDE aranır; ilk eşleşen kullanılır.
# Listede olmayan yeni bir model gelirse varsayılan (orta-düşük) puan alır.
# ---------------------------------------------------------------------------
MODEL_BILGI = [
    ("gpt-oss-120b",        92, 70, 131072, True),
    ("kimi-k2",             90, 60, 131072, False),
    ("llama-4-maverick",    86, 75, 131072, False),
    ("llama-3.3-70b",       85, 65, 131072, False),
    ("qwen3-32b",           82, 70, 131072, True),
    ("gpt-oss-20b",         80, 90, 131072, True),
    ("llama-4-scout",       78, 85, 131072, False),
    ("deepseek-r1",         78, 40, 131072, True),
    ("llama-3.1-8b",        62, 98, 131072, False),
    ("gemma",               58, 90,   8192, False),
]
VARSAYILAN_BILGI = (55, 60, 8192, False)

# Sohbete uygun olmayan veya istenmeyen modeller
YASAKLI = ["guard", "whisper", "compound", "safeguard", "vision", "tts",
           "playai", "allam", "orpheus", "distil-whisper", "prompt-guard"]

TOP_N = 5                     # Denenecek en iyi model sayısı
MODEL_LISTE_ONBELLEK_SN = 3600
MAX_YANIT_TOKEN = 512


def _model_bilgisi(model_id):
    mid = model_id.lower()
    for desen, kalite, hiz, baglam, dusunen in MODEL_BILGI:
        if desen in mid:
            return kalite, hiz, baglam, dusunen
    return VARSAYILAN_BILGI


def _token_tahmini(metin):
    # Kabaca: 1 token ~ 4 karakter (Türkçe'de biraz daha az, güvenli tarafta kalıyoruz)
    return max(1, len(metin) // 3)


def _sure_parse(deger):
    """Groq reset başlıklarını ('2m59.56s', '7.66s', '120ms') saniyeye çevirir."""
    if not deger:
        return None
    try:
        return float(deger)
    except ValueError:
        pass
    toplam = 0.0
    for sayi, birim in re.findall(r"([\d.]+)(ms|h|m|s)", str(deger)):
        sayi = float(sayi)
        toplam += {"h": 3600, "m": 60, "s": 1, "ms": 0.001}[birim] * sayi
    return toplam or None


def _simdi():
    return datetime.now(_TZ) if _TZ else datetime.now()


def zaman_profili(saat=None):
    """İstek saatine göre puan ağırlıkları döndürür."""
    if saat is None:
        saat = _simdi().hour
    if 0 <= saat < 8:
        return "gece", {"kalite": 0.70, "hiz": 0.10, "kota": 0.20}
    if 8 <= saat < 18:
        return "gunduz", {"kalite": 0.55, "hiz": 0.20, "kota": 0.25}
    return "aksam_yogun", {"kalite": 0.35, "hiz": 0.35, "kota": 0.30}


class AIService:

    def __init__(self):
        self.config = config_dict['default']
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

        self._kilit = threading.Lock()
        self._model_listesi = []
        self._liste_zamani = 0.0
        # model_id -> {"kalan_token", "limit_token", "kalan_istek", "limit_istek",
        #              "soguma_bitis", "hata_sayisi"}
        self._kota = {}

    # ------------------------------------------------------------------ prompt
    def _get_system_prompt(self):
        ek_kural = (
            "\n\nÖNEMLİ KURALLAR:\n"
            "- Kullanıcı hangi dilde yazdıysa MUTLAKA aynı dilde yanıt ver "
            "(Türkçe yazana Türkçe, İngilizce yazana İngilizce).\n"
            "- Yanıtlarını kısa, öz ve net tut (en fazla 3-4 cümle veya 150 kelime).\n"
            "- Cümlelerini mutlaka tamamla, sözünü yarıda bırakma.\n"
            "- '[Adınızı girin]' gibi doldurulacak şablon alanları yazma."
        )
        return self.config.BUSINESS_CONTEXT + ek_kural

    # ------------------------------------------------------- model listeleme
    def _sohbet_modelleri(self):
        with self._kilit:
            taze = time.time() - self._liste_zamani < MODEL_LISTE_ONBELLEK_SN
            if taze and self._model_listesi:
                return list(self._model_listesi)
        ids = [m.id for m in self.client.models.list().data]
        modeller = [m for m in ids if not any(y in m.lower() for y in YASAKLI)]
        with self._kilit:
            self._model_listesi = modeller
            self._liste_zamani = time.time()
        return list(modeller)

    # ------------------------------------------------------------ puanlama
    def _kota_puani(self, model_id, gereken_token):
        k = self._kota.get(model_id)
        if not k:
            return 0.8  # Hiç kullanılmamış: bol kotalı varsay
        if k.get("soguma_bitis", 0) > time.time():
            return -1.0  # Soğumada: en sona at
        puan = 1.0
        if k.get("limit_token") and k.get("kalan_token") is not None:
            if k["kalan_token"] < gereken_token:
                return -0.5  # Bu istek sığmaz
            puan = min(puan, k["kalan_token"] / k["limit_token"])
        if k.get("limit_istek") and k.get("kalan_istek") is not None:
            puan = min(puan, k["kalan_istek"] / k["limit_istek"])
        puan -= 0.15 * min(k.get("hata_sayisi", 0), 4)
        return puan

    def model_sirala(self, modeller, giris_token, saat=None):
        """Modelleri puanlar ve en iyi TOP_N tanesini sırayla döndürür."""
        profil, w = zaman_profili(saat)
        gereken = giris_token + MAX_YANIT_TOKEN

        # Uzun/karmaşık sohbetlerde kaliteyi biraz daha öne çek
        if giris_token > 3000:
            w = dict(w, kalite=w["kalite"] + 0.15, hiz=max(0.0, w["hiz"] - 0.15))

        puanlar = []
        with self._kilit:
            for m in modeller:
                kalite, hiz, baglam, _ = _model_bilgisi(m)
                if gereken > baglam * 0.9:
                    continue  # Sohbet bu modelin hafızasına sığmıyor
                puan = (w["kalite"] * kalite / 100
                        + w["hiz"] * hiz / 100
                        + w["kota"] * self._kota_puani(m, gereken))
                puanlar.append((puan, m))
        puanlar.sort(reverse=True)
        return [m for _, m in puanlar[:TOP_N]], profil

    # -------------------------------------------------- kota güncelleme
    def _kota_guncelle(self, model_id, headers):
        def _int(ad):
            try:
                return int(headers.get(ad))
            except (TypeError, ValueError):
                return None
        with self._kilit:
            k = self._kota.setdefault(model_id, {})
            k["kalan_token"] = _int("x-ratelimit-remaining-tokens")
            k["limit_token"] = _int("x-ratelimit-limit-tokens")
            k["kalan_istek"] = _int("x-ratelimit-remaining-requests")
            k["limit_istek"] = _int("x-ratelimit-limit-requests")
            k["hata_sayisi"] = 0

    def _hata_kaydet(self, model_id, hata):
        with self._kilit:
            k = self._kota.setdefault(model_id, {})
            k["hata_sayisi"] = k.get("hata_sayisi", 0) + 1
            durum = getattr(hata, "status_code", None)
            bekle = None
            yanit = getattr(hata, "response", None)
            if yanit is not None:
                h = yanit.headers
                bekle = (_sure_parse(h.get("retry-after"))
                         or _sure_parse(h.get("x-ratelimit-reset-tokens"))
                         or _sure_parse(h.get("x-ratelimit-reset-requests")))
            if durum == 429:
                k["soguma_bitis"] = time.time() + (bekle or 60)
            elif durum in (404, 400) and "decommissioned" in str(hata).lower():
                k["soguma_bitis"] = time.time() + 24 * 3600  # Kaldırılmış model
            elif durum and durum >= 500:
                k["soguma_bitis"] = time.time() + 30

    # ----------------------------------------------------------- ana akış
    @staticmethod
    def _temizle(metin):
        # Düşünen modellerin <think>...</think> bölümünü kullanıcıya gösterme
        metin = re.sub(r"<think>.*?</think>", "", metin or "", flags=re.S)
        return metin.strip()

    def yanit_uret(self, mesaj, gecmis=None):
        if not self.client:
            return "DEMO MODU: API anahtarı ayarlanmamış."

        try:
            chat_models = self._sohbet_modelleri()
            if not chat_models:
                return "Hata: Hesabınızda kullanılabilecek bir metin modeli bulunamadı."

            messages = [{"role": "system", "content": self._get_system_prompt()}]
            if gecmis:
                messages.extend(gecmis[-12:])  # Son 12 mesaj yeterli, token tasarrufu
            messages.append({"role": "user", "content": mesaj})

            giris_token = sum(_token_tahmini(str(m.get("content", ""))) for m in messages)
            sirali, _profil = self.model_sirala(chat_models, giris_token)
            if not sirali:
                raise AIServiceError("Sohbet çok uzun; hiçbir modele sığmıyor.")

            last_error = None
            for model_adi in sirali:
                _, _, _, dusunen = _model_bilgisi(model_adi)
                params = dict(
                    messages=messages,
                    model=model_adi,
                    temperature=0.7,
                    # Düşünen modeller düşünmeye de token harcar, bütçeyi artır
                    max_tokens=MAX_YANIT_TOKEN * (2 if dusunen else 1),
                )
                if "gpt-oss" in model_adi:
                    params["reasoning_effort"] = "low"
                try:
                    ham = self.client.chat.completions.with_raw_response.create(**params)
                    self._kota_guncelle(model_adi, ham.headers)
                    yanit = ham.parse()
                    metin = self._temizle(yanit.choices[0].message.content)
                    if metin:
                        return metin
                    last_error = AIServiceError(f"{model_adi} boş yanıt döndü")
                except Exception as e:
                    self._hata_kaydet(model_adi, e)
                    last_error = e
                    continue

            raise AIServiceError(f"Hiçbir model yanıt vermedi. Son hata: {last_error}")

        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(str(e))

    def durum(self):
        """Hata ayıklama için: hangi modeller sırada, kota durumu ne?"""
        modeller = self._sohbet_modelleri() if self.client else []
        sirali, profil = self.model_sirala(modeller, 500)
        return {"profil": profil, "ilk5": sirali, "kota": self._kota}


ai_service = AIService()