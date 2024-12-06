import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.title("Option Chain Explorer")

# --- Sidebar for user input ---
with st.sidebar:
    ticker_symbols = st.text_input("Enter ticker symbols (comma-separated):", "TSLA,AAPL,MSFT,NVDA,GOOG,AMZN,PLTR")
    tickers = [t.strip() for t in ticker_symbols.split(",")]

    # Dictionary to store option chain data for each ticker
    option_chains = {}
    for ticker_symbol in tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            # Get available expiration dates
            available_expirations = ticker.options
            option_chains[ticker_symbol] = {
                'ticker': ticker,
                'expirations': available_expirations
            }
        except Exception as e:
            st.error(f"Error fetching ticker data for {ticker_symbol}: {e}")
            st.stop()

    # Select expiry date (assuming the same expiry date for all tickers for now)
    expiry_date = st.selectbox("Select expiry date:", option_chains[tickers[0]]['expirations'])

    # Fetch option chain data for all tickers
    for ticker_symbol in tickers:
        try:
            option_chains[ticker_symbol]['option_chain'] = option_chains[ticker_symbol]['ticker'].option_chain(expiry_date)
        except Exception as e:
            st.error(f"Error fetching option chain data for {ticker_symbol}: {e}")
            st.stop()

    # Choose plotting parameter for the first plot
    plot_param = st.selectbox("Select parameter to plot (Chain):", ['lastPrice', 'volume', 'openInterest'])

# --- Create pages ---
page = st.sidebar.radio("Select Page", ["Option Chain", "Option Price", "Highest Volume Options", "Calls Table", "Puts Table"])

# --- Page 1: Option Chain Visualization ---
if page == "Option Chain":
    st.subheader("Option Chain Visualization")

    # Create the plot
    fig, ax = plt.subplots()
    for ticker_symbol in tickers:
        option_chain = option_chains[ticker_symbol]['option_chain']
        calls = option_chain.calls[['strike', 'lastPrice', 'volume', 'openInterest']]
        calls['type'] = 'Call'
        puts = option_chain.puts[['strike', 'lastPrice', 'volume', 'openInterest']]
        puts['type'] = 'Put'
        df = pd.concat([calls, puts])

        # Get current stock price
        try:
            current_price = option_chains[ticker_symbol]['ticker'].info['currentPrice']
        except Exception as e:
            st.error(f"Error fetching stock price for {ticker_symbol}: {e}")
            current_price = None

        for option_type in df['type'].unique():
            df_type = df[df['type'] == option_type]
            # Add current price to legend label
            label = f"{ticker_symbol} {option_type}"
            if current_price:
                label += f" (Current Price: {current_price:.2f})"
            ax.plot(df_type['strike'], df_type[plot_param], label=label)

    ax.set_xlabel("Strike Price")
    ax.set_ylabel(plot_param)
    ax.set_title(f"Option Chain ({expiry_date}) - {plot_param}")
    ax.legend()
    st.pyplot(fig)

# --- Page 2: Option Price History ---
elif page == "Option Price":
    st.subheader("Option Price History")

    # Select ticker and option for price history
    selected_ticker = st.selectbox("Select ticker for price plot:", tickers)
    option_chain = option_chains[selected_ticker]['option_chain']
    all_contract_symbols = list(option_chain.calls['contractSymbol']) + list(option_chain.puts['contractSymbol'])
    all_contracts = pd.concat([option_chain.calls, option_chain.puts])
    all_contracts_sorted = all_contracts.sort_values(by='volume', ascending=False)
    all_contract_symbols_sorted = all_contracts_sorted['contractSymbol'].tolist()
    selected_option = st.selectbox("Select option for price plot:", all_contract_symbols_sorted)

    try:
        # Fetch historical data for the selected option
        option_data = yf.download(selected_option, period="1mo")  # Download 1 month of data

        # Create the plot
        fig, ax = plt.subplots()
        ax.plot(option_data['Close'], label="Last Price")  # Use 'Close' instead of 'Open'
        ax.plot(option_data['Low'], label="Bid")
        ax.plot(option_data['High'], label="Ask")

        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.set_title(f"{selected_option} Price History")
        ax.legend()

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error fetching or plotting option price data: {e}")

# --- Page 3: Highest Volume Options ---
elif page == "Highest Volume Options":
    st.subheader("Highest Volume Options")

    # Select ticker for highest volume options
    selected_ticker = st.selectbox("Select ticker for highest volume options:", tickers)
    option_chain = option_chains[selected_ticker]['option_chain']
    all_contracts = pd.concat([option_chain.calls, option_chain.puts])
    all_contracts_sorted = all_contracts.sort_values(by='volume', ascending=False)

    st.write(all_contracts_sorted)

# --- Page 4: Calls Table ---
elif page == "Calls Table":
    st.subheader("Calls (Sorted by Volume)")
    selected_ticker = st.selectbox("Select ticker for calls table:", tickers)
    option_chain = option_chains[selected_ticker]['option_chain']
    st.write(option_chain.calls.sort_values(by='volume', ascending=False))

# --- Page 5: Puts Table ---
elif page == "Puts Table":
    st.subheader("Puts (Sorted by Volume)")
    selected_ticker = st.selectbox("Select ticker for puts table:", tickers)
    option_chain = option_chains[selected_ticker]['option_chain']
    st.write(option_chain.puts.sort_values(by='volume', ascending=False))