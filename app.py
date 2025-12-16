import streamlit as st
import time
import google.generativeai as genai
from duckduckgo_search import DDGS
from datetime import datetime

# ==========================================
# 1. 页面配置与黑黄 UI 设计
# ==========================================
st.set_page_config(
    page_title="BioVenture AI - Deep Dive (Gemini)",
    page_icon="🧬",
    layout="wide"
)

# 自定义 CSS：黑黄配色 + 极简专业风
st.markdown("""
<style>
    .stApp {
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
        background-color: #FAFAFA;
    }
    
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E0E0E0;
    }
    
    /* 标题颜色：深黑 */
    h1, h2, h3 {
        color: #1A1A1A !important;
        font-weight: 700;
    }
    
    /* 核心按钮：品牌黄 (#FFD700) */
    div.stButton > button {
        background-color: #FFD700; 
        color: #000000;
        border: none;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #E5C100;
        color: #000000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* 搜索状态条样式 */
    .search-status {
        font-family: 'Courier New', monospace;
        color: #000000;
        background-color: #FFF9C4; /* 浅黄背景 */
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 8px;
        border-left: 4px solid #FFD700; /* 左侧黄色高亮条 */
        font-size: 0.9em;
    }
    
    /* 报告卡片样式 */
    .report-card {
        background: #FFFFFF;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        line-height: 1.6;
    }
    
    /* 代码块高亮 */
    code {
        color: #000000;
        background-color: #FFF9C4;
        border-radius: 4px;
        padding: 2px 4px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心工具函数：实时搜索 (Agent Tools)
# ==========================================

def search_market_intel(query, max_results=3):
    """
    使用 DuckDuckGo 搜索最新的市场情报。
    专门针对 'failure', 'discontinued', 'clinical data' 进行搜索。
    """
    results = []
    current_year = datetime.now().year
    
    # 强制加上年份，确保不抓取旧新闻
    search_query = f"{query} latest clinical data news {current_year}"
    
    try:
        with DDGS() as ddgs:
            ddgs_gen = ddgs.text(search_query, max_results=max_results)
            if ddgs_gen:
                for r in ddgs_gen:
                    results.append(f"- [Title]: {r['title']}\n  [Snippet]: {r['body']}\n  [Source]: {r['href']}")
            else:
                results.append("No immediate search results found via API.")
    except Exception as e:
        results.append(f"Search Tool Error (Network/RateLimit): {str(e)}")
        # 兜底信息，防止报错导致流程中断
        results.append("Note: Live search failed. Analysis will rely on model's internal knowledge.")

    return "\n".join(results)

def generate_vc_prompt(user_input, search_context, language):
    """
    构建 VC 视角的 Prompt，结合搜索到的上下文。
    """
    lang_instruction = "Output strictly in Professional Investment Banking English." if language == "English" else "请使用一级市场投资总监风格的中文输出（拒绝正确的废话，强调数据和风险）。"
    
    prompt = f"""
    {lang_instruction}
    
    You are a cynical, detail-oriented Healthcare Venture Capitalist (VC).
    You are analyzing the following project/sector:
    
    --- USER INPUT ---
    {user_input}
    
    --- REAL-TIME MARKET INTELLIGENCE (LATEST SEARCH DATA) ---
    {search_context}
    
    --- INSTRUCTIONS ---
    1. **Fact Check & Update**: Use the 'Market Intelligence' provided above to correct any outdated knowledge (e.g., if a competitor discontinued a drug in 2024/2025, state it clearly).
    2. **Data Granularity**: 
       - Do NOT say "significant weight loss". 
       - SAY "14.7% weight loss at 36 weeks (Source: Trial Name)".
    3. **Competitive Landscape (The most important part)**:
       - Group competitors into: **Tier 1 (Leaders)**, **Tier 2 (Challengers)**, and **The Graveyard (Failed/Discontinued)**.
       - You MUST identify at least one "failed" or "high risk" competitor if data permits.
    4. **Critical Risk Analysis**:
       - Analyze specific risks: Liver toxicity? Manufacturing costs (COGS)? IP expiration?
    
    Output Structure:
    # Deep Dive Investment Memo: {user_input}
    ## 1. Executive Summary & Investment Verdict (Pass/Watch/Invest)
    ## 2. Market Dynamics (Total Addressable Market & Unmet Needs)
    ## 3. Competitive Landscape (Detailed Table & Analysis)
    ## 4. Key Risks & "The Graveyard" (Who failed and why?)
    ## 5. Conclusion
    """
    return prompt

# ==========================================
# 3. 侧边栏：设置
# ==========================================
with st.sidebar:
    st.image("https://placehold.co/200x60/1A1A1A/FFD700?text=BIO+VENTURE", caption="AI Investment Copilot")
    st.markdown("---")
    
    # 这里特别注明填 Google Key
    api_key = st.text_input("Google Gemini API Key", type="password", placeholder="AIzaSy...")
    
    language = st.radio("Report Language / 报告语言", ["中文", "English"])
    
    st.info("💡 **提示:** 本模式会实时联网搜索最新数据（如辉瑞管线终止、最新 P3 数据），生成比传统 AI 更精准的研报。")
    st.caption("Powered by Google Gemini 1.5 & DuckDuckGo")

# ==========================================
# 4. 主界面逻辑
# ==========================================
st.title("🔎 VC-Grade Deep Dive System")
st.markdown("Enter a target (Molecule, Company, Mechanism) to generate a **Live Due Diligence Report**.")

# 默认值设为口服 GLP-1，方便演示
query = st.text_input("Research Target", value="Oral GLP-1 agonist competitive landscape")

if st.button("Start Due Diligence / 开始深度尽调"):
    if not api_key:
        st.error("❌ 请在侧边栏输入 Google Gemini API Key (以 AIzaSy 开头)")
    else:
        # 占位符
        main_placeholder = st.empty()
        status_box = st.empty()
        
        # --- PHASE 1: 联网侦察 (Agent Search) ---
        status_box.markdown(f"""
        <div class="search-status">
        ⚙️ <strong>Agent Activated</strong><br>
        > Analyzing Intent: {query}<br>
        > Strategy: Hunting for latest clinical data & failures...
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1)
        
        # 定义搜索策略：搜数据，搜失败案例，搜最新报告
        search_queries = [
            f"{query} clinical trial results phase 3 2024 2025",
            f"{query} discontinued failed clinical trials news", # 专门找负面
        ]
        
        full_search_context = ""
        
        for q in search_queries:
            status_box.markdown(f"""
            <div class="search-status">
            🔍 <strong>Live Searching...</strong><br>
            > Query: "{q}"
            </div>
            """, unsafe_allow_html=True)
            
            # 执行搜索
            results = search_market_intel(q)
            full_search_context += f"\n[Search Query]: {q}\n[Results]:\n{results}\n"
            time.sleep(0.5) # 稍微停顿，模拟思考
            
        status_box.markdown(f"""
        <div class="search-status">
        ✅ <strong>Data Retrieval Complete</strong><br>
        > Synthesizing market intelligence...<br>
        > Applying VC investment logic (Gemini 1.5)...
        </div>
        """, unsafe_allow_html=True)

        # --- PHASE 2: 生成报告 (Gemini Generation) ---
        try:
            # 配置 Google Gemini
            genai.configure(api_key=api_key)
            
            # 使用 gemini-1.5-flash (速度快) 或 gemini-1.5-pro (逻辑强)
            # 这里默认用 1.5-flash 以确保响应速度，如果你有 pro 权限可以改名
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            final_prompt = generate_vc_prompt(query, full_search_context, language)
            
            # 流式生成
            response_stream = model.generate_content(final_prompt, stream=True)
            
            report_text = ""
            for chunk in response_stream:
                if chunk.text:
                    report_text += chunk.text
                    # 实时渲染 Markdown + 光标效果
                    main_placeholder.markdown(f"""
                    <div class="report-card">
                    {report_text}
                    <span style="color:#FFD700;">▍</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 最终渲染（移除光标）
            main_placeholder.markdown(f"""
            <div class="report-card">
            {report_text}
            </div>
            """, unsafe_allow_html=True)
            
            status_box.empty() # 移除状态栏，保持界面干净
            
        except Exception as e:
            st.error(f"❌ Gemini API Error: {str(e)}")
            st.warning("常见原因：Key 无效、该 Key 未开通 Gemini API 权限、或免费版每分钟请求超限。")

# ==========================================
# 5. 底部版权
# ==========================================
st.markdown("---")
st.caption("© 2025 BioVenture Agent. Generated content is for reference only.")
