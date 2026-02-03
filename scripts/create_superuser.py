import sys
import os
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def main():
    # User requested login: gaspar, password: tijolo22
    # Since USERNAME_FIELD is 'email', we must use an email format.
    # We will use 'gaspar@oink.com' as the login.
    email = "gaspar@oink.com"
    password = "tijolo22"

    if User.objects.filter(email=email).exists():
        print(f"⚠️ User {email} already exists.")
    else:
        print(f"👤 Creating superuser {email}...")
        try:
            User.objects.create_superuser(
                email=email,
                password=password,
            )
            print(f"✔️ Superuser created successfully!")
        except Exception as e:
            print(f"❌ Error creating user: {e}")

    # Explicitly logging credentials as requested to be visible
    print("-" * 40)
    print("DJANGO SUPERUSER CREDENTIALS:")
    print(f"Login: {email}")
    print(f"Password: {password}")
    print("-" * 40)

if __name__ == "__main__":
    main()
