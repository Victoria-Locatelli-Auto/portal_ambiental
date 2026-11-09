from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fornecedores", "0002_fornecedor_anexo_contrato"),
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
    ]
