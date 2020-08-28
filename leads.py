
# coding: utf-8
# In[4]:
# -*- coding: utf-8 -*-
# install pyDF2
# pip install PyPDF2
# pip install brazilnum
# pip install mysql-connector
# importing all the required modules
import PyPDF2
import mysql.connector
import os
import sys

cnx = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    # passwd="ByMNj5pK", //production
    passwd="docker",
    database="minhamarca"
)

leads = []
for dirname, dirnames, filenames in os.walk('leads'):
    for filename in filenames:
        if(filename == ".DS_Store"):
            print("file unexpected")
        else:
            mag = dirname.split("/")[1]
            file = open(os.path.join(dirname, filename), 'rb')
            fileReader = PyPDF2.PdfFileReader(file)
            pageObj = fileReader.getPage(0)

           
          
            all_text = str(pageObj.extractText())
            # print(all_text)
            # sys.exit()
            nm_proc = all_text.split("Processo:")
            novo = nm_proc[1].split("Nome:")
            numero_proc = novo[0]
            novo = novo[1].split('CPF/CNPJ/Número INPI:')
            nome = novo[0]
            novo = novo[1].split('Endereço:')
            cpf_cnpj = novo[0]
            novo = novo[1].split('Cidade:')
            endereco = novo[0]
            novo = novo[1].split('Estado:')
            cidade = novo[0]
            novo = novo[1].split('CEP:')
            estado = novo[0]
            novo = novo[1].split('Pais:')
            cep = novo[0]
            novo = novo[1].split('Natureza Jurídica:')
            pais = novo[0]
            novo = novo[1].split('e-mail:')
            natureza_juridica = novo[0]
            novo = novo[1].split('Dados da MarcaApresentação:')
            email = novo[0].split('Dados do(s) requerente(s)')[0]

            
            lead = [email.lower(), numero_proc, nome, mag, "NEW"]
            # print(lead)
            leads.append(lead)

cursor = cnx.cursor()
query = "INSERT INTO leads (email, process, full_name, mag_number, status, created_at, updated_at) VALUES  (%s, %s, %s, %s, %s, now(), now())"
cursor.executemany(query, leads)
cnx.commit()
