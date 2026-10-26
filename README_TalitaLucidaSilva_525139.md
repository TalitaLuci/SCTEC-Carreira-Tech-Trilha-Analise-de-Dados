# Instruções de execução e reflexão — Talita Luci da Silva — Turma 525139

## Como executar

### VS Code / terminal
1. Baixe `Base Varejo.csv` na página do Kaggle indicada no enunciado.
2. Coloque o CSV na mesma pasta de `miniprojeto_varejo_aed.py`.
3. Instale as dependências: `pip install -r requirements.txt`.
4. Execute: `python miniprojeto_varejo_aed.py`.

Opcionalmente, informe o caminho do CSV como argumento:
`python miniprojeto_varejo_aed.py "caminho/Base Varejo.csv"`.

### Google Colab
Envie o script e execute `%run miniprojeto_varejo_aed.py`. Se o CSV não estiver disponível na pasta de trabalho, o script solicitará o upload.

O relatório aparece no terminal. A base tratada e os gráficos são gravados na pasta `saidas/`. O `README.md` inclui os gráficos com uma interpretação breve dos resultados e das limitações.

## Requisitos do enunciado e localização no código

| Requisito | Onde é atendido |
|---|---|
| Documentação | Docstring inicial, comentários por Sprint e README |
| Regras de negócio e datas | Sprint 2: validação de gênero, segmento, estado civil, número de filhos, consistência de cadastro e conversão de datas |
| Padrões de agrupamento | Sprint 5: `groupby()` e `pivot_table()` |
| Estatísticas básicas | Sprint 4: média, mediana, desvio padrão, moda, máximo, mínimo e contagem de `CL_FHL` |
| Manipulação de arquivos CSV | Sprint 1: `read_csv()`; saída: `to_csv()` |
| Tratamento de nulos e condicionais | Sprints 2 e 3: placeholders, `dropna()`, `fillna()` e regras comentadas |

O enunciado permite implementações equivalentes com pandas. Por isso, o projeto utiliza `read_csv()`, `pd.to_datetime()`, `dropna()`, `fillna()`, `groupby()` e `pivot_table()`.

## Reflexão teórica

Uma das decisões mais importantes foi tratar as linhas repetidas com cuidado. Remover automaticamente todas as repetições reduziria a contagem de registros, mas a base não contém uma coluna explícita de quantidade. O script agrupa as linhas idênticas e guarda a frequência em `QTD`, preservando o total de 830.000 registros como unidades. Essa abordagem é uma hipótese analítica, não uma certeza sobre a regra de negócio: é necessário confirmar com a documentação da fonte se as repetições representam unidades compradas ou erros de duplicação.

Outro ponto é que valores ausentes nem sempre aparecem como células vazias. Marcadores como `#N/D` precisam ser identificados e convertidos em nulos antes do tratamento. Para datas inválidas e identificadores essenciais ausentes, a linha é removida porque não há informação segura para reconstruí-los. Já a categoria ou o nome de produto ausente recebe `NAO INFORMADO`, evitando inventar dados e mantendo o registro nas contagens.

A unidade de análise também importa. O número de filhos é um atributo do cliente; portanto, a estatística principal usa uma linha por cliente para que clientes que compram mais não tenham peso excessivo. A versão ponderada por itens é apresentada apenas como comparação.

Por fim, a análise tem limites: não existe coluna de preço ou valor de venda, o período disponível termina em 08/12/2022 e há meses de 2022 com volume muito baixo. Assim, o projeto descreve itens e notas fiscais, mas não permite calcular faturamento nem afirmar que as diferenças observadas se aplicam a outros varejistas. Antes de usar os resultados para decisões, é importante validar as hipóteses e investigar a qualidade da fonte.

**Autora:** Talita Luci da Silva  
**Turma:** Modelagem de Dados 525139
