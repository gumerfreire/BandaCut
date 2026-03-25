import io
import zipfile
import streamlit as st
import pandas as pd

class csp_1D:
    def __init__(self, raw_length, piece_lengths=None, demand=None):
        self.raw_length = raw_length
        self.piece_lengths = piece_lengths or []
        self.demand = demand or []

    def import_dataframe(self, df, columnName_lengths='Longitud', columnName_demand='Unidades'):
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

st.title("Corte 1D — Greedy Solver (multi-sheet XLSX)")

raw_length = st.number_input("Longitud de la barra (numérica)", min_value=0.0, value=600.0, step=1.0, format="%.2f")

st.write("Suba un archivo .xlsx/.xls con hojas que contengan columnas exactas: **Longitud** y **Unidades** (ambas obligatorias).")
uploaded = st.file_uploader("Subir archivo .xlsx/.xls", type=["xlsx", "xls"])

if uploaded is not None:
    # read all sheet names
    try:
        xls = pd.ExcelFile(uploaded)
        sheet_names = xls.sheet_names
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        st.stop()

    st.subheader("Hojas encontradas")
    st.write(sheet_names)

    # Prepare storage for reports and per-sheet results
    reports = {}  # sheet_name -> report_text
    per_sheet_results = {}  # sheet_name -> results dict

    # Process each sheet
    for sheet in sheet_names:
        st.markdown(f"---\n**Hoja:** {sheet}")
        try:
            df_sheet = xls.parse(sheet_name=sheet)
        except Exception as e:
            st.error(f"Error al leer la hoja '{sheet}': {e}")
            continue

        # Check required columns
        required_cols = ["Longitud", "Unidades"]
        missing = [c for c in required_cols if c not in df_sheet.columns]
        if missing:
            st.error(f"Hoja '{sheet}': faltan columnas obligatorias: {', '.join(missing)}. Se omite esta hoja.")
            continue

        # Parse and validate
        parsed_df = pd.DataFrame({
            "Longitud": pd.to_numeric(df_sheet["Longitud"], errors="coerce"),
            "Unidades": pd.to_numeric(df_sheet["Unidades"], errors="coerce")
        })

        if parsed_df["Longitud"].isna().any():
            st.error(f"Hoja '{sheet}': la columna 'Longitud' contiene valores no numéricos o vacíos. Se omite esta hoja.")
            continue
        if parsed_df["Unidades"].isna().any():
            st.error(f"Hoja '{sheet}': la columna 'Unidades' contiene valores no numéricos o vacíos. Se omite esta hoja.")
            continue

        parsed_df["Unidades"] = parsed_df["Unidades"].astype(int)

        # Solve
        try:
            solver = csp_1D(raw_length)
            solver.import_dataframe(parsed_df, columnName_lengths="Longitud", columnName_demand="Unidades")
            results = solver.solve()
            per_sheet_results[sheet] = results
        except Exception as e:
            st.error(f"Hoja '{sheet}': error al resolver: {e}")
            continue

        # Display brief results
        st.write(f"Longitud barra: **{results['raw_length']}**")
        st.write(f"Piezas de barra usadas: **{results['stock_used']}**")
        st.write(f"Desperdicio total: **{results['total_waste']}**")
        st.write(f"Aprovechamiento: **{results['utilization_pct']} %**")
        st.write("Configuraciones de corte (primeras 5 barras):")
        for i, (cfg, w) in enumerate(zip(results["configurations"], results["waste_per_stock"]), start=1):
            if i > 5:
                st.write("...") 
                break
            st.write(f"Barra {i}: cortes = {cfg} — desperdicio = {w}")

        # Build plain-text report for this sheet
        lines = []
        lines.append(f"SHEET: {sheet}")
        lines.append("=" * (7 + len(sheet)))
        lines.append("")
        lines.append("INPUT DATA")
        lines.append("-----------")
        lines.append(f"Longitud (barra): {results['raw_length']}")
        lines.append("")
        lines.append("Piezas solicitadas (Longitud x Unidades):")
        for length, units in zip(parsed_df["Longitud"].tolist(), parsed_df["Unidades"].tolist()):
            lines.append(f"  - {length} x {units}")
        lines.append("")
        lines.append("RESULTS")
        lines.append("-------")
        lines.append(f"Piezas de barra usadas: {results['stock_used']}")
        lines.append(f"Desperdicio total: {results['total_waste']}")
        lines.append(f"Aprovechamiento: {results['utilization_pct']} %")
        lines.append("")
        lines.append("Configuraciones de corte por barra:")
        for i, (cfg, w) in enumerate(zip(results["configurations"], results["waste_per_stock"]), start=1):
            cfg_str = ", ".join(map(str, cfg)) if cfg else "(sin cortes)"
            lines.append(f"  Barra {i}: {cfg_str}  —  Desperdicio: {w}")
        lines.append("")
        report_text = "\n".join(lines)
        reports[sheet] = report_text

        # Show report preview and individual download button
        with st.expander(f"Ver reporte de '{sheet}'"):
            st.text(report_text)
        st.download_button(
            label=f"Descargar reporte: {sheet}.txt",
            data=report_text,
            file_name=f"{sheet}.txt",
            mime="text/plain",
            key=f"dl_{sheet}"
        )

    # If we have multiple reports, offer a ZIP download
    if reports:
        if len(reports) > 1:
            # create an in-memory ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for sheet_name, txt in reports.items():
                    # sanitize filename
                    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in sheet_name)
                    filename = f"{safe_name}.txt"
                    zf.writestr(filename, txt)
            zip_buffer.seek(0)
            st.download_button(
                label="Descargar todos los reportes (.zip)",
                data=zip_buffer,
                file_name="reportes_corte.zip",
                mime="application/zip"
            )
        else:
            st.info("Se generó 1 reporte. Use el botón de descarga individual arriba.")
else:
    st.info("Esperando archivo .xlsx/.xls. Asegúrese de que cada hoja tenga las columnas 'Longitud' y 'Unidades'.")
