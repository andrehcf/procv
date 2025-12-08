import streamlit as st
import pandas as pd
from io import BytesIO

# Configuração da Página
st.set_page_config(page_title="Gerador de PROCV", layout="wide")

st.title("📊 Ferramenta de PROCV (Merge) com Python")
st.markdown("""
Esta ferramenta cruza duas planilhas Excel (similar ao VLOOKUP/PROCV).
1. Faça o upload da **Planilha Principal**.
2. Faça o upload da **Base de Dados**.
3. Escolha as colunas de ligação e o que deseja trazer.
""")

st.divider()

# --- COLUNA 1: UPLOAD DOS ARQUIVOS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Arquivo Principal")
    arquivo_principal = st.file_uploader("Onde os dados serão colados", type=["xlsx", "xls"], key="main")

with col2:
    st.subheader("2. Base de Dados")
    arquivo_base = st.file_uploader("Origem das informações", type=["xlsx", "xls"], key="base")

# --- LÓGICA DO PROCESSO ---
if arquivo_principal and arquivo_base:
    try:
        # Carregar Dataframes
        df_main = pd.read_excel(arquivo_principal)
        df_base = pd.read_excel(arquivo_base)

        st.success("Arquivos carregados com sucesso!")
        st.divider()

        # --- SELEÇÃO DE COLUNAS ---
        st.subheader("3. Configuração do Cruzamento")

        # Seleção das Chaves (IDs)
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            chave_main = st.selectbox(
                "Qual a coluna de ID na Planilha Principal?",
                options=df_main.columns,
                help="Selecione o código único (ex: SKU, CPF, ID)"
            )

        with col_c2:
            chave_base = st.selectbox(
                "Qual a coluna de ID na Base de Dados?",
                options=df_base.columns,
                index=0
            )

        # Seleção do que trazer (excluindo a chave para não duplicar visualmente)
        colunas_disponiveis = [c for c in df_base.columns if c != chave_base]

        colunas_desejadas = st.multiselect(
            "Quais informações você quer trazer da Base para a Principal?",
            options=colunas_disponiveis,
            placeholder="Selecione uma ou mais colunas..."
        )

        # --- BOTÃO DE AÇÃO ---
        st.divider()
        if st.button("Executar PROCV", type="primary"):
            if not colunas_desejadas:
                st.warning("Por favor, selecione pelo menos uma coluna para trazer.")
            else:
                # Preparar colunas para o merge (Chave + Desejadas)
                cols_to_merge = [chave_base] + colunas_desejadas

                # Realizar o Merge (Left Join)
                # left_on e right_on permitem chaves com nomes diferentes

                df_resultado = pd.merge(
                    df_main,
                    df_base[cols_to_merge],
                    left_on=chave_main,
                    right_on=chave_base,
                    how='left'
                )

                # Se as chaves tiverem nomes diferentes, o Pandas mantém as duas.
                # Removemos a chave da base se for redundante e não for o que o usuário pediu explicitamente
                if chave_main != chave_base and chave_base not in colunas_desejadas:
                    df_resultado = df_resultado.drop(columns=[chave_base])

                st.subheader("Visualização do Resultado (Primeiras 50 linhas)")
                st.dataframe(df_resultado.head(50))

                # --- DOWNLOAD ---
                # Converter para Excel em memória (buffer)
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_resultado.to_excel(writer, index=False, sheet_name='Resultado')

                st.download_button(
                    label="📥 Baixar Planilha Pronta",
                    data=buffer.getvalue(),
                    file_name="resultado_procv_gerado.xlsx",
                    mime="application/vnd.ms-excel"
                )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os arquivos: {e}")

else:
    st.info("Aguardando upload dos dois arquivos para iniciar...")