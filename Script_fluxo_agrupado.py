# -*- coding: utf-8 -*-
"""
Created on Fri Mar 28 16:45:01 2025

@author: Usuário
"""

import pandas as pd
import matplotlib
import numpy as np

# Caminhos dos arquivos CSV
SC_2021_IMA = r'C:\Users\Usuário\Documents\MTR_IMA\tabela_IMA2021.csv'
SC_2021_MMA = r'C:\Users\Usuário\Documents\MTR_MMA\tabela_MMA2021.csv'

# Ler os arquivos CSV
df1 = pd.read_csv(SC_2021_IMA, sep=';', encoding='latin1')
df2 = pd.read_csv(SC_2021_MMA, sep=';', encoding='latin1')

# Unir as tabelas (concatenando as linhas)
df_unido = pd.concat([df1, df2], ignore_index=True)

# Adiciona a colunas
df1['Destinador (Estado)'] = "SC"
df1['Tipo Manifesto'] = "Normal"
df1['MTR'] = "IMA"

df2['Exportação (País)'] = 0
df2['Importação (País)'] = 0
df2['MTR'] = "MMA"

# Juntando as duas
df_combined = pd.concat([df1, df2], ignore_index=True)

# Condições específicas para suprimir duplicadas 

# Nome da coluna que queremos maximizar
coluna_quantidade = "Quantidade recebida"

# Lista de colunas a serem ignoradas na comparação
colunas_ignorar = ["Destinador (Estado)", "Tipo Manifesto", "MTR", "Exportação (País)",
                   "Importação (País)", "Classe", "Destinador (CNPJ/CPF)", "Gerador (CNPJ/CPF)"]

# Criar a lista de colunas para agrupar, excluindo "Quantidade recebida" e as que devem ser ignoradas
colunas_grupo = [col for col in df_combined.columns if col not in colunas_ignorar + [coluna_quantidade]]

# Identificar as linhas que deveriam ser mantidas
idx_max = df_combined.groupby(colunas_grupo, dropna=False)[coluna_quantidade].idxmax()

# Criar a coluna "Linha Modificada" com valor padrão False
df_combined["Linha Modificada"] = False

# Atualizar para True nas linhas que foram removidas
df_combined.loc[~df_combined.index.isin(idx_max), "Linha Modificada"] = True

# Manter apenas as linhas com os maiores valores em "Quantidade recebida"
df_final = df_combined.loc[idx_max].reset_index(drop=True)

# Exibir o resultado
print(df_final.head())


# Exportar em excel 
df_final.to_excel('tabela_MTR2021.xlsx', index=False)