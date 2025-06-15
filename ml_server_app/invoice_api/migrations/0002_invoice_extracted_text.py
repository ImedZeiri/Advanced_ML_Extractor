from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='extracted_text',
            field=models.TextField(blank=True, null=True),
        ),
    ]