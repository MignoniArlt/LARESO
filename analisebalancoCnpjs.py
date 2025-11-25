# -*- coding: utf-8 -*-
"""
Created on Thu Nov 13 13:54:39 2025

Analisar balanço de massa dos MTRs 

@author: ASUS
"""


import pandas as pd 
import os 
import numpy as np
import sqlite3
import re
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry import Point, LineString


# importar banco de dados MTR 

# caminho do banco
caminho_db = r"C:\Users\ASUS\OneDrive\Documentos\MTR\IMA\mtr_total.db"

# conecta no banco
con = sqlite3.connect(caminho_db)

# lista as tabelas existentes
tabelas = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", con)
print("Tabelas disponíveis:\n", tabelas)

# escolher uma tabela e carregar em DataFrame
mtr = pd.read_sql("SELECT * FROM mtr;", con)

print(mtr.head())

# fecha a conexão
con.close()

#%%

## Definindo função para classificar os resíduos 
def classificar_residuo(residuo):
    if residuo.startswith('01'):
        return 'RSM'
    elif residuo.startswith('17') or 'Classe' in residuo: 
        return 'RCC'
    elif residuo.startswith('0201'):
        return 'RSA'
    elif residuo.startswith(('2001', '1912', '1501', '2002', '1606')):
        return 'RSU'
    elif residuo.startswith(('2003')):
        if residuo in ['200304']:
            return 'RSAE'
        else:
            return 'RSU'
    elif residuo.startswith('2002'):
        return 'RSU'
    elif residuo.startswith('18') or 'Grupo' in residuo: 
        return 'RSS'
    elif residuo.startswith(('19', '200304')):
        return 'RSAE'
    elif residuo.startswith(('1601')):
        if residuo in ['160123', '160124', '160125', '160127', '160128', '160129']:
            return 'RSU'
        else:
            return 'Outros' # criar um para analisar os cnpjs que correspondem as empressas de transporte
    elif residuo[:2].isdigit() and 3 <= int(residuo[:2]) <= 14:
        return 'RSI'
    elif residuo.startswith(('0202', '0203', '0204', '0205', '0206', '0207', '1502', '1602', '1607')):
        return 'RSI'
    elif residuo.startswith(('1603', '1604', '1605', '1606', '1608', '1609', '161')):
            return 'Outros'
    return 'Outros'  # Caso não se enquadre em nenhuma condição

## Definindo função para limpar caracteres inválidos 
def clean_excel_string(s):
    if isinstance(s, str):
        return re.sub(r'[\x00-\x1F]+', '', s)
    return s

# Criando a nova coluna 'Classificação'
mtr['Classificação'] = mtr['manifesto_item_residuo'].apply(classificar_residuo)

mtr2024 = mtr[mtr['ano'] == 2024]



#%% Normalizar cnpjs
# Converte para inteiro (removendo decimais), depois para string com 14 dígitos
mtr2024["manifesto_gerador_cnpj"] = (
    pd.to_numeric(mtr2024["manifesto_gerador_cnpj"], errors="coerce")
      .dropna()
      .astype("Int64")
      .astype(str)
      .str.zfill(14)
)

mtr2024["manifesto_destinador_cnpj"] = (
    pd.to_numeric(mtr2024["manifesto_destinador_cnpj"], errors="coerce")
      .dropna()
      .astype("Int64")
      .astype(str)
      .str.zfill(14)
)

# excluir linha estranha 
mtr2024 = mtr2024.drop(9296865)

#%% Balanço de massa por unidade 

# Soma do que cada empresa gerou
gerado = mtr2024.groupby(['manifesto_gerador_cnpj', 'manifesto_gerador_nome'], as_index=False).agg({
    'manifesto_item_quantidade_recebida': 'sum',
    'manifesto_item_residuo': lambda x: ', '.join(sorted(set(x)))
}).rename(columns={'manifesto_item_quantidade_recebida': 'quant_gerada', 'manifesto_item_residuo': 'tipos_gerados'})

