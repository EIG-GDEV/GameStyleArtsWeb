from flask import Flask, jsonify
from config import config_dict
from .database import init_db
from .routes import sayfalar_bp, api_bp

def create_app(config_name='default'):
    """Flask uygulamasını oluşturur ve tüm ayarları/eklentileri yükler (Uygulama Fabrikası)"""
    app = Flask(__name__)
    

    app.config.from_object(config_dict[config_name])
    

    with app.app_context():
        init_db(app)
        

    @app.route('/health')
    def health_check():
        return jsonify({'basari': True, 'durum': 'aktif', 'mesaj': 'Sistem sağlıklı çalışıyor'})
        
  
    app.register_blueprint(sayfalar_bp)
    
    app.register_blueprint(api_bp, url_prefix='/api')
    

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', app.config['CORS_ORIGINS'])
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app