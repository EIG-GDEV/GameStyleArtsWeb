from flask import Flask, jsonify
from config import config_dict
from .database import init_db
from .routes import sayfalar_bp, api_bp

def create_app(config_name='default'):
    """Flask uygulamasını oluşturur ve tüm ayarları/eklentileri yükler (Uygulama Fabrikası)"""
    app = Flask(__name__)
    
    # 1. Ayarları yükle
    app.config.from_object(config_dict[config_name])
    
    # 2. Veritabanını başlat (Yönerge kuralı: app_context içinde çağrılmalı)
    with app.app_context():
        init_db(app)
        
    # 3. Yönerge kuralı: Sunucu canlılık kontrolü (health check) uç noktası
    @app.route('/health')
    def health_check():
        return jsonify({'basari': True, 'durum': 'aktif', 'mesaj': 'Sistem sağlıklı çalışıyor'})
        
    # 4. Blueprint'leri kaydet
    app.register_blueprint(sayfalar_bp)
    # API rotalarına otomatik olarak '/api' öneki ekliyoruz
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # CORS (Cross-Origin Resource Sharing) için temel bir başlık ayarı
    # Bu, Wix gibi farklı domainlerden gelen isteklere izin vermek için gereklidir
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', app.config['CORS_ORIGINS'])
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app