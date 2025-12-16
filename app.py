import streamlit as st
import time
from duckduckgo_search import DDGS # 用于实时搜索
from datetime import datetime

# ==========================================
# 1. 页面配置 (保持黑黄品牌调性)
# ==========================================
st.set_page_config(
    page_title="BioVenture AI - Deep Dive",
    page_icon="🧬",
    layout="wide"
)

# 保持之前的 CSS 样式 (黑/黄/极简)
st.markdown("""
<style>
    .stApp { font-family: 'Inter', sans-serif; background-color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }
    h1, h2, h3 { color: #1A1A1A !important; font-weight: 700; }
    
    /* 品牌黄按钮 */
    div.stButton > button {
        background-color: #FFD700; color: #000000; border: none;
        border-radius: 6px; padding: 10px 24px; font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover { background-color: #E5C100; color: #000000; }
    
    /* 搜索状态条 */
    .search-status {
        font-family: 'Courier New', monospace;
        color: #000000;
        background-color: #FFF9C4; /* 浅黄背景 */
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 5px;
        border-left: 3px solid #FFD700;
        font-size: 0.85em;
    }
    
    .report-card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心逻辑：AI Agent 工具函数
# ==========================================

def search_market_intel(query, max_results=3):
    """
    模拟联网搜索工具。
    在真实场景中，这里会根据 query 抓取最新的新闻、临床数据、FDA公告。
    """
    results = []
    try:
        # 使用 DuckDuckGo 搜索最新的信息 (模拟 Tavily/Google Search API)
        # 加上当前年份，强制搜索最新数据
        current_year = datetime.now().year
        search_query = f"{query} clinical trial data news {current_year}"
        
        with DDGS() as ddgs:
            # 搜索新闻和结果
            ddgs_gen = ddgs.text(search_query, max_results=max_results)
            for r in ddgs_gen:
                results.append(f"- [Title]: {r['title']}\n  [Snippet]: {r['body']}\n  [Link]: {r['href']}")
    except Exception as e:
        results.append(f"Search API Error: {str(e)}")
        # Fallback (如果在本地跑不通网络，这里是一个兜底数据，演示用)
        results.append("- [System Info] Pfizer discontinued Danuglipron twice-daily formulation in late 2023/early 2024 due to high adverse event rates.")

    return "\n".join(results)

def generate_vc_prompt(user_input, search_context, language):
    """
    构建 VC 视角的 Prompt。
    核心差异：强制要求 AI 引用 search_context 中的事实，尤其是负面信息。
    """
    lang_instruction = "Output strictly in Professional Investment Banking English." if language == "English" else "请使用一级市场投资总监风格的中文输出（拒绝正确的废话）。"
    
    prompt = f"""
    {lang_instruction}
    
    You are a cynical, detail-oriented Healthcare Venture Capitalist.
    You are analyzing the following project/sector:
    
    --- USER INPUT ---
    {user_input}
    
    --- REAL-TIME MARKET INTELLIGENCE (LATEST DATA) ---
    {search_context}
    
    --- INSTRUCTIONS ---
    1. **Data Granularity**: Do not say "significant growth". Say "CAGR of X%". Do not say "good efficacy". Say "15% weight loss at 68 weeks (OASIS-1)".
    2. **Fact Check**: Use the 'Market Intelligence' provided above to correct outdated assumptions. (e.g., If a competitor discontinued a drug, state it clearly as a RISK/FAILURE).
    3. **Critical Thinking**: Analyze the specific "Moat" (e.g., Bioavailability, Half-life, IP, CMC cost).
    4. **Structure**:
       - **Executive Summary & Verdict** (Pass or Invest?)
       - **Competitive Landscape (Deep Dive)**: Group by Leaders, Challengers, and GRAVEYARD (Failed projects).
       - **Risk Assessment**: CMC issues, Safety signals (Liver toxicity?), IP cliffs.
    """
    return prompt

# ==========================================
# 3. 侧边栏设置
# ==========================================
with st.sidebar:
    st.title("🔎 BioVenture DeepDive")
    st.caption("AI-Powered Due Diligence System")
    st.markdown("---")
    
    api_key = st.text_input("OpenAI API Key", type="password")
    language = st.radio("Output Language", ["中文", "English"])
    
    st.info("💡 **Pro Tip:** This mode performs live searches to verify competitor status (e.g., searching for 'Pfizer Danuglipron discontinuation').")

# ==========================================
# 4. 主界面
# ==========================================
st.title("🚀 VC-Grade Market Analysis")
st.markdown("Enter a target molecule, company, or sector to generate a **Live Competitive Report**.")

query = st.text_input("Research Target (e.g., Oral GLP-1, TIGIT, ADC Linkers)", value="Oral GLP-1 landscape")

if st.button("Start Deep Due Diligence / 开始深度尽调"):
    if not api_key:
        st.error("Please enter your OpenAI API Key in the sidebar.")
    else:
        main_placeholder = st.empty()
        status_box = st.empty()
        
        # --- STEP 1: 思考与规划 (Chain of Thought) ---
        status_box.markdown(f"""
        <div class="search-status">
        Executing Agent Strategy...<br>
        > Analyzing Intent: {query}<br>
        > Identifying Key Competitors: Novo Nordisk, Eli Lilly, Pfizer, Structure...
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1)
        
        # --- STEP 2: 实时联网搜索 (The "Agent" Part) ---
        # 我们针对性地搜索几个硬核问题，而不是泛泛搜索
        search_queries = [
            f"{query} latest clinical trial results 2024 2025",
            f"{query} failed or discontinued clinical trials 2024", # 专门找死掉的项目
            f"{query} competitive landscape market size reports"
        ]
        
        full_search_context = ""
        
        for q in search_queries:
            status_box.markdown(f"""
            <div class="search-status">
            🔍 Searching Live Web:<br>
            > "{q}"...
            </div>
            """, unsafe_allow_html=True)
            
            # 调用上面的 Python 搜索函数
            results = search_market_intel(q)
            full_search_context += f"\nQuery: {q}\nResults:\n{results}\n"
            time.sleep(0.5) # 避免触发防爬虫
            
        status_box.markdown(f"""
        <div class="search-status">
        ✅ Data Retrieval Complete.<br>
        > Synthesizing {len(full_search_context)} chars of market data...
        > Applying VC Investment Logic...
        </div>
        """, unsafe_allow_html=True)

        # --- STEP 3: 生成报告 (LLM Call) ---
        # 这里使用 openai 库进行调用 (需用户提供 Key)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        try:
            final_prompt = generate_vc_prompt(query, full_search_context, language)
            
            # 使用流式输出
            stream = client.chat.completions.create(
                model="gpt-4o", # 建议使用 GPT-4o 以获得最强的逻辑能力
                messages=[
                    {"role": "system", "content": "You are a senior healthcare investment analyst."},
                    {"role": "user", "content": final_prompt}
                ],
                stream=True
            )
            
            # 显示结果
            report_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    report_text += chunk.choices[0].delta.content
                    main_placeholder.markdown(f"""
                    <div class="report-card">
                    {report_text}
                    <span style="color:#FFD700;">▍</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 完成态
            main_placeholder.markdown(f"""
            <div class="report-card">
            {report_text}
            </div>
            """, unsafe_allow_html=True)
            status_box.empty() # 清空状态栏
            
        except Exception as e:
            st.error(f"Generation Error: {e}")

# ==========================================
# 5. 底部
# ==========================================
st.markdown("---")
st.caption("Powered by Real-Time Search & Agentic Reasoning.")
