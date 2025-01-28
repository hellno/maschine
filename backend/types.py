from typing import Optional, TypedDict


class UserContext(TypedDict):
    fid: int
    username: Optional[str]
    displayName: Optional[str]
    pfpUrl: Optional[str]
    location: Optional[dict]
