"""
This script extracts polygons from a GML file and
and merges them with spatial data from a shapefile 
based on the groundsurface.

Code taken from: https://github.com/TUB-DVG/TECDEM
"""

import os
import argparse
import geopandas as gpd
import shapely.geometry as geom
import xml.etree.ElementTree as ET
import pandas as pd

# Define the namespaces (you may need to adjust these based on your GML file)
ns = {
    'gml': 'http://www.opengis.net/gml',
    'bldg': 'http://www.opengis.net/citygml/building/2.0'
}

def get_3dPosList_from_str(text):
    """
    Function from: https://gitlab.e3d.rwth-aachen.de/e3d-software-tools/cityldt/-/blob/main/string_manipulation.py?ref_type=heads 
    """
    coor_list = [float(x) for x in text.split()]
    coor_list = [list(x) for x in zip(coor_list[0::3], coor_list[1::3], coor_list[2::3])]  # creating 2d coordinate array from 1d array
    return coor_list

def getGroundSurfaceCoorOfBuild(element, nss):
    """returns the ground surface coor form element"""
    # LoD0
    if element:
        for tagName in ['bldg:lod0FootPrint', 'bldg:lod0RoofEdge']:
            LoD_zero_E = element.find(tagName, nss)
            if LoD_zero_E is not None:
                posList_E = LoD_zero_E.find('.//{*}gml:posList', nss)
                if posList_E is not None:
                    return get_3dPosList_from_str(posList_E.text)
                else:
                    pos_Es = LoD_zero_E.findall('.//{*}gml:pos', nss)
                    polygon = []
                    for pos_E in pos_Es:
                        polygon.append(pos_E.text)
                    polyStr = ' '.join(polygon)
                    return get_3dPosList_from_str(polyStr)

        groundSurface_E = element.find('.//{*}boundedBy/.//{*}GroundSurface', nss)
        if groundSurface_E is not None:
            posList_E = groundSurface_E.find('.//gml:posList', nss)
            if posList_E is not None:
                return get_3dPosList_from_str(posList_E.text)
            else:
                pos_Es = groundSurface_E.findall('.//gml:pos', nss)
                polygon = []
                for pos_E in pos_Es:
                    polygon.append(pos_E.text)
                polyStr = ' '.join(polygon)
                return get_3dPosList_from_str(polyStr)
        else:
            geometry = element.find('bldg:lod1Solid', nss)
            if geometry is not None:
                poly_Es = geometry.findall('.//gml:Polygon', nss)
                all_poylgons = []
                for poly_E in poly_Es:
                    polygon = []
                    posList_E = element.find('.//gml:posList', nss)
                    if posList_E is not None:
                        polyStr = posList_E.text
                    else:
                        pos_Es = poly_E.findall('.//gml:pos', nss)
                        for pos_E in pos_Es:
                            polygon.append(pos_E.text)
                        polyStr = ' '.join(polygon)
                    coor_list = get_3dPosList_from_str(polyStr)
                    all_poylgons.append(coor_list)
                averages = []
                for polygon in all_poylgons:
                    average = 0
                    for i in range(len(polygon)-1):
                        average -=- polygon[i][2]
                    averages.append(average/(len(polygon)-1))
                return all_poylgons[averages.index(min(averages))]
            else:
                return ''
    else:
        return ''

def extract_polygons_with_ids(gml_file):
    temp_data = []
    tree = ET.parse(gml_file)
    root = tree.getroot()
    for building in root.findall('.//{*}Building'):
        building_id = building.get('{http://www.opengis.net/gml}id')
        bp_gC = getGroundSurfaceCoorOfBuild(building, ns)
        bp_gC_2d = [(x, y) for x, y, z in bp_gC]
        polygon = geom.Polygon(bp_gC_2d)
        temp_data.append({
            'geometry': polygon, 
            'coordinates': bp_gC,
            'gml_id': building_id, 
            'building_part_id': ""
        })

        for co_bp_E in building.findall('.//{*}consistsOfBuildingPart', ns):
            bp_E = co_bp_E.find('.//{*}BuildingPart', ns)
            bp_gC = getGroundSurfaceCoorOfBuild(bp_E, ns)
            building_part_id = bp_E.get('{http://www.opengis.net/gml}id')
            bp_gC_2d = [(x, y) for x, y, z in bp_gC]
            polygon = geom.Polygon(bp_gC_2d)

            temp_data.append({
                'geometry': polygon, 
                'coordinates': bp_gC,
                'gml_id': building_id, 
                'building_part_id': building_part_id
            })
    
    df = pd.DataFrame(temp_data)

    return df

