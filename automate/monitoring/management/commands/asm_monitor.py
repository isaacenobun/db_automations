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
    help = 'Checks Oracle ASM disk groups and sends an email report'

    def send_report(agent):
        port = 587
        smtp_server = os.environ.get('SMTP_SERVER')
        username=os.environ.get('USERNAME')
        password = os.environ.get('PASSWORD')
        
        if agent[-1] == "asm":
            
            agent.remove('asm')
            
            context = {
            'names': agent[:6],
            'percentages': agent[6:12],
            'statuses': agent[12:18],
            'db_check': agent[18:]
            }
            
            html_content = render_to_string('send_mail.html', context)
            
            msg = EmailMessage()
            msg['Subject'] = "ASM Monitor"
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
        
        elif agent[-1] == "cpu":
            
            context = {
            'names': agent[:5],
            'percentages': agent[5:10],
            'statuses': agent[10:15],
            'db_check': agent[15:20]
            }
            
            html_content = render_to_string('send_mail.html', context)
            
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
            
        return

    def handle(self, *args, **options):
        try:
            self.stdout.write("Starting ASM disk group check...")

            # Try running in thick mode
            try:
                oracledb.init_oracle_client(lib_dir=os.getenv("ORACLE_CLIENT_PATH"))
                self.stdout.write("Running in thick mode")
            except Exception as e:
                self.stdout.write("Running in thin mode")

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
                    self.stdout.write(f"Successfully connected to {db_name}")

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
                    self.stdout.write(f"Disconnected from {db_name}")
                
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error connecting to {db_name}: {str(e)}"))
                    percentages.append('N/A')
                    statuses.append('N/A')
                    
            agent = names + percentages + statuses + db_check + ['asm']

            if (self.send_report(agent)):
                self.stdout.write(self.style.SUCCESS("Successfully sent ASM report!"))
            else:
                self.stderr.write(self.style.ERROR("Failed to send ASM report."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Critical Error: {str(e)}"))
            raise