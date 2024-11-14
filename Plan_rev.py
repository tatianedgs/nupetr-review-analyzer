import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import locale
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression



# Configura o título e o ícone da página
st.set_page_config(page_title="Dashboard", layout="wide")

#########
st.markdown(
    """
    <style>
    body {
        background-color: #ffffff; /* Altere essa cor para o fundo desejado */
    }
    </style>
    """,
    unsafe_allow_html=True
)

############

# URL do ícone de - *** FALTA AJUSTAR ***
oil_rig_icon_url = "https://yt3.googleusercontent.com/vAsYHLthpm1q9vRIlkOO4JDmlUCrvk1zPbzYMN7wRLnkwNBTD88hMACD0EVWBvyY6C0Al_dW43M=s176-c-k-c0x00ffffff-no-rj"

# Título centralizado
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Sistema de Facilitação de Comunicação Interna no NUPETR</h1>", unsafe_allow_html=True)

# Sidebar com informações adicionais
with st.sidebar:
    # Título de agradecimento (IDEMA - NUPETR), centralizado e destacado
    st.sidebar.markdown('<h1 style="text-align: center; color: #4CAF50; font-weight: bold;">IDEMA - NUPETR</h1>', unsafe_allow_html=True)

    # Explicação sobre a aplicação, com formato mais compacto e link centralizado
    st.sidebar.markdown('<h3 style="text-align: center; color: #388E3C;">Sobre o Sistema</h3>', unsafe_allow_html=True)
    st.sidebar.markdown("""
        <sub>Desenvolvido por Tatiane Santos ([LinkedIn](https://www.linkedin.com/in/tatiane-santos-31b79938))<br>
        <sup>Código fonte disponível [aqui](https://github.com)<br>
        <sup><strong>Obs:</strong> Sistema de Prova de Conceito, pode conter erros.
    """, unsafe_allow_html=True)

    # Explicação sobre a base de dados (texto resumido e com estilo verde)
    st.sidebar.markdown("""
        Faça o upload da planilha CSV com as revisões do NUPETR.
    """, unsafe_allow_html=True)

    # Carregamento da base de dados
    uploaded_file = st.sidebar.file_uploader("Clique para carregar o arquivo CSV:", type="csv")

    # Filtros (título maior e com destaque em verde)
    st.sidebar.markdown('<h4 style="text-align: center; color: #388E3C; font-weight: bold;">Filtros</h4>', unsafe_allow_html=True)
    st.sidebar.markdown("""
        Utilize os filtros abaixo para ajustar os dados conforme necessário.
    """, unsafe_allow_html=True)


