from django.db import migrations


APLICABILIDADES_ANTIGAS = {
    "U_GURUPI": "UNIDADE:U1",
    "U_ARAGUAINA": "UNIDADE:U2",
    "U_BALSAS": "UNIDADE:U3",
    "U_SAO_LUIS": "UNIDADE:U5",
    "U_TERESINA": "UNIDADE:U6",
    "U_POSTO_ROMA": "UNIDADE:U7",
    "U_PALMAS": "UNIDADE:U8",
}

EXECUTORES_ANTIGOS = {
    "GURUPI": "UNIDADE:U1",
    "ARAGUAINA": "UNIDADE:U2",
    "BALSAS": "UNIDADE:U3",
    "SAO_LUIS": "UNIDADE:U5",
    "TERESINA": "UNIDADE:U6",
    "POSTO_ROMA": "UNIDADE:U7",
    "PALMAS": "UNIDADE:U8",
}


def _converter(valor, mapa):
    return ",".join(mapa.get(item.strip(), item.strip()) for item in valor.split(",") if item.strip())


def migrar_referencias(apps, schema_editor):
    TipoDocumento = apps.get_model("compliance", "TipoDocumento")
    for tipo in TipoDocumento.objects.all().only(
        "pk", "aplicabilidade", "responsavel_execucao"
    ):
        tipo.aplicabilidade = _converter(tipo.aplicabilidade, APLICABILIDADES_ANTIGAS)
        tipo.responsavel_execucao = _converter(
            tipo.responsavel_execucao, EXECUTORES_ANTIGOS
        )
        tipo.save(update_fields=["aplicabilidade", "responsavel_execucao"])


class Migration(migrations.Migration):
    dependencies = [
        ("compliance", "0011_alter_tipodocumento_cor_agenda"),
    ]

    operations = [
        migrations.RunPython(migrar_referencias, migrations.RunPython.noop),
    ]
