
from common_resources import _getSession, RequestiumSession
from time import sleep
import fire, types, os, magic, re
from tqdm import tqdm
from collections import namedtuple

SITE = {
    'root'		    :	'https://www.ziprecruiter.com'
    ,'login'	    :	'/login?realm=candidates'
    ,'postlogin'    :   'https://www.ziprecruiter.com/candidate/suggested-jobs'
    ,'resume'       :   {
        'root'  :   '/candidate/resume'
        ,'data' :   {
            '_safesave'     :   ''
            ,'_token'       :   ''
            ,'resume_text'  :   ''
        }
        ,'files':   {
            'resume'    :   ()
        }
    }
    ,'applied_jobs' :   '/candidate/my-jobs?page={PageNumber}'
    ,'search'	    :	{
        'root'	: 	'/candidate/search?'
        ,'keywords'			: 'search={0}'
        ,'posteddaysago' 	: 'days={0}'
        ,'salary'			: 'refine_by_salary={0}'
        ,'type'				: {
            'root'		:	'refine_by_tags=employment_type:{0}'
            ,'options'	:	{
                'part_time'			:	'part_time'
                ,'full_time'		:	'full_time'
                ,'contract'			:	'contract'
                ,'contract_to_hire'	:	'contract_to_hire'
                ,'temporary'		:	'temporary'
                ,'internship'		:	'internship'
            }
        }
    }
}

SearchResult = namedtuple( 'SearchResult', "ApplyLink, DetailsLink" )

