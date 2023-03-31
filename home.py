from flask import Flask, render_template, request, jsonify

import sqlalchemy as sa
import pandas as pd
import datetime as dt

# Database credentials
dbUser = "database user"
dbpw = "user password"
host = "database host server"
dbname = "database name"

# Name of table to store the posted information
tbname_rht_readings = "rht_readings"

print("Acessing database....")
engine = sa.create_engine("mysql://"+dbUser+":"+dbpw+"@"+host+"/"+dbname,echo=True)


app = Flask(__name__, static_folder='static')

# ----- function to render the main home page
@app.route('/')
def home():
	# get a list of unique student ID numbers
	print('Testing')
	qry = 'SELECT DISTINCT id_number FROM '+tbname_rht_readings+' ORDER BY ukey ASC'
	id_numbers = pd.read_sql_query(qry, engine)

	# create an empty dataframe 'full_list' with the following column names
	COLUMN_NAMES=['name','location','id_number','device_mac','first_dt','last_dt','temperature','humidity']
	full_list = pd.DataFrame(columns=COLUMN_NAMES)
	# loop thru all unique ID numbers
	for ids in id_numbers['id_number']:
		print(ids)
		# pull from DB the latest readings
		qry = 'SELECT * FROM '+tbname_rht_readings+' WHERE id_number='+str(ids)+' ORDER BY datetime DESC LIMIT 1'
		latest_readings = pd.read_sql_query(qry, engine)
		temp_df = pd.DataFrame([[latest_readings['name'].iloc[0],latest_readings['location'].iloc[0],latest_readings['id_number'].iloc[0],latest_readings['device_mac'].iloc[0],'',latest_readings['datetime'].iloc[0],latest_readings['temperature'].iloc[0],latest_readings['humidity'].iloc[0]]], columns=COLUMN_NAMES)
		print(temp_df)
		# pull from DB the first readings
		qry = 'SELECT * FROM '+tbname_rht_readings+ ' WHERE id_number='+str(ids)+' ORDER BY datetime ASC LIMIT 1'
		first_readings = pd.read_sql_query(qry, engine)
		temp_df['first_dt'].iloc[0] = first_readings['datetime'].iloc[0]
		full_list = pd.concat([full_list,temp_df])
	print(full_list)
	return render_template('index.html',full_list=full_list)

# ----- retrieve sensor readings of a user by his/her id number and rendering or displaying them on chart.html using Chart JS
@app.route('/<id_num>')
def chart(id_num):
	# get RHT readings of used 'id_num'
	qry = 'SELECT * FROM '+tbname_rht_readings+' WHERE id_number='+id_num
	rht_readings = pd.read_sql_query(qry, engine)
	device_mac = rht_readings['device_mac'].iloc[-1]
	name = rht_readings['name'].iloc[-1]
	location = rht_readings['location'].iloc[-1]
	print(rht_readings)

	# --- get last 24 hours only
	end = rht_readings['datetime'].iloc[-1]
	start = end - dt.timedelta(hours=24)
	ex_i_g = rht_readings['datetime'] >= start
	ex_i_l = rht_readings['datetime'] <= end
	ts_24 = rht_readings['datetime'][ex_i_g & ex_i_l]
	t_24 = rht_readings['temperature'][ex_i_g & ex_i_l]
	h_24 = rht_readings['humidity'][ex_i_g & ex_i_l]
	#labels = [row.strftime("%Y-%m-%d+%H:%M:%S") for row in ts_24]
	labels = [row.strftime("%Y-%m-%d %H:%M:%S") for row in ts_24]
	t_values = [row for row in t_24]
	h_values = [row for row in h_24]
	return render_template('chart.html', labels=labels, t_values=t_values, h_values=h_values, device_mac=device_mac, name=name, location=location)


# ----- Post API
@app.route('/post', methods = ['POST'])
def api_post():
	content = request.get_json()
	date_in = dt.date.strftime(dt.datetime.today()+ dt.timedelta(hours=8), '%Y-%m-%d %H:%M:%S')
	# -- Example of how the POSTED JSON object should be formatted:
	# {"name" : "Some name", "location" : "some address", "id_number" : 123456, "device_mac" : "mac address",  "temperature" : 25.23, "humidity": 58.98}

	# Check if JSON format is valid
	keys = ["name", "location", "id_number", "device_mac", "temperature", "humidity"]

	for val in keys:
		if val not in content:
			print("Invalid JSON format. Missing the key '"+val+"'")
			return 'Error posting the information. Invalid JSON format. Missing the key "'+val+'".'
		else:
		    if content[val] == "":
		        print("Invalid JSON. The value of key '"+val+"' is missing.")
		        return 'Error posting the information. Invalid JSON. The value of key "'+val+'" is missing.'

	insert_req=engine.execute("INSERT INTO  "+tbname_rht_readings+" (name,location,id_number,device_mac,datetime,temperature,humidity) VALUES ('"+content["name"]+"','"+content["location"]+"','"+str(content["id_number"])+"','"+content["device_mac"]+"','"+date_in+"','"+str(content["temperature"])+"','"+str(content["humidity"])+"')")

	return 'JSON posted successfully.'



# ----- GET API (will send all the readings of  )
@app.route('/get/<id_num>', methods = ['GET'])
def api_get(id_num):
	qry = "SELECT * FROM "+tbname_rht_readings+" WHERE id_number="+id_num
	rht_readings = pd.read_sql_query(qry, engine)
	print(rht_readings)
	data = []
	for index, row in rht_readings.iterrows():
		data.append({'name': row['name'], 'location': row['location'], 'temperature': row['temperature'], 'humidity': row['humidity']})
	print(type(data))
	return jsonify(data)

# ----- Testing flask deploymeny
@app.route('/test')
def test():
	return 'Flask app posted'


