NETRC_HOST_NAME = "api-dev.juiceboxdata.com"
PUBLIC_API_URL = "https://api-dev.juiceboxdata.com"

# CUSTOM_URL = 'http://127.0.0.1:8000'
CUSTOM_URL = None


def get_public_api():
    return CUSTOM_URL if CUSTOM_URL is not None else PUBLIC_API_URL
