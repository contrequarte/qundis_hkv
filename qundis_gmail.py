import yaml
import logging
import imaplib
import pandas as pd
import json
import re

# https://www.chilkatsoft.com/imap_search_criteria.asp

pattern_uid = re.compile(r'\d+ \(UID (?P<uid>\d+)\)')

def load_credentials(filepath):
    try:
        with open(filepath, 'r') as file:
            credentials = yaml.safe_load(file)
            user = credentials['user']
            password = credentials['password']
            return user, password
    except Exception as e:
        logging.error("Failed to load credentials: {}".format(e))
        raise

def connect_to_gmail_imap(user, password):
    imap_url = 'imap.gmail.com'
    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(user, password)
        mail.select('inbox')  # Connect to the inbox.
        return mail
    except Exception as e:
        logging.error("Connection failed: {}".format(e))
        raise

def get_emails_to_delete(mail, filepath):
    # with open(filepath, 'r') as file:
    #     data = json.load(file)
    #     emails_to_delete = data['emails']
    emails_to_delete = [
        "spam@example.com",
        "newsletter@example.com",
        "notifications@example.com"
    ]
    summary = pd.DataFrame(columns=['Email', 'Count'])
    for email in emails_to_delete:
        _, messages = mail.search(None, 'FROM "{}"'.format(email))
        mail.store(messages, '+FLAGS', '\\Deleted')
        summary = summary.append({'Email': email, 'Count': len(messages)}, ignore_index=True)
    return summary

def parse_uid(data):
    match = pattern_uid.match(data)
    return match.group('uid')

def get_list_of_email_ids(mail, folder):
    result, num_of_messages = mail.select(folder) #select a folder
    print(result)
    ret_dict = {}
    if result == 'OK':
        print(f'Folder: {folder} contains {num_of_messages} messages.')
        for mail_no in (mail.search(None, 'ALL'))[1][0].split():
            result, data = mail.fetch(mail_no, "(UID)")
            if result == 'OK':
               ret_dict[mail_no.decode("utf-8")] = parse_uid(data[0].decode("utf-8"))
    else:
        print(f'Folder: {folder} doesn\'t exist!.')
    return ret_dict

def list_emails(mail):
    summary = pd.DataFrame(columns=['Email', 'Count'])
    #t, data = mail.fetch('2', '(RFC822)')
    rv, data = mail.search(None, 'ALL')
    #rv, data = mail.search(None, 'FROM "*@ifttt.com" SINCE 22-Jul-2026')
    #rv, data = mail.search(None, 'OR SUBJECT "*alert" SUBJECT TEST')
    #print(f'You have a total of {str(int(data[0]))} messages')
    print(rv)
    print(data)
    print(data[0])
    t, data = mail.fetch('4', '(RFC822)')
    print(data)
    #print(data[0][1])

    #return summary

def main():
    credentials = load_credentials('.\\credentials.yaml')
    mail = connect_to_gmail_imap(*credentials)
    #list_emails(mail)
    print(get_list_of_email_ids(mail, "processed"))
    print(get_list_of_email_ids(mail, "inbox"))
    print(get_list_of_email_ids(mail, "Spam"))
    #summary = get_emails_to_delete(mail, 'path_to_email_list.json')
    #print(summary)


if __name__ == "__main__":
    main()