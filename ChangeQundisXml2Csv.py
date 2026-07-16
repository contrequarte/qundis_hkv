import xml.etree.ElementTree as ET
from glob import glob
from tabulate import tabulate # type: ignore
from zipfile import ZipFile
import csv

in_folder = 'C:\\Development\\Python\\HeizkostenXml\\data\\in'
out_folder = 'C:\\Development\\Python\\HeizkostenXml\\data\\out'

#Returning a list of all .zip files in the given folder
#The list returned only contains the main filenames without the file name extension
def get_zip_files(folder):
    stripped_zip_lst = [z.split("\\")[-1].split(".")[0]
                        for z in  [zip_file
                                   for zip_file in glob("\\".join([folder, "*.zip"]))
                                  ]
                        ]
    return stripped_zip_lst

#creating a csv file containing the latest month end values of all devices in the qundis xml file
def extract_latest_month_end_values(xml_meter_file):
    meter_data = ET.parse(xml_meter_file)
    root = meter_data.getroot()
    print(root.tag)
    print(xml_meter_file)
    measure_devices_list = []
    for measure_dev in root.iter('measuredev'):
        measure_dev_fabnr = measure_dev.find('fabnr').text
        for storage_nr in ["17"]:
            latest_month_measures_dict = {"device_id": measure_dev_fabnr}
            for data_point in measure_dev.findall(''.join(['.//datapoint[storagenr="', storage_nr,'"]'])):
                measure_dim = data_point.find('dimension').text
                measure_value = data_point.find('value').text
                if  measure_dim ==  "date":
                    latest_month_measures_dict["date"] = measure_value
                elif  measure_dim == "m3":
                    latest_month_measures_dict["value"] = str(float(measure_value.replace(",",".")))
                    #latest_month_measures_dict["dimension"] = measure_dim
                elif measure_dim == "H.C.A.":
                    latest_month_measures_dict["value"] = str(int(measure_value))
                    #latest_month_measures_dict["dimension"] = measure_dim
        #print(latest_month_measures_dict)
        measure_devices_list.append(latest_month_measures_dict)
    print(measure_devices_list)
    write_values_to_csv(measure_devices_list, xml_meter_file.replace(".xml", ".csv"))

#writing out a list of dictionaries handed over to a specified csv file
def write_values_to_csv(devices_values, csv_file):
    keys = devices_values[0].keys()

    with open(csv_file, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(devices_values)

#extracting the -xml file out of the given password protected qundis zip file
def extract_xml_from_zip(folder_in, folder_out, file_name):
    pw = file_name[0:8]
    zip_file = '\\'.join([folder_in, ''.join([file_name, '.zip'])])
    with ZipFile(zip_file, "r") as zip_file:
            zip_file.extract( member=''.join([file_name, '.xml']),path=folder_out, pwd=pw.encode("utf-8"))
    extract_latest_month_end_values('\\'.join([folder_out, ''.join([file_name, '.xml'])]))

#the main application
def main():
    for file_name in get_zip_files(in_folder):
        extract_xml_from_zip(in_folder, out_folder, file_name)

main()