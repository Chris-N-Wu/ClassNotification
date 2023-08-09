import json
import sys

import requests
from discord import SyncWebhook

import config


class Webhook:
    """This class contains methods to help send information to the desired Discord Webhook"""

    def __init__(self, message):
        self.message = message

    def add_one(self):
        print(self.message + str(3))


# takes the custom json save file
class DataJson:
    """Stores basic information for each course"""

    def __init__(self, json_file_path):
        # file processing
        file = open(file=json_file_path)
        # json object as a dictionary
        json_data = json.load(file)

        self.json_file_path = json_file_path
        self.term_code = json_data['termCode']
        self.course_ids = json_data['ids']
        self.courses = json_data['data']

    """
    Getters
    """

    # adding a course to be tracked
    def add_tracked_course(self, course_id, course_name, course_crn, seats_available, wait_available, subject,
                           course_number):
        # checking that this course hasn't already been added to be tracked
        for course in self.courses:
            if course_id == course['courseId']:
                return

        # adding the course to be tracked
        self.courses.append({'courseId': course_id,
                             'courseName': course_name,
                             'courseCrn': course_crn,
                             'seatsAvailable': seats_available,
                             'waitAvailable': wait_available,
                             'lookupInfo': {'subject': subject,
                                            'courseNumber': course_number}})

    def collect_ids(self):
        ids = []
        for course in self.courses:
            ids.append(course['courseId'])

        return ids

    # saving the current information
    def save_json(self):
        # serializing the json
        json_object = json.dumps({'termCode': self.term_code,
                                  'ids': self.collect_ids(),
                                  'data': self.courses},
                                 indent=2)

        # saving
        with open(self.json_file_path, 'w') as file:
            file.write(json_object)


# Parses Jsons returned from Banner
class BannerDataJson:
    """Breaks down returned Banner JSONs into manageable dictionary"""

    def __init__(self, json_input):
        self.json_input = json_input
        self.courses = self.json_input['data']

    """
    Getters
    """

    def get_course_name(self, course_id):
        for course in self.courses:
            if course['id'] == course_id:
                return course['courseTitle']

    def get_seats_available(self, course_id):
        for course in self.courses:
            if course['id'] == course_id:
                return course['seatsAvailable']

    def get_waitlist_seats(self, course_id):
        for course in self.courses:
            if course['id'] == course_id:
                return course['waitAvailable']


# setting the discord webhook
webhook = SyncWebhook.from_url(url=config.webhook_url)
"""
# gaining access to our session
clickContinue = requests.post(
    url="https://nubanner.neu.edu/StudentRegistrationSsb/ssb/term/search?mode=search",
    data={
        "term": "202410"
    },
)

# parsing the returned session
headers = clickContinue.headers['Set-Cookie']
headers = headers.split(';')
# retrieving the JSESSIONID
jsessionid = headers[0].split('=')[1]
# retrieving nu banner-cookie
nu_banner_cookie = headers[3].split('=')[1]

# setting cookies
cookies = {"nubanner-cookie": nu_banner_cookie, "JSESSIONID": jsessionid}

# # resets input from last search
# post = requests.post(
#     url='https://nubanner.neu.edu/StudentRegistrationSsb/ssb/classSearch/resetDataForm',
#     cookies=cookies
# )

get = requests.get(
    url='https://nubanner.neu.edu/StudentRegistrationSsb/ssb/searchResults/searchResults?'
        'txt_subject=CS'
        '&txt_courseNumber=3200'
        '&txt_term=202410'
        '&startDatepicker=&endDatepicker=&pageOffset=0'
        '&pageMaxSize=100'
        '&sortColumn=subjectDescription&sortDirection=asc',
    cookies=cookies
)
print(get.text)

response_json = get.json()


seats_remaining = response_json['data'][1]['seatsAvailable']

# user id for Dolphins0248
# webhook.send('<@350046129892622336> IT WORKS!!!')
# webhook.send("Database Design Has " + str(seats_remaining) + " Seats Remaining")
"""

if __name__ == '__main__':
    # term code for Fall 2023-24 school year
    term_code = '202410'

    # gaining access to our session
    clickContinue = requests.post(
        url="https://nubanner.neu.edu/StudentRegistrationSsb/ssb/term/search?mode=search",
        data={
            "term": "202410"
        },
    )

    # parsing the returned session
    headers = clickContinue.headers['Set-Cookie']
    headers = headers.split(';')
    # retrieving the JSESSIONID
    jsessionid = headers[0].split('=')[1]
    # retrieving nu banner-cookie
    nu_banner_cookie = headers[3].split('=')[1]

    # setting cookies
    cookies = {"nubanner-cookie": nu_banner_cookie, "JSESSIONID": jsessionid}

    # loading saved data
    saved_data = DataJson('data.json')  # TODO: Replace hard coded path

    # looping through each course in the saved courses to check their enrollment numbers
    for course in saved_data.courses:
        subject = course['lookupInfo']['subject']
        course_number = course['lookupInfo']['courseNumber']

        # string for course lookup
        search_url = 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/searchResults/searchResults?' \
                     f'txt_subject={subject}' \
                     f'&txt_courseNumber={course_number}' \
                     f'&txt_term={term_code}' \
                     '&startDatepicker=' \
                     '&endDatepicker=&pageOffset=0' \
                     '&pageMaxSize=100' \
                     '&sortColumn=subjectDescription&sortDirection=asc'

        print(search_url)

        get = requests.get(url=search_url,
                           cookies=cookies)

        # print(get.json())
        banner_data = BannerDataJson(get.json())
        print(course['courseName'])
        print(banner_data.get_seats_available(course['courseId']))

        # resets input from last search
        post = requests.post(
            url='https://nubanner.neu.edu/StudentRegistrationSsb/ssb/classSearch/resetDataForm',
            cookies=cookies
        )

