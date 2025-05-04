from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///news_articles.db')
Session = sessionmaker(bind=engine)

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text)
    source = Column(String)
    published_date = Column(DateTime, default=datetime.utcnow)
    url = Column(String, unique=True)

def init_db():
    Base.metadata.create_all(engine)

def save_article(article_data):
    session = Session()
    try:
        article = Article(**article_data)
        session.add(article)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving article: {e}")
    finally:
        session.close()
