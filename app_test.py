import requests
import pandas as pd
def fetch_forecast(lat=34.05,lon=131.57):
    url="https://api.open-meteo.com/v1/forecast"
    params={
            "latitude" :lat,
            "longitude":lon,
            "daily":",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "precipitation_probability_mean",
                "uv_index_max",
                "wind_speed_10m_max"
            ]),
            "timezone":"Asia/Tokyo"
    }

    r=requests.get(url,params=params,timeout=10)
    r.raise_for_status()
    j=r.json()
    daily=j["daily"]

    df=pd.DataFrame(daily)

    df["time"]=pd.to_datetime(df["time"])
    df=df.rename(columns={
        "time":"data",
        "temperature_2m_max":"tmax",
        "temperature_2m_min":"tmin",
        "apparent_temperature_max":"app_max",
        "precipitation_probability_mean":"pop",
        "uv_index_max":"uv",
        "wind_speed_10m_max":"wind"
    })
    return df
if __name__=="__main__":
    df=fetch_forecast()
    #print(df)
#折れ線の下ごしらえ。気温を縦にし、そのほかを色分けして表示
def to_long_for_chart(df):
    plot_df=pd.melt(
        df[["date","tmax","tmin","app_max"]],
        id_vars=["data"],
        var_name="kind",
        value_name="temp").sort_values("date")
    return plot_df

#コーデ判定のロジック
def outfit_rules(row):
    base=row["app_max"] if pd.notna(row.get("app_max"))else row["tmax"]
    tips=[]
    #温度帯（ざっくり）
    if base>=30:
        tips+=["Tシャツ","通気性トップス","サングラス"]
    elif base>=25:
        tips+=["半袖","薄手カーデ"]
    elif base>=15:
        tips+=["ライトジャケット"]
    else:
        tips+=["厚手コート","マフラー・手袋"]
    #調整要素
    if row.get("pop",0)>=50:
        tips+=["撥水アウター","防水スニーカー"]
    if row.get("uv",0)>=6:
        tips+=["日傘/帽子","サングラス（UV強）"]
    if row.get("wind",0)>=8:
        tips+=["フード付き","飛ばされにくい帽子"]

    return list(dict.fromkeys(tips))


    