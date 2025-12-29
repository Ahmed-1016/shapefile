import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap
import os
import json
import pandas as pd

# ضبط إعدادات الصفحة
st.set_page_config(
    page_title="El Massa Consult - GIS Premium",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="auto"  # لا يوجد sidebar
)

# حقن CSS مخصص لتطوير الواجهة (Premium Professional Design)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --primary-gradient: linear-gradient(135deg, #00C853 0%, #00E676 100%);
        --secondary-gradient: linear-gradient(135deg, #00B0FF 0%, #2979FF 100%);
        --accent-gradient: linear-gradient(135deg, #FFD600 0%, #FFEA00 100%);
        --danger-gradient: linear-gradient(135deg, #FF1744 0%, #F50057 100%);
        --bg-primary: #0A0E27;
        --bg-secondary: #0E1538;
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.12);
        --text-primary: #FFFFFF;
        --text-secondary: rgba(255, 255, 255, 0.9);
        --text-tertiary: rgba(255, 255, 255, 0.7);
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.15);
        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.2);
        --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.3);
        --shadow-glow: 0 0 20px rgba(0, 200, 83, 0.3);
    }

    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Cairo', 'Inter', sans-serif;
        direction: rtl;
        text-align: right;
        background: var(--bg-primary);
        color: var(--text-primary);
    }

    /* تقليل المسافة العلوية */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* تقليل المسافة فوق العنوان */
    .main-title {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Animated Title */
    .main-title {
        background: linear-gradient(135deg, #0A0E27 0%, #0E1538 50%, #0A0E27 100%);
        background-size: 200% 200%;
        animation: gradientShift 15s ease infinite;
    }

    /* Animated Background */
    .stApp {
        background: linear-gradient(135deg, #0A0E27 0%, #0E1538 50%, #0A0E27 100%);
        background-size: 200% 200%;
        animation: gradientShift 15s ease infinite;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* إخفاء جميع عناصر Streamlit غير المرغوبة */
    header[data-testid="stHeader"],
    #MainMenu,
    footer,
    section[data-testid="stSidebar"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Premium Glassmorphism Control Panel (Expander) */
    .streamlit-expanderHeader {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        padding: 16px 20px;
        font-size: 1.1rem;
        font-weight: 700;
    }

    .streamlit-expanderHeader:hover {
        border-color: rgba(0, 200, 83, 0.3);
        box-shadow: var(--shadow-glow);
        background: linear-gradient(135deg, 
            rgba(0, 200, 83, 0.05) 0%, 
            rgba(0, 176, 255, 0.05) 100%);
    }

    .streamlit-expanderContent {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-top: none;
        border-radius: 0 0 12px 12px;
        backdrop-filter: blur(10px);
        padding: 20px;
        margin-top: -1px;
    }

    /* Premium Metric Cards */
    [data-testid="stMetric"] {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 16px;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        box-shadow: var(--shadow-sm);
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-md), var(--shadow-glow);
        border-color: rgba(0, 200, 83, 0.3);
    }

    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(0, 200, 83, 0.5));
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: var(--text-secondary);
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* Main Title with Animation */
    .main-title {
        background: linear-gradient(90deg, #00C853, #00B0FF, #FFD600, #00C853);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        animation: gradientFlow 8s ease infinite;
        filter: drop-shadow(0 0 20px rgba(0, 200, 83, 0.4));
        letter-spacing: -0.5px;
    }

    @keyframes gradientFlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .sub-header {
        color: var(--text-secondary);
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 400;
        opacity: 0.9;
    }

    /* Enhanced Buttons */
    .stButton > button {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        color: var(--text-primary);
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        backdrop-filter: blur(10px);
        box-shadow: var(--shadow-sm);
    }

    .stButton > button:hover {
        background: var(--primary-gradient);
        border-color: transparent;
        transform: translateY(-2px);
        box-shadow: var(--shadow-md), var(--shadow-glow);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Download Button Special Styling */
    .stDownloadButton > button {
        background: var(--primary-gradient);
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 700;
        color: white;
        box-shadow: var(--shadow-md), var(--shadow-glow);
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    }

    .stDownloadButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: var(--shadow-lg), 0 0 30px rgba(0, 200, 83, 0.5);
    }

    /* Input Fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        color: #000000;
        padding: 12px 16px;
        font-weight: 500;
        transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
        backdrop-filter: blur(10px);
    }

    .stTextInput > div > div > input::placeholder {
        color: rgba(0, 0, 0, 0.5);
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #00C853;
        box-shadow: 0 0 0 3px rgba(0, 200, 83, 0.2), var(--shadow-glow);
        outline: none;
        background: rgba(255, 255, 255, 0.15);
    }

    /* Labels */
    label {
        color: rgba(255, 255, 255, 0.95) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            var(--glass-border) 50%, 
            transparent 100%);
        margin: 24px 0;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00C853, #00B0FF);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #00E676, #2979FF);
        box-shadow: 0 0 10px rgba(0, 200, 83, 0.5);
    }

    /* Force scrollbar to always show */
    html, body, .main, [data-testid="stAppViewContainer"] {
        overflow-y: scroll !important;
    }

    /* Ensure scrollbar is visible in iframe */
    .stApp {
        overflow-y: scroll !important;
    }

    /* Data Tables */
    .stDataFrame {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        overflow: hidden;
        backdrop-filter: blur(10px);
        box-shadow: var(--shadow-md);
    }

    /* Info/Warning/Error Boxes */
    .stAlert {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        padding: 16px;
        box-shadow: var(--shadow-sm);
    }

    /* Spinner Animation */
    .stSpinner > div {
        border-color: #00C853 transparent transparent transparent;
    }

    /* Container Cards */
    .element-container {
        animation: fadeIn 0.5s ease-in;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Legend Styling */
    section[data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.8;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        border-color: rgba(0, 200, 83, 0.3);
        box-shadow: var(--shadow-glow);
    }

    /* Loading State */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0.0, 0.6, 1) infinite;
    }

    /* Tooltip Enhancement */
    [data-testid="stTooltipIcon"] {
        color: var(--text-tertiary);
        transition: color 0.3s ease;
    }

    [data-testid="stTooltipIcon"]:hover {
        color: #00C853;
    }

    /* Caption Text */
    .stCaption {
        color: var(--text-tertiary);
        font-size: 0.85rem;
        font-weight: 400;
    }

    /* Success Message */
    .stSuccess {
        background: linear-gradient(135deg, rgba(0, 200, 83, 0.1), rgba(0, 230, 118, 0.1));
        border-left: 4px solid #00C853;
    }

    /* Warning Message */
    .stWarning {
        background: linear-gradient(135deg, rgba(255, 214, 0, 0.1), rgba(255, 234, 0, 0.1));
        border-left: 4px solid #FFD600;
    }

    /* Error Message */
    .stError {
        background: linear-gradient(135deg, rgba(255, 23, 68, 0.1), rgba(245, 0, 87, 0.1));
        border-left: 4px solid #FF1744;
    }

    /* Info Message */
    .stInfo {
        background: linear-gradient(135deg, rgba(0, 176, 255, 0.1), rgba(41, 121, 255, 0.1));
        border-left: 4px solid #00B0FF;
    }

    /* Responsive Design - Mobile First */
    
    /* Mobile Phones (< 768px) */
    @media (max-width: 767px) {
        .main-title {
            font-size: 1.8rem;
            letter-spacing: -0.3px;
        }
        
        .sub-header {
            font-size: 0.95rem;
        }
        
        /* Stack columns vertically on mobile */
        .stColumn {
            width: 100% !important;
            min-width: 100% !important;
        }
        
        /* Adjust expander padding */
        .streamlit-expanderHeader {
            padding: 12px 16px;
            font-size: 1rem;
        }
        
        .streamlit-expanderContent {
            padding: 16px;
        }
        
        /* Smaller buttons and inputs */
        .stButton > button,
        .stDownloadButton > button {
            padding: 10px 16px;
            font-size: 0.9rem;
        }
        
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            padding: 10px 12px;
            font-size: 0.9rem;
        }
        
        /* Adjust metric cards */
        [data-testid="stMetric"] {
            padding: 12px;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
    }
    
    /* Tablets (768px - 1024px) */
    @media (min-width: 768px) and (max-width: 1024px) {
        .main-title {
            font-size: 2.2rem;
        }
        
        .sub-header {
            font-size: 1.05rem;
        }
        
        .streamlit-expanderHeader {
            padding: 14px 18px;
            font-size: 1.05rem;
        }
    }
    
    /* Desktop (> 1024px) */
    @media (min-width: 1025px) {
        /* Default styles already optimized for desktop */
    }
    
    /* Landscape orientation adjustments */
    @media (orientation: landscape) and (max-height: 600px) {
        .main-title {
            font-size: 1.5rem;
            margin-bottom: 0.3rem;
        }
        
        .sub-header {
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
    }

</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🌍 El Massa Consult - Shapfile View</h1>', unsafe_allow_html=True)
# st.markdown('<p class="sub-header">نظام متطور لاستعراض وتحليل البيانات الجغرافية</p>', unsafe_allow_html=True)

# مسارات البحث عن الملفات (المحلي وفي السيرفر)
POSSIBLE_PATHS = [
    os.path.join("..", "assets", "gis"),     # التشغيل المحلي من داخل مجلد gis_service
    os.path.join("assets", "gis"),          # التشغيل من المجلد الرئيسي
    os.path.join(".", "gis_assets"),        # التشغيل داخل الحاوية (Docker)
]

ASSETS_PATH = next((p for p in POSSIBLE_PATHS if os.path.exists(p)), POSSIBLE_PATHS[0])

# قاموس ترجمة أسماء الحقول للعربية (نفس المستخدم في فلاتر)
FIELD_NAMES_AR = {
    'fid': 'المعرف الفريد',
    'id': 'الرقم',
    'requestnumber': 'رقم الطلب',
    'gov': 'المحافظة',
    'sec': 'القسم',
    'ssec': 'الشياخة',
    'streetname': 'اسم الشارع',
    'property_n': 'رقم العقار',
    'addeddate': 'تاريخ الإضافة',
    'due_date': 'تاريخ الاستحقاق',
    'unittype': 'نوع الوحدة',
    'floor_numb': 'رقم الدور',
    'floor_n_t': 'اسم الدور',
    'apart_num': 'رقم الشقة',
    'surveynum': 'رقم المسح',
    'name': 'الاسم',
    'phone': 'الهاتف',
    'north_b': 'الحد الشمالي',
    'south_b': 'الحد الجنوبي',
    'east_b': 'الحد الشرقي',
    'west_b': 'الحد الغربي',
    'north_l': 'الطول الشمالي',
    'south_l': 'الطول الجنوبي',
    'east_l': 'الطول الشرقي',
    'west_l': 'الطول الغربي',
    'area_land': 'مساحة الأرض',
    'area_build': 'مساحة المبنى',
    'manwr': 'المنور',
    'sealm': 'السلم',
    'corridor': 'الطرقة',
    'elevator': 'المصعد',
    'ket3a': 'قطعة',
    'hod': 'حوض',
    'usage': 'الاستخدام',
    'descrip': 'الوصف',
    'totalarea': 'المساحة الإجمالية',
    'survey_review_status': 'حالة مراجعة المسح',
}

@st.cache_data
def load_data(file_name):
    path = os.path.join(ASSETS_PATH, file_name)
    # معلومات تصحيح المسارات
    st.sidebar.info(f"📁 Current DIR: {os.getcwd()}")
    st.sidebar.info(f"📍 Assets Path: {path}")

    # التحقق من وجود الملف وحجمه قبل القراءة
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        st.write(f"📁 تحميل الملف: {file_name} ({size_mb:.1f} MB)")
    else:
        st.error(f"❌ الملف غير موجود في المسار: {path}")
        # عرض محتويات المجلد للمساعدة في التصحيح
        if os.path.exists(ASSETS_PATH):
            st.write(f"📂 محتويات مجلد Assets: {os.listdir(ASSETS_PATH)}")
        else:
            st.write(f"⚠️ مجلد Assets غير موجود أصلاً في: {ASSETS_PATH}")
        return None

    try:
        # التحقق إذا كان الملف مجرد "Pointer" لـ Git LFS (حجمه صغير جداً)
        if os.path.getsize(path) < 1000:
             st.error("⚠️ يبدو أن الملف لم يتم تحميله بالكامل من Git LFS. تأكد من تفعيل LFS في مستودع GitHub.")
             return None

        # تحديد الأعمدة الضرورية فقط لتقليل استهلاك الذاكرة
        essential_columns = [
            'geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status'
        ]
        
        # محاولة القراءة بمحرك pyogrio السريع أولاً
        try:
            gdf = gpd.read_file(path, engine='pyogrio', columns=essential_columns)
        except Exception:
            # Fallback للمحرك العادي إذا فشل pyogrio
            gdf = gpd.read_file(path)
            # اختيار الأعمدة يدوياً في حالة الـ fallback
            existing_cols = [c for c in essential_columns if c in gdf.columns]
            gdf = gdf[existing_cols]
        
        # تبسيط الأشكال الهندسية لتقليل حجم البيانات المرسلة للمتصفح
        # (تقليل الدقة بمقدار 0.0001 درجة - حوالي 10 أمتار)
        gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)

        # التأكد من وجود عمود الحالة
        if 'survey_review_status' not in gdf.columns:
             gdf['survey_review_status'] = ''

        # حل مشكلة الـ Timestamp
        for col in gdf.columns:
            if col == 'geometry': continue
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            elif gdf[col].dtype == 'object':
                gdf[col] = gdf[col].astype(str).replace('nan', '')

        # نظام الإحداثيات
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        else:
            gdf = gdf.to_crs(epsg=4326)
            
        # بناء الفهرس المكاني (Spatial Index) بأمان
        try:
             _ = gdf.sindex 
        except Exception as si_err:
             st.sidebar.warning(f"⚠️ Spatial Index warning: {si_err}")
        
        return gdf
    except Exception as e:
        st.error(f"❌ خطأ تقني في قراءة البيانات: {str(e)}")
        return None

# الحصول على قائمة الملفات المتاحة
if os.path.exists(ASSETS_PATH):
    available_files = [f for f in os.listdir(ASSETS_PATH) if f.endswith(".gpkg")]
else:
    st.warning("لم يتم العثور على مجلد assets/gis")
    available_files = []

# لوحة التحكم العلوية - Top Control Panel
with st.expander("⚙️ عناصر التحكم والتصفية", expanded=True):
    # تحديد الملف تلقائياً (أول ملف متاح)
    if available_files:
        selected_file = available_files[0]  # اختيار أول ملف تلقائياً
    else:
        # Fallback: السماح برفع ملف إذا لم توجد ملفات (مفيد للنشر على Cloud)
        uploaded_file = st.file_uploader("📂 لا توجد ملفات. قم برفع ملف GPKG:", type=['gpkg'])
        if uploaded_file:
            # حفظ الملف المرفوع مؤقتاً
            if not os.path.exists("temp_uploads"):
                os.makedirs("temp_uploads")
            temp_path = os.path.join("temp_uploads", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            selected_file = uploaded_file.name
            ASSETS_PATH = "temp_uploads" # تحديث المسار للملفات المرفوعة
        else:
            selected_file = None
            st.info("💡 يرجى رفع ملف بيانات للبدء.")
    
    if selected_file:
        with st.spinner("⏳ جاري تحميل البيانات..."):
            gdf = load_data(selected_file)
            
        if gdf is not None:
            st.divider()
            
            # صف ثاني: التصفية والبحث
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # تحسين سرعة الفلاتر باستخدام الكاش للقيم الفريدة
                if f"govs_{selected_file}" not in st.session_state:
                    st.session_state[f"govs_{selected_file}"] = sorted(gdf['gov'].dropna().unique().tolist()) if 'gov' in gdf.columns else []
                
                govs = st.session_state[f"govs_{selected_file}"]
                selected_gov = st.selectbox("🏛️ المحافظة", ["عرض الكل"] + govs, key="gov_selector")
            
            with col2:
                filtered_gdf = gdf
                if selected_gov != "عرض الكل":
                    filtered_gdf = gdf[gdf['gov'] == selected_gov]
                
                # تصفية القسم بناءً على المحافظة المختارة
                if selected_gov != "عرض الكل":
                    sec_key = f"secs_{selected_file}_{selected_gov}"
                    if sec_key not in st.session_state:
                        st.session_state[sec_key] = sorted(filtered_gdf['sec'].dropna().unique().tolist()) if 'sec' in filtered_gdf.columns else []
                    secs = st.session_state[sec_key]
                else:
                    if f"secs_all_{selected_file}" not in st.session_state:
                        st.session_state[f"secs_all_{selected_file}"] = sorted(gdf['sec'].dropna().unique().tolist()) if 'sec' in gdf.columns else []
                    secs = st.session_state[f"secs_all_{selected_file}"]
                    
                selected_sec = st.selectbox("📍 القسم", ["عرض الكل"] + secs, key="sec_selector")
            
            with col3:
                if selected_sec != "عرض الكل":
                    filtered_gdf = filtered_gdf[filtered_gdf['sec'] == selected_sec]
                
                search_query = st.text_input("🔍 بحث", placeholder="رقم الطلب...", key="search_input")
            
            with col4:
                st.markdown("###")  # مسافة للمحاذاة
                # زر التصدير
                if 'filtered_gdf' in locals() and filtered_gdf is not None and len(filtered_gdf) > 0:
                    csv = filtered_gdf.drop(columns=['geometry']).to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 تصدير CSV",
                        data=csv,
                        file_name=f"ElMassa_{selected_file}.csv",
                        mime='text/csv',
                    )

            # تطبيق البحث
            if search_query:
                mask = filtered_gdf.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
                search_results = filtered_gdf[mask]
                if not search_results.empty:
                    filtered_gdf = search_results
                else:
                    st.warning("⚠️ لم يتم العثور على نتائج للبحث.")

# دليل الألوان (خارج الـ expander - يظهر فوراً)
st.divider()
col1, col2, col3, col4 = st.columns(4)
col1.markdown('<span style="color: white;">🟢 **مقبول**</span>', unsafe_allow_html=True)
col2.markdown('<span style="color: white;">🔴 **مرفوض للشركة**</span>', unsafe_allow_html=True)
col3.markdown('<span style="color: white;">🟡 **بانتظار المراجعة**</span>', unsafe_allow_html=True)
col4.markdown('<span style="color: white;">🔵 **حالات أخرى**</span>', unsafe_allow_html=True)

# العرض الرئيسي
if 'filtered_gdf' in locals() and filtered_gdf is not None:
    # التحقق من اختيار القسم قبل رسم الخريطة
    if selected_sec == "عرض الكل":
        st.info("💡 يرجى اختيار قسم محدد من القائمة الجانبية لعرض الخريطة.")
    elif len(filtered_gdf) == 0:
        st.warning("⚠️ لا توجد نتائج تطابق اختياراتك.")
    else:
        # تعريف الـ Fragment لجعل التفاعل محلياً دون إعادة تحميل الصفحة كاملة
        @st.fragment
        def render_interactive_map(filtered_gdf):
            # إعدادات مركز الخريطة والزوم من الـ session_state
            if 'map_center' not in st.session_state:
                st.session_state['map_center'] = [filtered_gdf.geometry.centroid.y.mean(), filtered_gdf.geometry.centroid.x.mean()]
            if 'map_zoom' not in st.session_state:
                st.session_state['map_zoom'] = 12

            # إنشاء الخريطة
            m = leafmap.Map(center=st.session_state['map_center'], zoom=st.session_state['map_zoom'])
            m.add_basemap("HYBRID") 
            
            # إضافة زر "موقعي" للخريطة
            from folium.plugins import LocateControl
            LocateControl(
                auto_start=False,
                position='topleft',
                strings={
                    'title': 'موقعي',
                    'popup': 'أنت هنا'
                }
            ).add_to(m)
            
            if 'selected_map_ids' not in st.session_state:
                st.session_state['selected_map_ids'] = set()

            def style_function(feature):
                req_id = str(feature['properties'].get('requestnumber', ''))
                # الحالة الأصلية
                status = feature['properties'].get('survey_review_status', '').strip()
                
                # الستايل الأساسي بناءً على الحالة
                if status == 'مقبول':
                    base_style = {'fillColor': '#4CAF50', 'color': '#2E7D32', 'fillOpacity': 0.4, 'weight': 1.5}
                elif status == 'مرفوض للشركة':
                    base_style = {'fillColor': '#F44336', 'color': '#C62828', 'fillOpacity': 0.4, 'weight': 1.5}
                elif status == '':
                    base_style = {'fillColor': '#F5C973', 'color': '#FFB300', 'fillOpacity': 0.4, 'weight': 1.5}
                else:
                    base_style = {'fillColor': '#2196F3', 'color': '#1565C0', 'fillOpacity': 0.3, 'weight': 1}
                
                # إذا كان المضلع مختاراً، نقوم بتمييزه (Highlight)
                if req_id in st.session_state['selected_map_ids']:
                    base_style['color'] = '#FFFFFF' # إطار أبيض ساطع
                    base_style['weight'] = 4        # خط أسمك
                    base_style['fillOpacity'] = 0.7 # تعبئة أوضح
                
                return base_style

            # رسم جميع الأشكال بدون حد أقصى
            gdf_to_draw = filtered_gdf
            st.info(f"📍 يتم عرض {len(gdf_to_draw):,} طلب على الخريطة")

            # إضافة البيانات باستخدام folium.GeoJson مباشرة لتجنب تضارب الكلمات المفتاحية في leafmap
            import folium
            tooltip = folium.GeoJsonTooltip(
                fields=["requestnumber", "gov", "sec", "survey_review_status"],
                aliases=["رقم الطلب", "المحافظة", "القسم", "الحالة"],
                localize=True
            )
            
            folium.GeoJson(
                gdf_to_draw,
                name="الطلبات",
                style_function=style_function,
                tooltip=tooltip
            ).add_to(m)
            
            from folium.plugins import Draw
            draw = Draw(
                export=False,
                position='topleft',
                draw_options={'polyline': False, 'rectangle': True, 'polygon': True, 'circle': False, 'marker': False, 'circlemarker': False},
                edit_options={'edit': False, 'remove': True}
            )
            m.add_child(draw)

            from streamlit_folium import st_folium
            output = st_folium(
                m,
                height=600,
                width='stretch',
                returned_objects=["last_active_drawing", "all_drawings"],
                key="gis_map"
            )

            if 'selected_map_ids' not in st.session_state:
                st.session_state['selected_map_ids'] = set()

            # 1. التحديد بالضغط (Toggle Selection)
            if output and output.get("last_active_drawing"):
                props = output["last_active_drawing"].get("properties", {})
                req_id = str(props.get("requestnumber", ""))
                if req_id:
                    if req_id in st.session_state['selected_map_ids']:
                        st.session_state['selected_map_ids'].remove(req_id)
                    else:
                        st.session_state['selected_map_ids'].add(req_id)
                    st.rerun()

            # 2. التحديد بالسحب
            if output and output.get("all_drawings"):
                with st.spinner("⏳ جاري تحليل المنطقة..."):
                    import shapely.geometry as sg
                    new_found = False
                    for drawing in output["all_drawings"]:
                        geom_type = drawing['geometry']['type']
                        coords = drawing['geometry']['coordinates']
                        if geom_type in ['Polygon', 'LineString']:
                            draw_geom = sg.Polygon(coords[0]) if geom_type == 'Polygon' else sg.box(*sg.LineString(coords[0]).bounds)
                            spatial_index = gdf_to_draw.sindex
                            matches = gdf_to_draw.iloc[list(spatial_index.intersection(draw_geom.bounds))]
                            precise = matches[matches.intersects(draw_geom)]
                            if not precise.empty:
                                for nid in precise['requestnumber'].astype(str).tolist():
                                    if nid not in st.session_state['selected_map_ids']:
                                        st.session_state['selected_map_ids'].add(nid)
                                        new_found = True
                    if new_found:
                        st.rerun()

            # عرض الجدول والبحث تحت الخريطة داخل الـ Fragment
            st.divider()
            col_t1, col_t2 = st.columns([3, 1])
            col_t1.subheader("📊 الطلبات المحددة")
            if st.session_state['selected_map_ids'] and col_t2.button("🗑️ مسح الكل", key="clear_all"):
                st.session_state['selected_map_ids'] = set()
                st.rerun()

            if st.session_state['selected_map_ids']:
                display_gdf = filtered_gdf[filtered_gdf['requestnumber'].isin(st.session_state['selected_map_ids'])]
                display_df = display_gdf.drop(columns=['geometry']).copy()
                display_df.columns = [FIELD_NAMES_AR.get(col, col) for col in display_df.columns]
                st.dataframe(display_df, width='stretch', hide_index=True)
                
                if st.button("🔍 زوم للمحددين", key="zoom_selected"):
                    st.session_state['map_center'] = [display_gdf.geometry.centroid.y.mean(), display_gdf.geometry.centroid.x.mean()]
                    st.session_state['map_zoom'] = 16
                    st.rerun()
            else:
                st.info("💡 اختر من الخريطة بالضغط أو السحب لعرض البيانات هنا.")

        # تشغيل الـ Fragment
        render_interactive_map(filtered_gdf)
else:
    st.info("💡 يرجى اختيار ملف من القائمة الجانبية للبدء في استعراض الخرائط.")
