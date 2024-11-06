import requests
import json
from bs4 import BeautifulSoup
import re
from requests import Session

class PageNotFound(Exception):
    pass

# Function to get the first paragraph of a wiki page
def get_first_paragraph(wikipedia_url: str, session: Session):
    print(wikipedia_url) # keep this for the rest of the notebook
    req = session.get(wikipedia_url)
    soup = BeautifulSoup(req.text, "html")

    # Store all the p tags in a list. Strip and check that its not empty 
    # First paragraph - Has digits (year of birth) and is more than 20 words
    paragraphs = [para.text.strip() for para in soup.find_all("p") if len(para.text.strip())>0]
    for para in paragraphs:
        if((re.match('.*[1-9].*',para)) and (len(para.split()) >= 15)):
            first_paragraph = re.sub("\\[.{,2}\\]","",para)
            break
    return first_paragraph

# Function to return leaders info 
def get_leaders():
    countries = requests.get(f"{root_url}/{countries_url}", cookies=cookies).json()

    # Go through all the countries and extract the name of the leaders in a dict
    leaders_per_country = {country:requests.get(f"{root_url}/{leaders_url}", cookies=cookies, params={'country':country}).json() 
                           for country in countries}
    
    # Starting session to go over all the wiki links of the leaders
    with Session() as session:
        for country,leaders in leaders_per_country.items():
            for each in leaders: 
                each["first_wiki_para"] = get_first_paragraph(each["wikipedia_url"], session)
    return leaders_per_country

# Function to write the JSON into a new file
def save(leaders_per_country: dict, filename: str):
    with open(filename,"w") as file:
        json.dump(leaders_per_country, file, indent=4, separators=(". ", " = "))
    print("Saved the data in",filename)

# Initialise URL paths
root_url = "https://country-leaders.onrender.com"
status_url = "/status"
cookie_url = "/cookie"
countries_url = "/countries"
leaders_url = "/leaders"

# Query the root URL and check the status
req = requests.get(f"{root_url}/{status_url}")
if req.status_code != 200:
    raise PageNotFound(req.reason)

# Get cookies 
cookies = requests.get(root_url+"/"+cookie_url).cookies

# Get the information of the leaders and save it in a file
leaders_per_country = get_leaders()
save(leaders_per_country, "leaders.json")