"""
Main entry file that orchastrates QR code generation.

Author: Mohammed Alkhateeb (@MoAlkhateeb)

pyinstaller Command:
    pyinstaller --noconfirm --onefile --console 
    --icon "C:/Users/mh/Downloads/qr-code_icon-icons.com_69971.ico" 
    --name "QRCodeGenerator" --add-data "C:/Users/mh/Desktop/CustomImageQR/src/svg.py;." 
    --add-data "C:/Users/mh/Desktop/CustomImageQR/src/qr_code.py;." 
    --add-data "C:/Users/mh/Desktop/CustomImageQR/src/colour_finder.py;." 
    --add-binary "C:/Users/mh/Desktop/vips-dev-8.15/vips.exe;." 
    --add-binary "C:/Users/mh/Desktop/vips-dev-8.15/libvips-42.dll;." 
    --paths "C:/Users/mh/Desktop/vips-dev-8.15"  
    "C:/Users/mh/Desktop/CustomImageQR/src/main.py"
"""

import sys
import pprint
import warnings
import configparser
from pathlib import Path
from typing import TypedDict
from multiprocessing import freeze_support
from concurrent.futures import ProcessPoolExecutor

from tqdm import tqdm

import qr_code

PathLike = str | Path


warnings.simplefilter("ignore", UserWarning)

IS_FROZEN = getattr(sys, "frozen", False)
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg"]
BAR_FORMAT = "{l_bar}{bar} | {n_fmt}/{total_fmt} [ETA: {remaining}, Elapsed: {elapsed}, {rate_fmt}]"


class Config(TypedDict):
    """A Typed Dictionary for Configuration Options."""

    width: int
    height: int
    dpi: int
    url: str
    custom_marker: bool
    custom_marker_svg: Path
    input_path: Path
    output_path: Path


def read_config(config_path: PathLike) -> Config:
    """Reads a Config File and Returns a Dictionary of Configurations"""
    config = configparser.ConfigParser()

    if IS_FROZEN:
        config_path = Path(sys.executable).parent / "config.ini"
    elif __file__:
        config_path = Path(__file__).parent / "config.ini"

    config.read(config_path)

    return Config(
        width=config.getint("Specs", "Width"),
        height=config.getint("Specs", "Height"),
        dpi=config.getint("Specs", "DPI"),
        url=config["Specs"]["URL"],
        custom_marker=config.getboolean("Specs", "CustomMarker"),
        custom_marker_svg=Path(config["Paths"]["CustomMarkerSVG"]),
        input_path=Path(config["Paths"]["InputPath"]),
        output_path=Path(config["Paths"]["OutputPath"]),
    )


def helper(arguments: tuple[PathLike, Config]) -> Path:
    """Helper Function to Generate QR Code for Multiple Images."""
    return generate_qr_code(*arguments)


def generate_qr_code(image_path: PathLike, conf: Config) -> Path:
    """Creates a QR Code for the Image and Saves it in the Output Path."""

    if conf["custom_marker"]:
        marker_path = conf["custom_marker_svg"]
        marker_name = marker_path.stem
    else:
        marker_path = None
        marker_name = "default"

    save_path = conf["output_path"] / f"QR_{marker_name}_{Path(image_path).stem}.png"

    code = qr_code.QRCode(conf["url"], conf["width"], conf["height"], conf["dpi"])

    code.create_qr_code_image(
        image_path,
        dynamic_colours=True,
        custom_finder_marker_svg=marker_path,
    )

    code.save(save_path)

    return save_path


def generate_qr_codes(conf: Config) -> None:
    """Generate all qr codes for image in input_path and saves them in output_path."""

    request_list = []
    for image in find_images(conf["input_path"]):
        request_list.append((image, conf))

    print("Number of Images: ", len(request_list), "\n")

    save_paths: list[Path] = []

    with tqdm(
        total=len(request_list),
        bar_format=BAR_FORMAT,
    ) as pbar:
        with ProcessPoolExecutor() as executor:
            for save_path in executor.map(helper, request_list):
                pbar.update()
                save_paths.append(save_path)

    print("\n")
    print_heading("Generated QR Codes")
    for num, path in enumerate(save_paths, start=1):
        print(f"{num:<3}- {path}")
    print()


def print_heading(heading: str) -> None:
    """Prints a Heading with a Border of Asterisks"""
    print("\n")
    print("*" * 50)
    print(heading.center(50))
    print("*" * 50)
    print("\n")


def find_images(input_path: Path) -> list[Path]:
    """Finds all Images in the Input Path"""
    return [
        image
        for image in input_path.iterdir()
        if image.suffix.lower() in SUPPORTED_IMAGE_FORMATS
    ]


def main() -> None:
    """The Main Program Entry Point"""

    print_heading("QR Code Generator")

    conf = read_config("config.ini")

    width = input("\nWidth of the QR Code: (Enter for Default): ")
    if width:
        try:
            if int(width) <= 0:
                raise ValueError

            conf["width"] = int(width)
            print("Width Value Changed to", conf["width"])
        except ValueError:
            print(f"Invalid Width Value. Using Default Value={conf['width']}")

    height = input("\nHeight of the QR Code: (Enter for Default): ")
    if height:
        try:
            if int(height) <= 0:
                raise ValueError

            conf["height"] = int(height)
            print("Height Value Changed to", conf["height"])
        except ValueError:
            print(f"Invalid Height Value. Using Default Value={conf['height']}")

    dpi = input("\nDPI of the QR Code: (Enter for Default): ")
    if dpi:
        try:
            if int(dpi) <= 0:
                raise ValueError

            conf["dpi"] = int(dpi)
            print("DPI Value Changed to", conf["dpi"])
        except ValueError:
            print(f"Invalid DPI Value. Using Default Value={conf['dpi']}")

    print_heading("Final Configuration")
    pprint.pprint(conf, indent=4, sort_dicts=True)
    print("\n")

    print_heading("Generating QR Codes")

    generate_qr_codes(conf)

    if IS_FROZEN:
        print("Execution Complete... Press Enter to Close this window.")
        input()


if __name__ == "__main__":
    if IS_FROZEN:
        freeze_support()

    main()
