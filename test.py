import requests
import pandas as pd
def fetch_forecast(lat=34.05,lon=131.57):
    url="https://api.open-meteo.com/v1/forecast"
    daily=["temperature_2m_max","temperature_2m_min","uv_index_max"]
    params={
        "latitude":lat,
        "longitude":lon,
        "daily":",".join(daily),
        "timezone":"Asia/Tokyo"
    }
    r=requests.get(url,params=params)
    r.raise_for_status()
    data=r.json()
    daily=data["daily"]
    df=pd.DataFrame(daily)
    df["time"]=pd.to_datetime(df["time"])
    df=df.rename(columns={
        "time":"日付",
        "temperature_2m_max":"最高気温",
        "temperature_2m_min":"最低気温",
        "uv_index_max":"紫外線"
    })
    return df

if __name__=="__main__":
    df=fetch_forecast()


print(df)



