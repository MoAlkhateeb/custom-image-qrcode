"""
Finds the Most Prominent Color in an Image.

Modified from the JavaScript version https://github.com/pieroxy/color-finder under WTFPL, Version 2.

Author: Mohammed Alkhateeb (@MoAlkhateeb)
"""

import io
from pathlib import Path
from collections import Counter
from typing import Callable, Optional
from PIL import Image, ImageColor, ImageEnhance

RGBPixel = tuple[int, int, int]
PathLike = str | Path


class ColorFinder:
    """
    A Class that Finds the Most Prominent Color in an Image.
    By Default, it Favors Hue.
    """

    def __init__(
        self,
        image: Image.Image,
        color_factor_callback: Callable[[RGBPixel], float] | None = None,
    ):

        self.callback: Callable[[RGBPixel], float]

        if color_factor_callback is None:
            self.callback = self.favour_hue
        else:
            self.callback = color_factor_callback

        self.image = image.convert("RGB")

        self.counter = Counter(self.image.getdata())

    def set_callback(self, callback: Callable[[RGBPixel], float]) -> None:
        """Sets the Callback Function to be used for Colour Detection."""
        self.callback = callback

    def get_colour(self) -> str:
        """Returns the most prominent colour based on the callback function."""

        data = self.get_image_data()

        rgb = self.get_most_prominent_rgb_impl(data, 6, None)
        rgb = self.get_most_prominent_rgb_impl(data, 4, rgb)
        rgb = self.get_most_prominent_rgb_impl(data, 2, rgb)
        rgb = self.get_most_prominent_rgb_impl(data, 0, rgb)

        hex_colour = f"#{rgb['r']:02x}{rgb['g']:02x}{rgb['b']:02x}"

        return hex_colour

    def get_image_data(self) -> dict[RGBPixel, dict[str, int]]:
        """
        Gets Pixel Counts and Weights from an Image. Returns them as a dictionary.
        Weight is calculated based on the callback function.

        returns {
            (r, g, b): {
                "weight": int,
                "count": int,
            },
            ...
        }

        """
        result: dict[RGBPixel, dict[str, int]] = {}
        for pixel, count in self.counter.items():
            result[pixel] = {
                "weight": max(int(self.callback(pixel)), 0),
                "count": count,
            }

        return result

    def get_most_prominent_rgb_impl(
        self,
        pixels: dict[RGBPixel, dict[str, int]],
        degrade: int,
        rgb_match: Optional[dict[str, float]],
    ) -> dict[str, float]:
        """Gets the Most Prominent"""

        rgb: dict[str, float] = {"r": 0, "g": 0, "b": 0, "weight": 0, "d": degrade}
        db: dict[RGBPixel, float] = {}

        for pixel, value in pixels.items():
            total_weight = value["weight"] * value["count"]
            if self.does_rgb_match(rgb_match, pixel):
                degraded_pixel: RGBPixel = tuple(c >> degrade for c in pixel)  # type: ignore
                db[degraded_pixel] = db.get(degraded_pixel, 0) + total_weight

        max_weight = max(db.items(), key=lambda x: x[1])
        rgb["r"], rgb["g"], rgb["b"] = max_weight[0]
        rgb["weight"] = max_weight[1]

        return rgb

    def does_rgb_match(
        self, reference: Optional[dict[str, float]], pixel: RGBPixel
    ) -> bool:
        """Checks if the RGB values in `pixel` match the RGB values in `reference` after degrade."""
        if reference is None:
            return True

        r, g, b = (c >> int(reference["d"]) for c in pixel)

        return reference["r"] == r and reference["g"] == g and reference["b"] == b

    @staticmethod
    def get_dark_light_colours(image: Image.Image) -> tuple[str, str]:
        """
        Returns the most prominent Dark and Light Colours ensuring they are not too
        close to each other. If the colours are too close to each other, the dark colour
        is set to black and the light colour is set to white.
        """
        finder = ColorFinder(image, ColorFinder.favour_dark)
        dark = finder.get_colour()
        finder.set_callback(ColorFinder.favour_hue)
        light = finder.get_colour()

        dr, dg, db, *_ = ImageColor.getrgb(dark)
        lr, lg, lb, *_ = ImageColor.getrgb(light)

        distance = ((dr - lr) ** 2 + (dg - lg) ** 2 + (db - lb) ** 2) / 195075

        if distance < 0.3:
            dark = "#000000"
        if lr < 50 and lg < 50 and lb < 50:
            light = "#FFFFFF"

        return dark, light

    @staticmethod
    def favour_bright_exclude_white(pixel: RGBPixel) -> float:
        """A Callback Function that Favours Bright Colors and Excludes White."""

        r, g, b = pixel
        if r > 245 and g > 245 and b > 245:
            return 0
        return (r * r + g * g + b * b) / 65535 * 20 + 1

    @staticmethod
    def favour_dark(pixel: RGBPixel) -> float:
        """A Callback Function that Favours Dark Colors."""
        r, g, b = pixel
        return 768 - r - g - b + 1

    @staticmethod
    def favour_hue(pixel: RGBPixel) -> float:
        """A Callback Function that Favours Hue."""
        r, g, b = pixel
        return (
            abs(r - g) * abs(r - g) + abs(r - b) * abs(r - b) + abs(g - b) * abs(g - b)
        ) / 65535 * 50 + 1

    @staticmethod
    def favour_saturation(pixel: RGBPixel) -> float:
        """A Callback Function that Favours Saturation."""
        max_value: float = max(pixel) / 255
        min_value: float = min(pixel) / 255
        luminosity: float = max_value - min_value

        if luminosity == 0:
            saturation = 0.0
        elif luminosity < 0.5:
            saturation = luminosity / (max_value + min_value)
        elif luminosity > 0.5:
            saturation = luminosity / (2 - max_value - min_value)

        return saturation


def colour_correct_image(
    image_path: PathLike,
    contrast_factor: float = 1.3,
    brightness_factor: float = 1.1,
) -> io.BytesIO:
    """Increases the Brightness of an Image."""
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image File Not Found: {image_path}")

    img = Image.open(image_path).convert("RGB")

    contrast_enhancer = ImageEnhance.Contrast(img)
    brightness_enhancer = ImageEnhance.Brightness(img)

    img = contrast_enhancer.enhance(contrast_factor)
    img = brightness_enhancer.enhance(brightness_factor)
    img = contrast_enhancer.enhance(contrast_factor)

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")

    return img_bytes
