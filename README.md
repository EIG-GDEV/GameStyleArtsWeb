# Game Style Arts - AI Assistant & Lead Management Backend

Bu proje, "Dark List SandHell Storm" adlı açık dünya polis simulasyonu oyun projesinin Wix tabanlı web sitesi için geliştirilmiş Python (Flask) tabanlı bir backend servisidir.

## Projenin Amacı ve Özellikleri
Bu backend sistemi iki temel işlevi yerine getirmektedir:
1. Akıllı Asistan (Groq API): Kullanıcıların oyun hakkında sorduğu sorulara, oyunun sistem yönergelerine sadık kalarak yanıt veren, hata toleransı yüksek (dinamik model seçimi yapan) yapay zeka entegrasyonu.
2. Lead Generation (Kullanıcı Veri Yönetimi): Wix arayüzünden gelen kullanıcı iletişim bilgilerinin alınarak SQLite veritabanına kaydedilmesi ve bir Dashboard üzerinden yönetilmesi.

## Kullanılan Teknolojiler
* Frontend: Wix Velo (Arayüz ve Fetch API çağrıları)
* Backend: Python, Flask, Flask-CORS, Gunicorn
* Yapay Zeka: Groq API (Dinamik model listeleme ve fallback mimarisi)
* Veritabanı: SQLite
* Deployment: Render

## Projeyi Lokal Olarak Çalıştırma
Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımı izleyin:

1. Depoyu klonlayın:
   ```bash
   git clone [GITHUB_REPO_LINKIN]
