import streamlit as st
import pandas as pd

class csp_1D:
    def __init__(self, raw_length, piece_lengths=None, demand=None):
        self.raw_length = raw_length
        self.piece_lengths = piece_lengths or []
        self.demand = demand or []

    def import_dataframe(self, df, columnName_lengths='Longitud', columnName_demand='Unidades'):
        # Require exact columns
        missing = [c for c in (columnName_lengths, columnName_demand) if c not in df.columns]
        if missing:
            raise ValueError(f"Required column(s) missing: {', '.join(missing)}")
        self.piece_lengths = pd.to_numeric(df[columnName_lengths], errors="coerce").tolist()
        self.demand = pd.to_numeric(df[columnName_demand], errors="coerce").astype(int).tolist()

    def solve(self):
        if len(self.piece_lengths) == 0:
            raise ValueError('The list of pieces to cut is empty. Please import some data')
        if len(self.piece_lengths) != len(self.demand):
            raise ValueError('The list of lengths and the list of demands must have the same number of values')
        configurations, stock_used, waste = self.CSP_greedy()
        use_percentage = round(((stock_used * self.raw_length) - sum(waste)) / (stock_used * self.raw_length) * 100, 1)
        return {
            "configurations": configurations,
            "stock_used": stock_used,
            "waste_per_stock": waste,
            "total_waste": sum(waste),
            "raw_length": self.raw_length,
            "utilization_pct": use_percentage
        }

    def CSP_greedy(self):
        pieces_required = []
        for length, count in zip(self.piece_lengths, self.demand):
            pieces_required.extend([length] * count)
        pieces_required = [p for p in pieces_required if pd.notna(p)]
        pieces_required.sort(reverse=True)
        used_stock = 0
        waste_per_stock = []
        cutting_configurations = []
        while pieces_required:
            used_stock += 1
            remaining_length = self.raw_length
            current_cutting = []
            for piece in pieces_required[:]:
                if piece <= remaining_length:
                    remaining_length -= piece
                    current_cutting.append(piece)
                    pieces_required.remove(piece)
            cutting_configurations.append(current_cutting)
            waste_per_stock.append(remaining_length)
        return cutting_configurations, used_stock, waste_per_stock

# Streamlit UI
st.title("Corte 1D — Greedy Solver")

raw_length = st.number_input("Longitud de la barra (numérica)", min_value=0.0, value=600.0, step=1.0, format="%.2f")

st.write("Suba un archivo Excel (.xlsx/.xls) o CSV con columnas exactas: **Longitud** y **Unidades** (ambas obligatorias).")
uploaded = st.file_uploader("Subir archivo", type=["xlsx", "xls", "csv"])

if uploaded is not None:
    # Read file
    try:
        if uploaded.name.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded)
        else:
            df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # Enforce required column names
    required_cols = ["Longitud", "Unidades"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Faltan columnas obligatorias: {', '.join(missing)}. Asegúrese de que el archivo tenga exactamente las columnas 'Longitud' y 'Unidades'.")
        st.stop()

    # Parse columns (no previews)
    try:
        parsed_df = pd.DataFrame({
            "Longitud": pd.to_numeric(df["Longitud"], errors="coerce"),
            "Unidades": pd.to_numeric(df["Unidades"], errors="coerce").astype(int)
        })
    except Exception as e:
        st.error(f"Error al convertir columnas: {e}")
        st.stop()

    if parsed_df["Longitud"].isna().any():
        st.error("La columna 'Longitud' contiene valores no numéricos o vacíos. Corrija el archivo e intente de nuevo.")
        st.stop()
    if parsed_df["Unidades"].isna().any():
        st.error("La columna 'Unidades' contiene valores no numéricos o vacíos. Corrija el archivo e intente de nuevo.")
        st.stop()

    if st.button("Resolver"):
        try:
            solver = csp_1D(raw_length)
            solver.import_dataframe(parsed_df, columnName_lengths="Longitud", columnName_demand="Unidades")
            results = solver.solve()

            st.subheader("Resultados")
            st.write(f"Longitud barra: **{results['raw_length']}**")
            st.write(f"Piezas de barra usadas: **{results['stock_used']}**")
            st.write(f"Desperdicio total: **{results['total_waste']}**")
            st.write(f"Aprovechamiento: **{results['utilization_pct']} %**")

            st.subheader("Configuraciones de corte")
            for i, (cfg, w) in enumerate(zip(results["configurations"], results["waste_per_stock"]), start=1):
                st.write(f"Barra {i}: cortes = {cfg} — desperdicio = {w}")

            export_df = pd.DataFrame({
                "stock_index": [i for i in range(1, len(results["configurations"]) + 1)],
                "cuts": [", ".join(map(str, cfg)) for cfg in results["configurations"]],
                "waste": results["waste_per_stock"]
            })
            st.download_button("Descargar configuraciones CSV", export_df.to_csv(index=False), file_name="configs.csv", mime="text/csv")
        except Exception as e:
            st.error(str(e))
else:
    st.info("Esperando archivo. Asegúrese de que tenga las columnas 'Longitud' y 'Unidades'.")
