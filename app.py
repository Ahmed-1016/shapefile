import streamlit as st
import os
import sys

# 1. Page Config
st.set_page_config(page_title="GIS Diagnostics", layout="wide")

# 2. Memory Tracking
try:
    import psutil
    process = psutil.Process(os.getpid())
    mem_usage = process.memory_info().rss / (1024 * 1024)
except:
    mem_usage = 0

st.sidebar.markdown(f"### 📊 RAM Usage: {mem_usage:.1f} MB")

# 3. Fail-safe Library Imports
GIS_LIBS_LOADED = False
try:
    import geopandas as gpd
    import pandas as pd
    import folium
    from streamlit_folium import st_folium
    import traceback
    GIS_LIBS_LOADED = True
except Exception as e:
    st.error(f"❌ GIS Libraries failed to load: {e}")

# 4. Path Detection
def get_assets_path():
    possible = ["assets/gis", "gis_assets", "."]
    for p in possible:
        if os.path.exists(p) and any(f.endswith('.gpkg') for f in os.listdir(p)):
            return p
    return "."

ASSETS_PATH = get_assets_path()

# 5. Optimized Data Loading
@st.cache_data
def load_data_ultrasafe(file_name, base_path):
    path = os.path.join(base_path, file_name)
    try:
        # Strict memory limit: 5000 rows initially
        essential = ['geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status']
        gdf = gpd.read_file(path, engine='pyogrio', columns=essential, use_arrow=True)
        
        # Aggressive sampling for cloud stability
        total_rows = len(gdf)
        if total_rows > 5000:
            gdf = gdf.sample(5000)
            
        gdf['geometry'] = gdf['geometry'].simplify(0.0005, preserve_topology=True)
        
        for col in gdf.columns:
            if col != 'geometry':
                gdf[col] = gdf[col].astype(str).replace('nan', '')
        
        gdf = gdf.to_crs(epsg=4326)
        return gdf, total_rows, None
    except Exception as e:
        return None, 0, str(e)

def main():
    st.title("🌍 El Massa Consult - GIS Diagnostics")
    
    if not GIS_LIBS_LOADED:
        st.warning("⚠️ Application running in Diagnostics mode. GIS features are disabled.")
        return

    st.sidebar.text(f"Path: {ASSETS_PATH}")
    files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
    
    if not files:
        uploaded = st.file_uploader("Upload GPKG", type=['gpkg'])
        if uploaded:
            if not os.path.exists("temp"): os.makedirs("temp")
            with open(f"temp/{uploaded.name}", "wb") as f: f.write(uploaded.getbuffer())
            target_f, target_p = uploaded.name, "temp"
        else: return
    else:
        target_f, target_p = files[0], ASSETS_PATH

    if st.button("🚀 Load GIS Map"):
        with st.spinner("Processing..."):
            gdf, count, err = load_data_ultrasafe(target_f, target_p)
            
            if err:
                st.error(f"🚨 Serialization/Loading Error: {err}")
                st.code(traceback.format_exc())
            else:
                st.success(f"Loaded {len(gdf)} of {count} records (Sampled for stability)")
                
                center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
                m = folium.Map(location=center, zoom_start=13)
                
                folium.GeoJson(
                    gdf,
                    style_function=lambda f: {'fillColor': '#4CAF50' if 'مقبول' in str(f['properties']) else '#F44336', 'color': 'white', 'weight': 1}
                ).add_to(m)
                
                st_folium(m, height=500, width='100%')
                st.dataframe(gdf.drop(columns='geometry').head(100))

if __name__ == "__main__":
    main()
