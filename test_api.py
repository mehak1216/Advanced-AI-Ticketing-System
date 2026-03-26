import requests

# Test create ticket
response = requests.post('http://localhost:8001/api/tickets', json={
    'title': 'Password reset needed',
    'description': 'I forgot my password and need to reset it.'
})

print(response.status_code)
print(response.text)