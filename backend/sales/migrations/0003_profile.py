from django.conf import settings
from django.db import migrations, models
from django.db.models import deletion


def create_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('sales', 'Profile')

    for user in User.objects.all().iterator():
        Profile.objects.get_or_create(user_id=user.id, defaults={'role': 'sales'})


def delete_profiles(apps, schema_editor):
    Profile = apps.get_model('sales', 'Profile')
    Profile.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sales', '0002_alter_appointment_table_alter_enquiry_table_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('salesmanager', 'Sales Manager'), ('director', 'Director'), ('sales', 'Sales Executive')], default='sales', max_length=20)),
                ('user', models.OneToOneField(on_delete=deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(create_profiles, delete_profiles),
    ]
