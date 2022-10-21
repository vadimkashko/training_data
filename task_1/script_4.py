#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from pathlib import Path
from sys import argv


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


def invert_images_ids(tree: ET.ElementTree) -> ET.ElementTree:
    """Return updated structure of xml-document with inverted images ids.

    Args:
        tree (ET.ElementTree): source xml-structure.

    Returns:
        ET.ElementTree: output xml-structure.
    """
    root = tree.getroot()
    images_number = len(root.findall('image'))
    for image in root.iter('image'):
        id = int(image.get('id'))  # type: ignore
        new_id = images_number - (id + 1)
        image.set('id', str(new_id))
    return tree


def change_images_extensions(tree: ET.ElementTree,
                             extension: str) -> ET.ElementTree:
    """Return updated structure of xml-document with changed images extensions.

    Args:
        tree (ET.ElementTree): source xml-structure.

    Returns:
        ET.ElementTree: output xml-structure.
    """
    root = tree.getroot()
    for image in root.iter('image'):
        name = Path(image.get('name'))  # type: ignore
        name = name.with_suffix(extension)
        image.set('name', str(name))
    return tree


def delete_images_paths(tree: ET.ElementTree) -> ET.ElementTree:
    """Return updated structure of xml-document with deleteded images paths.

    Args:
        tree (ET.ElementTree): source xml-structure.

    Returns:
        ET.ElementTree: output xml-structure.
    """
    root = tree.getroot()
    for image in root.iter('image'):
        name = Path(image.get('name'))  # type: ignore
        name = name.name
        image.set('name', str(name))
    return tree


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

            updated_tree = invert_images_ids(tree)
            updated_tree = change_images_extensions(updated_tree, '.png')
            updated_tree = delete_images_paths(updated_tree)

            tree.write(f'{file.stem}-updated.xml',
                       encoding='utf-8',
                       xml_declaration=True)
    finally:
        print('Script is stopped!')
