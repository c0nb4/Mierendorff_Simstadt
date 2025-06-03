import os
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict

def analyze_gml_attributes(directory_path):
    # Dictionary to store attribute counts
    attribute_counts = defaultdict(int)
    total_files = 0
    buildings = 0
    building_parts = 0
    
    # Walk through directory and process all .gml files
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.gml'):
                total_files += 1
                file_path = os.path.join(root, file)
                
                try:
                    # Parse GML file
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    
                    # Find all buildings and building parts
                    for building in root.findall('.//{*}Building'):
                        buildings += 1
                        # Count attributes for the building
                        for attr_name in building.attrib:
                            attribute_counts[attr_name] += 1
                            
                        # Count string attributes
                        for string_attr in building.findall('.//{*}stringAttribute'):
                            attr_name = string_attr.get('name')
                            if attr_name:
                                attribute_counts[attr_name] += 1
                            
                        # Count attributes for building parts
                        for building_part in building.findall('.//{*}BuildingPart'):
                            # Count attributes for the building
                            building_parts += 1
                            for attr_name in building_part.attrib:
                                attribute_counts[attr_name] += 1
                                
                            # Count string attributes in building parts
                            for string_attr in building_part.findall('.//{*}stringAttribute'):
                                attr_name = string_attr.get('name')
                                if attr_name:
                                    attribute_counts[attr_name] += 1
                                    
                            # Count all direct child elements
                            for child in building_part:
                                tag = child.tag.split('}')[-1]  # Remove namespace
                                attribute_counts[tag] += 1
                            
                except ET.ParseError as e:
                    print(f"Error parsing {file_path}: {e}")
                    continue
    
    # Calculate percentages
    results = {}
    for attr, count in attribute_counts.items():
        percentage = (count / (buildings + building_parts)) * 100
        results[attr] = {
            'count': count,
            'percentage': percentage
        }
    
    return results, total_files

def main():
    # Directory containing GML files
    directory = r"C:\Users\felix\Programmieren\Mierendorff_Simstadt\gml_data\one_file"
    
    # Analyze attributes
    results, total_files = analyze_gml_attributes(directory)
    
    # Print results
    print(f"\nAnalyzed {total_files} GML files")
    print("\nAttribute Statistics:")
    print("-" * 50)
    
    # Sort results by percentage in descending order
    sorted_results = sorted(results.items(), key=lambda x: x[1]['percentage'], reverse=True)
    
    for attr, stats in sorted_results:
        print(f"{attr}:")
        print(f"  Count: {stats['count']}")
        print(f"  Percentage: {stats['percentage']:.2f}%")
        print("-" * 50)

if __name__ == "__main__":
    main()
