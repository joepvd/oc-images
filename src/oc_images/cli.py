import asyncio
from functools import update_wrapper

import click

from oc_images.comparer import Comparer
from oc_images.imagecollection import ImageCollection, assembly_to_imagestream


def click_coroutine(f):
    """A wrapper to allow to use asyncio with click.
    https://github.com/pallets/click/issues/85"""

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return update_wrapper(wrapper, f)


@click.group()
@click.option("--debug", is_flag=True, help="Show what is happening")
def images(debug):
    """\
    oc images: Generate reports of imagestreams or payloads
    """
    pass


@images.command("list")
@click.option("--filter", "-f", help="filter by payload name")
@click.option("--name", "-n", multiple=True, help="Report on exact payload names")
@click.option("--pullspec", "-p", is_flag=True, help="Return pullspec rather than nvr")
@click.option("--assembly", "-a", help="Look at x86_64 imagestream of assembly")
@click.argument("collection", required=False)
@click_coroutine
async def list_collection(
    filter: str, name: list, pullspec: str, assembly: str, collection: str = ""
):
    """\
    List contents of image stream or payload
      oc images list --filter ironic"""

    if filter and name:
        raise click.BadParameter("Filter and name cannot both be specified")
    if assembly and collection:
        raise click.BadParameter("Only one of assembly and collection can be specified")
    if not assembly and not collection:
        raise click.BadParameter("Must have one of assembly or collection")

    if assembly:
        collection = assembly_to_imagestream(assembly)

    ic = ImageCollection(collection)
    images = await ic.images()
    to_report = []
    for tag, image in images.items():
        if filter and filter not in tag:
            continue
        elif name and tag not in name:
            continue
        to_report.append(image)

    if pullspec:
        print("\n".join([f"{i.name} {i.pullspec}" for i in to_report]))
        return

    tasks = [asyncio.create_task(image.nvr()) for image in to_report]
    result = await asyncio.gather(*tasks)
    print("\n".join(result))


@images.command()
@click.argument("collection", nargs=2)
@click_coroutine
async def diff(collection):
    """\
    Show differences between two payload/imagestreams
    """
    comparer = Comparer(*collection)

    await comparer.gen_name_diff()
    await comparer.gen_payload_diff()

    await comparer.report_nvrdiff()
    comparer.report_name_diff()
