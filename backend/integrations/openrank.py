import requests


OPENRANK_FID_SCORES_ENDPOINT = "https://graph.cast.k3l.io/scores/global/engagement/fids"


def get_openrank_score_for_fid(fid: int):
    response = requests.post(OPENRANK_FID_SCORES_ENDPOINT, json=[fid])
    if not response.ok:
        raise Exception(f"Failed to fetch OpenRank score for fid {fid}")
    data = response.json()
    result = data["result"]
    user_score = next((r for r in result if r["fid"] == fid), None)
    if not user_score:
        raise Exception(f"Failed to find score for fid {fid} in data {result}")
    return user_score
