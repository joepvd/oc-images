import asyncio

from rich import print
from rich.console import Console
from rich.table import Table

from oc_images.imagecollection import ImageCollection


class Comparer:
    def __init__(self, first, second):
        self.first = ImageCollection(first)
        self.second = ImageCollection(second)

        self.console = Console(width=200)

        self.report: dict() = {}
        self.nvrdiff: list = []
        self.namediff: dict() = {}
        self.common_names: set() = {}

    async def gen_name_diff(self):
        result = await asyncio.gather(
            asyncio.create_task(self.first.images()),
            asyncio.create_task(self.second.images()),
        )
        first_names = set(result[0].keys())
        second_names = set(result[1].keys())

        self.namediff.update(
            {
                await self.first.name(): first_names - second_names,
                await self.second.name(): second_names - first_names,
            }
        )
        self.common_names = first_names & second_names

    async def gen_payload_diff(self):
        first_images = await self.first.images()
        second_images = await self.second.images()

        async def create_entry(name, first, second):
            result = await asyncio.gather(
                asyncio.create_task(first.nvr()),
                asyncio.create_task(second.nvr()),
            )
            return {
                "name": name,
                "first": result[0],
                "second": result[1],
            }

        tasks = []
        for name in self.common_names:
            first = first_images[name]
            second = second_images[name]
            if first.pullspec == second.pullspec:
                continue
            tasks.append(asyncio.create_task(create_entry(name, first, second)))
        self.nvrdiff = await asyncio.gather(*tasks)

    async def report_nvrdiff(self):
        if not self.nvrdiff:
            self.console.print(":tada: SHAs are all the same :tada:")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.title = "\n\nEnlisting difference NVRs"
        table.add_column(await self.first.name())
        table.add_column(await self.second.name())
        for entry in self.nvrdiff:
            table.add_row(entry["first"], entry["second"])
        self.console.print(table)

    def report_name_diff(self):
        for name, extra in self.namediff.items():
            if not extra:
                continue

            table = Table(show_header=True, header_style="bold magenta", min_width=50)
            table.title = f"\n\nOnly in {name}"
            table.add_column("Payload name")
            for image in extra:
                table.add_row(image)
            self.console.print(table)
