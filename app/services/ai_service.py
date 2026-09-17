import os
from groq import Groq
from config import config_dict

class AIServiceError(Exception):
    pass

class AIService:
    def __init__(self):
        self.config = config_dict['default']
        self.api_key = os.environ.get("GROQ_API_KEY")
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            try:
                # Hesabının desteklediği aktif modelleri Groq'tan otomatik çekiyoruz!
                models_response = self.client.models.list()
                available_models = [m.id for m in models_response.data if 'llama' in m.id]
                
                if available_models:
                    self.model = available_models[0] # Çalışan ilk Llama modelini seç
                elif models_response.data:
                    self.model = models_response.data[0].id
                else:
                    self.model = "llama-3.1-8b-instant"
                print(f"Otomatik Seçilen Groq Modeli: {self.model}")
            except Exception as e:
                print(f"Model listelenirken hata, varsayılan atanıyor: {e}")
                self.model = "llama-3.1-8b-instant"
        else:
            self.client = None
            self.model = "llama-3.1-8b-instant"

    def _get_system_prompt(self):
        return self.config.BUSINESS_CONTEXT

    def yanit_uret(self, mesaj, gecmis=None):
        if gecmis is None:
            gecmis = []

        if not self.client:
            return "DEMO MODU: API anahtarı algılanamadı."

        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        for msg in gecmis:
            messages.append(msg)
           
        messages.append({"role": "user", "content": mesaj})

        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.7,
                max_tokens=512  # Burayı 512 yaptık!
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            print(f"Groq SDK Hata Detayı: {str(e)}")
            raise AIServiceError(f"Yapay zeka servisiyle iletişim kurulamadı: {str(e)}")

ai_service = AIService()