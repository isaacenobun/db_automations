import os

from django.shortcuts import render

# SMTP
import smtplib, ssl
from email.message import EmailMessage

# Send mail 
def report(agent):
    port = 587
    smtp_server = "smtp.zeptomail.com"
    username=os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    
    if agent == "asm":
        message = "ASM Report"
        msg = EmailMessage()
        msg['Subject'] = "Test Email"
        msg['From'] = "noreply@creditreferencenigeria.net"
        msg['To'] = "noreply@creditreferencenigeria.net"
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
        except Exception as e:
            print (e)
            return False
    
    elif agent == "cpu":
        message = "CPU Report"
        msg = EmailMessage()
        msg['Subject'] = "Test Email"
        msg['From'] = "noreply@creditreferencenigeria.net"
        msg['To'] = "noreply@creditreferencenigeria.net"
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
        except Exception as e:
            print (e)
            return False
        
    return True

# Db Connections
def connections():
    pass

# Collect ASM data
def asm(request):
    
    # Start connection to Db's
    
    # Start cursor and send query
    
    # Collect data
    
    # End connection
    
    # Send to mail function
    report(agent = "asm")
    
    # Return HTTPResponse
    
    pass

def cpu(request):
    
    #  Start connection to Db's
    
    # Start cursor and send query
    
    # Collect data
    
    # End connection
    
    # Send to mail function
    print() if report(agent="cpu") else print()
    
    # Return HTTPResponse
    
    pass