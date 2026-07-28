import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FII/DII Sentiment & Market Analyzer", layout="wide")

st.title("📊 F&O Participant OI & Market Sentiment Analyzer")
st.write(
    "Upload your participant-wise open interest CSV file to instantly evaluate"
    " the market bias."
)

# Sidebar for Manual Metrics
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

# Container for Summary (Placed right below the file uploader)
summary_container = st.container()

if uploaded_file is not None:
  try:
    # Read file content safely as text string
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
    lines = stringio.readlines()

    # Find the line index where actual table headers start
    header_idx = 0
    for idx, line in enumerate(lines):
      if "Client Type" in line or (
          "Client" in line and "Future Index Long" in line
      ):
        header_idx = idx
        break

    # Recreate a clean CSV stream starting from the correct header line
    clean_csv_data = "".join(lines[header_idx:])
    df_clean = pd.read_csv(io.StringIO(clean_csv_data))

    # Standardize column names by stripping whitespace
    df_clean.columns = df_clean.columns.str.strip()

    col_names = df_clean.columns.tolist()
    client_col = col_names[0]
    fut_idx_long_col = col_names[1]
    fut_idx_short_col = col_names[2]

    participants = ["FII", "CLIENT", "PRO", "DII"]

    summary_data = []
    for _, row in df_clean.iterrows():
      c_type = str(row[client_col]).strip().upper()
      if any(p == c_type for p in participants):
        try:
          l_val = float(str(row[fut_idx_long_col]).replace(",", ""))
          s_val = float(str(row[fut_idx_short_col]).replace(",", ""))
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
      fii_row = summary_df[summary_df["Participant"] == "FII"]

      # Display Summary right below upload section with 16px font sizing
      with summary_container:
        st.markdown("---")
        st.subheader("🎯 Market Directional Bias Summary")

        if not fii_row.empty:
          fii_net = fii_row["Net Index Futures"].values[0]

          col1, col2, col3 = st.columns(3)
          with col1:
            st.metric("FII Net Index Futures", f"{fii_net:,.0f}")
          with col2:
            st.metric("India VIX", f"{manual_vix}")
          with col3:
            st.metric("Nifty PCR", f"{manual_pcr}")

          if fii_net < 0:
            st.markdown(
                '<p style="font-size: 16px; color: #ef4444; font-weight:'
                ' bold;">BEARISH BIAS: FIIs are net short in Index Futures.'
                ' Expect resistance on intraday rallies.</p>',
                unsafe_allow_html=True,
            )
          else:
            st.markdown(
                '<p style="font-size: 16px; color: #22c55e; font-weight:'
                ' bold;">BULLISH BIAS: FIIs are net long in Index Futures.'
                ' Expect support on intraday dips.</p>',
                unsafe_allow_html=True,
            )
        else:
          st.warning("Could not isolate FII row automatically.")

        st.markdown("---")

      # Detailed Tables below the summary
      st.subheader("📊 Participant Index Futures Net Position")
      st.dataframe(summary_df)

      st.subheader("📋 Raw Data Preview")
      st.dataframe(df_clean.head(10))

    else:
      st.warning("No matching participant rows found in the CSV structure.")

  except Exception as e:
    st.error(f"Error processing the file: {e}")
else:
  with summary_container:
    st.info("Please upload a valid F&O participant open interest CSV file above.")
