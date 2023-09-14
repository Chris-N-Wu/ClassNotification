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
        self.courses = json_data['data']

    """
    Getters
    """

    def get_seats_available(self, course_crn):
        for course in self.courses:
            if course_crn == course['courseCrn']:
                return course['seatsAvailable']

    # updating the number of seats available for this course
    def update_course_seats(self, course_crn, new_seats):
        # something cool, 'course' is a reference to the particular item in the list,
        # so when updating 'course', the item itself in the list is updated as well
        for course in self.courses:
            if course_crn == course['courseCrn']:
                course['seatsAvailable'] = new_seats

    # adding a course to be tracked
    def add_tracked_course(self, course_name, course_crn, seats_available, wait_available, subject,
                           course_number):
        # checking that this course hasn't already been added to be tracked
        for course in self.courses:
            if course_crn == course['courseCrn']:
                print("Error: Course Already Exists In System!")
                return

        # adding the course to be tracked
        self.courses.append({'courseName': course_name,
                             'courseCrn': course_crn,
                             'seatsAvailable': seats_available,
                             'waitAvailable': wait_available,
                             'lookupInfo': {'subject': subject,
                                            'courseNumber': course_number}})

    # saving the current information
    def save_json(self):
        # serializing the json
        json_object = json.dumps({'termCode': self.term_code,
                                  'data': self.courses},
                                 indent=2)

        # saving
        with open(self.json_file_path, 'w') as file:
            file.write(json_object)


# Parses Jsons returned from Banner
class BannerDataJson:
    """Breaks down returned Banner JSONs into manageable dictionary"""

    def __init__(self, json_output):
        self.json_input = json_output
        self.courses = json_output['data']

    def __getitem__(self, item):
        return self.json_input[item]

    def validate_crn(self, course_crn):
        course_crn_list = []

        for course in self.courses:
            course_crn_list.append(course['courseReferenceNumber'])

        if str(course_crn) not in course_crn_list:
            return 0
        else:
            return 1

    """
    Getters
    """

    def get_course_name(self, course_crn):
        for course in self.courses:
            if course['courseReferenceNumber'] == str(course_crn):
                return course['courseTitle']

    def get_seats_available(self, course_crn):
        for course in self.courses:
            if course['courseReferenceNumber'] == str(course_crn):
                return course['seatsAvailable']

    def get_waitlist_seats(self, course_crn):
        for course in self.courses:
            if course['courseReferenceNumber'] == str(course_crn):
                return course['waitAvailable']


# user id for Dolphins0248
# webhook.send('<@350046129892622336> IT WORKS!!!')
# webhook.send("Database Design Has " + str(seats_remaining) + " Seats Remaining")


# string for course_data lookup
def search_url(subject, course_number):
    return 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/searchResults/searchResults?' \
           f'txt_subject={subject}' \
           f'&txt_courseNumber={course_number}' \
           f'&txt_term={config.term_code}' \
           '&startDatepicker=' \
           '&endDatepicker=&pageOffset=0' \
           '&pageMaxSize=100' \
           '&sortColumn=subjectDescription&sortDirection=asc'


class Application:
    def __init__(self, saved_data_path):
        self.saved_data_path = saved_data_path
        start_data = self.start_app()
        self.cookies = start_data[0]
        self.saved_data = start_data[1]

    def start_app(self):
        # gaining access to our session
        start_session = requests.post(
            url='https://nubanner.neu.edu/StudentRegistrationSsb/ssb/term/search?mode=search',
            data={
                'term': config.term_code
            },
        )

        # parsing the returned session
        headers = start_session.headers['Set-Cookie']
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

            get = requests.get(url=search_url(subject, course_number),
                               cookies=self.cookies)

            banner_data = BannerDataJson(get.json())

            curr_time = time.strftime("%H:%M:%S")
            print(curr_time, "-", course_data['courseName'])
            print(banner_data.get_seats_available(course_data['courseCrn']), "Seats")

            # if banner_data.get_seats_available(course_data['courseCrn']) != \
            #         self.saved_data.get_seats_available(course_data['courseCrn']):
            #     print("A")

            banner_seats_available = banner_data.get_seats_available(course_data['courseCrn'])
            if (banner_seats_available > 0
                    and banner_seats_available != self.saved_data.get_seats_available(course_data['courseCrn'])):
                data = {'content': f'{config.discord_user_id} A Seat Is Open in '
                                   + course_data['courseName']
                                   + ", CRN: "
                                   + str(course_data['courseCrn'])}
                requests.post(url=config.webhook_url,
                              data=data)

            self.reset_inputs()

    # Allows user to add new course to tracked courses
    def add_course(self, subject, course_number, course_crn):
        # Finding the course
        get = requests.get(url=search_url(subject, course_number),
                           cookies=self.cookies)

        # converting to custom parsable class
        banner_data = BannerDataJson(get.json())

        print(get.text)

        if banner_data.validate_crn(course_crn) == 0:
            print("INVALID SEARCH")
            return

        if not (banner_data['totalCount'] == 0):
            self.saved_data.add_tracked_course(course_name=banner_data.get_course_name(course_crn),
                                               course_crn=course_crn,
                                               seats_available=banner_data.get_seats_available(course_crn),
                                               wait_available=banner_data.get_waitlist_seats(course_crn),
                                               subject=subject,
                                               course_number=course_number)

            self.saved_data.save_json()
        else:
            print("INVALID FIELD PROVIDED")

    def reset_inputs(self):
        # resets input from last search
        requests.post(
            url='https://nubanner.neu.edu/StudentRegistrationSsb/ssb/classSearch/resetDataForm',
            cookies=self.cookies
        )


if __name__ == '__main__':
    myApplication = Application('dataActual.json')

    # myApplication.add_course(subject="MATH", course_number=2341, course_crn=12074)

    while True:
        myApplication.lookup_courses()
        time.sleep(15)
