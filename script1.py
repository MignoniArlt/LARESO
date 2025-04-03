# -*- coding: utf-8 -*-
"""
Created on Tue Mar 25 16:37:52 2025

@author: Usuário
"""
import pandas as pd
import matplotlib
import numpy as np

# Usando pandas para carregar o arquivo CSV
SC_2021 = pd.read_csv(r'C:\Users\Usuário\Documents\MTR_MMA\SC 2021.csv', sep=';')

print(SC_2021.info()) 

print(SC_2021['Quantidade recebida'].describe())

soma = SC_2021['Quantidade recebida'].sum()
print("Soma:", soma)

media = SC_2021['Quantidade recebida'].mean()
print("Média:", media)

print(SC_2021['Quantidade recebida'].dtype)

#%%
# Convertendo a coluna 'Quantidade recebida' para numérico
SC_2021['Quantidade recebida'] = pd.to_numeric(SC_2021['Quantidade recebida'], errors='coerce')

# Verificando se houve algum valor não numérico
print(SC_2021['Quantidade recebida'].head())

# Preenchendo valores NaN com 0 (ou outro valor, como a média)
SC_2021['Quantidade recebida'].fillna(0, inplace=True)

# Garantindo que as colunas "Gerador (CNPJ/CPF)" e "Destinador (CNPJ/CPF)" sejam tratadas como strings
SC_2021['Gerador (CNPJ/CPF)'] = SC_2021['Gerador (CNPJ/CPF)'].astype(str)
SC_2021['Destinador (CNPJ/CPF)'] = SC_2021['Destinador (CNPJ/CPF)'].astype(str)

SC_2021['Destinador (Nome)'] = SC_2021['Destinador (Nome)'].astype(str)
SC_2021['Gerador (Nome)'] = SC_2021['Gerador (Nome)'].astype(str)

SC_2021['Quantidade recebida'] = SC_2021['Quantidade recebida'].astype(float) 



#%%

# Somando a quantidade de resíduos para cada fluxo 
resultado = SC_2021.groupby(['Destinador (Municipio)' ,'Destinador (Estado)','Destinador (CNPJ/CPF)',
                             'Destinador (Nome)', 'Tipo Manifesto', 'Gerador (Municipio)', 'Gerador (Estado)',
                             'Gerador (CNPJ/CPF)', 'Gerador (Nome)' , 
                             'Tratamento', 'Resíduo Cód/Descrição', 'Classe'], as_index=False)['Quantidade recebida'].sum()

# Adiciona a coluna 'Ano' com o valor '2021' para todas as linhas
resultado['Ano'] = 2021

# mover coluna 'Ano' para o início
colunas = ['Ano'] + [col for col in resultado.columns if col != 'Ano']
resultado = resultado[colunas]

# Passando a coluna 'Resíduo Cód/Descrição' para string
resultado['Resíduo Cód/Descrição'] = resultado['Resíduo Cód/Descrição'].astype(str)

print(resultado)

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
resultado['Classificação'] = resultado['Resíduo Cód/Descrição'].apply(classificar_residuo)

resultado.to_excel('tabela_MMA2021.xlsx', index=False)