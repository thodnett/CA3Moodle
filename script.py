import os
import requests
from requests import get, post
import json
from bs4 import BeautifulSoup
from dateutil import parser
import datetime

KEY = "bc7ad59923ad95f17dd955868790ccb5"

URL = "http://f0ae7213ef73.eu.ngrok.io/"

ENDPOINT="/webservice/rest/server.php"

def rest_api_parameters(in_args, prefix='', out_dict=None):
    """Transform dictionary/array structure to a flat dictionary, with key names
    defining the structure.
    Example usage:
    >>> rest_api_parameters({'courses':[{'id':1,'name': 'course1'}]})
    {'courses[0][id]':1,
     'courses[0][name]':'course1'}
    """
    if out_dict==None:
        out_dict = {}
    if not type(in_args) in (list,dict):
        out_dict[prefix] = in_args
        return out_dict
    if prefix == '':
        prefix = prefix + '{0}'
    else:
        prefix = prefix + '[{0}]'
    if type(in_args)==list:
        for idx, item in enumerate(in_args):
            rest_api_parameters(item, prefix.format(idx), out_dict)
    elif type(in_args)==dict:
        for key, item in in_args.items():
            rest_api_parameters(item, prefix.format(key), out_dict)
    return out_dict

def call(fname, **kwargs):
    """Calls moodle API function with function name fname and keyword arguments.
    Example:
    >>> call_mdl_function('core_course_update_courses',
                           courses = [{'id': 1, 'fullname': 'My favorite course'}])
    """
    parameters = rest_api_parameters(kwargs)
    parameters.update({"wstoken": KEY, 'moodlewsrestformat': 'json', "wsfunction": fname})
    #print(parameters)
    response = post(URL+ENDPOINT, data=parameters).json()
    if type(response) == dict and response.get('exception'):
        raise SystemError("Error calling Moodle API\n", response)
    return response

class LocalGetSections(object):
    """Get settings of sections. Requires courseid. Optional you can specify sections via number or id."""
    def __init__(self, cid, secnums = [], secids = []):
        self.getsections = call('local_wsmanagesections_get_sections', courseid = cid, sectionnumbers = secnums, sectionids = secids)


class LocalUpdateSections(object):
    """Updates sectionnames. Requires: courseid and an array with sectionnumbers and sectionnames"""
    def __init__(self, cid, sectionsdata):
        self.updatesections = call(
            'local_wsmanagesections_update_sections', courseid=cid, sections=sectionsdata)

def search_files_and_title(sec_num):
#Searches the files in directory and grabs the title from the index page.
    directory='/workspace/CA3Moodle/'
    for filename in os.listdir(directory):
        if filename.endswith("wk{0}".format(sec_num)):
            path=filename
            for filename in os.listdir(directory+path):
                if filename.endswith(".html"):
                    html_files=filename
                    soup=BeautifulSoup(open(directory+path+'/'+html_files), 'html.parser')
                    soup.prettify()
                    title=soup.find('title')
                    return title
        else:
            return

courseid = "9"
sec = LocalGetSections(courseid)
def get_summary(sec_num):
#Gets the summary from moodle.
    summary=(json.dumps(sec.getsections[sec_num]['summary'], indent=4, sort_keys=True))

def compare_title_summary(sec_num):
#Compares the title from the index with the summary on moodle. 
    summary=get_summary(sec_num)
    title=search_files_and_title(sec_num)
    if summary == None:
        return sec_num
    elif summary == title:
        pass

def search_files(sec_num):
#Searches the files in directory.
    directory='/workspace/CA3Moodle/'
    for filename in os.listdir(directory):
        if filename.endswith("wk{0}".format(sec_num)):
            return sec_num

def scrape_video_date():
#Scrapes the google drive page and retrieves the date, the date is converted into week number. 
    url="https://drive.google.com/drive/folders/1pFHUrmpLv9gEJsvJYKxMdISuQuQsd_qX"
    page=requests.get(url)
    soup=BeautifulSoup(page.content, 'html.parser')
    videos = soup.find_all('div',class_ = 'Q5txwe')
    for video in videos:
        video_date=video.text
        video_id = video.parent.parent.parent.parent.attrs['data-id']
        date=video_date
        new=date[ 0 : 10 ]
        month = parser.parse(new)
        mon=month.strftime("%V")
        yield mon, video_id

def compare_sdate_and_vdate(sec_num):
#Compares the wk of the video with the week of the moodle section.
    month = parser.parse(list(sec.getsections)[sec_num]['name'].split('-')[0])
    mon=month.strftime("%V")
    mon = int(mon) + 1
    smon=str(mon)
    for i in scrape_video_date():
        if smon in i:
            return (i[1])

def create_payload_write_to_moodle(sec_num):
#Assembles the payload for the write to moodle function.
    video_id=compare_sdate_and_vdate(sec_num)
    id=video_id
    #  Assemble the payload
    data = [{'type': 'num', 'section': 0, 'summary': '', 'summaryformat': 1, 'visible': 1 , 'highlight': 0, 'sectionformatoptions': [{'name': 'level', 'value': '1'}]}]
    # Assemble the correct summary
    summary = '<a href="https://thodnett.github.io/CA3Moodle/wk{0}/">Week{0}</a><br>'.format(sec_num), '<a href="https://thodnett.github.io/CA3Moodle/wk{0}.pdf"</a></br>'.format(sec_num),'<a href="https://drive.google.com/file/d/{0}"</a><br>'.format(id)
    # Assign the correct summary
    print(type(data))
    # Set the correct section number
    #data[0]['section'] = sec_num
    #for summ in summary:
        #data[0]['summary'] = sum
       # sec_write = LocalUpdateSections(courseid, data)
    
def main():
    for i in range(1,27):
        av_files=search_files(i)
        if av_files==None:
            pass
        else:
            files=compare_title_summary(av_files)
            create_payload_write_to_moodle(files)
            
if __name__ == "__main__":
    main()
