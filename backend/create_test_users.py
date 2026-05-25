import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.contrib.auth.models import User

def create_users():
    users = [
        {'username': 'admin', 'password': 'admin123', 'email': 'admin@platinum.com', 'is_staff': True, 'is_superuser': True},
        {'username': 'salesmanager', 'password': 'sales123', 'email': 'manager@platinum.com', 'is_staff': True, 'is_superuser': False},
        {'username': 'director', 'password': 'director123', 'email': 'director@platinum.com', 'is_staff': False, 'is_superuser': False},
    ]

    for user_data in users:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            user.is_staff = user_data['is_staff']
            user.is_superuser = user_data['is_superuser']
            user.save()
            print(f"Successfully created user: {user_data['username']}")
        else:
            print(f"User {user_data['username']} already exists.")

if __name__ == "__main__":
    create_users()
