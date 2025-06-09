import asyncio
from functools import update_wrapper

import click
from rich.console import Console
from rich.markdown import Markdown

from oc_images.comparer import Comparer
from oc_images.imagecollection import ImageCollection


def click_coroutine(f):
    """A wrapper to allow to use asyncio with click.
    https://github.com/pallets/click/issues/85"""

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return update_wrapper(wrapper, f)


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
def images():
    """\
    oc images: Generate reports of imagestreams or payloads

    \b
    oc images list -h
    oc images diff -h
    oc images help-collection
    """


@images.command("list")
@click.option("--filter", "-f", help="filter by payload name")
@click.option("--name", "-n", multiple=True, help="Report on exact payload names")
@click.option("--pullspec", "-p", is_flag=True, help="Return pullspec rather than nvr")
@click.argument("collection")
@click_coroutine
async def list_collection(filter: str, name: list, pullspec: str, collection: str = ""):
    """\
    List contents of image stream or payload

    \b
    Examples:
      oc images list --filter ironic 4.14.15
        Looks for payload entries containing string 'ironic'
        in x86_64 imagestream of 4.14.15 assembly
      oc images list --name ironic ocp/4.17-art-assembly-4.17.38
        Look for image with name 'ironic' in ImagesStream
      oc images list --name oc-mirror 4.18-nightly
        Look for image named 'oc-mirror' in 4.18 imagestream that feeds
        into the next nightly
      oc images list --name cli quay.io/openshift-release-dev/ocp-release:4.19.0-ec.4-x86_64
        Look for nvr of payload name 'cli' in release

    Run 'oc images help-collection' for help on specifying payloads, imagestreams, and assemblies
    """

    if filter and name:
        raise click.BadParameter("Filter and name cannot both be specified")

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
    Show differences between two payload/imagestreams/assemblies

    \b
    Examples:
      Show the difference between two assemblies:
        oc images diff 4.18.2 4.18.3
      Will there be a new nightly?
        oc images diff 4.19-latest registry.ci.openshift.org/ocp/release:4.19.0-0.nightly-2025-06-09-104318
      Show diff between imagestreams of custom assembly and standard assembly:
        oc images diff 4.14-art123 4.14.52

    Run 'oc images help-collection' for help on specifying payloads, imagestreams, and assemblies
    """
    comparer = Comparer(*collection)

    await comparer.gen_name_diff()
    await comparer.gen_payload_diff()

    await comparer.report_nvrdiff()
    comparer.report_name_diff()


@images.command()
def help_collection():
    """
    # On `collection` arguments
    Openshift has two similar concepts, _release payloads_, and _imageStreams_.
    A release payload is a Cluster Version Operator (CVO) image, where `oc` has layered references
    to images contained in the CVO, alongside the manifests that instruct how to run the payload
    operators. The "related images" in a release payload is somewhat tied to an ImageStream.

    ImageStreams are a collection of images with a name and a pullspec. Payloads typically get constructed
    with reference to such an imagestream.

    This application takes positional arguments for these image collections, and makes educated guesses
    what the user means. These are taken as payloads:

    ## Specify by payload


    This is straightforward: Paste the resource you would use in `oc adm release info`:

    ```
    registry.ci.openshift.org/ocp/release:4.20.0-0.nightly-2025-06-06-044542
    quay.io/openshift-release-dev/ocp-release:4.18.2-x86_64
    quay.io/openshift-release-dev/ocp-release:4.19.0-rc.5-s390x
    ```

    ## Specify by imagestream

    These are literal imageStreams that are interpreted correctly:

    | argument                                   | comment                                 |
    |--------------------------------------------|-----------------------------------------|
    | `4.19-art-latest`                          | x86\_64 is assumed                      |
    | `4.17-art-assembly-4.17-3`                 | Named assembly                          |
    | `4.17-art-assembly-4.17-3-s390x`           | Named assembly for funny arch           |
    | `ocp-arm64/4.17-art-assembly-4.17-3-arm64` | Named assembly for funny arch           |
    | `ocp/4.19-art-latest`                      | Explicitly specify namespace before `/` |
    | `ocp-s390x/4.19-art-latest-s390x`          | Fully qualified funny arch              |
    | `4.17-art-latest-ppc64le`                  | Namespace is assumed                    |
    | `4.17-art-assembly-art123`                 | Custom assemblies also work             |


    ## Specify by assembly

    ImageStreams for an assembly are always prepended with the OCP-ystream they
    are relevant for. For zstream releases, the entries in `releases.yml` have this
    OCP ystream embedded. For ECs, RCs, and custom assemblies, this is not the case.
    So prepend the ystream before the actual name in `releases.yml`, so that:


    | Assembly name | Accepted argument | ImageStream                         |
    |---------------|-------------------|-------------------------------------|
    | `4.19.3`      | `4.19.3`          | `ocp/4.19-art-assembly-4.19.3`      |
    | `rc.5`        | `4.19-rc.5`       | `ocp/4.19-art-assembly-4.19.0-rc.5` |
    | `art123`      | `4.12-art123`     | `ocp/4.12-art-assembly-4.12-art123` |
    | `stream`      | `4.12-stream`     | `ocp/4.12-art-latest`               |
    | `stream`      | `4.20-latest`     | `ocp/4.20-art-latest`               |
    """
    console = Console()
    console.print(Markdown(help_collection.__doc__))
