import yaml
import logging
import imaplib
import pandas as pd
import json

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

def list_emails(mail):
    summary = pd.DataFrame(columns=['Email', 'Count'])
    t, data = mail.fetch('2', '(RFC822)')
    print(data[0][1])

    #return summary

def main():
    credentials = load_credentials('.\\credentials.yaml')
    mail = connect_to_gmail_imap(*credentials)
    list_emails(mail)
    #summary = get_emails_to_delete(mail, 'path_to_email_list.json')
    #print(summary)


if __name__ == "__main__":
    main()