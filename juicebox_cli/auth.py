# In juicebox_cli/auth.py

"""Checks and gets authentication for juicebox_cli"""
import json
import netrc
import os
import stat
import jwt

from juicebox_cli.config import get_public_api, NETRC_HOST_NAME
from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.logger import logger
from juicebox_cli.jb_requests import jb_requests


class JuiceBoxAuthenticator:
    token = None

    def __init__(
        self, username=None, password=None, endpoint=None, netrc_location=None
    ):
        self.endpoint = endpoint
        logger.debug("Initializing JBAuth via netrc")
        try:
            if netrc_location:
                logger.debug("Using user defined netrc_file %s", netrc_location)
                self.netrc_proxy = netrc.netrc(netrc_location)
            elif os.name == "nt":
                logger.debug("Trying to use Windows _netrc")
                home = os.path.expanduser("~")
                netrc_file = os.path.join(home, "_netrc")
                self.netrc_proxy = netrc.netrc(netrc_file)
            else:
                self.netrc_proxy = netrc.netrc()
        except Exception as exc_info:
            if netrc_location:
                logger.debug(str(exc_info))
                raise ValueError(
                    "Could not read token from %s", netrc_location
                ) from exc_info
            netrc_filename = "_netrc" if os.name == "nt" else ".netrc"
            home = os.path.expanduser("~")
            netrc_file = os.path.join(home, netrc_filename)
            # Ensure the file is created if it doesn't exist to prevent FileNotFoundError on subsequent netrc.netrc()
            open(
                netrc_file, "a"
            ).close()  # Use 'a' to create if not exists, without truncating
            if os.name != "nt":
                os.chmod(
                    netrc_file, stat.S_IREAD | stat.S_IWRITE
                )  # Set permissions if not Windows
            self.netrc_proxy = netrc.netrc(netrc_file)  # Re-initialize after creation

        self.username = username
        self.password = password
        self.client_id = None

    def is_auth_preped(self):
        logger.debug("Checking for JB token")
        if self.token:
            logger.debug("Found JB Token")
            if self.client_id:
                return True
            try:
                decoded_token = jwt.decode(
                    self.token, options={"verify_signature": False}
                )
                self.client_id = decoded_token.get("client")
                logger.debug(
                    f"Extracted client ID from pre-existing token: {self.client_id}"
                )
                return True if self.client_id else False
            except jwt.DecodeError as e:
                logger.warning(f"Could not decode pre-existing JWT token: {e}")
                return False

        username, token = self.get_netrc_token()
        if username and token:
            self.username = username
            self.token = token
            try:
                decoded_token = jwt.decode(
                    self.token, options={"verify_signature": False}
                )
                self.client_id = decoded_token.get("client")
                logger.debug(f"Extracted client ID from netrc token: {self.client_id}")
                return True if self.client_id else False
            except jwt.DecodeError as e:
                logger.warning(f"Could not decode JWT token from netrc: {e}")
                return False
        logger.debug("No JB token found")
        return False

    def get_juicebox_token(
        self, username: str, password: str, endpoint: str, save: bool = False
    ):  # save=False is default
        logger.debug("Getting JB token from Public API")
        url = f"{get_public_api()}/token"

        data_payload = {
            "username": username,
            "password": password,
            "env": "prod",  # Assuming 'prod' by default, can be dynamically set if needed
            "endpoint": endpoint,
        }

        headers = {"content-type": "application/json"}

        response = jb_requests.post(url, data=json.dumps(data_payload), headers=headers)
        if response.status_code != 200:
            logger.debug(response)
            raise AuthenticationError(
                f"I was unable to authenticate you with "
                f"those credentials. Server response: {response.text}"
            )

        token = response.json()["data"]["token"]

        self.username = username  # Update self.username after successful login
        self.token = token

        try:
            decoded_token = jwt.decode(self.token, options={"verify_signature": False})
            self.client_id = decoded_token.get("client")
            logger.debug(
                f"Extracted client ID from newly obtained token: {self.client_id}"
            )
        except jwt.DecodeError as e:
            logger.warning(f"Could not decode newly obtained JWT token: {e}")
            self.client_id = None

        logger.debug("Successfully retrieved JB token")

        if save:
            logger.debug("Saving token to netrc")
            self.update_netrc()
        return self.token  # Return the token

    def get_netrc_token(self):
        """Pulls token from netrc file"""
        logger.debug("Checking for JB token in netrc")
        if auth := self.netrc_proxy.authenticators(NETRC_HOST_NAME):
            logger.debug("Found JB Token in netrc")
            login, _, token = auth
            return login, token
        logger.debug("No JB Token in netrc")
        return None, None

    def update_netrc(self):
        """Updates JB record in netrc file"""
        output_lines = []

        netrc_os_file = os.path.expanduser("~/.netrc")
        if os.name == "nt":
            logger.debug("WINDOWS!")
            home = os.path.expanduser("~")
            netrc_os_file = os.path.join(home, "_netrc")

        # Read existing netrc content, excluding our specific machine's entry if it exists
        if os.path.exists(netrc_os_file):
            with open(netrc_os_file, "r") as netrc_file:
                skip_existing_block = False
                for line in netrc_file.readlines():
                    if (
                        f"machine {NETRC_HOST_NAME}" in line
                    ):  # Check for the specific machine name
                        logger.debug(f"Found start of our entry for {NETRC_HOST_NAME}")
                        skip_existing_block = True
                    elif skip_existing_block and (
                        "login " in line or "password " in line
                    ):
                        pass  # Skip these lines if part of our entry
                    elif skip_existing_block and line.strip() == "":
                        skip_existing_block = False
                    elif (
                        skip_existing_block
                    ):  # Other lines within our entry that might need skipping
                        pass
                    else:
                        output_lines.append(line)

        # Ensure the file ends with a newline if it's not empty
        if output_lines and not output_lines[-1].endswith("\n"):
            output_lines[-1] += "\n"

        logger.debug("Building JB entry")
        output_lines.append(f"machine {NETRC_HOST_NAME}\n")  # <--- Use NETRC_HOST_NAME
        output_lines.append(f"  login {self.username}\n")
        output_lines.append(
            f"  password {self.token}\n"
        )  # Storing JWT token as 'password' for netrc compatibility

        logger.debug("Writing new netrc")
        try:
            with open(netrc_os_file, "w") as netrc_file:
                netrc_file.writelines(output_lines)
            if os.name != "nt":  # Set permissions only on non-Windows
                os.chmod(
                    netrc_os_file, stat.S_IREAD | stat.S_IWRITE
                )  # Read/write for owner only
            logger.debug("Successfully updated netrc")
        except Exception as e:
            logger.error(f"Error writing to netrc file {netrc_os_file}: {e}")
            raise AuthenticationError(f"Failed to save token to netrc: {e}")
