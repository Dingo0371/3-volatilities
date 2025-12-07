{\rtf1\ansi\ansicpg936\cocoartf2636
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\fnil\fcharset134 PingFangSC-Regular;\f2\fnil\fcharset0 AppleColorEmoji;
}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import yfinance as yf\
import numpy as np\
import pandas as pd\
import plotly.graph_objects as go\
from plotly.subplots import make_subplots\
from datetime import datetime, timedelta\
\
# --- 1. 
\f1 \'d2\'b3\'c3\'e6\'c5\'e4\'d6\'c3
\f0  ---\
st.set_page_config(page_title="Volatility Analyzer", layout="wide", page_icon="
\f2 \uc0\u55357 \u56520 
\f0 ")\
\
# --- 2. 
\f1 \'ba\'cb\'d0\'c4\'cb\'e3\'b7\'a8\'c7\'f8
\f0  (
\f1 \'cd\'ea\'c8\'ab\'b1\'a3\'c1\'f4\'c4\'e3\'b5\'c4\'c2\'df\'bc\'ad
\f0 ) ---\
def yang_zhang_volatility(df, window):\
    try:\
        log_ho = (df['High'] / df['Open']).apply(np.log)\
        log_lo = (df['Low'] / df['Open']).apply(np.log)\
        log_co = (df['Close'] / df['Open']).apply(np.log)\
        log_oc = (df['Open'] / df['Close'].shift(1)).apply(np.log)\
\
        var_open = log_oc.rolling(window).var()\
        var_close = log_co.rolling(window).var()\
\
        rs_term = (log_ho * (log_ho - log_co)) + (log_lo * (log_lo - log_co))\
        var_rs = rs_term.rolling(window).mean()\
\
        k = 0.34 / (1.34 + (window + 1) / (window - 1))\
        yz_variance = var_open + (k * var_close) + ((1 - k) * var_rs)\
\
        # 
\f1 \'b4\'a6\'c0\'ed\'bf\'c9\'c4\'dc\'b3\'f6\'cf\'d6\'b5\'c4\'b8\'ba\'d6\'b5\'a3\'a8\'cb\'e4\'c8\'bb\'c0\'ed\'c2\'db\'c9\'cf\'b2\'bb\'bb\'e1\'a3\'ac\'b5\'ab\'d4\'da\'bc\'ab\'b6\'cb\'ca\'fd\'be\'dd\'c8\'b1\'ca\'a7\'cf\'c2\'bf\'c9\'c4\'dc\'b7\'a2\'c9\'fa\'a3\'a9
\f0 \
        yz_variance = yz_variance.apply(lambda x: x if x > 0 else 0)\
        \
        return np.sqrt(yz_variance) * np.sqrt(252)\
    except Exception as e:\
        return pd.Series(index=df.index, dtype='float64')\
\
def calculate_metrics(df, window):\
    # Close-to-Close\
    c2c = df['Close'].pct_change().apply(np.log1p).rolling(window).std() * np.sqrt(252)\
\
    # Garman-Klass\
    log_hl = np.log(df['High'] / df['Low'])\
    log_co = np.log(df['Close'] / df['Open'])\
    gk_var = 0.5 * log_hl ** 2 - (2 * np.log(2) - 1) * log_co ** 2\
    gk = np.sqrt(gk_var.rolling(window).mean()) * np.sqrt(252)\
\
    # Yang-Zhang\
    yz = yang_zhang_volatility(df, window)\
    return c2c, gk, yz\
\
# --- 3. 
\f1 \'ca\'fd\'be\'dd\'bb\'f1\'c8\'a1\'ba\'af\'ca\'fd
\f0  ---\
@st.cache_data(ttl=3600) # 
\f1 \'bb\'ba\'b4\'e6\'ca\'fd\'be\'dd
\f0 1
\f1 \'d0\'a1\'ca\'b1\'a3\'ac\'b1\'dc\'c3\'e2\'d6\'d8\'b8\'b4\'cf\'c2\'d4\'d8
\f0 \
def get_stock_data(ticker, start_date, end_date):\
    try:\
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)\
        \
        # yfinance 
