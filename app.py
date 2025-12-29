import streamlit as st
import os

# --- APP VERSION ---
VERSION = "2.3.0 (Power Selection)"

# 1. Page Config
st.set_page_config(
    page_title=f"الماسة كونسلت GIS - {VERSION}",
    page_icon="🌍",
    layout="wide"
)

# Initialize Session State
if 'selected_requests' not in st.session_state:
    st.session_state.selected_requests = []

# 2. Lazy Imports
try:
    import geopandas as gpd
    import pandas as pd
    import folium
    from folium.plugins import LocateControl, Draw
    from streamlit_folium import st_folium
    import traceback
    from shapely.geometry import shape
except Exception as e:
    st.error(f"❌ خطأ في تحميل المكتبات: {e}")
    st.stop()

# 3. Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0A1128; color: white; }
    .stMultiSelect div[role="listbox"] { color: black !important; }
    .legend-box { padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 10px; margin-bottom: 10px; border: 1px solid #1E2A47; }
    .legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.8em; margin-bottom: 4px; }
    .dot { height: 10px; width: 10px; border-radius: 2px; display: inline-block; }
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

    # --- FIX: JSON Serialization (Date objects crash Folium/JSON) ---
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]) or gdf[col].dtype == object:
            # Try to catch date objects specifically if they are in 'object' dtype
            try:
                gdf[col] = gdf[col].apply(lambda x: x.isoformat() if hasattr(x, 'isoformat') else x)
            except:
                pass

    return gdf

# 6. Main App
def main():
    st.sidebar.markdown(f"### 🌐 نظام الماسة المتطور")
    st.sidebar.caption(f"إصدار التحديد الذكي: {VERSION}")
    
    if st.sidebar.button("🗑️ مسح كافة التحديدات"):
        st.session_state.selected_requests = []
        st.rerun()

    st.title("🗺️ تحديد الأشكال والمساحات المتعددة")

    files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
    if not files:
        st.error("⚠️ ملفات البيانات غير موجودة.")
        return
    
    target_file = files[0]

    # Legend Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div class="legend-box">
        <div class="legend-item"><span class="dot" style="background:#00E676"></span> مقبول</div>
        <div class="legend-item"><span class="dot" style="background:#FFEA00"></span> تحت المراجعة</div>
        <div class="legend-item"><span class="dot" style="background:#FF1744"></span> مرفوض / ملغى</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        # 1. Filtration
        meta_df = load_meta(target_file, ASSETS_PATH)
        govs = sorted(meta_df['gov'].unique())
        sel_gov = st.sidebar.selectbox("اختر المحافظة", ["-- اختر المحافظة --"] + govs)
        
        if sel_gov != "-- اختر المحافظة --":
            secs = sorted(meta_df[meta_df['gov'] == sel_gov]['sec'].unique())
            sel_sec = st.sidebar.selectbox(f"اختر القسم في {sel_gov}", ["-- اختر القسم --"] + secs)
            
            if sel_sec != "-- اختر القسم --":
                with st.spinner("⏳ جاري تحليل خرائط القسم..."):
                    gdf = load_map_data(target_file, ASSETS_PATH, sel_gov, sel_sec)
                
                if not gdf.empty:
                    # --- NEW: MULTI-SELECT DROPDOWN SYNC ---
                    all_ids = sorted(gdf['requestnumber'].unique().tolist())
                    
                    st.sidebar.markdown("---")
                    selected_from_sidebar = st.sidebar.multiselect(
                        "🔍 ابحث واربط الأرقام يدوياً:",
                        options=all_ids,
                        default=st.session_state.selected_requests,
                        help="يمكنك اختيار أرقام الطلبات مباشرة من هذه القائمة أيضاً"
                    )
                    
                    # Sync if sidebar changed
                    if set(selected_from_sidebar) != set(st.session_state.selected_requests):
                        st.session_state.selected_requests = selected_from_sidebar
                        st.rerun()

                    # Map Layout
                    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
                    m = folium.Map(location=center, zoom_start=14)
                    LocateControl(auto_start=False).add_to(m)
                    
                    folium.TileLayer(
                        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                        attr="Google Satellite",
                        name="Satellite View",
                        overlay=False, control=True
                    ).add_to(m)

                    # Drawing Tools (Spatial Select)
                    Draw(
                        export=True,
                        draw_options={
                            'polyline': False, 'circle': False, 'marker': False, 'circlemarker': False,
                            'rectangle': True, 'polygon': True
                        },
                        edit_options={'edit': False}
                    ).add_to(m)

                    # Layers
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

                    st.info("💡 **طرق التحديد المتعدد:** (1) اضغط على الأشكال مباشرة، (2) استخدم أدوات الرسم (المربع) من يسار الخريطة، (3) اختر من قائمة البحث الجانبية.")
                    
                    map_out = st_folium(m, height=520, width='100%', key="power_gis_map")

                    # Handle User Interactions
                    updated = False
                    
                    # A. Click Interaction
                    if map_out.get("last_object_clicked"):
                        clicked = map_out["last_object_clicked"]
                        if "properties" in clicked and "requestnumber" in clicked["properties"]:
                            req = clicked["properties"]["requestnumber"]
                            current_list = list(st.session_state.selected_requests)
                            if req in current_list:
                                current_list.remove(req)
                            else:
                                current_list.append(req)
                            st.session_state.selected_requests = current_list
                            updated = True

                    # B. Drawing Interaction
                    if map_out.get("all_drawings"):
                        for drawing in map_out["all_drawings"]:
                            if drawing.get("geometry"):
                                draw_geom = shape(drawing["geometry"])
                                matched_ids = gdf[gdf.intersects(draw_geom)]['requestnumber'].tolist()
                                if matched_ids:
                                    current_set = set(st.session_state.selected_requests)
                                    for mid in matched_ids:
                                        if mid not in current_set:
                                            current_set.add(mid)
                                            updated = True
                                    st.session_state.selected_requests = list(current_set)

                    if updated:
                        st.rerun()

                    # Table Display
                    st.divider()
                    if st.session_state.selected_requests:
                        display_df = gdf[gdf['requestnumber'].isin(st.session_state.selected_requests)]
                        st.success(f"📌 تم تحديد {len(display_df)} طلب. البيانات المعروضة مطابقة للتحديد:")
                    else:
                        display_df = gdf
                        st.subheader(f"📊 القائمة الحالية في {sel_sec}")

                    st.dataframe(
                        display_df.drop(columns=['geometry', 'status_color']),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("⚠️ لا توجد بيانات لهذا التقسيم.")
            else:
                st.info("👈 يرجى اختيار القسم.")
        else:
            st.info("👈 يرجى اختيار المحافظة.")

    except Exception as e:
        st.error("🚨 خطأ تقني غير متوقع")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