# Função para criar a coluna Codigo_Processo
def criar_codigo_processo(df):
    # Utiliza uma expressão regular para extrair os seis números próximos de /TEC ou -TEC, em qualquer posição
    df['Codigo_Processo'] = df['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].str.extract(r'(\d{6})(?=.*TEC)', expand=False)

    # Preenchendo possíveis valores ausentes na coluna 'Codigo_Processo' com um identificador genérico
    df['Codigo_Processo'] = df['Codigo_Processo'].fillna('Desconhecido')

    # Contagem total de cada processo
    df['Contagem_Processo'] = df.groupby('Codigo_Processo')['Codigo_Processo'].transform('count')
    
    # Contagem por processo e por analista
    df['Contagem_Processo_Por_Analista'] = df.groupby(['Codigo_Processo', 'Analista (você)'])['Codigo_Processo'].transform('count')
    
    return df

# Função para carregar dados do arquivo CSV
def load_data(file_path):
    try:
        # Tenta carregar o arquivo com codificação utf-8
        df = pd.read_csv(file_path, encoding='utf-8', dayfirst=True)
    except UnicodeDecodeError:
        # Em caso de erro de decodificação, tenta com latin1
        df = pd.read_csv(file_path, encoding='latin1', dayfirst=True)
    
    # Verifica se a coluna "Carimbo de data/hora" existe e faz a conversão para datetime
    if 'Carimbo de data/hora' in df.columns:
        df['Carimbo de data/hora'] = pd.to_datetime(df['Carimbo de data/hora'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    else:
        st.warning("A coluna 'Carimbo de data/hora' não foi encontrada no arquivo.")
    
    return df


# Página selecionada pelo usuário
def main():
    paginaSelecionada = st.selectbox("Selecione a página:", ["Visão Global - NUPETR", "Visão - Analista", "Visão - Revisão", "Resumo de Envios", "Resumo de Revisões", "Análise dos Tempos e Estatísticas", ])

    if paginaSelecionada == "Visão Global - NUPETR":
        visao_global()
    elif paginaSelecionada == "Visão - Analista":
        visao_analista()
    elif paginaSelecionada == "Visão - Revisão":
        visao_revisao()
    elif paginaSelecionada == "Resumo de Envios":
        resumo_envios()
    elif paginaSelecionada == "Resumo de Revisões":
        resumo_revisoes()
    elif paginaSelecionada == "Análise dos Tempos e Estatísticas":
        analise_tempos()

# Função para formatar a exibição da semana com intervalo de datas dos envios
def formatar_semanas(df):
    semanas_disponiveis_envio = []
    for ano in sorted(df['ANO_envio'].unique(), reverse=True):
        if ano == 0:
            continue  # Ignora ano 0
        for semana in sorted(df[df['ANO_envio'] == ano]['SEMANA_envio'].unique(), reverse=True):
            if semana == 0:
                continue  # Ignora semana 0
            inicio_semana = datetime.strptime(f'{int(ano)}-W{int(semana)}-1', "%Y-W%W-%w")
            fim_semana = inicio_semana + timedelta(days=6)
            semanas_disponiveis_envio.append(
                (int(ano), int(semana), f"Semana {int(semana)} - {inicio_semana.strftime('%d/%m/%y')} a {fim_semana.strftime('%d/%m/%y')}")
            )
    return semanas_disponiveis_envio

# Função para formatar a exibição da semana com intervalo de datas das revisões
def formatar_semanas_revisão(df):
    semanas_disponiveis_revisão = []
    
    # Filtra apenas valores válidos para ANO
    anos_validos = pd.to_numeric(df['ANO'], errors='coerce').dropna().astype(int).unique()
    
    for ano in sorted(anos_validos, reverse=True):
        if ano == 0:
            continue  # Ignora ano 0
        for semana in sorted(df[(df['ANO'].notna()) & (df['ANO'] == ano)]['SEMANA_revisão'].dropna().unique(), reverse=True):
            if semana > 0:
                try:
                    inicio_semana = datetime.strptime(f'{int(ano)}-W{int(semana)}-1', "%Y-W%W-%w")
                    fim_semana = inicio_semana + timedelta(days=6)
                    semanas_disponiveis_revisão.append(
                        (int(ano), int(semana), f"Semana {int(semana)} - {inicio_semana.strftime('%d/%m/%y')} a {fim_semana.strftime('%d/%m/%y')}")
                    )
                except ValueError:
                    st.warning(f"A semana {semana} do ano {ano} é inválida e foi ignorada.")
    return semanas_disponiveis_revisão

# Função aprimorada para extrair o tipo de processo
def extrair_tipo_processo(numero_processo):
    # Lista das siglas reconhecidas
    siglas_reconhecidas = ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']
    match = re.search(r'TEC[-]*([A-Z]{2,3})', numero_processo, re.IGNORECASE)
    if match:
        sigla = match.group(1).upper()
        if sigla in siglas_reconhecidas:
            return sigla
    for sigla in siglas_reconhecidas:
        if re.search(rf'\b{sigla}\b', numero_processo, re.IGNORECASE):
            return sigla
    return 'Outros'


# Função para criar a visão global
def visao_global():
    
    if uploaded_file is not None:
        # Carrega os dados do arquivo
        df = load_data(uploaded_file)

        st.markdown(
            "<h1 style='text-align: center; color: #98FF98; font-size: 42px; font-weight: bold; text-decoration: underline;'>Visão Global - NUPETR</h1>",
            unsafe_allow_html=True
        )

        # Filtrar o DataFrame para remover processos "cancelados" e "cancelar"
        df = df[~df['Qual o tipo de envio?'].str.contains(r'\bcancel(ad|ar)\b', case=False, na=False)]

        if df is not None and not df.empty:
            # Convertendo valores de ano, mês e semana, tratando valores ausentes
            df['MÊS_envio'] = df['Carimbo de data/hora'].dt.month.fillna(0).astype(int)
            df['ANO_envio'] = df['Carimbo de data/hora'].dt.year.fillna(0).astype(int)
            df['SEMANA_envio'] = df['Carimbo de data/hora'].dt.isocalendar().week.fillna(0).astype(int)

            # Filtrando anos e meses disponíveis como inteiros, removendo o valor 0
            anos_disponiveis_envio = [ano for ano in sorted(df['ANO_envio'].unique(), reverse=True) if ano != 0]
            meses_disponiveis_envio = [mes for mes in sorted(df['MÊS_envio'].unique(), reverse=True) if mes != 0]

            # Adicionando a opção "TODOS" para ano e mês
            anos_disponiveis_envio.insert(0, "TODOS")
            meses_disponiveis_envio.insert(0, "TODOS")

            # Gerando semanas disponíveis com intervalos de datas, sem semanas/anos inválidos
            semanas_disponiveis_envio = formatar_semanas(df)

            # Incluindo a opção "TODOS" para semanas
            semanas_disponiveis_envio.insert(0, "TODOS")

            # Obter o mês e ano atual
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year

            # Seleção padrão inicial
            ano_default = [ano_atual] if ano_atual in anos_disponiveis_envio else ["TODOS"]
            mes_default = [mes_atual] if mes_atual in meses_disponiveis_envio else ["TODOS"]
            semana_default = ["TODOS"]

            # Sidebar para seleção de ano, mês e semana
            ano = st.sidebar.multiselect("SELECIONE O ANO", options=anos_disponiveis_envio, default=ano_default)
            mes = st.sidebar.multiselect("SELECIONE O MÊS", options=meses_disponiveis_envio, default=mes_default)
            semana = st.sidebar.multiselect(
                "SELECIONE A SEMANA", 
                options=semanas_disponiveis_envio, 
                default=semana_default, 
                format_func=lambda x: x[2] if isinstance(x, tuple) else x
            )

            # Aplicando os filtros de ano, mês e semana ao DataFrame
            df_selection = df
            if "TODOS" not in ano:
                df_selection = df_selection[df_selection['ANO_envio'].isin(ano)]
            if "TODOS" not in mes:
                df_selection = df_selection[df_selection['MÊS_envio'].isin(mes)]

            # Verifica se "TODOS" não está selecionado para aplicar o filtro da semana
            if "TODOS" not in semana:
                semanas_selecionadas = [s[1] for s in semana if isinstance(s, tuple)]  # Extrai apenas o número da semana
                df_selection = df_selection[df_selection['SEMANA_envio'].isin(semanas_selecionadas)]


            # Criando a coluna Codigo_Processo
            df_selection = criar_codigo_processo(df_selection)

            # Contagem de processos enviados (excluindo os processos com status de cancelamento)
            quantidade_processos_enviados = df_selection[~df_selection['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)].shape[0]
  
            # Contagem de envios por tipo
            envios_por_tipo = df_selection['Qual o tipo de envio?'].value_counts()
 
            # Contagem de reenvio
            reenvio = envios_por_tipo.get('Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)', 0)

            # Contagem de prioridades
            prioridades = envios_por_tipo.get('Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)',  0)
 
            # Contagem de 1º envio
            primeiro_envio = envios_por_tipo.get('1º envio (Primeira vez que o Parecer está sendo enviado para revisão)', 0)
   
            # Espaçador ou linha de separação entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            # Exibindo resultados
            st.subheader('Envios Realizados para a Planilha de Revisão do NUPETR')

            # Layout: 4 colunas, com informações centralizadas e contornadas
            col1, col2, col3, col4 = st.columns(4)

            # Definindo estilo customizado para métricas
            def style_metric_box(box_color, font_color):
                return f"""
                    <div style="background-color:{box_color}; padding:10px; border-radius:10px; border:2px solid #ddd;">
                        <h4 style="color:{font_color}; text-align:center;">{{}}</h4>
                        <h2 style="color:{font_color}; text-align:center;">{{}}</h2>
                    </div>
                """

            # Renderizando métricas com estilo e cores ajustadas
            with col1:               
                st.markdown("<hr style='border: 2px solid #ccc;'/>", unsafe_allow_html=True)
                st.markdown(style_metric_box("#66BB6A", "black").format("Total", quantidade_processos_enviados), unsafe_allow_html=True)

            with col2:
                st.markdown("<hr style='border: 2px solid #ccc;'/>", unsafe_allow_html=True)
                st.markdown(style_metric_box("#FF7043", "black").format("Prioridades", prioridades), unsafe_allow_html=True)

            with col3:
                st.markdown("<hr style='border: 2px solid #ccc;'/>", unsafe_allow_html=True)
                st.markdown(style_metric_box("#42A5F5", "black").format("1º Envio", primeiro_envio), unsafe_allow_html=True)

            with col4:
                st.markdown("<hr style='border: 2px solid #ccc;'/>", unsafe_allow_html=True)
                st.markdown(style_metric_box("#FFEB3B", "black").format("Reenvios", reenvio), unsafe_allow_html=True)

            # [Seção anterior do código]

            # Título da seção "Informação Técnica" com cor neutra para visibilidade em ambos os temas
            st.markdown("<h3 style='font-size:20px; margin-top:10px; margin-bottom:5px; color:#555555;'>Informação Técnica</h3>", unsafe_allow_html=True)


            # Filtrando o DataFrame para excluir registros com "cancelado" na coluna 'Qual o tipo de envio?'
            df_informacao_tecnica = df_selection[~df_selection['Qual o tipo de envio?'].str.contains('cancelado', na=False, case=False)]

            # Contagem de processos por tipo de "Informação Técnica"
            it_rada = df_informacao_tecnica[df_informacao_tecnica['Informação Técnica'].str.contains('IT - RADA', na=False, case=False)].shape[0]
            it_ipa = df_informacao_tecnica[df_informacao_tecnica['Informação Técnica'].str.contains('IT - IPA', na=False, case=False)].shape[0]
            nao = df_informacao_tecnica[df_informacao_tecnica['Informação Técnica'].str.contains('Não', na=False, case=False)].shape[0]
            it_fiscalizacao = df_informacao_tecnica[df_informacao_tecnica['Informação Técnica'].str.contains('IT - FISCALIZAÇÃO', na=False, case=False)].shape[0]
            it_descumprimento = df_informacao_tecnica[df_informacao_tecnica['Informação Técnica'].str.contains('IT - Descumprimento de Condicionante', na=False, case=False)].shape[0]
            it_outros = df_informacao_tecnica[df_informacao_tecnica['Informação Técnica'].str.contains('IT - Outros', na=False, case=False)].shape[0]

            # Layout: 4 colunas para a "Informação Técnica"
            col_it1, col_it2, col_it3, col_it4 = st.columns(4)

            # Função para estilizar as métricas de "Informação Técnica"
            def style_metric_box_it(box_color, font_color, title, values):
                values_html = "<br>".join([f"{name}: {value}" for name, value in values.items()])
                return f"""
                    <div style="background-color:{box_color}; padding:8px; border-radius:8px; border:1px solid #ccc;">
                        <h4 style="color:{font_color}; text-align:center; font-size:20px;">{title}</h4>
                        <h2 style="color:{font_color}; text-align:center; font-size:18px;">{values_html}</h2>
                    </div>
                """

            # Renderizando as métricas com estilo e valores separados para a coluna 4
            with col_it1:
                st.markdown(style_metric_box_it("#A5D6A7", "black", "Não Contém ou não é Informação Técnica", {"Contagem": nao}), unsafe_allow_html=True)

            with col_it2:
                st.markdown(style_metric_box_it("#FFAB91", "black", "Informação Técnica<br>IT RADA", {"Contagem": it_rada}), unsafe_allow_html=True)

            with col_it3:
                st.markdown(style_metric_box_it("#81D4FA", "black", "Informação Técnica<br>IT IPA", {"Contagem": it_ipa}), unsafe_allow_html=True)

            with col_it4:
                st.markdown(
                    style_metric_box_it(
                        "#FFE082", 
                        "black", 
                        "", 
                        {
                            "IT - Descumprimento": it_descumprimento,
                            "IT - Fiscalização": it_fiscalizacao,                            
                            "IT - Outros": it_outros
                        }
                    ), 
                    unsafe_allow_html=True
                )


### Gráfico de linhas e barras empilhadas para análises temporais


            # Filtrando o DataFrame para excluir os processos cancelados
            df_selection_filtered = df_selection[~df_selection['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)]

            # Espaçador ou linha de separação entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Gráfico de linhas e barras empilhadas para análises temporais
            st.subheader('Processos ao Longo do Tempo - Envios Totais por Semana')


            # Agrupando os dados por semana e tipo de envio
            df_temporal = df_selection_filtered.groupby(['ANO_envio', 'MÊS_envio', 'SEMANA_envio', 'Qual o tipo de envio?']).size().reset_index(name='Quantidade de Processos')

            # Filtra apenas os envios de prioridades e primeiros envios
            df_prioridade_primeiro_envio = df_temporal[
                df_temporal['Qual o tipo de envio?'].str.contains('Prioridades|1º envio', case=False, na=False)
            ]

            # Soma a quantidade de processos de prioridade e primeiro envio por semana
            df_total_prioridade_primeiro_envio = df_prioridade_primeiro_envio.groupby(['ANO_envio', 'SEMANA_envio'])['Quantidade de Processos'].sum().reset_index(name='Total de Prioridade e 1º Envio')

            # Gráfico de barras empilhadas para os tipos de envio
            fig_temporal = go.Figure()

            # Adicionando as barras empilhadas para cada tipo de envio
            for tipo_envio in df_temporal['Qual o tipo de envio?'].unique():
                df_tipo = df_temporal[df_temporal['Qual o tipo de envio?'] == tipo_envio]
                fig_temporal.add_trace(go.Bar(
                    x=df_tipo['SEMANA_envio'],
                    y=df_tipo['Quantidade de Processos'],
                    name=tipo_envio,
                    text=df_tipo['Quantidade de Processos'],  # Adicionando os valores
                    textposition='auto',  # Exibindo os valores nas barras
                    marker_color=px.colors.sequential.Tealgrn[df_temporal['Qual o tipo de envio?'].unique().tolist().index(tipo_envio)],
                    textfont=dict(size=12)  # Aumentando o tamanho do texto dos rótulos de barra
                ))

            # Adicionando a linha com a quantidade total de processos por semana
            df_total_semana = df_selection_filtered.groupby(['ANO_envio', 'SEMANA_envio']).size().reset_index(name='Quantidade Total de Processos')
            fig_temporal.add_trace(go.Scatter(
                x=df_total_semana['SEMANA_envio'],
                y=df_total_semana['Quantidade Total de Processos'],
                mode='lines+markers+text',  # Adicionando valores à linha
                name='Total de Processos',
                line=dict(color='green', width=3),
                marker=dict(size=10),
                text=df_total_semana['Quantidade Total de Processos'],  # Adicionando os valores
                textposition='top center',  # Posicionando os valores
                textfont=dict(size=14, color='green'),  # Tamanho e cor para destaque dos rótulos da linha de total
            ))

            # Adicionando a linha com o total de prioridades e primeiro envio por semana
            fig_temporal.add_trace(go.Scatter(
                x=df_total_prioridade_primeiro_envio['SEMANA_envio'],
                y=df_total_prioridade_primeiro_envio['Total de Prioridade e 1º Envio'],
                mode='lines+markers+text',
                name='Total de Prioridade e 1º Envio',
                line=dict(color='orange', width=3, dash='dash'),
                marker=dict(size=10),
                text=df_total_prioridade_primeiro_envio['Total de Prioridade e 1º Envio'],
                textposition='top center',
                textfont=dict(size=14, color='orange'),  # Tamanho e cor para destaque dos rótulos da linha de prioridade e 1º envio
            ))

            # Ajustando o layout
            fig_temporal.update_layout(
                barmode='stack',  # Para empilhar as barras
                xaxis_title='Semana',  # Renomeando o eixo X para "Semana"
                yaxis_title='Quantidade de Processos',
                legend_title='Tipo de Envio',
                template='plotly_white',
                width=1000,  # Aumentando a largura do gráfico
                height=600,  # Mantendo uma altura adequada
                xaxis=dict(
                    tickmode='linear',  # Forçando o modo de exibição de ticks em sequência
                    tick0=1,            # Primeiro tick começa em 1 (para semana 1)
                    dtick=1,            # Mostra apenas números inteiros no eixo X
                ),
                legend=dict(
                    orientation="h",  # Configurando a legenda em orientação horizontal
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,  # Posicionando a legenda no canto superior direito
                    font=dict(size=10),  # Diminuindo o tamanho da fonte da legenda
                    title_font=dict(size=10),  # Diminuindo o tamanho da fonte do título da legenda
                )
            )

            # Exibindo o gráfico
            st.plotly_chart(fig_temporal, use_container_width=True)

            # Separador e título para a seção de gráficos mensais
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            st.subheader("Distribuição Mensal dos Tipos de Envio")

            # Filtrar o DataFrame para excluir processos cancelados
            df_selection_filtered = df_selection[~df_selection['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)]

            # Renomear valores em 'Qual o tipo de envio?' para consistência
            df_selection_filtered['Qual o tipo de envio?'] = df_selection_filtered['Qual o tipo de envio?'].replace({
                '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)': '1º Envio',
                'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)': 'Prioridades',
                'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)': 'Reenvios'
            })

            # Definir cores para cada tipo de envio
            cor_1_envio = '#2ca02c'  # Verde
            cor_prioridades = '#ffdd57'  # Amarelo
            cor_reenvios = '#1f77b4'  # Azul

            def grafico_mensal_por_tipo(df, tipo_envio, cor_barras):
                # Filtrar dados para o tipo de envio específico
                df_tipo = df[df['Qual o tipo de envio?'] == tipo_envio]
                df_mes_tipo = df_tipo.groupby(['ANO_envio', 'MÊS_envio']).size().reset_index(name='Quantidade')

                # Verificar se o dataframe está vazio após o filtro
                if df_mes_tipo.empty:
                    # Exibir mensagem informando que não há dados para o filtro selecionado
                    st.warning(f"Não há dados disponíveis para o tipo de envio '{tipo_envio}' no filtro selecionado.")
                    return go.Figure()  # Retornar um gráfico vazio

                # Ordenar dados cronologicamente por mês e ano
                df_mes_tipo['Período_Mes'] = pd.to_datetime(df_mes_tipo['ANO_envio'].astype(str) + '-' + df_mes_tipo['MÊS_envio'].astype(str) + '-01')
                df_mes_tipo = df_mes_tipo.sort_values('Período_Mes')

                # Linha de tendência: transformar o 'Período_Mes' para valores numéricos e calcular a regressão linear
                X = np.arange(len(df_mes_tipo)).reshape(-1, 1)  # Valores X para regressão
                y = df_mes_tipo['Quantidade']  # Valores y

                # Regressão linear para obter a linha de tendência
                model = LinearRegression()
                model.fit(X, y)
                y_trend = model.predict(X)

                # Criar o gráfico de barras com linha de tendência
                fig = go.Figure()

                # Adicionar barras para distribuição mensal
                fig.add_trace(go.Bar(
                    x=df_mes_tipo['Período_Mes'].dt.strftime('%b %Y'),
                    y=df_mes_tipo['Quantidade'],
                    name=tipo_envio,
                    marker_color=cor_barras,
                    text=df_mes_tipo['Quantidade'],
                    textposition='auto'
                ))

                # Adicionar linha de tendência
                fig.add_trace(go.Scatter(
                    x=df_mes_tipo['Período_Mes'].dt.strftime('%b %Y'),
                    y=y_trend,
                    mode='lines',
                    name='Tendência',
                    line=dict(color='red', width=2, dash='dash')
                ))

                # Ajuste do layout para exibir em ordem cronológica e em português
                fig.update_layout(
                    title=f"Distribuição Mensal - {tipo_envio}",
                    xaxis_title='Mês-Ano',
                    yaxis_title='Quantidade de Processos',
                    xaxis=dict(
                        tickmode='array',
                        tickvals=df_mes_tipo['Período_Mes'],
                        ticktext=df_mes_tipo['Período_Mes'].dt.strftime('%b %Y')
                    ),
                    width=400,
                    height=400,
                    template='plotly_white',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.5,
                        xanchor="center",
                        x=0.5
                    )
                )
                return fig


            # Exibir os gráficos em três colunas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(grafico_mensal_por_tipo(df_selection_filtered, '1º Envio', cor_1_envio), use_container_width=True)
            with col2:
                st.plotly_chart(grafico_mensal_por_tipo(df_selection_filtered, 'Prioridades', cor_prioridades), use_container_width=True)
            with col3:
                st.plotly_chart(grafico_mensal_por_tipo(df_selection_filtered, 'Reenvios', cor_reenvios), use_container_width=True)

            def grafico_mensal_area_por_tipo(df, tipo_envio, cor_area):
                # Filtrar dados para o tipo de envio específico
                df_tipo = df[df['Qual o tipo de envio?'] == tipo_envio]
                df_mes_tipo = df_tipo.groupby(['ANO_envio', 'MÊS_envio']).size().reset_index(name='Quantidade')

                # Verificar se o dataframe está vazio após o filtro
                if df_mes_tipo.empty:
                    # Exibir mensagem informando que não há dados para o filtro selecionado
                    st.warning(f"Não há dados disponíveis para o tipo de envio '{tipo_envio}' no filtro selecionado.")
                    return go.Figure()  # Retornar um gráfico vazio

                # Ordenar dados cronologicamente por mês e ano
                df_mes_tipo['Período_Mes'] = pd.to_datetime(df_mes_tipo['ANO_envio'].astype(str) + '-' + df_mes_tipo['MÊS_envio'].astype(str) + '-01')
                df_mes_tipo = df_mes_tipo.sort_values('Período_Mes')

                # Verificar se temos pelo menos um ponto de dados para realizar a regressão linear
                if len(df_mes_tipo) < 2:
                    st.warning("Não há dados suficientes para calcular a linha de tendência.")
                    y_trend = df_mes_tipo['Quantidade']  # Linha de tendência será igual aos dados originais (sem regressão)
                else:
                    # Linha de tendência: transformar o 'Período_Mes' para valores numéricos e calcular a regressão linear
                    X = np.arange(len(df_mes_tipo)).reshape(-1, 1)  # Valores X para regressão
                    y = df_mes_tipo['Quantidade']  # Valores y

                    # Regressão linear para obter a linha de tendência
                    model = LinearRegression()
                    model.fit(X, y)
                    y_trend = model.predict(X)

                # Criar o gráfico de área com linha de tendência
                fig = go.Figure()

                # Adicionar área para distribuição mensal
                fig.add_trace(go.Scatter(
                    x=df_mes_tipo['Período_Mes'].dt.strftime('%b %Y'),
                    y=df_mes_tipo['Quantidade'],
                    fill='tozeroy',
                    name=tipo_envio,
                    mode='lines',
                    line=dict(color=cor_area),
                ))

                # Adicionar linha de tendência, se houver mais de um ponto de dados
                if len(df_mes_tipo) >= 2:
                    fig.add_trace(go.Scatter(
                        x=df_mes_tipo['Período_Mes'].dt.strftime('%b %Y'),
                        y=y_trend,
                        mode='lines',
                        name='Tendência',
                        line=dict(color='red', width=2, dash='dash')
                    ))

                # Ajuste do layout para exibir em ordem cronológica e em português
                fig.update_layout(
                    title=f"Distribuição Mensal - {tipo_envio}",
                    xaxis_title='Mês-Ano',
                    yaxis_title='Quantidade de Processos',
                    xaxis=dict(
                        tickmode='array',
                        tickvals=df_mes_tipo['Período_Mes'],
                        ticktext=df_mes_tipo['Período_Mes'].dt.strftime('%b %Y')
                    ),
                    width=400,
                    height=400,
                    template='plotly_white',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.5,
                        xanchor="center",
                        x=0.5
                    )
                )
                return fig


            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(grafico_mensal_area_por_tipo(df_selection_filtered, '1º Envio', cor_1_envio), use_container_width=True)
            with col2:
                st.plotly_chart(grafico_mensal_area_por_tipo(df_selection_filtered, 'Prioridades', cor_prioridades), use_container_width=True)
            with col3:
                st.plotly_chart(grafico_mensal_area_por_tipo(df_selection_filtered, 'Reenvios', cor_reenvios), use_container_width=True)




### Tipos de Processo

            # Criar uma nova coluna 'Tipo de Processo' aplicando a função de extração
            # Função para extrair o tipo de processo
            def extrair_tipo_processo(numero_processo):
                # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                if match:
                    sigla = match.group(1)
                    # Verifica se a sigla extraída é uma das especificadas
                    if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                        return sigla
                return 'Outros'

            # Aplicando a função para criar a coluna 'Tipo de Processo'
            df_selection['Tipo de Processo'] = df_selection['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].apply(extrair_tipo_processo)

            import locale

            # Tentar configurar a localidade para português
            try:
                locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            except locale.Error:
                # Se a localidade não estiver disponível, usar o padrão do sistema
                locale.setlocale(locale.LC_TIME, '')

            # Separador visual entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            # Título descritivo
            st.subheader("Distribuição Hierárquica dos Tipos de Processo ao Longo do Tempo - Comparativo Mensal e Semanal - 1° Envio e Prioridades")

            # Função aprimorada para extrair o tipo de processo
            # Função para extrair o tipo de processo
            def extrair_tipo_processo(numero_processo):
                # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                if match:
                    sigla = match.group(1)
                    # Verifica se a sigla extraída é uma das especificadas
                    if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                        return sigla
                return 'Outros'

            # Aplicando a função ao DataFrame
            df_selection['Tipo de Processo'] = df_selection['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].apply(extrair_tipo_processo)

            # Filtrando para excluir "cancelados"
            df_selection_filtrado = df_selection[~df_selection['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)]

            # Filtro para "Tipo de Processo" dentro da seção de gráficos
            tipos_de_processo_unicos = sorted(df_selection['Tipo de Processo'].unique().tolist())
            tipo_processo_selecionado = st.multiselect("Selecione o Tipo de Processo", ["Todos"] + tipos_de_processo_unicos, default="Todos")

            # Filtrar o DataFrame com base na seleção do filtro
            if "Todos" in tipo_processo_selecionado or not tipo_processo_selecionado:
                df_selection_filtrado = df_selection_filtrado
            else:
                df_selection_filtrado = df_selection_filtrado[df_selection_filtrado['Tipo de Processo'].isin(tipo_processo_selecionado)]

            # Agrupando os dados para o gráfico de barras empilhadas mensal
            df_bar_mes = df_selection_filtrado.groupby(['ANO_envio', 'MÊS_envio', 'Tipo de Processo']).size().reset_index(name='Quantidade')
            df_bar_mes['Período_Mes'] = pd.to_datetime(df_bar_mes['ANO_envio'].astype(str) + '-' + df_bar_mes['MÊS_envio'].astype(str) + '-01')
            df_bar_mes['Período_Mes'] = df_bar_mes['Período_Mes'].dt.strftime('%b %Y')  # Formata para "Mês abreviado Ano"

            # Ordenando os tipos de processo para decrescente e ajustando as cores de verde escuro a amarelo claro
            tipo_processo_order = df_bar_mes.groupby('Tipo de Processo')['Quantidade'].sum().sort_values(ascending=False).index.tolist()
            df_bar_mes['Tipo de Processo'] = pd.Categorical(df_bar_mes['Tipo de Processo'], categories=tipo_processo_order, ordered=True)

            # Configuração de cores específicas em tons de verde
            color_sequence = [
                '#4db6ac',   
                '#1bfa4c',                
                '#b4e055',                         
                '#dae63e',
                '#5999d9',  
                '#009688', 
                '#7fa128',
                '#46c29f',  
                '#46b6c2',
                '#9fc4e0',
                '#dbdb21',
                '#0c593d'   
                
            ]

            # Ordenando os dados cronologicamente e por quantidade de tipo de processo
            df_bar_mes['Período_Mes'] = pd.to_datetime(df_bar_mes['ANO_envio'].astype(str) + '-' + df_bar_mes['MÊS_envio'].astype(str) + '-01')
            df_bar_mes = df_bar_mes.sort_values(['Período_Mes', 'Quantidade'], ascending=[True, False])  # Ordem cronológica e por quantidade

            # Ordenando os tipos de processo para que o maior fique na base
            tipo_processo_order = df_bar_mes.groupby('Tipo de Processo')['Quantidade'].sum().sort_values(ascending=False).index.tolist()
            df_bar_mes['Tipo de Processo'] = pd.Categorical(df_bar_mes['Tipo de Processo'], categories=tipo_processo_order, ordered=True)

            # Total mensal para adicionar ao gráfico
            df_bar_mes_total = df_bar_mes.groupby('Período_Mes')['Quantidade'].sum().reset_index(name='Total_Quantidade')
            df_bar_mes['Período_Mes_str'] = df_bar_mes['Período_Mes'].dt.strftime('%b %Y')

            # Configuração do gráfico de barras empilhadas mensal
            fig_bar_mes = px.bar(
                df_bar_mes,
                x='Período_Mes',  # Utiliza a coluna de data para garantir a ordem
                y='Quantidade',
                color='Tipo de Processo',
                title="Distribuição dos Tipos de Processo por Mês",
                labels={'Quantidade': 'Quantidade de Processos', 'Período_Mes': 'Período (Mês-Ano)'},
                color_discrete_sequence=color_sequence
            )

            # Adicionando o total geral acima das colunas no gráfico mensal
            fig_bar_mes.add_trace(go.Scatter(
                x=df_bar_mes_total['Período_Mes'],
                y=df_bar_mes_total['Total_Quantidade'],
                mode='text',
                text=df_bar_mes_total['Total_Quantidade'],
                textposition='top center',
                showlegend=False
            ))

            # Ajuste do layout para exibir 'Período_Mes_str' como rótulos e manter a ordem cronológica
            fig_bar_mes.update_layout(
                xaxis_title='Período (Mês-Ano)',
                yaxis_title='Quantidade de Processos',
                xaxis=dict(
                    tickvals=df_bar_mes['Período_Mes'],
                    ticktext=df_bar_mes['Período_Mes_str']
                ),
                barmode='stack',
                width=800,
                height=500,
                template='plotly_white',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.5,
                    xanchor="center",
                    x=0.5
                )
            )




            # Aplicar o filtro para o gráfico semanal
            df_selection_filtrado = df_selection_filtrado if "Todos" in tipo_processo_selecionado or not tipo_processo_selecionado else df_selection_filtrado[df_selection_filtrado['Tipo de Processo'].isin(tipo_processo_selecionado)]

            # Agrupamento semanal para o gráfico de áreas
            df_area_semana = df_selection_filtrado.groupby(['ANO_envio', 'SEMANA_envio', 'Tipo de Processo']).size().reset_index(name='Quantidade')
            df_area_semana['Data_Semana'] = pd.to_datetime(df_area_semana['ANO_envio'].astype(str) + df_area_semana['SEMANA_envio'].astype(str) + '1', format='%Y%U%w')

            # Criar coluna 'Período_Semana' para exibição no formato desejado
            df_area_semana['Período_Semana'] = (
                'S' + df_area_semana['SEMANA_envio'].astype(str) + '-' +
                df_area_semana['Data_Semana'].dt.strftime('%b-%y').str.upper()
            )

            # Agrupar quantidades totais semanais, ordenadas por 'Data_Semana'
            df_area_semana_total = df_area_semana.groupby(['Data_Semana', 'Período_Semana'])['Quantidade'].sum().reset_index(name='Total_Quantidade')

            # Configurar o gráfico semanal de áreas, usando 'Data_Semana' para ordenação e exibindo 'Período_Semana' como texto de hover
            fig_area_semana = px.area(
                df_area_semana.sort_values('Data_Semana'),  # Garantir que os dados estejam ordenados por 'Data_Semana'
                x='Data_Semana',  # Usar 'Data_Semana' como eixo x para ordenar diretamente pela data
                y='Quantidade',
                color='Tipo de Processo',
                title="Evolução dos Tipos de Processo por Semana",
                labels={'Quantidade': 'Quantidade de Processos', 'Data_Semana': 'Data da Semana'},
                color_discrete_sequence=color_sequence
            )

            # Adicionar valores totais semanais como rótulos de texto
            fig_area_semana.add_trace(go.Scatter(
                x=df_area_semana_total['Data_Semana'],
                y=df_area_semana_total['Total_Quantidade'],
                mode='text',
                text=df_area_semana_total['Total_Quantidade'],
                textposition='top center',
                showlegend=False
            ))

            # Ajuste do layout para o gráfico semanal
            fig_area_semana.update_layout(
                xaxis_title='Semana',
                yaxis_title='Quantidade de Processos',
                width=1000,
                height=500,
                template='plotly_white',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.5,
                    xanchor="center",
                    x=0.5
                ),
                xaxis=dict(
                    tickformat='%d-%b-%y',  # Exibir data no formato "dia-mês-ano"
                    tickvals=df_area_semana['Data_Semana'].unique()  # Usar datas semanais únicas como valores do eixo x
                )
            )

            # Exibindo os gráficos lado a lado
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.plotly_chart(fig_area_semana, use_container_width=True)
            with col2:
                st.plotly_chart(fig_bar_mes, use_container_width=True)

          


### Seção dos Porcessos Enviados e Quantitativo de por tipo de empreendimento

            # Exibindo resultados
            st.subheader('Processos Enviados e Quantitativo por Tipo de Empreendimento')

            # Ajustando a lógica de filtro para permitir "TODOS"
            if "TODOS" in ano:
                anos_filtrados = df_selection['ANO_envio'].unique()
            else:
                anos_filtrados = ano

            if "TODOS" in mes:
                meses_filtrados = df_selection['MÊS_envio'].unique()
            else:
                meses_filtrados = mes

            # Aplicando filtros de ano e mês ao DataFrame filtrado
            df_filtered = df_selection[
                ~df_selection['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)
                & (df_selection['Qual o tipo de envio?'].str.contains('1º envio|Prioridades', case=False))
                & (df_selection['ANO_envio'].isin(anos_filtrados))  # Filtro de ano ajustado
                & (df_selection['MÊS_envio'].isin(meses_filtrados))  # Filtro de mês ajustado
            ].copy()

            df_filtered['Quantidade de empreendimentos'] = pd.to_numeric(df_filtered['Quantidade de empreendimentos'], errors='coerce').fillna(0)


            # Selecionando os 7 principais tipos de empreendimento para destacar no gráfico
            top_7_empreendimentos = df_filtered['Tipo de empreendimento'].value_counts().nlargest(7).index.tolist()
            df_filtered['Tipo de empreendimento_agrupado'] = df_filtered['Tipo de empreendimento'].apply(
                lambda x: x if x in top_7_empreendimentos else 'Outros'
            )

            # Soma da Quantidade de Empreendimentos por Tipo dentro dos filtros aplicados
            soma_quantidade_empreendimentos = df_filtered.groupby('Tipo de empreendimento_agrupado')['Quantidade de empreendimentos'].sum()

            # Contagem de processos por tipo de empreendimento para "1º Envio + Prioridades"
            contagem_primeiro_envio = df_filtered['Tipo de empreendimento_agrupado'].value_counts()

            # Criando a legenda personalizada para o primeiro gráfico
            legenda_customizada_envio = contagem_primeiro_envio.reset_index()
            legenda_customizada_envio.columns = ['Tipo de empreendimento_agrupado', 'Quantidade']
            # Convertendo para numérico para evitar erros
            legenda_customizada_envio['Quantidade'] = pd.to_numeric(legenda_customizada_envio['Quantidade'], errors='coerce')
            legenda_customizada_envio['Percentual'] = (legenda_customizada_envio['Quantidade'] / legenda_customizada_envio['Quantidade'].sum()) * 100
            legenda_customizada_envio['Legenda'] = legenda_customizada_envio.apply(
                lambda row: f"{row['Tipo de empreendimento_agrupado']} ({row['Quantidade']}, {row['Percentual']:.2f}%)", axis=1
            )

            # Gráfico de Pizza para "Processos por Tipo de Empreendimento - 1º Envio + Prioridades"
            fig_primeiro_envio = px.pie(
                contagem_primeiro_envio, 
                names=contagem_primeiro_envio.index, 
                values=contagem_primeiro_envio.values, 
                title='Processos por Tipo de Empreendimento - 1º Envio + Prioridades',
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4
            )
            fig_primeiro_envio.update_traces(
                textinfo='label',  # Exibe a quantidade e a porcentagem
                marker=dict(line=dict(color='#000000', width=2))  # Bordas pretas
            )
            for i, label in enumerate(legenda_customizada_envio['Legenda']):
                fig_primeiro_envio.data[0].labels[i] = label

            # Criando a legenda personalizada para o segundo gráfico
            legenda_customizada_empreendimentos = soma_quantidade_empreendimentos.reset_index()
            legenda_customizada_empreendimentos.columns = ['Tipo de empreendimento_agrupado', 'Quantidade']
            # Convertendo para numérico para evitar erros
            legenda_customizada_empreendimentos['Quantidade'] = pd.to_numeric(legenda_customizada_empreendimentos['Quantidade'], errors='coerce')
            legenda_customizada_empreendimentos['Percentual'] = (legenda_customizada_empreendimentos['Quantidade'] / legenda_customizada_empreendimentos['Quantidade'].sum()) * 100
            legenda_customizada_empreendimentos['Legenda'] = legenda_customizada_empreendimentos.apply(
                lambda row: f"{row['Tipo de empreendimento_agrupado']} ({row['Quantidade']}, {row['Percentual']:.2f}%)", axis=1
            )

            # Gráfico de Pizza para "Soma da Quantidade de Empreendimentos"
            fig_quantidade_empreendimentos = px.pie(
                soma_quantidade_empreendimentos,
                names=soma_quantidade_empreendimentos.index,
                values=soma_quantidade_empreendimentos.values,
                title='Quantidade de Empreendimentos - 1º Envio + Prioridades',
                color_discrete_sequence=px.colors.qualitative.Pastel,
                hole=0.4
            )
            fig_quantidade_empreendimentos.update_traces(
                textinfo='label',  # Exibe a quantidade e a porcentagem
                marker=dict(line=dict(color='#000000', width=2))  # Bordas pretas
            )
            for i, label in enumerate(legenda_customizada_empreendimentos['Legenda']):
                fig_quantidade_empreendimentos.data[0].labels[i] = label

            # Configurando os gráficos com a legenda abaixo dos gráficos e distribuindo os itens em duas colunas, com maior foco nos gráficos
            fig_primeiro_envio.update_layout(
                height=700,  # Aumenta a altura do gráfico para dar mais destaque
                width=500,   # Ajuste de largura
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,           # Posiciona a legenda mais abaixo para reduzir a área que ocupa
                    xanchor="center",
                    x=0.5,
                    traceorder="normal",
                    tracegroupgap=5,
                    itemwidth=100     # Ajuste para quebrar a legenda em menos colunas, deixando mais espaço para o gráfico
                )
            )

            fig_quantidade_empreendimentos.update_layout(
                height=700,
                width=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,
                    xanchor="center",
                    x=0.5,
                    traceorder="normal",
                    tracegroupgap=5,
                    itemwidth=100
                )
            )

            # Configurando os gráficos lado a lado, com o layout ajustado para dar mais espaço aos gráficos de pizza
            col1, col2 = st.columns([1, 1])  # Ajusta as colunas para que ambos os gráficos ocupem mais espaço
            with col1:
                st.plotly_chart(fig_primeiro_envio, use_container_width=False)  # Define False para usar a largura configurada
            with col2:
                st.plotly_chart(fig_quantidade_empreendimentos, use_container_width=False)
 


### Seção dos Processos Enviados e Quantitativo por Tipo de Empreendimento - Se IT

            # Separador visual entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)            

            # Título descritivo
            st.subheader("Processos Enviados e Quantitativo por Tipo de Empreendimento - Classificação por Informação Técnica (IT) - 1° Envio e Prioridades")

            # Aplicando o filtro "TODOS" para a segunda seção da mesma forma
            df_it_summary = df_filtered.groupby(['Informação Técnica', 'Tipo de empreendimento_agrupado']).agg(
                Quantidade_Processos=('Tipo de empreendimento_agrupado', 'count'),
                Quantidade_Empreendimentos=('Quantidade de empreendimentos', 'sum')
            ).reset_index()

            # Função para criar o treemap para uma categoria específica de Informação Técnica
            def criar_treemap_por_informacao_tecnica(informacao_tecnica, dados):
                # Filtrando os dados para a informação técnica específica
                dados_treemap = dados[dados['Informação Técnica'].str.strip().str.upper() == informacao_tecnica.strip().upper()].groupby(
                    ['Informação Técnica', 'Tipo de empreendimento_agrupado']
                ).agg(
                    Quantidade_Processos=('Tipo de empreendimento_agrupado', 'count'),
                    Quantidade_Empreendimentos=('Quantidade de empreendimentos', 'sum')
                ).reset_index()

                # Verifica se existem dados para a categoria
                if dados_treemap.empty:
                    st.warning(f"Não há dados para a categoria '{informacao_tecnica}'")
                    return None

                # Criando o gráfico de Treemap
                fig_treemap = px.treemap(
                    dados_treemap,
                    path=['Informação Técnica', 'Tipo de empreendimento_agrupado'],
                    values='Quantidade_Processos',
                    color='Quantidade_Processos',
                    title=f'Treemap - {informacao_tecnica}',
                    color_continuous_scale=px.colors.sequential.Tealgrn,
                    labels={
                        'Quantidade_Processos': 'Quantidade de Processos',
                        'Quantidade_Empreendimentos': 'Quantidade de Empreendimentos'
                    }
                )

                # Exibindo os rótulos de Quantidade de Empreendimentos corretamente
                fig_treemap.update_traces(
                    texttemplate="<b>%{label}</b><br>Processos: %{value}<br>Empreendimentos: %{customdata[0]}",
                    customdata=dados_treemap[['Quantidade_Empreendimentos']].values
                )

                # Removendo a barra de cores para um visual mais limpo
                fig_treemap.update_coloraxes(showscale=False)

                return fig_treemap

            # Exibindo os gráficos para "NÃO" e "IT - RADA" lado a lado
            col1, col2 = st.columns(2)
            with col1:
                fig_nao = criar_treemap_por_informacao_tecnica('NÃO', df_filtered)
                if fig_nao:
                    st.plotly_chart(fig_nao, use_container_width=True)
            with col2:
                fig_rada = criar_treemap_por_informacao_tecnica('IT - RADA', df_filtered)
                if fig_rada:
                    st.plotly_chart(fig_rada, use_container_width=True)

            # Exibindo os gráficos para as outras categorias em colunas menores
            col3, col4, col5, col6 = st.columns(4)
            with col3:
                fig_descumprimento = criar_treemap_por_informacao_tecnica('IT - Descumprimento de Condicionante', df_filtered)
                if fig_descumprimento:
                    st.plotly_chart(fig_descumprimento, use_container_width=True)
            with col4:
                fig_ipa = criar_treemap_por_informacao_tecnica('IT - IPA', df_filtered)
                if fig_ipa:
                    st.plotly_chart(fig_ipa, use_container_width=True)
            with col5:
                fig_outros = criar_treemap_por_informacao_tecnica('IT - Outros', df_filtered)
                if fig_outros:
                    st.plotly_chart(fig_outros, use_container_width=True)
            with col6:
                fig_fiscalizacao = criar_treemap_por_informacao_tecnica('IT - FISCALIZAÇÃO', df_filtered)
                if fig_fiscalizacao:
                    st.plotly_chart(fig_fiscalizacao, use_container_width=True)



            
### Gráfico de barras para empresa

            # Separador visual entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            st.subheader("Processos Enviados por Empresa - 1° Envio e Prioridades")

            # Filtro para "Informação Técnica" dentro da seção de gráficos
            info_tec_unicos = df_selection['Informação Técnica'].unique().tolist()
            info_tec_unicos.sort()  # Ordenar alfabeticamente
            info_tec_unicos.insert(0, "Todos")  # Adicionar "Todos" como a primeira opção

            # Permitir seleção múltipla e deixar "Todos" selecionado como padrão
            info_tec_selecionado = st.multiselect("Selecione a Informação Técnica", info_tec_unicos, default="Todos")

            # Aplicar o filtro selecionado, verificando se "Todos" está na seleção
            if "Todos" in info_tec_selecionado:
                df_selection_filtrado = df_selection
            else:
                df_selection_filtrado = df_selection[df_selection['Informação Técnica'].isin(info_tec_selecionado)]

            # Filtrando para excluir processos com 'cancelado' no tipo de envio e incluir apenas "1º Envio" e "Prioridades"
            df_filtered_empresa = df_selection_filtrado[
                (~df_selection_filtrado['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)) &
                (df_selection_filtrado['Qual o tipo de envio?'].str.contains('1º envio|Prioridades', case=False, na=False))
            ]

            # Definindo o DataFrame df_temporal para análises temporais
            df_temporal = df_filtered_empresa.groupby(['ANO_envio', 'MÊS_envio', 'SEMANA_envio']).size().reset_index(name='Quantidade de Processos')
            df_company_filtered = df_filtered_empresa[df_filtered_empresa['SEMANA_envio'].isin(df_temporal['SEMANA_envio'])]

            # Contagem de processos por empresa
            contagem_empresa = df_company_filtered['Empresa'].value_counts()

            # Criando o gráfico de barras com tons de verde
            fig_company = go.Figure()
            fig_company.add_trace(
                go.Bar(
                    y=contagem_empresa.index, 
                    x=contagem_empresa.values, 
                    orientation='h',
                    marker=dict(color=px.colors.sequential.Darkmint[2:8]), 
                    text=contagem_empresa.values,
                    textposition='inside', 
                    texttemplate='%{text:.2s}',
                )
            )

            fig_company.update_layout(
                title='Distribuição de Processos por Empresa',
                xaxis_title='Quantidade de Processos',
                yaxis_title='Empresa',
                title_font_size=18,
                xaxis=dict(
                    tickvals=contagem_empresa.values,
                    ticktext=[f'{value}' for value in contagem_empresa.values],
                    color='black'
                ),
                yaxis=dict(
                    tickvals=contagem_empresa.index,
                    ticktext=[f'{label}' for label in contagem_empresa.index],
                    color='black',
                    autorange='reversed'
                ),
                height=500,
                width=600,
                plot_bgcolor='rgba(255, 255, 255, 0)',
                paper_bgcolor='rgba(255, 255, 255, 0)',
                font=dict(color='black'),
                margin=dict(l=150, r=20, t=80, b=50)
            )

            st.plotly_chart(fig_company, use_container_width=True)

            ### Gráficos Sunburst

            # Verificar se 'Tipo de empreendimento' existe no DataFrame, e exibir uma mensagem de erro caso contrário
            if 'Tipo de empreendimento' not in df_selection.columns:
                st.error("A coluna 'Tipo de empreendimento' não está presente no conjunto de dados.")
            else:
                # Filtrar para incluir apenas 1º Envio e Prioridades, excluindo cancelados
                df_filtered_sunburst = df_selection_filtrado[
                    (~df_selection_filtrado['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)) &
                    (df_selection_filtrado['Qual o tipo de envio?'].str.contains('1º envio|Prioridades', case=False, na=False))
                ]

                # Colunas relevantes para o gráfico sunburst de Empresa e Tipo de Processo
                df_sunburst_proc = df_filtered_sunburst[['Empresa', 'Tipo de Processo']].copy()
                df_sunburst_proc['Quantidade'] = df_sunburst_proc.groupby(['Empresa', 'Tipo de Processo'])['Tipo de Processo'].transform('count')
                df_sunburst_proc = df_sunburst_proc.drop_duplicates()

                fig_sunburst_proc = px.sunburst(
                    df_sunburst_proc,
                    path=['Empresa', 'Tipo de Processo'],
                    values='Quantidade',
                    title="Distribuição de Processos por Empresa e Tipo de Processo",
                    color='Quantidade',
                    color_continuous_scale=px.colors.sequential.Teal,
                    labels={'Quantidade': 'Quantidade de Processos'},
                )

                fig_sunburst_proc.update_layout(
                    coloraxis_colorbar=dict(
                        title="Quantidade",
                        tickvals=[10, 50, 100, 150, 200],
                    ),
                    margin=dict(t=40, l=0, r=0, b=0),
                )

                # Colunas relevantes para o gráfico sunburst de Empresa e Tipo de Empreendimento
                df_sunburst_emp = df_filtered_sunburst[['Empresa', 'Tipo de empreendimento']].copy()
                df_sunburst_emp['Quantidade'] = df_sunburst_emp.groupby(['Empresa', 'Tipo de empreendimento'])['Tipo de empreendimento'].transform('count')
                df_sunburst_emp = df_sunburst_emp.drop_duplicates()

                fig_sunburst_emp = px.sunburst(
                    df_sunburst_emp,
                    path=['Empresa', 'Tipo de empreendimento'],
                    values='Quantidade',
                    title="Distribuição de Processos por Empresa e Tipo de Empreendimento",
                    color='Quantidade',
                    color_continuous_scale=px.colors.sequential.Teal,
                    labels={'Quantidade': 'Quantidade de Processos'},
                )

                fig_sunburst_emp.update_layout(
                    coloraxis_colorbar=dict(
                        title="Quantidade",
                        tickvals=[10, 50, 100, 150, 200],
                    ),
                    margin=dict(t=40, l=0, r=0, b=0),
                )

                # Exibir os gráficos lado a lado no Streamlit
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(fig_sunburst_proc, use_container_width=True)
                with col2:
                    st.plotly_chart(fig_sunburst_emp, use_container_width=True)

            
### Tabelas de dados

            ### Tabelas de dados

            # Função para aplicar o estilo condicional
            def aplicar_estilos(df):
                styles = []
                for index, row in df.iterrows():
                    if pd.isna(row['Revisado em']):
                        styles.append(['background-color: #B0B0B0; color: #000000'] * len(row))  # Cor para "Não Revisados"
                    elif "Prioridades" in str(row["Qual o tipo de envio?"]):
                        styles.append(['background-color: #2E8B57; color: #FFFFFF'] * len(row))  # Cor para "Prioridade"
                    else:
                        styles.append([''] * len(row))
                return pd.DataFrame(styles, index=df.index, columns=df.columns)

            # Separador visual entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Título descritivo centralizado com tamanho maior
            st.markdown("<h2 style='text-align: center; font-size: 28px;'>Tabelas de Dados</h2>", unsafe_allow_html=True)

            # Legenda explicativa à esquerda
            st.markdown("<h4>Legenda de Cores</h4>", unsafe_allow_html=True)
            st.markdown(
                """
                <div style="display: flex; align-items: flex-start; flex-direction: column;">
                    <div style="display: flex; align-items: center; margin-top: 8px;">
                        <div style="width: 20px; height: 20px; background-color: #B0B0B0; margin-right: 10px; border-radius: 3px; border: 1px solid #444;"></div>
                        <span>Não Revisados</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-top: 8px;">
                        <div style="width: 20px; height: 20px; background-color: #2E8B57; margin-right: 10px; border-radius: 3px; border: 1px solid #444;"></div>
                        <span>Prioridade</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


            # Tabela Geral
            st.markdown("<h3 style='text-align: center;'>Tabela Geral</h3>", unsafe_allow_html=True)
            st.write("Visualização de dados filtrados:")
            styled_df_full = df_selection.style.apply(aplicar_estilos, axis=None)
            st.dataframe(styled_df_full, use_container_width=True)

            # Crie sua Tabela
            st.markdown("<h3 style='text-align: center;'>Crie sua Tabela", unsafe_allow_html=True)
            st.markdown("OBS: Manter sempre: 'Qual o tipo de envio?' e 'Revisado em'")

            # Expansor para visualização personalizada dos dados
            with st.expander("VISUALIZAÇÃO GERAL DOS DADOS"):
                showData = st.multiselect(
                    'Filtrar: ',
                    df_selection.columns,
                    default=[
                        "Codigo_Processo", "Carimbo de data/hora",
                        "Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)",
                        "Analista (você)", "Qual o tipo de envio?", "Informação Técnica", "Empresa", "Tipo de empreendimento", "Quantidade de empreendimentos",
                        "Revisado por", "Revisado em", "MÊS", "ANO", "Status do processo pós revisão"
                    ]
                )

                styled_df = df_selection[showData].style.apply(aplicar_estilos, axis=None)
                st.dataframe(styled_df, use_container_width=True)


        else:
            st.error("O arquivo está vazio ou ocorreu um erro ao processar os dados.")
    else:
        st.warning("""
            Carregue a base no Sidebar ao lado.

            ⬅️   Por favor, faça o upload do arquivo CSV - Revisão de Pareceres (respostas) 
            disponível em: https://docs.google.com/spreadsheets/d/18juQmpGe86MRr4uXTxDiJC1wAPQXXqJs1SgMoFpFC2g/edit?gid=1572677783#gid=1572677783.
            """)


### *** Seção Visão - Analista ***

# Função para criar a visão analista com filtro "Informação Técnica"
def visao_analista():
    
    if uploaded_file is not None:
        # Carrega os dados do arquivo
        df = load_data(uploaded_file)

        st.markdown(
            "<h1 style='text-align: center; color: #98FF98; font-size: 42px; font-weight: bold; text-decoration: underline;'>Visão - Revisão</h1>",
            unsafe_allow_html=True
        )

        # Espaçador ou linha de separação entre seções
        st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # Filtrar o DataFrame para remover processos "cancelados" e "cancelar"
        df = df[~df['Qual o tipo de envio?'].str.contains(r'\bcancel(ad|ar)\b', case=False, na=False)]

        # Continuar com o código de filtragem e processamento apenas com os dados válidos
        if df is not None and not df.empty:
            # Convertendo valores de ano, mês e semana, tratando valores ausentes
            df['MÊS_envio'] = df['Carimbo de data/hora'].dt.month.fillna(0).astype(int)
            df['ANO_envio'] = df['Carimbo de data/hora'].dt.year.fillna(0).astype(int)
            df['SEMANA_envio'] = df['Carimbo de data/hora'].dt.isocalendar().week.fillna(0).astype(int)

            # Filtrando anos e meses disponíveis como inteiros, removendo o valor 0
            anos_disponiveis_envio = [ano for ano in sorted(df['ANO_envio'].unique(), reverse=True) if ano != 0]
            meses_disponiveis_envio = [mes for mes in sorted(df['MÊS_envio'].unique(), reverse=True) if mes != 0]

            # Adicionando a opção "TODOS" para ano e mês
            anos_disponiveis_envio.insert(0, "TODOS")
            meses_disponiveis_envio.insert(0, "TODOS")

            # Gerando semanas disponíveis com intervalos de datas, sem semanas/anos inválidos
            semanas_disponiveis_envio = formatar_semanas(df)

            # Incluindo a opção "TODOS" para semanas
            semanas_disponiveis_envio.insert(0, "TODOS")

            # Obter o mês e ano atual
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year

            # Seleção padrão inicial
            ano_default = [ano_atual] if ano_atual in anos_disponiveis_envio else ["TODOS"]
            mes_default = [mes_atual] if mes_atual in meses_disponiveis_envio else ["TODOS"]
            semana_default = ["TODOS"]

            # Sidebar para seleção de ano, mês e semana
            ano = st.sidebar.multiselect("SELECIONE O ANO", options=anos_disponiveis_envio, default=ano_default)
            mes = st.sidebar.multiselect("SELECIONE O MÊS", options=meses_disponiveis_envio, default=mes_default)
            semana = st.sidebar.multiselect(
                "SELECIONE A SEMANA", 
                options=semanas_disponiveis_envio, 
                default=semana_default, 
                format_func=lambda x: x[2] if isinstance(x, tuple) else x
            )

            # Filtro "Informação Técnica" com opção "TODOS" e excluindo NaN
            informacao_tecnica_opcoes = [opcao for opcao in sorted(df['Informação Técnica'].dropna().unique().tolist())]
            informacao_tecnica_opcoes.insert(0, "TODOS")  # Adiciona "TODOS" no início da lista
            informacao_tecnica_selecionada = st.sidebar.multiselect(
                "Filtrar por Informação Técnica", 
                options=informacao_tecnica_opcoes, 
                default=["TODOS"]
            )

            # Aplicando os filtros ao DataFrame
            df_selection_filtered = df.copy()  # Cria uma cópia para aplicar os filtros

            # Filtra por ano se "TODOS" não estiver selecionado
            if "TODOS" not in ano:
                df_selection_filtered = df_selection_filtered[df_selection_filtered['ANO_envio'].isin(ano)]

            # Filtra por mês se "TODOS" não estiver selecionado
            if "TODOS" not in mes:
                df_selection_filtered = df_selection_filtered[df_selection_filtered['MÊS_envio'].isin(mes)]

            # Filtra por semana se "TODOS" não estiver selecionado
            if "TODOS" not in semana:
                semanas_selecionadas = [s[1] if isinstance(s, tuple) else s for s in semana]  # Extrai apenas o número da semana
                df_selection_filtered = df_selection_filtered[df_selection_filtered['SEMANA_envio'].isin(semanas_selecionadas)]

            # Filtra por "Informação Técnica" se "TODOS" não estiver selecionado
            if "TODOS" not in informacao_tecnica_selecionada:
                df_selection_filtered = df_selection_filtered[df_selection_filtered['Informação Técnica'].isin(informacao_tecnica_selecionada)]

            # Agora utilize `df_selection_filtered` para todos os gráficos e tabelas subsequentes.


            
            # Destaque para o filtro de analista com verde e alinhamento à esquerda
            st.markdown(
                """
                <div style="background-color: #E6F4EA; padding: 10px; border-radius: 8px; border: 2px solid #3CB371; margin-bottom: 20px; text-align: left;">
                    <h3 style="color: #2E8B57; font-weight: bold; margin: 0;">Selecione o Analista</h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Filtro de analista com borda e fundo mais destacados em tons de verde
            analistas_disponiveis = df_selection_filtered['Analista (você)'].dropna().unique().tolist()
            analista_selecionado = st.selectbox(
                label="",
                options=["TODOS"] + sorted(analistas_disponiveis),
            )


            # Aplicando filtro de analista com base na coluna "Analista (você)"
            if analista_selecionado != "TODOS":
                df_selection_filtered = df_selection_filtered[df_selection_filtered['Analista (você)'] == analista_selecionado]
                
                # Verificar se o analista selecionado também aparece como revisor na coluna "Revisado por"
                if analista_selecionado in df['Revisado por'].values:
                    st.warning(f"Nota: {analista_selecionado} também aparece como 'Revisor' na coluna 'Revisado por'.")
                else:
                    st.info(f"Nota: {analista_selecionado} atua apenas como responsável pelo processo e não como revisor.")

           


            # Verifica se o filtro de analista está marcado como "TODOS"
            if analista_selecionado == "TODOS":
                # Separador visual para a nova seção de gráficos
                st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

                # Título centralizado
                st.markdown(
                    "<h2 style='text-align: center; color: #3CB371;'>Envios Semanais por Analista - Todos os Analistas</h2>",
                    unsafe_allow_html=True
                )

                # Filtrando o DataFrame para excluir processos cancelados e usar apenas "Carimbo de data/hora"
                df_selection_filtered = df_selection_filtered[
                    (~df_selection_filtered['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)) &
                    (df_selection_filtered['Carimbo de data/hora'].notna())
                ]

                
                # Configuração de cores com tons de verde, azul, amarelo e laranja, usando transparência
                color_sequence = [
                    'rgba(0, 191, 255, 0.8)',    # Azul profundo
                    'rgba(0, 0, 205, 0.8)',      # Azul marinho
                    'rgba(0, 255, 255, 0.8)',    # Ciano
                    'rgba(32, 178, 170, 0.8)',   # Turquesa
                    'rgba(127, 255, 212, 0.8)',  # Verde água claro
                    'rgba(0, 250, 154, 0.8)',    # Verde primavera
                    'rgba(60, 179, 113, 0.8)',   # Verde mar
                    'rgba(127, 255, 0, 0.8)',    # Verde limão
                    'rgba(255, 255, 0, 0.8)',    # Amarelo
                    'rgba(255, 0, 0, 0.8)',      # Vermelho
                    'rgba(250, 128, 114, 0.8)',  # Coral claro
                    'rgba(128, 0, 128, 0.8)',    # Roxo
                    'rgba(245, 222, 179, 0.8)',  # Pêssego claro
                    'rgba(25, 25, 112, 0.8)',    # Azul escuro
                    'rgba(0, 128, 128, 0.8)',    # Verde-azulado
                    'rgba(47, 79, 79, 0.8)',     # Verde escuro
                    'rgba(75, 0, 130, 0.8)'      # Índigo
                ]
                analistas_unicos = sorted(df_selection_filtered['Analista (você)'].unique())
                color_map = {analista: color_sequence[i % len(color_sequence)] for i, analista in enumerate(analistas_unicos)}

                # Calcula os totais de envios por analista para exibir na legenda
                analistas_unicos = sorted(df_selection_filtered['Analista (você)'].unique())
                totais_por_analista = df_selection_filtered['Analista (você)'].value_counts().to_dict()
                color_map = {analista: color_sequence[i % len(color_sequence)] for i, analista in enumerate(analistas_unicos)}

                # Função para gerar gráfico empilhado de envios por semana para cada tipo de envio
                def gerar_grafico_envio(tipo_envio, titulo, cor_linha="darkgoldenrod"):
                    df_tipo_envio = df_selection_filtered[
                        df_selection_filtered['Qual o tipo de envio?'].str.contains(tipo_envio, case=False, na=False)
                    ]
                    
                    # Agrupa por semana e analista
                    df_analista_semana = df_tipo_envio.groupby(
                        [df_tipo_envio['Carimbo de data/hora'].dt.isocalendar().week, 'Analista (você)']
                    ).size().unstack(fill_value=0)

                    analistas_ordenados = df_analista_semana.sum().sort_values(ascending=False).index
                    df_analista_semana = df_analista_semana[analistas_ordenados]

                    # Criando gráfico empilhado
                    fig = go.Figure()

                    for i, analista in enumerate(df_analista_semana.columns):
                        total_analista = totais_por_analista.get(analista, 0)
                        fig.add_trace(go.Bar(
                            x=df_analista_semana.index,
                            y=df_analista_semana[analista],
                            name=f"{analista} ({total_analista})",
                            marker_color=color_map[analista],
                            text=df_analista_semana[analista],
                            textposition='none'  # Remove os valores nas barras, mantendo apenas na linha
                        ))

                    # Adiciona linha de total semanal
                    df_total_semanal = df_analista_semana.sum(axis=1)
                    fig.add_trace(go.Scatter(
                        x=df_total_semanal.index,
                        y=df_total_semanal,
                        mode='lines+markers+text',
                        name='Total Semanal',
                        line=dict(color=cor_linha, width=3, dash='dash'),
                        text=df_total_semanal.round(2),
                        textposition='top center',
                        textfont=dict(size=14, color=cor_linha),
                    ))

                    # Configura layout
                    fig.update_layout(
                        barmode='stack',
                        title=titulo,
                        xaxis_title='Semana',
                        yaxis_title='Quantidade de Processos',
                        template='plotly_white',
                        width=1000,
                        height=600,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.4,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=10)
                        )
                    )

                    return fig

                # Gráfico mensal de envios por analista com totais na legenda
                def gerar_grafico_mensal_por_analista():
                    df_analista_mes = df_selection_filtered.groupby(
                        [df_selection_filtered['Carimbo de data/hora'].dt.month, 'Analista (você)']
                    ).size().unstack(fill_value=0)

                    analistas_ordenados = df_analista_mes.sum().sort_values(ascending=False).index
                    df_analista_mes = df_analista_mes[analistas_ordenados]

                    fig = go.Figure()
                    for analista in df_analista_mes.columns:
                        total_analista = totais_por_analista.get(analista, 0)
                        fig.add_trace(go.Bar(
                            y=df_analista_mes.index,
                            x=df_analista_mes[analista],
                            name=f"{analista} ({total_analista})",
                            orientation='h',
                            marker_color=color_map[analista],
                            text=df_analista_mes[analista],
                            textposition='none'  # Remove os valores nas barras
                        ))

                    fig.update_layout(
                        barmode='stack',
                        title="Envios Mensais por Analista - Todos os Analistas",
                        xaxis_title='Quantidade de Processos',
                        yaxis_title='Mês',
                        template='plotly_white',
                        height=500,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-1.1,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=10)
                        )
                    )

                    return fig

                # Exibindo gráficos de envios semanais e mensais lado a lado
                col_main, col_side = st.columns([3, 1.5])
                with col_main:
                    st.plotly_chart(gerar_grafico_envio("Prioridades|1º envio|Reenvio após correções", "Total de Envios por Semana - Todos os Analistas"), use_container_width=True)
                with col_side:
                    st.plotly_chart(gerar_grafico_mensal_por_analista(), use_container_width=True)
                
                # Gráficos de rosca para distribuições totais
                def gerar_grafico_donut(tipo_envio, titulo):
                    df_tipo_envio = df_selection_filtered[
                        df_selection_filtered['Qual o tipo de envio?'].str.contains(tipo_envio, case=False, na=False)
                    ]
                    total_por_analista = df_tipo_envio['Analista (você)'].value_counts().reset_index()
                    total_por_analista.columns = ['Analista', 'Quantidade']

                    fig_donut = px.pie(
                        total_por_analista,
                        values='Quantidade',
                        names='Analista',
                        title=titulo,
                        hole=0.4,  # Criando gráfico de rosca
                        color='Analista',
                        color_discrete_map=color_map
                    )

                    fig_donut.update_traces(
                        textinfo='label+percent+value',
                        textfont_size=12
                    )
                    fig_donut.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.8,  # Posicionando a legenda mais abaixo
                            xanchor="center",
                            x=0.5,
                            font=dict(size=10)
                        )
                    )
                    return fig_donut

                # Exibindo gráficos de rosca para envios por analista
                st.markdown("<h3 style='text-align: center; color: #3CB371;'>Distribuição Total de Envios por Analista</h3>", unsafe_allow_html=True)
                col_pie1, col_pie2, col_pie3 = st.columns(3)
                with col_pie1:
                    st.plotly_chart(gerar_grafico_donut("Prioridades", "Envios de Prioridades por Analista"), use_container_width=True)
                with col_pie2:
                    st.plotly_chart(gerar_grafico_donut("1º envio", "1º Envios por Analista"), use_container_width=True)
                with col_pie3:
                    st.plotly_chart(gerar_grafico_donut("Reenvio após correções", "Reenvios por Analista"), use_container_width=True)






                # Agrupa os dados por analista e tipo de envio para contar a quantidade
                df_analista_envio = df_selection_filtered.groupby(['Analista (você)', 'Qual o tipo de envio?']).size().reset_index(name='Quantidade')

                # Calcula o total de envios para cada tipo de envio
                df_total_envio_por_tipo = df_selection_filtered.groupby('Qual o tipo de envio?').size().reset_index(name='Total por Tipo de Envio')

                # Junta as tabelas para adicionar o total de cada tipo de envio na tabela por analista
                df_analista_envio = df_analista_envio.merge(df_total_envio_por_tipo, on='Qual o tipo de envio?', how='left')

                # Calcula a proporção de cada analista para cada tipo de envio
                df_analista_envio['Proporção (%)'] = (df_analista_envio['Quantidade'] / df_analista_envio['Total por Tipo de Envio']) * 100

             



                # Função para criar um gráfico de velocímetro para um tipo de envio específico com escala de cores baseada no tipo de envio
                def gerar_grafico_velocidade(tipo_envio, proporcao, total):
                    # Define cores com base no tipo de envio
                    if tipo_envio == '1º Envio':
                        cor_barra = "darkgreen"
                        cor_steps = [{'range': [0, 25], 'color': "#c7e9b4"},
                                    {'range': [25, 50], 'color': "#7fcdbb"},
                                    {'range': [50, 75], 'color': "#41b6c4"},
                                    {'range': [75, 100], 'color': "#1d91c0"}]
                    elif tipo_envio == 'Reenvios':
                        cor_barra = "darkblue"
                        cor_steps = [{'range': [0, 25], 'color': "#c6dbef"},
                                    {'range': [25, 50], 'color': "#9ecae1"},
                                    {'range': [50, 75], 'color': "#6baed6"},
                                    {'range': [75, 100], 'color': "#3182bd"}]
                    elif tipo_envio == 'Prioridades':
                        cor_barra = "darkorange"
                        cor_steps = [{'range': [0, 25], 'color': "#fff7b2"},  # Tons de amarelo claro
                                    {'range': [25, 50], 'color': "#fee08b"},
                                    {'range': [50, 75], 'color': "#fdae61"},
                                    {'range': [75, 100], 'color': "#f46d43"}]

                    # Configuração do gráfico
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=proporcao,
                        number={'valueformat': ".1f", 'suffix': "%"},
                        title={'text': f"{tipo_envio}<br>Total: {total}", 'font': {'size': 16}, 'align': 'center'},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': cor_barra},
                            'steps': cor_steps
                        }
                    ))

                    # Ajuste de layout para descer o título e corrigir espaços
                    fig.update_layout(
                        margin=dict(t=40, b=10, l=10, r=10),
                        height=200,
                        width=200
                    )
                    return fig


                                



                # Cálculo do total de envios por tipo e média proporcional por tipo de envio
                total_envios_por_tipo = df_analista_envio.groupby('Qual o tipo de envio?')['Quantidade'].sum().reset_index()
                num_analistas = df_analista_envio['Analista (você)'].nunique()

                # Adiciona a coluna da média de envios em valores absolutos (sem porcentagem)
                total_envios_por_tipo['Média de Envios'] = (total_envios_por_tipo['Quantidade'] / num_analistas)

                # Renomeia colunas para melhorar a apresentação
                total_envios_por_tipo = total_envios_por_tipo.rename(columns={
                    'Qual o tipo de envio?': 'Tipo de Envio',
                    'Quantidade': 'Total de Envios'
                })

                # Adiciona o ícone de média à coluna de Média de Envios
                total_envios_por_tipo['Média de Envios'] = total_envios_por_tipo['Média de Envios'].apply(lambda x: f"⭐ {x:.2f}")
                # Função para aplicar estilo condicional específico para as três primeiras linhas
                def aplicar_estilos_personalizados(df):
                    estilos = []
                    for i in range(len(df)):
                        if i == 0:
                            estilos.append(['background-color: #DFF0D8; color: black; font-weight: bold'] * len(df.columns))  # Verde claro para a primeira linha
                        elif i == 1:
                            estilos.append(['background-color: #FFF3CD; color: black; font-weight: bold'] * len(df.columns))  # Amarelo claro para a segunda linha
                        elif i == 2:
                            estilos.append(['background-color: #D0E2FF; color: black; font-weight: bold'] * len(df.columns))  # Azul claro para a terceira linha
                        else:
                            estilos.append([''] * len(df.columns))
                    return pd.DataFrame(estilos, index=df.index, columns=df.columns)

                # Estiliza a tabela para melhorar a legibilidade e visual
                st.markdown("<h3 style='text-align: center; color: #3CB371;'>Resumo de Envios por Tipo</h3>", unsafe_allow_html=True)
                st.write("Esta tabela mostra o total de envios por tipo e a média de envios entre todos os analistas:")

                # Configura estilo para a tabela
                styled_table = total_envios_por_tipo.style\
                    .apply(aplicar_estilos_personalizados, axis=None)\
                    .set_properties(subset=['Tipo de Envio'], **{'font-weight': 'bold'})\
                    .bar(subset=['Total de Envios'], color='#81D4FA', vmin=0, vmax=total_envios_por_tipo['Total de Envios'].max())\
                    .set_table_styles([
                        {'selector': 'thead th', 'props': [('background-color', '#3CB371'), ('color', 'white'), ('font-weight', 'bold'), ('text-align', 'center')]},
                        {'selector': 'tbody td', 'props': [('border', '1px solid #ddd'), ('text-align', 'center')]}
                    ])\
                    .set_caption("Tabela com o total de envios por tipo e a média de envios entre analistas")

                # Exibe a tabela com estilo
                st.dataframe(styled_table, use_container_width=True)



                

                # Ajustando os textos dos tipos de envio no DataFrame
                df_analista_envio['Qual o tipo de envio?'] = df_analista_envio['Qual o tipo de envio?'].replace({
                    '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)': '1º Envio',
                    'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)': 'Prioridades',
                    'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)': 'Reenvios'
                })

                # Título da seção
                st.markdown("<h3 style='text-align: center;'>Gráficos de Velocidade por Analista e Tipo de Envio</h3>", unsafe_allow_html=True)

                # Verifica se o DataFrame 'df_analista_envio' não está vazio
                if not df_analista_envio.empty:
                    # Obter a lista de analistas únicos
                    analistas = df_analista_envio['Analista (você)'].unique()

                    # Define o número de colunas (ajuste conforme necessário)
                    num_colunas = 8
                    colunas = st.columns(num_colunas)  # Cria colunas para exibir os analistas em quadros

                    # Variável para alternar entre as colunas
                    coluna_atual = 0

                    # Loop para cada analista
                    for analista in analistas:
                        with colunas[coluna_atual]:  # Coluna atual para o analista
                            # Cria uma caixa para agrupar os gráficos do analista
                            st.markdown(f"<div style='border: 1px solid #3CB371; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
                            
                            # Título do analista com cor verde
                            st.markdown(f"<h4 style='text-align: center; color: #3CB371;'>{analista}</h4>", unsafe_allow_html=True)

                            # Filtra dados para o analista
                            df_analista = df_analista_envio[df_analista_envio['Analista (você)'] == analista]

                            # Função para exibir o gráfico com valores padrão se os dados estiverem vazios
                            def exibir_grafico(tipo_envio):
                                df_tipo_envio = df_analista[df_analista['Qual o tipo de envio?'] == tipo_envio]
                                if not df_tipo_envio.empty:
                                    proporcao = df_tipo_envio['Proporção (%)'].values[0]
                                    total = df_tipo_envio['Quantidade'].values[0]
                                    st.plotly_chart(gerar_grafico_velocidade(tipo_envio, proporcao, total), use_container_width=True)
                                else:
                                    st.plotly_chart(gerar_grafico_velocidade(tipo_envio, 0, 0), use_container_width=True)

                            # Gráfico de 1º Envio
                            exibir_grafico('1º Envio')

                            # Gráfico de Prioridades
                            exibir_grafico('Prioridades')

                            # Gráfico de Reenvios
                            exibir_grafico('Reenvios')

                            # Fecha a caixa do analista
                            st.markdown("</div>", unsafe_allow_html=True)

                        # Alterna para a próxima coluna ou volta à primeira
                        coluna_atual = (coluna_atual + 1) % num_colunas
                    else:
                        st.write("Dados de envios por analista não disponíveis.")



            # Espaçador ou linha de separação entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Gráfico de linhas e barras empilhadas para análises temporais do analista
            st.subheader(f'Processos por Semana - {analista_selecionado}')

            # Agrupando os dados por semana e tipo de envio
            df_temporal_analista = df_selection_filtered.groupby(['ANO_envio', 'SEMANA_envio', 'Qual o tipo de envio?']).size().reset_index(name='Quantidade de Processos')

            # Filtra apenas os envios de prioridades e primeiros envios
            df_prioridade_primeiro_envio_analista = df_temporal_analista[
                df_temporal_analista['Qual o tipo de envio?'].str.contains('Prioridades|1º envio', case=False, na=False)
            ]

            # Soma a quantidade de processos de prioridade e primeiro envio por semana
            df_total_prioridade_primeiro_envio_analista = df_prioridade_primeiro_envio_analista.groupby(['ANO_envio', 'SEMANA_envio'])['Quantidade de Processos'].sum().reset_index(name='Total de Prioridade e 1º Envio')

            # Gráfico de barras empilhadas para os tipos de envio
            fig_temporal_analista = go.Figure()

            # Define the order of types for stacking: "1º Envio" at the base, "Prioridades" in the middle, and "Reenvio" on top
            stack_order = ["1º envio (Primeira vez que o Parecer está sendo enviado para revisão)", "Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)", "Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)"]

            # Adicionando as barras empilhadas para cada tipo de envio na ordem especificada
            for tipo_envio in stack_order:
                df_tipo = df_temporal_analista[df_temporal_analista['Qual o tipo de envio?'] == tipo_envio]
                fig_temporal_analista.add_trace(go.Bar(
                    x=df_tipo['SEMANA_envio'],
                    y=df_tipo['Quantidade de Processos'],
                    name=tipo_envio,
                    text=df_tipo['Quantidade de Processos'],  # Adicionando os valores
                    textposition='auto',  # Exibindo os valores nas barras
                    marker_color=px.colors.sequential.Tealgrn[stack_order.index(tipo_envio)],  # Aplicando cor com base na ordem
                    textfont=dict(size=12)  # Aumentando o tamanho do texto dos rótulos de barra
                ))

            # Adicionando a linha com a quantidade total de processos por semana para o analista
            df_total_semana_analista = df_selection_filtered.groupby(['ANO_envio', 'SEMANA_envio']).size().reset_index(name='Quantidade Total de Processos')
            fig_temporal_analista.add_trace(go.Scatter(
                x=df_total_semana_analista['SEMANA_envio'],
                y=df_total_semana_analista['Quantidade Total de Processos'],
                mode='lines+markers+text',  # Adicionando valores à linha
                name='Total de Processos',
                line=dict(color='green', width=3),
                marker=dict(size=10),
                text=df_total_semana_analista['Quantidade Total de Processos'],  # Adicionando os valores
                textposition='top center',  # Posicionando os valores
                textfont=dict(size=14, color='green'),  # Tamanho e cor para destaque dos rótulos da linha de total
            ))

            # Adicionando a linha com o total de prioridades e primeiro envio por semana para o analista
            fig_temporal_analista.add_trace(go.Scatter(
                x=df_total_prioridade_primeiro_envio_analista['SEMANA_envio'],
                y=df_total_prioridade_primeiro_envio_analista['Total de Prioridade e 1º Envio'],
                mode='lines+markers+text',
                name='Total de Prioridade e 1º Envio',
                line=dict(color='orange', width=3, dash='dash'),
                marker=dict(size=10),
                text=df_total_prioridade_primeiro_envio_analista['Total de Prioridade e 1º Envio'],
                textposition='top center',
                textfont=dict(size=14, color='orange'),  # Tamanho e cor para destaque dos rótulos da linha de prioridade e 1º envio
            ))

            # Ajustando o layout
            fig_temporal_analista.update_layout(
                barmode='stack',  # Para empilhar as barras
                xaxis_title='Semana',  # Renomeando o eixo X para "Semana"
                yaxis_title='Quantidade de Processos',
                legend_title='Tipo de Envio',
                template='plotly_white',
                width=1000,  # Aumentando a largura do gráfico
                height=600,  # Mantendo uma altura adequada
                xaxis=dict(
                    tickmode='linear',  # Forçando o modo de exibição de ticks em sequência
                    tick0=1,            # Primeiro tick começa em 1 (para semana 1)
                    dtick=1,            # Mostra apenas números inteiros no eixo X
                ),
                legend=dict(
                    orientation="h",  # Configurando a legenda em orientação horizontal
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,  # Posicionando a legenda no canto superior direito
                    font=dict(size=10),  # Diminuindo o tamanho da fonte da legenda
                    title_font=dict(size=10),  # Diminuindo o tamanho da fonte do título da legenda
                )
            )
                                    
                      
            # Exibe o gráfico de barras empilhadas para tipos de envio por semana
            st.plotly_chart(fig_temporal_analista, use_container_width=True)


###Grafico Radar e Barras laterais
          

            # Espaçador ou linha de separação entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Gráfico de linhas e barras empilhadas para análises temporais do analista
            st.subheader(f'Processos Enviados - {analista_selecionado}')

            # Função aprimorada para extrair o tipo de processo de acordo com diferentes padrões
            # Função para extrair o tipo de processo
            def extrair_tipo_processo(numero_processo):
                # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                if match:
                    sigla = match.group(1)
                    # Verifica se a sigla extraída é uma das especificadas
                    if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                        return sigla
                return 'Outros'

            # Criando a coluna 'Tipo de Processo' aplicando a função de extração ao 'Número do Processo'
            if 'Tipo de Processo' not in df_selection_filtered.columns:
                df_selection_filtered['Tipo de Processo'] = df_selection_filtered[
                    'Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'
                ].apply(extrair_tipo_processo)

            # Remove as entradas que contêm "cancelado" em "Qual o tipo de envio?"
            df_selection_filtered = df_selection_filtered[~df_selection_filtered['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)]


            # Simplifica os textos dos tipos de envio
            df_selection_filtered['Qual o tipo de envio?'] = df_selection_filtered['Qual o tipo de envio?'].replace({
                '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)': '1º Envio',
                'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)': 'Prioridades',
                'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)': 'Reenvio'
            })

            # Filtros interativos para "Tipo de Envio" e "Informação Técnica" com múltipla seleção
            tipo_envio_opcoes = df_selection_filtered['Qual o tipo de envio?'].unique().tolist()
            informacao_tecnica_opcoes = df_selection_filtered['Informação Técnica'].unique().tolist()

            tipo_envio_selecionado = st.multiselect("Filtrar por Tipo de Envio", options=tipo_envio_opcoes, default=tipo_envio_opcoes)
            informacao_tecnica_selecionada = st.multiselect("Filtrar por Informação Técnica", options=informacao_tecnica_opcoes, default=informacao_tecnica_opcoes)

            # Aplicando os filtros selecionados ao DataFrame
            df_filtrado = df_selection_filtered[
                (df_selection_filtered['Qual o tipo de envio?'].isin(tipo_envio_selecionado)) &
                (df_selection_filtered['Informação Técnica'].isin(informacao_tecnica_selecionada))
            ]

            # Função para criar gráfico de barras empilhadas horizontal com total e filtros
            def gerar_grafico_barras_tipo_envio(df):
                # Agrupando os dados
                df_envios_processos = df.groupby(['Qual o tipo de envio?', 'Tipo de Processo']).size().reset_index(name='Quantidade')
                total_por_tipo_envio = df_envios_processos.groupby('Qual o tipo de envio?')['Quantidade'].sum()

                # Atualizando o nome da coluna 'Qual o tipo de envio?' para incluir o total no título de cada tipo
                df_envios_processos['Qual o tipo de envio?'] = df_envios_processos['Qual o tipo de envio?'].apply(
                    lambda envio: f"{envio} ({total_por_tipo_envio[envio]})"
                )

                # Criando o gráfico de barras empilhadas com tons de verde
                fig_barras = px.bar(
                    df_envios_processos,
                    x='Quantidade',
                    y='Qual o tipo de envio?',
                    color='Tipo de Processo',
                    orientation='h',
                    title="Quantidade Total por Tipo de Envio<br>e Tipo de Processo",  # Quebra de linha inserida
                    text='Quantidade',
                    color_discrete_sequence=['#98FB98', '#90EE90', '#8FBC8F', '#66CDAA', '#7FFFD4', '#00FA9A']  # Tons de verde claros
                )

                fig_barras.update_layout(
                    showlegend=True,
                    template='plotly_white',
                    height=400,
                    xaxis_title='Quantidade de Processos',
                    yaxis_title='Tipo de Envio',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.8,  # Movendo a legenda mais abaixo do gráfico
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10),
                        itemsizing="constant"  # Alinhando os itens lado a lado
                    )
                )

                # Invertendo o eixo X para que as barras cresçam para a esquerda
                fig_barras.update_xaxes(autorange="reversed")

                return fig_barras

            # Função para criar gráfico de radar com a legenda ajustada para a parte superior
            def gerar_grafico_radar_completo(df):
                df_prioridades = df[df['Qual o tipo de envio?'] == 'Prioridades']
                df_primeiro_envio = df[df['Qual o tipo de envio?'] == '1º Envio']
                df_reenvios = df[df['Qual o tipo de envio?'] == 'Reenvio']

                radar_data_prioridades = df_prioridades.groupby('Tipo de Processo').size().reindex(df['Tipo de Processo'].unique(), fill_value=0)
                radar_data_primeiro_envio = df_primeiro_envio.groupby('Tipo de Processo').size().reindex(df['Tipo de Processo'].unique(), fill_value=0)
                radar_data_reenvios = df_reenvios.groupby('Tipo de Processo').size().reindex(df['Tipo de Processo'].unique(), fill_value=0)

                radar_data_prioridades_normalized = radar_data_prioridades / radar_data_prioridades.max()
                radar_data_primeiro_envio_normalized = radar_data_primeiro_envio / radar_data_primeiro_envio.max()
                radar_data_reenvios_normalized = radar_data_reenvios / radar_data_reenvios.max()

                fig_radar = go.Figure()

                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_data_prioridades_normalized,
                    theta=radar_data_prioridades.index,
                    fill='toself',
                    opacity=0.5,
                    name='Prioridades',
                    line=dict(color='rgba(0, 100, 0, 0.9)', width=2),  # Verde escuro mais opaco e linha mais grossa
                ))

                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_data_primeiro_envio_normalized,
                    theta=radar_data_primeiro_envio.index,
                    fill='toself',
                    opacity=0.5,
                    name='1º Envio',
                    line=dict(color='rgba(34, 139, 34, 0.9)', width=2),  # Verde floresta escuro
                ))

                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_data_reenvios_normalized,
                    theta=radar_data_reenvios.index,
                    fill='toself',
                    opacity=0.5,
                    name='Reenvio',
                    line=dict(color='rgba(85, 107, 47, 0.9)', width=2),  # Verde oliva escuro
                ))

                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1])
                    ),
                    showlegend=True,
                    title="Radar - Distribuição por Tipo de Processo e Tipo de Envio",
                    template='plotly_white',
                    height=600,
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.05,  # Movendo a legenda para a parte superior
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10)
                    )
                )

                return fig_radar

            # Exibindo os gráficos lado a lado
            col_radar, col_barras = st.columns([2, 1])
            with col_radar:
                st.plotly_chart(gerar_grafico_radar_completo(df_filtrado), use_container_width=True)
            with col_barras:
                st.plotly_chart(gerar_grafico_barras_tipo_envio(df_filtrado), use_container_width=True)


