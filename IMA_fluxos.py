# -*- coding: utf-8 -*-
"""
Created on Wed Apr 23 15:15:38 2025


Começa com os geradores iniciais

Procura para onde vão

Armazena essas relações no array da etapa 1 (fluxo1)

Para cada destinador encontrado, verifica se ele também é um gerador para outro fluxo

Se sim, registra no fluxo2 (e assim por diante)

Continua até não achar mais para onde ele envia

Mas, considerar apenas os NOVOS, diferenciando os já contados 

Logo:
    Gerador_puro -> Destinador 1 = DF1
        Destinador 1 = Gerador 2
    Gerador 2 (!= DF1)  -> Destinador 2 = DF2
        Destinador 3 = Gerador 2
    Gerador 3 (!= DF1 & DF2) -> Destinador 3 = DF3 

Primeira resposta: 
Fluxo 1: 87007 linhas
Fluxo 2: 5404 linhas
Fluxo 3: 520 linhas
Fluxo 4: 4 linhas
⚠️ Nenhum novo fluxo encontrado no passo 5. Encerrando.

Agora, identificar os 131 cnpjs faltantes 
- criar df pra cada fluxo com todas infos 
- criar os garfor a partir dos dfs 

Em seguida, foi incorporado os cnpjs que eram iguais (tanto destinador quanto gerador) no geradores primários
Depois rodado novamente essa nova condição 

Análise da geração de resíduos nos intermediários 
fazendo o balanço de massa para cada cnpj,
quanto entrou e quanto saiu de resíduo, se:
    > 0 logo, gerou redíduo
    < 0 logo, reteu resíduo 
    = 0 logo, apenas destinou 
Para isso, foi analisado o cnpj que recebeu a partir do cnpj que gerou (puxando do dataframe do passo anterior)
e o que foi destinado. 

Por fim, somando todo o gerado e retido temos o valor final. 

@author: ASUS 
"""
import networkx as nx
import pandas as pd

df = abaixo45semtipo

#%% Criando loop 

# Inicializa a lista de DataFrames por etapa
fluxos = []

# Começa pelos geradores puros: aqueles que NÃO aparecem como destinadores
geradores_puros = set(df['manifesto_gerador_cnpj'].dropna().unique()) - set(df['manifesto_destinador_cnpj'].dropna().unique())

# Primeiro fluxo: Gerador_puro → Destinador
fluxo_atual = df[df['manifesto_gerador_cnpj'].isin(geradores_puros)].copy() #Pega todas as linhas da tabela onde o gerador for um dos geradores_puros
fluxos.append(fluxo_atual)

print(f"Fluxo 1: {len(fluxo_atual)} linhas")

# Lista de todos CNPJs já processados como geradores
geradores_processados = set(geradores_puros) # guardando lista de cnpjs já usados como geradores 

i = 2  # contador de fluxos

while True:
    # Pega os destinos do fluxo anterior
    destinos_anteriores = fluxo_atual['manifesto_destinador_cnpj'].dropna().unique()
    
    # Filtra o DataFrame original: onde esses destinos agora aparecem como geradores
    fluxo_novo = df[df['manifesto_gerador_cnpj'].isin(destinos_anteriores)].copy()
    
    # Remove linhas que já processaram esses geradores antes (evita loop)
    fluxo_novo = fluxo_novo[~fluxo_novo['manifesto_gerador_cnpj'].isin(geradores_processados)]
    
    if fluxo_novo.empty:
        print(f"Nenhum novo fluxo encontrado no passo {i}. Encerrando.")
        break
    
    # Adiciona novo fluxo
    fluxos.append(fluxo_novo)
    print(f"Fluxo {i}: {len(fluxo_novo)} linhas")
    
    # Atualiza os geradores já processados
    geradores_processados.update(fluxo_novo['manifesto_gerador_cnpj'].unique())
    
    # Prepara para próxima iteração
    fluxo_atual = fluxo_novo
    i += 1
    
# Agora a lista `fluxos` contém DataFrames para cada etapa da cadeia!

