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
        ek_kural = "\n\nÖNEMLİ KURAL: Yanıtlarını kısa, öz ve net tut (Maksimum 3-4 cümle veya 150 kelime). Cümlelerini mutlaka tamamla ve sözünü asla yarıda bırakma."
        return self.config.BUSINESS_CONTEXT + ek_kural

    def yanit_uret(self, mesaj, gecmis=None):
        if not self.client:
            return "DEMO MODU: API anahtarı ayarlanmamış."

        try:
            
            model_ids = [m.id for m in self.client.models.list().data]

            yasakli = ['guard', 'whisper', 'compound', 'safeguard', 'vision']
            chat_models = [m for m in model_ids if not any(y in m.lower() for y in yasakli)]
            
            if not chat_models:
                return "Hata: Hesabınızda kullanılabilecek bir metin modeli bulunamadı."

        
            messages = [{"role": "system", "content": self._get_system_prompt()}]
            if gecmis:
                messages.extend(gecmis)
            messages.append({"role": "user", "content": mesaj})

            
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
                    continue 
            
            raise AIServiceError(f"Hiçbir model yanıt vermedi. Son hata: {last_error}")
            
        except Exception as e:
            raise AIServiceError(str(e))

ai_service = AIService()