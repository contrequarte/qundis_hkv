from flask import Flask, request, send_file, jsonify
import zipfile
import io
import os
import xml.etree.ElementTree as ET
import csv
app = Flask(__name__)


#creating a csv structure containing the latest month's end values of all devices in the qundis xml file
def extract_latest_month_end_values(xml_meter_string):
    root = ET.fromstring(xml_meter_string)
    #print(root.tag, flush=True)
    #print(xml_meter_string, flush=True)
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
    #print(measure_devices_list, flush=True)
    #write_values_to_csv(measure_devices_list, xml_meter_file.replace(".xml", ".csv"))
    csv_data = convert_values_to_csv(measure_devices_list)
    #print(csv_data.getvalue(), flush=True)
    return csv_data

#writing out a list of dictionaries handed over to a specified csv file
def convert_values_to_csv(devices_values):
    keys = devices_values[0].keys()

    #with open(csv_file, 'w', newline='') as output_file:
    csv_output = io.StringIO()
    dict_writer = csv.DictWriter(csv_output, keys)
    dict_writer.writeheader()
    dict_writer.writerows(devices_values)

    return csv_output


@app.route("/extract-xml", methods=["POST"])
def extract_xml():
    # Check, if a file has been transmitted
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    zip_password = uploaded_file.filename[0:8]
    try:
        # open zip file in memory
        zip_buffer = io.BytesIO(uploaded_file.read())

        with zipfile.ZipFile(zip_buffer, "r") as zip_ref:
            # looking for xml files
            xml_files = [
                f for f in zip_ref.namelist()
                if f.lower().endswith(".xml")
            ]

            if not xml_files:
                return jsonify({"error": "No XML file found in ZIP"}), 404

            # using first .xml file contained in archive (There should be on .xml only!)
            xml_name = xml_files[0]
            print(f'Processing xml file: "{xml_name}"', )
            xml_data = zip_ref.read(xml_name, zip_password.encode("utf-8"))

            csv_output = extract_latest_month_end_values(xml_data)

            #print(csv_output.getvalue(), flush=True)

            return send_file(
                io.BytesIO(csv_output.getvalue().encode('utf8')),
                mimetype="text/csv",
                as_attachment=True,
                download_name=os.path.basename(xml_name.replace('.xml', '.csv')),
            )

    except zipfile.BadZipFile:
        return jsonify({"error": "Invalid ZIP file"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)