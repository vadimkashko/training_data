#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from pathlib import Path
from sys import argv

import cv2 as cv
import numpy as np


def get_files(extension: str, path: str = '') -> list[Path]:
    """Return Path objects of target files.

    Return paths of images specified in script parameters
    or all images from images directiry.

    Raises:
        FileNotFoundError: If the target file is not found.
        ValueError: If file extension isn't .xml.

    Returns:
        list[Path]: list of target files.
    """
    files_path = Path.cwd() / path
    files = []

    for arg in argv[1:]:
        file = files_path / arg
        if not file.exists():
            raise FileNotFoundError(file)
        elif file.suffix != extension:
            raise ValueError(file.suffix)
        else:
            files.append(file)

    if not files:
        files = list(files_path.glob(f'*{extension}'))

    return files


def make_directories(dir_names: list[str]) -> list[Path]:
    """Make directories and return directories paths.

    Args:
        dir_names (list[str]): directories names.

    Returns:
        list[Path]: directories paths.
    """
    dir_paths = []
    for dir_name in dir_names:
        path = Path(dir_name)
        path.mkdir(exist_ok=True)
        dir_paths.append(path)
    return dir_paths


def get_color(tree: ET.ElementTree) -> tuple:
    """Return mask color.

    Args:
        tree (ET.ElementTree): source xml-structure.

    Returns:
        tuple: mask color.
    """
    root = tree.getroot()
    label = root.find('.//label')
    color = label.find('color')  # type: ignore
    color = color.text[1:]  # type: ignore
    color = tuple(int(color[i:i + 2], 16) for i in (4, 2, 0))
    return color


def get_shapes(image_tag: ET.Element) -> list[dict]:
    """Return shapes with parameters for <image> element.

    Args:
        image (ET.Element): source image.

    Returns:
        list[dict[Any, Any]]: shapes list.
    """
    shapes = []
    for shape_tag in image_tag.iterfind('*'):
        shape = {'type': f'{shape_tag.tag}'}
        for key, value in shape_tag.items():
            shape[key] = value
        shapes.append(shape)
    return shapes


def parse_annotation(tree: ET.ElementTree, image_name: str) -> dict:
    """Return annotation for image from xml-structure with annotations.

    Args:
        tree (ET.ElementTree): xml-structure with annotations.
        image_name (str): image name.

    Returns:
        dict: dictionary with annotation for image.
    """
    annotation = dict()
    root = tree.getroot()
    for image_tag in root.iter('image'):
        name = Path(image_tag.get('name')).name  # type: ignore
        if name == image_name:
            image_tag.set('name', name)
            image = {key: value for key, value in image_tag.items()}
            image['shapes'] = get_shapes(image_tag)
            annotation = image
    return annotation


def create_overlay(width: int, height: int, shapes: list[dict]) -> np.ndarray:
    """Return overlay image with shapes from annotation.

    Args:
        width (int): image width.
        height (int): image height.
        shapes (list[dict]): shapes to draw.

    Returns:
        np.ndarray: overlay image.
    """
    overlay = np.zeros((height, width, 3), np.uint8)
    ignore = np.zeros((height, width, 3), np.uint8)

    overlay_points = []
    ignore_points = []

    for shape in shapes:
        points = [
            tuple(map(float, point.split(',')))
            for point in shape['points'].split(';')
        ]
        points = np.array(points).astype(int)
        if shape['label'] != 'Ignore':
            overlay_points.append(points)
        else:
            ignore_points.append(points)

    overlay = cv.fillPoly(overlay, overlay_points, color=color)
    ignore = cv.fillPoly(ignore, ignore_points, color=color)

    overlay = cv.bitwise_xor(overlay, ignore)
    return overlay


def apply_mask(background: np.ndarray, overlay: np.ndarray) -> np.ndarray:
    """Return result image after adding overlay to source image.

    Args:
        background (np.ndarray): source image.
        overlay (np.ndarray): overlay image.

    Returns:
        np.ndarray: result image.
    """
    mask = overlay.astype(bool)
    background[mask] = cv.addWeighted(background, 0.0, overlay, 1.0, 0.0)[mask]
    return background


if __name__ == '__main__':
    try:
        images = get_files('.jpg', 'images')
        annotations = get_files('.xml')[0]
    except FileNotFoundError as err:
        print(f'File not found by path: {err}.')
    except ValueError as err:
        print(f'Extension must be .xml, not {err}.')
    else:
        tree = ET.parse(annotations)
        color = get_color(tree)

        dir_names = ['mask', 'mask_on_photo']
        paths = make_directories(dir_names)

        for image in images:
            current_image = cv.imread(f'{image}')
            height, width = current_image.shape[:2]

            backgrounds = [
                np.zeros((height, width, 3), np.uint8),
                np.full((height, width, 3), current_image, dtype=np.uint8)
            ]

            annotation = parse_annotation(tree, image.name)

            for bg, path in zip(backgrounds, paths):
                overlay = create_overlay(width, height, annotation['shapes'])
                result = apply_mask(bg, overlay)

                output_path = Path(f'{path}/{path.name}-{image.name}')
                cv.imwrite(f'{output_path}', result)

    finally:
        print('Script is stopped!')