# Soma do que cada empresa recebeu
recebido = mtr2024.groupby(['manifesto_destinador_cnpj', 'manifesto_destinador_nome'], as_index=False).agg({
    'manifesto_item_quantidade_recebida': 'sum',
    'manifesto_item_residuo': lambda x: ', '.join(sorted(set(x))),
    'manifesto_tecnologia_destinacao': lambda x: ', '.join(sorted(set(x))),
    'manifesto_destinador_municipio': 'first'
}).rename(columns={'manifesto_gerador_cnpj': 'cnpj', 'manifesto_gerador_nome': 'nome',
                   'manifesto_item_quantidade_recebida': 'quant_recebida', 'manifesto_item_residuo': 'tipos_recebidos'})

# junta os dois 
gerado = gerado.rename(columns={'manifesto_gerador_cnpj': 'cnpj', 'manifesto_gerador_nome': 'nome'})
recebido = recebido.rename(columns={'manifesto_destinador_cnpj': 'cnpj', 'manifesto_destinador_nome': 'nome'})

balanco = pd.merge(gerado, recebido, on=['cnpj', 'nome'], how='outer')

# Calcula saldo 
balanco['quant_gerada'] = balanco['quant_gerada'].fillna(0)
balanco['quant_recebida'] = balanco['quant_recebida'].fillna(0)
balanco['saldo'] = balanco['quant_gerada'] - balanco['quant_recebida']

# Junta os tipos de resíduos (gerados + recebidos) 
balanco['tipos_residuos_total'] = balanco[['tipos_gerados', 'tipos_recebidos']].fillna('').agg(lambda x: ', '.join(sorted(set(', '.join(x).split(', ')))), axis=1)

## Balanço até aqui 


#%% 
#classificação das unidades 

# Evita divisão por zero
balanco['soma_total'] = balanco['quant_gerada'] + balanco['quant_recebida']
balanco['saldo_relativo'] = np.where(
    balanco['soma_total'] > 0,
    (balanco['quant_gerada'] - balanco['quant_recebida']) / balanco['soma_total'],
    0
)

# Calcula percentis 
p20, p40, p60, p80 = np.percentile(balanco['saldo_relativo'], [20, 40, 60, 80])

print(f"Percentis:\n20%: {p20:.2f}, 40%: {p40:.2f}, 60%: {p60:.2f}, 80%: {p80:.2f}")

# Classificação baseada nos percentis
def classificar_unidade(saldo_relativo):
    if saldo_relativo >= p80:
        return 'GERADOR'
    elif saldo_relativo >= p60:
        return 'INTERMEDIÁRIO GERADOR'
    elif saldo_relativo >= p40:
        return 'INTERMEDIÁRIO NEUTRO'
    elif saldo_relativo >= p20:
        return 'INTERMEDIÁRIO DESTINADOR'
    else:
        return 'DESTINADOR FINAL'

balanco['categoria'] = balanco['saldo_relativo'].apply(classificar_unidade)

# Remove coluna auxiliar
balanco_final = balanco.drop(columns=['soma_total'])

# --- HISTOGRAMA ---
plt.figure(figsize=(8,5))
plt.hist(balanco_final['saldo_relativo'], bins=30, edgecolor='black')
plt.axvline(p20, color='red', linestyle='--', label='20%')
plt.axvline(p40, color='orange', linestyle='--', label='40%')
plt.axvline(p60, color='green', linestyle='--', label='60%')
plt.axvline(p80, color='blue', linestyle='--', label='80%')
plt.title('Distribuição do Saldo Relativo de Massa')
plt.xlabel('Saldo Relativo = (Gerado - Recebido) / (Gerado + Recebido)')
plt.ylabel('Número de CNPJs')
plt.legend()
plt.show()

# --- RESUMO DE CATEGORIAS ---
resumo = balanco_final['categoria'].value_counts().reset_index()
resumo.columns = ['Categoria', 'Número de CNPJs']
resumo['Percentual (%)'] = (resumo['Número de CNPJs'] / len(balanco_final) * 100).round(1)

print("\nResumo de categorias:\n")
print(resumo)

