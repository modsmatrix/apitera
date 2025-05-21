from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from urllib.parse import parse_qs, urlparse

app = Flask(__name__)
CORS(app)

COOKIE = 'TSID=2ry6kGU1Twa9WfV7G1cNBN4kHIu7kKJv; __bid_n=1953d2ef2e1b85190b4207; _ga=GA1.1.1736863767.1740488242; PANWEB=1; browserid=jikmP8CMH6qAXGYO9PBUj6x9padjsYFvkCdO-2QzqourgO9JGXF5weWfF6g=; _ga_06ZNKL8C2E=GS2.1.s1746854650$o4$g1$t1746856320$j60$l0$h0; lang=en; __stripe_mid=28097f86-68d4-4ef1-8afd-38b2ef009a62edccea; __stripe_sid=3e40b078-e60d-4b17-a412-d32c94d39e69ab538d; csrfToken=GIDLJxVQxNmQjGTdIQ2gOPJw; ab_sr=1.0.1_OGQ1MDJkZGVhMjZkNzNkMWNiY2YwMWMxMGRiYmQ5MDcxNTA3OGU3MDJjYzM4MjYwMWE2YmU5ZDgyYzVhMTBiMTYzMzIwODlhNzhiMjhlZGI0NTU5YjMxNjIwOTE3YzFmZmNkNDA5NjM1MDRkMDQ5OThhMTg4MjMzNGYzNGQ3YmViMTk5NDA2MjhmNTk5ZjE0MGZjOTJjMWI4MzBmZmY2ZQ==; g_state={"i_l":0}; ndus=Yq09igCteHuiVxARw2R4sr89sO-TU_wTl0OCVFOT; ndut_fmt=FFA60E0AFB48D0AA60F91E8388B1F17A870E1F97E615851239A975DEEFF1ED4C; _ga_HSVH9T016H=GS2.1.s1747818780$o1$g1$t1747820218$j0$l0$h0'

def extract_surl_from_url(url: str) -> str | None:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])
    return surl[0] if surl else None

def find_between(data: str, first: str, last: str) -> str | None:
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return None

def get_data(url: str):
    r = requests.Session()
    headersList = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Connection": "keep-alive",
        "Cookie": COOKIE,
        "DNT": "1",
        "Host": "www.terabox.app",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    payload = ""
    response = r.get(url, data=payload, headers=headersList)
    response = r.get(response.url, data=payload, headers=headersList)
    logid = find_between(response.text, "dp-logid=", "&")
    jsToken = find_between(response.text, "fn%28%22", "%22%29")
    shorturl = extract_surl_from_url(response.url)
    
    if not shorturl:
        return None

    reqUrl = f"https://www.terabox.app/share/list?app_id=250528&web=1&channel=0&jsToken={jsToken}&dp-logid={logid}&page=1&num=20&by=name&order=asc&site_referer=&shorturl={shorturl}&root=1"

    response = r.get(reqUrl, data=payload, headers=headersList)

    if response.status_code != 200:
        return None

    r_j = response.json()
    if r_j.get("errno"):
        return None

    if "list" not in r_j or not r_j["list"]:
        return None

    file_info = r_j["list"][0]
    
    dlink = file_info.get("dlink")
    if not dlink:
        return None

    response = r.head(dlink, headers=headersList)
    direct_link = response.headers.get("location")
    
    data = {
        "file_name": file_info.get("server_filename", None),
        "download_link": dlink,
        "fast_link": direct_link,
        "thumb": file_info.get("thumbs", {}).get("url3", None),
        "sizebytes": int(file_info.get("size", 0)),
        "fs_id": file_info.get("fs_id", None),
        "shareid": r_j.get("share_id", None),
        "uk": r_j.get("uk", None)
    }
    return data

@app.route('/', methods=['GET'])
def api_get_data():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is missing"}), 400

    data = get_data(url)
    if not data:
        return jsonify({"error": "Failed to retrieve data"}), 500

    return jsonify(data), 200

@app.route('/status', methods=['GET'])
def api_status():
    return jsonify({"status": "OK"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4401, debug=True)
