from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_whatsappconfiguration_whatsapplog'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(help_text="Africa's Talking username. Use sandbox for testing.", max_length=100)),
                ('api_key', models.TextField(help_text="Africa's Talking API key.")),
                ('sender_id', models.CharField(blank=True, default='', help_text='Optional approved sender ID or shortcode.', max_length=50)),
                ('default_country_code', models.CharField(default='254', help_text='Used when users enter local phone numbers, e.g. 254 for Kenya.', max_length=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SMSLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient', models.CharField(max_length=30)),
                ('message', models.TextField()),
                ('status', models.CharField(choices=[('sent', 'Sent'), ('failed', 'Failed')], max_length=20)),
                ('response_message', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
