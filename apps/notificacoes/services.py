"""Regua de notificacoes.

Regras implementadas:
  * um alerta diario para cada documento dentro da antecedencia configurada
    no tipo documental;
  * aviso diario para documento vencido, com escalonamento a diretoria
    apos 15 dias;
  * uma unica cobranca semanal consolidada por casa, com todo o checklist
    pendente - em vez de um e-mail por documento;
  * idempotencia: o mesmo gatilho nao e reenviado duas vezes no mesmo dia.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.compliance.enums import StatusConformidade
from apps.compliance.selectors import ItemChecklist, checklist_da_unidade
from apps.core.models import LogAuditoria
from apps.core.services import registrar
from apps.core.utils import dias_ate, hoje
from apps.accounts.models import PERFIS_ESCOPO_GLOBAL, Usuario
from apps.notificacoes.models import (
    ModeloEmail,
    Notificacao,
    NotificacaoSistema,
    TipoNotificacao,
)
from apps.organizacao.models import Unidade

logger = logging.getLogger(__name__)


def renderizar_email(
    tipo: str, contexto: dict, assunto_padrao: str, template_padrao: str
) -> tuple[str, str]:
    """Renderiza o modelo configurado; usa o texto original enquanto não houver configuração."""
    modelo = ModeloEmail.objects.filter(tipo=tipo, ativo=True).first()
    if modelo:
        contexto_template = Context(contexto, autoescape=False)
        return (
            Template(modelo.assunto).render(contexto_template).strip(),
            Template(modelo.corpo).render(contexto_template),
        )
    return assunto_padrao, render_to_string(template_padrao, contexto)


@dataclass(slots=True)
class Mensagem:
    """Uma notificacao pronta para virar e-mail."""

    tipo: str
    unidade: Unidade
    destinatario: str
    assunto: str
    template: str
    contexto: dict
    chave: str
    copias: list[str] = field(default_factory=list)
    documento_id: int | None = None
    gatilho_dias: int | None = None


def _copias(*, incluir_gestao: bool, incluir_diretoria: bool = False) -> list[str]:
    cfg = settings.SIGA
    destinos = [cfg["EMAIL_CONSULTORIA"]]
    if incluir_gestao:
        destinos.append(cfg["EMAIL_GESTAO"])
    if incluir_diretoria:
        destinos.append(cfg["EMAIL_DIRETORIA"])
    return destinos


def criar_avisos_no_sistema(notificacao: Notificacao) -> int:
    """Replica um alerta de e-mail para os usuários com acesso à casa."""
    usuarios = Usuario.objects.filter(is_active=True, recebe_notificacoes=True)
    if notificacao.unidade_id:
        usuarios = usuarios.filter(
            Q(unidade_id=notificacao.unidade_id) | Q(perfil__in=PERFIS_ESCOPO_GLOBAL)
        )
    if notificacao.documento_id:
        link = reverse(
            "compliance:detalhe_documento", args=[notificacao.documento.uuid]
        )
    elif notificacao.unidade_id:
        link = reverse("dashboard:checklist", args=[notificacao.unidade.codigo])
    else:
        link = reverse("dashboard:painel")

    avisos = [
        NotificacaoSistema(
            usuario=usuario,
            origem_email=notificacao,
            tipo=notificacao.tipo,
            unidade=notificacao.unidade,
            documento=notificacao.documento,
            titulo=notificacao.assunto.removeprefix("[SIGA-MCM] "),
            mensagem=notificacao.corpo,
            link=link,
        )
        for usuario in usuarios.distinct()
    ]
    criados = NotificacaoSistema.objects.bulk_create(avisos, ignore_conflicts=True)
    return len(criados)


def montar_alertas(unidade: Unidade, referencia: date | None = None) -> list[Mensagem]:
    """Alertas de vencimento e avisos de vencido de uma casa."""
    referencia = referencia or hoje()
    mensagens: list[Mensagem] = []

    for item in checklist_da_unidade(unidade):
        doc = item.documento
        if doc is None or doc.data_vencimento is None:
            continue

        dias_restantes = dias_ate(doc.data_vencimento, referencia)
        if dias_restantes is None:
            continue

        destino_casa = item.da_casa
        para = (
            unidade.destinatario_notificacao
            if destino_casa
            else settings.SIGA["EMAIL_CONSULTORIA"]
        )
        if not para:
            logger.warning("Casa %s sem destinatario de notificacao", unidade.codigo)
            continue

        if dias_restantes < 0:
            atraso = abs(dias_restantes)
            escalar = atraso > settings.SIGA["ESCALONAR_DIRETORIA_APOS_DIAS"]
            mensagens.append(
                Mensagem(
                    tipo=TipoNotificacao.VENCIDO,
                    unidade=unidade,
                    destinatario=para,
                    copias=_copias(incluir_gestao=True, incluir_diretoria=escalar),
                    assunto=(
                        f"[SIGA-MCM] URGENTE - {item.tipo.nome} VENCIDO "
                        f"ha {atraso} dias - {unidade.nome}"
                    ),
                    template="notificacoes/email_vencido.txt",
                    contexto={"item": item, "unidade": unidade, "atraso": atraso},
                    chave=f"VENCIDO:{unidade.pk}:{doc.pk}:{referencia:%Y-%m-%d}",
                    documento_id=doc.pk,
                    gatilho_dias=dias_restantes,
                )
            )
            continue

        if dias_restantes > item.tipo.dias_alerta:
            continue

        prazo = "1 dia" if dias_restantes == 1 else f"{dias_restantes} dias"
        mensagens.append(
            Mensagem(
                tipo=TipoNotificacao.ALERTA,
                unidade=unidade,
                destinatario=para,
                copias=_copias(incluir_gestao=dias_restantes <= settings.SIGA["DIAS_CRITICO"]),
                assunto=(
                    f"[SIGA-MCM] {item.tipo.nome} vence em {prazo} - "
                    f"{unidade.nome}"
                ),
                template="notificacoes/email_alerta.txt",
                contexto={
                    "item": item,
                    "unidade": unidade,
                    "dias_restantes": dias_restantes,
                },
                chave=f"ALERTA:{unidade.pk}:{doc.pk}:{referencia:%Y-%m-%d}",
                documento_id=doc.pk,
                gatilho_dias=dias_restantes,
            )
        )
    return mensagens


def montar_cobranca(unidade: Unidade, referencia: date | None = None) -> Mensagem | None:
    """Uma unica cobranca com todo o checklist pendente da casa."""
    referencia = referencia or hoje()
    pendentes: list[ItemChecklist] = [
        i
        for i in checklist_da_unidade(unidade)
        if i.da_casa and i.status == StatusConformidade.PENDENTE
    ]
    if not pendentes:
        return None
    para = unidade.destinatario_notificacao
    if not para:
        return None

    semana = referencia.isocalendar()
    return Mensagem(
        tipo=TipoNotificacao.COBRANCA,
        unidade=unidade,
        destinatario=para,
        copias=_copias(incluir_gestao=False),
        assunto=(
            f"[SIGA-MCM] Checklist da casa {unidade.nome}: "
            f"{len(pendentes)} documento(s) a enviar"
        ),
        template="notificacoes/email_cobranca.txt",
        contexto={"unidade": unidade, "itens": pendentes, "total": len(pendentes)},
        chave=f"COBRANCA:{unidade.pk}:{semana.year}-W{semana.week:02d}",
    )


@transaction.atomic
def despachar(mensagem: Mensagem) -> Notificacao | None:
    """Persiste e envia. Retorna None quando o gatilho ja foi disparado."""
    if existente := Notificacao.objects.filter(chave_idempotencia=mensagem.chave).first():
        criar_avisos_no_sistema(existente)
        return None

    assunto, corpo = renderizar_email(
        mensagem.tipo, mensagem.contexto, mensagem.assunto, mensagem.template
    )
    try:
        notificacao = Notificacao.objects.create(
            tipo=mensagem.tipo,
            unidade=mensagem.unidade,
            documento_id=mensagem.documento_id,
            gatilho_dias=mensagem.gatilho_dias,
            destinatario=mensagem.destinatario,
            copias="; ".join(mensagem.copias),
            assunto=assunto,
            corpo=corpo,
            chave_idempotencia=mensagem.chave,
        )
    except IntegrityError:  # corrida entre workers
        return None

    criar_avisos_no_sistema(notificacao)

    try:
        email = EmailMultiAlternatives(
            subject=assunto,
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[mensagem.destinatario],
            cc=mensagem.copias,
        )
        email.send(fail_silently=False)
    except Exception as exc:
        logger.exception("Falha ao enviar notificacao %s", notificacao.pk)
        notificacao.situacao = Notificacao.Situacao.FALHA
        notificacao.erro = str(exc)
        notificacao.save(update_fields=["situacao", "erro"])
        return notificacao

    notificacao.situacao = Notificacao.Situacao.ENVIADA
    notificacao.enviada_em = timezone.now()
    notificacao.save(update_fields=["situacao", "enviada_em"])
    registrar(
        LogAuditoria.Acao.NOTIFICACAO,
        assunto,
        detalhe=f"para {mensagem.destinatario}",
        entidade="Notificacao",
        entidade_id=notificacao.pk,
    )
    return notificacao


def processar_alertas(referencia: date | None = None) -> list[Notificacao]:
    enviadas: list[Notificacao] = []
    for unidade in Unidade.objects.ativos():
        for mensagem in montar_alertas(unidade, referencia):
            if (n := despachar(mensagem)) is not None:
                enviadas.append(n)
    return enviadas


def processar_cobrancas(referencia: date | None = None) -> list[Notificacao]:
    enviadas: list[Notificacao] = []
    for unidade in Unidade.objects.ativos():
        mensagem = montar_cobranca(unidade, referencia)
        if mensagem and (n := despachar(mensagem)) is not None:
            enviadas.append(n)
    return enviadas


def previa(referencia: date | None = None) -> list[Mensagem]:
    """Simulacao do disparo sem gravar nem enviar nada."""
    mensagens: list[Mensagem] = []
    for unidade in Unidade.objects.ativos():
        mensagens.extend(montar_alertas(unidade, referencia))
        if cobranca := montar_cobranca(unidade, referencia):
            mensagens.append(cobranca)
    return mensagens
