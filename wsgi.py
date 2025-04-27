"""
Módulo WSGI para rodar a aplicação com Gunicorn
"""
from run import app

if __name__ == "__main__":
    app.run() 