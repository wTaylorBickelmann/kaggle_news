import schedule
import time
import threading
from flask import Flask, render_template
from database import init_db
from scraper import NewsScraper, NEWS_SOURCES

app = Flask(__name__)

def run_scraper():
    scraper = NewsScraper(NEWS_SOURCES)
    scraper.scrape_all()
    print("News scraping completed.")

def start_scheduler():
    init_db()
    schedule.every(6).hours.do(run_scraper)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

def main():
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.start()
    
    # Run Flask app
    app.run(debug=True)

if __name__ == '__main__':
    main()
