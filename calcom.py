import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
import json


def get_current_time():
    # Get the current time in UTC
    current_time = datetime.now(timezone.utc)

    # Format the time as a string
    formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    return formatted_time


class CalAPI:
    BASE_URL = "https://api.cal.com/v1/"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        self.default_params = {"apiKey": self.api_key}

    def fetch(self, endpoint, params=None):
        if params is None:
            params = {}
        params.update(self.default_params)
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return {"error": "Unauthorized. Check your API key."}
        elif response.status_code == 404:
            return {"error": "Not Found."}
        else:
            return {"error": f"Unexpected error: {response.status_code}"}

    def post(self, endpoint, data):
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.post(
            url, headers=self.headers, params=self.default_params, json=data
        )
        if response.status_code in {200, 201}:
            return response.json()
        elif response.status_code == 401:
            return {"error": "Unauthorized. Check your API key."}
        elif response.status_code == 404:
            return {"error": "Not Found."}
        else:
            print(response.json())
            return {"error": f"Unexpected error: {response.status_code}"}

    def patch(self, endpoint, data):
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.patch(
            url, headers=self.headers, params=self.default_params, json=data
        )
        print(response.text)
        if response.status_code in {200, 201}:
            return response.json()
        elif response.status_code == 401:
            return {"error": "Unauthorized. Check your API key."}
        elif response.status_code == 404:
            return {"error": "Not Found."}
        else:
            print(response.json())
            return {"error": f"Unexpected error: {response.status_code}"}

    def delete(self, endpoint):
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.delete(
            url, headers=self.headers, params=self.default_params
        )
        if response.status_code == 200:
            return {"message": "Deleted successfully"}
        elif response.status_code == 401:
            return {"error": "Unauthorized. Check your API key."}
        elif response.status_code == 404:
            return {"error": "Not Found."}
        else:
            print(response.json())
            return {"error": f"Unexpected error: {response.status_code}"}

    def get_users(self, email=None):
        params = {}
        if email:
            params["email"] = email
        return self.fetch("users", params)

    def get_bookings(self):
        return self.fetch("bookings")

    def get_event_types(self):
        return self.fetch("event-types")

    def cancel_meeting(self, id):
        return self.delete(f"bookings/{id}/cancel")

    def reschedule_meeting(self, id, new_time):
        print()
        print("reschedule", id, new_time)
        print()
        return self.patch(f"bookings/{id}", {"startTime": new_time})

    def create_booking(
        self,
        start,
        title,
    ):
        data = {
            "eventTypeId": 888704,
            "start": start,
            "title": title,
            "responses": {
                "name": "Bharath Sriraam R R",
                "email": "bharathsriraam.rr@gmail.com",
                "notes": "First meeting",
                "phone": "123456789",
                "guests": [],
            },
            "metadata": {},
            "timeZone": "America/New_York",
            "language": "en",
        }
        return self.post("bookings", data)


if __name__ == "__main__":

    load_dotenv()

    # Example usage
    api_key = os.environ.get("CALCOM_API_KEY")
    api = CalAPI(api_key)

    # Get all users
    # users = api.get_users()
    # print("Users", users)

    # Get event types
    # print("Event types", api.get_event_types())

    # Get bookings
    # print("Bookings", json.dumps(api.get_bookings(), indent=2))

    # Create a new booking
    booking_data = {
        "start": "2024-07-02T10:40:00.332Z",
        "title": "Meeting with John",
    }
    # booking = api.create_booking(**booking_data)
    # print(booking)

    # Reschedule meeting
    print(
        api.reschedule_meeting(
            id=2461847, new_time="2023-07-03T15:00:00.000-04:00"
        )
    )
