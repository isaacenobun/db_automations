import os
import json

import oracledb

from django.template.loader import render_to_string
from django.core.management.base import BaseCommand

# SMTP
import smtplib, ssl
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

import pandas as pd
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from dotenv import load_dotenv
load_dotenv()

class Command(BaseCommand):
    help = 'Plots CPU utilization data from Oracle databases and sends an email report'

    def send_report(self, agent):
        port = 587
        smtp_server = os.environ.get('SMTP_SERVER')
        username=os.environ.get('USERNAME')
        password = os.environ.get('PASSWORD')
        
        image_cid = make_msgid(domain='crccreditbureau.com')[1:-1]
        
        context = {
            'peak_load': agent['peak_load'],
            'peak_db': agent['peak_db'],
            'peak_time': agent['peak_time'],
            'most_loaded_db': agent['most_loaded_db'],
            'most_loaded_db_load': agent['most_loaded_db_load'],
            'least_loaded_db': agent['least_loaded_db'],
            'least_loaded_db_load': agent['least_loaded_db_load'],
            'load_std': agent['load_std'],
            'stability': agent['stability'],
            'image_cid': image_cid
        }
        
        html_content = render_to_string('cpu_viz_mail.html', context)
        
        msg = EmailMessage()
        msg['Subject'] = "CPU Utilization Report"
        msg['From'] = os.environ.get('FROM')
        msg['To'] = os.environ.get('TO')
        
        msg.set_content("CPU Utilization Report")
        msg.add_alternative(html_content, subtype='html')
        
        html_part = msg.get_body('html')
        day = datetime.now().strftime('%d_%m_%y')
        image_path = f'/cpu_viz_{day}.png'
        
        if not Path(image_path).exists():
            self.stderr.write(self.style.ERROR(f"Image file {image_path} does not exist."))
            return False
        
        with open(image_path, 'rb') as img:
            html_part.add_related(
                img.read(),
                maintype='image',
                subtype='jpeg',
                cid=f"<{image_cid}>"
            )
        
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
            self.stdout.write("Starting CPU Utilization Plots...")

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
            
            df_numeric = df.drop(columns=['Time']).astype(float)

            peak_load = round(df_numeric.max().max(),2)
            peak_db = df_numeric.max().idxmax()
            peak_time = df.loc[df[peak_db] == peak_load, 'Time'].values[0]

            avg_load = df_numeric.mean()
            most_loaded_db = avg_load.idxmax()
            least_loaded_db = avg_load.idxmin()
            most_loaded_db_load = round(avg_load.max(),2)
            least_loaded_db_load = round(avg_load.min(),2)

            load_std = df_numeric.std().mean()
            stability = "stable" if load_std < 1.5 else "fluctuating"
            
            agent = {
                'peak_load': peak_load,
                'peak_db': peak_db,
                'peak_time': peak_time,
                'most_loaded_db': most_loaded_db,
                'most_loaded_db_load': most_loaded_db_load,
                'least_loaded_db': least_loaded_db,
                'least_loaded_db_load': least_loaded_db_load,
                'load_std': load_std,
                'stability': stability
            }

            if (self.send_report(agent)):
                self.stdout.write(self.style.SUCCESS("Successfully sent CPU Utilization report!"))
            else:
                self.stderr.write(self.style.ERROR("Failed to send CPU Utilization report."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Critical Error: {str(e)}"))
            raise