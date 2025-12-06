import streamlit as st
import google.generativeai as genai

# ================= 配置区 =================
st.set_page_config(
    page_title="Sensight 晟策 | 智能投行合伙人",
    page_icon="🧬",
    layout="wide"
)

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/4a90e2/dna-helix.png", width=50)
    st.title("Sensight 晟策")
    st.markdown("---")
    
    # 1. 核心功能选择器 (新增)
    st.subheader("🛠️ 选择生成模块")
    task_type = st.radio(
        "请选择您需要撰写的章节：",
        ("📄 Executive Summary (执行摘要)", "📊 Market & Competition (市场竞品)"),
        captions=["投资亮点、核心数据、融资规划", "TAM/SAM/SOM 测算、竞品格局"]
    )
    
    st.markdown("---")
    
    # 获取 API Key
    api_key = st.text_input("请输入 Google API Key", type="password")
    
    st.info("💡 提示：'市场分析'模块会自动根据您的赛道进行 TAM/SAM/SOM 估算。")
    st.caption("Powered by Gemini 2.5 Pro")

# ================= 核心逻辑区 =================

st.title("🚀 Sensight 晟策 · 商业计划书智能生成")

# 动态显示副标题
if "Market" in task_type:
    st.markdown("### 🔍 模块 B：市场规模与竞争格局分析")
else:
    st.markdown("### 📝 模块 A：执行摘要 (Executive Summary)")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 项目输入")
    project_name = st.text_input("项目名称/代号", placeholder="例如：新型丝素蛋白人造血管")
    
    # 根据不同任务提示不同的输入内容
    if "Market" in task_type:
        placeholder_text = "请提供：\n1. 目标适应症 (如：晚期非小细胞肺癌)\n2. 目标患者人群 (如：中国每年新增 xx 万人)\n3. 主要竞品 (如：泰瑞沙)\n4. 定价策略 (可选)"
    else:
        placeholder_text = "请提供：\n1. 核心技术壁垒\n2. 动物/临床数据\n3. 团队背景\n4. 融资需求"

    raw_text = st.text_area("2. 把您的项目信息丢在这里：", height=400, placeholder=placeholder_text)
    
    generate_btn = st.button(f"✨ 立即生成 {task_type.split(' ')[1]}", type="primary")

with col2:
    st.subheader("3. 交付结果")
    
    if generate_btn:
        if not api_key:
            st.error("请先在左侧侧边栏输入您的 API Key 才能启动大脑。")
        elif not raw_text:
            st.warning("巧妇难为无米之炊，请先输入项目信息。")
        else:
            try:
                genai.configure(api_key=api_key)
                # 使用最强模型
                model = genai.GenerativeModel('gemini-2.5-pro') 
                
                # ================= 提示词路由逻辑 =================
                
                if "Executive Summary" in task_type:
                    # === 提示词 A: 执行摘要 ===
                    system_prompt = """
                    # Role
                    你现在是 Sensight (晟策) 的首席医疗投资顾问。
                    
                    # Task
                    接收用户的输入，重写为 **Executive Summary (执行摘要)**。
                    
                    # Output Format
                    请严格按照以下 Markdown 结构输出：
                    ### [项目名称] - Executive Summary
                    #### 🚀 投资亮点 (Investment Highlights)
                    * **[核心技术]**: (提炼技术壁垒)
                    * **[验证数据]**: (强调动物/临床数据)
                    * **[商业壁垒]**: (强调专利/排他性)
                    #### 🩺 未满足需求 (Unmet Needs)
                    * (描述现有疗法痛点)
                    #### 💡 解决方案 (Solution)
                    * (描述产品优势)
                    #### 📅 融资与规划 (Ask & Milestones)
                    * (描述融资用途及预期节点)
                    """
                
                else:
                    # === 提示词 B: 市场与竞品 (新增) ===
                    system_prompt = """
                    # Role
                    你现在是 Sensight (晟策) 的行业研究员，擅长进行费米估算和竞争格局分析。

                    # Task
                    基于用户输入，撰写 **市场规模 (Market Sizing)** 与 **竞争分析 (Competition)** 章节。
                    
                    # Critical Rule (估算逻辑)
                    如果用户未提供具体市场数据，请利用你作为 LLM 的知识库，**根据适应症的流行病学数据（发病率/患病率）和当前标准疗法费用**，进行合理的 TAM/SAM/SOM 估算，并**必须在括号里注明估算逻辑**。

                    # Output Format
                    请严格按照以下 Markdown 结构输出：
                    ### [项目名称] - 市场与竞品分析

                    #### 📈 市场规模测算 (Market Sizing)
                    > *注：以下数据基于行业公开流行病学数据估算*
                    * **TAM (潜在总市场)**: [金额] 
                        * *测算逻辑*: [目标人群总数] x [年治疗费用]
                    * **SAM (可服务市场)**: [金额]
                        * *测算逻辑*: [符合特定基因型/分期的具体人群] x [渗透率]
                    * **CAGR (年复合增长率)**: [百分比] (预测未来 5 年增长趋势)

                    #### ⚔️ 竞争格局 (Competitive Landscape)
                    | 竞品名称 | 研发阶段 | 靶点/机制 | 劣势/痛点 | 我们的优势 |
                    | :--- | :--- | :--- | :--- | :--- |
                    | [竞品A] | [如: 上市] | [如: EGFR TKI] | [如: 耐药性] | [如: 克服耐药] |
                    | [竞品B] | [如: 临床III期] | ... | ... | ... |
                    
                    #### 🎯 市场准入与策略 (Go-to-Market)
                    * **定价策略**: ...
                    * **医保路径**: ...
                    """
                
                user_prompt = f"项目名称：{project_name}\n项目原始信息：{raw_text}"
                
                with st.spinner(f"Sensight 正在分析{task_type.split(' ')[1]}数据..."):
                    response = model.generate_content(system_prompt + "\n\n" + user_prompt)
                    st.markdown(response.text)
                    st.success("生成完成！您可以直接复制上方内容。")
                    
            except Exception as e:
                st.error(f"发生错误: {e}")
