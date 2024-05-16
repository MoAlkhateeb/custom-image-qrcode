"""A Program that Creates custom QR Codes with Images"""

import io
import os
from pathlib import Path
from typing import Optional
from xml.dom import minidom

import cairosvg
from PIL import Image


class SVG:
    """Custom SVG Class."""

    def __init__(self, svg_path: os.PathLike) -> None:
        if not Path(svg_path).exists():
            raise FileNotFoundError(f"SVG File Not Found: {svg_path}")

        self.svg_path: io.PathLike = svg_path
        self.svg: minidom.Document = self.read()

    def read(self) -> minidom.Document:
        """Reads an SVG File and Returns a minidom Document."""
        return minidom.parse(str(self.svg_path))

    def to_image(self, width: int, height: int) -> Image.Image:
        """Saves the SVG as a PNG."""
        image_bytes = io.BytesIO()
        cairosvg.svg2png(
            bytestring=self.svg.toxml().encode(),
            write_to=image_bytes,
            output_width=width,
            output_height=height,
        )
        image_bytes.seek(0)
        return Image.open(image_bytes)

    def save(self, save_path: os.PathLike) -> None:
        """Saves the SVG to a File."""
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(self.svg.toprettyxml())

    def save_png(self, save_path: os.PathLike, width: int, height: int) -> None:
        """Saves the SVG as a PNG."""
        image = self.to_image(width, height)
        image.save(save_path)

    def set_attribute(
        self, attribute: str, value: str, condition: Optional[str] = None
    ) -> None:
        """
        Replaces an all values of an `attribute` with a new `value`.
        If `condition` is provided, only the elements with the `attribute` value equal
        to `condition` will be replaced.
        """
        elements = self.svg.getElementsByTagName("*")

        for element in elements:
            if not element.hasAttribute(attribute):
                continue

            if condition is not None and element.getAttribute(attribute) != condition:
                continue

            element.setAttribute(attribute, value)

    @staticmethod
    def overlay_svg_on_image(
        svg: "SVG",
        image: Image.Image,
        position: tuple[int, int],
        width: int,
        height: int,
    ) -> Image.Image:
        """Overlays an SVG on an Image at a Specified Position."""
        svg_image = svg.to_image(width, height)
        image.paste(svg_image, position, svg_image)
        return image