for idx, fluxo in enumerate(fluxos):
    print(f"Etapa {idx + 1}: {len(fluxo)} linhas")
    print(fluxo.head())
    
# Df do resultado dos passos, transformando-os emm variáveis
fluxo_1 = fluxos[0]
fluxo_2 = fluxos[1] if len(fluxos) > 1 else None
fluxo_3 = fluxos[2] if len(fluxos) > 2 else None
fluxo_4 = fluxos[3] if len(fluxos) > 3 else None

print(fluxo_1.head())
print(fluxo_2.head() if fluxo_2 is not None else "Fluxo 2 não existe.")

#%% Algumas linhas não retornaram, pois, ou os geradores dessas linhas não são geradores puros, ou 
# as cadeias não têm conexão com as cadeias iniciadas pelos geradores puros identificados

# verificar se o cnpj de df encontra-se no fluxo
df['existe_em_df2'] = df['manifesto_gerador_cnpj'].isin(fluxo_1['manifesto_gerador_cnpj'])

# Concatena os CNPJs de todos os fluxos
cnpjs_fluxos = pd.concat([
    fluxo_1['manifesto_gerador_cnpj'],
    fluxo_1['manifesto_destinador_cnpj'],
    fluxo_2['manifesto_gerador_cnpj'],
    fluxo_2['manifesto_destinador_cnpj'],
    fluxo_3['manifesto_gerador_cnpj'],
    fluxo_3['manifesto_destinador_cnpj'],
    fluxo_4['manifesto_gerador_cnpj'],
    fluxo_4['manifesto_destinador_cnpj'] 
]).dropna().unique()

# Concatena os CNPJs do DataFrame original
cnpjs_df = pd.concat([
    df['manifesto_gerador_cnpj'],
    df['manifesto_destinador_cnpj']
]).dropna().unique()

# Verifica os CNPJs que estão no DataFrame original mas não apareceram em nenhum fluxo
cnpjs_restantes = set(cnpjs_df) - set(cnpjs_fluxos)

print(f"Quantidade de CNPJs no DataFrame original: {len(cnpjs_df)}")
print(f"Quantidade de CNPJs em todos os fluxos: {len(cnpjs_fluxos)}")
print(f"CNPJs que não apareceram em nenhum fluxo: {len(cnpjs_restantes)}")

# Filtra as linhas do DataFrame original onde o CNPJ do gerador ou destinador está nos cnpjs_restantes
filtro = df['manifesto_gerador_cnpj'].isin(cnpjs_restantes) | df['manifesto_destinador_cnpj'].isin(cnpjs_restantes)

df_restantes = df[filtro]

# Mostra o resultado
print(f"Linhas do DataFrame original correspondentes a esses CNPJs restantes: {len(df_restantes)}")
print(df_restantes)

pd.DataFrame({'CNPJ': list(cnpjs_restantes)}).to_excel('cnpjs_perdidos.xlsx', index=False)

# Concatena todos os DataFrames de fluxos encontrados
todos_fluxos = pd.concat(fluxos)

# Remove duplicatas, se houver
todos_fluxos = todos_fluxos.drop_duplicates()

# Faz um merge anti-join: pega as linhas do df original que NÃO estão nos fluxos
restantes = pd.merge(df, todos_fluxos, how='outer', indicator=True).query('_merge == "left_only"').drop(columns=['_merge'])

print(f"Linhas restantes: {len(restantes)}")
print(restantes)

#%% Gerar Planilhas 

fluxo_1.to_excel('Fluxos_1.xlsx', index=False)
fluxo_2.to_excel('Fluxos_2.xlsx', index=False)
fluxo_3.to_excel('Fluxos_3.xlsx', index=False)
fluxo_4.to_excel('Fluxos_4.xlsx', index=False)
restantes.to_excel('Perdidos.xlsx', index=False)