def average_year_from_range(year_range):
    # This function extracts the start and end years from a range, calculates the average, and returns it as an integer
    # "gemischte"
    if isinstance(year_range, str):
        if '-' in year_range:
            start_year, end_year = year_range.split('-')
            average_year = (int(start_year) + int(end_year)) // 2
            return average_year
        elif year_range == "gemischte Baualtersklasse":
            return None 
        elif year_range == "bis 1900": 
            return 1900
        elif year_range == "NaN":
            return None 
    if isinstance(year_range, float):
        if year_range == "":
            return ""
        else:
            return ""
    return int(year_range)  # Handles cases where the year is not a range but a single year

if __name__ == '__main__':
    #parser = argparse.ArgumentParser(description='Extract polygons from GML files and merge with spatial data from shapefile.')
    #parser.add_argument('gml_files', nargs='+', help='List of GML files to process.')
    #parser.add_argument('--shape_data_path', required=True, help='Path to the shapefile data.')
    #parser.add_argument('--block_shape_path', required=True, help='Path to the block shape file.')
    #parser.add_argument('--output_dir', required=True, help='Directory to save the resulting CSV files.')

    #args = parser.parse_args()
    shape_data_path = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\berlin_shape\00_block_shape.shp'
    gml_folder_path = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\gml_data'
    file_path_age = r'berlin_shape\02_Gebäudealter.csv'

    #shape_data_path = args.shape_data_path
    shapes = gpd.read_file(shape_data_path)
    shapes["blknr"] = shapes["blknr"].astype('int64')

    age_df = pd.read_csv(file_path_age)
    bldg_age_shapes = shapes.merge(age_df, on='blknr')

    for gml_file in os.listdir(gml_folder_path):
        if not gml_file.endswith('.gml') and not gml_file.endswith('.xml'):
            print(f"Skipping {gml_file} as it is not a GML file.")
            continue
        else: 
            gml_file_path = os.path.join(gml_folder_path, gml_file)
            df = extract_polygons_with_ids(gml_file_path)
            print(df.head())
            gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=shapes.crs)
            within_blocks = gpd.sjoin(gdf, bldg_age_shapes, how='inner', predicate='intersects')
            within_blocks["year"] = within_blocks.apply(lambda row: average_year_from_range(row['ueberw_dek']), axis=1)

            # Drop duplicates based on gml_id, keeping only the first occurrence
            within_blocks = within_blocks.drop_duplicates(subset='gml_id', keep='first')

            output_csv_path = os.path.join(gml_folder_path, os.path.splitext(os.path.basename(gml_file))[0] + '.csv')
            
               # Create the subset DataFrame
            subset_df = within_blocks[['gml_id', 'year']].copy()
            subset_df.columns = ['BuildingID', 'yearOfConstruction']

            # Delete values where no year of construction
            subset_df = subset_df[subset_df['yearOfConstruction'].notna() & (subset_df['yearOfConstruction'] != '')]

            # Add the attribute type row
            attribute_type_row = pd.DataFrame([{
                'BuildingID': 'attribute_type',
                'yearOfConstruction': 'bldg'
            }])
            subset_df = pd.concat([attribute_type_row, subset_df], ignore_index=True)

            output_csv_path = os.path.join(gml_folder_path, os.path.splitext(os.path.basename(gml_file))[0] + '.csv')
            subset_df.to_csv(output_csv_path, index=False)