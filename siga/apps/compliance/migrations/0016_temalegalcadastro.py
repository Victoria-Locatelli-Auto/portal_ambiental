from django.db import migrations, models
import django.core.validators


TEMAS = [
    ("CONDICIONANTES", "Condicionantes"),
    ("LICENCIAMENTO", "Licenciamento"),
    ("HIDRICOS", "Recursos hídricos"),
    ("FEDERAL", "Conformidade federal"),
    ("RESIDUOS", "Resíduos"),
    ("EFLUENTES", "Efluentes"),
    ("SOLO", "Solo e a água subterrânea"),
    ("POSTO", "Posto de combustível"),
    ("MONITORAMENTO", "Monitoramento"),
    ("SGA", "Gestão/SGA"),
    ("EMERGENCIA", "Emergência"),
    ("SEGURANCA", "Segurança"),
    ("SST", "Saúde e segurança do trabalho"),
    ("TERCEIROS", "Terceiros"),
]


def cadastrar_temas(apps, schema_editor):
    Tema = apps.get_model("compliance", "TemaLegalCadastro")
    for ordem, (codigo, nome) in enumerate(TEMAS, start=1):
        Tema.objects.get_or_create(
            codigo=codigo,
            defaults={"nome": nome, "ordem": ordem * 10, "ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [("compliance", "0015_documento_fornecedor")]
    operations = [
        migrations.CreateModel(
            name="TemaLegalCadastro",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="criado em")),
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("codigo", models.CharField(max_length=20, unique=True, validators=[django.core.validators.RegexValidator(message="Use somente letras maiúsculas, números e sublinhado.", regex="^[A-Z0-9_]+$")], verbose_name="código")),
                ("nome", models.CharField(max_length=120, unique=True, verbose_name="nome")),
                ("ordem", models.PositiveSmallIntegerField(default=0, verbose_name="ordem de exibição")),
                ("ativo", models.BooleanField(db_index=True, default=True, verbose_name="ativo")),
            ],
            options={"verbose_name": "tema legal", "verbose_name_plural": "temas legais", "ordering": ("ordem", "nome")},
        ),
        migrations.RunPython(cadastrar_temas, migrations.RunPython.noop),
    ]