class ZipRecruiter():

    def __init__( self, oSession=None, Headless=True, solveCaptcha=None ):
        '''
        Arguments:
            solveCaptcha - method - captcha solving method. whatever
                                    method you are using to solve captchas.
        '''
        self._session = None
        self.username = None
        self.password = None
        self.resume = None
        self.solveCaptcha = solveCaptcha
        self._headless = Headless
        if oSession != None:
            if not isinstance( oSession, RequestiumSession ):
                raise ValueError( 'ERROR : NOT A REQUESTIUMSESSION INSTANCE' )
            self._session = oSession
        else:
            self._session = _getSession( Headless=self._headless )

    def login( self, Username=None, Password=None, CloseDriverOnComplete=True ):
        '''
        Purpose:	Login to the site on behalf of the user.
        Arguments:
            Username - str - the email of the user
            Password - str - the password of this user for this job site
            CloseDriverOnComplete - bool - [ optional ] True if this is a retry of the login.
                                            when True, the driver will be quit after successfully
                                            logging in.
        Returns:
            True/False - bool - True if successful. False if login creds did not work.
        '''

        # CHECK FOR USER CREDS
        if Username == None:
            if self.username == None:
                raise ValueError( 'ERROR : USERNAME REQUIRED' )
        else:
            self.username = Username
        if Password == None:
            if self.password == None:
                raise ValueError( 'ERROR : PASSWORD REQUIRED' )
        else:
            self.password = Password

        # ATTEMPT LOGIN
        self._session.driver.get( SITE[ 'root' ] + SITE[ 'login' ] )
        self._session.driver.find_element_by_xpath(
            "//input[@name='email']" ).send_keys( self.username )
        self._session.driver.find_element_by_xpath(
            "//input[@name='password']" ).send_keys( self.password )
        self._session.driver.find_element_by_xpath(
            "//input[@type='submit']").click()

        # CHECK FOR CAPTCHA
        if self._session.element_exists( self._session.driver, "//script[@data-sitekey]" ):

            # TRY PROGRAMMATIC CAPTCHA SOLUTION
            if self.solveCaptcha != None:
                CaptchaSiteKey = self._session.driver.find_element_by_xpath(
                    "//script[@data-sitekey]" ).get_attribute( 'data-sitekey' )
                CaptchaSolution = self.solveCaptcha( CaptchaSiteKey )
                self._session.driver.execute_script(
                    "document.getElementById('g-recaptcha-response').setAttribute('value', '" + \
                    CaptchaSolution + "')")

            # NEED HUMAN INTERVENTION
            else:

                # IF RUNNING HEADLESS, NEED TO RESTART SO USER CAN SOLVE
                if self._headless:
                    Headless = self._headless
                    self._headless = False
                    self._session.driver.quit()
                    self._session = None
                    self._session = _getSession( Headless=False
                                                 ,WebdriverOptions={} )
                    self.login( self.username, self.password, False )
                    self._headless = Headless

                # WAIT FOR USER TO SOLVE
                else:
                    while self._session.driver.current_url == \
                        SITE['root'] + SITE['login']:
                        sleep( 0.1 )

        # IF BAD LOGIN CREDS
        if self._session.element_exists( \
            self._session.driver, "//div[contains(text(),'Incorrect email or password')]" ):
            return False

        # IF STILL ON THE LOGIN PAGE, BUT NO ERROR
        elif self._session.driver.current_url == SITE[ 'root' ] + SITE[ 'login' ]:
            raise ValueError( 'ERROR : LOGIN FAILED' )

        # COPY SESSION TO REQUESTS SESSION
        self._session.transfer_driver_cookies_to_session()

        # CLOSE BROWSER UNLESS IN DEBUG MODE - ALL OTHER METHODS USE REQUESTS
        if CloseDriverOnComplete:
            self._session.driver.quit()

        return True

    def uploadResume( self, FilePath=None ):
        '''
        Purpose:    Upload a resume to ZipRecruiter.
        Arguments:
            FilePath - str - path to the resume you want to upload
        Returns:
            True/False - bool - True if upload successful. False otherwise.
        '''
        
        # VALIDATE USER INPUTS
        if FilePath == None:
            if self.resume == None:
                raise ValueError( 'ERROR : RESUME FILE PATH REQUIRED' )
        else:
            self.resume = FilePath
        if not os.path.isfile( FilePath ):
            raise ValueError( 'ERROR : FILE DOES NOT EXIST' )
        
        ResumePostURL = SITE[ 'root' ] + SITE[ 'resume' ][ 'root' ]

        # GET UPLOAD TOKEN
        ResumeUploadPage = self._session.get( ResumePostURL )
        Token = ResumeUploadPage.xpath('//input[@name="_token"]/@value')[ 0 ].extract()

        # BUILD UPLOAD DATA
        Data = SITE[ 'resume' ][ 'data' ]
        Data[ '_safesave' ] = self._session.cookies[ 'SAFESAVE_TOKEN' ]
        Data[ '_token' ] = Token

        # BUILD FILE DATA
        Files = SITE[ 'resume' ][ 'files' ]
        FileName = os.path.basename( self.resume )
        Mime = magic.Magic(mime=True)
        MimeType = Mime.from_file( self.resume )                                  # tell website what file encoding to use
        Files[ 'resume' ] = ( FileName, open( self.resume, 'rb' ), MimeType )

        # UPLOAD
        UploadResult = self._session.post( ResumePostURL, data=Data, files=Files )
        if UploadResult.status_code != 200:
            return False
        else:
            return True

    def search( self, Quantity=25, **kwargs ):
        '''
        Purpose:	Search for jobs. See the SITE dictionary
                    for all available search parameters.
        Arguments:
            Quantity - int - the number of jobs to yield
            **kwargs - dict/named tuple - search values. see SITE for details on options.
        Returns:
            JobLink - str - job quick apply links for the user.
        '''

        # BUILD SEARCH URL
        SearchURL = SITE[ 'root' ] + SITE[ 'search' ][ 'root' ]
        for SearchField, SearchValue in kwargs.items():
            if SearchField in SITE[ 'search' ]:
                if isinstance( SITE[ 'search' ][ SearchField ], str ):
                    SearchFormat = SITE[ 'search' ][ SearchField ]
                    SearchURL = SearchURL + '&' + \
                        SearchFormat.format( SearchValue )
                elif isinstance( SITE[ 'search' ][ SearchField ], dict ):
                    SearchFormat = SITE[ 'search' ][ SearchField ][ 'root' ]
                    OptionDict = SITE[ 'search' ][ SearchField ][ 'options' ]
                    if SearchValue in OptionDict:
                        EncodedSearchValue = OptionDict[ SearchValue ]
                        SearchURL = SearchURL + '&' + \
                            SearchFormat.format( EncodedSearchValue )
                    else:
                        raise ValueError( 'ERROR : {0} IS NOT AN OPTION FOR {1}'.\
                            format( SearchValue, SearchField ) )

        # SEARCH
        JobSearchPage = self._session.get( SearchURL )
        if JobSearchPage.status_code != 200:
            raise ValueError( 'ERROR : SEARCH FAILED : ' + SearchURL )

        # YIELD QUICK APPLY JOBS
        iReturnedJobs = 0
        NextButtonXPath = "//a[@id='pagination-button-next']/@href"
        NextButton = JobSearchPage.xpath( NextButtonXPath )
        while NextButton and iReturnedJobs < Quantity:				# continue looping until we run out of jobs or meet demand
            QuickApplyJobLinks = JobSearchPage.xpath(  \
                "//button[contains(@class,'one_click_apply')]" )
            for QuickApplyJobLink in QuickApplyJobLinks:
                ApplyLink = QuickApplyJobLink.xpath( "./@data-href" ).extract()[0]
                DetailsLink = QuickApplyJobLink.xpath("../..//" +
                            "a[contains(@class,'job_link')]/@href").extract()[0]
                SR = SearchResult( ApplyLink, DetailsLink )
                if iReturnedJobs >= Quantity: break
                iReturnedJobs += 1									# increment count of returned jobs
                yield SR
            if iReturnedJobs < Quantity:
                NextButton = JobSearchPage.xpath( NextButtonXPath )
                if len( NextButton ) > 0:  							# get the hyperlink to next search result page
                    NextButtonLink = NextButton[0].extract()
                    JobSearchPage = self._session.get( \
                        SITE[ 'root' ] + NextButtonLink )			# goto next result page

    def batchApply( self, JobLinks ):
        '''
        Purpose:	Apply to all jobs in provided list.
        Arguments:
            JobLinks - list of str - list of job apply links
        Returns:
            QuantityAppliedTo - int - count of the number of jobs successfully
                                        applied to out of given list
        '''
        QuantityAppliedTo = 0
        JobCount = 0
        if not isinstance(JobLinks, types.GeneratorType):                   # if not generator, we can calc actual size
            JobCount = len( JobLinks )
        ProgressBar = tqdm( total=JobCount, desc='Applying', unit='Jobs' )
        for JobLink in JobLinks:
            if self.apply( JobLink ):
                QuantityAppliedTo += 1
            if isinstance( JobLinks, types.GeneratorType ):
                ProgressBar.total += 1
            ProgressBar.update( 1 )
        return QuantityAppliedTo

    def apply( self, JobLink ):
        '''
        Purpose:	Apply to the ziprecruiter job.
        Arguments:
            JobLink - str or SearchResult - the link to apply to the job.
                                            if SearchResult, apply link will
                                            be extracted from it.
        Returns:
            True/False - bool - True if applying successful. False otherwise
        '''
        if isinstance( JobLink, SearchResult ):
            JobLink = JobLink.ApplyLink
        ApplyReponse = self._session.get( JobLink )
        if ApplyReponse.status_code == 200:
            return True
        else:
            return False

    def getApplied( self, TopCount=1 ):
        '''
        Purpose:    Get json data on all jobs applied to.
                    Includes: application_status, job_title, company_name, company_address
                    ,job_page_link, application_date, job_status, other_applicants
                    ,resume_on_file
        Arguments:
            TopCount - int - get the first TopCount many applied jobs. jobs list
                                starts with most recent jobs applied to at the top
        '''

        AppliedJobsURL = SITE[ 'root' ] + SITE[ 'applied_jobs' ]
        iPage = 1
        AppliedJobsPage = self._session.get( AppliedJobsURL.format( PageNumber=iPage ) )

        # EXTRACT PAGE COUNT FROM NAV BUTTONS AT BOTTOM
        PageCount = AppliedJobsPage.xpath(
                        "//ul[contains(@class,'paginationNumbers')]" + \
                        "/li[last()]/a/text()" ).extract()[0]
        PageCount = int( PageCount ) if PageCount.isdigit() else 1

        # EXTRACT APPLIED JOBS DATA - USE JOB ID AS KEY
        AppliedJobs = {}
        while iPage <= PageCount and len( AppliedJobs ) < TopCount:
            JobElements = AppliedJobsPage.xpath( "//ul[@class='appliedJobsList']/li" )
            for JobElement in JobElements:
                JobID = JobElement.xpath("./@id").extract()[0].rsplit('-',1)[1]
                JobTitle = JobElement.xpath(".//h4[@class='jobTitle']/text()").extract()[0]
                JobPageLink = SITE['root'] + JobElement.xpath( ".//h4[@class='jobTitle']/../@href" ).extract()[0]
                CompanyName = JobElement.xpath( ".//p[@class='jobCompany']/span/" +
                                                "span[not(@data-name)]/text()" ).extract()[0]
                CompanyAddress = ' '.join( JobElement.xpath(".//span[@data-name='address']" +
                                                            "/node()/text()").extract() )
                ApplicationStatus = ' '.join( x.strip() for x in \
                                              JobElement.xpath(".//div[@class='status_bar']" +
                                                               "//text()").extract() if x.strip() != '' )

                # GET DATA FROM TABLE - USES MORE GENERALIZED SEARCH PATTERN, TO HANDLE FUTURE CHANGES
                ApplicationDate = ''
                ResumeName = ''
                JobStatus = ''
                ApplicantCount = ''
                DetailRows = JobElement.xpath( ".//tr" )
                for DetailRow in DetailRows:
                    DetailValues = DetailRow.xpath( "./td//text()" ).extract()
                    FieldName = None
                    FieldValue = None
                    for DetailValue in DetailValues:
                        if DetailValue.strip() != '':
                            if FieldName == None:
                                FieldName = DetailValue.strip()
                            elif FieldValue == None:
                                FieldValue = DetailValue.strip()
                            else:
                                break
                    if 'app' in FieldName.lower() and 'date' in FieldName.lower():
                        ApplicationDate = FieldValue
                    elif 'resume' in FieldName.lower():
                        ResumeName = FieldValue
                    elif 'status' in FieldName.lower():
                        JobStatus = FieldValue
                    elif 'other' in FieldName.lower() and 'app' in FieldName.lower():
                        ApplicantCount = re.search( r'\d+', FieldValue ).group(0)

                # STORE IN DICT
                AppliedJobs.update( {
                    JobID    :   {
                        'job_title'             :   JobTitle
                        ,'job_page_link'        :   JobPageLink
                        ,'company_name'         :   CompanyName
                        ,'company_address'      :   CompanyAddress
                        ,'application_status'   :   ApplicationStatus
                        ,'application_date'     :   ApplicationDate
                        ,'application_count'    :   ApplicantCount
                        ,'resume_name'          :   ResumeName
                        ,'job_status'           :   JobStatus
                    }
                } )
            iPage += 1
            AppliedJobsPage = self._session.get(AppliedJobsURL.format(PageNumber=iPage))
        return AppliedJobs

    def getJobDetails( self, JobLink ):
        '''
        Purpose:    Get the details of the job at the given job link,
                    including job_title, company_name, job_address,
                    job_link, and job_description.
        Arguments:
            JobLink - str - full url to job on ziprecruiter
        Returns:
            JobDict - dict - dictionary of job details
        '''
        JobPage = self._session.get( JobLink )

        try:
            JobTitle = JobPage.xpath( "//h1[@class='job_title']/text()" ).\
                                extract()[0].strip()
            CompanyName = ' '.join( x.strip() for x in \
                                    JobPage.xpath( "//a[@class='job_details_link']" +
                                    "//text()" ).extract() if x.strip() != '' )
            JobAddress = ''.join( JobPage.xpath( "//span[@itemprop='address']" +
                                                 "//text()" ).extract() )
            JobDescription = ''.join( x.strip() for x in \
                                      JobPage.xpath( "//div[@class='jobDescriptionSection']" +
                                                     "//text()" ).extract() )
            JobDict = {
                'job_link'          :   JobLink
                ,'job_title'        :   JobTitle
                ,'job_address'      :   JobAddress
                ,'company_name'     :   CompanyName
                ,'job_description'  :   JobDescription
            }
        except:
            JobDict = {}

        return JobDict

if __name__ == '__main__':
    fire.Fire( ZipRecruiter )
