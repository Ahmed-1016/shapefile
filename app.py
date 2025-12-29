import streamlit as st
import os

# 1. Page Config
st.set_page_config(
    page_title="الماسة كونسلت - الخرائط التفاعلية",
    page_icon="🌍",
    layout="wide"
)

# 2. Lazy Imports
try:
    import geopandas as gpd
    import pandas as pd
    import folium
    from folium.plugins import LocateControl
    from streamlit_folium import st_folium
    import traceback
except Exception as e:
    st.error(f"❌ خطأ في تحميل المكتبات: {e}")
    st.stop()

# 3. Custom CSS for Right-to-Left and Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0A1128; color: white; }
    .legend-box {
        padding: 10px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .legend-item { display: flex; align-items: center; margin-bottom: 5px; gap: 10px; }
    .dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# 4. Helpers
def get_color(status):
    status = str(status)
    if 'مقبول' in status: return '#00E676'  # Green
    if 'مرفوض' in status or 'ملغى' in status: return '#FF1744'  # Red
    return '#FFEA00'  # Yellow (Neutral/Review)

def get_assets_path():
    possible = ["assets/gis", "."]
    for p in possible:
        if os.path.exists(p) and any(f.endswith('.gpkg') for f in os.listdir(p)):
            return p
    return "."

ASSETS_PATH = get_assets_path()

# 5. Optimized Data Loading
@st.cache_data
def load_meta(file_name, base_path):
    path = os.path.join(base_path, file_name)
    return gpd.read_file(path, engine='pyogrio', columns=['gov', 'sec'], use_arrow=True), None

@st.cache_data
def load_map_data(file_name, base_path, gov, sec):
    path = os.path.join(base_path, file_name)
    where = f"gov = '{gov}' AND sec = '{sec}'"
    cols = ['geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status']
    gdf = gpd.read_file(path, engine='pyogrio', columns=cols, where=where, use_arrow=True)
    gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)
    if gdf.crs is None: gdf.set_crs(epsg=4326, inplace=True)
    else: gdf = gdf.to_crs(epsg=4326)
    return gdf

# 6. Main App logic
def main():
    st.title("🌍 هضبة الماسة - منصة البيانات الجغرافية الذكية")
    
    files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
    if not files:
        st.info("برجاء التأكد من وجود ملفات البيانات.")
        return
    
    target_file = files[0]
    
    # Phase 1: Sidebar & Legend
    st.sidebar.image("https://img.icons8.com/fluency/96/map-marker.png", width=80)
    st.sidebar.markdown("### 🗺️ مفتاح الخريطة")
    st.sidebar.markdown(f"""
    <div class="legend-box">
        <div class="legend-item"><span class="dot" style="background:#00E676"></span> تم القبول</div>
        <div class="legend-item"><span class="dot" style="background:#FFEA00"></span> قيد المراجعة</div>
        <div class="legend-item"><span class="dot" style="background:#FF1744"></span> مرفوض / ملغى</div>
    </div>
    """, unsafe_allow_html=True)

    # Phase 2: Metadata Filtering
    try:
        meta_df, _ = load_meta(target_file, ASSETS_PATH)
        govs = sorted(meta_df['gov'].unique())
        sel_gov = st.sidebar.selectbox("المحافظة", ["إختر المحافظة"] + govs)
        
        if sel_gov != "إختر المحافظة":
            secs = sorted(meta_df[meta_df['gov'] == sel_gov]['sec'].unique())
            sel_sec = st.sidebar.selectbox("القسم / المركز", ["إختر القسم"] + secs)
            
            if sel_sec != "إختر القسم":
                # Phase 3: Targeted Loading
                with st.spinner("⏳ جاري تحليل الخريطة..."):
                    gdf = load_map_data(target_file, ASSETS_PATH, sel_gov, sel_sec)
                
                if not gdf.empty:
                    # Map Rendering
                    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
                    m = folium.Map(location=center, zoom_start=14, control_scale=True)
                    
                    # Plugins
                    LocateControl(auto_start=False).add_to(m)
                    
                    # Google Hybrid Base
                    folium.TileLayer(
                        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                        attr="Google Satellite",
                        name="صور الأقمار الصناعية",
                        overlay=False,
                        control=True
                    ).add_to(m)

                    # Dynamic Layer
                    geojson = folium.GeoJson(
                        gdf,
                        name="الطلبات",
                        style_function=lambda f: {
                            'fillColor': get_color(f['properties'].get('survey_review_status')),
                            'color': 'white', 'weight': 1, 'fillOpacity': 0.6
                        },
                        highlight_function=lambda f: {'weight': 3, 'fillOpacity': 0.8, 'color': '#00E676'},
                        tooltip=folium.GeoJsonTooltip(fields=['requestnumber', 'survey_review_status'], aliases=['رقم الطلب:', 'الحالة:'])
                    ).add_to(m)

                    # Selection Capture
                    out = st_folium(m, height=600, width='100%', key="gis_map")
                    
                    # Table Logic: Show selected or all if nothing selected
                    selected_request = out.get("last_object_clicked_tooltip")
                    
                    st.divider()
                    
                    if selected_request:
                        # Extract request number from tooltip "رقم الطلب: x..."
                        req_num = selected_request.split('\n')[0].replace('رقم الطلب: ', '').strip()
                        display_df = gdf[gdf['requestnumber'] == req_num]
                        st.success(f"📌 عرض بيانات الطلب المختار: {req_num}")
                    else:
                        display_df = gdf
                        st.info("💡 اضغط على مكان في الخريطة لعرض بياناته التفصيلية في الجدول")

                    st.dataframe(
                        display_df.drop(columns='geometry'),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("⚠️ لا توجد بيانات لهذا التقسيم.")
            else:
                st.info("👈 يرجى اختيار القسم لعرض الخريطة")
        else:
            st.info("👈 ابدأ باختيار المحافظة من القائمة الجانبية")
            
    except Exception as e:
        st.error("🚨 حدث خطأ غير متوقع")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
