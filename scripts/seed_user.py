import sys
import os
import django

# Ajusta o path para encontrar o settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def main():
    print("👤 Criando usuário seed...")

    email = "devs@gmail.com"
    password = "Senha1234!"

    # Evita duplicar
    if User.objects.filter(email=email).exists():
        print(f"⚠️ Usuário {email} já existe.")
        return

    user = User.objects.create_user(
        email=email,
        password=password,
    )

    print("✔️ Usuário criado com sucesso!")
    print(f"   Email: {user.email}")
    print(f"   ID: {user.id}")


if __name__ == "__main__":
    main()
