import streamlit as st
import pandas as pd

# Paste or import your class here (slightly adapted to accept pandas DataFrame import)
class csp_1D:
    def __init__(self, raw_length, piece_lengths=None, demand=None):
        self.raw_length = raw_length
        self.piece_lengths = piece_lengths or []
        self.demand = demand or []

    def import_dataframe(self, df, columnName_lengths='Length', columnName_demand='Units'):
        # Allow alternative demand column names
        if columnName_lengths not in df.columns:
            raise ValueError(f"Column '{columnName_lengths}' not found in dataframe")
        # If demand column not present, keep demand empty (will default later)
        self.piece_lengths = df[columnName_lengths].astype(float).tolist()
        if columnName_demand in df.columns:
            self.demand = df[columnName_demand].astype(int).tolist()
        else:
            self.demand = []

    def solve(self):
        if len(self.piece_lengths) == 0:
            raise ValueError('The list of pieces to cut is empty. Please import some data')
        elif len(self.piece_lengths) > 0 and len(self.demand) == 0:
            # assign default demand 1
            self.demand = [1] * len(self.piece_lengths)
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

# --- Streamlit UI ---
st.title("1D Cutting Stock — Greedy Solver")

# Raw length input
raw_length = st.number_input("Raw length (numeric)", min_value=0.0, value=600.0, step=1.0, format="%.2f")

st.write("Upload an Excel (.xlsx/.xls) or CSV file with columns: **Length** and **Units** (Units optional).")
uploaded = st.file_uploader("Upload file", type=["xlsx", "xls", "csv"])

df = None
if uploaded is not None:
    try:
        if uploaded.name.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded)
        else:
            df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Failed to read file: {e}")

# If file loaded, let user choose column names (in case they differ)
if df is not None:
    st.subheader("Imported data (first rows)")
    st.dataframe(df.head())

    # Suggest column names
    length_col = st.selectbox("Select column for piece lengths", options=list(df.columns), index=0)
    # allow optional demand column
    demand_options = ["(no column / default = 1)"] + list(df.columns)
    demand_choice = st.selectbox("Select column for demand/units (optional)", options=demand_options, index=0)

    # Convert and show parsed table
    parsed_df = pd.DataFrame()
    parsed_df["Length"] = pd.to_numeric(df[length_col], errors="coerce")
    if demand_choice != "(no column / default = 1)":
        parsed_df["Units"] = pd.to_numeric(df[demand_choice], errors="coerce").fillna(0).astype(int)
    else:
        parsed_df["Units"] = 1

    st.subheader("Parsed pieces")
    st.dataframe(parsed_df.fillna("").head(200))

    # Run solver button
    if st.button("Solve"):
        try:
            solver = csp_1D(raw_length)
            solver.import_dataframe(parsed_df, columnName_lengths="Length", columnName_demand="Units")
            results = solver.solve()

            st.subheader("Results")
            st.write(f"Raw length: **{results['raw_length']}**")
            st.write(f"Stock used: **{results['stock_used']}**")
            st.write(f"Total waste: **{results['total_waste']}**")
            st.write(f"Material utilization: **{results['utilization_pct']} %**")

            # Show each stock configuration and waste
            st.subheader("Cutting configurations")
            configs = results["configurations"]
            wastes = results["waste_per_stock"]
            for i, (cfg, w) in enumerate(zip(configs, wastes), start=1):
                st.write(f"Stock {i}: cuts = {cfg} — waste = {w}")

            # Optional: export configurations to CSV
            export_df = pd.DataFrame({
                "stock_index": [i for i in range(1, len(configs) + 1)],
                "cuts": [", ".join(map(str, cfg)) for cfg in configs],
                "waste": wastes
            })
            st.download_button("Download configurations CSV", export_df.to_csv(index=False), file_name="configs.csv", mime="text/csv")
        except Exception as e:
            st.error(str(e))
else:
    st.info("Awaiting file upload. You can still enter raw length and prepare a file to upload.")
