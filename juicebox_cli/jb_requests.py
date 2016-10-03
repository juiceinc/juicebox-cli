from requests import Session
from requests.adapters import HTTPAdapter


jb_requests = Session()
jb_requests.mount('https://', HTTPAdapter(max_retries=5))
