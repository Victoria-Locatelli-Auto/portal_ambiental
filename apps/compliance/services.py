"""Regras de escrita do dominio de conformidade.

Toda mutacao passa por aqui: valida permissao, versiona, grava trilha de
auditoria e dispara notificacao. Views e API nao falam com o ORM diretamente.
"""
from __future__ import annotations

from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.compliance.enums import SituacaoDocumento
from apps.compliance.models import Documento, TipoDocumento
from apps.core.models import LogAuditoria
from apps.core.services import registrar
from apps.organizacao.models import Unidade


class RegraDeNegocio(ValidationError):
    """Erro de dominio, exibido ao usuario sem stack trace."""


@transaction.atomic
def enviar_documento(
    *,
    unidade: Unidade,
    tipo: TipoDocumento,
    identificacao: str,
    data_emissao: date,
    usuario,
    numero_protocolo: str = "",
    data_vencimento: date | None = None,
    sem_data_validade: bool = False,
    arquivo=None,
    observacao: str = "",
) -> Documento:
    """Registra uma nova versao de documento e a coloca em analise.

    Fecha automaticamente a versao anterior, calcula o vencimento pela
    periodicidade do tipo quando nao informado, e encerra a cobranca
    automatica daquele item.
    """
    if usuario.somente_leitura:
        raise PermissionDenied("Perfil somente leitura nao pode enviar documentos.")
    if not usuario.pode_acessar(unidade):
        raise PermissionDenied("Voce nao tem acesso a esta casa.")
    if not tipo.aplica_a(unidade):
        raise RegraDeNegocio(
            f"O requisito {tipo.codigo} nao e aplicavel a casa {unidade.nome} "
            "conforme as caracteristicas cadastradas."
        )
    if data_emissao > timezone.localdate():
        raise RegraDeNegocio("A data de emissao nao pode ser futura.")

    if sem_data_validade:
        data_vencimento = None
    elif data_vencimento is None:
        data_vencimento = tipo.calcular_vencimento(data_emissao)
    if data_vencimento and data_vencimento <= data_emissao:
        raise RegraDeNegocio("O vencimento deve ser posterior a emissao.")

    anterior = Documento.objects.vigentes().filter(unidade=unidade, tipo=tipo).first()
    if anterior:
        anterior.versao_corrente = False
        anterior.save(update_fields=["versao_corrente", "atualizado_em"])

    documento = Documento.objects.create(
        unidade=unidade,
        tipo=tipo,
        identificacao=identificacao or tipo.nome,
        numero_protocolo=numero_protocolo,
        data_emissao=data_emissao,
        data_vencimento=data_vencimento,
        arquivo=arquivo,
        situacao=SituacaoDocumento.AGUARDANDO,
        versao=(anterior.versao + 1) if anterior else 1,
        versao_corrente=True,
        enviado_por=usuario,
        observacao=observacao,
    )
    registrar(
        LogAuditoria.Acao.ENVIO,
        f"{tipo.nome} - {unidade.nome}",
        detalhe=f"versao {documento.versao} | {identificacao}",
        usuario=usuario,
        entidade="Documento",
        entidade_id=documento.pk,
    )
    return documento


@transaction.atomic
def enviar_documentos(*, arquivos=None, identificacao: str = "", **dados) -> list[Documento]:
    """Salva um lote de anexos como versões rastreáveis do mesmo requisito."""
    lista = list(arquivos or [None])
    if not lista:
        lista = [None]
    documentos = []
    for arquivo in lista:
        nome = getattr(arquivo, "name", "")
        identificacao_do_arquivo = identificacao
        if len(lista) > 1 and nome:
            identificacao_do_arquivo = f"{identificacao or dados['tipo'].nome} — {nome}"
        documentos.append(
            enviar_documento(
                arquivo=arquivo,
                identificacao=identificacao_do_arquivo,
                **dados,
            )
        )
    return documentos


@transaction.atomic
def validar_documento(*, documento: Documento, usuario) -> Documento:
    """Aprova tecnicamente o documento. Exclusivo da consultoria e do admin."""
    if not usuario.pode_validar:
        raise PermissionDenied("Apenas a STX Engenharia e o administrador validam documentos.")
    if documento.situacao == SituacaoDocumento.VALIDADO:
        raise RegraDeNegocio("Este documento ja esta validado.")

    documento.situacao = SituacaoDocumento.VALIDADO
    documento.validado_por = usuario
    documento.validado_em = timezone.now()
    documento.motivo_rejeicao = ""
    documento.save(update_fields=["situacao", "validado_por", "validado_em", "motivo_rejeicao"])

    registrar(
        LogAuditoria.Acao.VALIDACAO,
        f"{documento.tipo.nome} - {documento.unidade.nome}",
        usuario=usuario,
        entidade="Documento",
        entidade_id=documento.pk,
    )
    return documento


@transaction.atomic
def rejeitar_documento(*, documento: Documento, usuario, motivo: str) -> Documento:
    """Devolve o documento a casa. Volta a contar como pendencia."""
    if not usuario.pode_validar:
        raise PermissionDenied("Apenas a STX Engenharia e o administrador avaliam documentos.")
    if not motivo.strip():
        raise RegraDeNegocio("Informe o motivo da rejeicao para orientar a casa.")

    documento.situacao = SituacaoDocumento.REJEITADO
    documento.motivo_rejeicao = motivo
    documento.validado_por = usuario
    documento.validado_em = timezone.now()
    documento.save(update_fields=["situacao", "motivo_rejeicao", "validado_por", "validado_em"])

    registrar(
        LogAuditoria.Acao.REJEICAO,
        f"{documento.tipo.nome} - {documento.unidade.nome}",
        detalhe=motivo,
        usuario=usuario,
        entidade="Documento",
        entidade_id=documento.pk,
    )
    return documento
