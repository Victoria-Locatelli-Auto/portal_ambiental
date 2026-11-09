import apps.fornecedores.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("fornecedores", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="fornecedor",
            name="anexo_contrato",
            field=models.FileField(
                blank=True,
                help_text="Anexe o contrato em PDF, DOC, DOCX ou ODT.",
                upload_to=apps.fornecedores.models.caminho_anexo_fornecedor,
                validators=[
                    django.core.validators.FileExtensionValidator(
                        ["pdf", "doc", "docx", "odt"]
                    )
                ],
                verbose_name="anexo do contrato",
            ),
        ),
    ]
