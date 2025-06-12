import os
import json

import oracledb

from django.template.loader import render_to_string
from django.core.management.base import BaseCommand

# SMTP
import smtplib, ssl
from email.message import EmailMessage

from dotenv import load_dotenv
load_dotenv()

class Command(BaseCommand):
    help = 'Checks CPU Utilization and sends an email report'

    def send_report(agent):
        port = 587
        smtp_server = os.environ.get('SMTP_SERVER')
        username=os.environ.get('USERNAME')
        password = os.environ.get('PASSWORD')
        
        context = {
        'names': agent[:6],
        'percentages': agent[6:12],
        'statuses': agent[12:18],
        'db_check': agent[18:]
        }
        
        html_content = render_to_string('cpu_mail.html', context)
        
        msg = EmailMessage()
        msg['Subject'] = "CPU Load Monitor"
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
            self.stdout.write("Starting CPU Utilization check...")

            # Try running in thick mode
            try:
                oracledb.init_oracle_client(lib_dir=os.getenv("ORACLE_CLIENT_PATH"))
                self.stdout.write("Running in thick mode")
            except Exception as e:
                self.stdout.write("Running in thin mode")

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
                    self.stdout.write(f"Successfully connected to {db_name}")

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
                    self.stdout.write(f"Disconnected from {db_name}")
                
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error connecting to {db_name}: {str(e)}"))
                    cpu.append('N/A')
                    statuses.append('N/A')
                    
            agent = names + cpu + statuses + db_check

            if (self.send_report(agent)):
                self.stdout.write(self.style.SUCCESS("Successfully sent CPU Load report!"))
            else:
                self.stderr.write(self.style.ERROR("Failed to send CPU Load report."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Critical Error: {str(e)}"))
            raise