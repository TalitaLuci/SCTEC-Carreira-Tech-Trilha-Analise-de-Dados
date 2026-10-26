# -*- coding: utf-8 -*-
"""
Mini-Projeto Avaliativo - Módulo 1 (SCTEC)
Análise Exploratória de Dados (AED) - Base Varejo

Autora : Talita Luci da Silva
Turma  : Modelagem de Dados 525139

Como executar
-------------
VS Code / terminal : python miniprojeto_varejo_aed.py
                     (opcional) python miniprojeto_varejo_aed.py "caminho/Base Varejo.csv"
Google Colab       : faça upload deste .py, rode `%run miniprojeto_varejo_aed.py`
                     (se o CSV não for encontrado, o script abre a janela de upload)

Estrutura do script (cada SPRINT do enunciado é um bloco):
    Sprint 1 - Importação dos dados
    Sprint 2 - Diagnóstico de qualidade + transformação de tipos/strings
    Sprint 3 - Limpeza de nulos e duplicatas
    Sprint 4 - Estatística descritiva (número de filhos)
    Sprint 5 - Agrupamentos, conclusões e relatório final
    Saídas   - df_limpo.csv e gráficos .png (pasta "saidas")

Observação importante sobre a base:
    Não existe coluna de VALOR (R$) na base Varejo. Cada linha é um item
    de uma nota fiscal. Por isso, "vendas" aqui significa ITENS vendidos
    e "compras" significa NOTAS FISCAIS distintas (CO_ID).
"""

import os
import re
import sys

import pandas as pd

# ----------------------------------------------------------------------
# CONFIGURAÇÕES GERAIS
# ----------------------------------------------------------------------
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
PASTA_SAIDA = os.path.join(PASTA_PROJETO, "saidas")  # base limpa e gráficos junto ao projeto
ARQUIVO_LIMPO = os.path.join(PASTA_SAIDA, "df_limpo.csv")
NOMES_POSSIVEIS = ["Base Varejo.csv", "Varejo.csv", "base_varejo.csv"]

# Regras de negócio (dicionário de dados do enunciado original da base)
ESTADO_CIVIL = {1: "Casado/União estável", 2: "Divorciado", 3: "Separado",
                4: "Solteiro", 5: "Viúvo"}
GENEROS_VALIDOS = {"M", "F"}
SEGMENTOS_VALIDOS = {"A", "B", "C"}
COLUNAS_CHAVE_PRODUTO = ["PR_ID", "PR_CAT", "PR_NOME"]


def titulo(texto):
    """Imprime um cabeçalho padronizado no terminal."""
    print("\n" + "=" * 78)
    print(texto)
    print("=" * 78)


def pct(parte, total):
    """Percentual formatado (evita divisão por zero)."""
    return f"{(parte / total * 100):.2f}%" if total else "n/d"


# ======================================================================
# SPRINT 1 - IMPORTAÇÃO DOS DADOS
# ======================================================================
titulo("SPRINT 1 - IMPORTAÇÃO DOS DADOS")


