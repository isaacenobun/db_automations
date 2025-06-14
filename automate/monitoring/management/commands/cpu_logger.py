import os
import json

import oracledb

from django.template.loader import render_to_string
from django.core.management.base import BaseCommand

# SMTP
import smtplib, ssl
from email.message import EmailMessage

import pandas as pd
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

class Command(BaseCommand):
    help = 'Appends new CPU data to a pipe-separated log file'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Starting CPU Logging...")

            # Try running in thick mode
            try:
                oracledb.init_oracle_client(lib_dir=os.getenv("ORACLE_CLIENT_PATH"))
                self.stdout.write("Running in thick mode")
            except Exception as e:
                self.stdout.write("Running in thin mode")

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
                    self.stdout.write(f"Successfully connected to {db_name}")

                    cursor = conn.cursor()
                    cursor.execute("SELECT ROUND(value,2) AS host_cpu_utilization_pct FROM v$sysmetric WHERE metric_name = 'Host CPU Utilization (%)'")
                    data = cursor.fetchall()
                    
                    load = str(data[0][0])
                    cpu.append(load)
                    
                    cursor.close()
                    conn.close()
                    self.stdout.write(f"Disconnected from {db_name}")
                
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error connecting to {db_name}: {str(e)}"))
                    cpu.append('0')
                    
            day = datetime.now().strftime('%d_%m_%y')
            file_path = f"/cpu_log_{day}.txt"
            
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write(f"Time|{'|'.join(names)}\n")
                    
            try:
                new_entry = dict(zip(names, cpu))
                new_entry['Time'] = datetime.now().strftime('%H:%M')
                
                print("New data:", new_entry)
                
                try:
                    df = pd.read_csv(file_path, sep='|')
                except (pd.errors.EmptyDataError, FileNotFoundError):
                    df = pd.DataFrame(columns=['Time'] + names)
                        
                new_row = pd.DataFrame([new_entry])
                df = pd.concat([df, new_row], ignore_index=True)
                
                df = df[['Time'] + names]
                
                df.to_csv(file_path, sep='|', index=False)
                self.stdout.write(f"Data appended to {file_path}")
                
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error appending data: {str(e)}"))
            self.stdout.write("CPU Logging completed successfully.")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Critical Error: {str(e)}"))
            raise