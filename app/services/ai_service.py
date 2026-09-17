import os
from groq import Groq
from config import config_dict

class AIServiceError(Exception):
    pass

class AIService:
    def __init__(self):
        self.config = config_dict['default']
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.model = "mixtral-8x7b-32768"
        
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
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

        try:
            
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.7,
                max_tokens=1024
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            print(f"Groq SDK Hata Detayı: {str(e)}")
            raise AIServiceError(f"Yapay zeka servisiyle iletişim kurulamadı: {str(e)}")

ai_service = AIService()