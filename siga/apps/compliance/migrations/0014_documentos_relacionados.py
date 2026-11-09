from django.db import migrations, models

import apps.compliance.models


class Migration(migrations.Migration):
    dependencies = [("compliance", "0013_anexoprocessorenovacao")]

    operations = [
        migrations.AddField(
            model_name="tipodocumento",
            name="quantidade_arquivos",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "1 documento"), (2, "2 documentos relacionados")],
                default=1,
                verbose_name="quantidade de documentos",
            ),
        ),
        migrations.AddField(
            model_name="tipodocumento",
            name="nome_anexo_complementar",
            field=models.CharField(
                blank=True,
                help_text="Ex.: Certificado.",
                max_length=120,
                verbose_name="nome do segundo documento",
            ),
        ),
        migrations.AddField(
            model_name="documento",
            name="anexo_complementar",
            field=models.FileField(
                blank=True,
                upload_to=apps.compliance.models.caminho_do_arquivo,
                verbose_name="segundo documento",
            ),
        ),
        migrations.AddField(
            model_name="documento",
            name="nome_anexo_complementar",
            field=models.CharField(
                blank=True,
                max_length=120,
                verbose_name="nome do segundo documento",
            ),
        ),
    ]
