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
    txt = st.text_area("Sube un archivo de Excel o CSV. La tabla debe tener las columnas: Unidades, Longitud.")
    uploaded = st.file_uploader("Subir un archivo de Excel o CSV", type=["csv", "xlsx", "xls"])
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
        df["Length"] = pd.to_numeric(df["Length"], errors="coerce")
        invalid = df["Length"].isna()
        if invalid.any():
            st.warning(f"{invalid.sum()} row(s) have non-numeric Length and were set to NaN.")
        st.write("Data preview:", df)
        # Example: use the integer 'n' and the table in a simple calculation
        st.markdown("### Example result")
        # simple demo: multiply lengths by n (skip NaN)
        result = df["Length"].dropna() * int(n)
        st.write(result.to_frame(name="Length_times_n"))
    else:
        st.error(f"Data must include columns: {', '.join(needed)}. Found: {', '.join(df.columns)}")
else:
    st.info("Provide data via upload, paste, or the editable table.")
