#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from sys import argv

import prettytable as pt

# Dictionary with column names and align types for table
TABLE_PARAMS = {'Shape type': 'l', 'Quantity': 'x'}


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


def create_table(rows: list[tuple[str, int]],
                 params: dict[str, str]) -> pt.PrettyTable:
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


def get_shapes(tree: ET.ElementTree) -> list[str]:
    """Return all subelement tags (shapes) of <image> tags.

    Args:
        tree (ET.ElementTree): xml tree.

    Returns:
        list[str]: list of shapes.
    """
    root = tree.getroot()
    shapes = []
    for image in root.iter('image'):
        for tag in image.iterfind('*'):
            shapes.append(tag.tag)
    return shapes


def count_shapes(shapes: list[str]) -> list[tuple[str, int]]:
    """Return list of tuples with shape's types and quantity for table's rows.

    Args:
        shapes (list[str]): list of shapes.

    Returns:
        list[tuple[str, int]]: list of rows.
    """
    counter = Counter(shapes)
    rows = counter.most_common()
    return rows


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

            shapes = get_shapes(tree)

            rows = count_shapes(shapes)
            table = create_table(rows, TABLE_PARAMS)
            file_info = table.get_string()

            dir_name = Path(f'{file.stem}')
            dir_name.mkdir(exist_ok=True)
            with open(f'{dir_name}/shapes.txt', 'w') as out_file:
                out_file.write(file_info)
    finally:
        print('Script is stopped!')
