import os
from groq import Groq
from config import config_dict

class AIServiceError(Exception):
    pass

class AIService:
    def __init__(self):
        self.config = config_dict['default']
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def _get_system_prompt(self):
        return self.config.BUSINESS_CONTEXT

    def yanit_uret(self, mesaj, gecmis=None):
        if not self.client:
            return "DEMO MODU: API anahtarı ayarlanmamış."

        try:
            # 1. API anahtarının yetkili olduğu TÜM modelleri çek
            model_ids = [m.id for m in self.client.models.list().data]
            
            # 2. Sadece ses ve koruma kalkanı modellerini filtrele (Geriye saf metin modelleri kalsın)
            yasakli = ['guard', 'whisper', 'compound', 'safeguard', 'vision']
            chat_models = [m for m in model_ids if not any(y in m.lower() for y in yasakli)]
            
            if not chat_models:
                return "Hata: Hesabınızda kullanılabilecek bir metin modeli bulunamadı."

            # 3. İsteği hazırla
            messages = [{"role": "system", "content": self._get_system_prompt()}]
            if gecmis:
                messages.extend(gecmis)
            messages.append({"role": "user", "content": mesaj})

            # 4. YIKILMAZ DÖNGÜ: Listede kalan tüm modelleri başarıya ulaşana kadar sırayla dene!
            last_error = None
            for model_adi in chat_models:
                try:
                    chat_completion = self.client.chat.completions.create(
                        messages=messages,
                        model=model_adi,
                        temperature=0.7,
                        max_tokens=512
                    )
                    return chat_completion.choices[0].message.content
                except Exception as e:
                    last_error = e
                    continue # Bu model hata verdiyse çökme, sıradakine geç!
            
            raise AIServiceError(f"Hiçbir model yanıt vermedi. Son hata: {last_error}")
            
        except Exception as e:
            raise AIServiceError(str(e))

ai_service = AIService()