
import mysql.connector
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

ONESIGNAL_APP_ID = "72a0153b-103b-45b6-ae55-e9440eb66340"
ONESIGNAL_API_KEY = "OGUyN2JhODgtNTYyYy00MmE3LThiZTgtM2I3MDQzOWYwZjhl"

cnx = mysql.connector.connect(
    host=os.getenv("MINHAMARCA_KERNEL_DB_HOST"),
    user=os.getenv("MINHAMARCA_KERNEL_DB_USER"),
    passwd=os.getenv("MINHAMARCA_KERNEL_DB_PASS"),
    database=os.getenv("MINHAMARCA_KERNEL_DB_NAME"),
    auth_plugin='mysql_native_password'
)


def get_users_to_notificate():
    query = "select users.push_player_id, notifications.* from notifications inner join users on notifications.user_id = users.id where notifications.status = 'PENDING'"
    cursor = cnx.cursor()
    cursor.execute(query)
    result_set = cursor.fetchall()
    for rs in result_set:
        resp_code = send_notification(rs[0], rs[4], rs[5])
        if resp_code == 200:
          cursor.execute("UPDATE notifications SET status = 'SEND' WHERE id ="+str(rs[1]))
          cnx.commit()


def send_notification(player_id, notification_title, notification_body):
    header = {"Content-Type": "application/json; charset=utf-8",
              "Authorization": "Basic "+ONESIGNAL_API_KEY}
    payload = {"app_id": ONESIGNAL_APP_ID,
               "include_player_ids": [str(player_id)],
               "headings": {"en": str(notification_title)},
               "contents": {"en": str(notification_body)}}
    req = requests.post("https://onesignal.com/api/v1/notifications",
                        headers=header, data=json.dumps(payload))
    print(req.status_code, req.reason)
    return req.status_code


get_users_to_notificate()
