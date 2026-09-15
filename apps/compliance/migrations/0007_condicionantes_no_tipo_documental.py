from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("compliance", "0006_processorenovacao")]

    operations = [
        migrations.AddField(
            model_name="tipodocumento",
            name="regras_condicionantes",
            field=models.TextField(
                blank=True,
                help_text="Descreva cada condicionante, seu prazo e a evidência necessária.",
                verbose_name="regras a serem seguidas",
            ),
        ),
        migrations.AlterField(
            model_name="tipodocumento",
            name="tema",
            field=models.CharField(
                choices=[
                    ("CONDICIONANTES", "Condicionantes"),
                    ("LICENCIAMENTO", "Licenciamento"),
                    ("HIDRICOS", "Recursos hidricos"),
                    ("FEDERAL", "Conformidade federal"),
                    ("RESIDUOS", "Residuos"),
                    ("EFLUENTES", "Efluentes"),
                    ("SOLO", "Solo e agua subterranea"),
                    ("POSTO", "Posto de combustivel"),
                    ("MONITORAMENTO", "Monitoramento"),
                    ("SGA", "Gestao / SGA"),
                    ("EMERGENCIA", "Emergencia"),
                    ("SEGURANCA", "Seguranca"),
                    ("SST", "Saude e seguranca do trabalho"),
                    ("TERCEIROS", "Terceiros"),
                ],
                max_length=20,
                verbose_name="tema legal",
            ),
        ),
    ]
