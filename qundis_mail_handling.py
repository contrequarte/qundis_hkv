
import logging
from typing import Any

import yaml
from datetime import datetime
import io, zipfile
import xml.etree.ElementTree as ET
import csv
import os
from imap_tools import MailBox, A
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

logger = logging.getLogger(__name__)

#global config values:
log_filename  = ''
target_sender_address = ''
credentials_file_location = ''

# https://pypi.org/project/imap-tools/

#out_folder = 'C:\\Development\\Python\\HeizkostenXml\\data\\out\\test'

def load_config():
    cfg_file = f'{os.path.abspath(os.path.dirname(__file__))}/config.yaml'
    global log_filename
    global target_sender_address
    global credentials_file_location
    try:
        with (open(cfg_file, 'r') as file):
            config = yaml.safe_load(file)
            log_filename = config['log_filename']
            target_sender_address = config['target_sender_address']
            credentials_file_location = config['credentials_file_location']
    except Exception as e:
        logger.exception("Failed to load configuration: {}".format(e))
        raise

def load_credentials(filepath):
    try:
        with (open(filepath, 'r') as file):
            credentials = yaml.safe_load(file)
            user = credentials['user']
            password = credentials['password']
            imap_server = credentials['imap_server']
            smtp_server = credentials['smtp_server']
            port = credentials['port']
            csv_to = credentials['csv_to']
            csv_bcc = credentials['csv_bcc']
            no_hkv_found_to = credentials['no_hkv_found_to']
            return user, password, imap_server, smtp_server, port, csv_to, csv_bcc, no_hkv_found_to
    except Exception as e:
        logger.exception("Failed to load credentials: {}".format(e))
        raise

#creating a csv structure containing the latest month's end values of all devices in the qundis xml file
def extract_latest_month_end_values(xml_meter_string):
    root = ET.fromstring(xml_meter_string)

    measure_devices_list = []
    for measure_dev in root.iter('measuredev'):
        measure_dev_fabnr = measure_dev.find('fabnr').text
        for storage_nr in ["17"]:    # this contains the month's end values of the month before sending date of email
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

        measure_devices_list.append(latest_month_measures_dict)

    csv_data = convert_values_to_csv(measure_devices_list)

    return csv_data

#writing out a list of dictionaries handed over to a specified csv file
def convert_values_to_csv(devices_values):
    keys = devices_values[0].keys()

    csv_output = io.StringIO()
    dict_writer = csv.DictWriter(csv_output, keys)
    dict_writer.writeheader()
    dict_writer.writerows(devices_values)

    return csv_output


def main():
    #initializing the logging:
    load_config()
    #print(f'{log_filename} - {target_sender_address} - {credentials_file_location}')
    logging.basicConfig(filename=log_filename, level=logging.INFO)
    logger.info(f'Started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    user, pwd, imap_server, _, _, _, _, _ = load_credentials(credentials_file_location)

    with (MailBox(imap_server).login(user, pwd) as mailbox):
        try:
            result = mailbox.folder.set('inbox')
            print(result[0])
        except:
            print('Couldn\'t set the folder')
        else:
            #print(f'There are {int(result[1][0])} emails in the folder!')
            found_new_hkv_values = False
            for msg in mailbox.fetch():
                #print(f'Date: {msg.date} From: {msg.from_values.email} Subject: {msg.subject} Length: {len(msg.text or msg.html)} Num of attachments: {len(msg.attachments)}' )
                if ((msg.from_values.email == target_sender_address)          # email comes from Qundis
                    and (len(msg.attachments) > 0)                            # email has an attachment
                    and (msg.subject.index('[Q SMP]') >=0)                    # email has a Qundis subject
                    and (msg.attachments[0].filename.split('.')[1]=='zip')    # the first attachment is a zip archive
                    and ('processed' not in msg.flags)):                      # the message hasn't been processed successfully
                    log_entry = f'Processing email with UID: {msg.uid } Flags: {msg.flags} Date: {msg.date} From: {msg.from_values.email} Subject: {msg.subject} Length: {len(msg.text or msg.html)} Num of attachments: {len(msg.attachments)}'
                    print(log_entry)
                    found_new_hkv_values = True
                    logger.info(log_entry)
                    att = msg.attachments[0]
                    zip_password = att.filename[0:8]
                    zip_buffer = io.BytesIO(att.payload)

                    with zipfile.ZipFile(zip_buffer, "r") as zip_ref:
                        # looking for xml files
                        xml_files = [
                            f for f in zip_ref.namelist()
                            if f.lower().endswith(".xml")
                        ]

                        if not xml_files:
                            #return jsonify({"error": "No XML file found in ZIP"}), 404
                            logger.info('No XML file found in ZIP')
                        # using first .xml file contained in archive (There should be on .xml only!)
                        xml_name = xml_files[0]
                        logger.info(f'Processing xml file: "{xml_name}"', )
                        xml_data = zip_ref.read(xml_name, zip_password.encode("utf-8"))

                        csv_output = extract_latest_month_end_values(xml_data)
                        send_csv_by_email(csv_output, xml_name.replace(".xml", ".csv"))

                        logger.info(csv_output.getvalue())
                        mailbox.flag([msg.uid], ["processed"], True)
                        logger.info(f'Email with UID: {msg.uid }, has been flagged as \'processed\', processing this email now ends. ')

            if not found_new_hkv_values:
                send_found_no_new_hkv_email()

            for i in mailbox.fetch(A(gmail_label='processed')):
                 print(f'UID:  {msg.uid} Date: {msg.date} From: {msg.from_values.email} Tags: {msg.flags}')
    logger.info(f'Ended at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

###################################################################
# Creating a multipart message to attach the csv data and send it #
# via the configured smtp account                                 #
###################################################################
def send_csv_by_email(csv_data, file_name):
    # get the credentials
    user, pwd, _, smtp_server, port, csv_to, csv_bcc, _ = load_credentials(credentials_file_location)

    msg = MIMEMultipart()
    msg["Subject"] = "Heating values csv-file for BLK_Bezirksstr"
    msg["From"] = user
    msg["To"] = csv_to
    msg["BCC"] = csv_bcc


    msg.attach(MIMEText("Hello, here are the csv values for BLK_Bezirksstr converted from Qundis xml.", "plain"))

    part = MIMEBase("text", "csv")
    part.set_payload(csv_data.getvalue()) #.read())
    part.add_header("Content-Disposition", f"attachment; filename= {file_name}")
    msg.attach(part)


    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)

    logger.info("Email sent successfully!")

def send_found_no_new_hkv_email():
    # get the credentials
    user, pwd, _, smtp_server, port, _, _, no_hkv_found_to = load_credentials('/app/credentials.yaml')

    msg = MIMEMultipart()
    msg["Subject"] = "No new HKV files found!"
    msg["From"] = user
    msg["To"] = no_hkv_found_to

    msg.attach(MIMEText(f'<h1>No new HKV values found at {datetime.now().strftime("%Y-%m-%d %H:%M")}!</h1>', "html"))

    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)

    logger.info("No HKV email sent successfully!")

if __name__ == '__main__':
    main()