# Exibe amostra do resultado
balanco_final[['cnpj', 'nome', 'quant_gerada', 'quant_recebida', 'saldo_relativo', 'categoria']].head()


balanco_final.to_excel('balançoMassaUnidades2024.xlsx', index=True)

# planilha até aqui 

#%%   a partir daqui algumas analises realizadas para tentar verificar o comportamento das unidades
#Histograma


# valores sem geradores puros e sem destinadores puros 

# filtrar para valores onde o gerador é differente de zero 
intermediarios = balanco[balanco['quant_gerada'] != 0]
# filtrar para valores onde o destinador é diferente de zero
intermediarios = intermediarios[intermediarios['quant_recebida'] != 0]

# Ordenar
dados_ordenados = intermediarios['saldo'].sort_values().reset_index(drop=True)

y = dados_ordenados

# criar o x automaticamente
x = np.arange(1, len(y) + 1)

# ajustar um polinômio (ex: grau 3)
grau = 3
coef = np.polyfit(x, y, grau)
p = np.poly1d(coef)

print("Equação encontrada:")
print(p)

# plotar
plt.scatter(x, y, label='dados', s=40)

#x_fit = np.linspace(x.min(), x.max(), 300)
#plt.plot(x_fit, p(x_fit), label=f'Polinômio grau {grau}', linewidth=2)

plt.grid()
plt.legend()
plt.show()


#%% descobrir o melhor grau
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import numpy as np
import ruptures as rpt

x = np.arange(len(y))
signal = y.copy()

model = rpt.Pelt(model="rbf").fit(signal)
breaks = model.predict(pen=50)   
print(breaks)


#%% plotar com os break points

import numpy as np
from numpy.polynomial.polynomial import polyfit, polyval
import matplotlib.pyplot as plt

# x e y definidos antes
# suposição de pontos de mudança
b1, b2 = 215, 870


# Transformação tipo "log" mas que aceita negativos
def t(x):
    return np.arcsinh(x)

# Ajuste por trechos
coef1 = np.polyfit(x[:b1], t(y[:b1]), deg=1)      # ajuste linear no espaço arcsinh
coef2 = np.polyfit(x[b1:b2], y[b1:b2], deg=1)     # linear normal
coef3 = np.polyfit(x[b2:], y[b2:], deg=2)         # polinomial

# Reconstrução
y_fit = np.zeros_like(y)

# Inverso da transformação arcsinh
def inv_t(z):
    return np.sinh(z)

y_fit[:b1]     = inv_t(np.polyval(coef1, x[:b1]))
y_fit[b1:b2]   = np.polyval(coef2, x[b1:b2])
y_fit[b2:]     = np.polyval(coef3, x[b2:])

# Plot
plt.figure(figsize=(12,6))
plt.scatter(x, y, s=10, label="dados")
plt.plot(x, y_fit, color="red", linewidth=2, label="ajuste piecewise (arcsinh)")
plt.legend()
plt.grid()
plt.show()

print("coef1 (arcsinh):", coef1)
print("coef2 (linear):", coef2)
print("coef3 (quadrático):", coef3)

## pra achar o vértice 

# Trecho 1
trecho1 = y_fit[:b1]
xs1 = x[:b1]

imin1 = np.argmin(trecho1)
imax1 = np.argmax(trecho1)

print("Trecho 1 - mínimo:", xs1[imin1], trecho1[imin1])
print("Trecho 1 - máximo:", xs1[imax1], trecho1[imax1])

#%% 


import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# --- parâmetros (ajuste se quiser) ---
b1, b2 = 215, 870   # seus pontos de corte
min_points = 8      # mínimo de pontos para considerar reta inicial
r2_threshold = 0.98 # R² mínimo para considerar trecho linear "bom"

# garante arrays numpy
x = np.asarray(x)
y = np.asarray(y).astype(float)

# -------- 1) detecta porção inicial aproximadamente linear dentro de [0, b1)
best_s = None
best_r2 = -np.inf

