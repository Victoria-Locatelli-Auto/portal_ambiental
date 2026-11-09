from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("compliance", "0010_documento_numero_protocolo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tipodocumento",
            name="cor_agenda",
            field=models.CharField(
                choices=[
                    ("VERDE", "Verde"),
                    ("MARROM", "Marrom"),
                    ("AZUL", "Azul"),
                    ("SEM_COR", "Sem cor"),
                ],
                default="VERDE",
                max_length=10,
                verbose_name="cor da agenda",
            ),
        ),
    ]
