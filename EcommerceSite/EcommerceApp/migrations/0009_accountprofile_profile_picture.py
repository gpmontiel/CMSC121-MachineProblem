# Generated by Django 5.2 on 2025-05-12 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EcommerceApp', '0008_cartitem_price_at_add'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pics/'),
        ),
    ]
