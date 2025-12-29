import streamlit as st
import os

# --- APP VERSION ---
VERSION = "2.4.0 (Premium Redesign)"

# 1. Page Config
st.set_page_config(
    page_title="El Massa Consult - Shapefile View",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if 'selected_requests' not in st.session_state:
    st.session_state.selected_requests = []
if 'last_click' not in st.session_state:
    st.session_state.last_click = None
if 'last_draw' not in st.session_state:
    st.session_state.last_draw = None

# 2. Lazy Imports
try:
    import geopandas as gpd
    import pandas as pd
    import folium
    from folium.plugins import LocateControl, Draw, Fullscreen
    from streamlit_folium import st_folium
    import traceback
    from shapely.geometry import shape
except Exception as e:
    st.error(f"❌ خطأ في تحميل المكتبات: {e}")
    st.stop()

# 3. Custom Premium CSS (Matching Mockup)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] { 
        font-family: 'Cairo', sans-serif; 
        direction: rtl; 
        text-align: right; 
    }
    .stApp { 
        background-color: #0A1128; 
        color: white; 
    }
    
    /* Top Green Header Bar */
    .top-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 50px;
        background-color: #00BFA5;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        z-index: 1000;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .main .block-container { padding-top: 70px; }

    /* Main Title Styling */
    .main-title {
        color: #C6FF00;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .status-dot {
        height: 35px;
        width: 35px;
        background-color: #C6FF00;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 15px #C6FF00;
    }

    /* Control Elements Container */
    .controls-header {
        background-color: white;
        color: #333;
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 0;
    }
    .controls-body {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px;
        border-radius: 0 0 8px 8px;
        margin-bottom: 30px;
    }

    /* Input Styling */
    .stSelectbox label, .stMultiSelect label { color: white !important; font-size: 0.9rem !important; }
    div[data-baseweb="select"] { background-color: white !important; border-radius: 8px !important; }
    div[data-baseweb="select"] * { color: #333 !important; }
    
    /* Horizontal Legend */
    .legend-container {
        display: flex;
        justify-content: center;
        gap: 40px;
        margin: 20px 0;
        padding: 15px;
        flex-wrap: wrap;
    }
    .legend-item { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 0.95rem; }
    .dot { height: 15px; width: 15px; border-radius: 50%; display: inline-block; }
    
    /* CSV Button Styling */
    .stButton button {
        background-color: #00E676 !important;
        color: #0A1128 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 2rem !important;
    }

    /* Hide Sidebar elements if any */
    [data-testid="stSidebar"] { background-color: #050A18 !important; }
</style>
""", unsafe_allow_html=True)

# 4. Helpers
def get_color(status):
    status = str(status)
    if 'مقبول' in status: return '#4CAF50'  # Bright Green
    if 'مرفوض' in status or 'ملغى' in status: return '#FF5252'  # Soft Red
    if 'مراجعة' in status: return '#FFD600'  # Yellow
    return '#2196F3'  # Blue for others

def get_assets_path():
    possible = ["assets/gis", ".", "gis_service/assets/gis"]
    for p in possible:
        if os.path.exists(p) and any(f.endswith('.gpkg') for f in os.listdir(p)):
            return p
    return "."

ASSETS_PATH = get_assets_path()

# 5. Data Loading
@st.cache_data(ttl=3600)
def load_meta(file_name, base_path):
    path = os.path.join(base_path, file_name)
    return gpd.read_file(path, engine='pyogrio', columns=['gov', 'sec'], use_arrow=True)

@st.cache_data(ttl=3600)
def load_map_data(file_name, base_path, gov, sec):
    path = os.path.join(base_path, file_name)
    where = f"gov = '{gov}' AND sec = '{sec}'"
    gdf = gpd.read_file(path, engine='pyogrio', where=where, use_arrow=True)
    if gdf.crs is None: gdf.set_crs(epsg=4326, inplace=True)
    else: gdf = gdf.to_crs(epsg=4326)
    gdf['status_color'] = gdf['survey_review_status'].apply(get_color)

    # JSON Cleanup for Dates
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]) or gdf[col].dtype == object:
            try:
                gdf[col] = gdf[col].apply(lambda x: x.isoformat() if hasattr(x, 'isoformat') else x)
            except: pass
    return gdf

# 6. Main App
def main():
    # Top Bar
    st.markdown('<div class="top-header">مستعرض الخرائط (الماسة كونسلت)</div>', unsafe_allow_html=True)

    # Title
    st.markdown('<div class="main-title">El Massa Consult - Shapefile View <span class="status-dot"></span></div>', unsafe_allow_html=True)

    files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
    if not files:
        st.error("⚠️ ملفات البيانات غير موجودة.")
        return
    
    target_file = files[0]

    # Control Section (عناصر التحكم والتصفية)
    st.markdown('<div class="controls-header">⚙️ عناصر التحكم والتصفية</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="controls-body">', unsafe_allow_html=True)
        
        # Grid for dropdowns
        col1, col2, col3 = st.columns([1, 1, 2])
        
        try:
            meta_df = load_meta(target_file, ASSETS_PATH)
            govs = sorted(meta_df['gov'].unique())
            
            with col1:
                sel_gov = st.selectbox("🏛️ المحافظة", ["عرض الكل"] + govs)
            
            with col2:
                if sel_gov != "عرض الكل":
                    secs = sorted(meta_df[meta_df['gov'] == sel_gov]['sec'].unique())
                    sel_sec = st.selectbox("📍 القسم", ["عرض الكل"] + secs)
                else:
                    sel_sec = st.selectbox("📍 القسم", ["عرض الكل"], disabled=True)
            
            with col3:
                # Search / Multi-select
                # Check for updates and sync Sidebar selections
                if sel_gov != "عرض الكل" and sel_sec != "عرض الكل":
                    # Lazy loading for large dropdown
                    pass
                
                selected_ids = st.multiselect("🔍 بحث (رقم الطلب...)", options=st.session_state.selected_requests + ["..."])

            # CSV Export Button
            st.markdown('<div style="text-align: left;">', unsafe_allow_html=True)
            if st.button("📥 تصدير CSV"):
                st.toast("جاري تحضير ملف البيانات...")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True) # End controls-body

            # Horizontal Legend
            st.markdown(f"""
            <div class="legend-container">
                <div class="legend-item"><span class="dot" style="background:#4CAF50"></span> مقبول</div>
                <div class="legend-item"><span class="dot" style="background:#FF5252"></span> مرفوض للشركة</div>
                <div class="legend-item"><span class="dot" style="background:#FFD600"></span> بانتظار المراجعة</div>
                <div class="legend-item"><span class="dot" style="background:#2196F3"></span> حالات أخرى</div>
            </div>
            """, unsafe_allow_html=True)

            # --- Map Processing ---
            if sel_gov != "عرض الكل" and sel_sec != "عرض الكل":
                with st.spinner("⏳ جاري تحليل خرائط القسم..."):
                    gdf_full = load_map_data(target_file, ASSETS_PATH, sel_gov, sel_sec)
                
                if not gdf_full.empty:
                    # 1. Memory Optimization for Folium
                    # We create a lightweight copy ONLY for the map to prevent ArrayMemoryError
                    keep_map_cols = ['requestnumber', 'survey_review_status', 'accepted_date', 'status_color', 'geometry']
                    gdf_map = gdf_full[[c for c in keep_map_cols if c in gdf_full.columns]].copy()
                    # Micro-simplification (0.00001 is ~1m). Preserves look, saves RAM.
                    gdf_map['geometry'] = gdf_map['geometry'].simplify(0.00001, preserve_topology=True)

                    # 2. Sidebar Search Sync
                    all_ids = sorted(gdf_full['requestnumber'].unique().tolist())
                    with col3:
                        current_sel = [x for x in st.session_state.selected_requests if x in all_ids]
                        sidebar_sel = st.multiselect("🔍 بحث بالرقم", options=all_ids, default=current_sel)
                        if set(sidebar_sel) != set(current_sel):
                            st.session_state.selected_requests = sidebar_sel
                            st.rerun()

                    center = [gdf_map.geometry.centroid.y.mean(), gdf_map.geometry.centroid.x.mean()]
                    m = folium.Map(location=center, zoom_start=14)
                    LocateControl(auto_start=False).add_to(m)
                    Fullscreen(position='topright', title='ملء الشاشة', title_cancel='إغلاق', force_separate_button=True).add_to(m)
                    
                    folium.TileLayer(
                        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                        attr="Google Satellite",
                        name="Satellite View",
                        overlay=False, control=True
                    ).add_to(m)

                    Draw(
                        draw_options={
                            'polyline': False, 'circle': False, 'marker': False, 
                            'circlemarker': False, 'rectangle': True, 'polygon': True
                        },
                        edit_options={'edit': False, 'remove': False}
                    ).add_to(m)

                    folium.GeoJson(
                        gdf_map,
                        style_function=lambda f: {
                            'fillColor': f['properties'].get('status_color'),
                            'color': '#00B0FF' if f['properties'].get('requestnumber') in st.session_state.selected_requests else 'white',
                            'weight': 3 if f['properties'].get('requestnumber') in st.session_state.selected_requests else 1,
                            'fillOpacity': 0.7
                        },
                        tooltip=folium.GeoJsonTooltip(
                            fields=['requestnumber', 'survey_review_status', 'accepted_date'],
                            aliases=['الطلب:', 'الحالة:', 'التاريخ:'], localize=True
                        )
                    ).add_to(m)

                    map_out = st_folium(m, height=520, width='100%', key="main_map")

                    # 3. Handle Map Interaction
                    
                    # A. Spatial Selection (Drawing) - Every new drawing REPLACES the current selection
                    new_drawings = map_out.get("all_drawings")
                    if new_drawings and str(new_drawings) != st.session_state.last_draw:
                        st.session_state.last_draw = str(new_drawings)
                        # Process the latest drawing
                        last_draw = new_drawings[-1] # Get most recent
                        if "geometry" in last_draw:
                            draw_geom = shape(last_draw["geometry"])
                            # Find all request numbers within the drawing
                            # Intersection check
                            mask = gdf_full.geometry.apply(lambda x: draw_geom.contains(x) or x.intersects(draw_geom))
                            found_ids = gdf_full[mask]['requestnumber'].tolist()
                            if found_ids:
                                st.session_state.selected_requests = found_ids
                                st.rerun()

                    # B. Click Selection - Every new click REPLACES the current selection
                    new_click = map_out.get("last_object_clicked")
                    if new_click and new_click != st.session_state.last_click:
                        st.session_state.last_click = new_click
                        if "properties" in new_click and "requestnumber" in new_click["properties"]:
                            req = new_click["properties"]["requestnumber"]
                            # REPLACEMENT logic: Selection becomes only this request
                            st.session_state.selected_requests = [req]
                            st.rerun()

                    # Table
                    if st.session_state.selected_requests:
                        st.subheader("📋 بيانات الطلبات المختارة")
                        display_df = gdf_full[gdf_full['requestnumber'].isin(st.session_state.selected_requests)]
                        
                        # Apply Arabic Names Mapping
                        field_names = {
                            'fid': 'المعرف الفريد', 'id': 'الرقم', 'requestnumber': 'رقم الطلب',
                            'gov': 'المحافظة', 'sec': 'القسم', 'ssec': 'الشياخة',
                            'streetname': 'اسم الشارع', 'property_n': 'رقم العقار',
                            'addeddate': 'تاريخ الإضافة', 'due_date': 'تاريخ الاستحقاق',
                            'unittype': 'نوع الوحدة', 'floor_numb': 'رقم الدور',
                            'floor_n_t': 'اسم الدور', 'apart_num': 'رقم الشقة',
                            'surveynum': 'رقم المسح', 'name': 'الاسم', 'phone': 'الهاتف',
                            'north_b': 'الحد الشمالي', 'south_b': 'الحد الجنوبي',
                            'east_b': 'الحد الشرقي', 'west_b': 'الحد الغربي',
                            'north_l': 'الطول الشمالي', 'south_l': 'الطول الجنوبي',
                            'east_l': 'الطول الشرقي', 'west_l': 'الطول الغربي',
                            'area_land': 'مساحة الأرض', 'area_build': 'مساحة المبنى',
                            'manwr': 'المنور', 'sealm': 'السلم', 'corridor': 'الطرقة',
                            'elevator': 'المصعد', 'ket3a': 'قطعة', 'hod': 'حوض',
                            'usage': 'الاستخدام', 'descrip': 'الوصف',
                            'north_l1': 'الطول الشمالي 1', 'south_l1': 'الطول الجنوبي 1',
                            'east_l1': 'الطول الشرقي 1', 'west_l1': 'الطول الغربي 1',
                            'area_ap1': 'مساحة الشقة 1', 'north_l2': 'الطول الشمالي 2',
                            'south_l2': 'الطول الجنوبي 2', 'east_l2': 'الطول الشرقي 2',
                            'west_l2': 'الطول الغربي 2', 'area_ap2': 'مساحة الشقة 2',
                            'north_l3': 'الطول الشمالي 3', 'south_l3': 'الطول الجنوبي 3',
                            'east_l3': 'الطول الشرقي 3', 'west_l3': 'الطول الغربي 3',
                            'area_ap3': 'مساحة الشقة 3', 'north_l4': 'الطول الشمالي 4',
                            'south_l4': 'الطول الجنوبي 4', 'east_l4': 'الطول الشرقي 4',
                            'west_l4': 'الطول الغربي 4', 'area_ap4': 'مساحة الشقة 4',
                            'north_l5': 'الطول الشمالي 5', 'south_l5': 'الطول الجنوبي 5',
                            'east_l5': 'الطول الشرقي 5', 'west_l5': 'الطول الغربي 5',
                            'area_ap5': 'مساحة الشقة 5', 'north_l6': 'الطول الشمالي 6',
                            'south_l6': 'الطول الجنوبي 6', 'east_l6': 'الطول الشرقي 6',
                            'west_l6': 'الطول الغربي 6', 'area_ap6': 'مساحة الشقة 6',
                            'x': 'الإحداثي X', 'y': 'الإحداثي Y', 'totalarea': 'المساحة الإجمالية',
                            'totalaparts': 'إجمالي الشقق', 'overlap': 'تداخل',
                            'ncpslu_overlap': 'تداخل NCPSLU', 'north_lg': 'الطول الشمالي G',
                            'south_lg': 'الطول الجنوبي G', 'east_lg': 'الطول الشرقي G',
                            'west_lg': 'الطول الغربي G', 'area_g': 'المساحة G',
                            'comcode': 'كود الشركة', 'accepted_date': 'تاريخ القبول',
                            'compy_old': 'الشركة القديمة', 'survey_review_status': 'حالة مراجعة المسح'
                        }
                        
                        # Filter only existing columns
                        final_df = display_df.drop(columns=['geometry', 'status_color'], errors='ignore')
                        final_df = final_df.rename(columns=field_names)
                        
                        st.dataframe(final_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("لا توجد بيانات لهذا القسم.")
            else:
                st.info("💡 يرجى اختيار قسم محدد من القائمة الجانبية لعرض الخريطة.")

        except Exception as e:
            st.error("🚨 خطأ تقني")
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
