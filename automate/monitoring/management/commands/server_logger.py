import os
import json

import oracledb

from django.template.loader import render_to_string
from django.core.management.base import BaseCommand

from fabric import Connection

# SMTP
import smtplib, ssl
from email.message import EmailMessage

from dotenv import load_dotenv
load_dotenv()

class Command(BaseCommand):
    help = 'Checks AWS Servers and sends an email report of usage statistics'

    def send_report(agent):
        port = 587
        smtp_server = os.environ.get('SMTP_SERVER')
        username=os.environ.get('USERNAME')
        password = os.environ.get('PASSWORD')
        
        context = {
            'host_names': agent[:5],
            'ip_addresses': agent[5:10],
            'cpu': agent[10:15],
            'ram': agent[15:20],
            'hourly_usage': agent[20:25],
            'total_usage': agent[25:30]
        }
        
        html_content = render_to_string('server_mail.html', context)
        
        msg = EmailMessage()
        msg['Subject'] = "Server Hourly Report"
        msg['From'] = os.environ.get('FROM')
        msg['To'] = os.environ.get('TO')
        msg.set_content(html_content, subtype='html')
        
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
            return True
        except Exception as e:
            print (e)
            return False

    def handle(self, *args, **options):
        try:
            self.stdout.write("Starting AWS Remote Servers check...")

            # Try running in thick mode
            try:
                oracledb.init_oracle_client(lib_dir=os.getenv("ORACLE_CLIENT_PATH"))
                self.stdout.write("Running in thick mode")
            except Exception as e:
                self.stdout.write("Running in thin mode")

            host_names, cpu, ram, hourly_usage, total_usage  = [], [], [], [], []
            
            connections_str = os.getenv('CONNECTIONS')
            connection = json.loads(connections_str)[0]
            db_name = connection[3]
            
            self.stdout.write(f"Successfully connected to {db_name}")
            
            try:
    
                conn = oracledb.connect(
                    user=connection[0],
                    password=connection[1],
                    dsn=connection[2]
                )
                self.stdout.write(f"Successfully connected to {db_name}")
                
                cursor = conn.cursor()
                
                # Get total usage data
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
                        
                        # Get hourly usage data for each server
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
                        self.stdout.write(f"Disconnected from {db_name}")
                    
                    except Exception as e:
                        print(f"Error connecting to {host_name}: {str(e)}")
                        
                agent =  host_names + cpu + ram + hourly_usage + total_usage

                if (self.send_report(agent)):
                    self.stdout.write(self.style.SUCCESS("Successfully sent Server Statistics report!"))
                else:
                    self.stderr.write(self.style.ERROR("Failed to send Server Statistics report."))
            
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Critical Error: {str(e)}"))
                raise
            
        except Exception as e:
                self.stderr.write(self.style.ERROR(f"Critical Error: {str(e)}"))
                raise