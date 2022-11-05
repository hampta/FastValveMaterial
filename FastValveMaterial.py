""" Simple Source Material "PBR" generator

Prerequisites (Python 3.x):
pillow, numpy


MIT License

Copyright (c) 2022 Marvin Friedrich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. """


import configparser
import math
import os
import shutil
import sys
import logging
from ctypes import create_string_buffer
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageOps

import VTFLibWrapper.VTFLib as VTFLib
import VTFLibWrapper.VTFLibEnums as VTFLibEnums

vtf_lib = VTFLib.VTFLib()
version = "221105"


class Config:
    def __init__(self) -> None:
        __config = configparser.ConfigParser()
        __config.read("config.ini")
        # Input
        self.input_format = __config["Input"]["Format"]
        self.input_scale = __config["Input"].getfloat("Scale")
        self.input_color = __config["Input"]["Color"]
        self.input_ao = __config["Input"]["AO"]
        self.input_normal = __config["Input"]["Normal"]
        self.input_metallic = __config["Input"]["Metallic"]
        self.input_roughness = __config["Input"]["Roughness"]
        self.input_path = __config["Input"]["Path"]
        #self.input_mat_format = __config["Input"]["MatFormat"]
        # Output
        self.output_path = __config["Output"]["Path"]
        self.midtone = __config["Output"].getint("Midtone")
        self.export_images = __config["Output"].getboolean("ExportImages")
        self.material_setup = __config["Output"]["MaterialSetup"]
        # Debug
        self.debug_messages = __config["Debug"].getboolean("DebugMessages")
        self.info_config = __config["Debug"].getboolean("PrintConfig")
        self.force_compression = __config["Debug"].getboolean(
            "ForceCompression")
        self.clear_exponent = __config["Debug"].getboolean("ClearExponent")
        self.metallic_factor = __config["Debug"].getint(
            "MetallicFactor") / 255 * 0.83
        self.material_proxies = __config["Debug"].getboolean("MaterialProxies")
        self.orm = __config["Debug"].getboolean("ORM")
        self.phongwarps = __config["Debug"].getboolean("Phongwarps")


config = Config()

handler = logging.StreamHandler(sys.stdout)
handler.terminator = "\r"

logging.basicConfig(level=logging.DEBUG if config.debug_messages else logging.INFO,
                    format='[FVM] [%(levelname)s] %(message)s', handlers=[handler])
logging.info(f"FastValveMaterial (v{version}" + ")\n")


# Check if a file in "path" starts with the desired "name" and ends with "ending"
def check_for_valid_files(path, name, ending):
    for file in os.listdir(path):
        # ? Works in theory, but is busted if materials start with the same prefix
        if file.endswith(ending) and file.startswith(name + ending):
            return file


def replace_list(string, list):
    for i in list:
        string = string.replace(i, "")
    return string


def find_material_names():  # Uses the color map to determine the current material name
    listStuff = []
    for file in os.listdir(config.input_path):
        # If file ends with "scheme.format
        # if file.endswith(f"{config.input_mat_format}.{config.input_format}"):
        if file.endswith(config.input_format):
            # Get rid of "scheme.format" to get the material name and append it to the list of all materials
            listStuff.append(replace_list(file, [f".{config.input_format}", config.input_color,
                             config.input_ao, config.input_normal, config.input_metallic, config.input_roughness]))
    return list(set(listStuff))


