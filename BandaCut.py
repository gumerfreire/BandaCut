            # Build plain-text report
            lines = []
            lines.append("INPUT DATA")
            lines.append("-----------")
            lines.append("Longitud (barra): {}".format(results["raw_length"]))
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

            # Show report on screen (optional)
            st.subheader("Reporte de texto")
            st.text(report_text)

            # Provide .txt download
            st.download_button(
                label="Descargar reporte (.txt)",
                data=report_text,
                file_name="corte_resultado.txt",
                mime="text/plain"
            )
