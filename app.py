import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Gerador PROCV Dinâmico", layout="wide")

st.title("📊 Painel de Análise Dinâmica (PROCV)")
st.markdown("Faça o cruzamento e **escolha na hora** qual gráfico deseja visualizar.")
st.divider()

# --- 1. UPLOAD DE ARQUIVOS ---
col1, col2 = st.columns(2)
with col1:
    arquivo_principal = st.file_uploader("📂 1. Arquivo Principal", type=["xlsx", "xls"], key="main")
with col2:
    arquivo_base = st.file_uploader("📂 2. Base de Dados", type=["xlsx", "xls"], key="base")

if arquivo_principal and arquivo_base:
    try:
        df_main = pd.read_excel(arquivo_principal)
        df_base = pd.read_excel(arquivo_base)
        st.success("Arquivos carregados!")
        st.divider()

        # --- 2. CONFIGURAÇÃO DO CRUZAMENTO ---
        c1, c2 = st.columns(2)
        with c1:
            chave_main = st.selectbox("Coluna Chave (Principal):", df_main.columns)
        with c2:
            chave_base = st.selectbox("Coluna Chave (Base):", df_base.columns)

        cols_disponiveis = [c for c in df_base.columns if c != chave_base]

        # Tenta achar "Serviço" para facilitar
        pre_selecao = [c for c in cols_disponiveis if "serviço" in c.lower()]

        colunas_desejadas = st.multiselect(
            "Quais colunas trazer da Base?",
            options=cols_disponiveis,
            default=pre_selecao if pre_selecao else None
        )

        st.divider()

        if st.button("🚀 Processar Dados", type="primary"):
            if not colunas_desejadas:
                st.warning("Selecione colunas para trazer.")
            else:
                # --- PROCESSAMENTO (MERGE) ---
                cols_to_merge = [chave_base] + colunas_desejadas
                df_resultado = pd.merge(
                    df_main, df_base[cols_to_merge],
                    left_on=chave_main, right_on=chave_base, how='left'
                )

                if chave_main != chave_base and chave_base not in colunas_desejadas:
                    df_resultado = df_resultado.drop(columns=[chave_base])

                # Salva no estado para não perder ao interagir com filtros
                st.session_state['df_resultado'] = df_resultado

    except Exception as e:
        st.error(f"Erro: {e}")

# --- 3. ÁREA DINÂMICA E VISUALIZAÇÃO ---
if 'df_resultado' in st.session_state:
    df = st.session_state['df_resultado']

    st.subheader("📈 Análise Gráfica")

    # Menu de Configuração do Gráfico
    box_col1, box_col2, box_col3 = st.columns(3)

    with box_col1:
        coluna_eixo_x = st.selectbox(
            "O que você quer analisar? (Eixo X)",
            options=df.columns,
            index=len(df.columns) - 1
        )

    with box_col2:
        tipo_grafico = st.selectbox("Tipo de Gráfico:", ["Barras", "Pizza", "Rosca", "Funil"])

    with box_col3:
        qtd_top = st.slider("Mostrar quantos itens? (Top N)", 5, 50, 10)

    # --- PROCESSAMENTO DO GRÁFICO ---
    dados_agrupados = df[coluna_eixo_x].value_counts(dropna=False).reset_index()
    dados_agrupados.columns = ['Categoria', 'Total']
    dados_agrupados['Categoria'] = dados_agrupados['Categoria'].fillna("NÃO ENCONTRADO / VAZIO")
    dados_plot = dados_agrupados.head(qtd_top)

    # --- PLOTAGEM ---
    if tipo_grafico == "Barras":
        fig = px.bar(
            dados_plot, x='Total', y='Categoria', orientation='h',
            text='Total', title=f"Top {qtd_top} - {coluna_eixo_x}",
            color='Total', color_continuous_scale='Bluered'
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))

    elif tipo_grafico == "Pizza":
        fig = px.pie(dados_plot, names='Categoria', values='Total', title=f"Distribuição - {coluna_eixo_x}")

    elif tipo_grafico == "Rosca":
        fig = px.pie(dados_plot, names='Categoria', values='Total', hole=0.4, title=f"Distribuição - {coluna_eixo_x}")

    elif tipo_grafico == "Funil":
        fig = px.funnel(dados_plot, x='Total', y='Categoria', title=f"Funil - {coluna_eixo_x}")

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- 4. TABELA E DOWNLOAD (CORRIGIDO) ---

    # Prepara o arquivo Excel na memória
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)

    # Layout: Texto na esquerda, Botão na direita
    col_header, col_btn = st.columns([3, 1])

    with col_header:
        st.subheader("📋 Visualização dos Dados")

    with col_btn:
        # Botão alinhado à direita do header, mas acima da tabela
        st.download_button(
            label="📥 Baixar Excel Completo",
            data=buffer.getvalue(),
            file_name="resultado_procv_dinamico.xlsx",
            mime="application/vnd.ms-excel",
            type="primary",
            use_container_width=True  # Botão ocupa toda a largura da coluna dele
        )

    # Tabela ocupa a largura total agora
    st.dataframe(df, use_container_width=True)