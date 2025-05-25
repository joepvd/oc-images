import re
from enum import Enum

from oc_images.image import Image
from oc_images.util import run


class CollectionType(Enum):
    PAYLOAD = 1
    IMAGESTREAM = 2


def assembly_to_imagestream(assembly):
    components = [
        re.search(r"^[0-9]+\.[0-9]+", assembly)[0],
        "art",
        "latest" if "stream" in assembly else "assembly",
    ]
    if "stream" not in assembly:
        name = assembly
        if result := re.search(r"art[0-9]+$", assembly):
            name = result[0]
        components.append(name)
    return f"ocp/{'-'.join(components)}"


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
            if self.pointer.startswith("quay.io"):
                self._type = CollectionType.PAYLOAD
            elif self.pointer.startswith("registry.ci.openshift.org/ocp/release"):
                self._type = CollectionType.PAYLOAD
            else:
                self._type = CollectionType.IMAGESTREAM
        return self._type

    async def name(self):
        if not self._name:
            if self.type == CollectionType.PAYLOAD:
                payload_info = await self.payload_info()
                self._name = payload_info["image"]
            elif self.type == CollectionType.IMAGESTREAM:
                is_info = await self.is_info()
                self._name = (
                    f"{is_info['metadata']['namespace']}/{is_info['metadata']['name']}"
                )
        return self._name

    async def images(self):
        if not self._images:
            if self.type == CollectionType.PAYLOAD:
                self._images = await self.get_payload_images()
            elif self.type == CollectionType.IMAGESTREAM:
                self._images = await self.get_is_images()
        return self._images

    async def get_payload_images(self):
        images = dict()
        payload_info = await self.payload_info()
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

    async def payload_info(self):
        if not self._payload_info:
            cmd = ["oc", "adm", "release", "info", "-o", "json", self.pointer]
            self._payload_info = await run(cmd)
        return self._payload_info

    async def is_info(self):
        if not self._is_info:
            coordinates = self.is_coordinates
            cmd = ["oc", "--namespace", coordinates["namespace"]]
            cmd.extend(["get", "is", "--output", "json", coordinates["name"]])
            self._is_info = await run(cmd)

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

    async def get_is_images(self):
        images = dict()
        is_info = await self.is_info()
        for entry in is_info["status"]["tags"]:
            name = entry["tag"]
            pullspec = entry["items"][0]["dockerImageReference"]
            images.update({name: Image(name=name, pullspec=pullspec)})
        return images
