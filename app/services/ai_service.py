import os
import requests
from config import config_dict


class AIServiceError(Exception):
    pass

class AIService:
    def __init__(self):
        
        self.config = config_dict['default']
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"

    def _get_system_prompt(self):
        """Sistem talimatını config'den okur"""
        return self.config.BUSINESS_CONTEXT

    def yanit_uret(self, mesaj, gecmis=None):
        """Kullanıcı mesajını alır, Groq API'sine gönderir ve yanıtı döndürür"""
        if gecmis is None:
            gecmis = []

        
        if not self.api_key:
            print("HATA: GROQ_API_KEY bulunamadı!")
            return "DEMO MODU: Sistemde API anahtarı algılanamadı. Lütfen Render ortam değişkenlerini kontrol edin."

        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        for msg in gecmis:
            messages.append(msg)
           
        messages.append({"role": "user", "content": mesaj})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            
            yanit_verisi = response.json()
            return yanit_verisi["choices"][0]["message"]["content"]
            
        except Exception as e:
            
            print(f"Groq API İletişim Hatası Detayı: {str(e)}")
            raise AIServiceError(f"Yapay zeka servisiyle iletişim kurulamadı: {str(e)}")


ai_service = AIService()