def localizar_csv():
    """Procura o CSV: argumento da linha de comando > pasta atual > ./data > upload no Colab."""
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        return sys.argv[1]
    for pasta in [".", "data", os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."]:
        for nome in NOMES_POSSIVEIS:
            caminho = os.path.join(pasta, nome)
            if os.path.exists(caminho):
                return caminho
    try:  # Google Colab: pede upload do arquivo
        from google.colab import files
        print("CSV não encontrado. Selecione o arquivo 'Base Varejo.csv'...")
        enviado = files.upload()
        return list(enviado.keys())[0]
    except ImportError:
        sys.exit("ERRO: 'Base Varejo.csv' não encontrado. Coloque-o na mesma pasta do script "
                 "ou passe o caminho como argumento.")


caminho_csv = localizar_csv()
print(f"Arquivo utilizado: {caminho_csv}")

# O arquivo usa ';' como separador e termina cada linha com ';;;;' extras
# (gera 4 colunas 'Unnamed' vazias). Lemos tudo como texto (dtype=str) para
# controlar a conversão de tipos manualmente na Sprint 2.
try:
    df_bruto = pd.read_csv(caminho_csv, sep=";", dtype=str, encoding="utf-8")
except UnicodeDecodeError:
    df_bruto = pd.read_csv(caminho_csv, sep=";", dtype=str, encoding="latin-1")

colunas_obrigatorias = {
    "DATA", "CO_ID", "CL_ID", "CL_GENERO", "CL_EC", "CL_FHL",
    "CL_SEG", "PR_ID", "PR_CAT", "PR_NOME"
}
faltantes = sorted(colunas_obrigatorias - set(df_bruto.columns))
if faltantes:
    sys.exit(
        "ERRO: a base CSV não contém as colunas esperadas: "
        + ", ".join(faltantes)
    )

print(f"Número de registros : {len(df_bruto):,}".replace(",", "."))
print(f"Número de colunas   : {df_bruto.shape[1]}")
print("\nColunas e tipos de dados (como lidos do CSV):")
print(df_bruto.dtypes.to_string())
print("\nPrimeiras linhas:")
print(df_bruto.head().to_string())

# ======================================================================
# SPRINT 2 - DIAGNÓSTICO DE QUALIDADE + TRANSFORMAÇÃO DE TIPOS
# ======================================================================
titulo("SPRINT 2 - DIAGNÓSTICO DE QUALIDADE (ANTES DA LIMPEZA)")

total_bruto = len(df_bruto)

# --- Problema 1: colunas inteiramente vazias (resíduo dos ';' no fim das linhas)
nulos_por_coluna = df_bruto.isna().sum()
print("Valores nulos por coluna:")
print(pd.DataFrame({"nulos": nulos_por_coluna,
                    "% nulos": (nulos_por_coluna / total_bruto * 100).round(2)}).to_string())
colunas_vazias = [c for c in df_bruto.columns if df_bruto[c].isna().all()]
print(f"\n[Problema 1] Colunas 100% vazias (serão removidas): {colunas_vazias}")

# Trabalhamos só com as colunas úteis daqui em diante
df = df_bruto.drop(columns=colunas_vazias).copy()
del df_bruto  # libera memória (a base tem 800 mil+ linhas)

# --- Problema 2: duplicatas
n_dup = int(df.duplicated().sum())
print(f"\n[Problema 2] Linhas totalmente duplicadas: {n_dup:,} ({pct(n_dup, total_bruto)})".replace(",", "."))
print("  -> Atenção: aqui uma duplicata costuma ser o MESMO produto comprado mais de uma vez "
      "na mesma nota (quantidade > 1), e não um erro de digitação.")

# --- Problema 3: placeholders de "vazio" escondidos como texto (ex.: '#N/D' do Excel)
padrao_placeholder = r"^\s*(#N/D|#N/A|N/A|NA|NULL|NONE|-|)\s*$"
mascara_placeholder = df.apply(lambda s: s.str.match(padrao_placeholder, case=False, na=False))
placeholders = mascara_placeholder.sum()
placeholders = placeholders[placeholders > 0]
print("\n[Problema 3] Valores 'vazios disfarçados' (ex.: '#N/D') por coluna:")
print(placeholders.to_string() if len(placeholders) else "  nenhum")

# --- Problema 4: datas inválidas (formato dia/mês/ano)
datas_teste = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors="coerce")
print(f"\n[Problema 4] Datas inválidas (não convertem para dd/mm/aaaa): {int(datas_teste.isna().sum())}")

