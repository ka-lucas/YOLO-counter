from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Modelo LogEvent removido - agora usamos CountingSession do app video_ao_vivo
# para histórico de contagens de animais