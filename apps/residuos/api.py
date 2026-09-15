from rest_framework import serializers, viewsets

from apps.organizacao.selectors import unidades_do_usuario
from apps.residuos.models import MovimentacaoResiduo


class MovimentacaoResiduoSerializer(serializers.ModelSerializer):
    unidade_nome = serializers.CharField(source="unidade.nome", read_only=True)
    rastreavel = serializers.BooleanField(read_only=True)

    class Meta:
        model = MovimentacaoResiduo
        fields = [
            "uuid", "unidade", "unidade_nome", "residuo", "classe", "codigo_ibama",
            "quantidade", "unidade_medida", "destinacao", "destinador",
            "numero_mtr", "numero_cdf", "data_movimentacao", "rastreavel", "observacao",
        ]


class MovimentacaoResiduoViewSet(viewsets.ModelViewSet):
    serializer_class = MovimentacaoResiduoSerializer
    lookup_field = "uuid"
    filterset_fields = ["unidade", "classe"]

    def get_queryset(self):
        return MovimentacaoResiduo.objects.filter(
            unidade__in=unidades_do_usuario(self.request.user)
        ).select_related("unidade")
