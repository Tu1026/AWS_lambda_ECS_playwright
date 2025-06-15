FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

COPY . /app

RUN pip install playwright python-dotenv discord.py
RUN playwright install chromium

# If you have requirements.txt, uncomment the next line:
# RUN pip install -r requirements.txt

CMD ["python", "playwright_test.py", "--loop"]