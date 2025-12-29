import streamlit as st
import os

# 1. Page Config
st.set_page_config(
    page_title="El Massa Consult - Smart GIS",
    page_icon="🌍",
    layout="wide"
)

# 2. Lazy Imports
try:
    import geopandas as gpd
    import pandas as pd
    import folium
    from streamlit_folium import st_folium
    import traceback
except Exception as e:
    st.error(f"❌ Error during library import: {e}")
    st.stop()

# 3. Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0A1128; color: white; }
    [data-testid="stMetricValue"] { color: #00E676; }
</style>
""", unsafe_allow_html=True)

# 4. Path Detection
def get_assets_path():
    possible = ["assets/gis", "."]
    for p in possible:
        if os.path.exists(p) and any(f.endswith('.gpkg') for f in os.listdir(p)):
            return p
    return "."

ASSETS_PATH = get_assets_path()

# 5. Targeted Loading Logic
@st.cache_data
def load_metadata(file_name, base_path):
    path = os.path.join(base_path, file_name)
    try:
        # Load ONLY necessary text columns (No Geometry!) - Extremely fast and light
        df = gpd.read_file(path, engine='pyogrio', columns=['gov', 'sec'], use_arrow=True)
        return df, None
    except Exception as e:
        return None, str(e)

@st.cache_data
def load_section_data(file_name, base_path, gov, sec):
    path = os.path.join(base_path, file_name)
    try:
        # Load only target data using a SQL-like filter via pyogrio (High Performance)
        where_clause = f"gov = '{gov}' AND sec = '{sec}'"
        cols = ['geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status']
        
        gdf = gpd.read_file(path, engine='pyogrio', columns=cols, where=where_clause, use_arrow=True)
        
        # Aggressive geometry simplification for the browser
        gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)
        
        if gdf.crs is None: gdf.set_crs(epsg=4326, inplace=True)
        else: gdf = gdf.to_crs(epsg=4326)
        
        return gdf, None
    except Exception as e:
        return None, str(e)

# 6. Main App
def main():
    st.title("🌍 هضبة الماسة - نظام المعلومات الجغرافية")
    
    files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
    if not files:
        st.error("No GIS files detected.")
        return
    
    target_file = files[0]
    
    # Phase 1: Load Metadata
    with st.spinner("⏳ جاري قراءة قواعد البيانات..."):
        meta_df, err = load_metadata(target_file, ASSETS_PATH)
    
    if err:
        st.error(f"Error reading file structure: {err}")
        return

    # Phase 2: Sidebar Filters
    st.sidebar.markdown("### 🔍 تصفية البيانات")
    
    govs = sorted(meta_df['gov'].unique())
    sel_gov = st.sidebar.selectbox("المحافظة", ["إختر المحافظة"] + govs)
    
    if sel_gov != "إختر المحافظة":
        secs = sorted(meta_df[meta_df['gov'] == sel_gov]['sec'].unique())
        sel_sec = st.sidebar.selectbox("القسم / المركز", ["إختر القسم"] + secs)
        
        if sel_sec != "إختر القسم":
            # Phase 3: Targeted Data Loading
            with st.spinner(f"⏳ جاري تحميل بيانات {sel_sec}..."):
                gdf, load_err = load_section_data(target_file, ASSETS_PATH, sel_gov, sel_sec)
            
            if load_err:
                st.error(f"Error loading section: {load_err}")
            elif not gdf.empty:
                st.sidebar.success(f"✅ تم تحميل {len(gdf)} سجل")
                
                # Map
                center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
                m = folium.Map(location=center, zoom_start=13)
                
                # Google Satellite Hybrid Layer
                google_hybrid = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
                folium.TileLayer(
                    tiles=google_hybrid,
                    attr="Google Satellite",
                    name="Satellite View",
                    overlay=False,
                    control=True
                ).add_to(m)

                folium.GeoJson(
                    gdf,
                    style_function=lambda f: {
                        'fillColor': '#00E676' if 'مقبول' in str(f['properties'].get('survey_review_status')) else '#FF1744',
                        'color': 'white', 'weight': 1, 'fillOpacity': 0.5
                    },
                    tooltip=folium.GeoJsonTooltip(fields=['requestnumber', 'survey_review_status'], aliases=['رقم الطلب:', 'الحالة:'])
                ).add_to(m)
                
                st_folium(m, height=600, width='100%')
                st.write("---")
                st.dataframe(gdf.drop(columns='geometry'), use_container_width=True)
            else:
                st.warning("⚠️ لا توجد بيانات لهذا التقسيم")
        else:
            st.info("👈 يرجى اختيار القسم لعرض الخريطة")
    else:
        st.info("👈 ابدأ باختيار المحافظة من القائمة الجانبية")

if __name__ == "__main__":
    main()
