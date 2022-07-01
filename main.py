import os
from mysql.connector.constants import ClientFlag
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
import mysql.connector
import requests
import time
import re

app = Flask(__name__)

err_postal = "I do not recognize this Postal Code. Please enter a valid 6 digit Alberta Postal code. If that does not work try entering the first 3 digits or visit the AHS Vaccine website for more help: "+ "https://www.albertahealthservices.ca/topics/Page17295.aspx"
err_db = "Database Error! Sorry for the inconvenience. Please visit the AHS Vaccine website for more help: "+ "https://www.albertahealthservices.ca/topics/Page17295.aspx"
err_lat_long = "Google Maps API could not find your postal code - This usually occurs if your neighbourhood is new. Please try entering the first 3 digits of your postal code. If that does not work, please visit the AHS Vaccine website for more help: "+ "https://www.albertahealthservices.ca/topics/Page17295.aspx"

@app.route("/sms", methods=['GET', 'POST'])
def incoming_sms():
    """Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    final_body = body.strip()
    try:
        postal_code = validate_body(final_body)
    except Exception:
        resp = MessagingResponse()
        resp.message(err_postal)
        return str(resp)
    try:
        lat, longitude = get_lat_lon_prod(postal_code)
    except Exception:
        resp = MessagingResponse()
        resp.message(err_lat_long)
        return str(resp)
    try:        
        db_data= make_query(lat,longitude)
    except Exception:
        resp = MessagingResponse()
        resp.message(err_db)
        return str(resp)
    
    final = format_final(db_data)  
    # Start our TwiML response
    resp = MessagingResponse()
    resp.message(final)
    return str(resp)

def format_final(db_data):
    final = ""
    first = "1: "
    second ="2: "
    third = "3: "
    fourth = "4: "
    fifth = "5: "
    for i,e in enumerate(db_data):
        temp=list(db_data[i])
        temp[2] = "Next date to book an appointment: " + e[2]
        if e[5]==None: 
            temp[5]='Website not available'
 
        temp[4] = "DISTANCE: "+str(round(e[4],2)) + " Miles"
        db_data[i]=tuple(temp)

    first += str(db_data[0])
    second += str(db_data[1])
    third += str(db_data[2])
    fourth += str(db_data[3])
    fifth += str(db_data[4])

    final = '''This tool is built to find the closest vaccine providers to you.
Providers are listed based on proximity. For more information about Eligible groups, visit: https://www.albertahealthservices.ca/topics/Page17295.aspx
    '''+'\n'+'\n'+first+'\n'+'\n'+second+'\n'+'\n' +third +'\n'+'\n' +fourth+'\n'+'\n' +fifth  + '\n' +'\n' "For more Vaccine providers, visit: https://www.ab.bluecross.ca/news/covid-19-immunization-program-information.php#map" + "\n" +"\n" "If you want to leave feedback or have any comments about the tool, please message me: Musa.mohannad1@gmail.com"
    return final

def makeDb_connection():
    config = {
        'user': 'root',
        'password': os.environ["password_google"],
        'host': os.environ["host"],
        'client_flags': [ClientFlag.SSL],
        'ssl_ca': os.environ["ssl"],
        'ssl_cert': os.environ["client-cert.pem"],
        'ssl_key': os.environ['client-key.pem'],
        'database':'Vaccinesdb'
        }

# now we establish our connection
    cnxn = mysql.connector.connect(**config)
    return cnxn

# def get_lat_lon(body):
#     url = 'http://api.positionstack.com/v1/forward?access_key=&query={}&country=CA&region=Alberta'.format(body)
#     r=requests.get(url).json()
#     try:
#         if len(r["data"]) == 0 or "error" in r:
#             raise Exception
#     except Exception:
#         raise
#     lat = r["data"][0]["latitude"]
#     longitude = r["data"][0]["longitude"]
#     return lat,longitude

def get_lat_lon_prod(body):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?key={}&components=postal_code:{}|country:CA'.format(os.environ
    ["Key"],body)
    r=requests.get(url).json()
    try:
        status_code = r["status"]
        if len(r["results"])==0 or status_code != "OK":
            raise Exception
    except Exception:
        raise
    dict_lat_lon = r["results"][0]["geometry"]["location"]
    lat = dict_lat_lon["lat"]
    longitude = dict_lat_lon["lng"]

    return lat,longitude

def make_query(lat,longitude):
    mydb = makeDb_connection()
    mycursor = mydb.cursor()
    try: 
        sql = '''SELECT name,address, available, phone, SQRT(
        POW(69.1 * (latitude - {}), 2) +
        POW(69.1 * ({} - Longitude) * COS(latitude / 57.3), 2)) AS distance, website
        FROM alberta HAVING distance < 1000 ORDER BY distance LIMIT 5;'''.format(lat,longitude)
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        return myresult
    except Exception:
        raise
    finally:
        mycursor.close()
        mydb.close()

def validate_body(S):
    if len(S) < 3:
        raise Exception
    elif len(S) > 7:
        raise Exception
    elif len(S) == 3:
        try:
            spaceless = S.replace(' ','')
            if not re.match(r"[t|T][0-9][a|a-z|A|A-Z]",spaceless):
                raise Exception
        except Exception:
            raise
        return spaceless.upper()
    else:
        try:
            spaceless = S.replace(' ','')
            if not re.match(r"[t|T][0-9][a-zA-Z][0-9][a-zA-Z][0-9]",spaceless):
                raise Exception
        except Exception:
            raise
        return spaceless.upper()
    

if __name__ == "__main__":
    app.run()

