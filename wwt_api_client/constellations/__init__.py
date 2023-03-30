# Copyright 2023 the .NET Foundation
# Distributed under the MIT license

"""
Interacting with the WWT Constellations APIs.

"Constellations" (sometimes abbreviated "CX") is a modernized WWT web service
with a social-media-style interface. It includes an identity layer based on
`OpenID Connect`_ that Python-based tools can use to authenticate to the
Constellations APIs.

.. _OpenID Connect: https://openid.net/connect/

The client can connect to different instances of the backend API and
authentication service: the production environment (**which doesn't exist
yet**), the development environment, or a local testing instance. To make it so
that your code can choose which version to use on-the-fly, use the default
constructors and set the environment variable ``NUXT_PUBLIC_API_URL``. You'll
probably wish to use one of the following values:

- ``http://localhost:7000`` for a standard local testing environment, or
- ``https://api.wwtelescope.dev/`` for the development environment

"""

from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json
import os
from requests import RequestException, Response
from typing import List, Optional

from openidc_client import OpenIDCClient

__all__ = """
ClientConfig
CxClient
ImageStorage
ImageSummary
ImageWwt
""".split()


@dataclass
class ClientConfig:
    """
    Configuration settings for a WWT Constellations client.

    These influence which instance of the API the client actually connects to.
    """

    id_provider_url: str
    client_id: str
    api_url: str

    @classmethod
    def new_default(cls) -> "ClientConfig":
        """
        Create a new client configuration with sensible default settings.

        **Note!** Eventually this method will default to using the public,
        production WWT Constellations service. But since that doesn't exist, you
        currently must set *at least* the environment variable
        ``NUXT_PUBLIC_API_URL`` to indicate which service to use. The short
        advice for now is that you should almost definitely set
        ``NUXT_PUBLIC_API_URL`` to either ``http://localhost:7000`` or to
        ``https://api.wwtelescope.dev/``.

        The long version is that the "sensible default" settings are determined
        in the following way:

        - If the environment variable ``NUXT_PUBLIC_API_URL`` is set, its value
          used as the base URL for all API calls. (The name of this variable
          aligns with the one used by the Constellations frontend server.)
        - **Otherwise, an error is raised as mentioned above.**
        - If the environment variable ``NUXT_PUBLIC_KEYCLOAK_URL`` is set, its
          value used as the base URL for the authentication service.
        - Otherwise, if the environment variable ``KEYCLOAK_URL`` is set, its
          value is used.
        - Otherwise, if the base API URL contains the string ``localhost``, the
          value ``http://localhost:8080`` is used. This is the default used by
          the standard Keycloak Docker image.
        - Otherwise, if the base API URL contains the string
          ``wwtelescope.dev``, the value ``https://wwtelescope.dev/auth/`` is
          used. This is the setting for the WWT Constellations development
          environment.
        - Otherwise, an error is raised
        - The base API URL is normalized to *not* end in a slash
        - The base authentication URL is normalized *to* end in a slash; then
          the text ``realms/constellations`` is appended.
        - Finally, if the environment variable ``WWT_API_CLIENT_ID`` is set, its
          value is used to set the client ID.
        - Otherwise it defaults to ``cli-tool``.
        """

        api_url = os.environ.get("NUXT_PUBLIC_API_URL")
        client_id = os.environ.get("WWT_API_CLIENT_ID", "cli-tool")
        default_id_base = None

        if api_url is not None:
            if "localhost" in api_url:
                # localhost mode?
                default_id_base = "http://localhost:8080/"
            elif "wwtelescope.dev" in api_url:
                # dev mode?
                default_id_base = "https://wwtelescope.dev/auth/"
        else:
            # TODO: default to using the production API, once it exists!
            raise Exception(
                "until WWT Constellations is released, you must set the environment variable NUXT_PUBLIC_API_URL"
            )

        if api_url.endswith("/"):
            api_url = api_url[:-1]

        id_base = os.environ.get("NUXT_PUBLIC_KEYCLOAK_URL")
        if id_base is None:
            id_base = os.environ.get("KEYCLOAK_URL", default_id_base)
        if id_base is None:
            raise Exception(
                "unable to infer the WWT Constellations Keycloak URL; set the environment variable NUXT_PUBLIC_KEYCLOAK_URL"
            )

        if not id_base.endswith("/"):
            id_base += "/"

        return cls(
            id_provider_url=id_base + "realms/constellations",
            client_id=client_id,
            api_url=api_url,
        )

    @classmethod
    def new_dev(cls) -> "ClientConfig":
        """
        Create a new client configuration explicitly set up for the WWT
        Constellations development environment.

        You should probably use :meth:`new_default` unless you explicitly want
        your code to *always* refer to the development environment.
        """
        return cls(
            id_provider_url="https://wwtelescope.dev/auth/realms/constellations",
            client_id="cli-tool",
            api_url="https://api.wwtelescope.dev/",
        )


