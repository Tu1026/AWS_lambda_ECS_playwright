FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

COPY . /app

RUN pip install playwright
RUN playwright install chromium

# If you have requirements.txt, uncomment the next line:
# RUN pip install -r requirements.txt

CMD ["python", "playwright_test.py"]