soma1 = fluxo_1['manifesto_item_quantidade'].sum()
print(soma1)
soma2 = fluxo_2['manifesto_item_quantidade'].sum()
print(soma2)
soma3 = fluxo_3['manifesto_item_quantidade'].sum()
print(soma3)
soma4 = fluxo_4['manifesto_item_quantidade'].sum()
print(soma4)
soma5 = restantes['manifesto_item_quantidade'].sum()
print(soma5)


#%%
# Gerando planilha para os cnpj restantes 

cnpjs_restantes_list = list(cnpjs_restantes)

# Filtra as linhas onde o CNPJ restante aparece como DESTINADOR
df_destinador_restante = df[df['manifesto_destinador_cnpj'].isin(cnpjs_restantes_list)][['manifesto_destinador_cnpj', 'manifesto_destinador_nome']].drop_duplicates()

# Filtra as linhas onde o CNPJ restante aparece como GERADOR
df_gerador_restante = df[df['manifesto_gerador_cnpj'].isin(cnpjs_restantes_list)][['manifesto_gerador_cnpj', 'manifesto_gerador_nome']].drop_duplicates()

# Renomeia as colunas para ficarem iguais (para concatenar depois)
df_destinador_restante = df_destinador_restante.rename(columns={
    'manifesto_destinador_cnpj': 'CNPJ',
    'manifesto_destinador_nome': 'Nome'
})

df_gerador_restante = df_gerador_restante.rename(columns={
    'manifesto_gerador_cnpj': 'CNPJ',
    'manifesto_gerador_nome': 'Nome'
})

# Concatena os dois DataFrames
df_restante = pd.concat([df_destinador_restante, df_gerador_restante], ignore_index=True).drop_duplicates()

print(df_restante)

#df_restante.to_excel('cnpjs_restantes_com_nomes.xlsx', index=False)

# ------- vendo os cnpjs que são iguais na linha ----------

# Filtra linhas em que o gerador e o destinador são o mesmo CNPJ
cnpjs_iguais = df[df['manifesto_gerador_cnpj'] == df['manifesto_destinador_cnpj']]

# Exibe os CNPJs únicos dessas linhas
cnpjs_iguais_unicos = cnpjs_iguais['manifesto_gerador_cnpj'].dropna().unique()

print(f"Total de CNPJs iguais gerador = destinador: {len(cnpjs_iguais_unicos)}")
print(cnpjs_iguais_unicos)

#%% nova análise com os cnpjs de restantes incorporados como geradores iniciais 

# Passo 1: Identifica os CNPJs autoencaminhados em 'restantes'

# Concatena todos os DataFrames de fluxos encontrados
todos_fluxos = pd.concat(fluxos) if 'fluxos' in locals() else pd.DataFrame()

# Remove duplicatas
todos_fluxos = todos_fluxos.drop_duplicates()

# Faz um merge anti-join: pega as linhas do df original que NÃO estão nos fluxos
restantes = pd.merge(df, todos_fluxos, how='outer', indicator=True).query('_merge == "left_only"').drop(columns=['_merge'])

# Identifica CNPJs com autoencaminhamento (mesmo CNPJ como gerador e destinador)
cnpjs_autoencaminhados = set(
    restantes[restantes['manifesto_gerador_cnpj'] == restantes['manifesto_destinador_cnpj']]['manifesto_gerador_cnpj'].dropna().unique()
)

# Passo 2: Roda a lógica de fluxos com os novos geradores puros

# Inicializa a lista de DataFrames por etapa
fluxos = []

# Começa pelos geradores puros: aqueles que NÃO aparecem como destinadores
geradores_puros = (
    set(df['manifesto_gerador_cnpj'].dropna().unique()) - set(df['manifesto_destinador_cnpj'].dropna().unique())
).union(cnpjs_autoencaminhados)

# Primeiro fluxo: Gerador_puro → Destinador
fluxo_atual = df[df['manifesto_gerador_cnpj'].isin(geradores_puros)].copy()
fluxos.append(fluxo_atual)
print(f"Fluxo 1: {len(fluxo_atual)} linhas")

# Lista de todos CNPJs já processados como geradores
geradores_processados = set(geradores_puros)

