NETRC_HOST_NAME = 'api.juiceboxdata.com'
PUBLIC_API_URL = 'https://api.juiceboxdata.com'

CUSTOM_URL = None

def get_public_api():
    if CUSTOM_URL is not None:
        return CUSTOM_URL
    else:
        return PUBLIC_API_URL

