# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 16:36:38 2025

@author: Usuário
"""

import pandas as pd
import matplotlib
import numpy as np

# Caminhos dos arquivos CSV
SC_2021_2 = r'C:\Users\Usuário\Documents\MTR_IMA\MTR_IMA2021-2.csv'
SC_2021_1 = r'C:\Users\Usuário\Documents\MTR_IMA\MTR_IMA2021-1.csv'

# Ler os arquivos CSV
df1 = pd.read_csv(SC_2021_1, sep = ';')
df2 = pd.read_csv(SC_2021_2, sep = ';')

# Unir as tabelas (concatenando as linhas)
df_unido = pd.concat([df1, df2], ignore_index=True)

# Mostrar o DataFrame unido
print(df_unido)

print(df_unido.info()) 

soma = df_unido['manifesto_item_quantidade'].sum()
print("Soma:", soma)

# Converter a coluna manifesto_item_quantidadea para numérico
df_unido['manifesto_item_quantidade'] = pd.to_numeric(df_unido['manifesto_item_quantidade'], errors='coerce')

# Excluir as linhas onde a coluna 'manifesto_item_quantidade' é NaN ou vazia
df_unido = df_unido.dropna(subset=['manifesto_item_quantidade'])

# Preenchendo valores NaN com 0 (ou outro valor, como a média)
df_unido['manifesto_item_quantidade'].fillna(0, inplace=True)
df_unido['manifesto_exportacao_pais'].fillna(0, inplace=True)
df_unido['manifesto_importacao_pais_nome'].fillna(0, inplace=True)

# Somando a quantidade de resíduos para cada fluxo 
resultado = df_unido.groupby(['manifesto_destinador_municipio', 'manifesto_destinador_cnpj',
                             'manifesto_destinador_nome', 'manifesto_exportacao_pais', 'manifesto_gerador_municipio', 
                             'manifesto_gerador_estado', 'manifesto_importacao_pais_nome',
                             'manifesto_gerador_cnpj', 'manifesto_gerador_nome' , 
                             'manifesto_tecnologia_destinacao', 'manifesto_item_residuo',
                             'manifesto_residuo_classe'], as_index=False)['manifesto_item_quantidade'].sum()

# Adiciona a coluna 'Ano' com o valor '2021' para todas as linhas
resultado['Ano'] = 2021

# mover coluna 'Ano' para o início
colunas = ['Ano'] + [col for col in resultado.columns if col != 'Ano']
resultado = resultado[colunas]

# Criar coluna para classificação de resíduos com condições 
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
resultado['Classificação'] = resultado['manifesto_item_residuo'].apply(classificar_residuo)



resultado.to_excel('tabela_IMA2021.xlsx', index=False)
