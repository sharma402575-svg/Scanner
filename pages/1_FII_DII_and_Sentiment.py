import pandas as pd
import streamlit as st

st.set_page_config(page_title="FII/DII Sentiment & Market Analyzer", layout="wide")

st.title("📊 F&O Participant OI & Market Sentiment Analyzer")
st.write(
    "Upload your participant-wise open interest CSV file and optionally input market metrics to evaluate the bias."
)

# Sidebar or Main Input for Manual Metrics (Removes live_data dependency)
st.sidebar.header("Market Parameters")
manual_vix = st.sidebar.number_input(
    "India VIX (Optional)", min_value=0.0, value=13.5, step=0.1
)
manual_pcr = st.sidebar.number_input(
    "Nifty PCR (Optional)", min_value=0.0, value=1.0, step=0.01
)

# File Uploader
uploaded_file = st.file_uploader(
    "Upload Participant OI CSV file", type=["csv"]
)

if uploaded_file is not None:
  try:
    # Read CSV safely
    df = pd.read_csv(uploaded_file)

    # Clean up and find the data rows
    # Searching for rows containing participant labels like FII, CLIENT, etc.
    raw_text_df = pd.read_csv(uploaded_file, header=None)

    # Let's find where 'Client Type' or 'Client' or 'FII' is located
    header_row_idx = None
    for idx, row in raw_text_df.iterrows():
      row_str = str(row.values).upper()
      if "FII" in row_str or "CLIENT" in row_str:
        header_row_idx = idx
        break

    if header_row_idx is not None:
      df_clean = pd.read_csv(uploaded_file, skiprows=header_row_idx)
    else:
      df_clean = pd.read_csv(uploaded_file, skiprows=1)

    # Standardize column names by stripping whitespace
    df_clean.columns = df_clean.columns.str.strip()

    st.subheader("📋 Raw Data Preview")
    st.dataframe(df_clean.head(10))

    # Process Participant Data
    # Look for columns resembling Client Type, Future Index Long, Future Index Short
    col_names = df_clean.columns.tolist()

    # Attempting standard NSE mapping
    client_col = col_names[0]
    fut_idx_long_col = col_names[1]
    fut_idx_short_col = col_names[2]

    # Filter for key participants
    participants = ["FII", "CLIENT", "PRO", "DII"]

    summary_data = []
    for _, row in df_clean.iterrows():
      c_type = str(row[client_col]).strip().upper()
      if any(p in c_type for p in participants):
        try:
          l_val = float(row[fut_idx_long_col])
          s_val = float(row[fut_idx_short_col])
          net_val = l_val - s_val
          summary_data.append({
              "Participant": c_type,
              "Index Long": l_val,
              "Index Short": s_val,
              "Net Index Futures": net_val,
          })
        except ValueError:
          continue

    if summary_data:
      summary_df = pd.DataFrame(summary_data)

      st.subheader("📊 Participant Index Futures Net Position")
      st.dataframe(summary_df)

      # Sentiment Evaluation based on FII
      fii_row = summary_df[summary_df["Participant"].str.contains("FII")]
      if not fii_row.empty:
        fii_net = fii_row["Net Index Futures"].values[0]

        st.subheader("🎯 Market Directional Bias Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
          st.metric("FII Net Index Futures", f"{fii_net:,.0f}")
        with col2:
          st.metric("India VIX", f"{manual_vix}")
        with col3:
          st.metric("Nifty PCR", f"{manual_pcr}")

        if fii_net < 0:
          st.error(
              "**BEARISH BIAS:** FIIs are net short in Index Futures. Expect"
              " resistance on intraday rallies."
          )
        else:
          st.success(
              "**BULLISH BIAS:** FIIs are net long in Index Futures. Expect"
              " support on intraday dips."
          )
      else:
        st.warning("Could not isolate FII row automatically for summary metrics.")

  except Exception as e:
    st.error(f"Error processing the file: {e}")
else:
  st.info("Please upload a valid F&O participant open interest CSV file to begin.")