def do_diffuse(color_image: Image.Image, AOImage: Image.Image, metallicImage: Image.Image, glossinessImage: Image.Image, materialName):  # Generate Diffuse/Color map
    final_diffuse = color_image.convert("RGBA")
    if AOImage is None:
        final_diffuse = ImageChops.blend(final_diffuse.convert("RGB"), ImageChops.multiply(final_diffuse.convert(
            "RGB"), glossinessImage.convert("RGB")), 0.3).convert("RGBA")  # Combine diffuse and glossiness map
    else:
        final_diffuse = ImageChops.multiply(final_diffuse.convert("RGB"), AOImage.convert(
            "RGB")).convert("RGBA")  # Combine diffuse and occlusion map
    # Split diffuse image into channels to modify alpha
    r, g, b, a = final_diffuse.split()
    # * I think i forgot to remove some excess conversion but i literally cannot be asked to do so
    # Blend the alpha channel with metalImage
    a = Image.blend(color_image.convert(
        "L"), metallicImage.convert("L"), config.metallic_factor)
    a = a.convert("L")  # Convert back to Linear
    color_spc = (r, g, b, a)
    # Merge all channels together
    final_diffuse = Image.merge("RGBA", color_spc)
    logging.info("Exporting Diffuse...\n")
    export_texture(final_diffuse, f'{materialName}_c.vtf', 'DXT5')
    if os.path.exists(f'{config.output_path}/{materialName}_c.vtf'):
        logging.debug("Diffuse already exists, replacing!\n")
        src = os.path.join(os.getcwd(), f"{materialName}_c.vtf")
        dst = os.path.join(
            os.getcwd(), f"{config.output_path}{materialName}_c.vtf")
        shutil.copyfile(src, dst, follow_symlinks=True)
        os.remove(os.path.join(os.getcwd(), f"{materialName}_c.vtf"))
    else:
        Path(config.output_path).mkdir(parents=True, exist_ok=True)
        shutil.move(f'{materialName}_c.vtf', os.path.join(
            os.getcwd(), config.output_path))
        logging.debug("Diffuse exported\n")


def do_exponent(glossinessImage, materialName):  # Generate the exponent map
    finalExponent = glossinessImage.convert("RGBA")
    r, g, b, a = finalExponent.split()
    layerImage = Image.new(
        'RGBA', [finalExponent.size[0], finalExponent.size[1]], (0, 217, 0, 100))
    blackImage = Image.new(
        'RGBA', [finalExponent.size[0], finalExponent.size[1]], (0, 0, 0, 100))
    finalExponent = Image.blend(finalExponent, layerImage, 0.5)
    g = g.convert('RGBA')
    b = b.convert('RGBA')
    g = Image.blend(g, layerImage, 1)
    b = Image.blend(b, blackImage, 1)
    g = g.convert('L')
    b = b.convert('L')
    if config.clear_exponent:
        g = Image.new('L', [finalExponent.size[0], finalExponent.size[1]], 255)
    colorSpc = (r, g, b, a)
    finalExponent = Image.merge('RGBA', colorSpc)
    logging.info("Exporting Exponent...\n")
    export_texture(finalExponent, f'{materialName}_m.vtf',
                   'DXT5' if config.force_compression else 'DXT1')
    try:
        Path(config.output_path).mkdir(parents=True, exist_ok=True)
        shutil.move(f'{materialName}_m.vtf', config.output_path)
        logging.debug("Exponent exported\n")
    except Exception as e:
        logging.debug("Exponent already exists, replacing!\n")
        shutil.copyfile(os.path.join(os.getcwd(), f"{materialName}_m.vtf"), os.path.join(
            os.getcwd(), config.output_path + materialName + "_m.vtf"), follow_symlinks=True)
        os.remove(os.path.join(os.getcwd(), f"{materialName}_m.vtf"))


def do_normal(config_midtone, normalmapImage: Image.Image, glossinessImage: Image.Image, materialName):  # Generate the normal map
    finalNormal = normalmapImage.convert('RGBA')
    finalGloss = glossinessImage.convert('RGBA')
    row = finalGloss.size[0]
    col = finalGloss.size[1]
    for x in range(1, row):
        logging.info(f"Normal conversion: ({math.ceil(x / row * 100)}%)")
        for y in range(1, col):
            value = do_gamma(x, y, finalGloss, config_midtone)
            finalGloss.putpixel((x, y), value)
    r, g, b, a = finalNormal.split()
    finalGloss = finalGloss.convert('L')
    a = Image.blend(a, finalGloss, 1)
    a = a.convert('L')
    colorSpc = (r, g, b, a)
    finalNormal = Image.merge('RGBA', colorSpc)
    if config.export_images:
        finalNormal.save(f'{materialName}_n.tga', 'TGA')
    logging.info("Exporting Normal Map...\n")
    export_texture(finalNormal, f'{materialName}_n.vtf',
                   'DXT5' if config.force_compression else 'RGBA8888')
    try:
        Path(config.output_path).mkdir(parents=True, exist_ok=True)
        shutil.move(f'{materialName}_n.vtf', config.output_path)
        # Spaces are needed in order to overwrite the progress count, otherwise about 4 chars will stay on screen
        logging.debug("Normal exported\n")
    except Exception as e:
        logging.debug("Normal already exists, replacing!\n")
        shutil.copyfile(os.path.join(os.getcwd(), f"{materialName}_n.vtf"), os.path.join(
            os.getcwd(), config.output_path + materialName + "_n.vtf"), follow_symlinks=True)
        os.remove(os.path.join(os.getcwd(), f"{materialName}_n.vtf"))


