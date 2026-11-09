from rest_framework import serializers, viewsets
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.compliance import services
from apps.compliance.models import Documento, TipoDocumento
from apps.compliance.selectors import checklist_da_unidade
from apps.organizacao.models import Unidade
from apps.organizacao.selectors import unidades_do_usuario


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = [
            "uuid", "codigo", "nome", "tema", "periodicidade_meses", "dias_alerta",
            "aplicabilidade", "responsavel_execucao", "base_legal", "instrucao",
            "nota_tecnica", "ativo",
        ]


class TipoDocumentoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TipoDocumentoSerializer
    queryset = TipoDocumento.objects.ativos()
    lookup_field = "codigo"
    filterset_fields = ["tema", "aplicabilidade", "responsavel_execucao"]


class DocumentoSerializer(serializers.ModelSerializer):
    unidade_nome = serializers.CharField(source="unidade.nome", read_only=True)
    tipo_nome = serializers.CharField(source="tipo.nome", read_only=True)
    status = serializers.CharField(read_only=True)
    dias_para_vencer = serializers.IntegerField(read_only=True)

    class Meta:
        model = Documento
        fields = [
            "uuid", "unidade", "unidade_nome", "tipo", "tipo_nome", "fornecedor", "identificacao",
            "numero_protocolo", "arquivo", "data_emissao", "data_vencimento", "situacao", "versao",
            "status", "dias_para_vencer", "observacao",
        ]
        read_only_fields = ["uuid", "versao", "situacao"]

    def validate_data_emissao(self, valor):
        if valor > timezone.localdate():
            raise serializers.ValidationError(
                "A data de emissão não pode ser posterior à data atual."
            )
        return valor


class DocumentoViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentoSerializer
    lookup_field = "uuid"
    filterset_fields = ["unidade", "tipo", "situacao"]

    def get_queryset(self):
        return (
            Documento.objects.vigentes()
            .filter(unidade__in=unidades_do_usuario(self.request.user))
            .select_related("unidade", "tipo")
        )

    def perform_create(self, serializer) -> None:
        dados = serializer.validated_data
        serializer.instance = services.enviar_documento(
            unidade=dados["unidade"],
            tipo=dados["tipo"],
            usuario=self.request.user,
            identificacao=dados.get("identificacao", ""),
            numero_protocolo=dados.get("numero_protocolo", ""),
            data_emissao=dados["data_emissao"],
            data_vencimento=dados.get("data_vencimento"),
            fornecedor=dados.get("fornecedor"),
            arquivo=dados.get("arquivo"),
            observacao=dados.get("observacao", ""),
        )

    @action(detail=True, methods=["post"])
    def validar(self, request, uuid=None):  # noqa: ARG002
        documento = self.get_object()
        services.validar_documento(documento=documento, usuario=request.user)
        return Response(self.get_serializer(documento).data)

    @action(detail=False, methods=["get"], url_path=r"checklist/(?P<codigo>[^/.]+)")
    def checklist(self, request, codigo: str):
        unidade = unidades_do_usuario(request.user).get(codigo=codigo)
        itens = checklist_da_unidade(unidade)
        return Response(
            [
                {
                    "tipo": i.tipo.codigo,
                    "documento": i.tipo.nome,
                    "status": i.status,
                    "acao": i.verbo,
                    "quem_faz": i.tipo.get_responsavel_execucao_display(),
                    "instrucao": i.tipo.instrucao,
                    "vencimento": i.vencimento,
                    "dias": i.dias,
                    "da_casa": i.da_casa,
                }
                for i in itens
            ]
        )
