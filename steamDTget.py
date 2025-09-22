import http.client
import json
import os
import urllib

from dotenv import load_dotenv

single_skin_json = './SteamDTjson/SingleSkin.json'

load_dotenv()
steamDTapi = os.getenv("SteamDTapi")
conn = http.client.HTTPSConnection("open.steamdt.com")
payload = json.dumps(
    {"platform": "",
           "platformItemId": "",
           "sellPrice": 0.0,
           "sellCount": 0,
           "biddingPrice": 0.0,
           "biddingCount": 0,
           "updateTime": 0})

headers = {
    "marketHashName":"AWP | Pit Viper (Minimal Wear)",
    "Authorization": f"Bearer {steamDTapi}"
}
# 正确的物品名
name = "AWP | Pit Viper (Minimal Wear)"
encoded_name = urllib.parse.quote(name)   # 处理空格、竖线、括号
# 关键：f-string 插值
path = f"/open/cs2/v1/price/single?marketHashName={encoded_name}"

conn.request("GET", path, '', headers)
res = conn.getresponse()
data = res.read()
text = data.decode("utf-8")           # 转成 str
parsed = json.loads(text)            # 转成 dict / list
with open(single_skin_json, 'w', encoding='utf-8') as file:
    json.dump(parsed, file, ensure_ascii=False, indent=1)

print(data.decode("utf-8"))


# conn = http.client.HTTPSConnection("open.steamdt.com")
# payload = ''
# headers = {
#     "Authorization": f"Bearer {steamDTapi}"
# }
# conn.request("GET", "/open/cs2/v1/base", payload, headers)
# res = conn.getresponse()
# data = res.read().decode("utf-8")   # 字符串
# print(data)
#
# # 保存到文件
# with open("result.txt", "w", encoding="utf-8") as f:
#     f.write(data)


