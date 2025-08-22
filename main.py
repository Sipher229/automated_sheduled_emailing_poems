from selenium import webdriver
from selenium.webdriver.common.by import By
from random import choice
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from dotenv import load_dotenv
import smtplib
import ssl
from Poem import Poem
from selenium.webdriver.chrome.options import Options


chrome_options = Options()
chrome_options.add_argument("--headless")  # Required on GitHub Actions
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

load_dotenv()

RECIPIENT = os.getenv("RECIPIENT")


def get_poem_links(content_url: str) -> list:
    print("getting poem_links...")

    try:
        driver = webdriver.Chrome(chrome_options)
        driver.get(content_url)
        poem_link_elements = driver.find_elements(By.CLASS_NAME, "phLink")
        poem_links = [link.find_element(By.TAG_NAME, "a").get_property("href") for link in poem_link_elements]
        return poem_links
    except Exception as e:
        print(e)
        return []


def get_sent_poems_number() -> int:
    with open("sent_poems.txt", "r") as sent_poems:
        sent_poem_links = sent_poems.readlines()
        poems_number = len(sent_poem_links)
        return poems_number


def get_poem(poem_links: list, poems_number: int) -> Poem:
    driver = webdriver.Chrome(chrome_options)
    if len(poem_links) != 0:

        try:
            poem_to_send_link = poem_links[poems_number]

            driver.get(poem_to_send_link)
            poem_title = driver.find_element(By.CLASS_NAME, "phPageDetailsTitle").find_element(By.TAG_NAME, "h2").text
            poem_content = driver.find_element(By.CLASS_NAME, "phContent").text

            return Poem(poem_title, poem_content)
        except Exception as e:
            print(e)
            poem_links.remove(poem_links[poems_number])
            return get_poem(poem_links, poems_number)


def get_email_subject():
    print("getting email subject")
    driver = webdriver.Chrome(chrome_options)
    driver.get("https://www.wishesmsg.com/sweet-things-to-say-to-girlfriend/")
    subject_lines = driver.find_elements(By.CLASS_NAME, "m")

    subject_lines = [subj.text for subj in subject_lines]
    print("subject list: " + str(subject_lines))
    return choice(subject_lines)


def add_poem_to_file(file_name: str, poem_link: str) -> bool:
    try:
        with open(f"./{file_name}", "a") as sent_poems:
            sent_poems.write(poem_link + "\n")
        return True
    except Exception as e:
        print(e)
        return False


def verify_poem_sent(file_name: str, poem_link: str):
    try:
        with open(f"./{file_name}", r) as sent_poems:
            poems = sent_poems.readlines()
            if poem_link in poems:
                return True
            else:
                return False
    except Exception:
        print("error verifying poem link to file" + e)
        return False


def file_exists(file_name: str) -> bool:
    try:
        open(f"./{file_name}", "r")
        return True
    except FileNotFoundError:
        return False


def send_poem() -> None:
    poem_links = get_poem_links("https://www.poemhunter.com/poems/love/")
    poems_number = get_sent_poems_number()
    poem = get_poem(poem_links, poems_number)
    email_sent = send_email(
        RECIPIENT,
        get_email_subject(),
        poem.content,
        poem.title
    )
    if email_sent:
        add_poem_to_file("sent_poems.txt", poem_link=poem_links[poems_number])
        print("Email sent successfully")
    else:
        print("failed to send email")


def send_email(recipient: str, subject: str, content: str, poem_title: str) -> bool:
    msg = MIMEMultipart("related")

    smtp_port = os.environ["SMTP_PORT"]
    host = os.environ["HOST"]
    username = os.environ["USER"]
    password = os.environ["PASS"]
    context = ssl.create_default_context()

    try:
        with open("email_template_poems.txt", "r", encoding="utf-8") as html_email_template:
            html_email_message = html_email_template.read()
            html_email_message = html_email_message.replace("[poem content]", content)
            html_email_message = html_email_message.replace("[poem title]", poem_title)

        msg.attach(MIMEText(html_email_message, "html"))
        msg["From"] = username
        msg["To"] = recipient
        msg["Subject"] = subject
        print("Connecting to smtp server...")
        with smtplib.SMTP(host, port=int(smtp_port)) as server:
            server.starttls(context=context)
            server.login(user=username, password=password)
            server.sendmail(username, recipient, msg.as_string())

        print(f"email sent to {recipient}")
        return True
    except Exception as e:
        print("failed to send email" + str(e))
        return False


send_poem()