def _strip_nulls_in_place(d: dict):
    """
    Remove None values a dictionary and its sub-dictionaries.

    For the backend APIs, our convention is to have values be missing entirely
    rather than nulls; that's more future-proof if/when we add new fields to
    things.

    Returns the input for convenience.
    """

    keys_to_remove = []

    for key, val in d.items():
        if isinstance(val, dict):
            _strip_nulls_in_place(val)
        elif val is None:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del d[key]

    return d


@dataclass_json
@dataclass
class ImageWwt:
    """A description of the WWT data parameters associated with a Constellations image."""

    base_degrees_per_tile: float
    bottoms_up: bool
    center_x: float
    center_y: float
    file_type: str
    projection: str
    quad_tree_map: str
    rotation: float
    tile_levels: int
    width_factor: int
    thumbnail_url: str


@dataclass_json
@dataclass
class ImageStorage:
    """A description of data storage associated with a Constellations image."""

    legacy_url_template: Optional[str]


@dataclass_json
@dataclass
class ImageSummary:
    """Summary information about a Constellations image."""

    id: str = field(metadata=config(field_name="_id"))  # 24 hex digits
    handle_id: str  # 24 hex digits
    creation_date: str  # format: 2023-03-28T16:53:18.364Z'
    note: str
    storage: ImageStorage


@dataclass_json
@dataclass
class FindImagesByLegacyRequest:
    wwt_legacy_url: str


@dataclass_json
@dataclass
class FindImagesByLegacyResponse:
    error: bool
    results: List[ImageSummary]


# I think this is unlikely to ever need to be configurable?
_ID_PROVIDER_MAPPING = {
    "Authorization": "/protocol/openid-connect/auth",
    "Token": "/protocol/openid-connect/token",
}


class CxClient:
    """
    A client for the WWT Constellations APIs.

    This client authenticates automatically using OpenID Connect protocols. API
    calls may cause it to print a URL to the terminal, requesting that the user
    visit it to navigate a login flow.

    Parameters
    ----------
    config : optional :class:`ClientConfig`
        If specified, the client configuration to use. Defaults to calling
        :meth:`ClientConfig.new_default`.
    oidcc_cache_identifier: optional :class:`str`
        The identifier to use for caching this client's state in the
        ``openidc_client`` cache. Defaults to ``"wwt_api_client"``. You are
        unlikely to need to change this setting.
    """

    _config: ClientConfig
    _oidcc: OpenIDCClient

    def __init__(
        self,
        config: Optional[ClientConfig] = None,
        oidcc_cache_identifier: Optional[str] = "wwt_api_client",
    ):
        if config is None:
            config = ClientConfig.new_default()

        self._config = config
        self._oidcc = OpenIDCClient(
            oidcc_cache_identifier,
            config.id_provider_url,
            _ID_PROVIDER_MAPPING,
            config.client_id,
        )

    def _send_and_check(
        self, rel_url: str, scopes=["profile", "offline_access"], **kwargs
    ) -> Response:
        resp = self._oidcc.send_request(
            self._config.api_url + rel_url,
            new_token=True,
            scopes=scopes,
            **kwargs,
        )

        try:
            resp.raise_for_status()
        except RequestException as e:
            # digest the response into the message
            e.args = (f"{e}: {e.response.text}",)
            raise

        return resp

    def handle_client(self, handle: str) -> "handles.HandleClient":
        """
        Return a client class for making API calls specific to the given handle.

        Parameters
        ----------
        handle : :class:`str`
            The handle in question

        Returns
        -------
        :class:`handles.HandleClient`
        """
        from .handles import HandleClient

        return HandleClient(self, handle)

    def find_images_by_wwt_url(self, wwt_url: str) -> List[ImageSummary]:
        """
        Find images in the database associated with a particular "legacy" WWT
        data URL.

        This method corresponds to the
        :ref:`endpoint-GET-images-find-by-legacy-url` API endpoint.
        """
        req = FindImagesByLegacyRequest(wwt_legacy_url=wwt_url)
        resp = self._send_and_check(
            "/images/find-by-legacy-url", json=_strip_nulls_in_place(req.to_dict())
        )
        resp = FindImagesByLegacyResponse.schema().load(resp.json())
        return resp.results