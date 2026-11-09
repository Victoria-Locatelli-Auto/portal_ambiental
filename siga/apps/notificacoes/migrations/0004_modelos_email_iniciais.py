from django.db import migrations


MODELOS = {
    "ALERTA": (
        "[SIGA-MCM] {{ item.tipo.nome }} vence em {% if dias_restantes == 1 %}1 dia{% else %}{{ dias_restantes }} dias{% endif %} - {{ unidade.nome }}",
        """Prezado(a) {{ unidade.responsavel_nome|default:'responsável' }},

O documento abaixo está próximo do vencimento:

Casa: {{ unidade.nome }} - CNPJ {{ unidade.cnpj }}
Documento: {{ item.tipo.nome }}
Identificação: {{ item.documento.identificacao }}
Vencimento: {{ item.vencimento|date:'d/m/Y' }} ({{ dias_restantes }} dias)
Base legal: {{ item.tipo.base_legal }}

O QUE FAZER
{{ item.tipo.instrucao }}

Acesse o SIGA e envie o documento pela tela Checklist da casa.

Mensagem automática do SIGA - Sistema Integrado de Gestão Ambiental MCM.""",
    ),
    "VENCIDO": (
        "[SIGA-MCM] URGENTE - {{ item.tipo.nome }} VENCIDO há {{ atraso }} dias - {{ unidade.nome }}",
        """ATENÇÃO - DOCUMENTO VENCIDO

Prezado(a) {{ unidade.responsavel_nome|default:'responsável' }},

Casa: {{ unidade.nome }} - CNPJ {{ unidade.cnpj }}
Documento: {{ item.tipo.nome }}
Identificação: {{ item.documento.identificacao }}
Venceu em: {{ item.vencimento|date:'d/m/Y' }} (há {{ atraso }} dias)
Base legal: {{ item.tipo.base_legal }}

O QUE FAZER IMEDIATAMENTE
{{ item.tipo.instrucao }}

Este aviso será reenviado diariamente até a regularização.

SIGA - Sistema Integrado de Gestão Ambiental MCM""",
    ),
    "COBRANCA": (
        "[SIGA-MCM] Checklist da casa {{ unidade.nome }}: {{ total }} documento(s) a enviar",
        """Prezado(a) {{ unidade.responsavel_nome|default:'responsável' }},

A casa {{ unidade.nome }} tem {{ total }} documento(s) do checklist ainda não enviados ao SIGA:

{% for item in itens %}{{ forloop.counter }}. {{ item.tipo.nome }}
   O que fazer: {{ item.tipo.instrucao }}
   Base legal: {{ item.tipo.base_legal|truncatechars:110 }}
{% endfor %}
Acesse o SIGA, abra o Checklist da casa e envie cada documento.

Mensagem semanal automática do SIGA - Sistema Integrado de Gestão Ambiental MCM""",
    ),
    "RESUMO": (
        "[SIGA-MCM] Resumo gerencial mensal de conformidade ambiental",
        """RESUMO GERENCIAL DE CONFORMIDADE AMBIENTAL - SIGA / MCM

{% for r in resumos %}{{ r.unidade.nome }}
Conformidade: {{ r.percentual }}%
Não enviados: {{ r.pendente }}
Vencidos: {{ r.vencido }}
Vencendo em 30 dias: {{ r.critico }}
Em análise: {{ r.em_analise }}
Ação da casa: {{ r.acao_da_casa }} de {{ r.itens_da_casa }} itens

{% endfor %}SIGA - Sistema Integrado de Gestão Ambiental MCM""",
    ),
}


def criar_modelos(apps, schema_editor):
    ModeloEmail = apps.get_model("notificacoes", "ModeloEmail")
    for tipo, (assunto, corpo) in MODELOS.items():
        ModeloEmail.objects.get_or_create(
            tipo=tipo,
            defaults={"assunto": assunto, "corpo": corpo, "ativo": True},
        )


def remover_modelos(apps, schema_editor):
    apps.get_model("notificacoes", "ModeloEmail").objects.filter(
        tipo__in=MODELOS
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("notificacoes", "0003_modeloemail")]
    operations = [migrations.RunPython(criar_modelos, remover_modelos)]
