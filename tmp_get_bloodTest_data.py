#!/usr/bin/env python



import requests

# Airtable API details
base_id = 'appL3Wb1C7NvHTDl1'
table_name = 'BloodTest'
api_key = 'keyBQivgbhrgIZQS9'

# Airtable API endpoint URL
url = f'https://api.airtable.com/v0/{base_id}/{table_name}'

# Request headers with API key
headers = {
    'Authorization': f'Bearer {api_key}'
}

# Send GET request to fetch the table data
response = requests.get(url, headers=headers)
data = response.json()

# Extract column names
columns = data['records'][0]['fields'].keys()

# Store column names in a text file
with open('column_names.txt', 'w') as file:
    for column in columns:
        file.write(column + '\n')

print('Column names extracted and stored in column_names.txt')

