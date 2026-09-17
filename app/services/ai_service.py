import os
import requests
from config import config_dict

# Proje yönergesinde istenen özel hata sınıfı
class AIServiceError(Exception):
    pass

class AIService:
    def __init__(self):
        # Varsayılan ayarları yükle
        self.config = config_dict['default']
        self.api_key = self.config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant" # Yönergede istenen model

    def _get_system_prompt(self):
        """Sistem talimatını config'den okur"""
        return self.config.BUSINESS_CONTEXT

    def yanit_uret(self, mesaj, gecmis=None):
        """Kullanıcı mesajını alır, Groq API'sine gönderir ve yanıtı döndürür"""
        if gecmis is None:
            gecmis = []

        # API anahtarı yoksa demo modu mesajı döndür
        if not self.api_key:
            return "DEMO MODU: Merhaba! Groq API anahtarı ayarlanmamış. Sistem şu an test modunda çalışıyor. İletişim bilgilerinizi (İsim ve E-posta) bırakabilirsiniz."

        # Yönerge kuralı: system, geçmiş mesajlar, user mesajı sırası
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        # Geçmiş mesajları ekle
        for msg in gecmis:
            messages.append(msg)
            
        # Yeni kullanıcı mesajını ekle
        messages.append({"role": "user", "content": mesaj})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages
        }

        # Yönerge kuralı: İstek try-except ile sarılmalı
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=15)
            response.raise_for_status() # HTTP hatalarını yakala
            
            yanit_verisi = response.json()
            return yanit_verisi["choices"][0]["message"]["content"]
            
        except Exception as e:
            # Hata durumunda özel AIServiceError fırlat
            raise AIServiceError(f"Yapay zeka servisiyle iletişim kurulamadı: {str(e)}")

# Dosya sonunda tek bir örnek oluştur (Singleton benzeri kullanım için)
ai_service = AIService()