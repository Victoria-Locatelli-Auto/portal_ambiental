import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("compliance", "0014_documentos_relacionados"),
        ("fornecedores", "0005_cidades_atendidas_dropdown"),
    ]
    operations = [
        migrations.AddField(
            model_name="documento",
            name="fornecedor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="documentos",
                to="fornecedores.fornecedor",
                verbose_name="fornecedor",
            ),
        ),
    ]
