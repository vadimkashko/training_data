#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from pathlib import Path
from sys import argv

import prettytable as pt

# Dictionary with column names and align types for table
TABLE_PARAMS = {'Parameter': 'l', 'Value': 'x'}


def get_files() -> list[Path]:
    """Return Path objects of target files.

    Return paths of xml files specified in script parameters or all xml
    files from current directiry.

    Raises:
        FileNotFoundError: If the target file is not found.
        ValueError: If file extension isn't .xml.

    Returns:
        list[Path]: list of target files.
    """
    current_path = Path.cwd()
    files = []

    for arg in argv[1:]:
        file = current_path / arg
        if not file.exists():
            raise FileNotFoundError(file)
        elif file.suffix != '.xml':
            raise ValueError(file.suffix)
        else:
            files.append(file)

    if not files:
        files = list(current_path.glob('*.xml'))

    return files


def create_table(rows: list[list], params: dict[str, str]) -> pt.PrettyTable:
    """Return PrettyTable object filled with data.

    Args:
        rows (list[tuple]): data for filling.
        params (dict): column names and align parametres.

    Returns:
        PrettyTable: PrettyTable object.
    """
    table = pt.PrettyTable()
    table.field_names = params
    table.add_rows(rows)
    for k, v in params.items():
        table.align[k] = v
    table.border = False
    table.preserve_internal_border = True
    return table


def get_images(tree: ET.ElementTree) -> list[ET.Element]:
    """Return list of elements with <image> tag.

    Args:
        tree (ET.ElementTree): xml tree.

    Returns:
        list[ET.Element]: list of <image> elements.
    """
    images = tree.findall('image')
    return images


def get_annotated_images(images: list[ET.Element]) -> list[ET.Element]:
    """Return list of <image> elements containing subelements.

    Args:
        images (list[ET.Element]): list of <image> elements.

    Returns:
        list[ET.Element]: list of <image> elements.
    """
    annotated_images = list(filter(len, images))
    return annotated_images


def get_figures(images: list[ET.Element]) -> list[ET.Element]:
    """Return list of subelements from all elements.

    Args:
        images (list[ET.Element]): list of <image> elements.

    Returns:
        list[ET.Element]: list of <image> elements.
    """
    figures = []
    for image in images:
        figures.extend(image.iterfind('*'))
    return figures


def get_image_size(image: ET.Element) -> int:
    """Return size of image from <image> element as height multiplied by width.

    Args:
        image (ET.Element): <image> element.

    Returns:
        int: size.
    """
    height = int(image.get('height', default=0))
    width = int(image.get('width', default=0))
    size = height * width
    return size


def get_extreme_images(images: list[ET.Element], func=max) -> list[ET.Element]:
    """Return list of <image> elements with extremal (min or max) sizes.

    Args:
        images (list[ET.Element]): list of <image> elements.
        func (_type_, optional): max or min function. Defaults to max.

    Returns:
        list[ET.Element]: list of extremal <image> elements.
    """
    extreme_image = func(images, key=get_image_size)
    max_size = get_image_size(extreme_image)
    extreme_images = [img for img in images if get_image_size(img) == max_size]
    return extreme_images


if __name__ == '__main__':
    try:
        files = get_files()
    except FileNotFoundError as err:
        print(f'File not found by path: {err}.')
    except ValueError as err:
        print(f'Extension must be .xml, not {err}.')
    else:
        for file in files:
            tree = ET.parse(file)
            rows = []

            images = get_images(tree)
            images_number = len(images)
            rows.append(['Images', images_number])

            annotated_images = get_annotated_images(images)
            annotated_images_number = len(annotated_images)
            not_annotated_images_number = 0

            if images_number != annotated_images_number:
                not_annotated_images_number = \
                                    images_number - annotated_images_number

            rows.append(['Annotated images', annotated_images_number])
            rows.append(['Not annotated images', not_annotated_images_number])

            figures = get_figures(annotated_images)
            figures_number = len(figures)
            rows.append(['Figures', figures_number])

            largest_images = get_extreme_images(images, max)
            smallest_images = get_extreme_images(images, min)
            largest_images_number = len(largest_images)
            smallest_images_number = len(smallest_images)
            rows.extend(
                [['Largest images', largest_images_number],
                 ['Largest image', largest_images[0].get("name")],
                 ['Largest image height', largest_images[0].get("height")],
                 ['Largest image width', largest_images[0].get("width")],
                 ['Smallest images', smallest_images_number],
                 ['Smallest image', smallest_images[0].get("name")],
                 ['Smallest image height', smallest_images[0].get("height")],
                 ['Smallest image width', smallest_images[0].get("width")]])

            table = create_table(rows, TABLE_PARAMS)
            file_info = table.get_string()

            with open(f'{file.stem}-common.txt', 'w') as out_file:
                out_file.write(file_info)
    finally:
        print('Script is stopped!')
