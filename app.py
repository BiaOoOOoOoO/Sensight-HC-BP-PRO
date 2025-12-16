import streamlit as st
import time

# ==========================================
# 1. 页面配置与 UI/UX 优化 (符合黑/黄品牌色)
# ==========================================
st.set_page_config(
    page_title="BioVenture AI - BP Generator",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS：黑黄配色 + 专业排版
st.markdown("""
<style>
    /* 全局字体优化 */
    .stApp {
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
    }
    
    /* 侧边栏背景色 - 极简白或浅灰，避免过于压抑 */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E0E0E0;
    }

    /* 标题颜色 - 深黑色 */
    h1, h2, h3 {
        color: #1A1A1A !important;
        font-weight: 700;
    }

    /* 关键按钮样式 - 品牌黄底，黑字，圆角 */
    div.stButton > button {
        background-color: #FFD700; 
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #E5C100; /* 悬停稍微变深 */
        color: #000000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    /* 下拉框和输入框的聚焦边框色 - 品牌黄 */
    div[data-baseweb="select"] > div:focus-within, 
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within {
        border-color: #FFD700 !important;
        box-shadow: 0 0 0 1px #FFD700 !important;
    }

    /* 报告生成区域的卡片样式 */
    .report-container {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* 模拟 Markdown 中的高亮 */
    code {
        color: #000000;
        background-color: #FFF9C4; /* 浅黄色背景高亮 */
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 侧边栏：设置与输入 (中英文切换 + 全模态)
# ==========================================
with st.sidebar:
    st.image("https://placehold.co/200x60/1A1A1A/FFD700?text=BIO+VENTURE", caption="AI Powered Investment Banking") # 模拟你的Logo
    
    st.markdown("---")
    
    # --- 需求点 2: 中英文选项 ---
    lang_choice = st.radio(
        "Interface & Output Language / 语言设置",
        ("中文", "English"),
        horizontal=True
    )
    
    is_cn = lang_choice == "中文"
    
    # 动态标签文本
    lbl_modality = "选择核心模态 (Modality)" if is_cn else "Select Core Modality"
    lbl_stage = "融资阶段 (Stage)" if is_cn else "Funding Stage"
    lbl_input = "输入核心材料 (Input Data)" if is_cn else "Input Core Data"
    lbl_btn = "生成商业计划书 (Generate BP)" if is_cn else "Generate Business Plan"
    lbl_other_placeholder = "请输入具体模态" if is_cn else "Please specify modality"

    # --- 需求点 1: 完善的模态列表 ---
    modality_options = [
        "小分子 (Small Molecule) - Target/PROTAC",
        "抗体药物 (Antibody) - mAb/BsAb/ADC",
        "细胞治疗 (Cell Therapy) - CAR-T/NK/TILs/Stem Cell",
        "基因治疗 (Gene Therapy) - AAV/Lentiviral/CRISPR",
        "核酸药物 (Nucleic Acid) - mRNA/siRNA/ASO",
        "多肽与蛋白 (Peptides & Proteins) - Peptides/Fusion Proteins", # 新增
        "核药 (Radiopharmaceuticals) - RDC/Dx", # 新增
        "合成生物学 (Synthetic Biology)",
        "医疗器械/IVD (MedTech/IVD)",
        "AI制药/数字疗法 (AI Drug Discovery/DTx)",
        "其他 (Other)" # 留口子
    ]
    
    selected_modality = st.selectbox(lbl_modality, modality_options)
    
    # 如果选了其他，显示输入框
    final_modality = selected_modality
    if "其他 (Other)" in selected_modality:
        custom_modality = st.text_input("Specify Other Modality", placeholder=lbl_other_placeholder)
        if custom_modality:
            final_modality = custom_modality

    st.markdown("---")
    
    # 简单的其他输入
    project_stage = st.selectbox(lbl_stage, ["Angel/Seed", "Pre-A", "Series A", "Series B+"])

# ==========================================
# 3. 主界面逻辑
# ==========================================

st.title("🏥 BioMed BP Generator")
st.markdown(f"**Current Mode:** `{final_modality}` | **Language:** `{lang_choice}`")

# 输入区域
user_input = st.text_area(
    lbl_input, 
    height=200, 
    placeholder="在此粘贴技术文档、专利摘要、或者简单的项目想法...\n(Paste your technical docs, patent abstract, or rough ideas here...)"
)

# 模拟大模型生成函数 (Prompt Logic)
def generate_prompt_logic(input_text, modality, lang):
    """
    这里构建发给 LLM 的 Prompt。
    核心是：无论用户输入什么语言，都强制要求 LLM 按照 `lang` 参数输出。
    """
    system_instruction = ""
    if lang == "English":
        system_instruction = """
        You are a professional Healthcare Investment Banker. 
        Please analyze the input data and generate a comprehensive Business Plan in **English**.
        Structure the output strictly as:
        1. Executive Summary
        2. Market Size & Unmet Needs
        3. Competitive Landscape (Present as a Markdown Table)
        4. Technology & Moat (Highlighting modality: {modality})
        5. Financial Projections
        """
    else:
        system_instruction = """
        你是一位专业的医疗健康领域投资银行家。
        请分析输入材料，并撰写一份专业的**中文**商业计划书。
        输出结构必须包含（不要分开回答，一次性输出）：
        1. 执行摘要 (Executive Summary)
        2. 市场空间与未满足需求 (Market Size & Unmet Needs)
        3. 竞品分析 (Competitive Landscape) - 请使用 Markdown 表格形式
        4. 技术壁垒与创新点 (Technology & Moat) - 重点结合模态：{modality}
        5. 财务预测与融资规划
        """
    return system_instruction

# ==========================================
# 4. 生成与流式输出 (拒绝假动画)
# ==========================================

if st.button(lbl_btn):
    if not user_input:
        st.warning("⚠️ 请先输入项目信息 (Please input project data first).")
    else:
        # --- 需求点 4: 一次性生成所有内容 ---
        # --- 需求点 3: 真实流式体验 (Streaming) ---
        
        # 占位符
        report_box = st.empty()
        
        # 这里模拟 LLM 的流式返回。
        # 在实际开发中，这里会替换为 OpenAI/Anthropic API 的 stream=True 调用
        
        # 模拟生成的中文内容
        simulated_response_cn = f"""
# {final_modality} 项目商业计划书

## 1. 执行摘要 (Executive Summary)
本项目旨在开发针对实体瘤的下一代 **{final_modality}**。基于初步数据，我们的先导管线在小鼠模型中显示出优于标准疗法（SoC）3倍的抑瘤率。核心团队来自哈佛医学院及罗氏研发中心，拥有平均15年的新药研发经验。

## 2. 市场空间 (Market Size)
全球肿瘤药物市场预计在2028年达到3000亿美元。
* **痛点：** 现有疗法耐药性高，副作用大。
* **TAM (潜在市场总额)：** 500亿美元。
* **SOM (可服务市场)：** 预计首款产品上市后峰值销售额可达 8亿美元。

## 3. 竞品分析 (Competitive Landscape)

| 竞品公司 | 技术路线 | 临床阶段 | 优势 | 劣势 |
| :--- | :--- | :--- | :--- | :--- |
| **本项目** | **{final_modality} (Next-Gen)** | **PCC** | **高亲和力，低脱靶毒性** | **早期阶段** |
| Competitor A | 传统单抗 | Phase II | 临床数据成熟 | 疗效天花板明显 |
| Competitor B | 第一代 ADC | Phase I | 杀伤力强 | 严重的血液毒性 |

## 4. 技术壁垒 (Technical Moat)
我们采用了独有的 **"Bio-Lock" 连接技术**，解决了 {final_modality} 常见的稳定性问题。
> 核心专利已提交 PCT 申请 (PCT/CN2024/XXXXX)。

## 5. 融资规划
计划融资：**3000万 RMB**，用于推进 PCC 筛选至 IND 申报。
"""

        # 模拟生成的英文内容
        simulated_response_en = f"""
# {final_modality} Business Plan

## 1. Executive Summary
This project focuses on developing next-generation **{final_modality}** for solid tumors. Preliminary data indicates superior efficacy with a 3x tumor inhibition rate compared to SoC in mouse models. The team comprises veterans from Harvard Medical School and Roche R&D.

## 2. Market Size & Unmet Needs
The global oncology market is projected to reach $300B by 2028.
* **Unmet Need:** High resistance rates and toxicity in current therapies.
* **TAM:** $50B.
* **SOM:** Projected peak sales of $800M.

## 3. Competitive Landscape

| Company | Modality | Stage | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **Our Project** | **{final_modality}** | **PCC** | **High Affinity, Low Toxicity** | **Early Stage** |
| Competitor A | Traditional mAb | Phase II | Clinical Data | Efficacy Ceiling |
| Competitor B | 1st Gen ADC | Phase I | Potency | Hematotoxicity |

## 4. Technical Moat
Proprietary **"Bio-Lock" Linker Technology** addresses stability issues inherent in {final_modality}.
> Core IP submitted via PCT (PCT/US2024/XXXXX).

## 5. Use of Proceeds
Seeking **$4M USD** to advance from PCC selection to IND submission.
"""
        
        # 选择要展示的模拟文本
        full_response = simulated_response_cn if is_cn else simulated_response_en
        
        # --- 模拟打字机效果 (Streaming Effect) ---
        displayed_text = ""
        # 模拟思考延迟
        with st.spinner("Analyzing input data & Structuring models..."): 
            time.sleep(1.5) 
        
        # 开始逐字输出
        for char in full_response:
            displayed_text += char
            # 每次更新都重新渲染 Markdown，这就是真实的流式感
            report_box.markdown(f"""
            <div class="report-container">
            {displayed_text}
            <span style="color:#FFD700;">▍</span> 
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.01)