# --- Problema 5: regras de negócio (domínio dos valores)
ec_num = pd.to_numeric(df["CL_EC"], errors="coerce")
fhl_num = pd.to_numeric(df["CL_FHL"], errors="coerce")
print("\n[Problema 5] Validação das regras de negócio:")
print(f"  CL_GENERO fora de {sorted(GENEROS_VALIDOS)}  : {int((~df['CL_GENERO'].str.strip().str.upper().isin(GENEROS_VALIDOS)).sum())}")
print(f"  CL_SEG fora de {sorted(SEGMENTOS_VALIDOS)} : {int((~df['CL_SEG'].str.strip().str.upper().isin(SEGMENTOS_VALIDOS)).sum())}")
print(f"  CL_EC fora de 1..5       : {int((~ec_num.isin(ESTADO_CIVIL.keys())).sum())}")
print(f"  CL_FHL negativo/não num. : {int(((fhl_num < 0) | fhl_num.isna()).sum())}")
# O mesmo cliente deve ter sempre os mesmos atributos cadastrais
consistencia = df.groupby("CL_ID")[["CL_GENERO", "CL_EC", "CL_FHL", "CL_SEG"]].nunique()
print(f"  Clientes com cadastro inconsistente (atributos variando): {int((consistencia > 1).any(axis=1).sum())}")
# Cada nota fiscal deve pertencer a um único cliente e uma única data
consist_nota = df.groupby("CO_ID")[["CL_ID", "DATA"]].nunique()
print(f"  Notas fiscais com mais de 1 cliente/data              : {int((consist_nota > 1).any(axis=1).sum())}")
# Um mesmo código de produto deve ter um único nome/categoria
consist_prod = df.groupby("PR_ID")[["PR_NOME", "PR_CAT"]].nunique()
print(f"  PR_ID com mais de um nome/categoria                   : {int((consist_prod > 1).any(axis=1).sum())}")

# ----------------------------------------------------------------------
# Transformação de strings, inteiros e datas
# ----------------------------------------------------------------------
titulo("SPRINT 2 - TRANSFORMAÇÃO DE STRINGS, INTEIROS E DATAS")


def limpar_texto(serie):
    """Remove espaços nas pontas, colapsa espaços repetidos (regex) e padroniza em MAIÚSCULAS."""
    return (serie.str.strip()
                 .str.replace(r"\s+", " ", regex=True)
                 .str.upper())


# Strings: padronização de texto
for col in ["CL_GENERO", "CL_SEG", "PR_CAT", "PR_NOME"]:
    df[col] = limpar_texto(df[col])

# Placeholders -> NaN real (assim o pandas reconhece como nulo)
for col in df.columns:
    df[col] = df[col].replace(padrao_placeholder, pd.NA, regex=True)

# Datas: texto 'dd/mm/aaaa' -> datetime64 (errors='coerce' transforma inválidas em NaT)
df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors="coerce")

