import base64
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="House Price Predictor", page_icon="🏠",
                   layout="wide")


def lerp(a, b, t):
    return a + (b - a) * t


def scale(v, lo, hi, out_lo, out_hi):
    t = max(0.0, min(1.0, (v - lo) / (hi - lo)))
    return lerp(out_lo, out_hi, t)


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return "#" + "".join(
        f"{int(lerp(int(c1[i:i + 2], 16), int(c2[i:i + 2], 16), t)):02x}"
        for i in (1, 3, 5)
    )


def house_svg(qual, area, garage, year, baths, lot_area, frontage, fireplaces):
    W, H, G = 700, 420, 340 
    p = []
    add = p.append

    
    house_w = scale(area, 500, 4000, 150, 300)
    stories = 2 if area >= 1900 else 1
    if stories == 1:
        wall_h = scale(area, 500, 1900, 70, 100)
    else:
        wall_h = scale(area, 1900, 4000, 150, 190)
    floor_h = wall_h / stories
    roof_h = 55
    garage_w = scale(garage, 0, 1400, 0, 170) if garage > 0 else 0
    gap = 8 if garage_w else 0
    total = house_w + gap + garage_w
    x0 = (W - total) / 2
    top = G - wall_h
    cx = x0 + house_w / 2
    lawn_w = min(W - 20, max(scale(frontage, 20, 200, 360, 680), total + 40))
    lawn_x = (W - lawn_w) / 2

    
    wall = mix("#b5aea3", "#f6c990", (qual - 1) / 9)
    roof = mix("#6b3f2a", "#44566b", (year - 1872) / (2010 - 1872))
    garage_wall = mix(wall, "#d9d9d9", 0.5)

    def roof_y(x):
        return top - roof_h * (1 - abs(x - cx) / (house_w / 2 + 12))

    
    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">')
    add('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#8ec5ff"/>'
        '<stop offset="1" stop-color="#e8f4ff"/></linearGradient></defs>')
    add(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    add('<circle cx="630" cy="55" r="28" fill="#ffd54f"/>')
    add('<ellipse cx="110" cy="60" rx="50" ry="15" fill="#fff" opacity=".9"/>')
    add(f'<rect y="{G}" width="{W}" height="{H - G}" fill="#a5d6a0"/>')
    add(f'<rect x="{lawn_x}" y="{G}" width="{lawn_w}" height="{H - G - 30}" '
        f'rx="8" fill="#7fc46b" stroke="#3d7a37" stroke-dasharray="6 4"/>')

    
    n_trees = 1 + int(scale(lot_area, 1500, 40000, 0, 3))
    for tx in [60, 640, 140, 560][:n_trees]:
        add(f'<rect x="{tx - 4}" y="{G - 40}" width="8" height="42" fill="#7a5230"/>')
        add(f'<circle cx="{tx}" cy="{G - 58}" r="28" fill="#2e7d32"/>')

    
    if garage_w >= 20:
        gx = x0 + house_w + gap
        gh = 62
        add(f'<rect x="{gx}" y="{G - gh}" width="{garage_w}" height="{gh}" '
            f'fill="{garage_wall}" stroke="#6b5b4b"/>')
        add(f'<rect x="{gx - 4}" y="{G - gh - 9}" width="{garage_w + 8}" '
            f'height="9" fill="{roof}"/>')
        n_doors = 1 if garage < 550 else 2 if garage < 900 else 3
        dw = (garage_w - 10) / n_doors
        for i in range(n_doors):
            dx = gx + 5 + i * dw
            add(f'<rect x="{dx + 1}" y="{G - 44}" width="{dw - 2}" height="44" '
                f'fill="#cfd8dc" stroke="#90a4ae"/>')
            for k in (1, 2, 3):
                add(f'<line x1="{dx + 1}" y1="{G - 44 + k * 11}" '
                    f'x2="{dx + dw - 1}" y2="{G - 44 + k * 11}" stroke="#90a4ae"/>')

   
    add(f'<rect x="{x0}" y="{top}" width="{house_w}" height="{wall_h}" '
        f'fill="{wall}" stroke="#6b5b4b" stroke-width="2"/>')

    
    for i in range(min(fireplaces, 3)):
        chx = cx + house_w * (-0.3, 0.3, 0.0)[i]
        cy = roof_y(chx)
        add(f'<rect x="{chx - 7}" y="{cy - 30}" width="14" height="45" fill="#8d6e63"/>')
        add(f'<circle cx="{chx + 4}" cy="{cy - 40}" r="6" fill="#cfd8dc" opacity=".7"/>')
        add(f'<circle cx="{chx + 10}" cy="{cy - 52}" r="8" fill="#cfd8dc" opacity=".5"/>')


    add(f'<polygon points="{x0 - 12},{top} {cx},{top - roof_h} '
        f'{x0 + house_w + 12},{top}" fill="{roof}" stroke="#333" stroke-width="2"/>')

    
    n_bath = min(baths, 4)
    for i in range(n_bath):
        bx = cx + (i - (n_bath - 1) / 2) * 20
        add(f'<circle cx="{bx}" cy="{top - 20}" r="7" fill="#bde3ff" '
            f'stroke="#fff" stroke-width="2"/>')

    
    n_win = max(2, int(house_w // 75))
    for f in range(stories):
        fy = G - (f + 1) * floor_h
        slots = n_win + (1 if f == 0 else 0)
        sw = house_w / slots
        for s in range(slots):
            sx = x0 + sw * (s + 0.5)
            if f == 0 and s == slots // 2:
                dh = min(54, floor_h - 8)
                add(f'<rect x="{sx - 11}" y="{G - dh}" width="22" height="{dh}" '
                    f'rx="3" fill="#6d4c41"/>')
                add(f'<circle cx="{sx + 6}" cy="{G - dh / 2}" r="1.8" fill="#ffd54f"/>')
            else:
                wy = fy + (floor_h - 30) / 2
                add(f'<rect x="{sx - 12}" y="{wy}" width="24" height="30" rx="2" '
                    f'fill="#bfe3ff" stroke="#fff" stroke-width="3"/>')
                add(f'<line x1="{sx}" y1="{wy}" x2="{sx}" y2="{wy + 30}" '
                    f'stroke="#fff" stroke-width="2"/>')
                if qual >= 6:
                    add(f'<rect x="{sx - 19}" y="{wy}" width="5" height="30" fill="#3e6b4a"/>')
                    add(f'<rect x="{sx + 14}" y="{wy}" width="5" height="30" fill="#3e6b4a"/>')

   
    if qual <= 3:
        add(f'<polyline points="{x0 + 20},{top + 5} {x0 + 28},{top + 20} '
            f'{x0 + 22},{top + 35} {x0 + 30},{top + 50}" fill="none" '
            f'stroke="#555" stroke-width="1.5"/>')

    add(f'<text x="{W / 2}" y="{H - 10}" text-anchor="middle" '
        f'font-family="sans-serif" font-size="14" fill="#1b4d1b">'
        f'{area} sq ft · quality {qual}/10 · built {year}</text>')
    add('</svg>')
    return "".join(p)


def show_svg(svg):
    b64 = base64.b64encode(svg.encode()).decode()
    st.markdown(
        f'<img src="data:image/svg+xml;base64,{b64}" '
        f'style="width:100%;border-radius:16px;'
        f'box-shadow:0 4px 16px rgba(0,0,0,.15)">',
        unsafe_allow_html=True,
    )


st.markdown("<h1 style='text-align:center'>🏠 House Price Predictor</h1>",
            unsafe_allow_html=True)

left, right = st.columns([2, 3], gap="large")

with left:
    st.subheader("House features")
    qual = st.slider("Overall quality (1-10)", 1, 10, 6)
    area = st.slider("Living area (sq ft)", 500, 4000, 1500, step=50)
    garage = st.slider("Garage area (sq ft, 0 = no garage)", 0, 1400, 480, step=20)
    year = st.slider("Year built", 1872, 2010, 1970)
    baths = st.slider("Full bathrooms", 0, 3, 2)
    fireplaces = st.slider("Fireplaces", 0, 3, 1)
    lot_area = st.slider("Lot area (sq ft)", 1500, 40000, 10000, step=500)
    frontage = st.slider("Lot frontage (ft)", 20, 200, 70)

with right:
    show_svg(house_svg(qual, area, garage, year, baths,
                       lot_area, frontage, fireplaces))
    st.caption("Bigger area → bigger house (2nd floor from 1900 sq ft) · "
               "garage width = garage area · round windows = bathrooms · "
               "chimneys = fireplaces · trees = lot area · "
               "lawn width = lot frontage")

if st.button("Predict price", type="primary", use_container_width=True):
    payload = {
        "OverallQual": qual, "GrLivArea": area, "GarageArea": garage,
        "YearBuilt": year, "FullBath": baths, "LotArea": lot_area,
        "LotFrontage": frontage, "Fireplaces": fireplaces,
    }
    try:
        with st.spinner("Asking the model..."):
            r = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
            r.raise_for_status()
        st.metric("Estimated sale price", f"${r.json()['prediction']:,.0f}")
    except requests.RequestException as e:
        st.error(f"API request failed: {e}")