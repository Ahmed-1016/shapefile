import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap
import os
import json
import pandas as pd
import folium
from folium.plugins import LocateControl, Draw
from streamlit_folium import st_folium
import shapely.geometry as sg
import traceback

# 1. Page Config (Must be first)
st.set_page_config(
    page_title="El Massa Consult - GIS Premium",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="auto"
)

# 2. Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .main-title {
        background: linear-gradient(90deg, #00C853, #00B0FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Path Detection
def get_assets_path():
    possible = [
        os.path.join(".", "assets", "gis"),
        os.path.join("..", "assets", "gis"),
        os.path.join(".", "gis_assets"),
        "assets/gis",
        "gis_service/assets/gis"
    ]
    for p in possible:
        if os.path.exists(p) and any(f.endswith('.gpkg') for f in os.listdir(p)):
            return p
    return "."

ASSETS_PATH = get_assets_path()

# 4. Data Loading Logic
@st.cache_data
def load_data(file_name, base_path):
    path = os.path.join(base_path, file_name)
    if not os.path.exists(path):
        return None, f"❌ الملف غير موجود: {path}"
    
    try:
        # Load only essential columns
        essential = ['geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status']
        try:
            gdf = gpd.read_file(path, engine='pyogrio', columns=essential)
        except:
            gdf = gpd.read_file(path)
            gdf = gdf[[c for c in essential if c in gdf.columns]]
        
        # Simplify geometry for performance
        gdf['geometry'] = gdf['geometry'].simplify(0.0001)
        
        # Cleanup types for JS serialization
        for col in gdf.columns:
            if col != 'geometry':
                if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                    gdf[col] = gdf[col].dt.strftime('%Y-%m-%d')
                else:
                    gdf[col] = gdf[col].astype(str).replace('nan', '')
        
        if gdf.crs is None: gdf.set_crs(epsg=4326, inplace=True)
        else: gdf = gdf.to_crs(epsg=4326)
        
        return gdf, None
    except Exception as e:
        return None, f"Error: {str(e)}"

# 5. Main App
def main():
    try:
        st.markdown('<h1 class="main-title">🌍 El Massa Consult - GIS View</h1>', unsafe_allow_html=True)
        
        # Debug info in sidebar
        st.sidebar.markdown("### 🛠️ DEBUG INFO")
        st.sidebar.text(f"Path: {ASSETS_PATH}")
        if st.sidebar.button("🧹 Clear Cache"):
            st.cache_data.clear()
            st.rerun()

        files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
        
        if not files:
            uploaded = st.file_uploader("Upload GPKG", type=['gpkg'])
            if uploaded:
                if not os.path.exists("temp"): os.makedirs("temp")
                with open(f"temp/{uploaded.name}", "wb") as f: f.write(uploaded.getbuffer())
                target_file, target_path = uploaded.name, "temp"
            else:
                st.info("Please upload a file or add to assets/gis")
                return
        else:
            target_file, target_path = files[0], ASSETS_PATH

        with st.spinner("Loading..."):
            gdf, err = load_data(target_file, target_path)
        
        if err:
            st.error(err)
            return

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            govs = sorted(gdf['gov'].unique()) if 'gov' in gdf.columns else []
            sel_gov = st.selectbox("المحافظة", ["الكل"] + govs)
        
        filtered = gdf
        if sel_gov != "الكل": filtered = filtered[filtered['gov'] == sel_gov]
        
        with col2:
            secs = sorted(filtered['sec'].unique()) if 'sec' in filtered.columns else []
            sel_sec = st.selectbox("القسم", ["الكل"] + secs)
        
        if sel_sec != "الكل": filtered = filtered[filtered['sec'] == sel_sec]
        
        with col3:
            search = st.text_input("بحث برقم الطلب")
            if search: filtered = filtered[filtered['requestnumber'].str.contains(search, na=False)]

        st.divider()

        if sel_sec == "الكل":
            st.warning("⚠️ اختر قسماً محدداً لعرض الخريطة")
        elif filtered.empty:
            st.error("❌ لا توجد بيانات")
        else:
            # Map Fragment
            @st.fragment
            def show_map(df):
                m = leafmap.Map(center=[df.geometry.centroid.y.mean(), df.geometry.centroid.x.mean()], zoom=13)
                m.add_basemap("HYBRID")
                
                folium.GeoJson(
                    df,
                    style_function=lambda f: {
                        'fillColor': '#4CAF50' if f['properties'].get('survey_review_status') == 'مقبول' else '#F44336',
                        'color': 'white', 'weight': 1, 'fillOpacity': 0.6
                    },
                    tooltip=folium.GeoJsonTooltip(fields=['requestnumber', 'survey_review_status'])
                ).add_to(m)
                
                st_folium(m, height=600, width='stretch')
                
                st.subheader("📊 البيانات المحددة")
                st.dataframe(df.drop(columns='geometry'), hide_index=True)

            show_map(filtered)

    except Exception as e:
        st.error("🚨 Critical Error")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
