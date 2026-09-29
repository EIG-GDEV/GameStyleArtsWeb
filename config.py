import os
from dotenv import load_dotenv


load_dotenv()

class Config:
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'varsayilan-guvenlik-anahtari')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///leads.db')
    
    # Yapay Zeka 
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'Groq')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    
    BUSINESS_CONTEXT = """Sen Game Style Arts oyun stüdyosunun asistanısın. 
    Kullanıcılara 3 mobil oyunumuzun 2 tanesinin 2D arcade aksiyon diğerinin 3D arcade aksiyon olduğunu ayrıca bilgisayar için mecut 3d şerif simulasyonu oyunu olduğunu göz önünde bulundurarak bilgilendir. 
    Mobil oyunların yayından kalktığını ve bilgisayar oyununun geliştirildiğini göz önünde bulundur.
    Sadece para kazanma gayesinden uzak, oyuncuya ve topluluğa önem veren kurumsal ama samimi bir dil kullan. 
    Ziyaretçileri oyuna erken erişim fırsatları veya geri bildirim vermek üzere iletişim bilgilerini (isim ve e-posta) bırakmaya yönlendir."""


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}