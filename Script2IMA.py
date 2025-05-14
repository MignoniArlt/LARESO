# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 13:07:56 2025

Novo script IMA para analisar os dados de fluxo

1. Unificação das tabelas 
2. "Limpar" dados 
3. Selecionar apenas dados que são em Toneladas
4. Selecionar apenas dados iguais ou abaixo de 45 toneladas 
6. Reclassificar os resíduos em uma nova coluna 
7. Somar as quantidades que são iguais 

@author: ASUS
"""


import pandas as pd
import matplotlib
import numpy as np


# Caminhos dos arquivos CSV
SC_2021_2 = r'C:\Users\ASUS\OneDrive\Documentos\MTR\IMA\MTR_2021_2.csv'
SC_2021_1 = r'C:\Users\ASUS\OneDrive\Documentos\MTR\IMA\MTR_2021_1.csv'

# Ler os arquivos CSV
df1 = pd.read_csv(SC_2021_1)
df2 = pd.read_csv(SC_2021_2) 

# Unir as tabelas (concatenando as linhas)
df_unido = pd.concat([df1, df2], ignore_index=True)

df_unido = df_unido[df_unido['manifesto_gerador_nome'].notna() & (df_unido['manifesto_gerador_nome'].str.strip() != '')]

# Excluindo as linhas Un e vazias 
df_unido = df_unido[(df_unido['manifesto_item_quantidade_unidade']!= 'Un') &
                    (df_unido['manifesto_item_quantidade_unidade']!= '')]

# ----- limpando os cnpjs ------

# funcao limpar
import re

def limpar_cnpj(cnpj):
    """Converte para string e remove tudo que não for número."""
    if pd.isna(cnpj):
        return None
    return re.sub(r'\D', '', str(cnpj).split('.')[0])

# Aplica ao DataFrame
df_unido['manifesto_gerador_cnpj'] = df_unido['manifesto_gerador_cnpj'].apply(limpar_cnpj)
df_unido['manifesto_destinador_cnpj'] = df_unido['manifesto_destinador_cnpj'].apply(limpar_cnpj)

# Converter a coluna manifesto_item_quantidadea para numérico
df_unido['manifesto_item_quantidade'] = pd.to_numeric(df_unido['manifesto_item_quantidade'], errors='coerce')

# Excluir as linhas onde a coluna 'manifesto_item_quantidade' é NaN ou vazia
df_unido = df_unido.dropna(subset=['manifesto_item_quantidade'])

# substituindo os valores NaN
df_unido['manifesto_item_quantidade'].fillna(0, inplace=True)
df_unido['manifesto_exportacao_pais'].fillna(0, inplace=True)
df_unido['manifesto_importacao_pais_nome'].fillna(0, inplace=True)

# Retornar tabela apenas com valores menores de 45 toneladas 
menores_que_45 = df_unido[df_unido['manifesto_item_quantidade'] <= 45]
print(menores_que_45)

# somar a quantidade 
soma = menores_que_45['manifesto_item_quantidade'].sum()
print(soma)

# reclassificaçao dos residuos 
# Classificação de resíduos 
def classificar_residuo(residuo):
    if residuo.startswith('01'):
        return 'RSM'
    elif residuo.startswith('17') or 'Classe' in residuo:  # Corrigido para verificar '17' e 'Classe'
        return 'RCC'
    elif residuo.startswith('0201'):
        return 'RSA'
    elif residuo.startswith(('2001', '1912', '1501', '1502')):
        return 'RSU'
    elif residuo.startswith('2002'):
        return 'RPU'
    elif residuo.startswith('18') or 'Grupo' in residuo:  # Corrigido para verificar '18' e 'Grupo'
        return 'RSS'
    elif residuo.startswith('19'):
        return 'RSB'
    elif residuo[:2].isdigit() and 3 <= int(residuo[:2]) <= 14:
        return 'RSI'
    elif residuo.startswith('16'):
        # Verificar exceções para 160123 a 160129, 1602, 1606
        if residuo in ['160123', '160124', '160125', '160126', '160127', '160128', '160129', '1602', '1606']:
            return 'Outros'
        else:
            return 'Outros'
    return 'Outros'  # Caso não se enquadre em nenhuma condição

# Criando a nova coluna 'Classificação'
menores_que_45['Classificação'] = menores_que_45['manifesto_item_residuo'].apply(classificar_residuo)


abaixo45semtipo = menores_que_45.groupby(['manifesto_destinador_municipio', 'manifesto_destinador_cnpj',
                             'manifesto_destinador_nome', 'manifesto_gerador_municipio', 
                             'manifesto_gerador_estado',
                             'manifesto_gerador_cnpj', 
                             'manifesto_gerador_nome', 'manifesto_item_residuo', 'Classificação',
                             'manifesto_tecnologia_destinacao'], as_index=False)['manifesto_item_quantidade'].sum()
#abaixo45.to_csv("abaixo45.csv", index=False)


# Tratar os cnpj de maneira unitaria
cnpjs_geradores = set(menores_que_45['manifesto_gerador_cnpj'].dropna().unique())
cnpjs_destinadores = set(menores_que_45['manifesto_destinador_cnpj'].dropna().unique())

#%%
# cnpjs dos intermediarios
cnpjs_em_ambos = cnpjs_geradores & cnpjs_destinadores

len(cnpjs_em_ambos)
pd.DataFrame(cnpjs_em_ambos, columns=['cnpj'])

# gerando df para os intermediarios
intermediarios = menores_que_45[
    menores_que_45['manifesto_gerador_cnpj'].isin(cnpjs_em_ambos) &
    menores_que_45['manifesto_destinador_cnpj'].isin(cnpjs_em_ambos)
]

# Somando a quantidade de resíduos para cada fluxo 
intermediariosSoma = intermediarios.groupby(['manifesto_destinador_municipio', 'manifesto_destinador_cnpj',
                             'manifesto_destinador_nome', 'manifesto_exportacao_pais', 'manifesto_gerador_municipio', 
                             'manifesto_gerador_estado', 'manifesto_importacao_pais_nome',
                             'manifesto_gerador_cnpj', 'manifesto_gerador_nome' , 
                             'manifesto_tecnologia_destinacao', 'manifesto_item_residuo',
                             'manifesto_residuo_classe'], as_index=False)['manifesto_item_quantidade'].sum()

# gerando excel dos intermediarios 
#intermediariosSoma.to_excel("somente_intermediarios.xlsx", index=False)

soma1 = intermediarios['manifesto_item_quantidade'].sum()
print(soma1)

#%%
# cnpjs apenas geradores 
somente_geradores = cnpjs_geradores - cnpjs_destinadores

apenas_geradores = menores_que_45[
    menores_que_45['manifesto_gerador_cnpj'].isin(somente_geradores)
]

# Somando a quantidade de resíduos para cada fluxo 
geradoresSoma = apenas_geradores.groupby(['manifesto_destinador_municipio', 'manifesto_destinador_cnpj',
                             'manifesto_destinador_nome', 'manifesto_exportacao_pais', 'manifesto_gerador_municipio', 
                             'manifesto_gerador_estado', 'manifesto_importacao_pais_nome',
                             'manifesto_gerador_cnpj', 'manifesto_gerador_nome' , 
                             'manifesto_tecnologia_destinacao', 'manifesto_item_residuo',
                             'manifesto_residuo_classe'], as_index=False)['manifesto_item_quantidade'].sum()

#geradoresSoma.to_excel("somente_geradores.xlsx", index=False)

soma2 = geradoresSoma['manifesto_item_quantidade'].sum()
print(soma2)









