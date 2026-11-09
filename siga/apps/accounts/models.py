"""Usuario customizado com perfil de acesso e escopo por casa."""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from apps.core.models import TimestampedModel


class Perfil(models.TextChoices):
    """Perfis do SIGA.

    O perfil define os modulos visiveis e o escopo de dados. Perfis com escopo
    proprio so enxergam a casa vinculada ao usuario.
    """

    ADMIN = "ADMIN", "Administrador do sistema"
    GESTOR = "GESTOR", "Gestor MCM (matriz)"
    CONSULTORIA = "CONSULTORIA", "STX Engenharia (contratada)"
    UNIDADE = "UNIDADE", "Responsavel de casa"
    AUDITOR = "AUDITOR", "Auditor (somente leitura)"


#: Perfis que enxergam todas as casas.
PERFIS_ESCOPO_GLOBAL = frozenset(
    {Perfil.ADMIN, Perfil.GESTOR, Perfil.CONSULTORIA, Perfil.AUDITOR}
)
#: Perfis autorizados a validar tecnicamente um documento enviado.
PERFIS_VALIDADORES = frozenset({Perfil.ADMIN, Perfil.CONSULTORIA})
#: Perfis sem permissao de escrita.
PERFIS_SOMENTE_LEITURA = frozenset({Perfil.AUDITOR})


class UsuarioManager(UserManager):
    def da_consultoria(self):
        return self.filter(perfil=Perfil.CONSULTORIA, is_active=True)

    def responsaveis_de_casa(self):
        return self.filter(perfil=Perfil.UNIDADE, is_active=True)


class Usuario(AbstractUser, TimestampedModel):
    email = models.EmailField("e-mail", unique=True)
    nome_completo = models.CharField("nome completo", max_length=160)
    cargo = models.CharField("cargo", max_length=160, blank=True)
    telefone = models.CharField("telefone", max_length=32, blank=True)
    perfil = models.CharField(
        "perfil de acesso", max_length=20, choices=Perfil.choices, default=Perfil.UNIDADE
    )
    unidade = models.ForeignKey(
        "organizacao.Unidade",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="casa vinculada",
        help_text="Obrigatorio para o perfil Responsavel de casa.",
    )
    recebe_notificacoes = models.BooleanField("recebe notificacoes", default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "nome_completo"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ("nome_completo",)

    def __str__(self) -> str:
        return self.nome_exibicao

    @property
    def nome_exibicao(self) -> str:
        return self.nome_completo or self.get_username()

    # ------------------------------------------------------------------ regras
    @property
    def escopo_global(self) -> bool:
        """True quando o usuario enxerga as 7 casas."""
        return self.perfil in PERFIS_ESCOPO_GLOBAL

    @property
    def somente_leitura(self) -> bool:
        return self.perfil in PERFIS_SOMENTE_LEITURA

    @property
    def pode_validar(self) -> bool:
        """Somente a consultoria contratada e o administrador validam documentos."""
        return self.perfil in PERFIS_VALIDADORES

    def unidades_visiveis(self):
        """QuerySet de casas que este usuario pode enxergar."""
        from apps.organizacao.models import Unidade

        qs = Unidade.objects.ativos()
        if self.escopo_global:
            return qs
        return qs.filter(pk=self.unidade_id) if self.unidade_id else qs.none()

    def pode_acessar(self, unidade) -> bool:
        return self.escopo_global or self.unidade_id == getattr(unidade, "pk", unidade)