def do_gamma(x, y, im, mt):  # Change the gamma of the given channels of "im" at a given xy coordinate to "config.midtone", similar to how photoshop does it
    gamma = 1
    midToneNormal = mt / 255
    if mt < 128:
        midToneNormal = midToneNormal * 2
        gamma = 1 + (9 * (1 - midToneNormal))
        gamma = min(gamma, 9.99)
    elif mt > 128:
        midToneNormal = (midToneNormal * 2) - 1
        gamma = 1 - midToneNormal
        gamma = max(gamma, 0.01)
    gamma_correction = 1 / gamma
    (r, g, b, a) = im.getpixel((x, y))
    if mt != 128:
        # ! no clue what this does i copied it from stack overflow
        r = 255 * (pow((r / 255), gamma_correction))
        g = 255 * (pow((g / 255), gamma_correction))
        b = 255 * (pow((b / 255), gamma_correction))
    r = math.ceil(r)
    g = math.ceil(g)
    b = math.ceil(b)
    return (r, g, b, a)


# Resize the target image to be the same as rgbIm (needed for normal maps)
def fix_scale_mismatch(rgbIm: Image.Image, target: Image.Image):
    factor = rgbIm.height / target.height
    return ImageOps.scale(target, factor)


def do_material(materialName):  # Create a material with the given image names
    logging.debug(f"Creating material '{materialName}'\n")
    proxies = ""
    phong = ""
    if config.material_proxies:
        proxies = ['\n\t"Proxies"',
                   '\n\t{',
                   '\n\t\t"MwEnvMapTint"',
                   '\n\t\t{',
                   '\n\t\t\t"min" "0"',
                   '\n\t\t\t"max" "0.015"',
                   '\n\t\t}',
                   '\n\t}']
    if config.phongwarps:
        phong = '\n\t"$phongwarptexture" "' + config.output_path + 'phongwarp_steel"'
    else:
        '\n\t"$PhongFresnelRanges" "[ 4 3 10 ]"'
    writer = [f'// Generated by FastValveMaterial v{version}',
              f'\n// METALNESS: "{config.metallic_factor * 255}" GAMMA: "{config.midtone}"',
              '\n"VertexLitGeneric"',
              '\n{', f'\n\t"$basetexture" "{config.output_path}{materialName}_c"',
              f'\n\t"$bumpmap" "{config.output_path}{materialName}_n"',
              f'\n\t"$phongexponenttexture" "{config.output_path}{materialName}_m"',
              '\n\t"$color2" "[ .1 .1 .1 ]"',
              '\n\t"$blendtintbybasealpha" "1"',
              '\n\t"$phong" "1"',
              '\n\t"$phongboost" "10"',
              '\n\t"$phongalbedotint" "1"',
              phong,
              '\n\t"$envmap" "env_cubemap"',
              '\n\t"$basemapalphaenvmapmask" "1"',
              '\n\t"$envmapfresnel" "0.4"',
              '\n\t"$envmaptint" "[ .1 .1 .1 ]"']
    proxies += '\n}'
    writer += proxies
    try:
        Path(config.output_path).mkdir(parents=True, exist_ok=True)
        with open(f"{materialName}.vmt", 'w') as f:
            f.writelines(writer)
        shutil.move(f'{materialName}.vmt', config.output_path)
        shutil.copy("phongwarp_steel.vtf", config.output_path)
        # ? Spaces are needed in order to overwrite the progress count, otherwise about 4 chars will stay on screen (?????)
        logging.debug("Material exported\n")
    except Exception as e:
        logging.debug("Material already exists, replacing!\n")
        shutil.copy("phongwarp_steel.vtf", config.output_path)
        shutil.copyfile(os.path.join(os.getcwd(), f"{materialName}.vmt"), os.path.join(
            os.getcwd(), config.output_path + materialName + ".vmt"), follow_symlinks=True)
        os.remove(os.path.join(os.getcwd(), f"{materialName}.vmt"))


