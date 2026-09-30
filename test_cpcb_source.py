import requests

def test_openaq_v3():
    print("Testing OpenAQ API v3...")
    url = "https://api.openaq.org/v3/locations"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("Success! Data:", response.json())
    except Exception as e:
        print(f"Error accessing OpenAQ v3: {e}")

if __name__ == "__main__":
    test_openaq_v3()
