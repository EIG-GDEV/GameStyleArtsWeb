# os modülü: İşletim sistemiyle konuşmamızı sağlar. .env dosyasındaki gizli şifreleri okumak için kullanıyoruz.
import os

# groq modülü: Groq'un resmi kütüphanesi. API'ye güvenli ve standartlara uygun istek atmamızı sağlıyor.
from groq import Groq

# config modülü: config.py dosyamızdaki ayarları (özellikle yapay zekanın karakterini belirleyen BUSINESS_CONTEXT'i) buraya çağırıyoruz.
from config import config_dict


# Kendi özel hata sınıfımız. Eğer sistemde bir şeyler ters giderse, standart ve anlaşılmaz Python hataları yerine 
# kendi isimlendirdiğimiz (AIServiceError) hatayı fırlatacağız. Bu, hatanın nerede olduğunu anlamamızı kolaylaştırır.
class AIServiceError(Exception):
    pass


# Yapay Zeka servisimizin ana sınıfı (Blueprint). Uygulamamız yapay zeka ile konuşmak istediğinde bu sınıfı kullanacak.
class AIService:
    
    # __init__ metodu: Bu sınıf çağrıldığı anda ilk çalışan hazırlık (kurulum) bölümüdür.
    def __init__(self):
        # Ayarlar dosyasından projenin varsayılan yapılandırmasını (default) alıyoruz.
        self.config = config_dict['default']
        
        # Güvenlik! API anahtarını koda açıkça yazmak yerine, sunucunun (Render) ortam değişkenlerinden (Environment Variables) gizlice okuyoruz.
        self.api_key = os.environ.get("GROQ_API_KEY")
        
        # Eğer API anahtarı başarıyla okunmuşsa, Groq kütüphanesini bu anahtarla yetkilendirip başlatıyoruz.
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            # Anahtar yoksa sistemi çökertmiyoruz, client'ı None (boş) bırakıp aşağıda demo modu uyarısı vereceğiz.
            self.client = None


    # Bu metod, yapay zekanın "Kim olduğunu" ve "Nasıl davranması gerektiğini" belirleyen gizli talimatı çeker.
    def _get_system_prompt(self):
        # Önceden eklediğimiz kelime sınırı kuralını ve asıl hikaye/sistem metnini birleştirip geri döndürüyor.
        ek_kural = "\n\nÖNEMLİ KURAL: Yanıtlarını kısa, öz ve net tut (Maksimum 3-4 cümle veya 150 kelime). Cümlelerini mutlaka tamamla ve sözünü asla yarıda bırakma."
        return self.config.BUSINESS_CONTEXT + ek_kural


    # Dışarıdan (Wix arayüzünden) gelen mesajı alıp, Groq'a gönderen ve cevabı geri döndüren ana fonksiyon.
    def yanit_uret(self, mesaj, gecmis=None):
        
        # Eğer sunucuda API anahtarı girilmemişse, kodun çökmesini engeller ve kullanıcıya kibar bir uyarı döndürür.
        if not self.client:
            return "DEMO MODU: API anahtarı ayarlanmamış."

        try:
            # 1. DİNAMİK MODEL LİSTELEME
            # Groq'a bağlanıp "Benim API anahtarımla şu an hangi modelleri kullanmaya yetkim var?" diye soruyoruz.
            # Gelen yanıttaki modellerin sadece isimlerini (id) bir listeye kaydediyoruz.
            model_ids = [m.id for m in self.client.models.list().data]
            
            # 2. AKILLI FİLTRELEME
            # Hesabımızda bulunan ama sohbet edemeyen (sadece ses tanıyan, görüntü işleyen veya güvenlik kalkanı olan)
            # modellerin listesini belirliyoruz. Amacımız sadece saf metin/sohbet modellerini elde tutmak.
            yasakli = ['guard', 'whisper', 'compound', 'safeguard', 'vision']
            
            # Eğer model isminin içinde yukarıdaki yasaklı kelimelerden hiçbiri YOKSA, o modeli "chat_models" listesine alıyoruz.
            chat_models = [m for m in model_ids if not any(y in m.lower() for y in yasakli)]
            
            # Eğer tüm elemelerden sonra elimizde hiç model kalmadıysa süreci durdurup hata mesajı dönüyoruz.
            if not chat_models:
                return "Hata: Hesabınızda kullanılabilecek bir metin modeli bulunamadı."

            # 3. MESAJ PAKETİNİ HAZIRLAMA
            # Groq'un anlayacağı JSON/Sözlük formatında mesaj geçmişini hazırlıyoruz.
            # İlk sıraya her zaman yapay zekanın karakterini (System Prompt) koyuyoruz.
            messages = [{"role": "system", "content": self._get_system_prompt()}]
            
            # Eğer önceki sohbet geçmişi (gecmis) varsa, bunu araya ekliyoruz ki yapay zeka konuyu hatırlasın.
            if gecmis:
                messages.extend(gecmis)
                
            # En son sıraya kullanıcının anlık olarak yazdığı mesajı ekliyoruz.
            messages.append({"role": "user", "content": mesaj})

            
            # Bu kısım filtreden geçen modelleri tek tek dener.
            last_error = None
            for model_adi in chat_models:
                try:
                    # Hazırladığımız mesaj paketini seçilen modele gönderiyoruz.
                    chat_completion = self.client.chat.completions.create(
                        messages=messages,
                        model=model_adi,         # Döngüdeki sıradaki model
                        temperature=0.7,         # Yaratıcılık ayarı (0 robotik, 1 çok hayalperest. 0.7 dengeli)
                        max_tokens=512           # Cümlenin yarıda kesilmemesi için ayırdığımız maksimum hafıza/kelime bütçesi
                    )
                    
                    # Eğer istek başarılı olursa, Groq'tan gelen yanıt paketinin içinden sadece metin kısmını alıp kullanıcıya döndürüyoruz.
                    # Yanıt döndüğü an "return" çalıştığı için döngü (for) anında biter, diğer modeller denenmez.
                    return chat_completion.choices[0].message.content
                
                except Exception as e:
                    # Eğer bu model hata verirse (örn: kullanım limiti dolduysa veya geçici olarak kapalıysa),
                    # programı çökertmiyoruz. Hatayı 'last_error' içine not alıp 'continue' diyerek listedeki bir sonraki modele geçiyoruz.
                    last_error = e
                    continue 
            
            # Eğer 'for' döngüsü bittiyse ve buraya kadar indiysek, listedeki TÜM modeller hata vermiş demektir.
            # O zaman kendi özel hata mesajımızı fırlatıyoruz.
            raise AIServiceError(f"Hiçbir model yanıt vermedi. Son hata: {last_error}")
            
        except Exception as e:
            # Kodun herhangi bir yerinde (modelleri çekerken vs.) beklenmedik genel bir hata olursa sistemi güvenle durdurur.
            raise AIServiceError(str(e))

# Bu sınıfı başka dosyalarda (örneğin routes.py içinde) kolayca kullanabilmek için 'ai_service' adında hazır bir kopyasını (instance) oluşturuyoruz.
ai_service = AIService()