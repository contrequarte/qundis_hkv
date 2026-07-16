#
# Read a Qundis XML file and return the values of one measuring device in a tabular format
# 2026-07-13 rjs
#
import xml.etree.ElementTree as ET
from tabulate import tabulate # type: ignore
#xml_meter_file = 'C:\\Development\\Python\\HeizkostenXml\\OB003663 Bezirksstrasse 142_11147544_0000_20251201102956.xml'   # file as of 2025-12-01
xml_meter_file = 'C:\\Development\\Python\\HeizkostenXml\\OB003663 Bezirksstrasse 142_11147544_0000_20260101102533.xml'   # file as of 2026-01-01
#xml_meter_file = 'C:\\Development\\Python\\HeizkostenXml\\OB003663 Bezirksstrasse 142_11147544_0000_20260201102501.xml'   # file as of 2026-02-01

# add a data point entry to the device dictionary for a given storage number 
# or create a new entry if the storage number does not exist yet
def create_dp_entry(storage_nr, value, dimension, dev_dp_dict):
    if dev_dp_dict.get(storage_nr) != None:
        dev_dp_dict[storage_nr].append({"value": value, "dimension": dimension})
    else:
        dev_dp_dict[storage_nr] = [{"value": value, "dimension": dimension}]

# create a nice tabular output of the data points for a given counter id
def print_result_table(counter_id):
    table = []
    print(f'Counter ID: {counter_id}')
    for storage_nr in sorted(measure_devices_dict[counter_id].keys()):    
        for dp in measure_devices_dict[counter_id][storage_nr]:
            table.append([storage_nr, dp["value"], dp["dimension"]])
    print(tabulate(table, headers=["Storage Number", "Value", "Dimension"], tablefmt="grid"))

meter_data = ET.parse(xml_meter_file)
root = meter_data.getroot()
print(root.tag)
measure_devices_dict = {}
for measure_dev in root.iter('measuredev'):
    counter_id = measure_dev.find('fabnr').text
    device_dp_dict = {}
    for data_point in measure_dev.iter('datapoint'):
        storage_nr = data_point.find('storagenr').text
        value = data_point.find('value').text
        dimension = data_point.find('dimension').text    
        create_dp_entry(storage_nr, value, dimension, device_dp_dict)
    measure_devices_dict[counter_id] = device_dp_dict

#print_result_table('27418759') #HKV
print_result_table('27418743') #HKV
print_result_table('12246304') # Warmwasserzaehler
