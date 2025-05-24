from enum import Enum

from oc_images.image import Image
from oc_images.util import run


class CollectionType(Enum):
    PAYLOAD = 1
    IMAGESTREAM = 2


class ImageCollection:
    def __init__(self, pointer):
        self.pointer: str = pointer

        self._images = dict()
        self._type: CollectionType = None
        self._name: str = ""
        self._payload_info: dict() = {}
        self._is_info: dict() = {}
        self._is_coordinates: dict() = {}

    @property
    def type(self):
        if not self._type:
            self._type = self.determine_type()
        return self._type

    @property
    def name(self):
        if not self._name:
            if self.type == CollectionType.PAYLOAD:
                payload_info = self.payload_info
                self._name = payload_info["image"]
            elif self.type == CollectionType.IMAGESTREAM:
                is_info = self.is_info
                self._name = (
                    f"{is_info['metadata']['namespace']}/{is_info['metadata']['name']}"
                )
        return self._name

    def determine_type(self):
        if self.pointer.startswith("quay.io"):
            return CollectionType.PAYLOAD
        if self.pointer.startswith("registry.ci.openshift.org/ocp/release"):
            return CollectionType.PAYLOAD
        return CollectionType.IMAGESTREAM

    @property
    def images(self):
        if not self._images:
            if self.type == CollectionType.PAYLOAD:
                self._images = self.get_payload_images()
            elif self.type == CollectionType.IMAGESTREAM:
                self._images = self.get_is_images()
        return self._images

    def get_payload_images(self):
        images = dict()
        payload_info = self.payload_info
        for entry in payload_info["references"]["spec"]["tags"]:
            name = entry["name"]
            pullspec = entry["from"]["name"]
            commit = entry.get("annotations", {}).get(
                "io.openshift.build.commit.id", ""
            )
            repo = entry.get("annotations", {}).get(
                "io.openshift.build.source-location", ""
            )
            images.update(
                {name: Image(name=name, pullspec=pullspec, commit=commit, repo=repo)}
            )
        return images

    @property
    def payload_info(self):
        if not self._payload_info:
            cmd = ["oc", "adm", "release", "info", "-o", "json", self.pointer]
            self._payload_info = run(cmd)
        return self._payload_info

    @property
    def is_info(self):
        if not self._is_info:
            coordinates = self.is_coordinates
            cmd = ["oc", "--namespace", coordinates["namespace"]]
            cmd.extend(["get", "is", "--output", "json", coordinates["name"]])
            self._is_info = run(cmd)

        return self._is_info

    @property
    def is_coordinates(self):
        if not self._is_coordinates:
            name: str = ""
            namespace: str = ""
            split = self.pointer.split("/")
            if len(split) == 1:
                namespace = "ocp"
                name = self.pointer
            elif len(split) == 2:
                namespace = split[0]
                name = split[1]
            self._is_coordinates = {
                "namespace": namespace,
                "name": name,
            }
        return self._is_coordinates

    def get_is_images(self):
        images = dict()
        is_info = self.is_info
        for entry in is_info["status"]["tags"]:
            name = entry["tag"]
            pullspec = entry["items"][0]["dockerImageReference"]
            images.update({name: Image(name=name, pullspec=pullspec)})
        return images
