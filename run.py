from app import create_app

# Fabrikadan uygulamayı alıyoruz
app = create_app('development')

if __name__ == '__main__':
    
    app.run(port=5000)