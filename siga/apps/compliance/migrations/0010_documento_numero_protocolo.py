from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("compliance", "0009_multiplas_aplicabilidades_e_executores")]

    operations = [
        migrations.AddField(
            model_name="documento",
            name="numero_protocolo",
            field=models.CharField(blank=True, max_length=120, verbose_name="numero do protocolo"),
        ),
    ]
