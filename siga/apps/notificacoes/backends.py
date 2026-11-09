"""Backend de e-mail do Microsoft 365 usando OAuth2 e Microsoft Graph."""
from __future__ import annotations

import json
from email.utils import parseaddr
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address


class MicrosoftGraphEmailBackend(BaseEmailBackend):
    """Envia mensagens pela API Graph com credenciais de aplicação."""

    def _token(self) -> str:
        tenant = settings.MICROSOFT_TENANT_ID
        dados = urlencode(
            {
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            }
        ).encode()
        requisicao = Request(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data=dados,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(requisicao, timeout=30) as resposta:  # noqa: S310
            return json.load(resposta)["access_token"]

    @staticmethod
    def _destinatarios(enderecos) -> list[dict]:
        destinatarios = []
        for endereco in enderecos:
            endereco_seguro = sanitize_address(endereco, "utf-8")
            email = parseaddr(endereco_seguro)[1]
            destinatarios.append({"emailAddress": {"address": email}})
        return destinatarios

    def send_messages(self, email_messages) -> int:
        if not email_messages:
            return 0
        token = self._token()
        enviados = 0
        remetente = settings.MICROSOFT_SENDER_EMAIL or parseaddr(settings.DEFAULT_FROM_EMAIL)[1]
        endpoint = f"https://graph.microsoft.com/v1.0/users/{remetente}/sendMail"

        for mensagem in email_messages:
            payload = {
                "message": {
                    "subject": mensagem.subject,
                    "body": {"contentType": "Text", "content": mensagem.body},
                    "toRecipients": self._destinatarios(mensagem.to),
                    "ccRecipients": self._destinatarios(mensagem.cc),
                    "bccRecipients": self._destinatarios(mensagem.bcc),
                },
                "saveToSentItems": True,
            }
            requisicao = Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                method="POST",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(requisicao, timeout=30) as resposta:  # noqa: S310
                    if resposta.status == 202:
                        enviados += 1
            except (HTTPError, URLError) as erro:
                if self.fail_silently:
                    continue
                detalhe = ""
                if isinstance(erro, HTTPError):
                    detalhe = erro.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"Falha no Microsoft Graph ({getattr(erro, 'code', erro)}): {detalhe}"
                ) from erro
        return enviados
