NETRC_HOST_NAME = 'api.juiceboxdata.com'
PUBLIC_API_URL = 'https://api.juiceboxdata.com'
PUBLIC_API_URLS = {
    'prod': 'https://api.juiceboxdata.com',
    'nthriveprod': 'https://api.juiceboxdata.com',
    'dev': 'https://api-dev.juiceboxdata.com',
    'nthrivedev': 'https://api-dev.juiceboxdata.com',
}

CUSTOM_URL = None

def get_public_api(env=None):
    if CUSTOM_URL is not None:
        return CUSTOM_URL
    else:
        return PUBLIC_API_URL

