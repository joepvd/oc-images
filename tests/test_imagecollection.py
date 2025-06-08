import json
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest

pytest_plugins = ("pytest_asyncio",)

from oc_images.image import Image
from oc_images.imagecollection import (
    CollectionType,
    ImageCollection,
)

istream = CollectionType.IMAGESTREAM
payload = CollectionType.PAYLOAD


@pytest.mark.parametrize(
    ("name", "kind"),
    [
        ("quay.io/openshift-release-dev/ocp-release:4.20.0-ec.0-x86_64", payload),
        (
            "registry.ci.openshift.org/ocp/release:4.20.0-0.nightly-2025-05-24-021517",
            payload,
        ),
        ("4.5.6", istream),
        ("4.20-art-latest", istream),
        ("ocp/4.14-art-assembly-art123", istream),
        ("ocp-s390x/4.19-art-assembly-4.19.3-s390x", istream),
        ("4.16-art-assembly-4.16.0-rc.2-ppc64le", istream),
    ],
)
def test_determine_type(name, kind):
    assert ImageCollection(name).type == kind


@pytest.fixture
def payload_image():
    ic = ImageCollection("quay.io/openshift-release-dev/ocp-release:4.20.0-ec.0-x86_64")
    with open("tests/payload_data.json") as d:
        ic._payload_info = json.loads(d.read())
    return ic


@pytest.fixture
def imagestream():
    return ImageCollection("4.19-assembly-stream-art-latest")


@patch("oc_images.imagecollection.ImageCollection.get_payload_images")
@patch("oc_images.imagecollection.ImageCollection.get_is_images")
@pytest.mark.asyncio
async def test_images_p(get_is_images, get_payload_images, payload_image):
    await payload_image.images()
    get_payload_images.assert_called()
    get_is_images.assert_not_called()


@patch("oc_images.imagecollection.ImageCollection.get_payload_images")
@patch("oc_images.imagecollection.ImageCollection.get_is_images")
@pytest.mark.asyncio
async def test_images_i(get_is_images, get_payload_images, imagestream):
    await imagestream.images()
    get_payload_images.assert_not_called()
    get_is_images.assert_called()


@pytest.mark.asyncio
async def test_get_payload_images(payload_image):
    images = await payload_image.get_payload_images()
    assert "agent-installer-orchestrator" in images
    assert isinstance(images["ironic"], Image)
    assert images["oc-mirror"].commit


@pytest.mark.parametrize(
    ("collection", "isname"),
    [
        (
            "ocp-s390x/4.18-art-assembly-4.18.10-s390x",
            "ocp-s390x/4.18-art-assembly-4.18.10-s390x",
        ),
        ("4.18-rc.10", "ocp/4.18-art-assembly-rc.10"),
        ("4.19-rc.5", "ocp/4.19-art-assembly-rc.5"),
        ("4.19-art-latest", "ocp/4.19-art-latest"),
        ("4.19-art-latest-s390x", "ocp-s390x/4.19-art-latest-s390x"),
        ("4.17-art123", "ocp/4.17-art-assembly-art123"),
        ("4.19.3", "ocp/4.19-art-assembly-4.19.3"),
        ("4.12-art123", "ocp/4.12-art-assembly-art123"),
        ("4.16-stream", "ocp/4.16-art-latest"),
        ("4.20-nightly", "ocp/4.20-art-latest"),
        ("4.18-latest", "ocp/4.18-art-latest"),
    ],
)
def test_is_coordinates(collection, isname):
    ic = ImageCollection(collection)
    coordinates = ic.is_coordinates
    assert isname == f"{coordinates['namespace']}/{coordinates['name']}"
