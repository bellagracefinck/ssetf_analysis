import streamlit as st
import pandas as pd
import json



def summarize(accession_number, fund_holding, fund_info, swaps, counterparties, lev=2.0):
    etf = fund_holding[fund_holding['ACCESSION_NUMBER'] == accession_number]
    fund_name = fund_info[fund_info['ACCESSION_NUMBER'] == accession_number]['SERIES_NAME'].values[0]
    fund_nav = fund_info[fund_info['ACCESSION_NUMBER'] == accession_number]['NET_ASSETS'].values[0]
    fund_swaps = fund_holding[(fund_holding['ACCESSION_NUMBER'] == accession_number) &
                              (fund_holding['DERIVATIVE_CAT'] == 'SWP')]
    
    if fund_swaps.empty:
        return {"fund_name": fund_name, "message": "No swaps found for this fund."}
    
    fund_swaps = fund_swaps.merge(swaps, on='HOLDING_ID', how='left').merge(counterparties, on='HOLDING_ID', how='left')
    fund_swaps['DERIVATIVE_COUNTERPARTY_NAME'] = fund_swaps['DERIVATIVE_COUNTERPARTY_NAME'].fillna("Unknown").str.strip()
    
    total_notional = fund_swaps['NOTIONAL_AMOUNT'].sum()
    notional_to_nav_ratio = (total_notional / fund_nav * 100) if fund_nav else "N/A"
    unrealized_gains = fund_swaps['UNREALIZED_APPRECIATION'].sum()
    
    counterparties_data = []
    for counterparty in fund_swaps['DERIVATIVE_COUNTERPARTY_NAME'].unique():
        c_notional_value = fund_swaps[fund_swaps["DERIVATIVE_COUNTERPARTY_NAME"] == counterparty]['NOTIONAL_AMOUNT'].sum()
        term = fund_swaps[fund_swaps["DERIVATIVE_COUNTERPARTY_NAME"] == counterparty]["TERMINATION_DATE"].values[0]
        rate = fund_swaps[fund_swaps["DERIVATIVE_COUNTERPARTY_NAME"] == counterparty]["FLOATING_RATE_INDEX_PAYMENT"].values[0]
        spread = fund_swaps[fund_swaps["DERIVATIVE_COUNTERPARTY_NAME"] == counterparty]["FLOATING_RATE_SPREAD_PAYMENT"].values[0]
        counterparties_data.append({"name": counterparty, "notional": c_notional_value, "termination": term, "rate": f"{rate} ({spread} bp)"})
    
    return {
        "fund_name": fund_name,
        "total_holdings": len(etf),
        "total_notional_exposure": total_notional,
        "NAV": fund_nav,
        "notional_exposure_ratio": notional_to_nav_ratio,
        "unrealized_gains": unrealized_gains,
        "counterparties": counterparties_data
    }

# Streamlit UI
st.title("Single-Stock ETF Analyzer")

# Load your dataframes here (fund_holding, fund_info, swaps, counterparties)
# Example: fund_info = pd.read_csv("fund_info.csv")

# Dropdown for ETF selection
fund_options = dict(zip(fund_info["SERIES_NAME"], fund_info["ACCESSION_NUMBER"]))
selected_fund = st.selectbox("Select an ETF:", list(fund_options.keys()), index=0)
accession_number = fund_options[selected_fund]

# Run the summarization
if st.button("Analyze Fund"):
    summary = summarize(accession_number, fund_holding, fund_info, swaps, counterparties)
    
    st.subheader(f"Results for {summary['fund_name']}")
    st.markdown(f"**Total Holdings:** {summary['total_holdings']}")
    st.markdown(f"**Total Notional Exposure:** ${summary['total_notional_exposure']:,.2f}")
    st.markdown(f"**NAV:** ${summary['NAV']:,.2f}")
    st.markdown(f"**Notional Exposure/NAV Ratio:** {summary['notional_exposure_ratio']:.2f}%")
    st.markdown(f"**Unrealized Gains/Losses:** ${summary['unrealized_gains']:,.2f}")
    
    # Counterparty Breakdown Table
    st.subheader("Swap Counterparty Breakdown")
    df_counterparties = pd.DataFrame(summary["counterparties"])
    st.table(df_counterparties)
    
    # Download JSON Button
    json_data = json.dumps(summary, indent=4)
    st.download_button(label="Download JSON Report", data=json_data, file_name=f"{selected_fund}_report.json", mime="application/json")
