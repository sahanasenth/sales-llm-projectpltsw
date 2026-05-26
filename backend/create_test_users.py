import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_users():
    User = get_user_model()
    users = [
        {'username': 'admin', 'password': 'admin123', 'email': 'admin@platinum.com', 'role': 'director', 'is_staff': True, 'is_superuser': True},
        {'username': 'salesmanager', 'password': 'sales123', 'email': 'manager@platinum.com', 'role': 'manager', 'is_staff': True, 'is_superuser': False},
        {'username': 'director', 'password': 'director123', 'email': 'director@platinum.com', 'role': 'director', 'is_staff': False, 'is_superuser': False},
        {'username': 'salesexecutive', 'password': 'sales123', 'email': 'sales@platinum.com', 'role': 'sales_executive', 'is_staff': False, 'is_superuser': False},
    ]

    for user_data in users:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                role=user_data['role'],
            )
            user.is_staff = user_data['is_staff']
            user.is_superuser = user_data['is_superuser']
            user.save()
            print(f"Successfully created user: {user_data['username']}")
        else:
            user = User.objects.get(username=user_data['username'])
            user.email = user_data['email']
            user.role = user_data['role']
            user.is_staff = user_data['is_staff']
            user.is_superuser = user_data['is_superuser']
            user.save()
            print(f"Updated existing user: {user_data['username']}")

if __name__ == "__main__":
    create_users()
