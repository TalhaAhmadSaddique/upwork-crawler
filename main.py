import os, time, feedparser, requests, json, re
from datetime import datetime
from selenium import webdriver
from openai import OpenAI
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
ai_rss_feed = os.getenv("AI_RSS")
web_rss_feed = os.getenv("WEB_RSS")
mobile_rss_feed = os.getenv("MOBILE_RSS")
design_rss_feed = os.getenv("DESIGN_RSS")
devops_rss_feed = os.getenv("DEVOPS_RSS")
api_key = os.getenv("OPENAI_KEY")
google_api = os.getenv("SHEET_API")

kb = """
Content Extractor is precisely configured for analyzing Upwork job page content. 
You will be provided by these three things:
1- "Job Description" which is basically the description of the job that's the client wanted to be done. It could also contain links to other websites. The client could have mentioned his own name or the company's name he is working for in this section. 
2- "Links" which will be the web links to the attachments found with the job.
3- "Feedbacks" which will be the feedback given by the previous freelancers, the client has worked with. There the freelancers could have mentioned the client's name or client's company name.
Your role is to find these three things:
1- Client's Name (client_name) - If it's mentioned in the "Job Description" or "Feedbacks".
2- Client's Company Name (company_name) - If it's mentioned in the "Job Description" or "Feedbacks".
3- External Links (external_links) - All the links found in "Job Description" or "Feedbacks" or "Links"
The output data should be in JSON format with specific keys: 'external_links' (a list or null), 'client_name' (string or null), and 'company_name' (string or null). 
Ensure strict adherence to these rules and conditions in your extraction process. 
In cases of unclear content, preprocess it for clarity, and if it remains unclear, return null values for each of three but in the JSON format. 
Your responses should be formal, precise, and focused on delivering clear and error-free data extraction according to these specific guidelines.
"""

def entity_extraction(text: str, max_attempts=3):
    for attempt in range(max_attempts):
        client = OpenAI(api_key = api_key)
        completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": kb},
            {"role": "user", "content": text}
        ],
        max_tokens=2000
        )
        rs = completion.choices[0].message.content
        try:
            json_result = json.loads(rs)
            return rs
        except json.JSONDecodeError:
            print(f"Attempt {attempt + 1} failed. Retrying...")
    raise Exception("Failed to get a valid JSON response after multiple attempts")

def current_datetime():
    current_datetime = datetime.now()
    formatted_current_datetime = current_datetime.strftime('%a, %d %b %Y %H:%M:%S +0000')
    return formatted_current_datetime    

driver = webdriver.Chrome()
driver.maximize_window()

driver.get("https://upwork.com/")
driver.implicitly_wait(5)

login_link = driver.find_element(By.LINK_TEXT, 'Log in')
login_link.click()

wait1 = WebDriverWait(driver, 5).until(
    EC.presence_of_element_located((By.ID, "login_username"))
)

username = driver.find_element(By.ID, "login_username")
username.send_keys(email)
time.sleep(5)
continue_button = driver.find_element(By.ID, 'login_password_continue')
continue_button.click()
wait2 = WebDriverWait(driver, 5).until(
    EC.presence_of_element_located((By.ID, "login_password"))
)
time.sleep(5)
pwd = driver.find_element(By.ID, "login_password")

pwd.send_keys(password)
login_button = driver.find_element(By.ID, 'login_control_continue')

login_button.click()

print("login sucessfully")

with open('logs.txt', 'a') as logs_file:
    logs_file.write(f"""
Login Successfully at {current_datetime()}\n
    """)

time.sleep(15)

used_urls = set()

crash = False

total_jobs = ["AI & Machine Learning", "Web Development", "Mobile Development", "Web & Mobile Design", "DevOps & Solution Architect"]

