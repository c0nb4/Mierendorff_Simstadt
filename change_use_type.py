import os
from pathlib import Path
from lxml import etree


def change_use_type(input_folder: str, output_folder: str):
    for file in os.listdir(input_folder):
        if file.endswith('.gml') or file.endswith('.xml'):
            file_path = os.path.join(input_folder, file)
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            for building in root.findall('.//{*}Building'):
                for function in building.iter('{http://www.opengis.net/citygml/building/1.0}function'):
                    if function.text:
                        function_parts = function.text.split('_')
                        if len(function_parts) > 1:
                            function.text = function_parts[1]

            output_file = os.path.join(output_folder, file)
            try:
                tree.write(output_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')
            except FileNotFoundError:
                os.makedirs(os.path.dirname(output_file))
                tree.write(output_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')


if __name__ == '__main__':
    input_folder = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\gml_data\output'
    output_folder = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\gml_data\changed_use_type'

    change_use_type(input_folder, output_folder=output_folder)