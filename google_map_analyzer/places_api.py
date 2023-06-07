import json
import concurrent.futures
from tqdm import tqdm
import time
from typing import List, Optional
from .crawl import find_social_links

import requests

from .logger import log
from .settings import API_KEY

PLACES_API_ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GEOCODE_API_ENDPOINT = "https://maps.googleapis.com/maps/api/geocode/json"
NEARBY_API_ENDPOINT = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACE_DETAIL_ENDPOINT = "https://maps.googleapis.com/maps/api/place/details/json"


def get_location(place: str) -> List[str]:
    log.debug(f"Place is {place}.")
    params = {
        "address": place,
        "key": API_KEY,
        "region": "jp",
        "language": "ja",
    }
    res = requests.get(GEOCODE_API_ENDPOINT, params=params)
    res_json = json.loads(res.text)
    location = None
    if 0 < len(res_json["results"]):
        location_dict = res_json["results"][0]["geometry"]["location"]
        location = [str(location_dict["lat"]), str(location_dict["lng"])]
    return location


def get_nearby_places(
    keyword: str,
    location: str,
    radius: int,
    limit: int,
    _type: str = "food",
):
    log.debug(f"Searching for {keyword}. location={location}")
    next_page_token = None
    params = {
        "location": ",".join(location),
        "keyword": keyword,
        "radius": radius,
        "language": "ja",
        "type": _type,  # types: https://developers.google.com/maps/documentation/places/web-service/supported_types
        "key": API_KEY,
    }
    results = []
    for i in range(limit):
        log.debug(f"[*] page={i}")
        res = requests.get(NEARBY_API_ENDPOINT, params=params)
        res_json = json.loads(res.text)

        next_page_token = res_json.get("next_page_token", None)
        params = {"key": API_KEY, "pagetoken": next_page_token}

        results.extend(res_json["results"])
        log.debug(f"len={len(results)}")
        if next_page_token is None:
            break
        time.sleep(2)
    return results


def add_google_map_url(results: list) -> list:
    log.debug(f"Adding google map url... ({len(results)})")
    for result in results:
        result[
            "google_map_url"
        ] = f"https://www.google.com/maps/place/?q=place_id:{result['place_id']}"
    return results


def add_detail_to_result(result: dict) -> dict:
    try:
        place_id = result["place_id"]
        details = get_place_details(place_id)
        result["details"] = details
    except Exception as e:
        log.error(e)
        result["details"] = {}
    return result


def add_details(results: list) -> list:
    log.debug(f"Adding details ... ({len(results)})")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(
            tqdm(
                executor.map(add_detail_to_result, results),
                total=len(results),
                desc="details",
            )
        )
    return results


def find_sns_for_result(result: dict) -> dict:
    try:
        website = result["details"]["result"]["website"]
        sns_urls = find_social_links(website)
        result["sns"] = sns_urls
    except Exception as e:
        log.error(e)
        result["sns"] = []
    return result


def add_sns(results: list) -> list:
    log.debug(f"Adding sns ... ({len(results)})")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(
            tqdm(
                executor.map(find_sns_for_result, results),
                total=len(results),
                desc="sns",
            )
        )
    return results


def get_place_details(place_id):
    # Place DetailsリクエストのURL

    # パラメータ
    params = {
        "placeid": place_id,
        "fields": "name,rating,formatted_phone_number,website",
        "key": API_KEY,
    }

    # リクエストの実行
    res = requests.get(PLACE_DETAIL_ENDPOINT, params=params)

    # レスポンスのJSONをデコード
    place_details = json.loads(res.text)

    return place_details


def extract_info_from_results(results):
    new_results = []
    for result in results:
        if len(result["sns"]) == 0:
            continue
        new_results.append(
            {
                "name": result["name"],
                "google_map_url": result["google_map_url"],
                "sns": result["sns"],
                "details": result["details"],
            }
        )
    return new_results


def run_search_api(keyword: str, place: str, radius=800, limit=3, _type="food") -> list:
    # 徒歩圏内が10~15分圏内だとすると、800~1200m

    """
    Geocode API
    """
    location = get_location(place=place)

    """
    Places API
    """
    results = get_nearby_places(
        keyword=keyword, location=location, radius=radius, limit=limit, _type=_type
    )
    """
    googlemapを追加
    """
    results = add_google_map_url(results)

    """
    Detailsを追加
    """
    results = add_details(results)

    """
    snsを追加
    """
    results = add_sns(results)
    # 確認
    if 0 < len(results):
        log.debug(f"sample[0]=\n{results[0]}")

    return results


if __name__ == "__main__":
    from pprint import pprint
    from place_type import PlaceType

    results = run_search_api(keyword="カフェ", place="道玄坂", limit=1, _type=PlaceType.CAFE)
    results = extract_info_from_results(results[:10])

    pprint(results)
