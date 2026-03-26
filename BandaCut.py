import io
import zipfile
import streamlit as st
import pandas as pd

'''
BANDACUT

App para Streamlit escrita en Python.

Genera optimización de corte de perfiles 1D utilizando un algoritmo tipo greedy básico.
La introducción de datos se hace mediante tablas de Excel, y la salida se da por pantalla
o a través de archivos de texto descargable. Permite el procesado de múltiples tablas en
una sola operación.

Gumer Freire, 2026
'''

class csp_1D:
    '''
    Clase que implementa el optimizador básico de corte.
    Resuelve un problema tipo Cutting Stock Problem (CSP) 1D mediante un algoritmo greedy.
    '''
    def __init__(self, raw_length, piece_lengths=None, demand=None):
        self.raw_length = raw_length
        self.piece_lengths = piece_lengths or []
        self.demand = demand or []

    def import_dataframe(self, df, columnName_lengths='Longitud', columnName_demand='Unidades'):
        missing = [c for c in (columnName_lengths, columnName_demand) if c not in df.columns]
        if missing:
            raise ValueError(f"Faltan las columnas requeridas: {', '.join(missing)}")
        self.piece_lengths = pd.to_numeric(df[columnName_lengths], errors="coerce").tolist()
        self.demand = pd.to_numeric(df[columnName_demand], errors="coerce").astype(int).tolist()

    def solve(self):
        if len(self.piece_lengths) == 0:
            raise ValueError('La lista de piezas está vacía. Introduce datos.')
        if len(self.piece_lengths) != len(self.demand):
            raise ValueError('La lista de unidades y de longitudes debe tener la misma dimensión.')
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

st.title("BandaCut")
st.write("Optimización de corte de perfiles 1D. Esta herramienta utiliza un algoritmo tipo greedy básico. Introduce la medida de la barra en bruto y los datos de corte para optimizar. Las unidades son definidas por el usuario, deben coincidir las unidades de bara en bruto y cortes.")

st.write("Sube un archivo .xlsx/.xls. El archivo puede tener una o varias hojas, cada una con un listado de cortes de perfil para optimizar. Cada hoja debe contener una tabla con las columnas: **Longitud** y **Unidades**.")

raw_length = st.number_input("Longitud de barras en bruto:", min_value=1, value=600, step=1, format="%d")

uploaded = st.file_uploader("Subir archivo .xlsx/.xls", type=["xlsx", "xls"])

if uploaded is not None:
    # Leer la lista de hojas en el archivo
    try:
        xls = pd.ExcelFile(uploaded)
        sheet_names = xls.sheet_names
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        st.stop()
    st.write("**Hojas encontradas:** " + ", ".join(sheet_names))

    # Preparar almacenamiento para datos de informes
    reports = {}  
    per_sheet_results = {}
    st.markdown(f"---")
    st.subheader("Informes de corte")
    # Procesado de cada hoja
    for sheet in sheet_names:
        st.markdown(f"**Hoja: {sheet}**")
        try:
            df_sheet = xls.parse(sheet_name=sheet)
        except Exception as e:
            st.error(f"Error al leer la hoja '{sheet}': {e}")
            st.markdown(f"---")
            continue

        # Comprobar columnas requeridas
        required_cols = ["Longitud", "Unidades"]
        missing = [c for c in required_cols if c not in df_sheet.columns]
        if missing:
            st.error(f"Hoja '{sheet}': faltan columnas obligatorias: {', '.join(missing)}. Se omite esta hoja.")
            st.markdown(f"---")
            continue

        # Parse y validar
        parsed_df = pd.DataFrame({
            "Longitud": pd.to_numeric(df_sheet["Longitud"], errors="coerce"),
            "Unidades": pd.to_numeric(df_sheet["Unidades"], errors="coerce")
        })

        if parsed_df["Longitud"].isna().any():
            st.error(f"Hoja '{sheet}': la columna 'Longitud' contiene valores no numéricos o vacíos. Se omite esta hoja.")
            st.markdown(f"---")
            continue
        if parsed_df["Unidades"].isna().any():
            st.error(f"Hoja '{sheet}': la columna 'Unidades' contiene valores no numéricos o vacíos. Se omite esta hoja.")
            st.markdown(f"---")
            continue
        
        if parsed_df["Longitud"].max() > raw_length:
            st.error(f"Hoja '{sheet}': Existen longitudes de corte más grandes que el perfil en bruto. Se omite esta hoja.")
            st.markdown("---")
            continue

        parsed_df["Unidades"] = parsed_df["Unidades"].astype(int)

        # Optimización
        try:
            solver = csp_1D(raw_length)
            solver.import_dataframe(parsed_df, columnName_lengths="Longitud", columnName_demand="Unidades")
            results = solver.solve()
            per_sheet_results[sheet] = results
        except Exception as e:
            st.error(f"Hoja '{sheet}': error al resolver: {e}")
            continue

        # Mostrar resumen en pantalla
        st.write(f"Piezas de barra usadas: **{results['stock_used']}**")
        st.write(f"Desperdicio total: **{results['total_waste']}**")
        st.write(f"Aprovechamiento: **{results['utilization_pct']} %**")
 
        # Construir salida de texto para archivo / pantalla
        lines = []
        lines.append(f"HOJA: {sheet}")
        lines.append("=" * (7 + len(sheet)))
        lines.append("")
        lines.append("DATOS DE ENTRADA")
        lines.append("-----------")
        lines.append(f"Longitud de barra en bruto: {results['raw_length']}")
        lines.append("")
        lines.append("Piezas solicitadas (Longitud x Unidades):")
        for length, units in zip(parsed_df["Longitud"].tolist(), parsed_df["Unidades"].tolist()):
            lines.append(f"  - {length} x {units}")
        lines.append("")
        lines.append("RESULTADO DE OPTIMIZACIÓN")
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

        # Mostrar en pantalla resumen de informe y botones de descarga
        with st.expander(f"Ver informe de {sheet}"):
            st.text(report_text)
        st.download_button(
            label=f"Descargar informe: {sheet}.txt",
            data=report_text,
            file_name=f"{sheet}.txt",
            mime="text/plain",
            key=f"dl_{sheet}"
        )
    
    # Descaarga en ZIP de informes en caso de haber más de uno
    if reports:
        if len(reports) > 1:
            st.markdown(f"---")
            # Crear ZIP en memoria
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for sheet_name, txt in reports.items():
                    # Formatear nombre de archivo
                    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in sheet_name)
                    filename = f"{safe_name}.txt"
                    zf.writestr(filename, txt)
            zip_buffer.seek(0)
            st.download_button(
                label="Descargar todos los informes (.zip)",
                data=zip_buffer,
                file_name="informes_corte.zip",
                mime="application/zip"
            )
        else:
            st.info("Se generó un informe. Usa el botón de descarga individual arriba.")
else:
    st.info("Esperando archivo .xlsx/.xls. Asegúrate de que cada hoja tenga las columnas 'Longitud' y 'Unidades'.")
