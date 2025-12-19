import requests
import pandas as pd
import altair as alt
import streamlit as st
from datetime import date


st.set_page_config(page_title="今日のおすすめコーデ！",page_icon="👔",layout="wide")



#-------データの取得-------
@st.cache_data(show_spinner=False,ttl=60*30)
def fetch_forecast_df(lat:float,lon:float,start:str|None=None,end:str|None=None)->pd.DataFrame:
    """Open-Meteop(目次)→DataFrame(date,tmax,tmin,app_max,pop,uv,wind)"""    
    url="https://api.open-meteo.com/v1/forecast"
    daily_vars=[
        "temperature_2m_max",
        "temperature_2m_min",
        "apparent_temperature_max",
        "precipitation_probability_mean",
        "uv_index_max",
        "wind_speed_10m_max",
    ]
    params={
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(daily_vars),
        "timezone": "Asia/Tokyo",
    }

    if start and end :
        params["start_date"]=start
        params["end_date"]=end
    
    r=requests.get(url,params=params,timeout=15)
    r.raise_for_status()
    j=r.json()
    df=pd.DataFrame(j["daily"])
    df["time"]=pd.to_datetime(df["time"])
    df=df.rename(
        columns={
            "time": "date",
            "temperature_2m_max": "tmax",
            "temperature_2m_min": "tmin",
            "apparent_temperature_max": "app_max",
            "precipitation_probability_mean": "pop",
            "uv_index_max": "uv",
            "wind_speed_10m_max": "wind",
        }
    )
    #形
    num_cols=["tmax","tmin","app_max","pop","uv","wind"]
    for c in num_cols:
        df[c]=pd.to_numeric(df[c],errors="coerce")
    return df

def to_long_for_chart(df:pd.DataFrame)->pd.DataFrame:
    """AItair用に縦持ち化：date,kind,temp"""
    plot_df=pd.melt(
        df[["date","tmax","tmin","app_max"]],
        id_vars=["date"],
        var_name="kind",
        value_name="temp",
    ).sort_values("date")
    return plot_df

def outfit_rules(row:pd.Series)->list[str]:
    """"1日の提案アイテムを返す（体感優先）"""
    base=row["app_max"]if pd.notna(row["app_max"]) else row["tmax"]
    tips: list[str]=[]
    #温度帯
    if base >=30:
        tips+=["Tシャツ","通気性トップス","サングラス"]
    elif base >=25:
        tips+=["半袖","薄手羽織（冷房対策に）"]
    elif base >=15:
        tips+=["長袖シャツ","薄手カーデ"]
    elif base >=10:
        tips+=["薄手コート","暖かインナー"]
    else :
        tips +=["厚手コート","マフラー・手袋"]
    #調整
    if pd.notna(row["pop"]) and row["pop"] >= 50:
        tips += ["撥水アウター","防水シューズ"]
    if pd.notna(row["uv"]) and row["uv"] >=6:
        tips +=["日傘/帽子","サングラス（UV強）"]
    if pd.notna(row["wind"]) and row["wind"]>=8:
        tips+=["フード付き","飛ばされにくい帽子"]
    #重複除去して順序維持
    return list(dict.fromkeys(tips))
#------UI------------
st.title("今日のおすすめコーデ・7days")
with st.sidebar:
    st.header("住んでる場所を選んでね")
    presets={
        "山口(周南/下松)":(34.05,131.57),
        "福岡(福岡市)":(33.59,130.40),
        "東京":(35.68,139.76),
        "大阪":(34.69,135.50),
        "札幌":(43.06,141.35),
    }
    city=st.selectbox("プリセット",list(presets.keys()))
    default_lat,default_lon=presets[city]

    with st.expander("緯度・経度を手動で調整"):
        lat=st.number_input("緯度(latitude)",value=float(default_lat),format="%.5f")
        lon=st.number_input("経度(longitude)",value=float(default_lon),format="%.5f")
    st.caption("※都市はおおよその中心点。必要なら緯度経度を微調整してね")

    st.header("オプション")
    show_pop =st.checkbox("降水確率カード表示",value=True)
    show_uv =st.checkbox("uv指数カード表示",value=True)
    show_wind = st.checkbox("風速カード表示",value=True)

#表示期間の設定　7日間
today_iso=date.today().isoformat()
df=fetch_forecast_df(lat,lon,start=today_iso,end=today_iso)
df=fetch_forecast_df(lat,lon)

#------グラフ-------

plot_df=to_long_for_chart(df)

ymin=float(pd.concat([plot_df["temp"]]).min())-2
ymax=float(pd.concat([plot_df["temp"]]).max())+2

chart=(
    alt.Chart(plot_df)
    .mark_line(point=True,clip=True)
    .encode(
        x=alt.X("date:T",title="日付"),
        y=alt.Y("temp:Q",title="気温（℃）",scale=alt.Scale(domain=[ymin,ymax])),
        color=alt.Color(
            "kind:N",
            title="系列",
            scale=alt.Scale(
                domain=["tmax","tmin","app_max"],
                range=["#d62728","#1f77b4","#2ca02c"],
            ),
            legend=alt.Legend(
                labelExpr='{"tmax":"最高","tmin":"最低","app_max":"体感"}[datum.label]'
            ),
        ),
        tooltip=[alt.Tooltip("date:T",title="日付"),alt.Tooltip("kind:N",title="系列"),alt.Tooltip("temp:Q",title="気温(℃)",format=".1f")],
    )
).properties(height=360)

st.subheader(f"7日間の気温(緯度{lat:.3f},緯度{lon:.3f})")
st.altair_chart(chart,use_container_width=True)

#---------今日のコーデ-----------
st.subheader("今日のコーデ")
today_row=df.iloc[0]
items=outfit_rules(today_row)

cols= st.columns(3)
with cols[0]:
    st.metric("体感(最高)", f"{today_row['app_max']:.1f} ℃" if pd.notna(today_row["app_max"]) else f"{today_row['tmax']:.1f} ℃")
with cols[1]:
    st.metric("最高 / 最低", f"{today_row['tmax']:.1f} ℃ / {today_row['tmin']:.1f} ℃")
with cols[2]:
    info = []
    if show_pop and pd.notna(today_row["pop"]):
        info.append(f"降水 {int(today_row['pop'])}%")
    if show_uv and pd.notna(today_row["uv"]):
        info.append(f"UV {today_row['uv']:.1f}")
    if show_wind and pd.notna(today_row["wind"]):
        info.append(f"風 {today_row['wind']:.1f} m/s")
    st.metric("コンディション", " / ".join(info) if info else "—")
st.write("**おすすめアイテム**：", "、".join(items))

# ---------- 週間の簡易カード ----------
st.subheader("週間のコーデヒント")
grid = st.columns(7, gap="small")
for i, (_, r) in enumerate(df.head(7).iterrows()):
    with grid[i]:
        st.caption(r["date"].strftime("%-m/%-d (%a)") if hasattr(r["date"], "strftime") else str(r["date"]))
        st.write(f"**{r['tmax']:.0f} / {r['tmin']:.0f} ℃**")
        add = []
        if show_pop and pd.notna(r["pop"]):
            add.append(f"☔{int(r['pop'])}%")
        if show_uv and pd.notna(r["uv"]):
            add.append(f"☀UV{r['uv']:.0f}")
        if show_wind and pd.notna(r["wind"]):
            add.append(f"🍃{r['wind']:.0f}m/s")
        st.write(" ".join(add))
        small = outfit_rules(r)[:2]  # 代表2点だけ
        if small:
            st.caption("・" + " / ".join(small))