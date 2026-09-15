# Decisões de arquitetura

## Por que Django e não FastAPI
O domínio é gestão documental multi-tenant com autenticação, permissões, upload, admin e
agendamento. Django entrega ORM com migrações, admin gerado, sistema de auth e storage de
arquivos prontos. Com FastAPI seria preciso escrever tudo isso à mão.

## Camadas
`models` (estrutura) → `selectors` (leitura) → `services` (escrita) → `views`/`api` (HTTP).

Views não fazem query nem regra. Isso garante que a mesma operação — enviar um documento —
se comporte igual vinda da tela, da API ou de um script. As permissões ficam num lugar só.

## Status calculado, não armazenado
Um campo `status` no banco ficaria desatualizado no instante seguinte: documento vence com o
tempo passando, sem ninguém tocar no registro. `calcular_status()` é função pura sobre
datas — sem cron de atualização, sem inconsistência.

Custo: não dá pra filtrar por status direto no SQL. Aceitável na escala do problema
(7 casas × ~32 requisitos = 224 linhas). Se crescer, a saída é uma coluna materializada
atualizada por signal, mantendo a função pura como fonte de verdade.

## Aplicabilidade por flag, não por lista
A alternativa seria uma tabela ligando casa a requisitos. Ficaria desatualizada toda vez que
uma casa mudasse de característica, e alguém teria que lembrar de atualizar. Com flags, a
verdade fica num lugar só: as características reais da casa.

## Versionamento com `versao_corrente`
Alternativas descartadas: tabela de histórico separada (duplica schema) e soft-delete puro
(perde a ordem). A flag booleana com índice resolve a consulta mais frequente do sistema
("qual é o documento vigente desta casa para este tipo") com um índice composto.

## Idempotência das notificações
Sem ela, reiniciar o worker ou rodar o comando duas vezes duplica e-mail para a coordenadora
— o caminho mais rápido para o sistema ser ignorado. `chave_idempotencia` com constraint
única no banco resolve inclusive corrida entre workers.

## Cobrança consolidada
A primeira versão mandava um e-mail por documento pendente: 194 e-mails numa segunda-feira.
Ninguém leria. Agora é um por casa, com a lista completa. Reduziu para 7.

## Exclusão lógica
Registro ambiental não some. `SoftDeleteModel` marca `excluido_em`; a trilha de auditoria é
`readonly` até no admin do Django.
