from xml.etree import cElementTree as ElementTree
from collections.abc import MutableMapping 
import mysql.connector
from dateutil.parser import parse
from datetime import datetime
import sys
import os
import json

import logging
logging.basicConfig(filename='debug_log.log',level=logging.DEBUG)

TABLE_NAME = "publications"

def is_int(s):
    if(not isinstance(s, str)):
        return False
    if "." in s:
        return False
    try: 
        int(s)
        return True
    except ValueError:
        return False

def is_date(string, fuzzy=False):
    if string == None:
        return False
    if(is_int(string)):
        return False
    if "." in string:
        return False
    if(not isinstance(string, str)):
        return False
    has_all_parts = string.split("/")
    if(len(has_all_parts) != 3):
        return False
    try: 
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False

def find_value_in_objects(objects, key_to_find):
    for ob in objects:
        if key_to_find in ob:
            return ob[key_to_find]

def normalize_keys_separators(dict_to_parse):
    parsed_dict = {}
    all_keys = dict_to_parse.keys()
    for key in all_keys:
        new_key = key.replace("-", "_")
        new_key = new_key.replace("despachos_despacho", "despacho")
        parsed_dict[new_key] = dict_to_parse[key]
    return parsed_dict


def convert_flatten(d, parent_key ='', sep ='_'): 
    items = [] 
    for k, v in d.items(): 
        new_key = parent_key + sep + k if parent_key else k 
  
        if isinstance(v, MutableMapping): 
            items.extend(convert_flatten(v, new_key, sep = sep).items()) 
        else: 
            items.append((new_key, v)) 
    return dict(items)