# Inteiros: IDs e variáveis numéricas (Int64 aceita nulos)
for col in ["CO_ID", "CL_ID", "CL_EC", "CL_FHL", "PR_ID"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

print("Tipos após a conversão:")
print(df.dtypes.to_string())

# ======================================================================
# SPRINT 3 - LIMPEZA DE NULOS E DUPLICATAS
# ======================================================================
titulo("SPRINT 3 - LIMPEZA DE NULOS E DUPLICATAS")

# ---- 3.1 Nulos -------------------------------------------------------
nulos_depois_conv = df.isna().sum()
print("Nulos por coluna após padronização (inclui os '#N/D' convertidos):")
print(nulos_depois_conv[nulos_depois_conv > 0].to_string() if nulos_depois_conv.any() else "  nenhum")

# Regra A - datas inválidas: sem data a compra não entra em nenhuma análise
#           temporal e não há como adivinhar a data -> REMOVER a linha.
linhas_antes = len(df)
df = df.dropna(subset=["DATA"])
removidas_data = linhas_antes - len(df)
print(f"\nRegra A: linhas removidas por data inválida: {removidas_data}")

# Regra B - chaves (nota, cliente) nulas: sem elas não é possível agrupar -> REMOVER.
linhas_antes = len(df)
df = df.dropna(subset=["CO_ID", "CL_ID"])
removidas_chave = linhas_antes - len(df)
print(f"Regra B: linhas removidas por CO_ID/CL_ID nulo: {removidas_chave}")

# Regra C - produto/categoria nulos: NÃO removemos. A base não tem valor em R$,
#           então não dá para inferir a categoria de outro jeito, e apagar essas
#           linhas distorceria a contagem de itens por nota. IMPUTAMOS o rótulo
#           'NAO INFORMADO', mantendo a linha visível e separável nas análises.
n_prod_nulo = int(df["PR_CAT"].isna().sum() + df["PR_NOME"].isna().sum())
df["PR_CAT"] = df["PR_CAT"].fillna("NAO INFORMADO")
df["PR_NOME"] = df["PR_NOME"].fillna("NAO INFORMADO")
print(f"Regra C: valores de produto/categoria imputados como 'NAO INFORMADO': {n_prod_nulo}")

# Regra D - atributos de cliente nulos: um cliente tem atributos fixos, então
#           preenchemos com o valor conhecido do próprio cliente (outra linha dele).
for col in ["CL_GENERO", "CL_EC", "CL_FHL", "CL_SEG"]:
    df[col] = df.groupby("CL_ID")[col].transform(lambda s: s.ffill().bfill())
restantes = int(df[["CL_GENERO", "CL_EC", "CL_FHL", "CL_SEG"]].isna().sum().sum())
print(f"Regra D: nulos de cadastro restantes após preencher pelo próprio cliente: {restantes}")
df = df.dropna(subset=["CL_GENERO", "CL_EC", "CL_FHL", "CL_SEG"])  # só roda se sobrar algo

# ---- 3.2 Duplicatas --------------------------------------------------
# Linhas 100% iguais = mesmo produto, mesma nota, mesmo cliente, mesma data.
# Interpretação adotada: linhas idênticas representam unidades repetidas do
# mesmo produto na nota. Como a base não possui uma coluna de quantidade, essa
# hipótese preserva o total de registros como QTD, mas deve ser validada com o
# dicionário/fonte original antes de uso operacional. Se duplicatas forem erros
# de coleta, esta regra superestimará os itens.
linhas_antes = len(df)
colunas_dados = list(df.columns)
df = (df.groupby(colunas_dados, dropna=False, observed=True, sort=False)
        .size().reset_index(name="QTD"))
duplicatas_eliminadas = linhas_antes - len(df)
print(f"\nDuplicatas eliminadas (consolidadas em QTD): {duplicatas_eliminadas:,}".replace(",", "."))
print(f"Linhas antes: {linhas_antes:,} | Linhas depois: {len(df):,} | Itens preservados (soma de QTD): {int(df['QTD'].sum()):,}"
      .replace(",", "."))

# ---- 3.3 Tipos finais e colunas auxiliares ----------------------------
df["CL_EC_DESC"] = df["CL_EC"].map(ESTADO_CIVIL)          # rótulo legível do estado civil
df["ANO"] = df["DATA"].dt.year
df["ANO_MES"] = df["DATA"].dt.to_period("M").astype(str)
for col in ["CL_GENERO", "CL_SEG", "PR_CAT", "CL_EC_DESC"]:
    df[col] = df[col].astype("category")                    # economiza memória

df = df.sort_values(["DATA", "CO_ID"]).reset_index(drop=True)
df_limpo = df
print(f"\nBase limpa: {df_limpo.shape[0]:,} linhas x {df_limpo.shape[1]} colunas".replace(",", "."))

# ======================================================================
# SPRINT 4 - ESTATÍSTICA DESCRITIVA (Nº DE FILHOS - CL_FHL)
# ======================================================================
titulo("SPRINT 4 - ESTATÍSTICA DESCRITIVA: NÚMERO DE FILHOS (CL_FHL)")


def resumo_estatistico(serie):
    """Retorna média, mediana, desvio padrão, moda, máximo, mínimo e contagem."""
    serie = serie.astype(float)
    return pd.Series({
        "contagem": serie.count(),
        "média": serie.mean(),
        "mediana": serie.median(),
        "desvio padrão": serie.std(),
        "moda": ", ".join(str(int(m)) for m in serie.mode()),  # pode haver mais de uma moda
        "máximo": serie.max(),
        "mínimo": serie.min(),
    })


# Visão 1 (principal): UMA linha por cliente. O número de filhos é atributo do
# cliente; usar a base de itens daria mais peso a quem compra mais.
clientes = df_limpo.drop_duplicates("CL_ID")[["CL_ID", "CL_FHL", "CL_GENERO", "CL_SEG"]]
# Visão 2 (comparação): por item vendido (cada unidade conta uma vez).
stats_clientes = resumo_estatistico(clientes["CL_FHL"])
stats_itens = resumo_estatistico(df_limpo["CL_FHL"].repeat(df_limpo["QTD"]))
tabela_filhos = pd.DataFrame({"Por cliente (1 linha = 1 cliente)": stats_clientes,
                              "Por item vendido (ponderado por compras)": stats_itens})
print(tabela_filhos.to_string())

print("\nDistribuição de clientes por nº de filhos:")
dist_filhos = clientes["CL_FHL"].value_counts().sort_index()
print(pd.DataFrame({"clientes": dist_filhos,
                    "%": (dist_filhos / dist_filhos.sum() * 100).round(1)}).to_string())

# ======================================================================
# SPRINT 5 - AGRUPAMENTOS (groupby / pivot_table)
# ======================================================================
titulo("SPRINT 5 - PADRÕES DE AGRUPAMENTO")

# Agrupamento 1 - por gênero
por_genero = df_limpo.groupby("CL_GENERO", observed=True).agg(
    itens=("QTD", "sum"),
    compras=("CO_ID", "nunique"),
    clientes=("CL_ID", "nunique"),
)
por_genero["itens_por_compra"] = (por_genero["itens"] / por_genero["compras"]).round(2)
por_genero["itens_por_cliente"] = (por_genero["itens"] / por_genero["clientes"]).round(1)
por_genero["% itens"] = (por_genero["itens"] / por_genero["itens"].sum() * 100).round(1)
print("\n[1] Vendas por gênero:")
print(por_genero.to_string())

# Agrupamento 2 - por categoria de produto
por_categoria = (df_limpo.groupby("PR_CAT", observed=True)["QTD"].sum()
                 .sort_values(ascending=False).to_frame("itens"))
por_categoria["% itens"] = (por_categoria["itens"] / por_categoria["itens"].sum() * 100).round(1)
print("\n[2] Itens vendidos por categoria:")
print(por_categoria.to_string())

# Agrupamento 3 - pivot_table: gênero x categoria (% de cada gênero)
pivot_gen_cat = pd.pivot_table(df_limpo, index="PR_CAT", columns="CL_GENERO",
                               values="QTD", aggfunc="sum", observed=True, fill_value=0)
pivot_pct = (pivot_gen_cat / pivot_gen_cat.sum() * 100).round(1)
print("\n[3] pivot_table - itens por categoria x gênero (valores) e % dentro de cada gênero:")
print(pivot_gen_cat.to_string())
print(pivot_pct.add_suffix(" (%)").to_string())

# Agrupamento 4 - por segmento econômico e por estado civil
por_segmento = df_limpo.groupby("CL_SEG", observed=True).agg(
    itens=("QTD", "sum"), compras=("CO_ID", "nunique"), clientes=("CL_ID", "nunique"))
por_segmento["itens_por_cliente"] = (por_segmento["itens"] / por_segmento["clientes"]).round(1)
print("\n[4a] Por segmento econômico:")
print(por_segmento.to_string())

por_estciv = df_limpo.groupby("CL_EC_DESC", observed=True).agg(
    itens=("QTD", "sum"), clientes=("CL_ID", "nunique"))
por_estciv["itens_por_cliente"] = (por_estciv["itens"] / por_estciv["clientes"]).round(1)
print("\n[4b] Por estado civil:")
print(por_estciv.sort_values("itens", ascending=False).to_string())

# Agrupamento 5 - nº de filhos x itens por cliente
por_filhos = df_limpo.groupby("CL_FHL").agg(itens=("QTD", "sum"), clientes=("CL_ID", "nunique"))
por_filhos["itens_por_cliente"] = (por_filhos["itens"] / por_filhos["clientes"]).round(1)
print("\n[5] Média de itens comprados por cliente, segundo o nº de filhos:")
print(por_filhos.to_string())

# Agrupamento 6 - evolução no tempo
por_ano = df_limpo.groupby("ANO").agg(
    itens=("QTD", "sum"), compras=("CO_ID", "nunique"),
    primeira_data=("DATA", "min"), ultima_data=("DATA", "max"))
print("\n[6a] Evolução anual:")
print(por_ano.to_string())

por_mes = df_limpo.groupby("ANO_MES")["QTD"].sum()
por_mes_calendario = df_limpo.groupby(df_limpo["DATA"].dt.month)["QTD"].sum()  # sazonalidade
print("\n[6b] Itens vendidos por mês do ano (todos os anos somados):")
print(por_mes_calendario.to_string())

# Agrupamento 7 - rankings
top_produtos = (df_limpo.groupby("PR_NOME")["QTD"].sum().sort_values(ascending=False).head(10))
top_clientes = (df_limpo.groupby("CL_ID")["QTD"].sum().sort_values(ascending=False).head(10))
print("\n[7a] Top 10 produtos mais vendidos (itens):")
print(top_produtos.to_string())
print("\n[7b] Top 10 clientes que mais compram (itens) - quem compra mais:")
print(top_clientes.to_string())

# ======================================================================
# SAÍDAS: df_limpo.csv e gráficos (matplotlib é opcional)
# ======================================================================
titulo("SAÍDAS: ARQUIVOS GERADOS")
os.makedirs(PASTA_SAIDA, exist_ok=True)
# Colunas auxiliares (derivadas) não vão para o arquivo final: deixam o CSV menor
# e podem ser recriadas a qualquer momento a partir de DATA e CL_EC.
df_limpo.drop(columns=["ANO_MES", "ANO", "CL_EC_DESC"]).to_csv(ARQUIVO_LIMPO, sep=";", index=False, encoding="utf-8-sig")
print(f"Base limpa salva em: {ARQUIVO_LIMPO}")

try:
    import matplotlib
    matplotlib.use("Agg")  # funciona sem janela (terminal/servidor)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(dist_filhos.index.astype(str), dist_filhos.values, color="#4C72B0")
    ax.set(title="Clientes por número de filhos", xlabel="Nº de filhos", ylabel="Clientes")
    fig.tight_layout(); fig.savefig(os.path.join(PASTA_SAIDA, "01_filhos.png"), dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    por_categoria["itens"].sort_values().plot.barh(ax=ax, color="#55A868")
    ax.set(title="Itens vendidos por categoria", xlabel="Itens", ylabel="")
    fig.tight_layout(); fig.savefig(os.path.join(PASTA_SAIDA, "02_categorias.png"), dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    por_mes.plot(ax=ax, color="#C44E52")
    ax.set(title="Itens vendidos por mês", xlabel="Mês", ylabel="Itens")
    ax.tick_params(axis="x", rotation=60)
    fig.tight_layout(); fig.savefig(os.path.join(PASTA_SAIDA, "03_evolucao_mensal.png"), dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    pivot_pct.T.plot.bar(ax=ax, rot=0)
    ax.set(title="Perfil de compra por gênero (% dos itens)", xlabel="Gênero", ylabel="%")
    ax.legend(title="Categoria", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(PASTA_SAIDA, "04_genero_categoria.png"), dpi=120); plt.close(fig)
    print(f"Gráficos salvos em: {PASTA_SAIDA}/ (4 arquivos .png)")
except ImportError:
    print("matplotlib não instalado - gráficos ignorados (opcional).")

# ======================================================================
# SPRINT 5 - RELATÓRIO FINAL NO TERMINAL (contadores + conclusões)
# ======================================================================
titulo("RELATÓRIO FINAL")

itens_total = int(df_limpo["QTD"].sum())
print("CONTADORES DO PROCESSO DE LIMPEZA")
print(f"  Registros lidos (brutos)                  : {total_bruto:,}".replace(",", "."))
print(f"  Colunas vazias removidas                  : {len(colunas_vazias)}")
print(f"  Linhas removidas (data/chave inválida)    : {removidas_data + removidas_chave}")
print(f"  Valores de produto imputados (NAO INFORM.): {n_prod_nulo}")
print(f"  Duplicatas consolidadas em QTD            : {duplicatas_eliminadas:,}".replace(",", "."))
print(f"  Registros na base limpa                   : {len(df_limpo):,}".replace(",", "."))
print(f"  Itens vendidos (soma de QTD)              : {itens_total:,}".replace(",", "."))
print(f"  Notas fiscais distintas                   : {df_limpo['CO_ID'].nunique():,}".replace(",", "."))
print(f"  Clientes distintos                        : {df_limpo['CL_ID'].nunique():,}".replace(",", "."))
print(f"  Produtos distintos (PR_ID)                : {df_limpo['PR_ID'].nunique()}")
print(f"  Período                                   : {df_limpo['DATA'].min():%d/%m/%Y} a {df_limpo['DATA'].max():%d/%m/%Y}")

# Valores usados nas conclusões (calculados, não digitados à mão)
g_top = por_genero["itens"].idxmax()
g_top_pct = por_genero.loc[g_top, "% itens"]
cat_top = por_categoria.index[0]
cat_top_pct = por_categoria.iloc[0]["% itens"]
cat_nd = por_categoria.loc["NAO INFORMADO", "% itens"] if "NAO INFORMADO" in por_categoria.index else 0
ano_top = int(por_ano["itens"].idxmax())
mes_top = int(por_mes_calendario.idxmax())
seg_top = por_segmento["itens"].idxmax()
seg_top_pct = por_segmento["itens"].max() / por_segmento["itens"].sum() * 100
filhos_media = stats_clientes["média"]
filhos_mediana = stats_clientes["mediana"]
filhos_zero_pct = dist_filhos.get(0, 0) / dist_filhos.sum() * 100
cli_top = int(top_clientes.index[0])
meses_nome = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
              7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}

print("\nCONCLUSÕES E INSIGHTS")
dif_genero_pp = abs(float(por_genero["% itens"].get("F", 0)) -
                    float(por_genero["% itens"].get("M", 0)))
print(f"  1. Gênero: {'mulheres (F)' if g_top == 'F' else 'homens (M)'} respondem por {g_top_pct}% dos itens. "
      f"A diferença entre os grupos é de {dif_genero_pp:.1f} pontos percentuais; isso descreve esta base, "
      f"não demonstra causalidade.")
if set(["F", "M"]).issubset(set(pivot_pct.columns)):
    diferencas_cat = (pivot_pct["F"] - pivot_pct["M"]).abs()
    maior_dif_cat = float(diferencas_cat.max()) if len(diferencas_cat) else 0.0
else:
    maior_dif_cat = float("nan")
print(f"  2. Categorias: {cat_top} lidera com {cat_top_pct}% dos itens. "
      f"A maior diferença entre as participações por categoria de F e M é {maior_dif_cat:.1f} p.p. "
      f"(ver pivot_table); associação descritiva não implica causalidade.")
print(f"  3. Segmento econômico: a classe {seg_top} concentra {seg_top_pct:.1f}% dos itens, "
      f"refletindo principalmente o tamanho da base de clientes dessa classe.")
print(f"  4. Número de filhos: média de {filhos_media:.2f} e mediana {filhos_mediana:.0f} por cliente; "
      f"{filhos_zero_pct:.1f}% dos clientes não têm filhos (moda = {stats_clientes['moda']}).")
print(f"  5. Tempo: {ano_top} foi o ano com mais itens vendidos e {meses_nome[mes_top]} o mês mais forte "
      f"na soma dos anos; o último ano da base termina em {df_limpo['DATA'].max():%d/%m/%Y} (ano incompleto).")
print(f"  6. Quem compra mais: o cliente {cli_top} lidera o ranking com {int(top_clientes.iloc[0]):,} itens."
      .replace(",", "."))

print("\nPROBLEMAS REMANESCENTES NA BASE")
print("  - Não há coluna de valor (R$) nem quantidade explícita: 'vendas' = itens; QTD representa a contagem de linhas idênticas, uma hipótese a validar com a fonte.")
print(f"  - Produto PR_ID 107 vem como '#N/D' ({cat_nd}% dos itens): categoria/nome desconhecidos (imputado 'NAO INFORMADO').")
print(f"  - Códigos x nomes: {df_limpo['PR_ID'].nunique()} PR_ID para {df_limpo['PR_NOME'].nunique()} nomes "
      f"(ex.: vários códigos para o mesmo produto) -> use PR_ID, não PR_NOME, para contar produtos.")
print("  - Acentos perdidos no texto de origem (ex.: 'LIMaO'): nomes não foram corrigidos automaticamente.")
print("  - A documentação original cita 2010-2022, mas os dados cobrem apenas 2019-2022 (2022 incompleto).")
print("  - Volume atípico em set/2022 (~1,4 mil itens) e out/2022 (~2,7 mil), muito abaixo dos demais meses: "
      "possível falha de coleta -> investigar antes de tirar conclusões sobre tendência.")
print("  - Apenas 1.000 clientes: resultados descrevem esta amostra e não podem ser generalizados.")
print("\nFim da execução.")
