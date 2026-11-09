from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("compliance", "0007_condicionantes_no_tipo_documental")]

    operations = [
        migrations.RemoveField(
            model_name="tipodocumento",
            name="regras_condicionantes",
        ),
    ]
