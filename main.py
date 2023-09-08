import json
import time

import requests

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

    def get_seats_available(self, course_id):
        for course in self.courses:
            if course_id == course['courseId']:
                return course['seatsAvailable']

    # updating the number of seats available for this course
    def update_course_seats(self, course_id, new_seats):
        # something cool, 'course' is a reference to the particular item in the list,
        # so when updating 'course', the item itself in the list is updated as well
        for course in self.courses:
            if course_id == course['courseId']:
                course['seatsAvailable'] = new_seats

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


# user id for Dolphins0248
# webhook.send('<@350046129892622336> IT WORKS!!!')
# webhook.send("Database Design Has " + str(seats_remaining) + " Seats Remaining")


class Application:
    def __init__(self, saved_data_path):
        self.saved_data_path = saved_data_path
        start_data = self.start_app()
        self.cookies = start_data[0]
        self.saved_data = start_data[1]

    def start_app(self):
        # gaining access to our session
        click_continue = requests.post(
            url='https://nubanner.neu.edu/StudentRegistrationSsb/ssb/term/search?mode=search',
            data={
                'term': config.term_code
            },
        )

        # parsing the returned session
        headers = click_continue.headers['Set-Cookie']
        headers = headers.split(';')
        # retrieving the JSESSIONID
        jsessionid = headers[0].split('=')[1]
        # retrieving nu banner-cookie
        nu_banner_cookie = headers[3].split('=')[1]

        # setting cookies
        cookies = {"nubanner-cookie": nu_banner_cookie, "JSESSIONID": jsessionid}

        # loading saved data
        saved_data = DataJson(self.saved_data_path)

        return cookies, saved_data

    def lookup_courses(self):
        # looping through each course_data in the saved courses to check their enrollment numbers
        for course_data in self.saved_data.courses:
            subject = course_data['lookupInfo']['subject']
            course_number = course_data['lookupInfo']['courseNumber']

            # string for course_data lookup
            search_url = 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/searchResults/searchResults?' \
                         f'txt_subject={subject}' \
                         f'&txt_courseNumber={course_number}' \
                         f'&txt_term={config.term_code}' \
                         '&startDatepicker=' \
                         '&endDatepicker=&pageOffset=0' \
                         '&pageMaxSize=100' \
                         '&sortColumn=subjectDescription&sortDirection=asc'

            get = requests.get(url=search_url,
                               cookies=self.cookies)

            # print(get.json())
            banner_data = BannerDataJson(get.json())
            print(course_data['courseName'])
            print(banner_data.get_seats_available(course_data['courseId']))

            if banner_data.get_seats_available(course_data['courseId']) != \
                    self.saved_data.get_seats_available(course_data['courseId']):
                print("A")

            self.reset_inputs()

            data = {'content': "HI!"}
            requests.post(url=config.webhook_url, data=data)

    def reset_inputs(self):
        # resets input from last search
        requests.post(
            url='https://nubanner.neu.edu/StudentRegistrationSsb/ssb/classSearch/resetDataForm',
            cookies=self.cookies
        )


if __name__ == '__main__':

    myApplication = Application('data.json')

    while True:
        myApplication.lookup_courses()
        time.sleep(15)