# feature from (https://stackoverflow.com/questions/2148119/how-to-convert-an-xml-string-to-a-dictionary)
class XmlListConfig(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                # treat like dict
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDictConfig(element))
                # treat like list
                elif element[0].tag == element[1].tag:
                    self.append(XmlListConfig(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)

# feature from (https://stackoverflow.com/questions/2148119/how-to-convert-an-xml-string-to-a-dictionary)
class XmlDictConfig(dict):
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                else:
                    aDict = {element[0].tag: XmlListConfig(element)}
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            elif element.items():
                self.update({element.tag: dict(element.items())})
            else:
                self.update({element.tag: element.text})


def create_tables(table, all_parsed_dict):
    logging.debug("[Function] Create Table")
    cursor = cnx.cursor()
    all_keys = set().union(*(d.keys()
                             for d in all_parsed_dict))
    table_columns = []
    cursor.execute("select COLUMN_NAME from information_schema.columns where TABLE_NAME = '"+str(table)+"' order by table_name,ordinal_position")
    result_set = cursor.fetchall()
    for rs in result_set:
        table_columns.append(rs[0])
    has_difference = list(set(all_keys) - set(table_columns))
    if(len(has_difference) > 0):
        for field in has_difference:
            if(is_int(find_value_in_objects(all_parsed_dict, field))):
                cursor.execute("ALTER TABLE "+table+" ADD " +field+" int NULL")
                cnx.commit()
            elif(is_date(find_value_in_objects(all_parsed_dict, field))):
                cursor.execute("ALTER TABLE "+table+" ADD " +field+" timestamp NULL")
                cnx.commit()
            else:
                cursor.execute("ALTER TABLE "+table+" ADD "+field+" varchar(65533) CHARSET utf8")
                cnx.commit()

def insert_objects(table, all_parsed_dict, mag_info):
    logging.debug("[Function] Insert Objects")
    cursor = cnx.cursor()
    table_columns = []
    try:
        cursor.execute("select COLUMN_NAME from information_schema.columns where TABLE_NAME = '"+str(table)+"' order by table_name,ordinal_position")
        result_set = cursor.fetchall()
    except:
        logging.warning("[Database] get columns error table: "+str(table))
    for rs in result_set:
        if(rs[0] != "id"):
            table_columns.append(rs[0])
    query =  'insert into ' + table + ' (' + ','.join(table_columns) + ') VALUES (' + ','.join(['%s'] * len(table_columns))+ ');'
    all_values = []
    for parsed_dict in all_parsed_dict:
        values = []
        for tc in table_columns:
            if tc == "mag_numero":
                values.append(mag_info['numero'])
                continue
            if tc == "mag_data":
                formatted_date = datetime.strptime(mag_info['data'], '%d/%m/%Y')
                values.append(formatted_date)
                continue
            if tc in parsed_dict:
                if isinstance(parsed_dict[tc], list):
                    try:
                        values.append('|'.join(parsed_dict[tc]))
                    except:
                        try:
                            values.append(json.dumps(parsed_dict[tc]))
                        except:
                            print(parsed_dict[tc])
                            print(parsed_dict)
                elif is_date(parsed_dict[tc]):
                    try:
                        formatted_date = datetime.strptime(parsed_dict[tc], '%d/%m/%Y')
                        values.append(formatted_date)
                    except:
                        logging.warning("[Date Formatter] error to format date: "+str(parsed_dict[tc]))
                        values.append(parsed_dict[tc])
                else:
                    values.append(parsed_dict[tc])
            else:
                values.append(None)
        all_values.append(values)
    all_values_a = all_values[:len(all_values)//2]
    all_values_b = all_values[len(all_values)//2:]
    cursor.execute('set global max_allowed_packet=67108864')
    logging.debug("[Parsing] All objects: "+str(len(all_values))+" Split A: "+str(len(all_values_a))+" Split B: "+str(len(all_values_b)))
    try:
        cursor.executemany(query, all_values_a)
        cnx.commit()
    except:
        logging.warning("[Database] insert many error :  "+str(len(all_values_a)))
    try:
        cursor.executemany(query, all_values_b)
        cnx.commit()
    except:
        logging.warning("[Database] insert many error :  "+str(len(all_values_b)))
    cursor.close()


cnx = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  passwd="docker",
  database="minhamarca"
)

def process_file(filepath):
    logging.debug("[Function] Process File: "+str(filepath))
    print("[Function] Process File: "+str(filepath))
    all_parsed_objects = []
    tree = ElementTree.parse(filepath)
    root = tree.getroot()
    mag = {
        'numero': root.attrib['numero'],
        'data': root.attrib['data']
    }
    for r in root.iter('processo'):
        xmldict = XmlDictConfig(r)
        parsed_object = normalize_keys_separators(convert_flatten(xmldict))
        if "despacho" in parsed_object:
            if isinstance(parsed_object["despacho"], list):
                for sub in parsed_object["despacho"]:
                    aux = parsed_object
                    aux["despacho"] = sub
                    aux_parsed = normalize_keys_separators(convert_flatten(aux))
                    all_parsed_objects.append(aux_parsed)
        else:
            all_parsed_objects.append(parsed_object)
    create_tables(TABLE_NAME,all_parsed_objects)
    insert_objects(TABLE_NAME,all_parsed_objects, mag)
    # set_users_to_notificate(all_parsed_objects, mag)

def set_users_to_notificate(objects, mag):
    print("[Creating Notifications] ...")
    process_numbers = [d['numero'] for d in objects]
    cursor = cnx.cursor()
    query = "select * from user_processes where process in ("+','.join(process_numbers)+")"
    cursor.execute(query)
    result_set = cursor.fetchall()
    user_to_notificate = []
    for rs in result_set:
        user_to_notificate.append([rs[1], "PENDING", "Temos Novidades", "Saiu uma nova atualização do seu processo na revista: "+str(mag['numero'])+". Abra o app para acompanhar."])
    insert_query = "INSERT INTO user_notifications (user_id, status, notification_title, notification_body) VALUES (%s, %s, %s, %s)"
    cursor.executemany(insert_query, user_to_notificate)
    cnx.commit()


BASE_FILE_DIR = "to_process"
FROM_FILE_DIR = "processed"


# process_file("to_process/2515.xml")
# sys.exit()
for dirname, dirnames, filenames in os.walk(BASE_FILE_DIR):
        for filename in filenames:
            if(dirname != BASE_FILE_DIR):
                continue 
            if(filename == ".DS_Store"):
                continue
            print(filename)
            process_file(BASE_FILE_DIR+"/"+filename)
            # try:
            #     os.rename(BASE_FILE_DIR+"/"+filename, FROM_FILE_DIR+"/"+filename)
            # except:
            #     logging.warning("[FileSystem] move file error :  "+str(filename))


