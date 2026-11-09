import django.db.models.deletion
from django.db import migrations, models


def preservar_primeira_cidade(apps, schema_editor):
    Fornecedor = apps.get_model("fornecedores", "Fornecedor")
    for fornecedor in Fornecedor.objects.all().iterator():
        primeira = fornecedor.cidades_atendidas.order_by("nome").first()
        if primeira:
            fornecedor.cidade_atendida_id = primeira.pk
            fornecedor.save(update_fields=["cidade_atendida"])


class Migration(migrations.Migration):
    dependencies = [
        ("fornecedores", "0003_fornecedor_cidades_atendidas"),
        ("organizacao", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="fornecedor",
            name="cidade_atendida",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="fornecedores",
                to="organizacao.unidade",
                verbose_name="cidade atendida",
            ),
        ),
        migrations.RunPython(preservar_primeira_cidade, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="fornecedor",
            name="cidades_atendidas",
        ),
    ]