def do_nrm_material(materialName):
    logging.debug(f"Creating NRM material '{materialName}' \n")
    proxies = ""
    if config.material_proxies:
        proxies = ['\n\t"Proxies"',
                   '\n\t{',
                   '\n\t\t"MwEnvMapTint"',
                   '\n\t\t{',
                   '\n\t\t\t"min" "0"',
                   '\n\t\t\t"max" "0.015"',
                   '\n\t\t}',
                   '\n\t}']
    writer = [f'// Generated by FastValveMaterial v{version}',
              '\n// NORMALIZED MATERIAL!' '\n"VertexLitGeneric"',
              '\n{',
              f'\n\t"$basetexture" "{config.output_path}{materialName} _c"',
              f'\n\t"$bumpmap" "{config.output_path}{materialName}_n"',
              f'\n\t"$phongexponenttexture" "{config.output_path}{materialName} _m"',
              '\n\t"$phong" "1"',
              '\n\t"$phongboost" "1"',
              '\n\t"$color2" "[ 0 0 0 ]"',
              '\n\t"$phongexponent"    "24"',
              '\n\t"$phongalbedotint" "1"',
              '\n\t"$additive"    "1"',
              '\n\t"$PhongFresnelRanges" "[ 2 4 6 ]"']
    proxies += '\n}'
    writer += proxies
    try:
        Path("materials/").mkdir(parents=True, exist_ok=True)
        with open(f"{materialName}_s.vmt", 'w') as f:
            f.writelines(writer)
        shutil.move(f'{materialName}_s.vmt', "materials/")
    except Exception as e:
        logging.debug("Normalized material already exists, replacing!\n")
        shutil.copyfile(os.path.join(os.getcwd(), f"{materialName}_s.vmt"), os.path.join(
            os.getcwd(), config.output_path + materialName + "_s.vmt"), follow_symlinks=True)
        os.remove(os.path.join(os.getcwd(), f"{materialName}_s.vmt"))


# Exports an image to VTF using VTFLib
def export_texture(texture, path, imageFormat=None):
    image_data = (np.asarray(texture)*-1) * 255
    image_data = image_data.astype(np.uint8, copy=False)
    def_options = vtf_lib.create_default_params_structure()
    if imageFormat.startswith('RGBA8888'):
        def_options.ImageFormat = VTFLibEnums.ImageFormat.ImageFormatRGBA8888
        def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha
        if imageFormat == 'RGBA8888Normal':
            def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagNormal
    elif imageFormat.startswith('DXT1'):
        def_options.ImageFormat = VTFLibEnums.ImageFormat.ImageFormatDXT1
        if imageFormat == 'DXT1Normal':
            def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagNormal
    elif imageFormat.startswith('DXT5'):
        def_options.ImageFormat = VTFLibEnums.ImageFormat.ImageFormatDXT5
        def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha
        if imageFormat == 'DXT5Normal':
            def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagNormal
    else:
        def_options.ImageFormat = VTFLibEnums.ImageFormat.ImageFormatRGBA8888
        def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha

    def_options.Resize = 1
    w, h = texture.size
    image_data = create_string_buffer(image_data.tobytes())
    vtf_lib.image_create_single(w, h, image_data, def_options)
    vtf_lib.image_save(path)
    vtf_lib.image_destroy()