\f1 \'d0\'c2\'b0\'e6\'b1\'be\'bf\'c9\'c4\'dc\'bb\'e1\'b7\'b5\'bb\'d8
\f0  MultiIndex 
\f1 \'c1\'d0
\f0  (Ticker, Price Type)
\f1 \'a3\'ac\'d0\'e8\'d2\'aa\'b1\'e2\'c6\'bd\'bb\'af
\f0 \
        if isinstance(df.columns, pd.MultiIndex):\
            df.columns = df.columns.get_level_values(0)\
            \
        # 
\f1 \'c8\'b7\'b1\'a3\'c1\'d0\'c3\'fb\'b4\'f3\'d0\'b4\'b2\'a2\'c8\'a5\'b3\'fd\'bf\'d5\'b8\'f1
\f0 \
        df.columns = [c.capitalize().strip() for c in df.columns]\
        \
        # 
\f1 \'bc\'f2\'b5\'a5\'b5\'c4\'ca\'fd\'be\'dd\'c7\'e5\'cf\'b4
\f0 \
        if not \{'Open', 'High', 'Low', 'Close'\}.issubset(df.columns):\
            return None, "
\f1 \'ca\'fd\'be\'dd\'c8\'b1\'c9\'d9
\f0  OHLC 
\f1 \'c1\'d0\'a3\'ac\'ce\'de\'b7\'a8\'bc\'c6\'cb\'e3\'a1\'a3
\f0 "\
            \
        df = df.sort_index()\
        # 
\f1 \'b9\'fd\'c2\'cb\'ce\'de\'d0\'a7\'ca\'fd\'be\'dd
\f0 \
        df = df[(df['High'] > 0) & (df['Low'] > 0) & (df['Open'] > 0)]\
        df = df[df['High'] >= df['Low']]\
        \
        return df, None\
    except Exception as e:\
        return None, str(e)\
