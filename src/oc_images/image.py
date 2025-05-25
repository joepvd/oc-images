from oc_images.util import run


class Image:
    def __init__(
        self, name: str = "", pullspec: str = "", commit: str = "", repo: str = ""
    ):
        self.name = name
        self.pullspec = pullspec
        self._commit = commit
        self._repo = repo

        self._version: str = ""
        self._nvr: str = ""
        self._component: str = ""
        self._release: str = ""
        self._release_operator: str = ""

    def __repr__(self):
        return f"{self.__class__!s}({self.__dict__})"

    def __str__(self):
        return f"{self.name}: {self.pullspec}"

    async def obtain_info(self):
        cmd = ["oc", "image", "info", "-o", "json", self.pullspec]
        info = await run(cmd)
        labels = info["config"]["config"]["Labels"]
        self._version = labels.get(
            "version", labels.get("org.opencontainers.image.version")
        )
        self._release = labels.get(
            "release", labels.get("coreos.build.manifest-list-tag")
        )
        self._commit = labels.get(
            "io.openshift.build.commit.id",
            labels.get("org.opencontainers.image.revision"),
        )
        self._component = labels.get("com.redhat.component", "rhel-coreos")
        self._repo = labels.get(
            "io.openshift.build.source-location",
            labels.get("org.opencontainers.image.source"),
        )
        self._release_operator = False
        if "io.openshift.release.operator" in labels:
            self._release_operator = True
        self._nvr = f"{self._component}-{self._version}-{self._release}"

    async def nvr(self):
        if not self._nvr:
            await self.obtain_info()
        return self._nvr

    async def version(self):
        if not self._version:
            await self.obtain_info()
        return self._version

    async def release(self):
        if not self._release:
            await self.obtain_info()
        return self._release

    async def commit(self):
        if not self._commit:
            await self.obtain_info()
        return self._commit

    async def component(self):
        if not self._component:
            await self.obtain_info()
        return self._component

    async def release_operator(self):
        if not self._release_operator:
            await self.obtain_info()
        return self._release_operator
