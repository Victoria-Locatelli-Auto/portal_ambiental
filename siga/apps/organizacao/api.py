from rest_framework import serializers, viewsets

from apps.organizacao.models import Unidade
from apps.organizacao.selectors import unidades_do_usuario


class UnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = [
            "uuid",
            "codigo",
            "nome",
            "uf",
            "municipio",
            "cnpj",
            "atividade",
            "potencial_poluidor",
            "imovel",
            "orgao_estadual",
            "orgao_municipal",
            "tem_oficina",
            "tem_poco",
            "opera_em_posto",
            "responsavel_nome",
            "responsavel_email",
            "ultima_visita_tecnica",
        ]


class UnidadeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UnidadeSerializer
    lookup_field = "uuid"
    filterset_fields = ["uf", "potencial_poluidor", "tem_oficina", "tem_poco"]

    def get_queryset(self):
        return unidades_do_usuario(self.request.user)
