'''
Purpose:	A set of common resources used between many of the job sites.
'''

from requestium import Session
from selenium.common.exceptions import NoSuchElementException
import os

working_dir = os.getcwd()
CHROME_DRIVER_PATH = working_dir + r"\chromedriver.exe"

class RequestiumSession(Session):

    @staticmethod
    def element_exists(xDoc, xpath):
        '''
		Purpose:	Check if element exists in selenium driver xpath.
		Arguments:
			xpath - str - xpath to the element(s) you are searching for
			driver - bool - True when
		Returns:
			True/False - bool - True if element found. False otherwise.
		'''
        try:
            if hasattr(xDoc, 'find_element_by_xpath'):  # check if this is selenium driver
                xDoc.find_element_by_xpath(xpath)
            else:  # if not selenium driver, assume parsel doc
                xDoc.xpath(xpath)
            return True
        except NoSuchElementException:
            return False


def _getSession(DriverPath=CHROME_DRIVER_PATH
                , BrowserName='chrome', TimeOut=15
                , WebdriverOptions={}
                , Headless=True):
    """
	Purpose:	Get a new requestium session.
	ArgumentS:
		DriverPath - str - [ optional ] path to the browser driver. Default is chrome.
		BrowserName - str - [ optiona ] name of the browser
		TimeOut - int - how many seconds before a request times out
	Returns:
		Session - requestium.Session - a requestium Session instance
	"""

    # SET SELENIUM HEADLESS, SO BROWSER IS INVISIBLE
    if Headless:
        if isinstance(WebdriverOptions, dict):
            if 'arguments' in WebdriverOptions:
                WebdriverOptions['arguments'].append('headless')
            else:
                WebdriverOptions.update({'arguments': ['headless']})
        else:
            WebdriverOptions = {'arguments': ['headless']}

    return RequestiumSession(webdriver_path=DriverPath, browser=BrowserName
                             ,
                             default_timeout=TimeOut, webdriver_options=WebdriverOptions
                             )