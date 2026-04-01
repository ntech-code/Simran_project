import feedparser
from fastapi import APIRouter

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/finance-news")
async def get_finance_news():
    """
    Scrapes the live Economic Times RSS feed for authentic, real-time Indian Finance and Tax news.
    """
    tax_feed = "https://economictimes.indiatimes.com/wealth/tax/rssfeeds/83722914.cms"
    market_feed = "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms"
    
    # Parse feeds
    t_data = feedparser.parse(tax_feed)
    m_data = feedparser.parse(market_feed)
    
    articles = []
    
    for entry in t_data.entries[:10]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "summary": entry.get('summary', ''),
            "category": "Tax & Wealth",
            "source": "The Economic Times India"
        })
        
    for entry in m_data.entries[:10]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "summary": entry.get('summary', ''),
            "category": "Stock Market",
            "source": "The Economic Times India"
        })
        
    # Sort chronologically or just alternate them (simulated simple blend)
    
    return {"status": "success", "articles": articles}
