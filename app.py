import streamlit as st
import os

# --- APP VERSION ---
VERSION = "2.2.0 (Spatial Multi-Select)"

# 1. Page Config
st.set_page_config(
    page_title=f"الماسة كونسلت GIS - {VERSION}",
    page_icon="🌍",
    layout="wide"
)

# Initialize Session State
if 'selected_requests' not in st.session_state:
    st.session_state.selected_requests = set()

# 2. Lazy Imports
try:
    import geopandas as gpd
    import pandas as pd
    import folium
    from folium.plugins import LocateControl, Draw
    from streamlit_folium import st_folium
    import traceback
    from shapely.geometry import shape, box
except Exception as e:
    st.error(f"❌ خطأ في تحميل المكتبات: {e}")
    st.stop()

# 3. Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0A1128; color: white; }
    .legend-box {
        padding: 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        margin-bottom: 10px;
    }
    .legend-item { display: flex; align-items: center; margin-bottom: 5px; gap: 10px; font-size: 0.85em; }
    .dot { height: 12px; width: 12px; border-radius: 2px; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# 4. Helpers
def get_color(status):
    status = str(status)
    if 'مقبول' in status: return '#00E676'
    if 'مرفوض' in status or 'ملغى' in status: return '#FF1744'
    return '#FFEA00'

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
    gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)
    if gdf.crs is None: gdf.set_crs(epsg=4326, inplace=True)
    else: gdf = gdf.to_crs(epsg=4326)
    gdf['status_color'] = gdf['survey_review_status'].apply(get_color)
    return gdf

# 6. Main App
def main():
    st.sidebar.markdown(f"### 🌐 El Massa GIS (V{VERSION})")
    
    if st.sidebar.button("🔄 إعادة تشغيل وتصفير"):
        st.cache_data.clear()
        st.session_state.selected_requests = set()
        st.rerun()

    if st.sidebar.button("🗑️ مسح التحديد الحالي") and st.session_state.selected_requests:
        st.session_state.selected_requests = set()
        st.rerun()

    st.title("🗺️ تحديد الأشكال المتعدد ونظام تحليل البيانات المساحية")

    files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
    if not files:
        st.error("لم يتم العثor على بيانات.")
        return
    
    target_file = files[0]

    # Legend Sidebar
    st.sidebar.markdown("#### 🎨 الحالات")
    st.sidebar.markdown(f"""
    <div class="legend-box">
        <div class="legend-item"><span class="dot" style="background:#00E676"></span> مقبول</div>
        <div class="legend-item"><span class="dot" style="background:#FFEA00"></span> مراجعة</div>
        <div class="legend-item"><span class="dot" style="background:#FF1744"></span> مرفوض</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        meta_df = load_meta(target_file, ASSETS_PATH)
        govs = sorted(meta_df['gov'].unique())
        sel_gov = st.sidebar.selectbox("المحافظة", ["-- اختر --"] + govs)
        
        if sel_gov != "-- اختر --":
            secs = sorted(meta_df[meta_df['gov'] == sel_gov]['sec'].unique())
            sel_sec = st.sidebar.selectbox(f"القسم في {sel_gov}", ["-- اختر --"] + secs)
            
            if sel_sec != "-- اختر --":
                with st.spinner("⏳ جاري سحب الخرائط..."):
                    gdf = load_map_data(target_file, ASSETS_PATH, sel_gov, sel_sec)
                
                if not gdf.empty:
                    # Map Setup
                    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
                    m = folium.Map(location=center, zoom_start=14)
                    
                    LocateControl(auto_start=False).add_to(m)
                    
                    # Google Satellite Layer
                    folium.TileLayer(
                        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                        attr="Google Satellite",
                        name="الأقمار الصناعية",
                        overlay=False,
                        control=True
                    ).add_to(m)

                    # Draw Plugin for Multi-Select (Rectangle/Polygon)
                    draw = Draw(
                        export=True,
                        draw_options={
                            'polyline': False,
                            'circle': False,
                            'marker': False,
                            'circlemarker': False,
                            'rectangle': True,
                            'polygon': True
                        },
                        edit_options={'edit': False}
                    )
                    draw.add_to(m)

                    # Main GeoJson Layer
                    folium.GeoJson(
                        gdf,
                        style_function=lambda f: {
                            'fillColor': f['properties'].get('status_color'),
                            'color': '#00B0FF' if f['properties'].get('requestnumber') in st.session_state.selected_requests else 'white',
                            'weight': 3 if f['properties'].get('requestnumber') in st.session_state.selected_requests else 1,
                            'fillOpacity': 0.8 if f['properties'].get('requestnumber') in st.session_state.selected_requests else 0.5
                        },
                        tooltip=folium.GeoJsonTooltip(fields=['requestnumber', 'survey_review_status'], aliases=['الطلب:', 'الحالة:'])
                    ).add_to(m)

                    st.markdown("""
                    **💡 طرق التحديد:**
                    1. **بالضغط:** اضغط على أي مضلع لاختياره أو إلغاء اختياره.
                    2. **بالرسم:** استخدم أدوات الرسم (المربع أو المضلع) من يسار الخريطة لتحديد منطقة بالكامل واختيار ما بداخلها.
                    """)
                    
                    map_out = st_folium(m, height=500, width='100%', key="advanced_map")

                    # 1. HANDLE CLICK SELECTION (Toggle)
                    if map_out.get("last_object_clicked"):
                        clicked = map_out["last_object_clicked"]
                        if "properties" in clicked and "requestnumber" in clicked["properties"]:
                            req = clicked["properties"]["requestnumber"]
                            if req in st.session_state.selected_requests:
                                st.session_state.selected_requests.remove(req)
                            else:
                                st.session_state.selected_requests.add(req)
                            st.rerun()

                    # 2. HANDLE DRAW SELECTION (Spatial Query)
                    if map_out.get("all_drawings"):
                        new_selection = False
                        for drawing in map_out["all_drawings"]:
                            if drawing.get("geometry"):
                                draw_shape = shape(drawing["geometry"])
                                # Find all requests intersecting with drawn area
                                matches = gdf[gdf.intersects(draw_shape)]['requestnumber'].tolist()
                                if matches:
                                    for m_req in matches:
                                        if m_req not in st.session_state.selected_requests:
                                            st.session_state.selected_requests.add(m_req)
                                            new_selection = True
                        if new_selection:
                            st.rerun()

                    st.divider()

                    # 3. DISPLAY TABLE
                    if st.session_state.selected_requests:
                        display_df = gdf[gdf['requestnumber'].isin(st.session_state.selected_requests)]
                        st.success(f"📌 تم تحديد {len(display_df)} طلب مصور")
                    else:
                        display_df = gdf
                        st.subheader("📋 كافة البيانات المعروضة")

                    st.dataframe(
                        display_df.drop(columns=['geometry', 'status_color']),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("⚠️ لا توجد بيانات لهذا القسم.")
            else:
                st.info("👈 اختر القسم للبدء.")
        else:
            st.info("👈 اختر المحافظة للبدء.")

    except Exception as e:
        st.error("🚨 خطأ تقني")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