i = 2  # contador de fluxos
while True:
    destinos_anteriores = fluxo_atual['manifesto_destinador_cnpj'].dropna().unique()
    fluxo_novo = df[df['manifesto_gerador_cnpj'].isin(destinos_anteriores)].copy()
    fluxo_novo = fluxo_novo[~fluxo_novo['manifesto_gerador_cnpj'].isin(geradores_processados)]
    
    if fluxo_novo.empty:
        print(f"⚠️ Nenhum novo fluxo encontrado no passo {i}. Encerrando.")
        break
    
    fluxos.append(fluxo_novo)
    print(f"Fluxo {i}: {len(fluxo_novo)} linhas")
    
    geradores_processados.update(fluxo_novo['manifesto_gerador_cnpj'].unique())
    fluxo_atual = fluxo_novo
    i += 1

# ======================================
# Passo 3: Resultado final e verificação
# ======================================

for idx, fluxo in enumerate(fluxos):
    print(f"Etapa {idx + 1}: {len(fluxo)} linhas")
    print(fluxo.head())

# Df do resultado dos passos
fluxo_1 = fluxos[0]
fluxo_2 = fluxos[1] if len(fluxos) > 1 else None
fluxo_3 = fluxos[2] if len(fluxos) > 2 else None
fluxo_4 = fluxos[3] if len(fluxos) > 3 else None

print(fluxo_1.head())
print(fluxo_2.head() if fluxo_2 is not None else "Fluxo 2 não existe.")

# Verifica CNPJs que ficaram de fora
cnpjs_fluxos = pd.concat([
    fluxo_1['manifesto_gerador_cnpj'],
    fluxo_1['manifesto_destinador_cnpj'],
    fluxo_2['manifesto_gerador_cnpj'] if fluxo_2 is not None else pd.Series(dtype=str),
    fluxo_2['manifesto_destinador_cnpj'] if fluxo_2 is not None else pd.Series(dtype=str),
    fluxo_3['manifesto_gerador_cnpj'] if fluxo_3 is not None else pd.Series(dtype=str),
    fluxo_3['manifesto_destinador_cnpj'] if fluxo_3 is not None else pd.Series(dtype=str),
    fluxo_4['manifesto_gerador_cnpj'] if fluxo_4 is not None else pd.Series(dtype=str),
    fluxo_4['manifesto_destinador_cnpj'] if fluxo_4 is not None else pd.Series(dtype=str),
]).dropna().unique()

cnpjs_df = pd.concat([
    df['manifesto_gerador_cnpj'],
    df['manifesto_destinador_cnpj']
]).dropna().unique()

cnpjs_restantes = set(cnpjs_df) - set(cnpjs_fluxos)

print(f"Quantidade de CNPJs no DataFrame original: {len(cnpjs_df)}")
print(f"Quantidade de CNPJs em todos os fluxos: {len(cnpjs_fluxos)}")
print(f"CNPJs que não apareceram em nenhum fluxo: {len(cnpjs_restantes)}")

# Filtra linhas do DataFrame original onde os CNPJs restantes aparecem
filtro = df['manifesto_gerador_cnpj'].isin(cnpjs_restantes) | df['manifesto_destinador_cnpj'].isin(cnpjs_restantes)
df_restantes = df[filtro]
print(f"Linhas do DataFrame original correspondentes a esses CNPJs restantes: {len(df_restantes)}")
print(df_restantes)

# Exporta CNPJs restantes
pd.DataFrame({'CNPJ': list(cnpjs_restantes)}).to_excel('cnpjs_perdidos.xlsx', index=False)



#%%    
# ==================================================================
#           Balanço de massa dos fluxos intermediários
# ==================================================================
#
# Para saber a massa gerada nos fluxos intermediários, teremos que pegar cada fluxo, a partir do 2, o cnpj do gerador e ver quanta massa 
# chegou nele, a partir do fluxo_1, e quanto ele está destinando. Depois diminuir a saída pela entrada, se o resultado for +
# retornar numa coluna "gerado", se ele der -, retornar uma coluna "retido" o valor. 


