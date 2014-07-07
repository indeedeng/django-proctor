import logging
import socket

import requests

logger = logging.getLogger('application')


def call_proctor(api_root, context_dict, identifier_dict,
        test_filter=None, force_groups=None, timeout=1.0):
    """
    Make an HTTP request to the Proctor REST API /groups/identify endpoint.

    Return the JSON API response or None if there was an error.

    api_root: The root URL of the Proctor API. No trailing slash.
    context_dict: Context variable source keys and their values.
    identifier_dict: Identifier source keys and their values.
    test_filter: List of test names to filter by. (default: no filter)
    force_groups: prforceGroups string (from query param or cookie).
    timeout: Timeout of the HTTP request in seconds. (default: 1.0 seconds)
        If None, requests will attempt the request forever.
        For network unreachable errors, requests inexplicably takes ~20x this
        value before returning.

    A timeout is important to ensure your web backend does not block on
    Proctor API calls forever if the API's performance severely degrades or
    starts hanging on all HTTP requests for some reason.
    """

    api_url = "{root}/groups/identify".format(root=api_root)

    params = {}
    # Context variables and identifiers need prefixes.
    params.update(('ctx.' + key, value)
        for key, value in context_dict.iteritems())
    params.update(('id.' + key, value)
        for key, value in identifier_dict.iteritems())

    # test is a comma-separated list of test names.
    if test_filter:
        params['test'] = ','.join(test_filter)
    if force_groups:
        params['prforceGroups'] = force_groups

    try:
        response = requests.get(api_url, params=params, timeout=timeout)

    # Handle all possible errors.
    # This may be running in production, and Proctor is not critical,
    # so we can log the error and fall back to default behavior.

    # socket.timeout is occasionally thrown instead of request's Timeout.
    except (requests.exceptions.Timeout, socket.timeout):
        logger.exception("Proctor API request to %s timed out.", api_url)
        return None
    except requests.exceptions.ConnectionError:
        logger.exception("Proctor API request to %s had a connection error.",
            api_url)
        return None
    # All other Requests exceptions
    except requests.exceptions.RequestException:
        logger.exception("Proctor API request to %s threw an exception.",
            api_url)
        return None

    if response.status_code != requests.codes.ok:
        # API errors may have additional JSON metadata.
        try:
            error_message = response.json()['meta']['error']
            logger.error("Proctor API at %s returned HTTP error (%d: %s) "
                "with API error message: %s",
                api_url, response.status_code, response.reason, error_message)
            return None
        # Response has no valid JSON. Maybe the HTTP server gave this error.
        except ValueError:
            logger.error("Proctor API at %s returned HTTP error (%d: %s)",
                api_url, response.status_code, response.reason)
            return None
        # Response had JSON, but it didn't use the envelope format.
        # The Proctor REST API should never cause this.
        except KeyError:
            logger.error("Proctor API at %s returned HTTP error (%d: %s) "
                "and JSON with missing error message.",
                api_url, response.status_code, response.reason)
            return None

    try:
        api_response = response.json()
    except ValueError:
        logger.exception("Proctor API at %s returned invalid JSON: %s",
            api_url, response.text)
        return None

    # The Proctor REST API should never return 200 without groups.
    if 'data' not in api_response or 'groups' not in api_response['data']:
        logger.error(
            "Proctor API at %s returned JSON with missing groups field: %s",
            api_url, api_response)
        return None

    # No error conditions detected.
    return api_response
