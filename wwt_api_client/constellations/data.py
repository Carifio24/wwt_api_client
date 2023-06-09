# Copyright 2023 the .NET Foundation
# Distributed under the MIT license

"""
Data classes for WWT Constellations APIs.
"""

from typing import List, Optional

from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from html_sanitizer.sanitizer import Sanitizer, DEFAULT_SETTINGS
from license_expression import get_spdx_licensing, ExpressionError

__all__ = """
HandleImageStats
HandleInfo
HandlePermissions
HandleSceneStats
HandleStats
HandleUpdate
ImageApiPermissions
ImageContentPermissions
ImageInfo
ImageDisplayInfo
ImageStorage
ImageSummary
ImageUpdate
ImageWwt
SceneContent
SceneContentHydrated
SceneHydrated
SceneImageLayer
SceneImageLayerHydrated
SceneInfo
ScenePermissions
ScenePlace
ScenePreviews
SceneUpdate
""".split()


CX_LICENSING = get_spdx_licensing()
CX_SANITIZER_SETTINGS = DEFAULT_SETTINGS.copy()
CX_SANITIZER_SETTINGS.update(
    tags={"b", "strong", "i", "em", "a", "br"}, empty={}, separate={}
)
CX_SANITIZER = Sanitizer(settings=CX_SANITIZER_SETTINGS)


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
class HandleInfo:
    handle: str
    display_name: str


@dataclass_json
@dataclass
class HandlePermissions:
    handle: str
    view_dashboard: bool


@dataclass_json
@dataclass
class HandleUpdate:
    display_name: Optional[str] = None


@dataclass_json
@dataclass
class HandleImageStats:
    count: int


@dataclass_json
@dataclass
class HandleSceneStats:
    count: int
    impressions: int
    likes: int


@dataclass_json
@dataclass
class HandleStats:
    handle: str
    images: HandleImageStats
    scenes: HandleSceneStats


@dataclass_json
@dataclass
class ImageWwt:
    """A description of the WWT data parameters associated with a Constellations image."""

    base_degrees_per_tile: float
    bottoms_up: bool
    center_x: float
    center_y: float
    file_type: str
    offset_x: float
    offset_y: float
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

    legacy_url_template: Optional[str] = None


@dataclass_json
@dataclass
class ImageSummary:
    """Summary information about a Constellations image."""

    id: str = field(metadata=config(field_name="_id"))  # 24 hex digits
    handle_id: str  # 24 hex digits
    creation_date: str  # format: 2023-03-28T16:53:18.364Z
    note: str
    storage: ImageStorage


@dataclass_json
@dataclass
class ImageContentPermissions:
    copyright: str
    credits: Optional[str]
    license: str

    def __post_init__(self):
        license_info = CX_LICENSING.validate(self.license, strict=True)
        if license_info.errors:
            msg = "\n".join(license_info.errors)
            raise ExpressionError(f"Invalid SPDX license:\n{msg}")
        if self.credits:
            self.credits = CX_SANITIZER.sanitize(self.credits)


@dataclass_json
@dataclass
class ImageDisplayInfo:
    wwt: ImageWwt
    storage: ImageStorage


@dataclass_json
@dataclass
class ImageInfo:
    """Note that this class is *not* what is returned by the
    ``/handle/:handle/imageinfo`` endpoint. That returns a
    :class:`ImageSummary`."""

    id: str  # 24 hex digits
    handle_id: str  # 24 hex digits
    handle: HandleInfo
    creation_date: str  # format: 2023-03-28T16:53:18.364Z
    wwt: ImageWwt
    permissions: ImageContentPermissions
    storage: ImageStorage
    note: str


@dataclass_json
@dataclass
class ImageUpdate:
    note: Optional[str] = None
    permissions: Optional[ImageContentPermissions] = None


@dataclass_json
@dataclass
class ImageApiPermissions:
    id: str
    edit: bool


@dataclass_json
@dataclass
class ScenePlace:
    ra_rad: float
    dec_rad: float
    roll_rad: float
    roi_height_deg: float
    roi_aspect_ratio: float


@dataclass_json
@dataclass
class SceneImageLayer:
    image_id: str
    opacity: float


@dataclass_json
@dataclass
class SceneContent:
    image_layers: Optional[List[SceneImageLayer]] = None


@dataclass_json
@dataclass
class SceneImageLayerHydrated:
    image: ImageDisplayInfo
    opacity: float


@dataclass_json
@dataclass
class SceneContentHydrated:
    background: Optional[ImageDisplayInfo] = None
    image_layers: Optional[List[SceneImageLayerHydrated]] = None


@dataclass_json
@dataclass
class ScenePreviews:
    video: Optional[str] = None
    thumbnail: Optional[str] = None


@dataclass_json
@dataclass
class SceneHydrated:
    id: str
    handle_id: str
    handle: HandleInfo
    creation_date: str
    likes: int
    place: ScenePlace
    content: SceneContentHydrated
    text: str
    previews: ScenePreviews


@dataclass_json
@dataclass
class SceneInfo:
    _id: str
    creation_date: str
    impressions: int
    likes: int


@dataclass_json
@dataclass
class ScenePermissions:
    id: str
    edit: bool


@dataclass_json
@dataclass
class SceneUpdate:
    outgoing_url: Optional[str]
    place: Optional[ScenePlace]
    text: Optional[str]