saldos_por_fluxo = {}

for i in range(1, min(4, len(fluxos))):
    fluxo_anterior = fluxos[i - 1]
    fluxo_atual = fluxos[i]

    # Massa recebida no fluxo anterior (como destinatário)
    entrada = fluxo_anterior.groupby('manifesto_destinador_cnpj')['manifesto_item_quantidade'].sum().rename("entrada")

    # Massa enviada no fluxo atual (como gerador)
    saida = fluxo_atual.groupby('manifesto_gerador_cnpj')['manifesto_item_quantidade'].sum().rename("saida")

    # Junta as séries
    saldo = pd.concat([entrada, saida], axis=1).fillna(0)

    # Calcula saldo
    saldo['gerado'] = (saldo['saida'] - saldo['entrada']).clip(lower=0)
    saldo['retido'] = (saldo['entrada'] - saldo['saida']).clip(lower=0)

    # Reset index
    saldo = saldo.reset_index()

    # Detecta automaticamente o nome da coluna de CNPJ (será a do index original)
    cnpj_col = saldo.columns[0]

    # Pega linhas do df que tenham esse CNPJ como gerador ou destinador
    info_cnpj = df[
        (df['manifesto_gerador_cnpj'].isin(saldo[cnpj_col])) |
        (df['manifesto_destinador_cnpj'].isin(saldo[cnpj_col]))
    ].drop_duplicates(subset=['manifesto_gerador_cnpj', 'manifesto_destinador_cnpj'])

    # Faz o merge (juntando as informações do saldo com os dados originais)
    saldo_completo = pd.merge(saldo, info_cnpj, how='left', left_on=cnpj_col,
                               right_on='manifesto_gerador_cnpj')

    # Armazena no dicionário
    saldos_por_fluxo[f'fluxo_{i+1}'] = saldo_completo

# Cria DataFrames nomeados a partir do dicionário
df_fluxo_2_saldo = saldos_por_fluxo.get('fluxo_2', pd.DataFrame())
df_fluxo_3_saldo = saldos_por_fluxo.get('fluxo_3', pd.DataFrame())
df_fluxo_4_saldo = saldos_por_fluxo.get('fluxo_4', pd.DataFrame())

# Exemplo: visualizar os saldos do fluxo 2
print("Fluxo 2:")
print(saldos_por_fluxo['fluxo_2'].head())

# Fluxo 3 e 4:
print("\nFluxo 3:")
print(saldos_por_fluxo['fluxo_3'].head() if 'fluxo_3' in saldos_por_fluxo else "Não há fluxo 3.")

print("\nFluxo 4:")
print(saldos_por_fluxo['fluxo_4'].head() if 'fluxo_4' in saldos_por_fluxo else "Não há fluxo 4.")


total_gerado_1 = fluxo_1['manifesto_item_quantidade'].sum()
print(total_gerado_1)
total_gerado_2 = df_fluxo_2_saldo['gerado'].sum()
print(total_gerado_2)
total_gerado_3 = df_fluxo_3_saldo['gerado'].sum()
print(total_gerado_3)
total_gerado_4 = df_fluxo_4_saldo['gerado'].sum()
print(total_gerado_4)

Total_gerado = total_gerado_1 + total_gerado_2 + total_gerado_3 + total_gerado_4
print(Total_gerado)

total_retido_2 = df_fluxo_2_saldo['retido'].sum()
print(total_retido_2)
total_retido_3 = df_fluxo_3_saldo['retido'].sum()
print(total_retido_3)
total_retido_4 = df_fluxo_4_saldo['retido'].sum()
print(total_retido_4)

Total_retido = total_retido_2 + total_retido_3 + total_retido_4
print(Total_retido)

df_fluxo_2_saldo.to_excel('Fluxos_1_balanco.xlsx', index=False)
df_fluxo_3_saldo.to_excel('Fluxos_2_balanco.xlsx', index=False)
df_fluxo_4_saldo.to_excel('Fluxos_3_balanco.xlsx', index=False)

