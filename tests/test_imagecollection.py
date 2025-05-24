from oc_images.imagecollection import ImageCollection, CollectionType
from oc_images.image import Image

import pytest
import json
from unittest import mock
from unittest.mock import patch, Mock, MagicMock


istream = CollectionType.IMAGESTREAM
payload = CollectionType.PAYLOAD

@pytest.mark.parametrize(("name", "kind"), [
    ('quay.io/openshift-release-dev/ocp-release:4.20.0-ec.0-x86_64', payload),
    ('registry.ci.openshift.org/ocp/release:4.20.0-0.nightly-2025-05-24-021517', payload),
])
def test_determine_type(name, kind):
    assert ImageCollection(name).determine_type() == kind


@pytest.fixture
def payload_image():
    ic = ImageCollection('quay.io/openshift-release-dev/ocp-release:4.20.0-ec.0-x86_64')
    with open('tests/payload_data.json') as d:
        ic._payload_info = json.loads(d.read())
    return ic

@pytest.fixture
def imagestream():
    return ImageCollection('4.19-assembly-stream-art-latest')

@patch('oc_images.imagecollection.ImageCollection.get_payload_images')
@patch('oc_images.imagecollection.ImageCollection.get_is_images')
def test_images_p(get_is_images, get_payload_images, payload_image):
    payload_image.images
    get_payload_images.assert_called()
    get_is_images.assert_not_called()

@patch('oc_images.imagecollection.ImageCollection.get_payload_images')
@patch('oc_images.imagecollection.ImageCollection.get_is_images')
def test_images_i(get_is_images, get_payload_images, imagestream):
    imagestream.images
    get_payload_images.assert_not_called()
    get_is_images.assert_called()

def test_get_payload_images(payload_image):
    images = payload_image.get_payload_images()
    assert 'agent-installer-orchestrator' in images
    assert isinstance(images['ironic'], Image)
    assert images['oc-mirror'].commit

@pytest.mark.parametrize(("imagestream", "namespace", "name"), [
    ('ocp-s390x/4.18-art-assembly-4.18.10-s390x', 'ocp-s390x', '4.18-art-assembly-4.18.10-s390x'),
    ('ocp-s390x/4.18.0-rc.10', 'ocp-s390x', '4.18.0-rc.10'),
    ('4.18.0-rc.10', 'ocp', '4.18.0-rc.10'),
])
def test_is_coordinates(imagestream, namespace, name):
    ic = ImageCollection(imagestream)
    coordinates = ic.is_coordinates
    assert coordinates['name'] == name
    assert coordinates['namespace'] == namespace
