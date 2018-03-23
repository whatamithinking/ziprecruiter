# ziprecruiter

An unofficial ziprecruiter api for applying to jobs,login,search, and upload new resumes.

<p align="left">
<img src="https://github.com/ConnorSMaynes/ziprecruiter/blob/master/logo.png" alt="ZipRecruiter Bot" >
</p>

A simple unofficial api for ziprecruiter.
Functionality:
  > application to jobs
  > uploading of resumes
  > searching for jobs

<p align="left">
<img src="https://github.com/ConnorSMaynes/ziprecruiter/blob/master/batteries.png", alt="Batteries Included - Selenium - Chrome Webdriver" width=30, height=30>
      Selenium Batteries Included - Chrome Webdriver
</p>

## Methods

- `login()` : Login to ZipRecruiter with the provided credentials. ZipRecruiter is protected by No Captcha ReCaptcha, so if this pops up and login cannot proceed the selenium browser will restart and display itself so you can solve the captcha. Selenium is ONLY used for login, because of the captcha problem, everything else is nice and fast through requests.
- `search` : search for jobs. returns a list of quick apply job links. generator. The following filters are supported:
  - keywords
  - posted x days ago
  - salary
  - type ( full-time, internship, temporary )
- `uploadResume` : Upload the provided resume to ziprecruiter to replace the existing resume in the account.
- `apply` : apply to the job at the given url returned from `search`
- `batchApply` : apply to a bunch of jobs at once. progress bar.

## Installation

```bash
pip install git+git://github.com/ConnorSMaynes/ziprecruiter
```

## Usage

```python
z = ZipRecruiter()
z.login( USERNAME, PASSWORD )
z.uploadResume( FilePath=RESUME_FILE_PATH )
Jobs = list( z.search( Quantity=10, keywords='math teacher' ) )
z.batchApply( Jobs )
```

## Similar Projects

This project was inspired by others:
- [getJob](https://github.com/jonathanhwinter/getJob)
- [ZipRecruiterHack](https://github.com/Original-heapsters/ZipRecruiterHack)

## License

Copyright © 2018, [ConnorSMaynes](https://github.com/ConnorSMaynes). Released under the [MIT](https://github.com/ConnorSMaynes/ziprecruiter/blob/master/LICENSE).

