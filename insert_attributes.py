#!/usr/bin/env python
# coding: utf-8

#   usage: inject_citygml_attributes.py [-h] [input_folder] [output_folder]
#   Inject building attributes or generic attributes into CityGML files.
#   code original taken from https://simstadt.hft-stuttgart.de/advanced-topics/python-scripts/ 
#   and modified and updated
#   Each CityGML file inside input_folder should have a corresponding spreadsheet,
import os
import time
import logging
from pathlib import Path
from lxml import etree
import pandas as pd
import numpy as np

logging.basicConfig(format='%(levelname)s: %(message)s')
logging.getLogger().setLevel(logging.INFO)

# NOTE: ods format requires odfpy package
ALLOWED_SPREADSHEET_FORMATS = ['.xls', '.xlsx', '.ods', '.csv']


def create_dir_if_needed(path):
    if not path.exists():
        logging.info(f"Creating '{path}' folder.")
        path.mkdir()


def get_attribute_if_present(building: etree._Element, attribute: str):
    # NOTE: Attributes can be in BuildingPart too
    for elem in building.findall('.//'):
        if attribute in elem.tag and elem.text and len(elem.text) > 0:
               return elem
    return None


def get_namespaces(gml_root):
    return {k: v for k, v in gml_root.nsmap.items() if k}


def fill_building_or_building_part_with_attributes(building_or_building_part, df, namespaces):
    gml_id = building_or_building_part.get("{http://www.opengis.net/gml}id")
    # check if gml_id present in excel in table
    if not (gml_id is None) and (gml_id in df.index.values):
        for attribute in df.columns:
            if df.loc['attribute_type', attribute].lower() in ('bldg', 'building'):
                append_citygml_building_attribute(
                    building_or_building_part, attribute, df, namespaces['bldg'])
            elif df.loc['attribute_type', attribute].lower() in ('gen', 'generic'):
                insert_generic_attribute(
                    building_or_building_part, attribute, df, namespaces['gen'])


def append_citygml_building_attribute(building_or_building_part, attribute, df, building_namespace):
    gml_id = building_or_building_part.get("{http://www.opengis.net/gml}id")
    # if the attribute is given in excel table
    if not (df.loc[gml_id, attribute] is None
            or pd.isnull(df.loc[gml_id, attribute])):
        logging.debug("%s.%s = %r (%s)" % (
            gml_id, attribute, df.loc[gml_id, attribute], type(df.loc[gml_id, attribute]).__name__))
        # ... and if buiding has not already this attribute in the gml file
        existing_attribute = get_attribute_if_present(building_or_building_part, attribute)
        if existing_attribute is not None:
            logging.warning("  %s.%s : Already present" % (gml_id, attribute))
        else:
            # Then add attribute at the end of the building element
            xmlsnip = f'<{attribute} xmlns="{building_namespace}"></{attribute}>\n'
            attr = etree.fromstring(xmlsnip, etree.XMLParser())
            attr.text = str(df.loc[gml_id, attribute])
            # building attributes must be at the end
            building_or_building_part.append(attr)
            logging.debug("  Changed!")


def insert_generic_attribute(building_or_building_part, attribute, df, generic_namespace):
    gml_id = building_or_building_part.get("{http://www.opengis.net/gml}id")
    # if the attribute is given in excel table
    if not (df.loc[gml_id, attribute] is None):
        attr_value = df.loc[gml_id, attribute]
        if isinstance(attr_value, str) or not np.isnan(df.loc[gml_id, attribute]):
            # ... and if building has not already this attribute in the gml file
            if get_attribute_if_present(building_or_building_part, attribute) is None:
                # Then add attribute at the end of the building element
                attr = (f'<stringAttribute xmlns="{generic_namespace}" name="{attribute}">'
                        f'<value xmlns="{generic_namespace}">{attr_value}</value></stringAttribute>\n')
                # generic attributes must be at the beginning
                building_or_building_part.insert(0, etree.fromstring(attr))


