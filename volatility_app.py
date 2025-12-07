import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. 页面配置 ---
st.set_page_config(page_title="Volatility Analyzer", layout="wide", page_icon="📈")

# --- 2. 核心算法区 (完全保留你的逻辑) ---
def yang_zhang_volatility(df, window):
    try:
        log_ho = (df['High'] / df['Open']).apply(np.log)
        log_lo = (df['Low'] / df['Open']).apply(np.log)
        log_co = (df['Close'] / df['Open']).apply(np.log)
        log_oc = (df['Open'] / df['Close'].shift(1)).apply(np.log)

        var_open = log_oc.rolling(window).var()
        var_close = log_co.rolling(window).var()

        rs_term = (log_ho * (log_ho - log_co)) + (log_lo * (log_lo - log_co))
        var_rs = rs_term.rolling(window).mean()

        k = 0.34 / (1.34 + (window + 1) / (window - 1))
        yz_variance = var_open + (k * var_close) + ((1 - k) * var_rs)

        # 处理可能出现的负值
        yz_variance = yz_variance.apply(lambda x: x if x > 0 else 0)
        
        return np.sqrt(yz_variance) * np.sqrt(252)
    except Exception as e:
        return pd.Series(index=df.index, dtype='float64')

def calculate_metrics(df, window):
    # Close-to-Close
    c2c = df['Close'].pct_change().apply(np.log1p).rolling(window).std() * np.sqrt(252)

    # Garman-Klass
    log_hl = np.log(df['High'] / df['Low'])
    log_co = np.log(df['Close'] / df['Open'])
    gk_var = 0.5 * log_hl ** 2 - (2 * np.log(2) - 1) * log_co ** 2
    gk = np.sqrt(gk_var.rolling(window).mean()) * np.sqrt(252)

    # Yang-Zhang
    yz = yang_zhang_volatility(df, window)
    return c2c, gk, yz

# --- 3. 数据获取函数 ---
@st.cache_data(ttl=3600) # 缓存数据1小时
def get_stock_data(ticker, start_date, end_date):
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        # yfinance 新版本可能会返回 MultiIndex 列
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # 确保列名大写并去除空格
        df.columns = [c.capitalize().strip() for c in df.columns]
        
        # 简单的数据清洗
        if not {'Open', 'High', 'Low', 'Close'}.issubset(df.columns):
            return None, "数据缺少 OHLC 列，无法计算。"
            
        df = df.sort_index()
        # 过滤无效数据
        df = df[(df['High'] > 0) & (df['Low'] > 0) & (df['Open'] > 0)]
        df = df[df['High'] >= df['Low']]
        
        return df, None
    except Exception as e:
        return None, str(e)

# --- 4. 主界面逻辑 ---
def main():
    st.title("📊 股票波动率分析系统 (Yang-Zhang)")
    st.markdown("基于 `yfinance` 数据 | 支持 HV20 / HV60 / HV90 分析")

    # --- 侧边栏：输入区 ---
    with st.sidebar:
        st.header("⚙️ 参数设置")
        
        # 默认代码
        default_ticker = "BHP.AX" 
        ticker_input = st.text_input("股票代码 (Yahoo 格式)", value=default_ticker, help="澳股请加 .AX，如 CBA.AX。美股直接输入代码，如 AAPL").strip().upper()
        
        # 日期选择
        today = datetime.today()
        start_date = st.date_input("开始日期", value=today - timedelta(days=365*2))
        end_date = st.date_input("结束日期", value=today)
        
        st.markdown("---")
        st.info("💡 **说明**: 图表可交互。鼠标悬停查看数值，拖拽缩放。")

    if ticker_input:
        with st.spinner(f"正在获取 {ticker_input} 数据..."):
            df, error = get_stock_data(ticker_input, start_date, end_date)

        if error:
            st.error(f"无法获取数据: {error}")
        elif df is None or len(df) < 60:
            st.warning("数据不足，无法计算波动率（至少需要60个交易日）。")
        else:
            # --- 计算指标 ---
            df['YZ_20'] = yang_zhang_volatility(df, 20)
            df['YZ_60'] = yang_zhang_volatility(df, 60)
            df['YZ_90'] = yang_zhang_volatility(df, 90)

            last_valid_idx = df['YZ_90'].last_valid_index()
            if last_valid_idx is None:
                 st.error("数据不足以计算长期波动率。")
                 return

            latest_data = df.loc[last_valid_idx]

            # --- 第一部分：关键指标卡片 ---
            st.subheader(f"📈 {ticker_input} 最新波动率概览 ({last_valid_idx.strftime('%Y-%m-%d')})")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("HV 20 (短期)", f"{latest_data['YZ_20']:.2%}", delta_color="off")
            with col2:
                st.metric("HV 60 (中期)", f"{latest_data['YZ_60']:.2%}", delta_color="off")
            with col3:
                st.metric("HV 90 (长期)", f"{latest_data['YZ_90']:.2%}", delta_color="off")

            # --- 第二部分：图表选择 ---
            tab1, tab2 = st.tabs(["🗓️ 期限结构 (Term Structure)", "🔬 方法对比 (Methods)"])

            # Tab 1: 期限结构
            with tab1:
                fig_term = go.Figure()
                fig_term.add_trace(go.Scatter(x=df.index, y=df['YZ_20'], name='HV 20 (Short)', line=dict(color='#ef4444', width=1.5)))
                fig_term.add_trace(go.Scatter(x=df.index, y=df['YZ_60'], name='HV 60 (Med)', line=dict(color='#3b82f6', width=2)))
                fig_term.add_trace(go.Scatter(x=df.index, y=df['YZ_90'], name='HV 90 (Long)', line=dict(color='#10b981', width=2, dash='dash')))
                
                fig_term.update_layout(
                    title=f"{ticker_input} Volatility Term Structure",
                    yaxis_title="Annualized Volatility",
                    yaxis_tickformat='.0%',
                    hovermode="x unified",
                    height=500
                )
                st.plotly_chart(fig_term, use_container_width=True)

            # Tab 2: 方法对比
            with tab2:
                compare_window = st.select_slider("选择对比窗口 (Window)", options=[20, 60, 90], value=20)
                
                c2c, gk, yz = calculate_metrics(df, compare_window)
                
                fig_comp = go.Figure()
                fig_comp.add_trace(go.Scatter(x=df.index, y=c2c, name='Close-to-Close', line=dict(dash='dot', width=1)))
                fig_comp.add_trace(go.Scatter(x=df.index, y=gk, name='Garman-Klass', line=dict(dash='dash', width=1)))
                fig_comp.add_trace(go.Scatter(x=df.index, y=yz, name=f'Yang-Zhang (HV{compare_window})', line=dict(color='purple', width=2.5)))

                fig_comp.update_layout(
                    title=f"Methodology Comparison (Window = {compare_window})",
                    yaxis_title="Annualized Volatility",
                    yaxis_tickformat='.0%',
                    hovermode="x unified",
                    height=500
                )
                st.plotly_chart(fig_comp, use_container_width=True)
            
            # --- 第三部分：查看原始数据 (可选) ---
            with st.expander("查看最近 30 天原始数据"):
                display_cols = ['Open', 'High', 'Low', 'Close', 'YZ_20', 'YZ_60', 'YZ_90']
                st.dataframe(df[display_cols].tail(30).style.format({
                    'Open': '{:.2f}', 'High': '{:.2f}', 'Low': '{:.2f}', 'Close': '{:.2f}',
                    'YZ_20': '{:.2%}', 'YZ_60': '{:.2%}', 'YZ_90': '{:.2%}'
                }))

if __name__ == "__main__":
    main()
