"""
Configuração do Gunicorn para o deploy da aplicação em produção
"""
import multiprocessing

# Configurações de Bind
bind = "0.0.0.0:5001"  # Endereço IP e porta onde o Gunicorn vai escutar

# Configurações de Worker
workers = multiprocessing.cpu_count() * 2 + 1  # Recomendação típica é (2 x num_cores) + 1
worker_class = 'sync'  # Tipo de worker (sync, eventlet, gevent, etc.)
threads = 2  # Número de threads por worker
timeout = 60  # Timeout em segundos para processar requisições

# Configurações de Logging
accesslog = '-'  # '-' para stdout
errorlog = '-'  # '-' para stderr
loglevel = 'info'  # Nível de log (debug, info, warning, error, critical)

# Outras configurações
max_requests = 1000  # Reinicia o worker após processar esse número de requisições
max_requests_jitter = 50  # Adiciona variação para evitar que todos os workers reiniciem ao mesmo tempo
graceful_timeout = 30  # Tempo em segundos para desligar graciosamente um worker
keepalive = 2  # Tempo em segundos para manter conexões HTTP abertas 