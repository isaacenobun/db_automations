import os
import json

import oracledb

from django.shortcuts import render, HttpResponse

# SMTP
import smtplib, ssl
from email.message import EmailMessage

from dotenv import load_dotenv
load_dotenv()

# Check if the Oracle client is installed in thick mode or thin mode
try:
    oracledb.init_oracle_client(lib_dir=os.getenv("ORACLE_CLIENT_PATH"))
    print("Running in thick mode")
except Exception as e:
    print("Running in thin mode")

# Send mail 
def report(agent):
    port = 587
    smtp_server = os.environ.get('SMTP_SERVER')
    username=os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    
    if agent[-1] == "asm":
        message = "ASM Report"
        msg = EmailMessage()
        msg['Subject'] = "Test Email"
        msg['From'] = os.environ.get('FROM')
        msg['To'] = os.environ.get('TO')
        msg.set_content(message)
        try:
            if port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                    server.login(username, password)
                    server.send_message(msg)
            elif port == 587:
                with smtplib.SMTP(smtp_server, port) as server:
                    server.starttls()
                    server.login(username, password)
                    server.send_message(msg)
            else:
                print ("use 465 / 587 as port value")
                exit()
            print ("successfully sent")
            return True
        except Exception as e:
            print (e)
            return False
    
    elif agent[-1] == "cpu":
        message = "CPU Report"
        msg = EmailMessage()
        msg['Subject'] = "Test Email"
        msg['From'] = os.environ.get('FROM')
        msg['To'] = os.environ.get('TO')
        msg.set_content(message)
        try:
            if port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                    server.login(username, password)
                    server.send_message(msg)
            elif port == 587:
                with smtplib.SMTP(smtp_server, port) as server:
                    server.starttls()
                    server.login(username, password)
                    server.send_message(msg)
            else:
                print ("use 465 / 587 as port value")
                exit()
            print ("successfully sent")
            return True
        except Exception as e:
            print (e)
            return False
    
    return

# Collect ASM data
def asm(request):
    
    names, percentages, statuses, db_check = [], [], [], []
    
    connections_str = os.getenv('CONNECTIONS')
    connections = json.loads(connections_str)
    
    for connection in connections:
        db_name = connection[3]
        names.append(db_name)
        
        try:
            conn = oracledb.connect(
                user=connection[0],
                password=connection[1],
                dsn=connection[2]
            )
            print (f"Successfully connected to {db_name}")

            cursor = conn.cursor()
            cursor.execute('Select round((free_mb/total_mb*100),2) PERCENTAGE from v$asm_diskgroup')
            data = cursor.fetchall()
            
            percentage = str(data[1][0] if db_name == 'Publisher' else data[0][0])
            percentages.append(percentage)

            if float(percentage) >= 30:
                statuses.append('OK')
            else:
                statuses.append('Check Now')
                db_check.append(db_name)

            cursor.close()
            conn.close()
            print (f"Disconnected from {db_name}")
        
        except Exception as e:
            print (f"Error connecting to {db_name}: {str(e)}")
            percentages.append('N/A')
            statuses.append('N/A')

    agent = names + percentages + statuses + db_check + ['asm']

    if report(agent):
        print ("Successfully sent ASM report!")
    else:
        print ("Failed to send ASM report.")
    
    return HttpResponse('<p>Success</p>')

# Collect CPU data
def cpu(request):
    
    names, cpu, statuses, db_check = [], [], [], []
    
    connections_str = os.getenv('CONNECTIONS')
    connections = json.loads(connections_str)
    
    for connection in connections:
        db_name = connection[3]
        names.append(db_name)
        
        try:
            conn = oracledb.connect(
                user=connection[0],
                password=connection[1],
                dsn=connection[2]
            )
            print (f"Successfully connected to {db_name}")
            
            cursor = conn.cursor()
            cursor.execute("SELECT ROUND(value,2) AS host_cpu_utilization_pct FROM v$sysmetric WHERE metric_name = 'Host CPU Utilization (%)'")
            data = cursor.fetchall()
            
            load = str(data[0][0])
            cpu.append(load)

            if float(cpu) <= 40:
                statuses.append('Normal Load')
            else:
                statuses.append('CPU Spiking')
                db_check.append(db_name)

            cursor.close()
            conn.close()
            print (f"Disconnected from {db_name}")
    
        except Exception as e:
            print (f"Error connecting to {db_name}: {str(e)}")
            cpu.append('N/A')
            statuses.append('N/A')
            
    agent = names + cpu + statuses + db_check + ['cpu']
    
    if report(agent):
        print ("Successfully sent CPU report!")
    else:
        print ("Failed to send CPU report.")
        
    return HttpResponse('<p>Success</p>')

def cpu_viz(request):
    pass