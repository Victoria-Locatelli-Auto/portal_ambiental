from django.db import migrations, models


def preservar_cidade_atual(apps, schema_editor):
    Fornecedor = apps.get_model("fornecedores", "Fornecedor")
    for fornecedor in Fornecedor.objects.exclude(cidade_atendida_id=None).iterator():
        fornecedor.cidades_atendidas.add(fornecedor.cidade_atendida_id)


class Migration(migrations.Migration):
    dependencies = [
        ("fornecedores", "0004_cidade_atendida_radio"),
        ("organizacao", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="fornecedor",
            name="cidades_atendidas",
            field=models.ManyToManyField(
                blank=True,
                related_name="fornecedores",
                to="organizacao.unidade",
                verbose_name="cidades atendidas",
            ),
        ),
        migrations.RunPython(preservar_cidade_atual, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="fornecedor",
            name="cidade_atendida",
        ),
    ]
