import datetime
import os
from enum import Enum
from typing import Dict, List

import pandas as pd
import streamlit as st
from google_map_analyzer import PlaceType, run_search_api

st.set_page_config(layout="wide")


# --- 1日の検索回数制限
DATA_FILE = "button_data.txt"
SEARCH_LIMIT = 15


def read_data():
    if not os.path.exists(DATA_FILE):
        return 0, None

    with open(DATA_FILE, "r") as f:
        lines = f.readlines()
        count = int(lines[0].strip())
        last_date = datetime.datetime.strptime(lines[1].strip(), "%Y-%m-%d").date()
        return count, last_date


def write_data(count, date):
    with open(DATA_FILE, "w") as f:
        f.write(str(count) + "\n")
        f.write(date.strftime("%Y-%m-%d"))


count, last_date = read_data()
today = datetime.date.today()

if last_date is None or last_date != today:
    count = 0
# ---


link_css = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"> 
"""
st.write(link_css, unsafe_allow_html=True)


st.title("SNS検索")

keyword = st.text_input("キーワードを入力してください", "ラーメン")
location = st.text_input("場所を入力してください", value="仙台駅")
radius = st.slider("検索半径を選択してください(m)", min_value=1, max_value=10000, value=1000)

type_list = list(PlaceType)
type_list.append("指定なし")
shop_type = st.selectbox(
    "タイプを選択してください",
    type_list,
    index=type_list.index("指定なし"),
)
sns_only = st.checkbox("SNSが存在する店舗のみ")

# Check if session state is already initialized
if "results" not in st.session_state:
    st.session_state["results"] = pd.DataFrame()

search_col, download_col = st.columns([1, 1])  # set up the columns


if (
    search_col.button("検索", disabled=not (count < SEARCH_LIMIT))
    and count < SEARCH_LIMIT
):
    results = run_search_api(keyword, location, radius, limit=5, _type=shop_type)
    results = [result for result in results if result["sns"] or not sns_only]

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

    # 検索制限 +1
    count += 1
    write_data(count, today)

if count >= SEARCH_LIMIT:
    st.warning("本日のボタンの押下回数の上限に達しました。")
else:
    remaining = SEARCH_LIMIT - count
    st.info(f"本日の残りの押下回数: {remaining} / {SEARCH_LIMIT}")


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
