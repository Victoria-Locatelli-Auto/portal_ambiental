from rest_framework import serializers, viewsets

from apps.auditoria.models import NaoConformidade
from apps.organizacao.selectors import unidades_do_usuario


class NaoConformidadeSerializer(serializers.ModelSerializer):
    unidade_nome = serializers.CharField(source="unidade.nome", read_only=True)
    dias_para_prazo = serializers.IntegerField(read_only=True)
    prazo_vencido = serializers.BooleanField(read_only=True)

    class Meta:
        model = NaoConformidade
        fields = [
            "uuid", "codigo", "unidade", "unidade_nome", "origem", "data_abertura",
            "descricao", "requisito_violado", "gravidade", "situacao",
            "o_que", "por_que", "onde", "quem", "prazo", "como", "quanto",
            "custo_estimado", "dias_para_prazo", "prazo_vencido",
        ]
        read_only_fields = ["uuid", "codigo"]


class NaoConformidadeViewSet(viewsets.ModelViewSet):
    serializer_class = NaoConformidadeSerializer
    lookup_field = "uuid"
    filterset_fields = ["unidade", "gravidade", "situacao", "origem"]

    def get_queryset(self):
        return NaoConformidade.objects.filter(
            unidade__in=unidades_do_usuario(self.request.user)
        ).select_related("unidade")
