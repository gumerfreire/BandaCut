import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="BandaCut - Optimización de material 1D")

st.title("BandaCut")

# Integer input
n = st.number_input("Longitud de perfiles en bruto:", min_value=0, step=1, value=0, format="%d")

st.markdown("### Listado de despiece")

# Option tabs: upload CSV/Excel, paste text, or edit table
tab1, tab2, tab3 = st.tabs(["Subir un archivo", "Introducir texto", "Editar datos en tabla"])

with tab1:
    uploaded = st.file_uploader("Sube un archivo de Excel o CSV. La tabla debe tener las columnas: Unidades, Longitud.", type=["csv", "xlsx", "xls"])
    df = None
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Error leyendo el archivo: {e}")

with tab2:
    txt = st.text_area("Introduce datos. Cada línea debe tener este formato: Unidades, Longitud")
    if txt.strip():
        try:
            # try comma first, then tab
            df = pd.read_csv(StringIO(txt))
        except Exception:
            try:
                df = pd.read_csv(StringIO(txt), sep="\t")
            except Exception as e:
                st.error(f"Error en el formato de datos: {e}")
                df = None

with tab3:
    # start with empty table template
    if "editable_df" not in st.session_state:
        st.session_state.editable_df = pd.DataFrame({"Unidades": [], "Longitud": []})
    st.session_state.editable_df = st.data_editor(
        st.session_state.editable_df,
        num_rows="dynamic",
        use_container_width=True,
    )
    df = st.session_state.editable_df

# Normalize/validate df if present
if 'df' in locals() and df is not None:
    # Ensure required columns exist
    needed = ["Unidades", "Longitud"]
    # allow case-insensitive match
    cols = {c.lower(): c for c in df.columns}
    if all(k.lower() in cols for k in needed):
        df = df.rename(columns={cols[k.lower()]: k for k in needed})
        # try convert Length to numeric
        df["Longitud"] = pd.to_numeric(df["Longitud"], errors="coerce")
        invalid = df["Longitud"].isna()
        if invalid.any():
            st.warning(f"{invalid.sum()} fila(s) tienen valores no númericos, se convierten a NaN.")
        st.write("Datos para optimización:", df)
        # Example: use the integer 'n' and the table in a simple calculation
        st.markdown("### Resultado:")
        # simple demo: multiply lengths by n (skip NaN)
        result = df["Longitud"].dropna() * int(n)
        st.write(result.to_frame(name="Length_times_n"))
    else:
        st.error(f"Los datos deben incluir las columnas: {', '.join(needed)}. Found: {', '.join(df.columns)}")
else:
    st.info("Introduce los datos mediante un archivo, texto o tabla.")
