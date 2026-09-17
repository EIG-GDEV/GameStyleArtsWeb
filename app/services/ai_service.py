import os
from groq import Groq
from config import config_dict

class AIServiceError(Exception):
    pass

class AIService:
    def __init__(self):
        self.config = config_dict['default']
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.model = "llama-3.1-8b-instant"

        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            try:
                models_response = self.client.models.list()
                # Sadece sohbet/metin üretme modellerini filtrele (sınıflandırma ve guard modellerini dışla)
                chat_models = [
                    m.id for m in models_response.data 
                    if any(k in m.id.lower() for k in ['chat', 'instruct', 'instant', 'versatile', '8b', '70b'])
                    and not any(bad in m.id.lower() for bad in ['guard', 'embed', 'whisper', 'classifier'])
                ]
                if chat_models:
                    self.model = chat_models[0]
                print(f"Seçilen Sohbet Modeli: {self.model}")
            except Exception as e:
                print(f"Model listelenirken hata: {e}")
        else:
            self.client = None

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

        # Başarısız olursa sırayla denenecek yedek sohbet modelleri listesi
        models_to_try = [self.model] + [m for m in ["llama-3.1-8b-instant", "llama3-70b-8192", "mixtral-8x7b-32768"] if m != self.model]
        
        last_error = None
        for model_name in models_to_try:
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=model_name,
                    temperature=0.7,
                    max_tokens=512
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                last_error = e
                continue
        
        raise AIServiceError(f"Yapay zeka servisiyle iletişim kurulamadı: {str(last_error)}")

ai_service = AIService()