# /////////////////////
# Main loop
# /////////////////////
def main():
    for materialName in find_material_names():  # For every material in the input folder
        logging.debug("Loading:\n")
        try:
            logging.debug(f"Material:\t{materialName}\n")
            # Set the paths to the textures based on the config file
            if config.orm:
                colorSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_color}.{config.input_format}")}'
                aoSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_roughness}.{config.input_format}")}'
                normalSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_normal}.{config.input_format}")}'
                metalSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_roughness}.{config.input_format}")}'
                glossSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_roughness}.{config.input_format}")}'
            else:
                colorSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_color}.{config.input_format}")}'
                if config.input_ao != '':  # If a map is set
                    aoSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_ao}.{config.input_format}")}'
                if config.input_normal != '':
                    normalSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_normal}.{config.input_format}")}'
                if config.input_roughness != '':
                    glossSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_roughness}.{config.input_format}")}'
                if config.input_metallic != '':
                    metalSt = f'{config.input_path}/{check_for_valid_files(config.input_path, materialName, f"{config.input_metallic}.{config.input_format}")}'
        except FileNotFoundError:
            logging.debug(f"[ERROR] v{version}" +
                          " terminated with exit code -1:\nCouldn't locate files with correct naming scheme, throwing FileNotFoundError!\n")
            sys.exit()

        if not config.orm:
            logging.info(f"Color:\t\t{colorSt}\n")
            if config.input_ao != '':
                logging.info(f"Occlusion:\t\t{aoSt}\n")
            else:
                logging.info("Occlusion:\t\t None given, ignoring!\n")
            if config.input_normal != '':
                logging.info(f"Normal:\t\t{normalSt}\n")
            else:
                logging.info("Normal:\t\t None given, ignoring!\n")
            if config.input_metallic != '':
                logging.info(f"Metalness:\t\t{metalSt}\n")
            else:
                logging.info("Metalness:\t\t None given, ignoring!\n")
            if config.input_roughness != '':
                logging.info(f"Glossiness:\t{glossSt}\n")
            else:
                logging.info("Glossiness:\t\tNone given, ignoring!\n\n")

            colorImage = Image.open(colorSt)
            colorImage = colorImage.resize((int(colorImage.width * config.input_scale),
                                            int(colorImage.height * config.input_scale)),
                                           Image.Resampling.LANCZOS)

            if config.input_ao != '':
                aoImage = Image.open(aoSt)
                aoImage = aoImage.resize((int(aoImage.width * config.input_scale),
                                          int(aoImage.height * config.input_scale)),
                                         Image.Resampling.LANCZOS)
            else:
                # If no AO image is given, use a white image
                aoImage = Image.new(
                    'RGB', (colorImage.width, colorImage.height), (255, 255, 255))

            if config.input_normal != '':
                normalImage = Image.open(normalSt)
                normalImage = normalImage.resize((int(normalImage.width * config.input_scale),
                                                  int(normalImage.height * config.input_scale)),
                                                 Image.Resampling.LANCZOS)
            else:
                raise FileNotFoundError()  # Couldn't find a normal map

            if config.input_metallic != '':
                metalImage = Image.open(metalSt)
                metalImage = metalImage.resize((int(metalImage.width * config.input_scale),
                                                int(metalImage.height * config.input_scale)),
                                               Image.Resampling.LANCZOS)
            else:
                # If no Metalness image is given, use a black image
                metalImage = Image.new(
                    'RGB', (colorImage.width, colorImage.height), (0, 0, 0))

            if config.input_roughness != '':
                glossImage = Image.open(glossSt)
                glossImage = glossImage.resize((int(glossImage.width * config.input_scale),
                                                int(glossImage.height * config.input_scale)),
                                               Image.Resampling.LANCZOS)
            else:
                # If no Gloss image is given, use a white image
                glossImage = Image.new(
                    'RGB', (colorImage.width, colorImage.height), (255, 255, 255))

            if config.material_setup == "rough":
                glossImage = ImageOps.invert(glossImage.convert('RGB'))
            aoImage = fix_scale_mismatch(normalImage, aoImage)
            metalImage = fix_scale_mismatch(normalImage, metalImage)
            colorImage = fix_scale_mismatch(normalImage, colorImage)
            glossImage = fix_scale_mismatch(normalImage, glossImage)

            if config.input_ao != '':
                do_diffuse(colorImage, aoImage, metalImage,
                           glossImage, materialName)
            else:
                do_diffuse(colorImage, None, metalImage,
                           glossImage, materialName)

        else:
            logging.info(f"Color:\t\t {colorSt}\n")
            logging.info(f"ORM:\t\t {metalSt}\n")
            logging.info(f"Normal:\t\t{normalSt}\n")

            colorImage = Image.open(colorSt)
            ormImage = Image.open(metalSt)
            try:
                (r, g, b) = ormImage.split()
            except Exception:
                logging.info(
                    "ERROR: Could not convert color bands on ORM! (Do you have empty image channels?)\n")
            aoImage = r
            glossImage = ImageOps.invert(g.convert('RGB'))
            metalImage = b
            normalImage = Image.open(normalSt)
            do_diffuse(colorImage, aoImage, metalImage, glossImage)
        do_exponent(glossImage, materialName)
        do_normal(config.midtone, normalImage, glossImage, materialName)

        if(config.clear_exponent):
            do_nrm_material(materialName)
        else:
            do_material(materialName)
        logging.info(
            f" Conversion for material '{materialName}' finished, files saved to '{config.output_path}'\n")


if __name__ == "__main__":
    main()
    logging.debug(
        f"v{version} finished with exit code 0: All conversions finished.\n")
    if(config.info_config):
        logging.debug("Config file dump:\n")
        logging.debug(config)
