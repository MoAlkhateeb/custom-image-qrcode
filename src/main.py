"""A Program that Creates custom QR Codes with Images"""

import os
import sys
import warnings
import configparser
from typing import Any
from pathlib import Path

import qr_code

warnings.simplefilter("ignore", UserWarning)


def read_config(config_path: os.PathLike) -> dict[str, Any]:
    """Reads a Config File and Returns a Dictionary of Configurations"""
    config = configparser.ConfigParser()

    if getattr(sys, "frozen", False):
        config_path = Path(sys.executable).parent / "config.ini"
    elif __file__:
        config_path = Path(__file__).parent / "config.ini"

    config.read(config_path)

    return {
        "width": config.getint("Specs", "Width"),
        "height": config.getint("Specs", "Height"),
        "dpi": config.getint("Specs", "DPI"),
        "url": config["Specs"]["URL"],
        "custom_marker": config.getboolean("Specs", "CustomMarker"),
        "custom_marker_svg": Path(config["Paths"]["CustomMarkerSVG"]),
        "input_path": Path(config["Paths"]["InputPath"]),
        "output_path": Path(config["Paths"]["OutputPath"]),
    }


def generate_qr_codes(conf: dict[str, Any]) -> None:
    """Generate all qr codes for image in input_path and saves them in output_path."""
    for image in conf["input_path"].iterdir():
        if image.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            if conf["custom_marker"]:
                marker_path = conf["custom_marker_svg"]
                marker_name = marker_path.stem
            else:
                marker_path = None
                marker_name = "default"

            save_path = conf["output_path"] / f"QR_{marker_name}_{image.stem}.png"

            print(f"[INFO]: Generating QR Code for {str(image):<50} = {save_path}")

            code = qr_code.QRCode(
                conf["url"], conf["width"], conf["height"], conf["dpi"]
            )

            code.create_qr_code_image(
                image,
                dynamic_colours=True,
                custom_finder_marker_svg=marker_path,
            )

            code.save(save_path)


def print_heading(heading: str) -> None:
    """Prints a Heading with a Border of Asterisks"""
    print("\n")
    print("*" * 50)
    print(heading.center(50))
    print("*" * 50)
    print("\n")


def main() -> None:
    """The Main Program Entry Point"""

    import pprint

    print_heading("QR Code Generator")

    conf = read_config("config.ini")

    width = input("Width of the QR Code: (Enter for Default): ")
    height = input("Height of the QR Code: (Enter for Default): ")
    dpi = input("DPI of the QR Code: (Enter for Default): ")

    if width:
        try:
            conf["width"] = int(width)
            print("Width Value Changed to ", conf["width"])
        except ValueError:
            print(f"Invalid Width Value. Using Default Value={conf['width']}")

    if height:
        try:
            conf["height"] = int(height)
            print("Height Value Changed to ", conf["height"])
        except ValueError:
            print(f"Invalid Height Value. Using Default Value={conf['height']}")

    if dpi:
        try:
            conf["dpi"] = int(dpi)
            print("DPI Value Changed to ", conf["dpi"])
        except ValueError:
            print(f"Invalid DPI Value. Using Default Value={conf['dpi']}")

    print_heading("Final Configuration")
    pprint.pprint(conf, indent=4, sort_dicts=True)
    print("\n")

    print_heading("Generating QR Codes")
    generate_qr_codes(conf)


if __name__ == "__main__":
    main()
