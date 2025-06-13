import os
import json

import oracledb

from django.shortcuts import render, HttpResponse

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