# testa todos os cortes possíveis entre min_points e b1-1
for s in range(min_points, max(min_points+1, b1-4)):
    xi = x[:s].reshape(-1,1)
    yi = y[:s]
    model = LinearRegression().fit(xi, yi)
    ypred = model.predict(xi)
    r2 = r2_score(yi, ypred)
    # guardamos o maior s que ainda tem R2 >= threshold (prefira porção maior linear)
    if r2 >= r2_threshold:
        best_s = s
        best_r2 = r2

# fallback: se não encontrou, escolhe s como ponto onde a curvatura começa pela segunda-derivada
if best_s is None:
    # calc segunda derivada numérica no intervalo 0:b1
    dy = np.gradient(y[:b1], x[:b1])
    ddy = np.gradient(dy, x[:b1])
    # detecta primeiro índice onde |segunda derivada| ultrapassa mediana*factor
    factor = 3.0
    thr = np.median(np.abs(ddy)) * factor
    candidates = np.where(np.abs(ddy) > thr)[0]
    if len(candidates) > 0:
        best_s = int(max(min_points, candidates[0]))  # pega o primeiro índice "não linear"
    else:
        best_s = max(min_points, int(b1*0.2))  # fallback conservador: 20% de b1

# agora ajusta uma reta à porção [0:best_s]
xi = x[:best_s].reshape(-1,1)
yi = y[:best_s]
lr1 = LinearRegression().fit(xi, yi)
m1 = lr1.coef_[0]
c1 = lr1.intercept_

# reta do trecho 2 (supondo que você já tem coef2 igual a np.polyfit -> [m2, c2])
# se não tiver, calcula agora:
# coef2 = np.polyfit(x[b1:b2], y[b1:b2], deg=1)  # caso precise recalcular
# m2, c2 = coef2[0], coef2[1]

# aqui assumimos que você tem coef2 no ambiente:
m2, c2 = coef2[0], coef2[1]

# -------- 2) calcular interseção analítica (se possível)
if abs(m1 - m2) < 1e-12:
    print("As retas são praticamente paralelas (m1 ~= m2). Não há interseção única.")
    x_inter = None
    y_inter = None
else:
    x_inter = (c2 - c1) / (m1 - m2)
    y_inter = m1 * x_inter + c1

# -------- 3) imprimir resultados e plotar
print(f"Detectado final da porção linear inicial (best_s) = {best_s} (R² ≈ {best_r2:.4f})")
print(f"Reta inicial (ajustada a 0:{best_s}): y = {m1:.6f} * x + {c1:.6f}")
print(f"Reta do trecho 2 : y = {m2:.6f} * x + {c2:.6f}")
if x_inter is not None:
    print(f"Interseção: x = {x_inter:.4f}, y = {y_inter:.4f}")
else:
    print("Interseção não definida (retas paralelas).")

# plot pra conferir
plt.figure(figsize=(10,5))
plt.scatter(x, y, s=12, alpha=0.6, label='dados', zorder=1)
# plot ajuste piecewise (opcional: sua reconstrução y_fit se já tiver)
if 'y_fit' in globals():
    plt.plot(x, y_fit, color='red', linewidth=2, label='ajuste piecewise', zorder=2)

# desenha reta inicial ajustada
xs_plot = np.linspace(0, b1, 200)
plt.plot(xs_plot, m1*xs_plot + c1, color='orange', linestyle='--', linewidth=2, label='reta inicial (fit)')

# desenha reta trecho2
xs_plot2 = np.linspace(0, x.max(), 200)
plt.plot(xs_plot2, m2*xs_plot2 + c2, color='green', linestyle='--', linewidth=2, label='reta trecho2')

# marca o final do segmento linear detectado e a interseção
plt.axvline(best_s, color='gray', linestyle=':', label=f'final linear ≈ {best_s}')
if x_inter is not None:
    plt.scatter([x_inter], [y_inter], color='black', s=80, zorder=10, label=f'interseção ({x_inter:.2f},{y_inter:.1f})')

plt.xlim(-5, x.max()+5)
plt.legend()
plt.grid(alpha=0.3)
plt.title("Detecção da porção linear inicial e interseção com a reta do trecho 2")
plt.show()

