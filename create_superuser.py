import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

print("=" * 50)
print("🔧 SUPERUSER CREATION SCRIPT")
print("=" * 50)

# Validar variáveis de ambiente
if not email or not password:
    print("❌ ERROR: Missing environment variables!")
    print(f"   DJANGO_SUPERUSER_EMAIL: {'✅ Set' if email else '❌ Missing'}")
    print(f"   DJANGO_SUPERUSER_PASSWORD: {'✅ Set' if password else '❌ Missing'}")
    sys.exit(1)

print(f"📧 Email: {email}")
print(f"🔐 Password: {'*' * len(password)}")
print(f"👤 User model: {User}")
print(f"🔑 Login field: {User.USERNAME_FIELD}")
print("-" * 50)

try:
    # Verificar se já existe
    existing_user = User.objects.filter(email=email).first()
    
    if existing_user:
        print(f"⚠️  User '{email}' already exists")
        print(f"   is_superuser: {existing_user.is_superuser}")
        print(f"   is_staff: {existing_user.is_staff}")
        print(f"   is_active: {existing_user.is_active}")
        
        if not existing_user.is_superuser or not existing_user.is_staff:
            print("🔄 Updating user permissions...")
            existing_user.is_superuser = True
            existing_user.is_staff = True
            existing_user.is_active = True
            existing_user.set_password(password)
            existing_user.save()
            print("✅ User updated to superuser successfully!")
        else:
            # Atualizar senha mesmo se já for superuser
            print("🔄 Updating password...")
            existing_user.set_password(password)
            existing_user.save()
            print("✅ Password updated successfully!")
    else:
        print(f"🆕 Creating new superuser with email '{email}'...")
        user = User.objects.create_superuser(
            email=email,
            password=password
        )
        print("✅ Superuser created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_active: {user.is_active}")
    
    print("=" * 50)
    print("✅ SUPERUSER SETUP COMPLETED")
    print("=" * 50)
    print("")
    print("🔑 LOGIN CREDENTIALS:")
    print(f"   Email: {email}")
    print(f"   Password: (use the one you configured)")
    print("=" * 50)
    
except Exception as e:
    print("=" * 50)
    print("❌ ERROR CREATING SUPERUSER")
    print("=" * 50)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)