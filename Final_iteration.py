import cv2
import smtplib
import os
import imghdr
from email.message import EmailMessage  # included all necessary libraries
import imaplib
import email
from pygame import mixer  #for play the siren
import time
from twilio.rest import Client  #calling

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 640)  # set all frame size
ret, frame1 = cap.read()
ret, frame2 = cap.read()
image_no = 0
flag_for_taking_ss = 0
counter = 0
message = "no_message"
flag2 = False
client = Client("", "")


def sendmail(img_no):
    email_id = os.environ.get("EMAIL_ADDR")
    email_pass = os.environ.get("MAIL_PASS")

    msg = EmailMessage()
    msg['Subject'] = "Alert!!!!"
    msg['From'] = '' #Sender email address
    msg['To'] = ''  #Receiver email address
    msg.set_content("Replay suspect or not !!")
    with open(f'images/suspect{image_no}.jpg', 'rb') as m:
        file_data = m.read()
        file_type = imghdr.what(m.name)
        file_name = m.name

    msg.add_attachment(file_data, maintype='image', subtype=file_type, filename=file_name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('', '')  # email and key
        smtp.send_message(msg)


def get_inbox():
    host = "imap.gmail.com"
    mymail = ""     #sender email
    mypass = ""     #sender password
    mail = imaplib.IMAP4_SSL(host)
    mail.login(mymail, mypass)
    mail.select('inbox')
    _, searched_data = mail.search(None, 'UNSEEN')          #receieve mail function

    for searched in searched_data[0].split():
        data_to_return = {}
        _, mail_data = mail.fetch(searched, "(RFC822)")
        _, data = mail_data[0]
        message = email.message_from_bytes(data)

        for msg_part in message.walk():
            if msg_part.get_content_type() == "text/plain":
                data_to_return["Body"] = msg_part.get_payload(decode=False)

        return data_to_return["Body"]

    return "no_message"


while cap.isOpened():
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)

        if cv2.contourArea(contour) < 22000:
            continue
        else:
            counter = (counter + 0.1)
            cv2.putText(frame1, "Status: {}".format('Movement'), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            if flag_for_taking_ss == 0 and counter > 20:
                filename = 'images/suspect{}.jpg'.format(image_no)
                cv2.imwrite(filename, frame1)
                sendmail(image_no)
                call = client.calls.create(
                     twiml="<Response><Say>Alert!!!!!!  Alert!!!!!  Alert!!!! suspect detected in strong room please check out mail</Say></Response>",
                     from_="", to='')   # Phone numbers
                image_no += 1
                flag = 1
                while True:
                    message = str(get_inbox())
                    if message != "no_message":
                        break
                i = len(message)
                if i == 5:
                    print("Permission granted by Administrator")
                elif i == 4:
                    print("Warning!!!!! Alert!!!!!!")
                    mixer.init()
                    mixer.music.load("alarm.mp3")
                    mixer.music.play()
                    while mixer.music.get_busy():  # wait for music to finish playing
                        time.sleep(1)
                flag_for_taking_ss = 1
            if counter > 30:
                counter = 0
                flag_for_taking_ss = 0
            print(counter)

    resized = cv2.resize(frame1, (800, 500))
    cv2.imshow("Video", resized)
    frame1 = frame2
    ret, frame2 = cap.read()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
cap.release()
