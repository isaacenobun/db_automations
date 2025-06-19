import os
import json

import oracledb

from django.shortcuts import render, HttpResponse

from fabric import Connection

# SMTP
import smtplib, ssl
from email.message import EmailMessage

import pandas as pd
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
        
    elif agent == "viz":
        message = "Today's CPU Utilization Report"
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

# Log CPU load data
def cpu_logger(request):
    
    names, cpu = [], []
    
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
            
            cursor.close()
            conn.close()
            print (f"Disconnected from {db_name}")
    
        except Exception as e:
            print (f"Error: {str(e)}")
            cpu.append('0')
    
    day = datetime.now().strftime('%d_%m_%y')
    file_path = f"/cpu_log_{day}.txt"
    
    try:
        with open(file_path, 'w') as f:
            f.read()
    except Exception as e:
        with open(file_path, 'w') as f:
            f.write(f"Time|{'|'.join(names)}\n")
            
    try:
        new_entry = dict(zip(names, cpu))
        new_entry['Time'] = datetime.now().strftime('%I:%M%p')
        
        print("New data:", new_entry)
                
        new_row = pd.DataFrame([new_entry])
        df = pd.concat([df, new_row], ignore_index=True)
        
        df = df[['Time'] + names]
        
        df.to_csv(file_path, sep='|', index=False)
        print(f"Data appended to {file_path}")
    
    except Exception as e:
        print(f"Error: {e}")
        
    return HttpResponse('<p>Success</p>')

# Visualize CPU load data
def cpu_viz():
    day = datetime.now().strftime('%d_%m_%y')
    file_path = f"/cpu_log_{day}.txt"
    df = pd.read_csv(file_path, sep='|')
    
    times = pd.to_datetime(df['Time'], format='%H:%M')
    lines = {
        'Primary': df['Primary'],
        'Publisher': df['Publisher'],
        'Sub01_prod': df['Sub01_prod'],
        'Sub02_prod': df['Sub02_prod'],
        'Sub03_prod': df['Sub03_prod'],
        'Sub04_prod': df['Sub04_prod']
    }
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(10, 5), dpi=1000)
    
    for label, values in lines.items():
        if label=='Primary':
            ax.plot(times, values, 
                    linewidth=1.3, 
                    alpha=0.9,
                    label=label,
                    color='blue')
        else:
            ax.plot(times, values, 
                    linewidth=0.8, 
                    alpha=0.7,
                    label=label)
            
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_xlabel('Time', fontsize=10, labelpad=8)
    ax.set_ylabel('CPU Load (%)', fontsize=10, labelpad=8)
    day = datetime.now().strftime('%A %d %b, %Y')
    ax.set_title(f'CPU Utilization for {day}', 
                fontsize=12, 
                pad=12,
                fontweight='bold')
    
    ax.legend(loc='upper right', 
              frameon=True,
              fontsize=5,
              framealpha=0.9,
              edgecolor='#2e3440',
              facecolor='white')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='both', labelsize=8)
    
    plt.tight_layout()
    plt.savefig(f'/cpu_viz_{day}.png', dpi=1000)
    
    agent = "viz"
    
    if report(agent):
        print ("Successfully sent CPU Viz report!")
    else:
        print ("Failed to send CPU Viz report.")
    
    return HttpResponse('<p>Success</p>')

def server_logger(request):
    
    host_names = []
    cpu = []
    ram = []
    hourly_usage = []
    total_usage = []
    
    connections_str = os.getenv('CONNECTIONS')
    connection = json.loads(connections_str)[0]
    db_name = connection[3]
    
    try:
    
        conn = oracledb.connect(
            user=connection[0],
            password=connection[1],
            dsn=connection[2]
        )
        print (f"Successfully connected to {db_name}")
        
        cursor = conn.cursor()
                
        cursor.execute("select host_name, client_machine_ip,request_type_id, count(1) from sbreportmart.sb_inquiry where request_type_id in ('REQ_Live') and trunc(request_date) = trunc(sysdate) group by host_name, request_type_id, client_machine_ip order by host_name, request_type_id, client_machine_ip desc;")
        
        total_usage_data = cursor.fetchall()
        print (str(total_usage_data[3]))
        # total_usage.append(str(total_usage_data[3]))
        cursor.close()
        
        server_connections_str = os.getenv('SERVER_CONNECTIONS')
        server_connections = json.loads(server_connections_str)
        
        for connection in server_connections:
            host_name = connection[0]
            host_names.append(host_name)
            
            try:
                cursor = conn.cursor()
                
                cursor.execute("SELECT total FROM (SELECT TO_CHAR(TRUNC(request_start_time, 'HH24'), 'DD-MON-YYYY') || ' ' || TO_CHAR(TRUNC(request_start_time, 'HH24'), 'HH24') || ':00' AS hour, COUNT(*) AS total, ROW_NUMBER() OVER (ORDER BY TRUNC(request_start_time, 'HH24') DESC) AS rn FROM sbreportmart.sb_inquiry t1 WHERE request_type_id = 'REQ_Live' AND client_machine_ip = '10.17.33.9' AND request_date BETWEEN TO_DATE('19-JUN-2025', 'DD-MON-YYYY') AND TO_DATE('20-JUN-2025', 'DD-MON-YYYY') GROUP BY TRUNC(request_start_time, 'HH24') ORDER BY TRUNC(request_start_time, 'HH24')) WHERE rn = 1;")
                
                hourly_usage_data = cursor.fetchall()
                print (str(hourly_usage_data[0][0]))
                # hourly_usage.append(str(hourly_usage_data[0][0]))
                cursor.close()
                
                server_conn = Connection(
                    connection[1],
                    connection[2],
                    connect_kwargs={"password": connection[3]}
                )
                
                cpu_value = server_conn.run("tail -n 1 /path_to_file.txt | grep -oE '[0-9]+%' | tail -n 1", hide=True)
                cpu_line = cpu_value.stdout.strip()
                cpu.append(cpu_line)
                
                ram_value = server_conn.run("tail -n 1 /path_to_file.txt | grep -oE '[0-9]+%' | tail -n 1", hide=True)
                ram_line = ram_value.stdout.strip()
                ram.append(ram_line)
                
                server_conn.close()
                
                conn.close()
                print (f"Disconnected from {db_name}")
            
            except Exception as e:
                print(f"Error connecting to {host_name}: {str(e)}")
                
    except Exception as e:
        print (f"Error: {str(e)}")
        
    return HttpResponse('<p>Success</p>')
        
        