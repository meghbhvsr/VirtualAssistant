How it works:
 - Create an account, if your already have an accoutn than log in
 - The virtual chatbot is AI powered (Using gpt3.5) so you can ask it anything you want.
 - You can also ask it to set reminders for you, you can ask it to tell you your reminders, delete reminders, etc.
 - There is also a calendar page, that displays a calendar with all of the reminders set for the user on their account
 - You can also ask it to send an email, you need to just give it the recipents email, the subject, and it will then open up the mail app, write the email for you, along with an AI generated body message based on the subject given. (Windows)

 How to simulate on your side:
  - Clone the repository ( git clone VirtualAssistant)
  - cd OpenAIProject, cd pythonlogin
  - pip install -r requirements.txt' 
  - Create a .env file in the root directory a 
    API_KEY=your_openai_api_key
    SESSION_TYPE=filesystem
    SECRET_KEY=your_secret_key
    MYSQL_HOST=localhost
    MYSQL_USER=root
    MYSQL_PASSWORD=your_mysql_password
    MYSQL_DB=pythonlogin
  - Run using python app.py

Steup Database
  - run the scripts in the SQLScripts folder, starting with accounts.sql and then reminders.sql