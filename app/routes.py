from flask import Blueprint, request, jsonify, render_template
# Kendi yazdığımız katmanları (database ve ai_service) içeri aktarıyoruz
from .database import lead_ekle, tum_leadler
from .services.ai_service import ai_service, AIServiceError

# Yönerge kuralı: İki ayrı Blueprint (Sayfalar ve API) oluşturulmalı
sayfalar_bp = Blueprint('sayfalar', __name__)
api_bp = Blueprint('api', __name__)

# --- SAYFA ROTALARI ---

@sayfalar_bp.route('/')
def index():
    """Karşılama sayfasını gösterir"""
    return render_template('index.html')

@sayfalar_bp.route('/dashboard')
def dashboard():
    """Yönetim panelini gösterir"""
    return render_template('dashboard.html')

# --- API ROTALARI ---
# Not: Yönerge gereği bu rotalar Modül E'de uygulamaya '/api' önekiyle kaydedilecek.
# Bu nedenle burada sadece '/sohbet' ve '/leads' yazıyoruz.

@api_bp.route('/sohbet', methods=['POST'])
def sohbet():
    """AI'a mesaj iletir ve yanıtı döndürür"""
    veri = request.get_json()
    
    if not veri or 'mesaj' not in veri:
        # Yönerge kuralı: Eksik veri gelirse 400 durum kodu dönülmeli
        return jsonify({'basari': False, 'hata': 'Mesaj alanı eksik'}), 400
    
    kullanici_mesaji = veri['mesaj']
    gecmis = veri.get('gecmis', [])
    
    try:
        # Yönerge kuralı: AI çağrısını try-except ile sarın
        yanit = ai_service.yanit_uret(kullanici_mesaji, gecmis)
        return jsonify({'basari': True, 'cevap': yanit}), 200
        
    except AIServiceError as e:
        # Yönerge kuralı: AI hatası olursa 503 ve kibar bir JSON hata dönülmeli
        return jsonify({'basari': False, 'hata': 'Game Style Arts asistanı şu an meşgul, lütfen birazdan tekrar deneyin.'}), 503

@api_bp.route('/leads', methods=['POST'])
def lead_kaydet():
    """Yeni lead (müşteri adayı/oyuncu) kaydeder"""
    veri = request.get_json()
    
    # DİKKAT: Senin isteğine göre 'telefon' yerine 'email' kontrolü yapıyoruz!
    if not veri or 'isim' not in veri or 'email' not in veri:
        return jsonify({'basari': False, 'hata': 'İsim ve email alanları zorunludur'}), 400
    
    try:
        # Veritabanı katmanındaki fonksiyonu çağırıyoruz
        lead_ekle(veri['isim'], veri['email'], veri.get('mesaj', ''))
        # Yönerge kuralı: Yeni kayıtta 201 durum kodu dönülmeli
        return jsonify({'basari': True, 'mesaj': 'Kayıt başarıyla oluşturuldu'}), 201
    except Exception as e:
        return jsonify({'basari': False, 'hata': 'Kayıt sırasında bir hata oluştu'}), 500

@api_bp.route('/leads', methods=['GET'])
def lead_listele():
    """Tüm lead'leri getirir (Dashboard için)"""
    try:
        # Veritabanı katmanından verileri çekiyoruz
        leadler = tum_leadler()
        return jsonify({'basari': True, 'data': leadler}), 200
    except Exception as e:
        return jsonify({'basari': False, 'hata': 'Kayıtlar alınamadı'}), 500