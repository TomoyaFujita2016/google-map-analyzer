import streamlit as st
import pandas as pd
from enum import Enum
from typing import List, Dict

from google_map_analyzer import PlaceType, run_search_api

st.set_page_config(layout="wide")


link_css = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"> 
"""
st.write(link_css, unsafe_allow_html=True)


st.title("SNS検索")

keyword = st.text_input("キーワードを入力してください", "スイーツ")
location = st.text_input("場所を入力してください", value="東京駅")
radius = st.slider("検索半径を選択してください(m)", min_value=3, max_value=10000, value=1000)
shop_type = st.selectbox(
    "タイプを選択してください", list(PlaceType), index=list(PlaceType).index(PlaceType.CAFE)
)

# Check if session state is already initialized
if "results" not in st.session_state:
    st.session_state["results"] = pd.DataFrame()

search_col, download_col = st.columns([1, 1])  # set up the columns


if search_col.button("検索"):
    results = run_search_api(keyword, location, radius, limit=1, _type=shop_type)

    # Prepare results for DataFrame
    formatted_results = []
    for result in results:
        details = result["details"]["result"]
        formatted_result = {
            "name": result["name"],
            "google_map_url": result["google_map_url"],
            "phone": details.get("formatted_phone_number", ""),
            "rating": details.get("rating", ""),
            "website": details.get("website", ""),
            "sns": "\n".join(result["sns"]) if result["sns"] else "",
        }
        formatted_results.append(formatted_result)

    # Update session state
    st.session_state["results"] = pd.DataFrame(formatted_results)

# Display results
for index, result in st.session_state["results"].iterrows():
    st.subheader(result["name"])
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"[Google Map]({result['google_map_url']})")
        st.markdown(f"**Phone**: {result['phone']}")
        st.markdown(f"**Rating**: {result['rating']}")
    with col2:
        st.markdown(f"**Website**: [{result['website']}]({result['website']})")
        if result["sns"] != "":
            icons = ""
            for sns in result["sns"].split("\n"):
                if "instagram." in sns:
                    icons += (
                        f'<a href="{sns}"><i class="fab fa-instagram fa-2x"></i></a> '
                    )
                elif "twitter." in sns:
                    icons += (
                        f'<a href="{sns}"><i class="fab fa-twitter fa-2x"></i></a> '
                    )
                elif "tiktok." in sns:
                    icons += f'<a href="{sns}"><i class="fab fa-tiktok fa-2x"></i></a> '
                elif "facebook." in sns:
                    icons += (
                        f'<a href="{sns}"><i class="fab fa-facebook fa-2x"></i></a> '
                    )
                elif "line." in sns:
                    icons += f'<a href="{sns}"><i class="fab fa-line fa-2x"></i></a> '
            st.markdown(icons, unsafe_allow_html=True)

csv = st.session_state["results"].to_csv(index=False)

download_col.download_button(
    label="結果をCSVに保存",
    data=csv,
    file_name="shop_search_results.csv",
    mime="text/csv",
)
