
from common_resources import _getSession, RequestiumSession
from time import sleep
import fire, types, os, magic
from tqdm import tqdm

SITE = {
    'root'		    :	'https://www.ziprecruiter.com'
    ,'apply'	    :	'/apply/contact-info/{Job_ID}' + \
                        '?_token={Token};oneClickApply=true&amp;purpose=one-click-apply-' + \
                        'click&amp;source=ziprecruiter-jobs-site#'
    ,'login'	    :	'/login?realm=candidates'
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
        self.solveCaptcha = solveCaptcha
        self.headless = Headless
        if oSession != None:
            if not isinstance( oSession, RequestiumSession ):
                raise ValueError( 'ERROR : NOT A REQUESTIUMSESSION INSTANCE' )
            self._session = oSession
        else:
            self._session = _getSession( Headless=self.headless )

    def login( self, Username, Password ):
        '''
        Purpose:	Login to the site on behalf of the user.
        Arguments:
            Username - str - the email of the user
            Password - str - the password of this user for this job site
        Returns:
            True/False - bool - True if successful. False if login creds did not work.
        '''

        # CHECK FOR USER CREDS
        if all( x == None for x in ( Username, Password ) ):
            raise ValueError( 'ERROR : USERNAME AND PASSWORD REQUIRED' )
        self.username = Username
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
                if self.headless:
                    self._session.driver.quit()
                    self._session = None
                    self._session = _getSession( Headless=self.headless )
                    self.login( self.username, self.password )

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

        return True

    def uploadResume( self, FilePath ):
        '''
        Purpose:    Upload a resume to ZipRecruiter.
        Arguments:
            FilePath - str - path to the resume you want to upload
        Returns:
            True/False - bool - True if upload successful. False otherwise.
        '''

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
        FileName = os.path.basename( FilePath )
        Mime = magic.Magic(mime=True)
        MimeType = Mime.from_file( FilePath )                                  # tell website what file encoding to use
        Files[ 'resume' ] = ( FileName, open( FilePath, 'rb' ), MimeType )

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
            **kwargs - dict/named tuple - search values
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
                "//button[contains(@class,'one_click_apply')]/@data-href" )
            for QuickApplyJobLink in QuickApplyJobLinks:
                JobLink = QuickApplyJobLink.extract()
                if iReturnedJobs >= Quantity: break
                iReturnedJobs += 1									# increment count of returned jobs
                yield JobLink
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
            JobLink - str - the link to apply to the job
        Returns:
            True/False - bool - True if applying successful. False otherwise
        '''
        ApplyReponse = self._session.get( JobLink )
        if ApplyReponse.status_code == 200:
            return True
        else:
            return False

if __name__ == '__main__':
    fire.Fire( ZipRecruiter )




