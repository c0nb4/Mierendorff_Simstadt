import os
import time
import logging
from pathlib import Path
from lxml import etree
import pandas as pd
import numpy as np

# Set up logging
logging.basicConfig(format='%(levelname)s: %(message)s')
logging.getLogger().setLevel(logging.INFO)

# epw format form https://github.com/RWTH-EBC/AixWeather/blob/main/aixweather/core_data_format_2_output_file/to_epw_energyplus.py
# See also: https://designbuilder.co.uk/cahelp/Content/EnergyPlusWeatherFileFormat.htm 
format_epw = {
    "Year": {"core_name": "", "unit": "year", "time_of_meas_shift": None, "nan": None},
    "Month": {"core_name": "", "unit": "month", "time_of_meas_shift": None, "nan": None},
    "Day": {"core_name": "", "unit": "day", "time_of_meas_shift": None, "nan": None},
    "Hour": {"core_name": "", "unit": "hour", "time_of_meas_shift": None, "nan": None},
    "Minute": {"core_name": "", "unit": "minute", "time_of_meas_shift": None, "nan": None},
    "Data Source and Uncertainty Flags": {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": "?"},
    "DryBulbTemp": {"core_name": "DryBulbTemp", "unit": "degC", "time_of_meas_shift": None, "nan": 99.9},
    "DewPointTemp": {"core_name": "DewPointTemp", "unit": "degC", "time_of_meas_shift": None, "nan": 99.9},
    "RelHum": {"core_name": "RelHum", "unit": "percent", "time_of_meas_shift": None, "nan": 999.0},
    "AtmPressure": {"core_name": "AtmPressure", "unit": "Pa", "time_of_meas_shift": None, "nan": 999999.0},
    "ExtHorRad": {"core_name": "ExtHorRad", "unit": "Wh/m2", "time_of_meas_shift": 'ind2prec', "nan": 9999.0},
    "ExtDirNormRad": {"core_name": "ExtDirNormRad", "unit": "Wh/m2", "time_of_meas_shift": 'ind2prec', "nan": 9999.0},
    "HorInfra": {"core_name": "HorInfra", "unit": "Wh/m2", "time_of_meas_shift": 'ind2prec', "nan": 9999.0},
    "GlobHorRad": {"core_name": "GlobHorRad", "unit": "Wh/m2", "time_of_meas_shift": 'ind2prec', "nan": 9999.0},
    "DirNormRad": {"core_name": "DirNormRad", "unit": "Wh/m2", "time_of_meas_shift": 'ind2prec', "nan": 9999.0},
    "DiffHorRad": {"core_name": "DiffHorRad", "unit": "Wh/m2", "time_of_meas_shift": 'ind2prec', "nan": 9999.0},
    "GlobHorIll": {"core_name": "GlobHorIll", "unit": "lux", "time_of_meas_shift": 'ind2prec', "nan": 999999.0},
    "DirecNormIll": {"core_name": "DirecNormIll", "unit": "lux", "time_of_meas_shift": 'ind2prec', "nan": 999999.0},
    "DiffuseHorIll": {"core_name": "DiffuseHorIll", "unit": "lux", "time_of_meas_shift": 'ind2prec', "nan": 999999.0},
    "ZenithLum": {"core_name": "ZenithLum", "unit": "Cd/m2", "time_of_meas_shift": 'ind2prec', "nan": 9999.0},
    "WindDir": {"core_name": "WindDir", "unit": "deg", "time_of_meas_shift": None, "nan": 999.0},
    "WindSpeed": {"core_name": "WindSpeed", "unit": "m/s", "time_of_meas_shift": None, "nan": 999.0},
    "TotalSkyCover": {"core_name": "TotalSkyCover", "unit": "1tenth", "time_of_meas_shift": None, "nan": 99},
    "OpaqueSkyCover": {"core_name": "OpaqueSkyCover", "unit": "1tenth", "time_of_meas_shift": None, "nan": 99},
    "Visibility": {"core_name": "Visibility", "unit": "km", "time_of_meas_shift": None, "nan": 9999.0},
    "CeilingH": {"core_name": "CeilingH", "unit": "m", "time_of_meas_shift": None, "nan": 99999},
    "WeatherObs": {"core_name": "", "unit": "None", "time_of_meas_shift": None, "nan": 9},
    "WeatherCode": {"core_name": "", "unit": "None", "time_of_meas_shift": None, "nan": 999999999},
    "PrecWater": {"core_name": "PrecWater", "unit": "mm", "time_of_meas_shift": None, "nan": 999.0},
    "Aerosol": {"core_name": "Aerosol", "unit": "1thousandth", "time_of_meas_shift": None, "nan": 0.999},
    "Snow": {"core_name": "", "unit": "cm", "time_of_meas_shift": None, "nan": 999.0},
    "DaysSinceSnow": {"core_name": "", "unit": "days", "time_of_meas_shift": None, "nan": 99},
    "Albedo": {"core_name": "", "unit": "None", "time_of_meas_shift": None, "nan": 999},
    "LiquidPrecD": {"core_name": "LiquidPrecD", "unit": "mm/h", "time_of_meas_shift": None, "nan": 999},
    "LiquidPrepQuant": {"core_name": "", "unit": "hours", "time_of_meas_shift": None, "nan": 99},
}

# Data description from https://www.nrel.gov/docs/fy08osti/43156.pdf 
# To-Do: Add the core names
format_tmy = {
    "Date (MM/DD/YYYY)": {"core_name": "", "unit": "month/day/year", "time_of_meas_shift": None, "nan": None},
    "Time (HH:MM)" : {"core_name": "", "unit": "hour:minute", "time_of_meas_shift": None, "nan": None},
    "ETR (W/m^2)" : {"core_name": "ExtHorRad", "unit": "Wh/m2", "time_of_meas_shift": None, "nan": None},
    "ETRN (W/m^2)" : {"core_name": "ExtDirNormRad", "unit": "Wh/m2", "time_of_meas_shift": None, "nan": None},
    "GHI (W/m^2)" : {"core_name": "GlobHorRad", "unit": "Wh/m2", "time_of_meas_shift": None, "nan": None},
    "GHI source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "GHI uncert (%)": {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None} ,
    "DNI (W/m^2)" : {"core_name": "", "unit": "Wh/m2", "time_of_meas_shift": None, "nan": None},
    "DNI source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DNI uncert (%)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DHI (W/m^2)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DHI source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DHI uncert (%)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "GH illum (lx)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "GH illum source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Global illum uncert (%)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DN illum (lx)" : {"core_name": "DirecNormIll", "unit": "100 lx", "time_of_meas_shift": None, "nan": None},
    "DN illum source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DN illum uncert (%)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DH illum (lx)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DH illum source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "DH illum uncert (%)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Zenith lum (cd/m^2)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Zenith lum source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Zenith lum uncert (%)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "TotCld (tenths)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "TotCld source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "TotCld uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "OpqCld (tenths)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "OpqCld source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "OpqCld uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Dry-bulb (C)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Dry-bulb source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Dry-bulb uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Dew-point (C)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Dew-point source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Dew-point uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "RHum (%)" : {"core_name": "", "unit": "percent", "time_of_meas_shift": None, "nan": None},
    "RHum source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "RHum uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Pressure (mbar)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Pressure source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Pressure uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Wdir (degrees)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Wdir source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Wdir uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Wspd (m/s)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Wspd source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Wspd uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Hvis (m)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Hvis source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Hvis uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "CeilHgt (m)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "CeilHgt source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "CeilHgt uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Pwat (cm)" : {"core_name": "PrecWater", "unit": "cm", "time_of_meas_shift": None, "nan": None},
    "Pwat source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Pwat uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "AOD (unitless)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "AOD source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "AOD uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Alb (unitless)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Alb source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Alb uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Lprecip depth (mm)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Lprecip quantity (hr)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Lprecip source" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None},
    "Lprecip uncert (code)" : {"core_name": "", "unit": None, "time_of_meas_shift": None, "nan": None}
}

def get_metadata(epw_file):
    with open(epw_file, 'r', encoding="latin1") as f:
        lines = f.readlines()
 
    location_name = lines[0].split(',')[1]
    latitude = float(lines[0].split(',')[6])
    longitude = float(lines[0].split(',')[7])
    timezone = float(lines[0].split(',')[8])
    altitude = float(lines[0].split(',')[9])
    return location_name, latitude, longitude, timezone, altitude

def get_weather_data(epw_file):
    with open(epw_file, 'r', encoding="latin1") as f:
        lines = f.readlines()
    data = []
    for line in lines[8:]:
        data.append(line.split(','))
    columns = format_epw.keys()
    data = pd.DataFrame(data, columns=columns)
    return data

def write_tmy(tmy_file_path, location_name, latitude, longitude, timezone, altitude, data):
    date = data["Month"].astype(str) + '/' + data["Day"].astype(str) + '/' + data["Year"].astype(str)
    time = data["Hour"].astype(str) + ':' + data["Minute"].astype(str)
    GHI = data['GlobHorRad']
    DNI = data['DirNormRad']
    DHI = data['DiffHorRad']
    DryBulb = data['DryBulbTemp']
    precipitation = data['PrecWater']
    humidity = data['RelHum']
    wind_speed = data['WindSpeed']

    # Take the exmaple from the TMY file and write it to the file
    data = pd.read_csv(r'weather_data\Stuttgart-hour_example.csv', skiprows=1)

    data['Date (MM/DD/YYYY)'] = date
    data['Time (HH:MM)'] = time
    data['ETR (W/m^2)'] = GHI
    data['ETRN (W/m^2)'] = np.nan
    data['GHI (W/m^2)'] = GHI
    data["Dry-bulb"] = DryBulb
    data["PrecWater"] = precipitation
    data["RHum (%)"] = humidity
    data["Wspd (m/s)"] = wind_speed

    path = os.path.join(tmy_file_path.split('.')[0] + '.txt')

    # Write the unrelated text row first
    with open(path, 'w') as f:
        f.write(f",{location_name},,{timezone},{latitude},{longitude},{altitude}" + '\n')

    data.to_csv(path, sep=',', index=False, mode='a')

   
   
    """ 
    with open(tmy_file_path, 'w', encoding="latin1") as f:
        lines = f.readlines()
        f.write(f"{location_name},,{latitude},,{longitude},,{altitude}\n")
        f.write("Date (MM/DD/YYYY),Time (HH:MM),ETR (W/m^2),ETRN (W/m^2),GHI (W/m^2),GHI source,GHI uncert (%),DNI (W/m^2),DNI source,DNI uncert (%),DHI (W/m^2),DHI source,DHI uncert (%),GH illum (lx),GH illum source,Global illum uncert (%),DN illum (lx),DN illum source,DN illum uncert (%),DH illum (lx),DH illum source,DH illum uncert (%),Zenith lum (cd/m^2),Zenith lum source,Zenith lum uncert (%),TotCld (tenths),TotCld source,TotCld uncert (code),OpqCld (tenths),OpqCld source,OpqCld uncert (code),Dry-bulb (C),Dry-bulb source,Dry-bulb uncert (code),Dew-point (C),Dew-point source,Dew-point uncert (code),RHum (%),RHum source,RHum uncert (code),Pressure (mbar),Pressure source,Pressure uncert (code),Wdir (degrees),Wdir source,Wdir uncert (code),Wspd (m/s),Wspd source,Wspd uncert (code),Hvis (m),Hvis source,Hvis uncert (code),CeilHgt (m),CeilHgt source,CeilHgt uncert (code),Pwat (cm),Pwat source,Pwat uncert (code),AOD (unitless),AOD source,AOD uncert (code),Alb (unitless),Alb source,Alb uncert (code),Lprecip depth (mm),Lprecip quantity (hr),Lprecip source,Lprecip uncert (code)\n")
        for i in range(len(data)):
            f.write(f"{date[i]},{time[i]},{GHI[i]},,,{DNI[i]},,,{DHI[i]}, 
            # f.write("Date (MM/DD/YYYY),Time (HH:MM),ETR (W/m^2),ETRN (W/m^2),GHI (W/m^2),GHI source,GHI uncert (%),DNI (W/m^2),DNI source,DNI uncert (%),DHI (W/m^2),DHI source,DHI uncert (%),GH illum (lx),GH illum source,Global illum uncert (%),DN illum (lx),DN illum source,DN illum uncert (%),DH illum (lx),DH illum source,DH illum uncert (%),Zenith lum (cd/m^2),Zenith lum source,Zenith lum uncert (%),TotCld (tenths),TotCld source,TotCld uncert (code),OpqCld (tenths),OpqCld source,OpqCld uncert (code),Dry-bulb (C),Dry-bulb source,Dry-bulb uncert (code),Dew-point (C),Dew-point source,Dew-point uncert (code),RHum (%),RHum source,RHum uncert (code),Pressure (mbar),Pressure source,Pressure uncert (code),Wdir (degrees),Wdir source,Wdir uncert (code),Wspd (m/s),Wspd source,Wspd uncert (code),Hvis (m),Hvis source,Hvis uncert (code),CeilHgt (m),CeilHgt source,CeilHgt uncert (code),Pwat (cm),Pwat source,Pwat uncert (code),AOD (unitless),AOD source,AOD uncert (code),Alb (unitless),Alb source,Alb uncert (code),Lprecip depth (mm),Lprecip quantity (hr),Lprecip source,Lprecip uncert (code)\n")
    """
if __name__ == '__main__':
    input_folder = r'C:\Users\felix\Programmieren\Mierendorff_Simstadt\weather_data'
    for file in os.listdir(input_folder):
        if file.endswith('.epw'):
            metadata = get_metadata(os.path.join(input_folder, file))
            data = get_weather_data(os.path.join(input_folder, file))
            write_tmy(os.path.join(input_folder, file), *metadata, data)
    ## Data for TMY files 
    # 107370,Stuttgart,,1,48.833,9.200, 318
    # Date (MM/DD/YYYY),Time (HH:MM),ETR (W/m^2),ETRN (W/m^2),GHI (W/m^2),GHI source,GHI uncert (%),DNI (W/m^2),DNI source,DNI uncert (%),DHI (W/m^2),DHI source,DHI uncert (%),GH illum (lx),GH illum source,Global illum uncert (%),DN illum (lx),DN illum source,DN illum uncert (%),DH illum (lx),DH illum source,DH illum uncert (%),Zenith lum (cd/m^2),Zenith lum source,Zenith lum uncert (%),TotCld (tenths),TotCld source,TotCld uncert (code),OpqCld (tenths),OpqCld source,OpqCld uncert (code),Dry-bulb (C),Dry-bulb source,Dry-bulb uncert (code),Dew-point (C),Dew-point source,Dew-point uncert (code),RHum (%),RHum source,RHum uncert (code),Pressure (mbar),Pressure source,Pressure uncert (code),Wdir (degrees),Wdir source,Wdir uncert (code),Wspd (m/s),Wspd source,Wspd uncert (code),Hvis (m),Hvis source,Hvis uncert (code),CeilHgt (m),CeilHgt source,CeilHgt uncert (code),Pwat (cm),Pwat source,Pwat uncert (code),AOD (unitless),AOD source,AOD uncert (code),Alb (unitless),Alb source,Alb uncert (code),Lprecip depth (mm),Lprecip quantity (hr),Lprecip source,Lprecip uncert (code)

    # Location Name, Cell B1
    # Latitude, Cell E1
    # Longitude, Cell F1
    # Elevation, Cell G1
    # GHI, Global Horizontal Irradiance, Column E - 
    # DNI, Direct Normal Irradiance, Column H
    # DHI, Diffuse Horizontal Irradiance, Column K
    # Dry-bulb, Dry-bulb ambient emperature, Column AF -> N6 
    # Sky temperautre - What is this supposed to be? No hint given in the documentation and in TMY files
    # Global Irradiance in Plane of Array
    # Precipitation
    # Humidity
    # Wind Speed 