\
# --- 4. 
\f1 \'d6\'f7\'bd\'e7\'c3\'e6\'c2\'df\'bc\'ad
\f0  ---\
def main():\
    st.title("
\f2 \uc0\u55357 \u56522 
\f0  
\f1 \'b9\'c9\'c6\'b1\'b2\'a8\'b6\'af\'c2\'ca\'b7\'d6\'ce\'f6\'cf\'b5\'cd\'b3
\f0  (Yang-Zhang)")\
    st.markdown("
\f1 \'bb\'f9\'d3\'da
\f0  `yfinance` 
\f1 \'ca\'fd\'be\'dd
\f0  | 
\f1 \'d6\'a7\'b3\'d6
\f0  HV20 / HV60 / HV90 
\f1 \'b7\'d6\'ce\'f6
\f0 ")\
\
    # --- 
\f1 \'b2\'e0\'b1\'df\'c0\'b8\'a3\'ba\'ca\'e4\'c8\'eb\'c7\'f8
\f0  ---\
    with st.sidebar:\
        st.header("
\f2 \uc0\u9881 \u65039 
\f0  
\f1 \'b2\'ce\'ca\'fd\'c9\'e8\'d6\'c3
\f0 ")\
        \
        # 
\f1 \'c4\'ac\'c8\'cf\'b4\'fa\'c2\'eb\'a3\'ba\'c8\'e7\'b9\'fb\'ca\'c7\'b0\'c4\'b9\'c9\'a3\'ac
\f0 yfinance 
\f1 \'d0\'e8\'d2\'aa\'bc\'d3
\f0  .AX
\f1 \'a3\'ac\'c0\'fd\'c8\'e7
\f0  BHP.AX\
        default_ticker = "BHP.AX" \
        ticker_input = st.text_input("
\f1 \'b9\'c9\'c6\'b1\'b4\'fa\'c2\'eb
\f0  (Yahoo 
\f1 \'b8\'f1\'ca\'bd
\f0 )", value=default_ticker, help="
\f1 \'b0\'c4\'b9\'c9\'c7\'eb\'bc\'d3
\f0  .AX
\f1 \'a3\'ac\'c8\'e7
\f0  CBA.AX
\f1 \'a1\'a3\'c3\'c0\'b9\'c9\'d6\'b1\'bd\'d3\'ca\'e4\'c8\'eb\'b4\'fa\'c2\'eb\'a3\'ac\'c8\'e7
\f0  AAPL").strip().upper()\
        \
        # 
\f1 \'c8\'d5\'c6\'da\'d1\'a1\'d4\'f1
\f0 \
        today = datetime.today()\
        start_date = st.date_input("
\f1 \'bf\'aa\'ca\'bc\'c8\'d5\'c6\'da
\f0 ", value=today - timedelta(days=365*2)) # 
\f1 \'c4\'ac\'c8\'cf\'bf\'b4\'c1\'bd\'c4\'ea
\f0 \
        end_date = st.date_input("
\f1 \'bd\'e1\'ca\'f8\'c8\'d5\'c6\'da
\f0 ", value=today)\
        \
        st.markdown("---")\
        st.info("
\f2 \uc0\u55357 \u56481 
\f0  **
\f1 \'cb\'b5\'c3\'f7
\f0 **: 
\f1 \'cd\'bc\'b1\'ed\'bf\'c9\'bd\'bb\'bb\'a5\'a1\'a3\'ca\'f3\'b1\'ea\'d0\'fc\'cd\'a3\'b2\'e9\'bf\'b4\'ca\'fd\'d6\'b5\'a3\'ac\'cd\'cf\'d7\'a7\'cb\'f5\'b7\'c5\'a1\'a3
\f0 ")\
\
    if ticker_input:\
        with st.spinner(f"
\f1 \'d5\'fd\'d4\'da\'bb\'f1\'c8\'a1
\f0  \{ticker_input\} 
\f1 \'ca\'fd\'be\'dd
\f0 ..."):\
            df, error = get_stock_data(ticker_input, start_date, end_date)\
\
        if error:\
            st.error(f"
\f1 \'ce\'de\'b7\'a8\'bb\'f1\'c8\'a1\'ca\'fd\'be\'dd
\f0 : \{error\}")\
        elif df is None or len(df) < 60:\
            st.warning("
\f1 \'ca\'fd\'be\'dd\'b2\'bb\'d7\'e3\'a3\'ac\'ce\'de\'b7\'a8\'bc\'c6\'cb\'e3\'b2\'a8\'b6\'af\'c2\'ca\'a3\'a8\'d6\'c1\'c9\'d9\'d0\'e8\'d2\'aa
\f0 60
\f1 \'b8\'f6\'bd\'bb\'d2\'d7\'c8\'d5\'a3\'a9\'a1\'a3
\f0 ")\
        else:\
            # --- 
\f1 \'bc\'c6\'cb\'e3\'d6\'b8\'b1\'ea
\f0  ---\
            df['YZ_20'] = yang_zhang_volatility(df, 20)\
            df['YZ_60'] = yang_zhang_volatility(df, 60)\
            df['YZ_90'] = yang_zhang_volatility(df, 90)\
\
            last_valid_idx = df['YZ_90'].last_valid_index()\
            if last_valid_idx is None:\
                 st.error("
\f1 \'ca\'fd\'be\'dd\'b2\'bb\'d7\'e3\'d2\'d4\'bc\'c6\'cb\'e3\'b3\'a4\'c6\'da\'b2\'a8\'b6\'af\'c2\'ca\'a1\'a3
\f0 ")\
                 return\
\
            latest_data = df.loc[last_valid_idx]\
\
            # --- 
\f1 \'b5\'da\'d2\'bb\'b2\'bf\'b7\'d6\'a3\'ba\'b9\'d8\'bc\'fc\'d6\'b8\'b1\'ea\'bf\'a8\'c6\'ac
\f0  ---\
            st.subheader(f"
\f2 \uc0\u55357 \u56520 
\f0  \{ticker_input\} 
\f1 \'d7\'ee\'d0\'c2\'b2\'a8\'b6\'af\'c2\'ca\'b8\'c5\'c0\'c0
\f0  (\{last_valid_idx.strftime('%Y-%m-%d')\})")\
            \
            col1, col2, col3 = st.columns(3)\
            with col1:\
                st.metric("HV 20 (
\f1 \'b6\'cc\'c6\'da
\f0 )", f"\{latest_data['YZ_20']:.2%\}", delta_color="off")\
            with col2:\
                st.metric("HV 60 (
\f1 \'d6\'d0\'c6\'da
\f0 )", f"\{latest_data['YZ_60']:.2%\}", delta_color="off")\
            with col3:\
                st.metric("HV 90 (
\f1 \'b3\'a4\'c6\'da
\f0 )", f"\{latest_data['YZ_90']:.2%\}", delta_color="off")\
\
            # --- 
\f1 \'b5\'da\'b6\'fe\'b2\'bf\'b7\'d6\'a3\'ba\'cd\'bc\'b1\'ed\'d1\'a1\'d4\'f1
\f0  ---\
            tab1, tab2 = st.tabs(["
\f2 \uc0\u55357 \u56787 \u65039 
\f0  
\f1 \'c6\'da\'cf\'de\'bd\'e1\'b9\'b9
\f0  (Term Structure)", "
\f2 \uc0\u55357 \u56620 
\f0  
\f1 \'b7\'bd\'b7\'a8\'b6\'d4\'b1\'c8
\f0  (Methods)"])\
\
            # Tab 1: 
\f1 \'c6\'da\'cf\'de\'bd\'e1\'b9\'b9
\f0  (20 vs 60 vs 90)\
            with tab1:\
                fig_term = go.Figure()\
                fig_term.add_trace(go.Scatter(x=df.index, y=df['YZ_20'], name='HV 20 (Short)', line=dict(color='#ef4444', width=1.5)))\
                fig_term.add_trace(go.Scatter(x=df.index, y=df['YZ_60'], name='HV 60 (Med)', line=dict(color='#3b82f6', width=2)))\
                fig_term.add_trace(go.Scatter(x=df.index, y=df['YZ_90'], name='HV 90 (Long)', line=dict(color='#10b981', width=2, dash='dash')))\
                \
                fig_term.update_layout(\
                    title=f"\{ticker_input\} Volatility Term Structure",\
                    yaxis_title="Annualized Volatility",\
                    yaxis_tickformat='.0%',\
                    hovermode="x unified",\
                    height=500\
                )\
                st.plotly_chart(fig_term, use_container_width=True)\
\
            # Tab 2: 
\f1 \'b7\'bd\'b7\'a8\'b6\'d4\'b1\'c8
\f0  (User original logic: C2C vs GK vs YZ)\
            with tab2:\
                compare_window = st.select_slider("
\f1 \'d1\'a1\'d4\'f1\'b6\'d4\'b1\'c8\'b4\'b0\'bf\'da
\f0  (Window)", options=[20, 60, 90], value=20)\
                \
                c2c, gk, yz = calculate_metrics(df, compare_window)\
                \
                fig_comp = go.Figure()\
                fig_comp.add_trace(go.Scatter(x=df.index, y=c2c, name='Close-to-Close', line=dict(dash='dot', width=1)))\
                fig_comp.add_trace(go.Scatter(x=df.index, y=gk, name='Garman-Klass', line=dict(dash='dash', width=1)))\
                fig_comp.add_trace(go.Scatter(x=df.index, y=yz, name=f'Yang-Zhang (HV\{compare_window\})', line=dict(color='purple', width=2.5)))\
\
                fig_comp.update_layout(\
                    title=f"Methodology Comparison (Window = \{compare_window\})",\
                    yaxis_title="Annualized Volatility",\
                    yaxis_tickformat='.0%',\
                    hovermode="x unified",\
                    height=500\
                )\
                st.plotly_chart(fig_comp, use_container_width=True)\
            \
            # --- 
\f1 \'b5\'da\'c8\'fd\'b2\'bf\'b7\'d6\'a3\'ba\'b2\'e9\'bf\'b4\'d4\'ad\'ca\'bc\'ca\'fd\'be\'dd
\f0  (
\f1 \'bf\'c9\'d1\'a1
\f0 ) ---\
            with st.expander("
\f1 \'b2\'e9\'bf\'b4\'d7\'ee\'bd\'fc
\f0  30 
\f1 \'cc\'ec\'d4\'ad\'ca\'bc\'ca\'fd\'be\'dd
\f0 "):\
                display_cols = ['Open', 'High', 'Low', 'Close', 'YZ_20', 'YZ_60', 'YZ_90']\
                st.dataframe(df[display_cols].tail(30).style.format(\{\
                    'Open': '\{:.2f\}', 'High': '\{:.2f\}', 'Low': '\{:.2f\}', 'Close': '\{:.2f\}',\
                    'YZ_20': '\{:.2%\}', 'YZ_60': '\{:.2%\}', 'YZ_90': '\{:.2%\}'\
                \}))\
\
if __name__ == "__main__":\
    main()}