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

    def gen_name_diff(self):
        first_names = set(self.first.images.keys())
        second_names = set(self.second.images.keys())

        self.namediff.update(
            {
                self.first.name: first_names - second_names,
                self.second.name: second_names - first_names,
            }
        )
        self.common_names = first_names & second_names

    def gen_payload_diff(self):
        for name in self.common_names:
            first = self.first.images[name]
            second = self.first.images[name]
            if first.pullspec == second.pullspec:
                continue
            self.nvrdiff.append(
                {
                    "name": name,
                    "first": first.nvr,
                    "second": second.nvr,
                }
            )

    def report_nvrdiff(self):
        if not self.nvrdiff:
            self.console.print(":tada: SHAs are all the same :tada:")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.title = "\n\nEnlisting difference NVRs"
        table.add_column(self.first.name)
        table.add_column(self.second.name)
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
