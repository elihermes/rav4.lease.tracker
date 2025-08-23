import requests

for i in range(1, 11):
    print(f"Run number: {i}")


response = requests.get(
        "https://wttr.in/New+York?format=3"
    )
if response.status_code == 200:
    print("Current weather in NYC:", response.text.strip())
else:
    print("Could not retrieve weather information.")