while True:
    for single_job in total_jobs:
        print(single_job)
        with open('logs.txt', 'a') as logs_file:
            logs_file.write(f"""
*********************************
Jobs Extraction: {single_job}\n
        """)
        job_type = single_job
        if single_job == "AI & Machine Learning":
            rss_feed = ai_rss_feed
        elif single_job == "Web Development":
            rss_feed = web_rss_feed
        elif single_job == "Mobile Development":
            rss_feed = mobile_rss_feed
        elif single_job == "Web & Mobile Design":
            rss_feed = design_rss_feed
        elif single_job == "DevOps & Solution Architect":
            rss_feed = devops_rss_feed
        feed = feedparser.parse(rss_feed)
        with open('rss_feed_data.txt', 'a') as f:
            f.write(f"""
*********************************
Jobs Extraction: {single_job}\n
            """)
        if feed.bozo:
            print("Error parsing the feed.")
            print(feed)
        total_links = []
        for entry in feed.entries:
            total_links.append(entry.link)
        length = len(total_links)
        with open('rss_feed_data.txt', 'a') as f:
            f.write(f"""
*********************************
Total Links: {length}\n
Jobs Links: \n
            """)
        for each in total_links:
            with open('rss_feed_data.txt', 'a') as f:
                f.write(f"""
*********************************
{each}\n
                """)
        feed = feedparser.parse(rss_feed)
        if feed.bozo:
            print("Error parsing the feed.")
            print(feed)
        for entry in feed.entries:
            with open('used_urls_data.txt', 'a') as f:
                f.write('')
            with open('used_urls_data.txt', 'r') as r:
                links_set = set(line.strip() for line in r)
            if entry.link in links_set:
                print("Already Used")
                with open('skip_urls.txt', 'a') as s:
                    s.write(f"{entry.link}\n")
                continue
            print("========================================================================================================================")
            print(entry.link)
            with open('used_urls_data.txt', 'a') as w:
                w.write(f"{entry.link}\n")
            with open('logs.txt', 'a') as logs_file:
                logs_file.write(f"""
*********************************
Link of job: {entry.link}\n
                """)
            try:
                """Start the Content Extraction"""
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])
                driver.get(entry.link)

                with open('logs.txt', 'a') as logs_file:
                    logs_file.write(f"""
Link open successfully at: {current_datetime()}\n
                    """)

                driver.implicitly_wait(10)
                data = ''
                """Extract job description"""
                job_description = driver.find_elements(By.CLASS_NAME, 'text-body-sm')
                i = 0
                for description in job_description:
                    if i == 1:
                        # print(description.text)
                        data = data + 'Job Description:' + '\n' + description.text + '\n'
                        with open('logs.txt', 'a') as logs_file:
                            logs_file.write(f"""
Job Description: {description.text}\n
External Link: 
                            """)
                        break
                    i = i + 1

                # time.sleep(10)
                """Extract attachments if any"""
                attachments = driver.find_elements(By.XPATH, '/html/body/div[4]/div/div/div/main/div[2]/div[4]/div/div/div[1]/div/section[4]/ul')
                if attachments:
                    data = data + 'Links:' + '\n'
                    for attachments_ul in attachments:
                        link_elements = attachments_ul.find_elements(By.TAG_NAME, 'a')
                        for link_element in link_elements:
                            href_attribute = link_element.get_attribute('href')
                            data = data + href_attribute + '\n'
                            with open('logs.txt', 'a') as logs_file:
                                logs_file.write(f"""
{href_attribute}\n
                                """)

                # time.sleep(10)
                """Click on view more button"""
                try:
                    while True:
                        view_more_link = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div/div/main/div[2]/div[4]/div/div/div[2]/div[1]/section[2]/footer/span/a'))
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", view_more_link)
                        view_more_link.click()
                        view_more_link = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div/div/main/div[2]/div[4]/div/div/div[2]/div[1]/section[2]/footer/span/a'))
                        )
                except Exception as e:
                    print(f"no more view more!!")

                # time.sleep(10)
                """Click on more button in feedbacks"""
                try:
                    feedbacks = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div/main/div[2]/div[4]/div/div/div[2]/div[1]/section[2]')
                    divs_xpath = "./div"
                    div_elements = feedbacks.find_elements(By.XPATH, divs_xpath)
                    div_count = len(div_elements)
                    print(div_count)
                    for j in range(div_count):
                        wait = WebDriverWait(driver, 10)
                        try:
                            css_selector = f"#main > div.container > div:nth-child(4) > div > div > div.extra-jobs-cards.px-md-6 > div:nth-child(1) > section.items.air3-card-section > div:nth-child({j+1}) > div.main > div.text-body-sm.mt-2x.mb-2x > span > span.air3-truncation > span:nth-child(2) > button"
                            buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
                            for button in buttons:
                                print(button.text)
                                button.click()
                        except Exception as e:
                            print('feedback opening error!')
                            pass
                except Exception as e:
                    print(e)
                    print('there is no job history!')

                print("More buttons are clicked successfully!")

                """Extract the user's feedback"""
                try:
                    feedbacks = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div/main/div[2]/div[4]/div/div/div[2]/div[1]/section[2]')
                    divs_xpath = "./div"
                    div_elements = feedbacks.find_elements(By.XPATH, divs_xpath)
                    div_count = len(div_elements)
                    print(div_count)
                    with open('logs.txt', 'a') as logs_file:
                        logs_file.write(f"""
Total Feedbacks: {div_count}\n
Feedbacks:
                        """)
                    data = data + 'Feedbacks:' + '\n'
                    for x in range(div_count):
                        try:
                            x_path = f"/html/body/div[4]/div/div/div/main/div[2]/div[4]/div/div/div[2]/div[1]/section[2]/div[{x+1}]/div[1]/div[1]/span/span[2]/span[1]/span"
                            feedback_text = driver.find_element(By.XPATH, x_path)
                            data = data + str(feedback_text.text) + '\n'
                            with open('logs.txt', 'a') as logs_file:
                                logs_file.write(f"""
{feedback_text.text}\n
                                """)
                        except Exception as e:
                            print("feedback extraction error!")
                            pass
                except Exception as e:
                    print(e)
                    print('there is no job history!')
                
                print(data)
                
                extracted_data = entity_extraction(data)
                print(extracted_data)
                with open('logs.txt', 'a') as logs_file:
                    logs_file.write(f"""
Extracted data from OpenAI: {extracted_data}\n
                    """)
                country_match = re.search(r'<b>Country</b>: (.+?)\n', entry['summary'])
                if country_match:
                    country = country_match.group(1)
                    print("Country:", country)
                else:
                    print("Country not found in the summary.")
                pre_result = json.loads(extracted_data)
                result = {}
                if pre_result["external_links"] is None:
                    result["external_links"] = pre_result["external_links"]
                else :
                    result["external_links"] = "$".join(pre_result["external_links"])
                
                result["client_name"] = pre_result["client_name"]
                result["company_name"] = pre_result["company_name"]
                result["job_link"] = entry.link
                result["job_title"] = entry.title
                result["posted_time"] = entry.published
                result["country"] = country
                result["scrapped_time"] = current_datetime()
                result['job_type'] = job_type
                print(result)
                with open('logs.txt', 'a') as logs_file:
                    logs_file.write(f"""
Final data to be stored in sheet: {result}\n
                    """)
                time.sleep(5)
                """Storing data into the google sheet"""
                payload = json.dumps(result)
                headers = {
                'Content-Type': 'application/json'
                }
                response = requests.request("POST", google_api, headers=headers, data=payload)
                print(response.text)
                with open('logs.txt', 'a') as logs_file:
                    logs_file.write(f"""
Sheet updated successfully!!\n
***********************************************************************************************************************
                    """)
                print("========================================================================================================================")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(60)
            except Exception as e:
                crash == True
                with open('logs.txt', 'a') as logs_file:
                    logs_file.write(f"""
Error at {current_datetime()}!!\n
Exception is: {e}
***********************************************************************************************************************
                    """)
                print("Erorrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
                break
        if crash == True:
            break
    if crash == True:
        with open('logs.txt', 'a') as logs_file:
            logs_file.write(f"""
Crwaler crashed at {current_datetime()} due to some error!!\n
***********************************************************************************************************************
            """)
        break
    time.sleep(120)


