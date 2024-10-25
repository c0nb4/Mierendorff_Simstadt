import os
import logging
import xml.etree.ElementTree as ET

def merge_gml_files(gml_files, output_file):
    """
    Merges multiple GML files into a single GML file.

    Parameters:
        gml_files (list of str): List of file paths to the GML files to be merged.
        output_file (str): The file path for the merged output GML.
    """
    if len(gml_files) < 2:
        raise ValueError("At least two GML files are required for merging.")
    
    # Parse the first file to use it as the base for merging
    tree = ET.parse(gml_files[0])
    root = tree.getroot()
    
    # Iterate through the rest of the files and append their content to the root
    for gml_file in gml_files[1:]:
        other_tree = ET.parse(gml_file)
        other_root = other_tree.getroot()
        
        # Append each child element of the other root to the main root
        for elem in other_root:
            root.append(elem)
    
    # Write the merged content to the output file
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    import shutil

    input_folder = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\gml_data'
    output_folder = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\gml_data'
    try:
        # Create backup folder
        input_folder_backup = os.path.join(input_folder, 'changed_use_type')
        if not os.path.exists(input_folder_backup):
            shutil.copytree(input_folder, input_folder_backup)
            
        # Create output folder for merged file
        output_folder = os.path.join(output_folder, 'one_file')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            
        # Get list of GML files from input backup folder
        gml_files = [os.path.join(input_folder_backup, file) for file in os.listdir(input_folder_backup) if file.endswith('.xml')]
        
        if not gml_files:
            raise ValueError("No GML files found in input folder")
            
        # Create output file path
        output_file = os.path.join(output_folder, "merged_output.gml")
        
        # Merge the files
        merge_gml_files(gml_files, output_file)
        print(f"Merged GML files saved to {output_file}")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")