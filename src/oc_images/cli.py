from oc_images.imagecollection import ImageCollection
from oc_images.comparer import Comparer

import click


@click.group()
@click.option('--debug', is_flag=True, help='Show what is happening')
def images(debug):
    '''\
    oc images: Generate reports of imagestreams or payloads
    '''
    pass

@images.command('list')
@click.option('--filter', '-f', help='filter by payload name')
@click.option('--name', '-n', multiple=True, help='Report on exact payload names')
@click.option('--nvr', help='output by nvr', is_flag=True)
@click.argument('collection')
def list_collection(collection, filter, nvr, name):
    '''\
    List contents of image stream or payload
      oc images list --filter ironic
    '''
    if filter and name:
        raise click.BadParameter('Filter and name cannot both be specified')
    ic = ImageCollection(collection)
    for tag, image in ic.images.items():
        if filter and filter not in tag:
            continue
        if name and tag not in name:
            continue
        if nvr:
            print(image.nvr)
        else:
            print(image)


@images.command()
@click.argument('collection', nargs=2)
def diff(collection):
    '''\
    Show differences between two payload/imagestreams
    '''
    comparer = Comparer(*collection)
    comparer.gen_name_diff()
    comparer.gen_payload_diff()

    comparer.report_nvrdiff()
    comparer.report_name_diff()
