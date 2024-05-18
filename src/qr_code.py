"""Holds Custom QR Code Functionality."""

import os
import io
import math
from PIL import Image
from pathlib import Path
from typing import Optional

import segno
import segno.consts
import qrcode_artistic

import svg
import colour_finder


class QRCode:
    """Custom QR Code Class."""

    def __init__(self, data: str, width: int, height: int, dpi: int) -> None:
        """
        Initializes the QR Code Object.

        dpi, width and height are only used when saving the QR Code Image.
        """

        self._data: int = data
        self._width: int = width
        self._height: int = height
        self._dpi: int = dpi

        self._qr_code: segno.QRCode = self._create_qr_code_object()
        self._qr_code_image: Optional[Image.Image] = None

    @property
    def data(self) -> str:
        """Returns the Data."""
        return self._data

    @property
    def width(self) -> int:
        """Returns the Width."""
        return self._width

    @property
    def height(self) -> int:
        """Returns the Height."""
        return self._height

    @property
    def dpi(self) -> int:
        """Returns the DPI."""
        return self._dpi

    @property
    def scale(self) -> int:
        """Returns the Scale Factor."""
        return math.ceil(self.width / self._qr_code.symbol_size(scale=1)[0])

    @property
    def qr_code(self) -> segno.QRCode:
        """Returns the QR Code Object."""
        return self._qr_code

    @property
    def qr_code_image(self) -> Optional[Image.Image]:
        """Returns the QR Code Image."""
        return self._qr_code_image

    def _create_qr_code_object(self) -> segno.QRCode:
        """Creates a `segno.QRCode` Object."""
        return segno.make_qr(self.data, error="H", boost_error=True)

    def create_qr_code_image(
        self,
        image_path: Optional[os.PathLike] = None,
        dark_colour: str = "black",
        light_colour: str = "white",
        dynamic_colours: bool = False,
        custom_finder_marker_svg: Optional[os.PathLike] = None,
    ) -> None:
        """
        Creates a QR Code using optionally an image.

        If `dynamic_colours` is True, the `dark_colour` and `light_colour` will be ignored.
        """
        if image_path is not None:

            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image File Not Found: {image_path}")

            if dynamic_colours:
                img = Image.open(image_path)
                dark_colour, light_colour = (
                    colour_finder.ColorFinder.get_dark_light_colours(img)
                )

            qr_code_image_bytes = io.BytesIO()

            qrcode_artistic.write_artistic(
                qrcode=self._qr_code,
                scale=self.scale,
                background=colour_finder.colour_correct_image(image_path),
                target=qr_code_image_bytes,
                finder_dark=dark_colour,
                finder_light=light_colour,
                kind="PNG",
            )

            image_bytes = qr_code_image_bytes.getvalue()

            self._qr_code_image = Image.open(io.BytesIO(image_bytes))

        else:

            self._qr_code_image = self._qr_code.to_pil(
                scale=self.scale,
                finder_dark=dark_colour,
                finder_light=light_colour,
            )

        self._qr_code_image = self._qr_code_image.convert("RGB")

        if custom_finder_marker_svg is not None:
            self.change_finder_markers(
                custom_finder_marker_svg, dark_colour, light_colour
            )

    def change_finder_markers(
        self,
        svg_path: os.PathLike,
        dark_colour: Optional[str] = "#000000",
        light_colour: Optional[str] = "#FFFFFF",
    ) -> None:
        """Overlays an SVG on the QR Code Image."""
        if self._qr_code_image is None:
            raise ValueError("No QR Code Image to Change Finder Markers.")

        if not Path(svg_path).exists():
            raise FileNotFoundError(f"SVG File Not Found: {svg_path}")

        if Path(svg_path).suffix != ".svg":
            raise ValueError("SVG File Required.")

        marker_positions = self._remove_finding_markers()

        # create a new SVG for the custom finder marker
        marker_svg = svg.SVG(svg_path)
        if dark_colour is not None:
            marker_svg.set_attribute("fill", dark_colour, "dark")
            marker_svg.set_attribute("stroke", dark_colour, "dark")

        if light_colour is not None:
            marker_svg.set_attribute("fill", light_colour, "light")
            marker_svg.set_attribute("stroke", light_colour, "light")

        for point1, point2 in marker_positions:
            width = point2[0] - point1[0] + 1
            height = point2[1] - point1[1] + 1

            self._qr_code_image = svg.SVG.overlay_svg_on_image(
                svg=marker_svg,
                image=self._qr_code_image,
                position=point1,
                width=width,
                height=height,
            )

    def save(self, save_path: os.PathLike) -> None:
        """Saves the QR Code Image to a File."""
        if self._qr_code_image is None:
            raise ValueError("No QR Code Image to Save.")

        if self._qr_code_image.size != (self.width, self.height):
            resized_image = self._qr_code_image.resize((self.width, self.height))
        else:
            resized_image = self._qr_code_image

        resized_image.save(save_path, dpi=(self.dpi, self.dpi))

    def _remove_finding_markers(
        self,
    ) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        """
        Completely Removes the Finder Markers from the QR Code.
        Returns the removed Finder Marker Positions.
        """
        if self._qr_code_image is None:
            raise ValueError("No QR Code Image to Remove Finder Markers.")

        finding_markers = self.get_finding_marker_positions(self)

        for point1, point2 in finding_markers:
            width = point2[0] - point1[0] + 1
            height = point2[1] - point1[1] + 1

            rectangle = Image.new("RGB", (width, height), "white")
            self._qr_code_image.paste(rectangle, point1)

        return finding_markers

    @staticmethod
    def get_finding_marker_positions(
        qr_code: "QRCode",
    ) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        """
        Returns the Positions of the Finder Markers.

        (top_left_marker, top_right_marker, bottom_left_marker):
        each marker is represented by a tuple of two points (top_left, bottom_right)
        """
        image: Optional[Image.Image] = qr_code.qr_code_image

        if image is None:
            raise ValueError("No QR Code Image to Get Finder Marker Positions.")

        middle_x, middle_y = image.width // 2, image.height // 2

        top_left_marker = []
        top_right_marker = []
        bottom_left_marker = []

        for y, row in enumerate(
            qr_code.qr_code.matrix_iter(scale=qr_code.scale, verbose=True)
        ):
            for x, col in enumerate(row):
                if col != segno.consts.TYPE_FINDER_PATTERN_DARK:
                    continue

                if x > middle_x:
                    top_right_marker.append((x, y))
                elif x < middle_x and y < middle_y:
                    top_left_marker.append((x, y))
                elif x < middle_x and y > middle_y:
                    bottom_left_marker.append((x, y))

        def coordinate_sum(x: tuple[int, int]) -> int:
            return x[0] + x[1]

        top_left_marker.sort(key=coordinate_sum)
        top_right_marker.sort(key=coordinate_sum)
        bottom_left_marker.sort(key=coordinate_sum)

        return (
            (top_left_marker[0], top_left_marker[-1]),
            (top_right_marker[0], top_right_marker[-1]),
            (bottom_left_marker[0], bottom_left_marker[-1]),
        )