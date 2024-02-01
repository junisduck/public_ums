import json
import datetime
import re
from fastapi import FastAPI, Response, Request
import uvicorn
import requests

app = FastAPI()

global url
url = 'https://ums.dreamline.co.kr/API/send_kkt.php'

@app.get("/")
def test():
    return {"hello": "get test"}

@app.post("/webhook")
async def receive_webhook(data_received: dict, request: Request):
    client_ip = request.client.host
    print(client_ip)

    #request method POST or GET
    if client_ip in ['${ip}', '${ip}'] and request.method in ('POST', 'GET'):
        try:
            #grafana webhook alert json data
            data = await request.body()
            if data:
                save_json_to_file(data_received)
                json_data = data_received
                alerts = json_data.get('alerts', [])
                for alert in alerts:
                    status = alert.get('status', '')
                    if status == 'firing':
                        parsing2(json_data)
                    elif status == 'resolved':
                        # Add resolved alert handling logic here
                        pass
                return {"message": "success"}
        except json.JSONDecodeError:
            return Response(content=json.dumps({"message": "Invalid JSON format"}), status_code=400)
        except Exception as e:
            return Response(content=json.dumps({"message": f"Error: {str(e)}"}), status_code=500)
    else:
        return Response(content=json.dumps({"message": "Only POST requests are allowed"}), status_code=405)

def save_json_to_file(json_data):
    # Generate a unique filename using the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    # Set the absolute path to the desired directory and filename
    filename = ${path} + timestamp + '.json'

    # Convert JSON data to a formatted string
    json_string = json.dumps(json_data, indent=2)

    # Save JSON data to a file
    with open(filename, "w") as file:
        file.write(json_string)

    print(f"JSON data saved to {filename}")

def parsing2(data):
    alerts = data.get('alerts', [])

    for alert in alerts:
        status = alert.get('status', '')
        if status == 'firing':
            server_time = alert.get('startsAt', '')
            parsed_time = datetime.datetime.strptime(server_time[:-1], '%Y-%m-%dT%H:%M:%S')
            formatted_time = parsed_time.strftime('%Y-%m-%d %H:%M:%S')

            instance_match = re.search(r'instance=([\d\.]+)', alert.get('valueString', ''))
            instance = instance_match.group(1) if instance_match else ''

            value_match = re.search(r'value=([\d.]+)', alert.get('valueString', ''))
            value = float(value_match.group(1)) if value_match else 0

            job_match = re.search(r'job=(\w+)', alert.get('valueString', ''))
            job = job_match.group(1) if job_match else ''

            if not job:
                job = ''

            metric_type = ""
            labels = alert.get('labels', {})
            alertname = labels.get('alertname', '')
            if "cpu" in alertname:
                metric_type = "cpu"
            elif "mem" in alertname:
                metric_type = "mem"
            elif "disk" in alertname:
                metric_type = "disk"

            error_send_message(status, formatted_time, instance, value, metric_type, job)

def error_send_message(status, formatted_time, instance, value, metric_type, job):
    work_phone = '${phone number}'
    leader_phone = '${phone number}'
    company = '${company}'
    person = '${name}'
    #ums format
    datas = {
        'id_type': '',
        'id': '',
        'auth_key': '',
        'msg_type': '',
        'callback_key': '',
        'send_id_receive_number': '',
        'template_code': '',
        'content': '',
        'resend': ''
    }

    try:
        response = requests.post(url, data=datas, timeout=5)
        response.raise_for_status()
        print(json.loads(response.text))
    except requests.exceptions.RequestException as e:
        print(f"Failed to send HTTP request: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5555, log_level="debug", reload=True)
