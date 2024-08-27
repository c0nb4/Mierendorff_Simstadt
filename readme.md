## Mierendorff Simstadt 

This repo contains code and data to model, simulate and evaluate the Mierendorffinsel in Berlin, Germany with [Simstadt](https://simstadt.hft-stuttgart.de/).

## How to use 

The python script 'insert_attributes.py'can add attributes to CityGML files of the bldg and the gen type. The csv files need to have the following structure to be valid:

| BuildingID       | yearOfConstruction | function | comment                    |
|------------------|--------------------|----------|----------------------------|
| attribute_type   | bldg               | bldg     | gen                        |
| DEBW_LOD2_2960   | 1978               | 1010     | Some old residential building |
| DEBW_LOD2_2869   | 2017               | 2020     | Recent office building     |

The python script 'transform_weather.py' transforms an .epw input file into a TMY3 format file for Simstadt. 

The python script 'change_use_type.py' transforms the CityGML use type to one needed for SimStadt. 


## Data and Auxillary files 

All code for simulation is wihin the "SimStadt" folder. If you open the folder with SimStadt, the resepctive workflows can be run. 

## Contact 

For any information or inquires reach out to [Felix Rehmann](mailto:Rehmann@tu-berlin.de).
