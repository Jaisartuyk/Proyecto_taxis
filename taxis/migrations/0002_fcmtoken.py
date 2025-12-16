# Generated migration for FCMToken model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taxis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FCMToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(help_text='Token FCM del dispositivo', max_length=255, unique=True)),
                ('device_id', models.CharField(blank=True, help_text='ID único del dispositivo (opcional)', max_length=255, null=True)),
                ('platform', models.CharField(choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')], default='android', max_length=20)),
                ('is_active', models.BooleanField(default=True, help_text='Si el token está activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fcm_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Token FCM',
                'verbose_name_plural': 'Tokens FCM',
                'ordering': ['-created_at'],
            },
        ),
    ]
