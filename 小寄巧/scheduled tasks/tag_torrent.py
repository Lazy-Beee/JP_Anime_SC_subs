import requests
import logging
from urllib.parse import urljoin

QB_URL = ""
USERNAME = ""
PASSWORD = ""

TRACKER_TO_TAG_MAP = {
    "tracker url": "tag"
}

SAVEPATH_TO_CATEGORY_MAP = {
    "save path": "category"
}

logger = logging.getLogger(__name__)

def tag_torrent(enable_logging=False):
    """
    Connects to qBittorrent via Web API using 'requests' library,
    then tags and categorizes torrents.
    """

    logger.handlers.clear()

    if enable_logging:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.propagate = False
    else:
        logger.addHandler(logging.NullHandler())
        logger.propagate = False

    base_url = f"{QB_URL}/api/v2/"
    session = requests.Session()

    def _api_call(method, endpoint, params=None, data=None, expected_statuses=(200,)):
        """Makes an API call and handles basic error checking."""
        url = urljoin(base_url, endpoint)
        try:
            response = session.request(method, url, params=params, data=data)
            if response.status_code not in expected_statuses:
                logger.error(
                    f"API call to {endpoint} failed with status {response.status_code}: {response.text}"
                )
                return None
            if response.headers.get('Content-Type', '').startswith('text/plain'):
                return response.text.strip()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {endpoint} failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to decode JSON response from {endpoint}: {e}. Response text: {response.text[:200]}")
            return None


    logger.info(f"Starting qBittorrent auto-tag/category process for {QB_URL}...")

    login_payload = {'username': USERNAME, 'password': PASSWORD}
    logger.info(f"Attempting to login with username: '{USERNAME if USERNAME else '<empty>'}'...")
    login_response_text = _api_call('POST', 'auth/login', data=login_payload)

    if login_response_text != "Ok.":
        logger.error(f"qBittorrent login failed. Response: {login_response_text}. Please check credentials and WebUI settings.")
        return False

    logger.info("Successfully logged in to qBittorrent.")

    try:
        app_version = _api_call('GET', 'app/version')
        api_version = _api_call('GET', 'app/webapiVersion')
        if app_version: logger.info(f"qBittorrent Version: {app_version}")
        if api_version: logger.info(f"qBittorrent API Version: {api_version}")

        logger.info("Fetching torrent list...")
        torrents = _api_call('GET', 'torrents/info')
        if torrents is None:
            logger.error("Failed to retrieve torrents list.")
            return False
        if not torrents:
            logger.info("No torrents found in the client.")
            return True

        logger.info(f"Found {len(torrents)} torrents. Starting processing...")
        processed_count = 0
        tagged_count = 0
        categorized_count = 0

        for torrent in torrents:
            torrent_name = torrent.get('name', 'N/A')
            torrent_hash = torrent.get('hash')

            if not torrent_hash:
                logger.warning(f"Skipping torrent with no hash: {torrent_name}")
                continue

            logger.debug(f"Processing torrent: {torrent_name} (Hash: {torrent_hash})")

            current_tags = torrent.get('tags', '')
            if not current_tags:
                logger.debug(f"Torrent '{torrent_name}' has no tags. Checking trackers...")
                trackers_info = _api_call('GET', 'torrents/trackers', params={'hash': torrent_hash})
                applied_tag_this_torrent = False
                if trackers_info:
                    for tracker_entry in trackers_info:
                        tracker_url = tracker_entry.get('url', '').lower()
                        for keyword, tag_to_apply in TRACKER_TO_TAG_MAP.items():
                            if keyword.lower() in tracker_url:
                                logger.info(f"Match found for tag: keyword '{keyword}' in tracker '{tracker_url}' for '{torrent_name}'. Applying tag '{tag_to_apply}'.")
                                add_tags_payload = {'hashes': torrent_hash, 'tags': tag_to_apply}
                                if _api_call('POST', 'torrents/addTags', data=add_tags_payload) is not None:
                                    logger.info(f"Tagged '{torrent_name}' with '{tag_to_apply}' (tracker: {tracker_entry.get('url')})")
                                    tagged_count += 1
                                    applied_tag_this_torrent = True
                                else:
                                    logger.error(f"Failed to tag '{torrent_name}' with '{tag_to_apply}'.")
                                break
                        if applied_tag_this_torrent:
                            break
                if not applied_tag_this_torrent:
                    logger.debug(f"No matching tracker keyword found for '{torrent_name}' to apply a tag.")
            else:
                logger.debug(f"Torrent '{torrent_name}' already has tags: {current_tags}. Skipping tagging.")

            current_category = torrent.get('category', '')
            if not current_category:
                save_path = torrent.get('save_path', '')
                logger.debug(f"Torrent '{torrent_name}' has no category. Save path: {save_path}")
                applied_category_this_torrent = False
                for keyword, category_to_apply in SAVEPATH_TO_CATEGORY_MAP.items():
                    if keyword.lower() in save_path.lower():
                        logger.info(f"Match found for category: keyword '{keyword}' in save path '{save_path}' for '{torrent_name}'. Applying category '{category_to_apply}'.")
                        set_category_payload = {'hashes': torrent_hash, 'category': category_to_apply}
                        if _api_call('POST', 'torrents/setCategory', data=set_category_payload) is not None:
                            logger.info(f"Categorized '{torrent_name}' as '{category_to_apply}' (save path: {save_path})")
                            categorized_count += 1
                            applied_category_this_torrent = True
                        else:
                            logger.error(f"Failed to categorize '{torrent_name}' as '{category_to_apply}'.")
                        break
                if not applied_category_this_torrent:
                    logger.debug(f"No matching save path keyword found for '{torrent_name}' to apply a category.")
            else:
                logger.debug(f"Torrent '{torrent_name}' already has category: {current_category}. Skipping categorization.")
            processed_count += 1

        logger.info("--- Processing Complete ---")
        logger.info(f"Total torrents checked: {len(torrents)}")
        logger.info(f"Torrents processed (attempted tag/category): {processed_count}")
        logger.info(f"Torrents newly tagged: {tagged_count}")
        logger.info(f"Torrents newly categorized: {categorized_count}")
        return True

    except Exception as e:
        logger.error(f"An unexpected error occurred during torrent processing: {e}", exc_info=True)
        return False
    finally:
        logger.info("Attempting to logout...")
        logout_response = _api_call('POST', 'auth/logout')
        if logout_response is not None: # Successful call, qBittorrent might return empty 200 OK or text
             logger.info("Successfully logged out from qBittorrent or logout command sent.")
        else:
            logger.warning("Logout command failed or could not confirm logout.")
        session.close()
        logger.info("Session closed. Script finished.")

if __name__ == "__main__":
    tag_torrent(True)
