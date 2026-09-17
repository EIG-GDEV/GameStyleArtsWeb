from app import create_app

# Fabrikadan uygulamayı alıyoruz
app = create_app('development')

if __name__ == '__main__':
    # Sunucuyu başlat (Varsayılan olarak 5000 portunda çalışır)
    app.run(port=5000)