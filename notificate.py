
import mysql.connector
import requests
import json

ONESIGNAL_APP_ID = "72a0153b-103b-45b6-ae55-e9440eb66340"
ONESIGNAL_API_KEY = "OGUyN2JhODgtNTYyYy00MmE3LThiZTgtM2I3MDQzOWYwZjhl"

cnx = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    passwd="docker",
    database="process_monitor_inpi"
)


def get_users_to_notificate():
    query = "select users.email, user_notifications.* from user_notifications inner join users on user_notifications.user_id = users.id where user_notifications.status = 'PENDING'"
    cursor = cnx.cursor()
    cursor.execute(query)
    result_set = cursor.fetchall()
    for rs in result_set:
        resp_code = send_notification(rs[0], rs[4], rs[5])
        if resp_code == 200:
          cursor.execute("UPDATE user_notifications SET status = 'DELIVERED' WHERE id ="+str(rs[1]))
          cnx.commit()


def send_notification(email, notification_title, notification_body):
    header = {"Content-Type": "application/json; charset=utf-8",
              "Authorization": "Basic "+ONESIGNAL_API_KEY}
    payload = {"app_id": ONESIGNAL_APP_ID,
               "filters": [{"field": "email", "value": str(email)}],
               "contents": {"en": str(notification_body)}}
    req = requests.post("https://onesignal.com/api/v1/notifications",
                        headers=header, data=json.dumps(payload))
    print(req.status_code, req.reason)
    return req.status_code


get_users_to_notificate()
