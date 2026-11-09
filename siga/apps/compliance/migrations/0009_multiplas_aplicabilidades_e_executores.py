from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("compliance", "0008_remove_regras_condicionantes")]

    operations = [
        migrations.AlterField(
            model_name="tipodocumento",
            name="aplicabilidade",
            field=models.CharField(default="TODAS", max_length=255, verbose_name="aplicabilidade"),
        ),
        migrations.AlterField(
            model_name="tipodocumento",
            name="responsavel_execucao",
            field=models.CharField(default="CASA", max_length=255, verbose_name="quem executa"),
        ),
    ]
