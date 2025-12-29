import streamlit as st
import os

# --- APP VERSION ---
VERSION = "2.0.1 (Premium - Full Features)"

# 1. Page Config
st.set_page_config(
    page_title=f"الماسة كونسلت GIS - {VERSION}",
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
        padding: 15px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .legend-item { display: flex; align-items: center; margin-bottom: 8px; gap: 12px; font-size: 0.9em; }
    .dot { height: 14px; width: 14px; border-radius: 3px; display: inline-block; border: 1px solid white; }
    .version-tag { font-size: 0.8em; color: gray; text-align: left; }
</style>
""", unsafe_allow_html=True)

# 4. Helpers
def get_color(status):
    status = str(status)
    if 'مقبول' in status: return '#00E676'  # Green
    if 'مرفوض' in status or 'ملغى' in status: return '#FF1744'  # Red
    return '#FFEA00'  # Yellow (Neutral/Review)

def get_assets_path():
    possible = ["assets/gis", ".", "gis_service/assets/gis"]
    for p in possible:
        if os.path.exists(p) and any(f.endswith('.gpkg') for f in os.listdir(p)):
            return p
    return "."

ASSETS_PATH = get_assets_path()

# 5. Data Loading (Targeted & Efficient)
@st.cache_data(ttl=3600)
def load_meta(file_name, base_path):
    path = os.path.join(base_path, file_name)
    df = gpd.read_file(path, engine='pyogrio', columns=['gov', 'sec'], use_arrow=True)
    return df

@st.cache_data(ttl=3600)
def load_map_data(file_name, base_path, gov, sec):
    path = os.path.join(base_path, file_name)
    where = f"gov = '{gov}' AND sec = '{sec}'"
    cols = ['geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status']
    gdf = gpd.read_file(path, engine='pyogrio', columns=cols, where=where, use_arrow=True)
    
    # Aggressive simplification for rendering performance
    gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)
    
    if gdf.crs is None: gdf.set_crs(epsg=4326, inplace=True)
    else: gdf = gdf.to_crs(epsg=4326)
    
    # Add status_color for easy access
    gdf['status_color'] = gdf['survey_review_status'].apply(get_color)
    return gdf

# 6. Main App
def main():
    # Sidebar Header
    st.sidebar.markdown(f"### 🌍 El Massa GIS")
    st.sidebar.markdown(f'<p class="version-tag">Version: {VERSION}</p>', unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 تحديث إجباري للبيانات"):
        st.cache_data.clear()
        st.rerun()

    st.title("🌐 نظام المعلومات الجغرافية - الماسة كونسلت")

    files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
    if not files:
        st.error("⚠️ لم يتم العثور على ملفات الخرائط في المسار المحدد.")
        st.info(f"المسار الحالي: {os.path.abspath(ASSETS_PATH)}")
        return
    
    target_file = files[0]

    # Legend
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🎨 مفتاح الحالات")
    st.sidebar.markdown(f"""
    <div class="legend-box">
        <div class="legend-item"><span class="dot" style="background:#00E676"></span> تم القبول (Accepted)</div>
        <div class="legend-item"><span class="dot" style="background:#FFEA00"></span> قيد المراجعة (Review)</div>
        <div class="legend-item"><span class="dot" style="background:#FF1744"></span> مرفوض / ملغى (Rejected)</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        # Step 1: Meta selection
        meta_df = load_meta(target_file, ASSETS_PATH)
        govs = sorted(meta_df['gov'].unique())
        sel_gov = st.sidebar.selectbox("اختر المحافظة", ["-- اختر --"] + govs)
        
        if sel_gov != "-- اختر --":
            secs = sorted(meta_df[meta_df['gov'] == sel_gov]['sec'].unique())
            sel_sec = st.sidebar.selectbox(f"اختر القسم في {sel_gov}", ["-- اختر --"] + secs)
            
            if sel_sec != "-- اختر --":
                # Step 2: Load targeted data
                with st.spinner(f"⏳ جاري تحميل خرائط {sel_sec}..."):
                    gdf = load_map_data(target_file, ASSETS_PATH, sel_gov, sel_sec)
                
                if not gdf.empty:
                    # Map Setup
                    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
                    m = folium.Map(location=center, zoom_start=14, control_scale=True)
                    
                    # 1. My Location Feature
                    LocateControl(
                        auto_start=False,
                        strings={"title": "موقعي الحالي", "popup": "أنت هنا"},
                        keepCurrentZoomLevel=True
                    ).add_to(m)
                    
                    # 2. Base Layer (Satellite)
                    folium.TileLayer(
                        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                        attr="Google Satellite",
                        name="الأقمار الصناعية",
                        overlay=False,
                        control=True
                    ).add_to(m)

                    # 3. GeoJson shapes
                    geo_json_layer = folium.GeoJson(
                        gdf,
                        name="القطع المساحية",
                        style_function=lambda f: {
                            'fillColor': f['properties'].get('status_color', '#FFEA00'),
                            'color': 'white',
                            'weight': 1,
                            'fillOpacity': 0.6
                        },
                        highlight_function=lambda f: {'weight': 3, 'fillOpacity': 0.9, 'color': '#00E676'},
                        tooltip=folium.GeoJsonTooltip(
                            fields=['requestnumber', 'survey_review_status'],
                            aliases=['رقم الطلب:', 'الحالة:'],
                            localize=True
                        )
                    ).add_to(m)

                    # --- INTERACTIVITY ---
                    st.info("💡 اضغط على القطعة في الخريطة لإظهار بياناتها فقط في الجدول بالأسفل.")
                    
                    map_data = st_folium(
                        m, 
                        height=550, 
                        width='100%', 
                        key="main_gis_map",
                        returned_objects=["last_active_drawing", "last_object_clicked"]
                    )

                    # Selection Logic
                    # We check last_object_clicked which contains properties
                    clicked_object = map_data.get("last_object_clicked")
                    
                    st.divider()
                    
                    if clicked_object and 'properties' in clicked_object:
                        req_num = clicked_object['properties'].get('requestnumber')
                        display_df = gdf[gdf['requestnumber'] == req_num]
                        st.success(f"📌 البيانات التفصيلية للطلب: {req_num}")
                    else:
                        display_df = gdf
                        st.subheader(f"📊 قائمة الطلبات في {sel_sec}")

                    st.dataframe(
                        display_df.drop(columns=['geometry', 'status_color']),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("⚠️ لا توجد بيانات مسجلة لهذا القسم.")
            else:
                st.info("👈 يرجى تحديد القسم من القائمة الجانبية.")
        else:
            st.info("👈 يرجى اختيار المحافظة للبدء.")

    except Exception as e:
        st.error("🚨 حدث خطأ فني أثناء معالجة البيانات")
        with st.expander("تفاصيل الخطأ التقني"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
