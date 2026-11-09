# Generated manually for the fornecedores module.
import uuid

import apps.fornecedores.models
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Fornecedor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="criado em")),
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("razao_social", models.CharField(max_length=180, verbose_name="razão social")),
                ("nome_fantasia", models.CharField(blank=True, max_length=180, verbose_name="nome fantasia")),
                ("cnpj_cpf", models.CharField(max_length=18, unique=True, verbose_name="CNPJ/CPF")),
                ("servico_fornecido", models.CharField(max_length=220, verbose_name="produto ou serviço fornecido")),
                ("responsavel", models.CharField(blank=True, max_length=160, verbose_name="pessoa de contato")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="e-mail")),
                ("telefone", models.CharField(blank=True, max_length=32, verbose_name="telefone")),
                ("endereco", models.CharField(blank=True, max_length=255, verbose_name="endereço")),
                ("observacoes", models.TextField(blank=True, verbose_name="observações")),
                ("ativo", models.BooleanField(db_index=True, default=True, verbose_name="ativo")),
            ],
            options={"verbose_name": "fornecedor", "verbose_name_plural": "fornecedores", "ordering": ("razao_social",)},
        ),
        migrations.CreateModel(
            name="Contrato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="criado em")),
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("numero", models.CharField(max_length=80, verbose_name="número do contrato")),
                ("objeto", models.TextField(verbose_name="objeto do contrato")),
                ("data_inicio", models.DateField(verbose_name="início da vigência")),
                ("data_fim", models.DateField(verbose_name="fim da vigência")),
                ("valor", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name="valor do contrato")),
                ("situacao", models.CharField(choices=[("VIGENTE", "Vigente"), ("ENCERRADO", "Encerrado"), ("SUSPENSO", "Suspenso"), ("CANCELADO", "Cancelado")], db_index=True, default="VIGENTE", max_length=12, verbose_name="situação")),
                ("arquivo", models.FileField(blank=True, help_text="Formatos aceitos: PDF, DOC, DOCX ou ODT.", upload_to=apps.fornecedores.models.caminho_contrato, validators=[django.core.validators.FileExtensionValidator(["pdf", "doc", "docx", "odt"])], verbose_name="arquivo do contrato")),
                ("observacoes", models.TextField(blank=True, verbose_name="observações")),
                ("fornecedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="contratos", to="fornecedores.fornecedor", verbose_name="fornecedor")),
            ],
            options={"verbose_name": "contrato", "verbose_name_plural": "contratos", "ordering": ("-data_fim", "numero")},
        ),
        migrations.AddConstraint(
            model_name="contrato",
            constraint=models.UniqueConstraint(fields=("fornecedor", "numero"), name="contrato_numero_unico_fornecedor"),
        ),
    ]
