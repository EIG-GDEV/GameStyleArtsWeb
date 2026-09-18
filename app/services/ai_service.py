import os
from groq import Groq
from config import config_dict

class AIServiceError(Exception):
    pass

class AIService:
    def __init__(self):
        self.config = config_dict['default']
        self.api_key = os.environ.get("GROQ_API_KEY")
        print(f"API Key yüklendi mi?: {bool(self.api_key)}", flush=True)
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def _get_system_prompt(self):
        return self.config.BUSINESS_CONTEXT

    def yanit_uret(self, mesaj, gecmis=None):
        print(f"--- YENİ MESAJ GELDİ: {mesaj} ---", flush=True)
        if not self.client:
            return "DEMO MODU: API anahtarı algılanamadı."

        try:
            # 1. Groq hesabındaki tüm açık modelleri çek ve loga bas
            models_data = self.client.models.list().data
            model_ids = [m.id for m in models_data]
            print(f"HESABINDAKİ AKTİF MODELLER: {model_ids}", flush=True)
            
            # 2. Guard/Vision modellerini eleyip gerçek sohbet modellerini bul
            chat_models = [m for m in model_ids if 'chat' in m.lower() or 'instruct' in m.lower() or 'llama' in m.lower() or 'gemma' in m.lower() or 'mixtral' in m.lower()]
            chat_models = [m for m in chat_models if 'guard' not in m.lower() and 'vision' not in m.lower() and 'whisper' not in m.lower()]
            
            if not chat_models:
                raise ValueError("Hesabınızda kullanılabilir sohbet modeli bulunamadı!")
                
            secilen_model = chat_models[0]
            print(f"KULLANILACAK MODEL: {secilen_model}", flush=True)

            # 3. Hazırlıkları yap ve isteği at
            messages = [{"role": "system", "content": self._get_system_prompt()}]
            if gecmis:
                messages.extend(gecmis)
            messages.append({"role": "user", "content": mesaj})

            print(f"{secilen_model} modeline istek atılıyor...", flush=True)
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=secilen_model,
                temperature=0.7,
                max_tokens=512
            )
            print("Groq'tan BAŞARILI yanıt geldi!", flush=True)
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            # flush=True sayesinde hata anında Render loglarına düşecek!
            print(f"!!! GROQ API KRİTİK HATA !!! Detay: {str(e)}", flush=True)
            raise AIServiceError(f"Hata: {str(e)}")

ai_service = AIService()