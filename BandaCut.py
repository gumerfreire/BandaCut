import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="BandaCut - Optimización de material 1D")
st.title("BandaCut")

# Integer input
n = st.number_input("Longitud de perfiles en bruto:", min_value=0, step=1, value=0, format="%d")

def process(df: pd.DataFrame, n: int):
    """Placeholder processing function — replace with your optimization logic."""
    st.write("Procesando...", "Filas:", len(df))
    # example: simple calculation (remove or replace)
    df = df.copy()
    df["Longitud"] = pd.to_numeric(df["Longitud"], errors="coerce")
    result = df["Longitud"].dropna() * int(n)
    st.write(result.to_frame(name="Longitud_por_n"))

st.markdown("### Listado de despiece")

tab1, tab2, tab3 = st.tabs(["Subir un archivo", "Introducir texto", "Editar datos en tabla"])

# ---- TAB 1 : Upload ----
with tab1:
    uploaded = st.file_uploader(
        "Sube un archivo de Excel o CSV. La tabla debe tener las columnas: Unidades, Longitud.",
        type=["csv", "xlsx", "xls"],
        key="uploader_tab1"
    )
    df_tab1 = None
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df_tab1 = pd.read_csv(uploaded)
            else:
                df_tab1 = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Error leyendo el archivo: {e}")
            df_tab1 = None

    if st.button("Procesar datos", key="process_tab1"):
        if df_tab1 is None:
            st.error("No hay datos cargados en este tab.")
        else:
            needed = ["Unidades", "Longitud"]
            cols = {c.lower(): c for c in df_tab1.columns}
            if all(k.lower() in cols for k in needed):
                df_tab1 = df_tab1.rename(columns={cols[k.lower()]: k for k in needed})
                process(df_tab1, n)
            else:
                st.error(f"Los datos deben incluir las columnas: {', '.join(needed)}. Encontrado: {', '.join(df_tab1.columns)}")

# ---- TAB 2 : Paste text ----
with tab2:
    txt = st.text_area("Introduce datos. Cada línea debe tener este formato: Unidades, Longitud", key="text_tab2")
    df_tab2 = None
    if txt.strip():
        try:
            df_tab2 = pd.read_csv(StringIO(txt))
        except Exception:
            try:
                df_tab2 = pd.read_csv(StringIO(txt), sep="\t")
            except Exception as e:
                st.error(f"Error en el formato de datos: {e}")
                df_tab2 = None

    if st.button("Procesar datos", key="process_tab2"):
        if df_tab2 is None:
            st.error("No hay datos introducidos en este tab.")
        else:
            needed = ["Unidades", "Longitud"]
            cols = {c.lower(): c for c in df_tab2.columns}
            if all(k.lower() in cols for k in needed):
                df_tab2 = df_tab2.rename(columns={cols[k.lower()]: k for k in needed})
                process(df_tab2, n)
            else:
                st.error(f"Los datos deben incluir las columnas: {', '.join(needed)}. Encontrado: {', '.join(df_tab2.columns)}")

# ---- TAB 3 : Editable table ----
with tab3:
    if "editable_df" not in st.session_state:
        st.session_state.editable_df = pd.DataFrame({"Unidades": [], "Longitud": []})
    st.session_state.editable_df = st.data_editor(
        st.session_state.editable_df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_tab3"
    )
    df_tab3 = st.session_state.editable_df

    if st.button("Procesar datos", key="process_tab3"):
        if df_tab3 is None or df_tab3.empty:
            st.error("No hay datos en la tabla editable.")
        else:
            needed = ["Unidades", "Longitud"]
            cols = {c.lower(): c for c in df_tab3.columns}
            if all(k.lower() in cols for k in needed):
                df_tab3 = df_tab3.rename(columns={cols[k.lower()]: k for k in needed})
                process(df_tab3, n)
            else:
                st.error(f"Los datos deben incluir las columnas: {', '.join(needed)}. Encontrado: {', '.join(df_tab3.columns)}")
