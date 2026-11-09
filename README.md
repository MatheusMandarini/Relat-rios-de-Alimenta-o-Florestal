# Relatório de alimentação florestal

Este projeto automatiza a geração do relatório mensal de alimentação florestal.

O código abre o Checklist Fácil, acessa a listagem de avaliações e aplica o
filtro de alimentos para o período atual. Em seguida, seleciona os registros
encontrados, exporta os dados em formato XLSX e escolhe o layout com os itens
organizados em colunas.

Depois da exportação, o programa acompanha a fila do Checklist Fácil até o
arquivo ficar pronto, faz o download e salva o relatório com o mês e o ano no
nome do arquivo. Caso não existam registros no período, nenhum arquivo é
substituído.