def indent_xml(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_xml(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def process(df, gml_path, output_folder):
    gml_filename = gml_path.name

    logging.info(f"## Processing file {gml_path}...")

    gml_tree = etree.parse(str(gml_path))
    gml_root = gml_tree.getroot()
    namespaces = get_namespaces(gml_root)

    for i, building in enumerate(gml_root.findall('.//bldg:Building', namespaces), 1):
        fill_building_or_building_part_with_attributes(
            building, df, namespaces)
        # look for buildingParts
        for building_part in building.findall('.//bldg:BuildingPart', namespaces):
            fill_building_or_building_part_with_attributes(
                building_part, df, namespaces)

        if i % 250 == 0:
            logging.debug(".")

    new_citygml = etree.ElementTree(gml_root)
    indent_xml(gml_root)

    new_citygml.write(str(output_folder / gml_filename),
                      pretty_print=True, xml_declaration=True, encoding='utf-8')

    logging.info(f"  Processed {i} buildings.")
    logging.info(f"  Finished writing {output_folder}/{gml_filename}.")


def parse_spreadsheet(filename):
    if not filename.is_file():
        # Possibly not a problem: different spreadsheets format are supported
        return
    # Dataframe from excel table
    if filename.suffix == '.csv':
        df = pd.read_csv(filename, sep=',')
    else:
        df = pd.read_excel(filename, header=0)
    df = df.set_index('BuildingID')

    # Remove rows if building id is not defined
    df = df[df.index.notnull()]

    # Make sure there are no duplicate rows
    duplicate_rows = df[df.index
                        .duplicated()].index
    if not duplicate_rows.empty:
        logging.error("Multiple rows with same building IDs are not allowed:\n" +
                      '\n'.join(duplicate_rows.array))
        return

    # Make sure ids are all strings, even if they look like integers.
    df.index = df.index.map(str)

    non_lowercase_attributes = [attribute for attribute in df
                                if not attribute[0].islower()]

    if len(non_lowercase_attributes) > 0:
        logging.error("Attributes should all start with a lower character." +
                      "Even comments should belong to a defined attribute column:\n" +
                      '\n'.join(non_lowercase_attributes))
        return
    return df


def save_csv_template(gml_path):
    csv_path = gml_path.with_suffix('.csv')
    gml_tree = etree.parse(str(gml_path))
    gml_root = gml_tree.getroot()
    with open(csv_path, 'w') as csv:
        csv.write("BuildingID;yearOfConstruction;function;comment\n")
        csv.write("attribute_type;bldg;bldg;gen\n")
        csv.write("building123456789;1234;1010;Fake building\n")
        #TODO: Check if year of construction already exists
        for building in gml_root.findall('.//{*}Building'):
            gml_id = building.get('{http://www.opengis.net/gml}id')
            csv.write(gml_id)
            csv.write(";")
            possible_year = get_attribute_if_present(building, 'yearOfConstruction')
            if possible_year is not None:
                csv.write(possible_year.text)
            csv.write(";")
            possible_function = get_attribute_if_present(building, 'function')
            if possible_function is not None:
                csv.write(possible_function.text)
            csv.write(";")
            csv.write("\n")

    logging.warning('%s has been written as template.' % csv_path)


def inject_attributes(input_folder, output_folder):
    input_folder = Path(input_folder)
    if not input_folder.exists():
        logging.error("'%s' folder does not exist." % input_folder)
        return
    logging.info("# Parsing every gml file inside '%s'" % input_folder)
    output_folder = Path(output_folder)
    create_dir_if_needed(output_folder)

    filenames = input_folder.glob("*.xml")
    if not filenames:
        filenames = input_folder.glob("*.gml")
    start_time = time.time()
    print(filenames)
    for gml_path in filenames:
        print(gml_path)
        dfs = [parse_spreadsheet(gml_path.with_suffix(ext))
               for ext in ALLOWED_SPREADSHEET_FORMATS]
        dfs = [df for df in dfs if df is not None]
        if len(dfs) > 1:
            logging.error(
                f'Too many spreadsheets have been found for {gml_path}')
        elif len(dfs) == 0:
            logging.warning('No spreadsheet (%s) has been found for %s' %
                            (', '.join(ALLOWED_SPREADSHEET_FORMATS), gml_path))
            save_csv_template(gml_path)
        else:
            process(dfs[0], gml_path, output_folder)

    logging.info("Finished all gml files in %.2f s." %
                 (time.time() - start_time))


if __name__ == '__main__':
    import shutil
    """import argparse

    parser = argparse.ArgumentParser(
        description=("Inject building attributes or generic attributes into CityGML files.\n"
                     "Each CityGML file inside input_folder should have a corresponding spreadsheet,\n"
                     "with the same filename as the CityGML but a different extension. (e.g. test.csv for test.gml).\n"
                     "If no spreadsheet is present, a CSV template will be automatically written, with the corresponding columns.\n"
                     "Supported formats : %s.\n" % ALLOWED_SPREADSHEET_FORMATS),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_folder", default='input', nargs='?',
                        help='Input folder, containing CityGML files and their corresponding spreadsheets. (default: input)')
    parser.add_argument("output_folder", default='output', nargs='?',
                        help='Output folder, in which the modified CityGML will be written. (default: output)')
    args = parser.parse_args()"""

    input_folder = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\gml_data'
    output_folder = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\gml_data'
    try:
        input_folder_backup = os.path.join(input_folder, 'backup')
        output_folder = os.path.join(output_folder, 'output')
        shutil.copytree(input_folder, input_folder_backup)
        inject_attributes(input_folder_backup, output_folder)
    except WindowsError as e:
        logging.info(e)
        logging.error("An error occurred. Please check the logs.")
        inject_attributes(input_folder_backup, output_folder)