from selenium import webdriver
import re

import twlog

logger = twlog.TimeWatchLogger()

class TimeWatch:
    """
    Class that embodies TimeWatch data/site.
    This class is a context manager.
    `with` statement opens a chrome driver instance and logs into *TimeWatch* site.
    """
    
    _user_cred = ''
    _url = r'https://checkin.timewatch.co.il/punch/punch.php'

    def __init__(self, chrome_driver, params):        
        self._user_cred = params.parameters['user']
        self.chrome_driver = chrome_driver
        self._driver = None

    def __enter__(self):
        self._driver = webdriver.Chrome(self.chrome_driver.driver_path)
        self.login_into_time_watch()
        return self

    def __exit__(self, *exception):
        self._driver.close()

    def login_into_time_watch(self):
        """
        Login into Timewatch website.
        user login information from params file
        """
        logger.debug('Try to login to %s', self._url)
        self._driver.get(self._url)
        self._driver.find_element_by_xpath('// *[@id="compKeyboard"]').send_keys(self._user_cred['company'])
        self._driver.find_element_by_xpath('//*[@id="nameKeyboard"]').send_keys(self._user_cred['worker'])
        self._driver.find_element_by_xpath('//*[@id="pwKeyboard"]').send_keys(self._user_cred['pswd'])
        self._driver.find_element_by_xpath(
            '//*[@id="cpick"]/table/tbody/tr[1]/td/div/div[2]/p/table/tbody/tr[4]/td[2]/input').click()
        logger.info('Logged in for worker %s', self._user_cred['worker'])

    def edit_single_date(self, start_time, end_time, download_date):
        """
        Enter values into a single date form
        :param tuple start: the time of the start end of the workday
        :param tuple end: the time of the end of the workday
        :param datetime download_date: the date of the kml data
        :return: Nothing
        """
        self._driver.get(self._generate_specific_date_url(edit_date=download_date))
        self._enter_value(x_path='ehh', value=start_time.hour)
        self._enter_value(x_path='emm', value=start_time.minute)
        self._enter_value(x_path='xhh', value=end_time.hour)
        self._enter_value(x_path='xmm', value=end_time.minute)

        enter = self._driver.find_element_by_xpath(
            '/html/body/div/span/form/table/tbody/tr[8]/td/div/div[2]/p/table/tbody/tr[9]/td/input')

        enter.click()

        logger.info('Finished updating for %s', download_date.strftime('%d-%m-%Y'))

    def _enter_value(self, x_path, value):
        """
        Enter values into specific place in webpage - specified by x_path

        :param str x_path: portion of the x_path required to uniquely identify enter/exit hour/minute box
        :param str value: hours/minute in 24H format to be entered to the element located using x_path parameter
        :return:
        """
        element = self._driver.find_element_by_xpath('//*[@id="' + x_path + '0"]')
        element.clear()
        element.send_keys(value)
        logger.debug('Entered %s into element %s', value, element.id)

    def _generate_specific_date_url(self, edit_date):
        """
        generate url for specific date edit form in the TimeWatch webpage.
        requires session to be logged in

        :param datetime edit_date: date that needs to be edited
        :return str: url for direct edit form for edit_date
        """
        elems = [e.get_attribute('href') for e in self._driver.find_elements_by_xpath("//a[@href]")]
        elems = [e for e in elems if 'editwh.php' in e]
        try:
            match = re.search(pattern=('(?<=ee\=)\d*(?=\&e)'), string=elems[0])
        except IndexError as e:
            raise IndexError('source of html page has no href with token')
        
        if match:
            self._user_cred['token'] = match[0]
        else:
            raise ValueError('did not extract token from %s', elems[0])

        base_url = 'http://checkin.timewatch.co.il/punch/editwh2.php?ie='
        comp_num = str(self._user_cred['company']) + '&e=' + str(self._user_cred['token']) + '&d='
        start_date = str(edit_date.year) + '-' + str(edit_date.month) + '-' + str(edit_date.day) + '&jd='
        end_date = str(edit_date.year) + '-' + str(edit_date.month) + '-' + str(edit_date.day + 1) + '&tl=' \
                    + str(self._user_cred['token'])
        return base_url + comp_num + start_date + end_date