## Gráfico Funil

            
            # Dados para o primeiro gráfico de funil com "Tipo de Processo"
            df_funnel_processo = df_selection_filtered.groupby(['Tipo de Processo', 'Informação Técnica']).size().reset_index(name='Quantidade')
            df_funnel_processo = df_funnel_processo.sort_values(by='Quantidade', ascending=False)

            # Dados para o segundo gráfico de funil com "Tipo de Envio"
            df_funnel_envio = df_selection_filtered.groupby(['Qual o tipo de envio?', 'Informação Técnica']).size().reset_index(name='Quantidade')
            df_funnel_envio = df_funnel_envio.sort_values(by='Quantidade', ascending=False)

            # Paleta de cores em tons claros de verde, amarelo, azul e laranja
            color_sequence = [
                '#98FB98', '#FFD700', '#ADD8E6', '#FFA07A', 
                '#66CDAA', '#FFFACD', '#87CEFA', '#FFDAB9'
            ]

            # Primeiro gráfico de funil: por "Tipo de Processo"
            fig_funnel_processo = go.Figure()


            # Calcula o total para cada categoria de "Informação Técnica" no gráfico de "Tipo de Processo"
            totais_processo = df_funnel_processo.groupby('Informação Técnica')['Quantidade'].sum().to_dict()

            for i, info_tec in enumerate(df_funnel_processo['Informação Técnica'].unique()):
                
                total = totais_processo[info_tec]  # Obtém o total para a categoria
  
                df_info = df_funnel_processo[df_funnel_processo['Informação Técnica'] == info_tec]
                fig_funnel_processo.add_trace(go.Funnel(
                    y=df_info['Tipo de Processo'],
                    x=df_info['Quantidade'],
                    name=f"{info_tec} ({total})",  # Adiciona o total ao nome na legenda
                    textinfo="value+percent total",
                    marker=dict(color=color_sequence[i % len(color_sequence)])
                ))

            fig_funnel_processo.update_layout(
                title="Funil de Processos por Tipo de Processo e Informação Técnica",
                yaxis_title="Tipo de Processo",
                xaxis_title="Quantidade de Processos",
                legend=dict(
                    title="Informação Técnica",
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                funnelmode='stack',
                template="plotly_white"
            )

            
            # Adicionando o total na legenda do segundo gráfico de funil (por Tipo de Envio)
            fig_funnel_envio = go.Figure()

            # Calcula o total para cada categoria de "Informação Técnica" no gráfico de "Tipo de Envio"
            totais_envio = df_funnel_envio.groupby('Informação Técnica')['Quantidade'].sum().to_dict()

            for i, info_tec in enumerate(df_funnel_envio['Informação Técnica'].unique()):
                total = totais_envio[info_tec]  # Obtém o total para a categoria
                df_info = df_funnel_envio[df_funnel_envio['Informação Técnica'] == info_tec]
                
                fig_funnel_envio.add_trace(go.Funnel(
                    y=df_info['Qual o tipo de envio?'],
                    x=df_info['Quantidade'],
                    name=f"{info_tec} ({total})",  # Adiciona o total ao nome na legenda
                    textinfo="value+percent total",
                    marker=dict(color=color_sequence[i % len(color_sequence)])
                ))

            fig_funnel_envio.update_layout(
                title="Funil de Processos por Tipo de Envio e Informação Técnica",
                yaxis_title="Tipo de Envio",
                xaxis_title="Quantidade de Processos",
                legend=dict(
                    title="Informação Técnica",
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                funnelmode='stack',
                template="plotly_white"
            )

            # Exibindo os gráficos lado a lado
            col_funnel_1, col_funnel_2 = st.columns(2)
            with col_funnel_1:
                st.plotly_chart(fig_funnel_processo, use_container_width=True)
            with col_funnel_2:
                st.plotly_chart(fig_funnel_envio, use_container_width=True)


# Gráfico de Distribuição por Tipo de Envio
            
            # Agrupando os dados para preparar o gráfico
            df_bolhas = df_filtrado.groupby(['Qual o tipo de envio?', 'Tipo de Processo']).size().reset_index(name='Quantidade')

            # Criando o gráfico de dispersão com bolhas
            fig = px.scatter(
                df_bolhas,
                x="Tipo de Processo",           # Eixo X (substituído por 'Tipo de Processo')
                y="Qual o tipo de envio?",       # Eixo Y (substituído por 'Qual o tipo de envio?')
                size="Quantidade",               # Tamanho das bolhas baseado em 'Quantidade'
                color="Qual o tipo de envio?",   # Cor das bolhas baseada em 'Qual o tipo de envio?'
                hover_name="Tipo de Processo",   # Nome ao passar o cursor (substituído por 'Tipo de Processo')
                size_max=60                      # Tamanho máximo das bolhas
            )

            # Configurando o layout e cores
            fig.update_layout(
                title="Distribuição de Quantidade por Tipo de Envio e Tipo de Processo",
                template="plotly_white",  # Tema Plotly branco para contraste com tons de verde, azul e amarelo
                xaxis_title="Tipo de Processo",
                yaxis_title="Tipo de Envio",
                height=600,
            )

            # Exibindo o gráfico com o tema do Streamlit e o tema nativo do Plotly em abas
            tab1, tab2 = st.tabs(["Streamlit theme (default)", "Plotly native theme"])
            with tab1:
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)
            with tab2:
                st.plotly_chart(fig, theme=None, use_container_width=True)


            # Função para aplicar o estilo condicional
            def aplicar_estilos(df):
                styles = []
                for index, row in df.iterrows():
                    if pd.isna(row['Revisado em']):
                        styles.append(['background-color: #B0B0B0; color: #000000'] * len(row))  # Cor para "Não Revisados"
                    elif "Prioridades" in str(row["Qual o tipo de envio?"]):
                        styles.append(['background-color: #2E8B57; color: #FFFFFF'] * len(row))  # Cor para "Prioridade"
                    else:
                        styles.append([''] * len(row))
                return pd.DataFrame(styles, index=df.index, columns=df.columns)

            # Separador visual entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Título descritivo centralizado com tamanho maior
            st.markdown("<h2 style='text-align: center; font-size: 28px;'>Visualização Geral dos Dados Filtrados</h2>", unsafe_allow_html=True)

            # Legenda explicativa à esquerda
            st.markdown("<h4>Legenda de Cores</h4>", unsafe_allow_html=True)
            st.markdown(
                """
                <div style="display: flex; align-items: flex-start; flex-direction: column;">
                    <div style="display: flex; align-items: center; margin-top: 8px;">
                        <div style="width: 20px; height: 20px; background-color: #B0B0B0; margin-right: 10px; border-radius: 3px; border: 1px solid #444;"></div>
                        <span>Não Revisados</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-top: 8px;">
                        <div style="width: 20px; height: 20px; background-color: #2E8B57; margin-right: 10px; border-radius: 3px; border: 1px solid #444;"></div>
                        <span>Prioridade</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Tabela Geral com Estilos Aplicados
            st.markdown("<h3 style='text-align: center;'>Tabela Geral com Estilos</h3>", unsafe_allow_html=True)
            st.write("Visualização de dados filtrados com estilo condicional:")
            styled_df_full = df_selection_filtered.style.apply(aplicar_estilos, axis=None)

            # Converte a tabela estilizada para HTML e exibe com st.write
            st.write(styled_df_full.to_html(), unsafe_allow_html=True)

            # Expansor para visualização personalizada dos dados
            st.markdown("<h3 style='text-align: center;'>Crie sua Tabela</h3>", unsafe_allow_html=True)
            st.markdown("**OBS:** Manter sempre: 'Qual o tipo de envio?' e 'Revisado em'")

            with st.expander("VISUALIZAÇÃO GERAL DOS DADOS"):
                showData = st.multiselect(
                    'Filtrar: ',
                    df_selection_filtered.columns,
                    default=[
                        "Analista (você)", "Carimbo de data/hora",
                        "Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)", 
                        "Tipo de Processo", "Qual o tipo de envio?",
                        "Tipo de empreendimento", "Quantidade de empreendimentos", "Informação Técnica", "Empresa",
                        "Revisado por", "Revisado em", "MÊS_envio", "ANO_envio", "Status do processo pós revisão"
                    ]
                )
                
                # Aplicação de estilo condicional na tabela filtrada e conversão para HTML
                styled_df = df_selection_filtered[showData].style.apply(aplicar_estilos, axis=None)
                st.write(styled_df.to_html(), unsafe_allow_html=True)


        else:
            st.error("O arquivo está vazio ou ocorreu um erro ao processar os dados.")
    else:
        st.warning("""
            Carregue a base no Sidebar ao lado.

            ⬅️   Por favor, faça o upload do arquivo CSV - Revisão de Pareceres (respostas) 
            disponível em: https://docs.google.com/spreadsheets/d/18juQmpGe86MRr4uXTxDiJC1wAPQXXqJs1SgMoFpFC2g/edit?gid=1572677783#gid=1572677783.
            """)


### *** Seção Visão - Revisão ***

# Função para acompanhar a revisão
def visao_revisao():
    
    if uploaded_file is not None:
        # Carrega os dados do arquivo
        df = load_data(uploaded_file)

        st.markdown(
            "<h1 style='text-align: center; color: #98FF98; font-size: 42px; font-weight: bold; text-decoration: underline;'>Visão - Revisão</h1>",
            unsafe_allow_html=True
        )

        # Espaçador ou linha de separação entre seções
        st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        # Visualização de acompanhamento
        st.subheader('Revisõs Totais Realizadas na Planilha de Revisão do NUPETR')
        # Filtrar o DataFrame para remover processos "cancelados" e "cancelar"

        df = df[~df['Qual o tipo de envio?'].str.contains(r'\bcancel(ad|ar)\b', case=False, na=False)]
         
        if df is not None and not df.empty:
            # Verifica se a coluna 'Revisado em' existe e converte para datetime
            if 'Revisado em' in df.columns:
                df['Revisado em'] = pd.to_datetime(df['Revisado em'], errors='coerce', dayfirst=True)

            # Adiciona a coluna de semana a partir de 'Revisado em'
            df['SEMANA_revisão'] = df['Revisado em'].dt.isocalendar().week.fillna(0).astype(int)

            # Converte colunas "ANO" e "MÊS" para numéricas, ignorando valores não numéricos
            df['ANO'] = pd.to_numeric(df['ANO'], errors='coerce').fillna(0).astype(int)
            df['MÊS'] = pd.to_numeric(df['MÊS'], errors='coerce').fillna(0).astype(int)

            # Filtrando anos e meses disponíveis como inteiros, removendo o valor 0
            anos_disponiveis_revisão = [ano for ano in sorted(df['ANO'].unique(), reverse=True) if ano != 0]
            meses_disponiveis_revisão = [mes for mes in sorted(df['MÊS'].unique(), reverse=True) if mes != 0]

            # Adicionando a opção "TODOS" para ano e mês
            anos_disponiveis_revisão.insert(0, "TODOS")
            meses_disponiveis_revisão.insert(0, "TODOS")

            # Gerando semanas disponíveis com intervalos de datas, sem semanas/anos inválidos
            semanas_disponiveis_revisão = formatar_semanas_revisão(df)
            semanas_disponiveis_revisão.insert(0, "TODOS")

            # Obter o mês e ano atual
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year

            # Seleção padrão inicial
            ano_default_revisão = [ano_atual] if ano_atual in anos_disponiveis_revisão else ["TODOS"]
            mes_default_revisão = [mes_atual] if mes_atual in meses_disponiveis_revisão else ["TODOS"]
            semana_default_revisão = ["TODOS"]

            # Sidebar para seleção de ano, mês e semana
            ano_revisão = st.sidebar.multiselect("SELECIONE O ANO", options=anos_disponiveis_revisão, default=ano_default_revisão)
            mes_revisão = st.sidebar.multiselect("SELECIONE O MÊS", options=meses_disponiveis_revisão, default=mes_default_revisão)
            semana_revisão = st.sidebar.multiselect(
                "SELECIONE A SEMANA",
                options=semanas_disponiveis_revisão,
                default=semana_default_revisão,
                format_func=lambda x: x[2] if isinstance(x, tuple) else x
            )

            # Aplicando os filtros de ano, mês e semana ao DataFrame
            df_selection = df
            if "TODOS" not in ano_revisão:
                df_selection = df_selection[df_selection['ANO'].isin(ano_revisão)]
            if "TODOS" not in mes_revisão:
                df_selection = df_selection[df_selection['MÊS'].isin(mes_revisão)]

            # Verifica se "TODOS" não está selecionado para aplicar o filtro da semana
            if "TODOS" not in semana_revisão:
                semanas_selecionadas_revisão = [s[1] for s in semana_revisão if isinstance(s, tuple)]
                df_selection = df_selection[df_selection['SEMANA_revisão'].isin(semanas_selecionadas_revisão)]

            
            # Contagem de revisões totais e únicas baseadas no 'Codigo_Processo'
            revisoes_totais = df_selection.shape[0]
            # revisoes_totais_unicos = df_selection['Codigo_Processo'].nunique()

            # Contagem de revisões por tipo de envio
            envios_por_tipo = df_selection['Qual o tipo de envio?'].value_counts()

            # Envios de Prioridades
            prioridades_totais = envios_por_tipo.get('Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)', 0)
            # prioridades_unicos = df_selection[df_selection['Qual o tipo de envio?'] == 'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)']['Codigo_Processo'].nunique()

            # Envios de 1º Envio
            primeiro_envio_totais = envios_por_tipo.get('1º envio (Primeira vez que o Parecer está sendo enviado para revisão)', 0)
            # primeiro_envio_unicos = df_selection[df_selection['Qual o tipo de envio?'] == '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)']['Codigo_Processo'].nunique()

            # Envios de Reenvios - Correções
            reenvio_totais = envios_por_tipo.get('Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)', 0)
            # reenvio_unicos = df_selection[df_selection['Qual o tipo de envio?'] == 'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)']['Codigo_Processo'].nunique()

            # Layout: 4 colunas para as contagens
            col1, col2, col3, col4 = st.columns(4)

            def style_metric_box(box_color, font_color):
                return f"""
                    <div style="background-color:{box_color}; padding:10px; border-radius:10px; border:2px solid #ddd;">
                        <h4 style="color:{font_color}; text-align:center;">{{}}</h4>
                        <h2 style="color:{font_color}; text-align:center;">{{}}</h2>
                    </div>
                """

            # Renderizando contagens totais nas colunas
            with col1:
                st.markdown("<hr style='border: 2px solid #ccc;'/>", unsafe_allow_html=True)
                st.markdown(style_metric_box("#66BB6A", "black").format("Revisões Totais", revisoes_totais), unsafe_allow_html=True)
            with col2:
                st.markdown("<hr style='border: 2px solid #ccc;'/>", unsafe_allow_html=True)
                st.markdown(style_metric_box("#FF7043", "black").format("Prioridades", prioridades_totais), unsafe_allow_html=True)
            with col3:
                st.markdown("<hr style='border: 2px solid #ccc;'/>", unsafe_allow_html=True)
                st.markdown(style_metric_box("#42A5F5", "black").format("1º Envio", primeiro_envio_totais), unsafe_allow_html=True)
            with col4:
                st.markdown("<hr style='border: 2px solid #ccc;'/>", unsafe_allow_html=True)
                st.markdown(style_metric_box("#FFEB3B", "black").format("Reenvios", reenvio_totais), unsafe_allow_html=True)

            # Seção para "Informação Técnica"
            st.subheader('Informação Técnica')

            # Contagem de processos por tipo de "Informação Técnica"
            it_rada = df_selection[df_selection['Informação Técnica'].str.contains('IT - RADA', na=False, case=False)].shape[0]
            it_ipa = df_selection[df_selection['Informação Técnica'].str.contains('IT - IPA', na=False, case=False)].shape[0]
            nao = df_selection[df_selection['Informação Técnica'].str.contains('Não', na=False, case=False)].shape[0]
            it_fiscalizacao = df_selection[df_selection['Informação Técnica'].str.contains('IT - FISCALIZAÇÃO', na=False, case=False)].shape[0]
            it_descumprimento = df_selection[df_selection['Informação Técnica'].str.contains('IT - Descumprimento de Condicionante', na=False, case=False)].shape[0]
            it_outros = df_selection[df_selection['Informação Técnica'].str.contains('IT - Outros', na=False, case=False)].shape[0]

            # Layout para contagens de "Informação Técnica"
            col_it1, col_it2, col_it3, col_it4 = st.columns(4)

            # Função para estilizar as métricas de "Informação Técnica", com suporte a múltiplas linhas de informação
            def style_metric_box_it(box_color, font_color, title, *values):
                formatted_values = "<br>".join([f"{label}: {value}" for label, value in values])
                return f"""
                    <div style="background-color:{box_color}; padding:8px; border-radius:8px; border:1px solid #ccc;">
                        <h4 style="color:{font_color}; text-align:center; font-size:20px;">{title}</h4>
                        <p style="color:{font_color}; text-align:center; font-size:18px; line-height:1.2;">{formatted_values}</p>
                    </div>
                """

            # Renderizando contagens de "Informação Técnica" com agrupamento
            with col_it1:
                st.markdown(style_metric_box_it("#A5D6A7", "black", "Não Contém ou não é Informação Técnica", ("Contagem", nao)), unsafe_allow_html=True)
            with col_it2:
                st.markdown(style_metric_box_it("#FFAB91", "black", "Informação Técnica<br>IT RADA", ("Contagem", it_rada)), unsafe_allow_html=True)
            with col_it3:
                st.markdown(style_metric_box_it("#81D4FA", "black", "Informação Técnica<br>IT IPA", ("Contagem", it_ipa)), unsafe_allow_html=True)
            with col_it4:
                st.markdown(
                    style_metric_box_it(
                        "#FFE082", "black", "", 
                        ("IT - Fiscalização", it_fiscalizacao),
                        ("IT - Descumprimento", it_descumprimento),
                        ("IT - Outros", it_outros)
                    ), 
                    unsafe_allow_html=True
                )


### Gráfico de barras para contagem de revisões por analista

            # Separador
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Subtítulo
            st.subheader('Contagem de Envios por Revisor')

            # Preenchendo valores ausentes na coluna 'Revisado por' e 'Qual o tipo de envio?' com valores padrão
            df_selection['Revisado por'] = df_selection['Revisado por'].fillna('Desconhecido')
            df_selection['Qual o tipo de envio?'] = df_selection['Qual o tipo de envio?'].fillna('Desconhecido')

            # Simplifica as legendas no DataFrame
            df_selection['Qual o tipo de envio?'] = df_selection['Qual o tipo de envio?'].replace({
                '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)': '1º Envio',
                'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)': 'Prioridade',
                'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)': 'Reenvio'
            })

            # Contando revisões por tipo e por analista
            revisoes_por_tipo_analista = df_selection.groupby(['Revisado por', 'Qual o tipo de envio?']).size().unstack(fill_value=0)

            # Verificando se as colunas simplificadas para tipos de envio estão presentes
            tipos_envio = ['1º Envio', 'Prioridade', 'Reenvio']
            for tipo in tipos_envio:
                if tipo not in revisoes_por_tipo_analista.columns:
                    revisoes_por_tipo_analista[tipo] = 0  # Garante que a coluna exista com valor 0 caso esteja ausente

            # Calculando o total de revisões por analista e ordenando por total de envios
            revisoes_por_tipo_analista['Total'] = revisoes_por_tipo_analista.sum(axis=1)
            revisoes_por_tipo_analista = revisoes_por_tipo_analista.sort_values(by='Total', ascending=False)
            revisoes_por_tipo_analista['Porcentagem Cumulativa'] = (revisoes_por_tipo_analista['Total'].cumsum() / revisoes_por_tipo_analista['Total'].sum()) * 100

            # Criando o gráfico de barras empilhadas com Plotly
            fig_pareto = go.Figure()

            # Adicionando barras empilhadas para cada tipo de processo com tons de verde
            cores = ['#2ca02c', '#66bb6a', '#98d4a4']  # Tons de verde para os tipos de envio

            for tipo_envio, cor in zip(tipos_envio, cores):
                fig_pareto.add_trace(go.Bar(
                    x=revisoes_por_tipo_analista.index,
                    y=revisoes_por_tipo_analista[tipo_envio],
                    name=tipo_envio,
                    text=revisoes_por_tipo_analista[tipo_envio],
                    textposition='auto',
                    marker_color=cor
                ))

            # Adicionando linha para a soma de "1º Envio" e "Prioridade" em dourado pontilhado
            fig_pareto.add_trace(go.Scatter(
                x=revisoes_por_tipo_analista.index,
                y=(revisoes_por_tipo_analista['1º Envio'] + revisoes_por_tipo_analista['Prioridade']),
                name='Soma 1º Envio e Prioridade',
                mode='lines+markers+text',
                text=(revisoes_por_tipo_analista['1º Envio'] + revisoes_por_tipo_analista['Prioridade']),
                textposition='top center',
                line=dict(color='darkgoldenrod', width=3, dash='dot'),
                marker=dict(size=8, color='darkgoldenrod'),
                textfont=dict(color='darkgoldenrod', size=14)
            ))

            # Adicionando linha para o Total de Envios em verde tracejado
            fig_pareto.add_trace(go.Scatter(
                x=revisoes_por_tipo_analista.index,
                y=revisoes_por_tipo_analista['Total'],
                name='Total de Envios',
                mode='lines+markers+text',
                text=revisoes_por_tipo_analista['Total'],
                textposition='top center',
                line=dict(color='green', width=3, dash='dash'),
                marker=dict(size=8, color='green'),
                textfont=dict(color='green', size=14)
            ))

            # Adicionando linha para o acumulado em azul sólido
            fig_pareto.add_trace(go.Scatter(
                x=revisoes_por_tipo_analista.index,
                y=revisoes_por_tipo_analista['Porcentagem Cumulativa'],
                name='Acumulado',
                yaxis='y2',
                mode='lines+markers+text',
                text=[f"{pct:.1f}%" for pct in revisoes_por_tipo_analista['Porcentagem Cumulativa']],
                textposition='top center',
                line=dict(color='blue', width=2, dash='dash'),
                marker=dict(size=6, color='blue'),
                textfont=dict(color='blue', size=12)
            ))

            # Ajustando o layout do gráfico
            fig_pareto.update_layout(
                title='Número de Envios por Revisor - Gráfico de Pareto',
                xaxis_title='Revisor',
                yaxis_title='Quantidade de Envios',
                yaxis=dict(title='Quantidade de Envios'),
                yaxis2=dict(
                    title='Porcentagem Acumulada',
                    overlaying='y',
                    side='right',
                    range=[0, 110]
                ),
                barmode='stack',
                template='plotly_white',
                width=1000,
                height=600,
                xaxis=dict(
                    tickmode='linear',
                    tick0=1,
                    dtick=1,
                ),
                legend=dict(
                    title='Tipo de Processo',
                    orientation="h",
                    yanchor="bottom",
                    y=-0.5,
                    xanchor="right",
                    x=1,
                    font=dict(size=10),
                    title_font=dict(size=10),
                )
            )


            # Contagem de revisões por mês e tipo de processo
            df_selection['Mês'] = df_selection['Revisado em'].dt.month
            revisoes_por_mes_tipo = df_selection.groupby(['Mês', 'Qual o tipo de envio?']).size().unstack(fill_value=0)
            revisoes_por_mes_tipo['Total Mensal'] = revisoes_por_mes_tipo.sum(axis=1)
            revisoes_por_mes_tipo['Soma 1º Envio e Prioridades'] = (
                revisoes_por_mes_tipo.get('1º Envio', 0) +
                revisoes_por_mes_tipo.get('Prioridade', 0)
            )

            # Ordenando por índice do mês para manter a sequência cronológica
            revisoes_por_mes_tipo = revisoes_por_mes_tipo.sort_index()

            # Criando o gráfico de barras horizontais para revisões por mês
            fig_mes = go.Figure()

            # Adicionando barras para cada tipo de envio com cores distintas
            for tipo_envio, cor in zip(tipos_envio, cores):
                if tipo_envio in revisoes_por_mes_tipo.columns:
                    fig_mes.add_trace(go.Bar(
                        y=revisoes_por_mes_tipo.index,
                        x=revisoes_por_mes_tipo[tipo_envio],
                        name=tipo_envio,
                        orientation='h',
                        text=revisoes_por_mes_tipo[tipo_envio],
                        textposition='auto',
                        marker_color=cor
                    ))

            # Adicionando linha para o Total Mensal com rótulos de dados afastados
            fig_mes.add_trace(go.Scatter(
                y=revisoes_por_mes_tipo.index,
                x=revisoes_por_mes_tipo['Total Mensal'],
                mode='lines+markers+text',
                name='Total Mensal',
                line=dict(color='green', width=2, dash='dash'),
                marker=dict(size=8, color='green'),
                text=revisoes_por_mes_tipo['Total Mensal'],
                textposition='middle left',  # Ajustando a posição do texto para evitar sobreposição com as barras
                textfont=dict(color='green', size=12)
            ))

            # Adicionando linha para a soma de "1º Envio" e "Prioridade" no gráfico de mês em dourado
            fig_mes.add_trace(go.Scatter(
                y=revisoes_por_mes_tipo.index,
                x=revisoes_por_mes_tipo['Soma 1º Envio e Prioridades'],
                mode='lines+markers+text',
                name='Soma 1º Envio e Prioridade',
                textposition='middle right',
                line=dict(color='darkgoldenrod', width=3, dash='dot'),
                marker=dict(size=8, color='darkgoldenrod'),
                textfont=dict(color='darkgoldenrod', size=12)
            ))

            # Ajustando layout do gráfico de revisões por mês
            fig_mes.update_layout(
                title='Número de Envios por Mês - Total Mensal',
                xaxis_title='Quantidade de Envios',
                yaxis_title='Mês',
                barmode='stack',
                template='plotly_white',
                height=600,
                width=800,
                xaxis=dict(
                    autorange='reversed',  # Inverte o eixo X para aumentar da direita para a esquerda
                    tickmode='linear',
                    dtick=50  # Escala compacta do eixo X
                ),
                yaxis=dict(
                    tickmode='linear',
                    dtick=1,
                    title_font=dict(size=12),
                    side='right'  # Coloca o eixo Y no lado direito
                ),
                legend=dict(
                    title='Tipo de Processo',
                    orientation="h",
                    yanchor="bottom",
                    y=-0.4,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10),
                    title_font=dict(size=10),
                )
            )

            # Exibindo os gráficos lado a lado
            col1, col2 = st.columns([2, 1])
            with col1:
                st.plotly_chart(fig_pareto, use_container_width=True)
            with col2:
                st.plotly_chart(fig_mes, use_container_width=True)



# Verifica se a coluna "Tipo de Processo" existe, se não, cria a coluna com a função de extração
            if 'Tipo de Processo' not in df_selection.columns:
                siglas_reconhecidas = ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']
                
                # Função para extrair o tipo de processo
                def extrair_tipo_processo(numero_processo):
                    # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                    match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                    if match:
                        sigla = match.group(1)
                        # Verifica se a sigla extraída é uma das especificadas
                        if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                            return sigla
                    return 'Outros'
                
                df_selection['Tipo de Processo'] = df_selection['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].apply(extrair_tipo_processo)

            # Contando revisões por tipo de processo e analista
            revisoes_por_tipo_analista = df_selection.groupby(['Revisado por', 'Tipo de Processo']).size().unstack(fill_value=0)

            # Calculando o total de revisões por analista e ordenando
            revisoes_por_tipo_analista['Total'] = revisoes_por_tipo_analista.sum(axis=1)
            revisoes_por_tipo_analista = revisoes_por_tipo_analista.sort_values(by='Total', ascending=False)
            revisoes_por_tipo_analista['Porcentagem Cumulativa'] = (revisoes_por_tipo_analista['Total'].cumsum() / revisoes_por_tipo_analista['Total'].sum()) * 100

            # Criando o gráfico de Pareto usando "Tipo de Processo"
            fig_pareto = go.Figure()

            # Adicionando barras empilhadas para cada tipo de processo com cores primárias e suas variações
            cores = ['#2ca02c', '#66bb6a', '#98d4a4', '#ffcc00', '#ff9933', '#1f77b4', '#aec7e8']  # Escala de cores ajustada
            tipos_processo = revisoes_por_tipo_analista.columns[:-2]

            for tipo_processo, cor in zip(tipos_processo, cores):
                fig_pareto.add_trace(go.Bar(
                    x=revisoes_por_tipo_analista.index,
                    y=revisoes_por_tipo_analista[tipo_processo],
                    name=f"{tipo_processo} (Total: {revisoes_por_tipo_analista[tipo_processo].sum()})",  # Exibe o total na legenda
                    text=revisoes_por_tipo_analista[tipo_processo],
                    textposition='auto',
                    marker_color=cor
                ))

            # Adicionando linha para a porcentagem acumulativa em azul sólido
            fig_pareto.add_trace(go.Scatter(
                x=revisoes_por_tipo_analista.index,
                y=revisoes_por_tipo_analista['Porcentagem Cumulativa'],
                name='Porcentagem Cumulativa',
                yaxis='y2',
                mode='lines+markers+text',
                text=[f"{pct:.1f}%" for pct in revisoes_por_tipo_analista['Porcentagem Cumulativa']],
                textposition='top center',
                line=dict(color='blue', width=2, dash='dash'),
                marker=dict(size=6, color='blue'),
                textfont=dict(color='blue', size=12)
            ))

            # Ajustando o layout do gráfico de Pareto
            fig_pareto.update_layout(
                title='Número de Envios por Revisor - Gráfico de Pareto por Tipo de Processo',
                xaxis_title='Revisor',
                yaxis_title='Quantidade de Envios',
                yaxis=dict(title='Quantidade de Envios'),
                yaxis2=dict(
                    title='Porcentagem Cumulativa',
                    overlaying='y',
                    side='right',
                    range=[0, 110]
                ),
                barmode='stack',
                template='plotly_white',
                width=1000,
                height=600,
                xaxis=dict(
                    tickmode='linear',
                    tick0=1,
                    dtick=1,
                ),
                legend=dict(
                    title='Tipo de Processo',
                    orientation="h",
                    yanchor="bottom",
                    y=-0.5,
                    xanchor="right",
                    x=1,
                    font=dict(size=10),
                    title_font=dict(size=10),
                )
            )

            # Contagem de revisões por mês e tipo de processo
            df_selection['Mês'] = df_selection['Revisado em'].dt.month
            revisoes_por_mes_tipo = df_selection.groupby(['Mês', 'Tipo de Processo']).size().unstack(fill_value=0)
            revisoes_por_mes_tipo['Total Mensal'] = revisoes_por_mes_tipo.sum(axis=1)
            revisoes_por_mes_tipo['Soma Prioridades'] = revisoes_por_mes_tipo.get('LIO', 0) + revisoes_por_mes_tipo.get('LO', 0)

            # Ordenando pelo índice do mês para manter a sequência cronológica
            revisoes_por_mes_tipo = revisoes_por_mes_tipo.sort_index()

            # Criando o gráfico de barras horizontais para revisões por mês
            fig_mes = go.Figure()

            # Adicionando barras para cada tipo de processo com as cores primárias e suas variações
            for tipo_processo, cor in zip(tipos_processo, cores):
                if tipo_processo in revisoes_por_mes_tipo.columns:
                    fig_mes.add_trace(go.Bar(
                        y=revisoes_por_mes_tipo.index,
                        x=revisoes_por_mes_tipo[tipo_processo],
                        name=f"{tipo_processo} (Total: {revisoes_por_mes_tipo[tipo_processo].sum()})",  # Exibe o total na legenda
                        orientation='h',
                        text=revisoes_por_mes_tipo[tipo_processo],
                        textposition='auto',
                        marker_color=cor
                    ))

            # Adicionando linha para o Total Mensal com destaque nos valores em verde tracejado
            fig_mes.add_trace(go.Scatter(
                y=revisoes_por_mes_tipo.index,
                x=revisoes_por_mes_tipo['Total Mensal'],
                mode='lines+markers+text',
                name='Total Mensal',
                line=dict(color='blue', width=2, dash='dash'),
                marker=dict(size=8, color='blue'),
                text=revisoes_por_mes_tipo['Total Mensal'],
                textposition='middle left',
                textfont=dict(color='blue', size=12)
            ))

            # Adicionando linha para a soma de LIO e LO no gráfico de mês em dourado
            fig_mes.add_trace(go.Scatter(
                y=revisoes_por_mes_tipo.index,
                x=revisoes_por_mes_tipo['Soma Prioridades'],
                mode='lines+markers+text',
                name='Soma LIO e LO',
                textposition='middle left',
                line=dict(color='darkgoldenrod', width=3, dash='dot'),
                marker=dict(size=8, color='darkgoldenrod'),
                textfont=dict(color='darkgoldenrod', size=12)
            ))

            # Ajustando layout do gráfico de revisões por mês
            fig_mes.update_layout(
                title='Número de Envios por Mês - Total Mensal por Tipo de Processo',
                xaxis_title='Quantidade de Envios',
                yaxis_title='Mês',
                barmode='stack',
                template='plotly_white',
                height=600,
                width=500,
                xaxis=dict(
                    tickmode='linear',
                    dtick=50,
                    autorange='reversed'
                ),
                yaxis=dict(
                    title='Mês',
                    tickmode='linear',
                    dtick=1,
                    title_font=dict(size=12),
                    side='right'
                ),
                legend=dict(
                    title='Tipo de Processo',
                    orientation="h",
                    yanchor="bottom",
                    y=-0.4,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10),
                    title_font=dict(size=10),
                )
            )

            # Exibindo os gráficos lado a lado
            col1, col2 = st.columns([2, 1])
            with col1:
                st.plotly_chart(fig_pareto, use_container_width=True)
            with col2:
                st.plotly_chart(fig_mes, use_container_width=True)


            # Separador
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Subtítulo
            st.subheader('Desempenho do Revisor por Tipo de Envio')

            # Simplifica as legendas no DataFrame
            df_selection['Qual o tipo de envio?'] = df_selection['Qual o tipo de envio?'].replace({
                '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)': '1° Envio',
                'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)': 'Prioridade',
                'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)': 'Reenvio'
            })

            # Organização em colunas para gráficos
            revisores = df_selection['Revisado por'].unique()

            # Cálculo do total de cada tipo de envio para todos os revisores
            total_por_tipo_envio = df_selection.groupby('Qual o tipo de envio?').size()

            # Ajuste para 5 colunas por vez
            for i in range(0, len(revisores), 5):
                cols = st.columns(5, gap="small")  # Redução do espaço entre as colunas
                for idx, revisor in enumerate(revisores[i:i+5]):
                    with cols[idx]:
                        # Início do quadro de fundo
                        st.markdown(
                            "<div style='background-color: #E0F7FA; padding: 10px; border-radius: 10px; border: 1px solid #B2EBF2;'>",
                            unsafe_allow_html=True
                        )

                        # Nome do revisor em verde
                        st.markdown(f"<h5 style='text-align: center; color: mediumseagreen;'>Revisor: {revisor}</h5>", unsafe_allow_html=True)

                        # Filtra as revisões por tipo de envio para o revisor atual
                        revisoes_por_envio = df_selection[df_selection['Revisado por'] == revisor].groupby('Qual o tipo de envio?').size()

                        # Converte revisões por envio em uma lista para indexação
                        revisoes_lista = list(revisoes_por_envio.items())

                        # Configura três linhas para o revisor atual
                        for row in range(3):
                            if row < len(revisoes_lista):  # Verifica se há dados para o gráfico
                                envio, valor = revisoes_lista[row]
                                total_tipo_envio = total_por_tipo_envio.get(envio, 1)  # Total daquele tipo de envio em todos os revisores
                                percent = (valor / total_tipo_envio) * 100  # Calcula o percentual com base no total do tipo de envio

                                fig_velocimetro = go.Figure()
                                # Exibir o título acima do gráfico usando st.markdown
                                st.markdown(f"<h6 style='text-align: center; color: green;'>{envio}</h6>", unsafe_allow_html=True)  # Título acima

                                fig_velocimetro.add_trace(go.Indicator(
                                    mode="gauge+number",  # Removido o delta para evitar a numeração em vermelho
                                    value=valor,
                                    number={
                                        'valueformat': '.0f', 
                                        'font': {'size': 16},  # Reduzido o tamanho da fonte do valor
                                        'suffix': f" ({percent:.1f}%)"
                                    },
                                    gauge={
                                        'axis': {'range': [0, total_tipo_envio]},  # Define o tamanho máximo como o total para aquele tipo de envio
                                        'bar': {'color': 'mediumseagreen'},
                                        'steps': [
                                            {'range': [0, valor * 0.5], 'color': 'lightgray'},
                                            {'range': [valor * 0.5, valor], 'color': 'mediumseagreen'}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': valor * 0.9
                                        }
                                    }
                                ))

                                # Ajuste das margens para mais espaço na parte superior e evitar sobreposição
                                fig_velocimetro.update_layout(
                                    margin=dict(t=10, b=10, l=10, r=10),
                                    height=120,  # Redução da altura para um visual mais compacto
                                    template="plotly_white"
                                )

                                st.plotly_chart(fig_velocimetro, use_container_width=True)
                            else:
                                # Exibe uma mensagem de espaço em branco com "Sem informação"
                                st.write("<div style='height:180px; display:flex; align-items:center; justify-content:center;'>Sem informação para este tipo de envio.</div>", unsafe_allow_html=True)

                        # Fim do quadro de fundo
                        st.markdown("</div>", unsafe_allow_html=True)
            







            # Separador
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Subtítulo centralizado e em verde
            st.markdown("<h2 style='text-align: center; color: mediumseagreen;'>Acompanhamento do Analista Revisor</h2>", unsafe_allow_html=True)


            # Filtro de seleção para "Revisado por"
            revisores_opcoes = df_selection['Revisado por'].unique().tolist()
            revisor_selecionado = st.selectbox("Selecione o Revisor para Filtrar:", options=['Todos'] + revisores_opcoes, index=0, key="selectbox_revisor_geral")

            # Filtrar o DataFrame com base no revisor selecionado
            if revisor_selecionado != 'Todos':
                df_filtrado = df_selection[df_selection['Revisado por'] == revisor_selecionado]
            else:
                df_filtrado = df_selection


            df_selection_filtered = df_filtrado.copy()  # Definindo df_selection_filtered para uso posterior

            # Gráfico de linhas e barras empilhadas para análises temporais do analista
            st.subheader(f'Processos Enviados - {revisor_selecionado}')

            # Função aprimorada para extrair o tipo de processo de acordo com diferentes padrões
            # Função para extrair o tipo de processo
            def extrair_tipo_processo(numero_processo):
                # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                if match:
                    sigla = match.group(1)
                    # Verifica se a sigla extraída é uma das especificadas
                    if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                        return sigla
                return 'Outros'

            # Criando a coluna 'Tipo de Processo' aplicando a função de extração ao 'Número do Processo'
            if 'Tipo de Processo' not in df_selection_filtered.columns:
                df_selection_filtered['Tipo de Processo'] = df_selection_filtered[
                    'Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'
                ].apply(extrair_tipo_processo)

            # Remove as entradas que contêm "cancelado" em "Qual o tipo de envio?"
            df_selection_filtered = df_selection_filtered[~df_selection_filtered['Qual o tipo de envio?'].str.contains('cancelado', case=False, na=False)]


            # Simplifica os textos dos tipos de envio
            df_selection_filtered['Qual o tipo de envio?'] = df_selection_filtered['Qual o tipo de envio?'].replace({
                '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)': '1º Envio',
                'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)': 'Prioridades',
                'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)': 'Reenvio'
            })

            # Filtros interativos para "Tipo de Envio" e "Informação Técnica" com múltipla seleção
            tipo_envio_opcoes = df_selection_filtered['Qual o tipo de envio?'].unique().tolist()
            informacao_tecnica_opcoes = df_selection_filtered['Informação Técnica'].unique().tolist()

            tipo_envio_selecionado = st.multiselect("Filtrar por Tipo de Envio", options=tipo_envio_opcoes, default=tipo_envio_opcoes)
            informacao_tecnica_selecionada = st.multiselect("Filtrar por Informação Técnica", options=informacao_tecnica_opcoes, default=informacao_tecnica_opcoes)

            # Aplicando os filtros selecionados ao DataFrame
            df_filtrado = df_selection_filtered[
                (df_selection_filtered['Qual o tipo de envio?'].isin(tipo_envio_selecionado)) &
                (df_selection_filtered['Informação Técnica'].isin(informacao_tecnica_selecionada))
            ]

## Gráfico Radar e de barras laterais            

            # Função para criar gráfico de barras empilhadas horizontal com total e filtros
            def gerar_grafico_barras_tipo_envio(df):
                # Agrupando os dados
                df_envios_processos = df.groupby(['Qual o tipo de envio?', 'Tipo de Processo']).size().reset_index(name='Quantidade')
                total_por_tipo_envio = df_envios_processos.groupby('Qual o tipo de envio?')['Quantidade'].sum()

                # Atualizando o nome da coluna 'Qual o tipo de envio?' para incluir o total no título de cada tipo
                df_envios_processos['Qual o tipo de envio?'] = df_envios_processos['Qual o tipo de envio?'].apply(
                    lambda envio: f"{envio} ({total_por_tipo_envio[envio]})"
                )

                # Criando o gráfico de barras empilhadas com tons de verde
                fig_barras = px.bar(
                    df_envios_processos,
                    x='Quantidade',
                    y='Qual o tipo de envio?',
                    color='Tipo de Processo',
                    orientation='h',
                    title="Quantidade Total por Tipo de Envio<br>e Tipo de Processo",  # Quebra de linha inserida
                    text='Quantidade',
                    color_discrete_sequence=['#98FB98', '#90EE90', '#8FBC8F', '#66CDAA', '#7FFFD4', '#00FA9A']  # Tons de verde claros
                )

                fig_barras.update_layout(
                    showlegend=True,
                    template='plotly_white',
                    height=400,
                    xaxis_title='Quantidade de Processos',
                    yaxis_title='Tipo de Envio',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.8,  # Movendo a legenda mais abaixo do gráfico
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10),
                        itemsizing="constant"  # Alinhando os itens lado a lado
                    )
                )

                # Invertendo o eixo X para que as barras cresçam para a esquerda
                fig_barras.update_xaxes(autorange="reversed")

                return fig_barras

            # Função para criar gráfico de radar com a legenda ajustada para a parte superior
            def gerar_grafico_radar_completo(df):
                df_prioridades = df[df['Qual o tipo de envio?'] == 'Prioridades']
                df_primeiro_envio = df[df['Qual o tipo de envio?'] == '1º Envio']
                df_reenvios = df[df['Qual o tipo de envio?'] == 'Reenvio']

                radar_data_prioridades = df_prioridades.groupby('Tipo de Processo').size().reindex(df['Tipo de Processo'].unique(), fill_value=0)
                radar_data_primeiro_envio = df_primeiro_envio.groupby('Tipo de Processo').size().reindex(df['Tipo de Processo'].unique(), fill_value=0)
                radar_data_reenvios = df_reenvios.groupby('Tipo de Processo').size().reindex(df['Tipo de Processo'].unique(), fill_value=0)

                radar_data_prioridades_normalized = radar_data_prioridades / radar_data_prioridades.max()
                radar_data_primeiro_envio_normalized = radar_data_primeiro_envio / radar_data_primeiro_envio.max()
                radar_data_reenvios_normalized = radar_data_reenvios / radar_data_reenvios.max()

                fig_radar = go.Figure()

                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_data_prioridades_normalized,
                    theta=radar_data_prioridades.index,
                    fill='toself',
                    opacity=0.5,
                    name='Prioridades',
                    line=dict(color='rgba(0, 100, 0, 0.9)', width=2),  # Verde escuro mais opaco e linha mais grossa
                ))

                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_data_primeiro_envio_normalized,
                    theta=radar_data_primeiro_envio.index,
                    fill='toself',
                    opacity=0.5,
                    name='1º Envio',
                    line=dict(color='rgba(34, 139, 34, 0.9)', width=2),  # Verde floresta escuro
                ))

                fig_radar.add_trace(go.Scatterpolar(
                    r=radar_data_reenvios_normalized,
                    theta=radar_data_reenvios.index,
                    fill='toself',
                    opacity=0.5,
                    name='Reenvio',
                    line=dict(color='rgba(85, 107, 47, 0.9)', width=2),  # Verde oliva escuro
                ))

                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1])
                    ),
                    showlegend=True,
                    title="Radar - Distribuição por Tipo de Processo e Tipo de Envio",
                    template='plotly_white',
                    height=600,
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.05,  # Movendo a legenda para a parte superior
                        xanchor="center",
                        x=0.5,
                        font=dict(size=10)
                    )
                )

                return fig_radar

            # Exibindo os gráficos lado a lado
            col_radar, col_barras = st.columns([2, 1])
            with col_radar:
                st.plotly_chart(gerar_grafico_radar_completo(df_filtrado), use_container_width=True)
            with col_barras:
                st.plotly_chart(gerar_grafico_barras_tipo_envio(df_filtrado), use_container_width=True)


## Gráfico Funil

            
            # Dados para o primeiro gráfico de funil com "Tipo de Processo"
            df_funnel_processo = df_selection_filtered.groupby(['Tipo de Processo', 'Informação Técnica']).size().reset_index(name='Quantidade')
            df_funnel_processo = df_funnel_processo.sort_values(by='Quantidade', ascending=False)

            # Dados para o segundo gráfico de funil com "Tipo de Envio"
            df_funnel_envio = df_selection_filtered.groupby(['Qual o tipo de envio?', 'Informação Técnica']).size().reset_index(name='Quantidade')
            df_funnel_envio = df_funnel_envio.sort_values(by='Quantidade', ascending=False)

            # Paleta de cores em tons claros de verde, amarelo, azul e laranja
            color_sequence = [
                '#98FB98', '#FFD700', '#ADD8E6', '#FFA07A', 
                '#66CDAA', '#FFFACD', '#87CEFA', '#FFDAB9'
            ]

            # Primeiro gráfico de funil: por "Tipo de Processo"
            fig_funnel_processo = go.Figure()
            for i, info_tec in enumerate(df_funnel_processo['Informação Técnica'].unique()):
                df_info = df_funnel_processo[df_funnel_processo['Informação Técnica'] == info_tec]
                fig_funnel_processo.add_trace(go.Funnel(
                    y=df_info['Tipo de Processo'],
                    x=df_info['Quantidade'],
                    name=info_tec,
                    textinfo="value+percent total",
                    marker=dict(color=color_sequence[i % len(color_sequence)])
                ))

            fig_funnel_processo.update_layout(
                title="Funil de Processos por Tipo de Processo e Informação Técnica",
                yaxis_title="Tipo de Processo",
                xaxis_title="Quantidade de Processos",
                legend=dict(
                    title="Informação Técnica",
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                funnelmode='stack',
                template="plotly_white"
            )

            # Segundo gráfico de funil: por "Tipo de Envio"
            fig_funnel_envio = go.Figure()
            for i, info_tec in enumerate(df_funnel_envio['Informação Técnica'].unique()):
                df_info = df_funnel_envio[df_funnel_envio['Informação Técnica'] == info_tec]
                fig_funnel_envio.add_trace(go.Funnel(
                    y=df_info['Qual o tipo de envio?'],
                    x=df_info['Quantidade'],
                    name=info_tec,
                    textinfo="value+percent total",
                    marker=dict(color=color_sequence[i % len(color_sequence)])
                ))

            fig_funnel_envio.update_layout(
                title="Funil de Processos por Tipo de Envio e Informação Técnica",
                yaxis_title="Tipo de Envio",
                xaxis_title="Quantidade de Processos",
                legend=dict(
                    title="Informação Técnica",
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                funnelmode='stack',
                template="plotly_white"
            )

            # Exibindo os gráficos lado a lado
            col_funnel_1, col_funnel_2 = st.columns(2)
            with col_funnel_1:
                st.plotly_chart(fig_funnel_processo, use_container_width=True)
            with col_funnel_2:
                st.plotly_chart(fig_funnel_envio, use_container_width=True)


## Gráfico de dispersão com bolhas

            # Agrupando os dados para o gráfico de dispersão com bolhas
            df_bolhas = df_filtrado.groupby(['Qual o tipo de envio?', 'Tipo de Processo']).size().reset_index(name='Quantidade')

            # Criando o gráfico de dispersão com bolhas
            fig_bolhas = px.scatter(
                df_bolhas,
                x="Tipo de Processo",
                y="Qual o tipo de envio?",
                size="Quantidade",
                color="Qual o tipo de envio?",
                hover_name="Tipo de Processo",
                size_max=60
            )

            # Configurando o layout e exibindo o gráfico
            fig_bolhas.update_layout(
                title="Distribuição de Quantidade por Tipo de Envio e Tipo de Processo",
                template="plotly_white",
                xaxis_title="Tipo de Processo",
                yaxis_title="Tipo de Envio",
                height=600
            )
            st.plotly_chart(fig_bolhas, use_container_width=True)



# Correçoes


            # Separador
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        
            # Subtítulo
            st.subheader('Análise de Pendências de Reenvio após Correções')
            
            # Filtrar o DataFrame para casos onde o status é "Correção"
            df_correcao = df_selection[df_selection['Status do processo pós revisão'] == 'Correção'].copy()

            # Verificar se o DataFrame df_correcao não está vazio
            if not df_correcao.empty:
                
                # Obtém a data de hoje no formato datetime64 para compatibilidade
                data_hoje = pd.to_datetime(datetime.now().date())

                # Calcula a diferença em dias entre a data de hoje e "Revisado em"
                df_correcao['Foi corrigido há (dias)'] = (data_hoje - df_correcao['Revisado em']).dt.days

                # Selecionar colunas para exibição e organizar em ordem alfabética e por tempo de correção em ordem decrescente
                df_correcao_selecao = df_correcao[['Revisado por', 'Analista (você)',
                                                'Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)',
                                                'Carimbo de data/hora', 'Revisado em', 'Foi corrigido há (dias)']]
                df_correcao_selecao = df_correcao_selecao.sort_values(by=['Revisado por', 'Foi corrigido há (dias)'], ascending=[True, False])

                # Obter opções únicas de "Revisado por" para o seletor
                revisores = df_correcao['Revisado por'].unique()
                revisor_selecionado_corr = st.selectbox("Selecione um Revisor para Filtrar", options=["Todos"] + list(revisores), key="selectbox_revisor_correcao")

                # Aplicar filtro baseado na seleção de revisor
                if revisor_selecionado_corr != "Todos":
                    df_correcao_selecao = df_correcao_selecao[df_correcao_selecao['Revisado por'] == revisor_selecionado_corr]
                    df_sunburst = df_correcao_selecao.groupby(['Revisado por', 'Analista (você)']).size().reset_index(name='Quantidade')
                else:
                    df_sunburst = df_correcao.groupby(['Revisado por', 'Analista (você)']).size().reset_index(name='Quantidade')

                # Gráfico de Barras para Quantidade por Revisor
                fig_barras = go.Figure(data=[
                    go.Bar(
                        x=df_correcao['Revisado por'].value_counts().index,
                        y=df_correcao['Revisado por'].value_counts().values,
                        marker_color="green"
                    )
                ])
                fig_barras.update_layout(
                    title="Quantidade de Correções por Revisor",
                    xaxis_title="Revisor",
                    yaxis_title="Quantidade de Correções",
                    template='plotly_white',
                    width=500,
                    height=400
                )

                # Gráfico Sunburst com tons de verde
                fig_sunburst = px.sunburst(
                    df_sunburst,
                    path=['Revisado por', 'Analista (você)'],
                    values='Quantidade',
                    title="Distribuição de Correções por Revisado<br>por e Analista",
                    color_discrete_sequence=px.colors.sequential.Tealgrn
                )
                fig_sunburst.update_layout(width=500, height=500)

                # Exibir gráficos lado a lado e a tabela filtrada
                col1, col2 = st.columns([1, 2])
                col1.plotly_chart(fig_barras, use_container_width=True)
                col1.plotly_chart(fig_sunburst, use_container_width=True)

                # Tabela com dados filtrados e estilo condicional aplicado
                with col2:
                    # Aplicando estilo condicional no DataFrame para a coluna "Foi corrigido há (dias)"
                    def apply_styles(df):
                        # Função para aplicar cores com base em valores na coluna "Foi corrigido há (dias)"
                        styles = pd.DataFrame('', index=df.index, columns=df.columns)
                        styles['Foi corrigido há (dias)'] = [
                            'color: white; background-color: #2e8b57;' if val >= 0 else ''
                            for val in df['Foi corrigido há (dias)']
                        ]
                        return styles

                    # Aplicar o estilo condicional no DataFrame
                    styled_df = df_correcao_selecao.style.apply(apply_styles, axis=None)
                    
                    # Exibir a tabela com altura e largura ajustadas
                    st.dataframe(styled_df, height=500, width=1000, use_container_width=True)

            else:
                st.warning("Não há dados para correções.")



### Tabelas de dados

            # Função para aplicar o estilo condicional
            def aplicar_estilos(df):
                styles = []
                for index, row in df.iterrows():
                    if pd.isna(row['Revisado em']):
                        styles.append(['background-color: #B0B0B0; color: #000000'] * len(row))  # Cor para "Não Revisados"
                    elif "Prioridades" in str(row["Qual o tipo de envio?"]):
                        styles.append(['background-color: #2E8B57; color: #FFFFFF'] * len(row))  # Cor para "Prioridade"
                    else:
                        styles.append([''] * len(row))
                return pd.DataFrame(styles, index=df.index, columns=df.columns)

            # Separador visual entre seções
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Título descritivo centralizado com tamanho maior
            st.markdown("<h2 style='text-align: center; font-size: 28px;'>Tabelas de Dados</h2>", unsafe_allow_html=True)

            # Legenda explicativa à esquerda
            st.markdown("<h4>Legenda de Cores</h4>", unsafe_allow_html=True)
            st.markdown(
                """
                <div style="display: flex; align-items: flex-start; flex-direction: column;">
                    <div style="display: flex; align-items: center; margin-top: 8px;">
                        <div style="width: 20px; height: 20px; background-color: #B0B0B0; margin-right: 10px; border-radius: 3px; border: 1px solid #444;"></div>
                        <span>Não Revisados</span>
                    </div>
                    <div style="display: flex; align-items: center; margin-top: 8px;">
                        <div style="width: 20px; height: 20px; background-color: #2E8B57; margin-right: 10px; border-radius: 3px; border: 1px solid #444;"></div>
                        <span>Prioridade</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Tabela Geral
            st.markdown("<h3 style='text-align: center;'>Tabela Geral</h3>", unsafe_allow_html=True)
            st.write("Visualização de dados filtrados:")
            styled_df_full = df_selection.style.apply(aplicar_estilos, axis=None)
            st.dataframe(styled_df_full, use_container_width=True)

            # Crie sua Tabela
            st.markdown("<h3 style='text-align: center;'>Crie sua Tabela</h3>", unsafe_allow_html=True)
            st.markdown("OBS: Manter sempre: 'Qual o tipo de envio?' e 'Revisado em'")

            # Filtra colunas existentes para usar como valores padrão
            default_columns = [
                'Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)',
                "Qual o tipo de envio?", 
                "Revisado por", 
                "Revisado em",
                "Status do processo pós revisão",
                "Informação Técnica",
                "Tipo de empreendimento",
                "Quantidade de empreendimentos",
                "Empresa"
            ]
            default_columns = [col for col in default_columns if col in df_selection.columns]  # Filtrar colunas que existem

            # Expansor para visualização personalizada dos dados
            with st.expander("VISUALIZAÇÃO GERAL DOS DADOS"):
                showData = st.multiselect(
                    'Filtrar: ',
                    df_selection.columns,
                    default=default_columns
                )

                styled_df = df_selection[showData].style.apply(aplicar_estilos, axis=None)
                st.dataframe(styled_df, use_container_width=True)

        else:
            st.error("O arquivo está vazio ou ocorreu um erro ao processar os dados.")
    else:
        st.warning("""
            Carregue a base no Sidebar ao lado.

            ⬅️   Por favor, faça o upload do arquivo CSV - Revisão de Pareceres (respostas) 
            disponível em: https://docs.google.com/spreadsheets/d/18juQmpGe86MRr4uXTxDiJC1wAPQXXqJs1SgMoFpFC2g/edit?gid=1572677783#gid=1572677783.
            """)


### *** Seção Resumo dos Envios ***

# Função principal para acompanhamento dos Envios
def resumo_envios():
    
    if uploaded_file is not None:
        # Carrega os dados do arquivo
        df = load_data(uploaded_file)

        # Título principal da seção
        st.markdown(
            "<h1 style='text-align: center; color: #98FF98; font-size: 42px; font-weight: bold; text-decoration: underline;'>Resumo dos Envios</h1>",
            unsafe_allow_html=True
        )

        # Filtrar o DataFrame para remover processos "cancelados" e "cancelar"
        df = df[~df['Qual o tipo de envio?'].str.contains(r'\bcancel(ad|ar)\b', case=False, na=False)]

        # Espaçador ou linha de separação entre seções
        st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # Verifica se o DataFrame contém dados
        if df is not None and not df.empty:
            # Converte a coluna de data "Carimbo de data/hora" para o formato datetime
            if 'Carimbo de data/hora' in df.columns:
                df['Carimbo de data/hora'] = pd.to_datetime(df['Carimbo de data/hora'], errors='coerce', dayfirst=True)

            # Verifica se a coluna "Tipo de Processo" existe, se não, cria a coluna com a função de extração
            if 'Tipo de Processo' not in df.columns:
                siglas_reconhecidas = ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']
                
                # Função para extrair o tipo de processo
                def extrair_tipo_processo(numero_processo):
                    # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                    match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                    if match:
                        sigla = match.group(1)
                        # Verifica se a sigla extraída é uma das especificadas
                        if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                            return sigla
                    return 'Outros'
                
                df['Tipo de Processo'] = df['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].apply(extrair_tipo_processo)

            # Define as variáveis para a data atual e o mês corrente
            hoje = datetime.now().date()
            mes_corrente = datetime.now().month
            ano_corrente = datetime.now().year

            # Configura os filtros lado a lado para data e mês
            st.markdown("<h3 style='text-align: center;'>Filtros</h3>", unsafe_allow_html=True)
            col1_filter, col2_filter = st.columns(2)
            with col1_filter:
                dias_disponiveis = sorted(df['Carimbo de data/hora'].dt.date.dropna().unique(), reverse=True)
                default_dias = [hoje] if hoje in dias_disponiveis else []
                dias_selecionados = st.multiselect(
                    "Selecione os Dias", 
                    options=dias_disponiveis, 
                    default=default_dias, 
                    format_func=lambda x: x.strftime('%d-%b-%Y'),
                    key="filtro_dias_envios"
                )
            
            with col2_filter:
                meses_disponiveis = sorted(df['Carimbo de data/hora'].dt.to_period("M").dropna().unique(), reverse=True)
                default_meses = [pd.Period(year=ano_corrente, month=mes_corrente, freq='M')] if pd.Period(year=ano_corrente, month=mes_corrente, freq='M') in meses_disponiveis else []
                meses_selecionados = st.multiselect(
                    "Selecione os Meses", 
                    options=meses_disponiveis, 
                    default=default_meses, 
                    format_func=lambda x: x.strftime('%b-%Y'),
                    key="filtro_meses_envios"
                )

            # Exibindo filtros adicionais para Tipo de Envio, Tipo de Processo e Informação Técnica
            tipos_envio_opcoes = ["Todos"] + sorted(df[~df['Qual o tipo de envio?'].str.contains("CANCELADO", case=False)]['Qual o tipo de envio?'].dropna().unique())
            tipos_processo_opcoes = ["Todos"] + sorted(df['Tipo de Processo'].dropna().unique())
            informacao_tecnica_opcoes = ["Todos"] + sorted(df['Informação Técnica'].dropna().unique())

            # Colocando os filtros de Tipo de Envio, Tipo de Processo e Informação Técnica recuados na coluna 1
            st.markdown("<h3 style='text-align: left;'>Filtros Adicionais</h3>", unsafe_allow_html=True)
            with col1_filter:
                tipos_envio_selecionados = st.multiselect(
                    "Selecione o(s) Tipo(s) de Envio",
                    options=tipos_envio_opcoes,
                    default="Todos"
                )
                tipos_processo_selecionados = st.multiselect(
                    "Selecione o(s) Tipo(s) de Processo",
                    options=tipos_processo_opcoes,
                    default="Todos"
                )
                informacao_tecnica_selecionada = st.multiselect(
                    "Filtrar por Informação Técnica",
                    options=informacao_tecnica_opcoes,
                    default="Todos"
                )

            # Aplicando filtros ao DataFrame, ignorando filtros "Todos"
            if "Todos" not in tipos_envio_selecionados:
                df = df[df['Qual o tipo de envio?'].isin(tipos_envio_selecionados)]
            if "Todos" not in tipos_processo_selecionados:
                df = df[df['Tipo de Processo'].isin(tipos_processo_selecionados)]
            if "Todos" not in informacao_tecnica_selecionada:
                df = df[df['Informação Técnica'].isin(informacao_tecnica_selecionada)]



            # Calcula o total do(s) dia(s) selecionado(s)
            df_dias_selecionados = df[df['Carimbo de data/hora'].dt.date.isin(dias_selecionados)]
            total_dia = df_dias_selecionados.shape[0]

            # Calcula o total do(s) mês(es) selecionado(s)
            df_meses_selecionados = df[df['Carimbo de data/hora'].dt.to_period("M").isin(meses_selecionados)]
            total_mes = df_meses_selecionados.shape[0]

            # Definindo estilo customizado para métricas com múltiplas linhas
            def style_metric_box_multi(box_color, font_color, title, content):
                return f"""
                    <div style="background-color:{box_color}; padding:10px; border-radius:10px; border:2px solid #ddd;">
                        <h4 style="color:{font_color}; text-align:center;">{title}</h4>
                        <div style="color:{font_color}; text-align:center; font-size:18px;">
                            {content}
                        </div>
                    </div>
                """

            # Renderizando métricas de total de envios diários e mensais com estilo e cores ajustadas
            st.markdown("<h3 style='text-align: center;'>Totais de Envios Selecionados</h3>", unsafe_allow_html=True)
            col1_total, col2_total = st.columns(2)

            with col1_total:
                st.markdown(style_metric_box_multi("#66BB6A", "black", "Total de Envios do Dia(s) Selecionado(s)", total_dia), unsafe_allow_html=True)

            with col2_total:
                st.markdown(style_metric_box_multi("#D8F0D8", "black", "Total de Envios do Mês(es) Selecionado(s)", total_mes), unsafe_allow_html=True)

            # Exibindo o total de envios por cada analista para o dia e para o mês
            totais_por_analista_dia = df_dias_selecionados.groupby("Analista (você)").size()
            totais_por_analista_mes = df_meses_selecionados.groupby("Analista (você)").size()

            conteudo_dia = "<br>".join([f"{analista}: {total}" for analista, total in totais_por_analista_dia.items()])
            conteudo_mes = "<br>".join([f"{analista}: {total}" for analista, total in totais_por_analista_mes.items()])

            st.markdown("<h3 style='text-align: center;'>Totais de Envios por Analista</h3>", unsafe_allow_html=True)
            col_analista_dia, col_analista_mes = st.columns(2)

            with col_analista_dia:
                st.markdown(style_metric_box_multi("#FFE082", "black", "Total Enviado por Analista (Dia)", conteudo_dia), unsafe_allow_html=True)

            with col_analista_mes:
                st.markdown(style_metric_box_multi("#FFECB3", "black", "Total Enviado por Analista (Mês)", conteudo_mes), unsafe_allow_html=True)


            
            # Configura estilo e layout dos gráficos
            st.markdown("<h3 style='text-align: center;'>Quadro de Envios</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)


            # Definição de cores e tipos de envio com os nomes simplificados, utilizando a paleta Tealgrn
            cores = ['#66CDAA', '#98FB98', '#00FA9A'] 
            tipos_envio = [
                '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)',
                'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)',
                'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)'
            ]
            nomes_legenda = ["1° Envio", "Prioridades", "Reenvios"]

            # Gráfico de Envios do Dia
            with col1:
                st.markdown("<div class='custom-col'>", unsafe_allow_html=True)
                st.subheader("Envios do Dia")


                # Filtragem do DataFrame com base nos dias selecionados
                df_dias_selecionados = df[df['Carimbo de data/hora'].dt.date.isin(dias_selecionados)]
                
        
                # Verifica se há dados para o(s) dia(s) selecionado(s)
                if df_dias_selecionados.empty:
                    st.warning("A base não contém dados para o dia selecionado. Selecione outro(s) dia(s).")
                else:
                    # Agrupa os dados por tipo de envio e analista
                    revisoes_dia = df_dias_selecionados.groupby(['Analista (você)', 'Qual o tipo de envio?']).size().unstack(fill_value=0).reset_index()
                    
                    # Garante que as colunas dos tipos de envio estão presentes com os nomes completos
                    for tipo in tipos_envio:
                        if tipo not in revisoes_dia.columns:
                            revisoes_dia[tipo] = 0
                    
                    # Cálculo das colunas de Totais e Pareto
                    revisoes_dia['Total'] = revisoes_dia[tipos_envio].sum(axis=1)
                    revisoes_dia = revisoes_dia.sort_values(by='Total', ascending=False)  # Ordena do maior para o menor
                    revisoes_dia['Cumulativo'] = revisoes_dia['Total'].cumsum()
                    revisoes_dia['Porcentagem'] = 100 * revisoes_dia['Cumulativo'] / revisoes_dia['Total'].sum()

                    # Obtém o valor máximo para ajustar o eixo y
                    max_y = revisoes_dia[tipos_envio].values.max() * 1.7

                    # Criação do gráfico de Pareto
                    fig_revisoes_dia = go.Figure()

                    # Calcula o total de cada tipo de envio
                    totais_por_tipo_envio_dia = revisoes_dia[tipos_envio].sum().to_dict()


                    # Adiciona barras para cada tipo de envio com os nomes simplificados e rótulos de dados
                    for tipo_envio, cor, nome_legenda in zip(tipos_envio, cores, nomes_legenda):
                        total_tipo_envio = int(totais_por_tipo_envio_dia[tipo_envio])  # Obtém o total e converte para inteiro
                        fig_revisoes_dia.add_trace(go.Bar(
                            x=revisoes_dia['Analista (você)'],
                            y=revisoes_dia[tipo_envio],
                            name=f"{nome_legenda} ({total_tipo_envio})",  # Inclui o total na legenda
                            marker_color=cor,
                            yaxis='y1',
                            text=revisoes_dia[tipo_envio],  # Rótulo de dados
                            textposition='auto'  # Exibe rótulos automaticamente
                        ))

                    # Linha para a soma de "1º Envio" e "Prioridades" em amarelo pontilhado
                    fig_revisoes_dia.add_trace(go.Scatter(
                        x=revisoes_dia['Analista (você)'],
                        y=revisoes_dia[tipos_envio[0]] + revisoes_dia[tipos_envio[1]],
                        mode='lines+markers+text',
                        text=revisoes_dia[tipos_envio[0]] + revisoes_dia[tipos_envio[1]],
                        line=dict(color='orange', width=3, dash='dash'),
                        textposition='top center',
                        name="Total 1º Envio e Prioridades",
                        yaxis='y1',
                        textfont=dict(color='orange')
                    ))

                    # Linha para o total geral de revisões
                    fig_revisoes_dia.add_trace(go.Scatter(
                        x=revisoes_dia['Analista (você)'],
                        y=revisoes_dia['Total'],
                        mode='lines+markers+text',
                        text=revisoes_dia['Total'],
                        line=dict(color='green', width=3, dash='dash'),
                        textposition='top center',
                        name="Total Geral",
                        yaxis='y1',
                        textfont=dict(color='green')
                    ))

                    # Linha de Pareto
                    fig_revisoes_dia.add_trace(go.Scatter(
                        x=revisoes_dia['Analista (você)'],
                        y=revisoes_dia['Porcentagem'],
                        mode='lines+markers+text',
                        text=[f'{p:.1f}% ({c})' for p, c in zip(revisoes_dia['Porcentagem'], revisoes_dia['Cumulativo'])],
                        line=dict(color='blue', width=0.5, dash='dash'),
                        textposition='top center',
                        name="Acumulado (%)",
                        yaxis='y2',
                        textfont=dict(color='blue')
                    ))

                    # Configuração do layout do gráfico de Envios do Dia com ajuste do eixo y
                    fig_revisoes_dia.update_layout(
                        title='Envios dos Dias Selecionados',
                        xaxis_title='Analista (você)',
                        yaxis=dict(title='Quantidade', side='left', range=[0, max_y]),
                        yaxis2=dict(title='Porcentagem Cumulativa', overlaying='y', side='right', range=[0, 110]),
                        barmode='stack',
                        width=700,
                        height=600,
                        legend=dict(orientation='h', yanchor='bottom', y=-1, xanchor='center', x=0.5)
                    )
                    st.plotly_chart(fig_revisoes_dia, use_container_width=True)

                    st.markdown("</div>", unsafe_allow_html=True)

# Gráficos de Envios Diárias e Mensais por Tipo de Processo com estilo consistente

            # Função aprimorada para extrair o tipo de processo, lidando com valores não-string
            # Função para extrair o tipo de processo
            def extrair_tipo_processo(numero_processo):
                # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                if match:
                    sigla = match.group(1)
                    # Verifica se a sigla extraída é uma das especificadas
                    if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                        return sigla
                return 'Outros'
            # Adicionando coluna "Tipo de Processo" se ainda não existir
            if 'Tipo de Processo' not in df.columns:
                df['Tipo de Processo'] = df['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].apply(extrair_tipo_processo)

            # Cores e tipos para o gráfico
            cores_processo = [
                '#66CDAA', '#98FB98', '#00FA9A', '#d4f0e1', '#a8e6cf', '#81cfa9', '#b3e2d4', '#cce5ff', '#99d3ff', 
                '#c3e8b0', '#fef9d7', '#fff7c1', '#fbf3d0', '#d2f1e1', '#9ad1e6', '#b5e0cc'
            ]
            tipos_processo_legenda = ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr' "Outros"]

            # Gráficos Diários e Mensais por Tipo de Processo com ordenação e totais na legenda
            for periodo, (df_tipo_processo, filtro_periodo, titulo) in {
                'dia': (df[df['Carimbo de data/hora'].dt.date.isin(dias_selecionados)], col1, "Envios Diárias por Tipo de Processo"),
                'mes': (df[df['Carimbo de data/hora'].dt.to_period("M").isin(meses_selecionados)], col2, "Envios Mensais por Tipo de Processo")
            }.items():

                with filtro_periodo:
                    st.markdown("<div class='custom-col'>", unsafe_allow_html=True)
                    st.subheader(titulo)

                    df_tipo_processo = df_tipo_processo.groupby(['Analista (você)', 'Tipo de Processo']).size().unstack(fill_value=0).reset_index()
                    if not df_tipo_processo.empty:
                        # Calcula totais e organiza ordem
                        df_tipo_processo['Total'] = df_tipo_processo.select_dtypes(include=[int, float]).sum(axis=1)
                        df_tipo_processo = df_tipo_processo.sort_values(by='Total', ascending=False)
                        df_tipo_processo['Cumulativo'] = df_tipo_processo['Total'].cumsum()
                        df_tipo_processo['Porcentagem'] = 100 * df_tipo_processo['Cumulativo'] / df_tipo_processo['Total'].sum()

                        # Calcular total de cada tipo de processo para exibir na legenda, formatando para remover o decimal
                        totais_por_tipo = df_tipo_processo.select_dtypes(include=[int, float]).sum().to_dict()

                        # Configuração do gráfico
                        fig_tipo_processo = go.Figure()
                        for tipo_processo, cor in zip(
                                sorted(df_tipo_processo.columns[1:-3], key=lambda x: totais_por_tipo[x], reverse=True),
                                cores_processo):
                            fig_tipo_processo.add_trace(go.Bar(
                                x=df_tipo_processo['Analista (você)'],
                                y=df_tipo_processo[tipo_processo],
                                name=f"{tipo_processo} ({int(totais_por_tipo[tipo_processo])})",  # Exibindo apenas o valor inteiro na legenda
                                marker_color=cor,
                                yaxis='y1',
                                text=df_tipo_processo[tipo_processo],
                                textposition='auto'
                            ))

                        # Linha de Pareto
                        fig_tipo_processo.add_trace(go.Scatter(
                            x=df_tipo_processo['Analista (você)'],
                            y=df_tipo_processo['Porcentagem'],
                            mode='lines+markers+text',
                            text=[f'{p:.1f}%' for p in df_tipo_processo['Porcentagem']],
                            line=dict(color='blue', width=0.5, dash='dash'),
                            textposition='top center',
                            name="Acumulado (%)",
                            yaxis='y2',
                            textfont=dict(color='blue')
                        ))

                        # Layout do gráfico
                        fig_tipo_processo.update_layout(
                            title=titulo,
                            xaxis_title='Analista (você)',
                            yaxis=dict(title='Quantidade', side='left', range=[0, df_tipo_processo[df_tipo_processo.columns[1:-3]].values.max() * 1.7]),
                            yaxis2=dict(title='Porcentagem Cumulativa', overlaying='y', side='right', range=[0, 110]),
                            barmode='stack',
                            width=700,
                            height=600,
                            legend=dict(orientation='h', yanchor='bottom', y=-1, xanchor='center', x=0.5)
                        )
                        st.plotly_chart(fig_tipo_processo, use_container_width=True)
                    else:
                        st.warning(f"A base não contém dados para o {periodo} selecionado.")





            # Gráfico de Envios do Mês
            with col2:
                st.markdown("<div class='custom-col'>", unsafe_allow_html=True)
                st.subheader("Envios do Mês")

                
            # Gráfico de Envios do Mês
            with col2:
                # Filtragem do DataFrame com base nos meses selecionados
                df_meses_selecionados = df[df['Carimbo de data/hora'].dt.to_period("M").isin(meses_selecionados)]
                
                # Verifica se há dados para o(s) mês(es) selecionado(s)
                if df_meses_selecionados.empty:
                    st.warning("A base não contém dados para o mês selecionado. Selecione outro(s) mês(es).")
                else:
                    # Agrupa os dados por tipo de envio e analista
                    revisoes_mes = df_meses_selecionados.groupby(['Analista (você)', 'Qual o tipo de envio?']).size().unstack(fill_value=0).reset_index()
                    
                    # Garante que as colunas dos tipos de envio estão presentes com os nomes completos
                    for tipo in tipos_envio:
                        if tipo not in revisoes_mes.columns:
                            revisoes_mes[tipo] = 0
                    
                    # Cálculo das colunas de Totais e Pareto
                    revisoes_mes['Total'] = revisoes_mes[tipos_envio].sum(axis=1)
                    revisoes_mes = revisoes_mes.sort_values(by='Total', ascending=False)  # Ordena do maior para o menor
                    revisoes_mes['Cumulativo'] = revisoes_mes['Total'].cumsum()
                    revisoes_mes['Porcentagem'] = 100 * revisoes_mes['Cumulativo'] / revisoes_mes['Total'].sum()

                    # Obtém o valor máximo para ajustar o eixo y
                    max_y = revisoes_mes[tipos_envio].values.max() * 2

                    # Calcula o total de cada tipo de envio
                    totais_por_tipo_envio = revisoes_mes[tipos_envio].sum().to_dict()

                    # Criação do gráfico de Pareto para o mês
                    fig_revisoes_mes = go.Figure()

                    # Adiciona barras para cada tipo de envio com os nomes simplificados e valores totais na legenda
                    for tipo_envio, cor, nome_legenda in zip(tipos_envio, cores, nomes_legenda):
                        total_tipo_envio = int(totais_por_tipo_envio[tipo_envio])  # Obtém o total e converte para inteiro
                        fig_revisoes_mes.add_trace(go.Bar(
                            x=revisoes_mes['Analista (você)'],
                            y=revisoes_mes[tipo_envio],
                            name=f"{nome_legenda} ({total_tipo_envio})",  # Inclui o total na legenda
                            marker_color=cor,
                            yaxis='y1',
                            text=revisoes_mes[tipo_envio],  # Rótulo de dados
                            textposition='auto'  # Exibe rótulos automaticamente
                        ))

                    # Linha para a soma de "1º Envio" e "Prioridades" em amarelo pontilhado
                    fig_revisoes_mes.add_trace(go.Scatter(
                        x=revisoes_mes['Analista (você)'],
                        y=revisoes_mes[tipos_envio[0]] + revisoes_mes[tipos_envio[1]],
                        mode='lines+markers+text',
                        text=revisoes_mes[tipos_envio[0]] + revisoes_mes[tipos_envio[1]],
                        line=dict(color='orange', width=3, dash='dash'),
                        textposition='top center',
                        name="Total 1º Envio e Prioridades",
                        yaxis='y1',
                        textfont=dict(color='orange')
                    ))

                    # Linha para o total geral de revisões
                    fig_revisoes_mes.add_trace(go.Scatter(
                        x=revisoes_mes['Analista (você)'],
                        y=revisoes_mes['Total'],
                        mode='lines+markers+text',
                        text=revisoes_mes['Total'],
                        line=dict(color='green', width=3, dash='dash'),
                        textposition='top center',
                        name="Total Geral",
                        yaxis='y1',
                        textfont=dict(color='green')
                    ))

                    # Linha de Pareto
                    fig_revisoes_mes.add_trace(go.Scatter(
                        x=revisoes_mes['Analista (você)'],
                        y=revisoes_mes['Porcentagem'],
                        mode='lines+markers+text',
                        text=[f'{p:.1f}% ({c})' for p, c in zip(revisoes_mes['Porcentagem'], revisoes_mes['Cumulativo'])],
                        line=dict(color='blue', width=0.5, dash='dash'),
                        textposition='top center',
                        name="Acumulado (%)",
                        yaxis='y2',
                        textfont=dict(color='blue')
                    ))

                    # Configuração do layout do gráfico de Envios do Mês
                    fig_revisoes_mes.update_layout(
                        title='Envios dos Meses Selecionados',
                        xaxis_title='Analista (você)',
                        yaxis=dict(title='Quantidade', side='left', range=[0, max_y]),
                        yaxis2=dict(title='Porcentagem Cumulativa', overlaying='y', side='right', range=[0, 110]),
                        barmode='stack',
                        width=700,
                        height=600,
                        legend=dict(orientation='h', yanchor='bottom', y=-1, xanchor='center', x=0.5)
                    )
                    st.plotly_chart(fig_revisoes_mes, use_container_width=True)

                
                st.markdown("</div>", unsafe_allow_html=True)


            # Seção de Tabelas com estilo condicional
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            
            # Função para aplicar o estilo condicional
            def aplicar_estilos(df):
                styles = []
                for index, row in df.iterrows():
                    if pd.isna(row['Carimbo de data/hora']):
                        styles.append(['background-color: #B0B0B0; color: #000000'] * len(row))  # Cor para "Não Revisados"
                    elif "Prioridades" in str(row["Qual o tipo de envio?"]):
                        styles.append(['background-color: #2E8B57; color: #FFFFFF'] * len(row))  # Cor para "Prioridade"
                    else:
                        styles.append([''] * len(row))
                return pd.DataFrame(styles, index=df.index, columns=df.columns)

            # Tabela de processos do dia
            st.markdown("<h3 style='text-align: center;'>Tabela de Processos do Dia Selecionado</h3>", unsafe_allow_html=True)
            df_dia_selecionados = df[df['Carimbo de data/hora'].dt.date.isin(dias_selecionados)]
            styled_df_dia = df_dia_selecionados.style.apply(aplicar_estilos, axis=None)
            st.dataframe(styled_df_dia, use_container_width=True)

            # Tabela de processos do mês
            st.markdown("<h3 style='text-align: center;'>Tabela de Processos do Mês Selecionado</h3>", unsafe_allow_html=True)
            df_mes_selecionados = df[df['Carimbo de data/hora'].dt.to_period("M").isin(meses_selecionados)]
            styled_df_mes = df_mes_selecionados.style.apply(aplicar_estilos, axis=None)
            st.dataframe(styled_df_mes, use_container_width=True)


        else:
            st.error("O arquivo está vazio ou ocorreu um erro ao processar os dados.")
    else:
        st.warning("""
            Carregue a base no Sidebar ao lado.

            ⬅️   Por favor, faça o upload do arquivo CSV - Revisão de Pareceres (respostas) 
            disponível em: https://docs.google.com/spreadsheets/d/18juQmpGe86MRr4uXTxDiJC1wAPQXXqJs1SgMoFpFC2g/edit?gid=1572677783#gid=1572677783.
            """)

### *** Seção Resumo de Envios***

# Função principal para acompanhamento do Realizado
def resumo_revisoes():
    
    if uploaded_file is not None:
        # Carrega os dados do arquivo
        df = load_data(uploaded_file)

        # Título principal da seção
        st.markdown(
            "<h1 style='text-align: center; color: #98FF98; font-size: 42px; font-weight: bold; text-decoration: underline;'>Resumo de Envios</h1>",
            unsafe_allow_html=True
        )

        # Filtrar o DataFrame para remover processos "cancelados" e "cancelar"
        df = df[~df['Qual o tipo de envio?'].str.contains(r'\bcancel(ad|ar)\b', case=False, na=False)]

        # Espaçador ou linha de separação entre seções
        st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # Verifica se o DataFrame contém dados
        if df is not None and not df.empty:
            # Converte a coluna de data "Revisado em" para o formato datetime
            if 'Revisado em' in df.columns:
                df['Revisado em'] = pd.to_datetime(df['Revisado em'], errors='coerce', dayfirst=True)


            # Verifica se a coluna "Tipo de Processo" existe, se não, cria a coluna com a função de extração
            if 'Tipo de Processo' not in df.columns:
                siglas_reconhecidas = ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']
                
                # Função para extrair o tipo de processo
                def extrair_tipo_processo(numero_processo):
                    # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                    match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                    if match:
                        sigla = match.group(1)
                        # Verifica se a sigla extraída é uma das especificadas
                        if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                            return sigla
                    return 'Outros'
                
                df['Tipo de Processo'] = df['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].apply(extrair_tipo_processo)

            # Define as variáveis para a data atual e o mês corrente
            hoje = datetime.now().date()
            mes_corrente = datetime.now().month
            ano_corrente = datetime.now().year

            # Configura os filtros lado a lado
            st.markdown("<h3 style='text-align: center;'>Filtros</h3>", unsafe_allow_html=True)
            col1_filter, col2_filter = st.columns(2)
            with col1_filter:
                dias_disponiveis = sorted(df['Revisado em'].dt.date.dropna().unique(), reverse=True)
                default_dias = [hoje] if hoje in dias_disponiveis else []
                dias_selecionados = st.multiselect(
                    "Selecione os Dias", 
                    options=dias_disponiveis, 
                    default=default_dias, 
                    format_func=lambda x: x.strftime('%d-%b-%Y'),
                    key="filtro_dias"
                )
            
            with col2_filter:
                meses_disponiveis = sorted(df['Revisado em'].dt.to_period("M").dropna().unique(), reverse=True)
                default_meses = [pd.Period(year=ano_corrente, month=mes_corrente, freq='M')] if pd.Period(year=ano_corrente, month=mes_corrente, freq='M') in meses_disponiveis else []
                meses_selecionados = st.multiselect(
                    "Selecione os Meses", 
                    options=meses_disponiveis, 
                    default=default_meses, 
                    format_func=lambda x: x.strftime('%b-%Y'),
                    key="filtro_meses"
                )


            # Exibindo filtros adicionais para Tipo de Envio, Tipo de Processo e Informação Técnica
            tipos_envio_opcoes = ["Todos"] + sorted(df[~df['Qual o tipo de envio?'].str.contains("CANCELADO", case=False)]['Qual o tipo de envio?'].dropna().unique())
            tipos_processo_opcoes = ["Todos"] + sorted(df['Tipo de Processo'].dropna().unique())
            informacao_tecnica_opcoes = ["Todos"] + sorted(df['Informação Técnica'].dropna().unique())

            # Colocando os filtros de Tipo de Envio, Tipo de Processo e Informação Técnica recuados na coluna 1
            st.markdown("<h3 style='text-align: left;'>Filtros Adicionais</h3>", unsafe_allow_html=True)
            with col1_filter:
                tipos_envio_selecionados = st.multiselect(
                    "Selecione o(s) Tipo(s) de Envio",
                    options=tipos_envio_opcoes,
                    default="Todos"
                )
                tipos_processo_selecionados = st.multiselect(
                    "Selecione o(s) Tipo(s) de Processo",
                    options=tipos_processo_opcoes,
                    default="Todos"
                )
                informacao_tecnica_selecionada = st.multiselect(
                    "Filtrar por Informação Técnica",
                    options=informacao_tecnica_opcoes,
                    default="Todos"
                )

            # Aplicando filtros ao DataFrame, ignorando filtros "Todos"
            if "Todos" not in tipos_envio_selecionados:
                df = df[df['Qual o tipo de envio?'].isin(tipos_envio_selecionados)]
            if "Todos" not in tipos_processo_selecionados:
                df = df[df['Tipo de Processo'].isin(tipos_processo_selecionados)]
            if "Todos" not in informacao_tecnica_selecionada:
                df = df[df['Informação Técnica'].isin(informacao_tecnica_selecionada)]

            # Calcula o total do(s) dia(s) selecionado(s)
            df_dias_selecionados = df[df['Carimbo de data/hora'].dt.date.isin(dias_selecionados)]
            total_dia = df_dias_selecionados.shape[0]

            # Calcula o total do(s) mês(es) selecionado(s)
            df_meses_selecionados = df[df['Revisado em'].dt.to_period("M").isin(meses_selecionados)]
            total_mes = df_meses_selecionados.shape[0]

            # Definindo estilo customizado para métricas com múltiplas linhas
            def style_metric_box_multi(box_color, font_color, title, content):
                return f"""
                    <div style="background-color:{box_color}; padding:10px; border-radius:10px; border:2px solid #ddd;">
                        <h4 style="color:{font_color}; text-align:center;">{title}</h4>
                        <div style="color:{font_color}; text-align:center; font-size:18px;">
                            {content}
                        </div>
                    </div>
                """

            # Renderizando métricas de total de revisões diárias e mensais com estilo e cores ajustadas
            st.markdown("<h3 style='text-align: center;'>Totais de Revisões Selecionadas</h3>", unsafe_allow_html=True)
            col1_total, col2_total = st.columns(2)

            with col1_total:
                st.markdown(style_metric_box_multi("#66BB6A", "black", "Total de Revisões do Dia(s) Selecionado(s)", total_dia), unsafe_allow_html=True)

            with col2_total:
                st.markdown(style_metric_box_multi("#D8F0D8", "black", "Total de Revisões do Mês(es) Selecionado(s)", total_mes), unsafe_allow_html=True)

            # Exibindo o total de revisões por cada revisor para o dia e para o mês
            # Calculando os totais revisados por cada revisor no período selecionado
            totais_por_revisor_dia = df_dias_selecionados.groupby("Revisado por").size()
            totais_por_revisor_mes = df_meses_selecionados.groupby("Revisado por").size()

            # Gerando o conteúdo formatado para exibição em uma única string
            conteudo_dia = "<br>".join([f"{revisor}: {total}" for revisor, total in totais_por_revisor_dia.items()])
            conteudo_mes = "<br>".join([f"{revisor}: {total}" for revisor, total in totais_por_revisor_mes.items()])

            # Exibindo as métricas de revisões por revisor para o dia e para o mês no mesmo estilo
            st.markdown("<h3 style='text-align: center;'>Totais de Revisões por Revisor</h3>", unsafe_allow_html=True)
            col_revisor_dia, col_revisor_mes = st.columns(2)

            with col_revisor_dia:
                st.markdown(style_metric_box_multi("#FFE082", "black", "Total Revisado por Revisor (Dia)", conteudo_dia), unsafe_allow_html=True)

            with col_revisor_mes:
                st.markdown(style_metric_box_multi("#FFECB3", "black", "Total Revisado por Revisor (Mês)", conteudo_mes), unsafe_allow_html=True)

            # Configura estilo e layout dos gráficos
            st.markdown("<h3 style='text-align: center;'>Quadro de Revisões</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)




            # Definição de cores e tipos de envio com os nomes simplificados, utilizando a paleta Tealgrn
            cores = ['#66CDAA', '#98FB98', '#00FA9A'] 
            tipos_envio = [
                '1º envio (Primeira vez que o Parecer está sendo enviado para revisão)',
                'Prioridades (Tarja amarela no Cerberus, LP, Lpper, LI, LIO, primeira LO, LRO, LA, AE, ATO ou solicitação da supervisão)',
                'Reenvio após correções (Parecer que já foi revisado e feitas as correções por você)'
            ]
            nomes_legenda = ["1° Envio", "Prioridades", "Reenvios"]

            # Gráfico de Enviados do Dia
            with col1:
                st.markdown("<div class='custom-col'>", unsafe_allow_html=True)
                st.subheader("Revisões do Dia")

                # Filtragem do DataFrame com base nos dias selecionados
                df_dias_selecionados = df[df['Revisado em'].dt.date.isin(dias_selecionados)]
                
                # Verifica se há dados para o(s) dia(s) selecionado(s)
                if df_dias_selecionados.empty:
                    st.warning("A base não contém dados para o dia selecionado. Selecione outro(s) dia(s).")
                else:
                    # Agrupa os dados por tipo de envio e analista
                    revisoes_dia = df_dias_selecionados.groupby(['Revisado por', 'Qual o tipo de envio?']).size().unstack(fill_value=0).reset_index()
                    
                    # Garante que as colunas dos tipos de envio estão presentes com os nomes completos
                    for tipo in tipos_envio:
                        if tipo not in revisoes_dia.columns:
                            revisoes_dia[tipo] = 0
                    
                    # Cálculo das colunas de Totais e Pareto
                    revisoes_dia['Total'] = revisoes_dia[tipos_envio].sum(axis=1)
                    revisoes_dia = revisoes_dia.sort_values(by='Total', ascending=False)  # Ordena do maior para o menor
                    revisoes_dia['Cumulativo'] = revisoes_dia['Total'].cumsum()
                    revisoes_dia['Porcentagem'] = 100 * revisoes_dia['Cumulativo'] / revisoes_dia['Total'].sum()

                    # Obtém o valor máximo para ajustar o eixo y
                    max_y = revisoes_dia[tipos_envio].values.max() * 1.7

                    # Criação do gráfico de Pareto
                    fig_revisoes_dia = go.Figure()

                    # Calcula o total de cada tipo de envio
                    totais_por_tipo_envio_dia = revisoes_dia[tipos_envio].sum().to_dict()

                    # Adiciona barras para cada tipo de envio com os nomes simplificados e rótulos de dados
                    for tipo_envio, cor, nome_legenda in zip(tipos_envio, cores, nomes_legenda):
                        total_tipo_envio = int(totais_por_tipo_envio_dia[tipo_envio])  # Obtém o total e converte para inteiro
                        fig_revisoes_dia.add_trace(go.Bar(
                            x=revisoes_dia['Revisado por'],
                            y=revisoes_dia[tipo_envio],
                            name=f"{nome_legenda} ({total_tipo_envio})",  # Inclui o total na legenda
                            marker_color=cor,
                            yaxis='y1',
                            text=revisoes_dia[tipo_envio],  # Rótulo de dados
                            textposition='auto'  # Exibe rótulos automaticamente
                        ))

                    # Linha para a soma de "1º Envio" e "Prioridades" em amarelo pontilhado
                    fig_revisoes_dia.add_trace(go.Scatter(
                        x=revisoes_dia['Revisado por'],
                        y=revisoes_dia[tipos_envio[0]] + revisoes_dia[tipos_envio[1]],
                        mode='lines+markers+text',
                        text=revisoes_dia[tipos_envio[0]] + revisoes_dia[tipos_envio[1]],
                        line=dict(color='orange', width=3, dash='dash'),
                        textposition='top center',
                        name="Total 1º Envio e Prioridades",
                        yaxis='y1',
                        textfont=dict(color='orange')
                    ))

                    # Linha para o total geral de revisões
                    fig_revisoes_dia.add_trace(go.Scatter(
                        x=revisoes_dia['Revisado por'],
                        y=revisoes_dia['Total'],
                        mode='lines+markers+text',
                        text=revisoes_dia['Total'],
                        line=dict(color='green', width=3, dash='dash'),
                        textposition='top center',
                        name="Total Geral",
                        yaxis='y1',
                        textfont=dict(color='green')
                    ))

                    # Linha de Pareto
                    fig_revisoes_dia.add_trace(go.Scatter(
                        x=revisoes_dia['Revisado por'],
                        y=revisoes_dia['Porcentagem'],
                        mode='lines+markers+text',
                        text=[f'{p:.1f}% ({c})' for p, c in zip(revisoes_dia['Porcentagem'], revisoes_dia['Cumulativo'])],
                        line=dict(color='blue', width=0.5, dash='dash'),
                        textposition='top center',
                        name="Acumulado (%)",
                        yaxis='y2',
                        textfont=dict(color='blue')
                    ))

                    # Configuração do layout do gráfico de Revisões do Dia com ajuste do eixo y
                    fig_revisoes_dia.update_layout(
                        title='Revisões dos Dias Selecionados',
                        xaxis_title='Revisado por',
                        yaxis=dict(title='Quantidade', side='left', range=[0, max_y]),
                        yaxis2=dict(title='Porcentagem Cumulativa', overlaying='y', side='right', range=[0, 110]),
                        barmode='stack',
                        width=700,
                        height=400,
                        legend=dict(orientation='h', yanchor='bottom', y=-0.55, xanchor='center', x=0.5)
                    )
                    st.plotly_chart(fig_revisoes_dia, use_container_width=True)

                    st.markdown("</div>", unsafe_allow_html=True)


            # Gráfico de Revisões do Mês
            with col2:
                st.markdown("<div class='custom-col'>", unsafe_allow_html=True)
                st.subheader("Revisões do Mês")



            # Gráfico de Revisões do Mês
            with col2:
                # Filtragem do DataFrame com base nos meses selecionados
                df_meses_selecionados = df[df['Revisado em'].dt.to_period("M").isin(meses_selecionados)]
                
                # Verifica se há dados para o(s) mês(es) selecionado(s)
                if df_meses_selecionados.empty:
                    st.warning("A base não contém dados para o mês selecionado. Selecione outro(s) mês(es).")
                else:
                    # Agrupa os dados por tipo de envio e analista
                    revisoes_mes = df_meses_selecionados.groupby(['Revisado por', 'Qual o tipo de envio?']).size().unstack(fill_value=0).reset_index()
                    
                    # Garante que as colunas dos tipos de envio estão presentes com os nomes completos
                    for tipo in tipos_envio:
                        if tipo not in revisoes_mes.columns:
                            revisoes_mes[tipo] = 0
                    
                    # Cálculo das colunas de Totais e Pareto
                    revisoes_mes['Total'] = revisoes_mes[tipos_envio].sum(axis=1)
                    revisoes_mes = revisoes_mes.sort_values(by='Total', ascending=False)  # Ordena do maior para o menor
                    revisoes_mes['Cumulativo'] = revisoes_mes['Total'].cumsum()
                    revisoes_mes['Porcentagem'] = 100 * revisoes_mes['Cumulativo'] / revisoes_mes['Total'].sum()

                    # Obtém o valor máximo para ajustar o eixo y
                    max_y = revisoes_mes[tipos_envio].values.max() * 2

                    # Calcula o total de cada tipo de envio
                    totais_por_tipo_envio = revisoes_mes[tipos_envio].sum().to_dict()

                    # Criação do gráfico de Pareto para o mês
                    fig_revisoes_mes = go.Figure()

                    # Adiciona barras para cada tipo de envio com os nomes simplificados e valores totais na legenda
                    for tipo_envio, cor, nome_legenda in zip(tipos_envio, cores, nomes_legenda):
                        total_tipo_envio = int(totais_por_tipo_envio[tipo_envio])  # Obtém o total e converte para inteiro
                        fig_revisoes_mes.add_trace(go.Bar(
                            x=revisoes_mes['Revisado por'],
                            y=revisoes_mes[tipo_envio],
                            name=f"{nome_legenda} ({total_tipo_envio})",  # Inclui o total na legenda
                            marker_color=cor,
                            yaxis='y1',
                            text=revisoes_mes[tipo_envio],  # Rótulo de dados
                            textposition='auto'  # Exibe rótulos automaticamente
                        ))

                    # Linha para a soma de "1º Envio" e "Prioridades" em amarelo pontilhado
                    fig_revisoes_mes.add_trace(go.Scatter(
                        x=revisoes_mes['Revisado por'],
                        y=revisoes_mes[tipos_envio[0]] + revisoes_mes[tipos_envio[1]],
                        mode='lines+markers+text',
                        text=revisoes_mes[tipos_envio[0]] + revisoes_mes[tipos_envio[1]],
                        line=dict(color='orange', width=3, dash='dash'),
                        textposition='top center',
                        name="Total 1º Envio e Prioridades",
                        yaxis='y1',
                        textfont=dict(color='orange')
                    ))

                    # Linha para o total geral de revisões
                    fig_revisoes_mes.add_trace(go.Scatter(
                        x=revisoes_mes['Revisado por'],
                        y=revisoes_mes['Total'],
                        mode='lines+markers+text',
                        text=revisoes_mes['Total'],
                        line=dict(color='green', width=3, dash='dash'),
                        textposition='top center',
                        name="Total Geral",
                        yaxis='y1',
                        textfont=dict(color='green')
                    ))

                    # Linha de Pareto
                    fig_revisoes_mes.add_trace(go.Scatter(
                        x=revisoes_mes['Revisado por'],
                        y=revisoes_mes['Porcentagem'],
                        mode='lines+markers+text',
                        text=[f'{p:.1f}% ({c})' for p, c in zip(revisoes_mes['Porcentagem'], revisoes_mes['Cumulativo'])],
                        line=dict(color='blue', width=0.5, dash='dash'),
                        textposition='top center',
                        name="Acumulado (%)",
                        yaxis='y2',
                        textfont=dict(color='blue')
                    ))

                    # Configuração do layout do gráfico de Revisões do Mês
                    fig_revisoes_mes.update_layout(
                        title='Revisões dos Meses Selecionados',
                        xaxis_title='Revisado por',
                        yaxis=dict(title='Quantidade', side='left', range=[0, max_y]),
                        yaxis2=dict(title='Porcentagem Cumulativa', overlaying='y', side='right', range=[0, 110]),
                        barmode='stack',
                        width=700,
                        height=400,
                        legend=dict(orientation='h', yanchor='bottom', y=-0.55, xanchor='center', x=0.5)
                    )
                    st.plotly_chart(fig_revisoes_mes, use_container_width=True)

                
                st.markdown("</div>", unsafe_allow_html=True)


# Gráficos de Revisões Diárias e Mensais por Tipo de Processo com estilo consistente

            ## Função para extrair o tipo de processo
            def extrair_tipo_processo(numero_processo):
                # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
                match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
                if match:
                    sigla = match.group(1)
                    # Verifica se a sigla extraída é uma das especificadas
                    if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                        return sigla
                return 'Outros'

            # Adicionando coluna "Tipo de Processo" se ainda não existir
            if 'Tipo de Processo' not in df.columns:
                df['Tipo de Processo'] = df['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].apply(extrair_tipo_processo)

            # Cores e tipos para o gráfico
            cores_processo = [
                '#66CDAA', '#98FB98', '#00FA9A', '#d4f0e1', '#a8e6cf', '#81cfa9', '#b3e2d4', '#cce5ff', '#99d3ff', 
                '#c3e8b0', '#fef9d7', '#fff7c1', '#fbf3d0', '#d2f1e1', '#9ad1e6', '#b5e0cc'
            ]

            # Gráficos Diários e Mensais por Tipo de Processo com ordenação e totais na legenda
            for periodo, (df_tipo_processo, filtro_periodo, titulo) in {
                'dia': (df[df['Revisado em'].dt.date.isin(dias_selecionados)], col1, "Revisões Diárias por Tipo de Processo"),
                'mes': (df[df['Revisado em'].dt.to_period("M").isin(meses_selecionados)], col2, "Revisões Mensais por Tipo de Processo")
            }.items():

                with filtro_periodo:
                    st.markdown("<div class='custom-col'>", unsafe_allow_html=True)
                    st.subheader(titulo)

                    df_tipo_processo = df_tipo_processo.groupby(['Revisado por', 'Tipo de Processo']).size().unstack(fill_value=0).reset_index()
                    if not df_tipo_processo.empty:
                        # Calcula totais e organiza ordem
                        df_tipo_processo['Total'] = df_tipo_processo.select_dtypes(include=[int, float]).sum(axis=1)
                        df_tipo_processo = df_tipo_processo.sort_values(by='Total', ascending=False)
                        df_tipo_processo['Cumulativo'] = df_tipo_processo['Total'].cumsum()
                        df_tipo_processo['Porcentagem'] = 100 * df_tipo_processo['Cumulativo'] / df_tipo_processo['Total'].sum()

                        # Calcular total de cada tipo de processo para exibir na legenda, formatando para remover o decimal
                        totais_por_tipo = df_tipo_processo.select_dtypes(include=[int, float]).sum().to_dict()

                        # Configuração do gráfico
                        fig_tipo_processo = go.Figure()
                        for tipo_processo, cor in zip(
                                sorted(df_tipo_processo.columns[1:-3], key=lambda x: totais_por_tipo[x], reverse=True),
                                cores_processo):
                            fig_tipo_processo.add_trace(go.Bar(
                                x=df_tipo_processo['Revisado por'],
                                y=df_tipo_processo[tipo_processo],
                                name=f"{tipo_processo} ({int(totais_por_tipo[tipo_processo])})",  # Exibindo apenas o valor inteiro na legenda
                                marker_color=cor,
                                yaxis='y1',
                                text=df_tipo_processo[tipo_processo],
                                textposition='auto'
                            ))

                        # Linha de Pareto
                        fig_tipo_processo.add_trace(go.Scatter(
                            x=df_tipo_processo['Revisado por'],
                            y=df_tipo_processo['Porcentagem'],
                            mode='lines+markers+text',
                            text=[f'{p:.1f}%' for p in df_tipo_processo['Porcentagem']],
                            line=dict(color='blue', width=0.5, dash='dash'),
                            textposition='top center',
                            name="Acumulado (%)",
                            yaxis='y2',
                            textfont=dict(color='blue')
                        ))

                        # Layout do gráfico
                        fig_tipo_processo.update_layout(
                            title=titulo,
                            xaxis_title='Revisado por',
                            yaxis=dict(title='Quantidade', side='left', range=[0, df_tipo_processo[df_tipo_processo.columns[1:-3]].values.max() * 1.7]),
                            yaxis2=dict(title='Porcentagem Cumulativa', overlaying='y', side='right', range=[0, 110]),
                            barmode='stack',
                            width=700,
                            height=400,
                            legend=dict(orientation='h', yanchor='bottom', y=-0.55, xanchor='center', x=0.5)
                        )
                        st.plotly_chart(fig_tipo_processo, use_container_width=True)
                    else:
                        st.warning(f"A base não contém dados para o {periodo} selecionado.")


            # Seção de Tabelas com estilo condicional
            st.markdown("<hr style='border: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            
            # Função para aplicar o estilo condicional
            def aplicar_estilos(df):
                styles = []
                for index, row in df.iterrows():
                    if pd.isna(row['Revisado em']):
                        styles.append(['background-color: #B0B0B0; color: #000000'] * len(row))  # Cor para "Não Revisados"
                    elif "Prioridades" in str(row["Qual o tipo de envio?"]):
                        styles.append(['background-color: #2E8B57; color: #FFFFFF'] * len(row))  # Cor para "Prioridade"
                    else:
                        styles.append([''] * len(row))
                return pd.DataFrame(styles, index=df.index, columns=df.columns)

            # Tabela de processos do dia
            st.markdown("<h3 style='text-align: center;'>Tabela de Processos do Dia Selecionado</h3>", unsafe_allow_html=True)
            df_dia_selecionados = df[df['Revisado em'].dt.date.isin(dias_selecionados)]
            styled_df_dia = df_dia_selecionados.style.apply(aplicar_estilos, axis=None)
            st.dataframe(styled_df_dia, use_container_width=True)

            # Tabela de processos do mês
            st.markdown("<h3 style='text-align: center;'>Tabela de Processos do Mês Selecionado</h3>", unsafe_allow_html=True)
            df_mes_selecionados = df[df['Revisado em'].dt.to_period("M").isin(meses_selecionados)]
            styled_df_mes = df_mes_selecionados.style.apply(aplicar_estilos, axis=None)
            st.dataframe(styled_df_mes, use_container_width=True)

        else:
            st.error("O arquivo está vazio ou ocorreu um erro ao processar os dados.")
    else:
        st.warning("""
            Carregue a base no Sidebar ao lado.

            ⬅️   Por favor, faça o upload do arquivo CSV - Revisão de Pareceres (respostas) 
            disponível em: https://docs.google.com/spreadsheets/d/18juQmpGe86MRr4uXTxDiJC1wAPQXXqJs1SgMoFpFC2g/edit?gid=1572677783#gid=1572677783.
            """)

# Função para a análise de tempos de revisão
def analisar_tempos_revisao(df):
    st.markdown(
        "<h1 style='text-align: center; color: #98FF98; font-size: 42px; font-weight: bold; text-decoration: underline;'>Análise de Tempo de Revisão</h1>",
        unsafe_allow_html=True
    )

    # Remover processos com valores ausentes em 'Revisado em' ou 'Carimbo de data/hora'
    df = df.dropna(subset=['Revisado em', 'Carimbo de data/hora'])

    # Converter colunas para apenas data, assumindo formato dia/mês/ano
    df['Revisado em'] = pd.to_datetime(df['Revisado em'], dayfirst=True, errors='coerce').dt.date
    df['Carimbo de data/hora'] = pd.to_datetime(df['Carimbo de data/hora'], dayfirst=True, errors='coerce').dt.date

    # Remover linhas com datas inválidas
    df = df.dropna(subset=['Revisado em', 'Carimbo de data/hora'])

    # Calcular o tempo de revisão em dias
    df['Tempo_Em_Revisao'] = df.apply(lambda row: (row['Revisado em'] - row['Carimbo de data/hora']).days 
                                    if row['Revisado em'] >= row['Carimbo de data/hora'] else 0, axis=1)

    # Verificar se existem dados válidos para 'Tempo_Em_Revisao'
    if df['Tempo_Em_Revisao'].notnull().any():
        # Colocar os gráficos de histograma, boxplot, média semanal e média mensal em duas colunas
        col1, col2 = st.columns([3, 1])

        with col1:
            # Histograma do Tempo de Revisão
            st.subheader('Distribuição do Tempo de Revisão')
            fig_hist = px.histogram(df, x='Tempo_Em_Revisao', nbins=30,
                                    title='Distribuição do Tempo de Revisão (dias)',
                                    labels={'Tempo_Em_Revisao': 'Tempo de Revisão (dias)'},
                                    color_discrete_sequence=['#66BB6A'])
            fig_hist.update_layout(bargap=0.1)

            # Calcular o total de revisões para cada intervalo do histograma
            total_revisoes = df['Tempo_Em_Revisao'].value_counts().sort_index()

            # Adicionar a linha de total sobre o histograma
            fig_hist.add_scatter(
                x=total_revisoes.index,
                y=total_revisoes.values,
                mode='lines+markers+text',
                name='Total por Intervalo',
                text=total_revisoes.values,
                texttemplate='<b><span style="color: darkgoldenrod;">%{text}</span></b>',  # Valores coloridos em amarelo escuro
                textposition='top center',
                line=dict(color='darkgoldenrod', width=3)
            )
            
            # Atualizar o layout para ajustar a legenda e garantir a visibilidade dos elementos
            fig_hist.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5)  # Legenda na parte inferior
            )
            
            # Exibir o gráfico atualizado
            st.plotly_chart(fig_hist, use_container_width=True)


            # Gráfico de Linha Temporal (Média do Tempo de Revisão por Semana)
            df['Ano_Semana'] = pd.to_datetime(df['Carimbo de data/hora'], dayfirst=True, errors='coerce').dt.to_period("W").apply(lambda r: r.start_time)
            tempo_medio_semanal = df.groupby('Ano_Semana')['Tempo_Em_Revisao'].mean().round(2).reset_index()
            tempo_medio_semanal['Ano_Semana_Label'] = tempo_medio_semanal['Ano_Semana'].dt.strftime('S%V-%m-%y')  # Formato SXX-MM-AA

            st.subheader('Média do Tempo de Revisão por Semana')
            fig_semanal = go.Figure()
            fig_semanal.add_trace(go.Scatter(x=tempo_medio_semanal['Ano_Semana_Label'], y=tempo_medio_semanal['Tempo_Em_Revisao'],
                                             mode='lines+markers+text', name='Média (linha)', text=tempo_medio_semanal['Tempo_Em_Revisao'],
                                             texttemplate='<b>%{text:.2f}</b>',  # Exibe valores da linha em amarelo e destacado
                                             # Configuração de fonte e posição do texto
                                             textfont=dict(size=14, color='gold'),
                                             textposition='top center',  # Coloca o texto mais próximo da borda superior
                                             line=dict(color='darkgoldenrod', width=2)))
            fig_semanal.add_trace(go.Bar(x=tempo_medio_semanal['Ano_Semana_Label'], y=tempo_medio_semanal['Tempo_Em_Revisao'],
                                         name='Média (barras)', marker_color='#66BB6A'))
            fig_semanal.update_layout(
                title='Média do Tempo de Revisão por Semana', 
                xaxis_title='Semana', 
                yaxis_title='Tempo de Revisão (dias)',
                legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_semanal, use_container_width=True)

        with col2:
            # Boxplot do Tempo de Revisão
            st.subheader('Boxplot do Tempo de Revisão')
            fig_box = px.box(df, y='Tempo_Em_Revisao',
                             title='Boxplot do Tempo de Revisão (dias)',
                             labels={'Tempo_Em_Revisao': 'Tempo de Revisão (dias)'},
                             color_discrete_sequence=['#81C784'])
            fig_box.update_layout(
                height=400,  # Reduzindo o tamanho do gráfico
                legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_box, use_container_width=True)

            # Gráfico de Linha Temporal (Média de Tempo de Revisão por Mês, em formato horizontal)
            df['Ano_Mes'] = pd.to_datetime(df['Carimbo de data/hora'], dayfirst=True, errors='coerce').dt.to_period("M").apply(lambda r: r.start_time)
            tempo_medio_mensal = df.groupby('Ano_Mes')['Tempo_Em_Revisao'].mean().round(2).reset_index()
            tempo_medio_mensal['Ano_Mes_Label'] = tempo_medio_mensal['Ano_Mes'].dt.strftime('%m-%y')  # Formato MM-AA

            st.subheader('Média do Tempo de Revisão por Mês')
            fig_mes = go.Figure()
            fig_mes.add_trace(go.Bar(y=tempo_medio_mensal['Ano_Mes_Label'], x=tempo_medio_mensal['Tempo_Em_Revisao'],
                                     name='Média (barras)', orientation='h', marker_color='#66BB6A'))
            fig_mes.add_trace(go.Scatter(y=tempo_medio_mensal['Ano_Mes_Label'], x=tempo_medio_mensal['Tempo_Em_Revisao'],
                                         mode='lines+markers+text', name='Média (linha)', text=tempo_medio_mensal['Tempo_Em_Revisao'],
                                         texttemplate='<b>%{text:.2f}</b>',  # Exibe valores da linha em amarelo e destacado
                                         textfont=dict(size=14, color='gold'),
                                         textposition='top center',  # Coloca o texto mais próximo da borda superior
                                         line=dict(color='darkgoldenrod', width=3)))
            fig_mes.update_layout(
                title='Média do Tempo de Revisão por Mês', 
                yaxis_title='Mês', 
                xaxis_title='Tempo de Revisão (dias)',
                height=400, 
                xaxis=dict(autorange="reversed"),
                legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_mes, use_container_width=True)

        # Gráfico de Média de Tempo de Revisão por Tipo de Processo
        st.subheader('Média do Tempo de Revisão por Tipo de Processo')
        tempo_medio_processo = df.groupby('Tipo de Processo')['Tempo_Em_Revisao'].mean().round(2).reset_index()
        fig_processo = px.bar(tempo_medio_processo, x='Tipo de Processo', y='Tempo_Em_Revisao', color='Tipo de Processo',
                              title='Média do Tempo de Revisão por Tipo de Processo',
                              labels={'Tempo_Em_Revisao': 'Tempo Médio de Revisão (dias)'})
        fig_processo.update_traces(marker=dict(line=dict(width=1, color='darkgoldenrod')))
        st.plotly_chart(fig_processo, use_container_width=True)

        # Gráfico de Média de Tempo de Revisão por Tipo de Empreendimento
        st.subheader('Média do Tempo de Revisão por Tipo de Empreendimento')
                # Gráfico de Média de Tempo de Revisão por Tipo de Empreendimento
        tempo_medio_empreendimento = df.groupby('Tipo de empreendimento')['Tempo_Em_Revisao'].mean().round(2).reset_index()
        fig_empreendimento = px.bar(tempo_medio_empreendimento, x='Tipo de empreendimento', y='Tempo_Em_Revisao', color='Tipo de empreendimento',
                                    title='Média do Tempo de Revisão por Tipo de Empreendimento',
                                    labels={'Tempo_Em_Revisao': 'Tempo Médio de Revisão (dias)'},
                                    color_discrete_sequence=px.colors.sequential.Emrld)
        fig_empreendimento.update_traces(marker=dict(line=dict(width=1, color='darkgoldenrod')))
        st.plotly_chart(fig_empreendimento, use_container_width=True)

        # Gráfico de Média de Tempo de Revisão por Tipo de Processo
        st.subheader('Média do Tempo de Revisão por Tipo de Processo')
        tempo_medio_processo = df.groupby('Tipo de Processo')['Tempo_Em_Revisao'].mean().round(2).reset_index()
        tempo_medio_processo = tempo_medio_processo.sort_values(by='Tempo_Em_Revisao', ascending=False)
        fig_processo = px.bar(tempo_medio_processo, x='Tipo de Processo', y='Tempo_Em_Revisao', color='Tipo de Processo',
                                title='Média do Tempo de Revisão por Tipo de Processo',
                                labels={'Tempo_Em_Revisao': 'Tempo Médio de Revisão (dias)'})
        fig_processo.update_traces(text=tempo_medio_processo['Tempo_Em_Revisao'], textposition='outside')
        fig_processo.update_layout(showlegend=False)
        st.plotly_chart(fig_processo, use_container_width=True)

        # Gráfico de Média de Tempo de Revisão por Tipo de Empreendimento
        st.subheader('Média do Tempo de Revisão por Tipo de Empreendimento')
        tempo_medio_empreendimento = df.groupby('Tipo de empreendimento')['Tempo_Em_Revisao'].mean().round(2).reset_index()
        tempo_medio_empreendimento = tempo_medio_empreendimento.sort_values(by='Tempo_Em_Revisao', ascending=False)
        fig_empreendimento = px.bar(tempo_medio_empreendimento, x='Tipo de empreendimento', y='Tempo_Em_Revisao', color='Tipo de empreendimento',
                                    title='Média do Tempo de Revisão por Tipo de Empreendimento',
                                    labels={'Tempo_Em_Revisao': 'Tempo Médio de Revisão (dias)'},
                                    color_discrete_sequence=px.colors.sequential.Emrld)
        fig_empreendimento.update_traces(text=tempo_medio_empreendimento['Tempo_Em_Revisao'], textposition='outside')
        fig_empreendimento.update_layout(showlegend=False)
        st.plotly_chart(fig_empreendimento, use_container_width=True)

        # Criar uma função para simplificar os rótulos
        def simplificar_tipo_envio(tipo_envio):
            if "1º envio" in tipo_envio:
                return "1º Envio"
            elif "Reenvio após correções" in tipo_envio:
                return "Reenvio"
            elif "Prioridades" in tipo_envio:
                return "Prioridades"
            return tipo_envio  # Caso não corresponda a nenhum dos padrões, manter o original

        # Aplicar a função para simplificar os rótulos
        df['Tipo de Envio Simplificado'] = df['Qual o tipo de envio?'].apply(simplificar_tipo_envio)

        # Gráfico de Média de Tempo de Revisão por Tipo de Envio
        st.subheader('Média do Tempo de Revisão por Tipo de Envio')
        tempo_medio_envio = df.groupby('Tipo de Envio Simplificado')['Tempo_Em_Revisao'].mean().round(2).reset_index()
        tempo_medio_envio = tempo_medio_envio.sort_values(by='Tempo_Em_Revisao', ascending=False)
        fig_envio = px.bar(tempo_medio_envio, x='Tipo de Envio Simplificado', y='Tempo_Em_Revisao', color='Tipo de Envio Simplificado',
                        title='Média do Tempo de Revisão por Tipo de Envio',
                        labels={'Tempo_Em_Revisao': 'Tempo Médio de Revisão (dias)'},
                        color_discrete_sequence=px.colors.sequential.Purp)

        # Exibir os valores nas barras
        fig_envio.update_traces(text=tempo_medio_envio['Tempo_Em_Revisao'], textposition='outside')

        # Ajustar layout
        fig_envio.update_layout(
            showlegend=False,
            xaxis=dict(tickfont=dict(size=12)),
            margin=dict(t=50, b=100)
        )
        st.plotly_chart(fig_envio, use_container_width=True)


        # Gráfico de Média de Tempo de Revisão por Informação Técnica
        st.subheader('Média do Tempo de Revisão por Informação Técnica')
        tempo_medio_info_tecnica = df.groupby('Informação Técnica')['Tempo_Em_Revisao'].mean().round(2).reset_index()
        tempo_medio_info_tecnica = tempo_medio_info_tecnica.sort_values(by='Tempo_Em_Revisao', ascending=False)
        fig_info_tecnica = px.bar(tempo_medio_info_tecnica, x='Informação Técnica', y='Tempo_Em_Revisao', color='Informação Técnica',
                                    title='Média do Tempo de Revisão por Informação Técnica',
                                    labels={'Tempo_Em_Revisao': 'Tempo Médio de Revisão (dias)'},
                                    color_discrete_sequence=px.colors.sequential.Sunset)
        fig_info_tecnica.update_traces(text=tempo_medio_info_tecnica['Tempo_Em_Revisao'], textposition='outside')
        fig_info_tecnica.update_layout(showlegend=False)
        st.plotly_chart(fig_info_tecnica, use_container_width=True)

        # Tabela de Análise dos Tempos de Revisão
        st.subheader('Tabela de Análise dos Tempos de Revisão')
        st.write(df[['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)', 
                     'Codigo_Processo', 'Analista (você)', 'Revisado por', 'Carimbo de data/hora', 
                     'Revisado em', 'Tempo_Em_Revisao', 'Tipo de Processo', 'Tipo de empreendimento', 
                     'Qual o tipo de envio?', 'Informação Técnica']])
    else:
        st.warning("Não há dados suficientes para calcular os tempos de revisão.")



def analise_tempos():
    # Carrega os dados do arquivo
    df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        # Filtrar o DataFrame para remover processos contendo qualquer variação de "cancelado" ou "cancelar"
        df = df[~df['Qual o tipo de envio?'].str.contains(r'cancelado|cancelar', case=False, na=False)]

        # Função para extrair o tipo de processo
        def extrair_tipo_processo(numero_processo):
            # Usa uma expressão regular que captura qualquer uma das variações de separador ou sem separador
            match = re.search(r'TEC(?:[/-]*|)([A-Z]{2,5})', str(numero_processo))
            if match:
                sigla = match.group(1)
                # Verifica se a sigla extraída é uma das especificadas
                if sigla in ['LP', 'LPpe', 'LI', 'LIO', 'LO', 'LRO', 'LA', 'AE', 'ATO', 'LS', 'RLO', 'RLS', 'LPpr']:
                    return sigla
            return 'Outros'

        # Aplicando a função para criar a coluna 'Tipo de Processo'
        df['Tipo de Processo'] = df['Número do Processo a ser revisado (Caso seja Reenvio, coloque a Inicial do revisor-CORRIGIDO-NúmeroDoProcesso)'].apply(extrair_tipo_processo)

        # Garantir que 'Carimbo de data/hora' está em formato datetime
        df['Carimbo de data/hora'] = pd.to_datetime(df['Carimbo de data/hora'], dayfirst=True, errors='coerce')
        df['ANO_envio'] = df['Carimbo de data/hora'].dt.year
        df['MÊS_envio'] = df['Carimbo de data/hora'].dt.month
        df['SEMANA_envio'] = df['Carimbo de data/hora'].dt.isocalendar().week

        # Aplicar função de criação do código do processo
        df = criar_codigo_processo(df)

        # Configuração das opções de filtros
        anos_disponiveis_envio = ["Todos"] + [ano for ano in sorted(df['ANO_envio'].unique(), reverse=True) if ano != 0]
        meses_disponiveis_envio = ["Todos"] + [mes for mes in sorted(df['MÊS_envio'].unique(), reverse=True) if mes != 0]
        semanas_disponiveis_envio = [("Todos", "Todos", "Todos")] + formatar_semanas(df)
        ano_default = [datetime.now().year] if datetime.now().year in anos_disponiveis_envio else ["Todos"]
        mes_default = [datetime.now().month] if datetime.now().month in meses_disponiveis_envio else ["Todos"]
        semana_default = [("Todos", "Todos", "Todos")]

        # Sidebar para seleção de Ano, Mês e Semana
        ano = st.sidebar.multiselect("SELECIONE O ANO", options=anos_disponiveis_envio, default=ano_default)
        mes = st.sidebar.multiselect("SELECIONE O MÊS", options=meses_disponiveis_envio, default=mes_default)
        semana = st.sidebar.multiselect(
            "SELECIONE A SEMANA", 
            options=semanas_disponiveis_envio, 
            default=semana_default, 
            format_func=lambda x: x[2] if isinstance(x, tuple) else str(x)
        )

        # Aplicando os filtros de ano, mês e semana ao DataFrame
        df_selection = df
        if "Todos" not in ano:
            df_selection = df_selection[df_selection['ANO_envio'].isin(ano)]
        if "Todos" not in mes:
            df_selection = df_selection[df_selection['MÊS_envio'].isin(mes)]
        if ("Todos", "Todos", "Todos") not in semana:
            semanas_selecionadas = [s[1] for s in semana if isinstance(s, tuple)]
            df_selection = df_selection[df_selection['SEMANA_envio'].isin(semanas_selecionadas)]

        # Filtros de Tipo de Envio, Tipo de Processo e Informação Técnica na interface principal
        tipo_envio_opcoes = ["Todos"] + df_selection['Qual o tipo de envio?'].unique().tolist()
        tipo_processo_opcoes = ["Todos"] + df_selection['Tipo de Processo'].unique().tolist()
        informacao_tecnica_opcoes = ["Todos"] + df_selection['Informação Técnica'].unique().tolist()

        tipo_envio_selecionado = st.multiselect("Filtrar por Tipo de Envio", options=tipo_envio_opcoes, default="Todos")
        tipo_processo_selecionado = st.multiselect("Filtrar por Tipo de Processo", options=tipo_processo_opcoes, default="Todos")
        informacao_tecnica_selecionada = st.multiselect("Filtrar por Informação Técnica", options=informacao_tecnica_opcoes, default="Todos")

        # Aplicar filtros ao DataFrame final
        if "Todos" not in tipo_envio_selecionado:
            df_selection = df_selection[df_selection['Qual o tipo de envio?'].isin(tipo_envio_selecionado)]
        if "Todos" not in tipo_processo_selecionado:
            df_selection = df_selection[df_selection['Tipo de Processo'].isin(tipo_processo_selecionado)]
        if "Todos" not in informacao_tecnica_selecionada:
            df_selection = df_selection[df_selection['Informação Técnica'].isin(informacao_tecnica_selecionada)]

        # Chamar a função de análise de tempos de revisão
        analisar_tempos_revisao(df_selection)
    else:
        st.warning("Carregue a base no Sidebar ao lado.")

if __name__ == "__main__":
    main()
