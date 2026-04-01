"""
Smart Spend Analyzer v2 — Massive Pre-Training Dataset Generator
80,000+ realistic Indian bank transaction descriptions.
Patterns match EXACT real-world HDFC/SBI/ICICI/Kotak bank statement formats.
"""
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

np.random.seed(42)

# ============================================================
# MASSIVE MERCHANT DATABASE — Real Indian Bank Statement Formats
# Each entry maps to exactly what appears in a real bank PDF
# ============================================================
MERCHANTS = {
    "Food": {
        "Swiggy": [
            "UPI: Swiggy", "UPI: SWIGGY", "UPI:Swiggy", "Swiggy", "SWIGGY",
            "UPI: Swiggy Instamart", "SWIGGY INSTAMART", "UPI-BUNDL TECHNOLOGIES",
            "BUNDL TECHNOLOGIES PVT", "UPI/SWIGGY", "POS: Swiggy",
            "UPI: Swiggy Order", "Swiggy Food Order", "Swiggy Delivery",
        ],
        "Zomato": [
            "UPI: Zomato", "UPI: Zomato Limited", "UPI:Zomato", "Zomato", "ZOMATO",
            "UPI-ZOMATO LTD", "ZOMATO LIMITED", "UPI: Zomato Order",
            "POS: Zomato", "Zomato Food", "UPI/ZOMATO", "Zomato Delivery",
        ],
        "Dominos": [
            "UPI: Dominos", "Dominos", "DOMINOS", "DOMINOS PIZZA", "Dominos Pizza",
            "JUBILANT FOODWORKS", "UPI: Dominos Pizza", "POS: Dominos",
        ],
        "McDonalds": [
            "UPI: McDonalds", "McDonalds", "MCDONALDS", "POS: McDonalds",
            "HARDCASTLE RESTAURANTS", "UPI: McDonald", "McD", "POS: McD",
        ],
        "KFC": [
            "UPI: KFC", "KFC", "POS: KFC", "KFC INDIA", "DEVYANI INTERNATIONAL",
        ],
        "Pizza Hut": [
            "UPI: Pizza Hut", "PIZZA HUT", "POS: Pizza Hut", "SAPPHIRE FOODS",
        ],
        "Burger King": [
            "UPI: Burger King", "BURGER KING", "POS: Burger King", "BURGER KING INDIA",
        ],
        "Subway": ["UPI: Subway", "SUBWAY", "POS: Subway", "SUBWAY INDIA"],
        "Local Restaurant": [
            "UPI: Hotel ", "UPI: Restaurant", "UPI: Dhaba", "UPI: Mess",
            "UPI: Tiffin", "UPI: Biryani", "UPI: Chinese", "UPI: Thali",
            "POS: Restaurant", "UPI: Food", "UPI: Lunch", "UPI: Dinner",
            "UPI: Breakfast", "UPI: Snacks", "UPI: Canteen",
        ],
        "MagicPin": ["UPI: MagicPin", "MAGICPIN", "UPI: Magicpin", "POS: MagicPin"],
        "EatSure": ["UPI: EatSure", "EATSURE", "REBEL FOODS"],
        "Box8": ["UPI: Box8", "BOX8"],
        "Behrouz": ["UPI: Behrouz", "BEHROUZ BIRYANI"],
        "FreshMenu": ["UPI: FreshMenu", "FRESHMENU"],
    },
    "Entertainment": {
        "BookMyShow": [
            "UPI: BookMyShow", "BOOKMYSHOW", "BIGTREE ENTERTAINMENT",
            "UPI: Bookmyshow", "POS: BookMyShow", "BookMyShow",
        ],
        "PVR INOX": [
            "UPI: PVR", "PVR INOX", "PVR CINEMAS", "INOX LEISURE", "POS: PVR",
            "UPI: INOX", "PVR", "INOX", "POS: INOX",
        ],
        "Netflix": [
            "NETFLIX", "NETFLIX.COM", "Netflix", "NETFLIX SUBSCRIPTION",
            "NETFLIX INDIA", "Netflix Subscription",
        ],
        "Amazon Prime": [
            "AMAZON PRIME", "AMAZON PRIME VIDEO", "PRIMEVIDEO.COM",
            "Amazon Prime", "PRIME VIDEO",
        ],
        "Hotstar": [
            "DISNEY HOTSTAR", "HOTSTAR", "HOTSTAR PREMIUM", 
            "NOVI DIGITAL", "Disney Hotstar",
        ],
        "Spotify": [
            "SPOTIFY", "SPOTIFY INDIA", "SPOTIFY PREMIUM", "Spotify",
        ],
        "YouTube Premium": [
            "YOUTUBE PREMIUM", "GOOGLE YOUTUBE", "YouTube Premium",
        ],
        "Gaming": [
            "STEAM", "STEAM PURCHASE", "PLAYSTATION", "GOOGLE PLAY",
            "UPI: Dream11", "DREAM11", "MPL", "UPI: MPL",
        ],
        "JioCinema": ["JIOCINEMA", "JIO CINEMA", "UPI: JioCinema"],
        "SonyLIV": ["SONYLIV", "SONY LIV"],
        "Zee5": ["ZEE5", "UPI: Zee5"],
    },
    "Cafes": {
        "Starbucks": [
            "UPI: Starbucks", "STARBUCKS", "TATA STARBUCKS", "POS: Starbucks",
            "Starbucks Coffee", "Starbucks", "POS: STARBUCKS",
        ],
        "CCD": [
            "CAFE COFFEE DAY", "CCD", "UPI: CCD", "COFFEE DAY",
            "POS: CCD", "POS: Cafe Coffee Day",
        ],
        "Third Wave Coffee": [
            "THIRD WAVE COFFEE", "UPI: Third Wave", "Third Wave Coffee",
            "POS: Third Wave",
        ],
        "Blue Tokai": [
            "BLUE TOKAI", "UPI: Blue Tokai", "Blue Tokai Coffee",
        ],
        "Chaayos": ["CHAAYOS", "UPI: Chaayos", "Chaayos"],
        "Local Cafe": [
            "UPI: Cafe", "UPI: Tea", "UPI: Chai", "UPI: Coffee",
            "UPI: Local Chaiwala", "Local Chaiwala", "POS: Chai",
            "UPI: Tapri", "UPI: Cutting Chai",
        ],
    },
    "Pan & Tobacco": {
        "Pan Shop": [
            "UPI: Pan", "UPI: Paan", "UPI: Pan Shop", "UPI: Paan Shop",
            "UPI: Gutkha", "UPI: Tambaku", "Pan Shop", "Paan",
            "UPI: Pan Corner", "UPI: Paan Corner", "UPI: Pan Wala",
        ],
    },
    "Credit Card Payment": {
        "HDFC Card": [
            "HDFC CREDIT CARD", "HDFC CARD PAYMENT", "NEFT-HDFC CARD",
            "HDFC CC PAYMENT", "HDFC Bank Credit Card",
        ],
        "ICICI Card": [
            "ICICI CREDIT CARD", "ICICI CARD PAYMENT", "NEFT-ICICI CARD",
            "ICICI CC PAYMENT", "ICICI Bank Credit Card",
        ],
        "SBI Card": [
            "SBI CREDIT CARD", "SBI CARD PAYMENT", "NEFT-SBI CARD",
            "SBI CC PAYMENT", "SBI Card",
        ],
        "Axis Card": [
            "AXIS CREDIT CARD", "AXIS CARD PAYMENT", "AXIS CC",
        ],
        "Kotak Card": [
            "KOTAK CREDIT CARD", "KOTAK CARD PAYMENT", "KOTAK CC",
        ],
    },
    "Bills & Utilities": {
        "Electricity": [
            "MSEDCL", "TATA POWER", "ADANI ELECTRICITY", "BESCOM",
            "UPI: Electricity", "Electricity Bill", "BSES", "CESC",
        ],
        "Gas": [
            "MAHANAGAR GAS", "HP GAS", "BHARAT GAS", "INDANE GAS",
            "UPI: Gas", "Gas Cylinder", "LPG REFILL",
        ],
        "Mobile Recharge": [
            "AIRTEL PREPAID", "UPI: Airtel", "AIRTEL RECHARGE",
            "UPI: Jio Recharge", "Jio Recharge", "JIO RECHARGE", "UPI: Jio",
            "VI RECHARGE", "UPI: Vi", "BSNL RECHARGE",
            "Airtel Recharge", "Jio Prepaid",
        ],
        "Broadband": [
            "AIRTEL BROADBAND", "JIO FIBER", "ACT FIBERNET", "HATHWAY",
            "UPI: Internet", "WiFi Bill", "Broadband",
        ],
        "Water Bill": ["WATER BOARD", "MUNICIPAL WATER", "UPI: Water Bill"],
        "DTH": [
            "TATA PLAY", "AIRTEL DTH", "DISH TV", "D2H RECHARGE",
            "UPI: DTH", "DTH Recharge",
        ],
        "Insurance": [
            "LIC PREMIUM", "HDFC LIFE", "ICICI PRUDENTIAL", "SBI LIFE",
            "Insurance Premium", "LIC", "BAJAJ ALLIANZ",
        ],
    },
    "Travel": {
        "Uber": [
            "UPI: Uber", "UPI: UberRides", "UBER INDIA", "UBER",
            "UberRides", "Uber", "UPI: Uber Rides", "UPI:UberRides",
        ],
        "Ola": [
            "UPI: Ola", "OLA CABS", "OLA", "Ola", "ANI TECHNOLOGIES",
            "UPI: Ola Cabs",
        ],
        "Rapido": [
            "UPI: Rapido", "RAPIDO", "Rapido", "RAPIDO BIKE",
        ],
        "IRCTC": [
            "IRCTC", "INDIAN RAILWAYS", "IRCTC WEB", "UPI: IRCTC",
            "Railway Ticket", "Train Ticket",
        ],
        "MakeMyTrip": ["MAKEMYTRIP", "MMT", "UPI: MakeMyTrip"],
        "Goibibo": ["GOIBIBO", "UPI: Goibibo"],
        "RedBus": ["REDBUS", "UPI: RedBus", "Red Bus"],
        "Petrol": [
            "PETROL PUMP", "HP PETROL", "BHARAT PETROLEUM", "INDIAN OIL",
            "UPI: Fuel", "POS: Petrol", "POS: Shell Petrol", "Shell Petrol",
            "POS: HP Petrol", "Petrol", "BPCL", "IOCL", "HPCL",
        ],
        "Metro": [
            "METRO RECHARGE", "DMRC", "PUNE METRO", "BMRCL",
            "UPI: Metro", "Metro Card Recharge",
        ],
        "Flight": [
            "INDIGO", "AIR INDIA", "VISTARA", "SPICEJET", "GOAIR",
            "UPI: IndiGo", "Flight Booking", "Air Ticket",
            "AKASA AIR", "AIRINDIA",
        ],
    },
    "Investments": {
        "Groww": [
            "UPI: Groww", "GROWW", "Groww", "NEXTBILLION TECH",
            "Groww Invest",
        ],
        "Zerodha": [
            "ZERODHA", "UPI: Zerodha", "ZERODHA KITE", "Zerodha",
        ],
        "Mutual Fund": [
            "SIP DEBIT", "MUTUAL FUND", "ICICI MF", "SBI MF", "HDFC AMC",
            "MF Purchase", "Axis MF", "NIPPON MF", "TATA MF",
        ],
        "PPF": ["PPF DEPOSIT", "PUBLIC PROVIDENT FUND", "PPF"],
        "Crypto": [
            "WAZIRX", "COINDCX", "COINSWITCH", "UPI: WazirX",
        ],
        "Fixed Deposit": ["FD CREATION", "FIXED DEPOSIT", "FD"],
    },
    "Shopping": {
        "Amazon": [
            "AMAZON", "UPI: Amazon", "UPI: Amazon Pay", "AMAZON PAY",
            "AMZN MKTP", "Amazon", "Amazon Pay", "POS: Amazon",
        ],
        "Flipkart": [
            "FLIPKART", "UPI: Flipkart", "FLIPKART INTERNET",
            "Flipkart", "POS: Flipkart",
        ],
        "Myntra": [
            "MYNTRA", "UPI: Myntra", "Myntra",
        ],
        "Ajio": ["AJIO", "RELIANCE AJIO", "UPI: Ajio"],
        "Nykaa": ["NYKAA", "UPI: Nykaa", "FSN E-COMMERCE"],
        "Meesho": ["MEESHO", "UPI: Meesho"],
        "BigBasket": [
            "BIGBASKET", "UPI: BigBasket", "UPI: Bigbasket",
        ],
        "BlinkIt": [
            "UPI: BlinkIt", "BLINKIT", "UPI: BlinkIt Groceries",
            "BlinkIt Groceries", "BlinkIt", "Blinkit",
        ],
        "Zepto": ["UPI: Zepto", "ZEPTO", "Zepto"],
        "DMart": [
            "POS: DMart", "DMART", "POS: DMART", "AVENUE SUPERMARTS",
            "DMart", "POS: Dmart",
        ],
        "Reliance": [
            "RELIANCE RETAIL", "RELIANCE FRESH", "RELIANCE SMART",
            "POS: Reliance", "JIO MART", "UPI: JioMart",
        ],
        "Local Shop": [
            "UPI: Shop", "UPI: Store", "UPI: Mart", "UPI: General Store",
            "UPI: Kirana", "UPI: Grocery", "POS: Shop",
        ],
        "Medical": [
            "UPI: Medical", "PHARMACY", "POS: Apollo Pharmacy",
            "Apollo Pharmacy", "APOLLO PHARMACY",
            "NETMEDS", "PHARMEASY", "UPI: Pharmacy", "UPI: Medplus",
            "1MG", "UPI: Chemist",
        ],
    },
    "Friends (Sent)": {
        "UPI Transfer": [
            "UPI/P2P/", "UPI: Transfer to", "IMPS TO", "NEFT TO",
            "UPI: Paid to", "GPay to", "PhonePe to",
            "UPI Transfer", "Sent to", "UPI/DR/",
        ],
    },
    "Friends (Received)": {
        "UPI Received": [
            "UPI/P2P/CR", "UPI: Received from", "IMPS FROM", "NEFT FROM",
            "UPI: Rcvd from", "GPay from", "PhonePe from",
            "UPI Received", "Received from", "UPI/CR/",
        ],
    },
    "Rent": {
        "House Rent": [
            "RENT PAYMENT", "HOUSE RENT", "NEFT-RENT", "UPI: Rent",
            "Rent", "Monthly Rent", "Room Rent",
        ],
        "PG/Hostel": [
            "PG CHARGES", "HOSTEL FEE", "PG Rent", "Hostel",
        ],
    },
    "Education": {
        "College Fee": [
            "COLLEGE FEE", "UNIVERSITY FEE", "TUITION FEE", "EXAM FEE",
            "Semester Fee",
        ],
        "Online Course": [
            "BYJUS", "UNACADEMY", "VEDANTU", "COURSERA", "UDEMY",
            "UPI: Byju", "UPI: Unacademy",
        ],
        "Books": ["UPI: Books", "AMAZON KINDLE", "Bookstore"],
    },
    "Health": {
        "Hospital": [
            "HOSPITAL", "CLINIC", "UPI: Doctor", "UPI: Hospital",
            "UPI: Clinic", "Doctor Fee", "Hospital Bill",
        ],
        "Gym": [
            "GYM FEE", "FITNESS", "UPI: Gym", "CULT FIT", "CULTFIT",
            "Gym Membership", "UPI: CultFit",
        ],
        "Lab Test": [
            "THYROCARE", "DR LAL PATH", "SRL DIAGNOSTICS",
            "UPI: Lab", "Blood Test", "Pathology",
        ],
    },
    "Others": {
        "ATM Withdrawal": [
            "ATM WDL", "ATM CASH", "CASH WITHDRAWAL", "ATM",
        ],
        "Bank Charges": [
            "ANNUAL MAINT", "SMS CHARGES", "DEBIT CARD FEE", "LOCKER RENT",
        ],
        "Government": [
            "GOVT CHARGES", "STAMP DUTY", "RTO FEE", "PASSPORT FEE",
            "FINE", "CHALLAN",
        ],
    },
}

# Famous Indian names for P2P transfers
FRIEND_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Rohan", "Pooja", "Karan", "Neha",
    "Arjun", "Sakshi", "Vikram", "Anjali", "Aditya", "Simran", "Gaurav",
    "Shruti", "Varun", "Meera", "Harsh", "Divya", "Kunal", "Riya",
    "Siddharth", "Tanya", "Nikhil", "Ishita", "Manish", "Kavya", "Raj", "Nidhi",
    "Omkar", "Tanvi", "Sahil", "Komal", "Pranav", "Ruchi", "Aarav", "Bhavna",
    "Yash", "Pallavi", "Dhruv", "Megha", "Tushar", "Swati", "Akash", "Ritika",
    "Arya", "Sakhi", "Pratik", "Jyoti"
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Joshi", "Verma",
    "Kokate", "Kadam", "Deshmukh", "Jadhav", "Patil", "More", "Gaikwad",
    "Reddy", "Nair", "Rao", "Menon", "Iyer", "Chatterjee", "Das",
    "Agarwal", "Mishra", "Tiwari", "Pandey", "Dubey", "Soni", "Thakur",
]


def generate_dataset(n_samples=80000):
    """Generate massive realistic Indian banking transaction dataset"""
    data = []
    categories = list(MERCHANTS.keys())
    
    weights = {
        "Food": 0.17, "Entertainment": 0.05, "Cafes": 0.06,
        "Pan & Tobacco": 0.02, "Credit Card Payment": 0.03,
        "Bills & Utilities": 0.10, "Travel": 0.12, "Investments": 0.04,
        "Shopping": 0.12, "Friends (Sent)": 0.10, "Friends (Received)": 0.08,
        "Rent": 0.03, "Education": 0.02, "Health": 0.03, "Others": 0.03
    }
    
    for _ in range(n_samples):
        category = np.random.choice(categories, p=[weights[c] for c in categories])
        subcategories = list(MERCHANTS[category].keys())
        subcategory = np.random.choice(subcategories)
        patterns = MERCHANTS[category][subcategory]
        description = np.random.choice(patterns)
        
        # For friend transfers, append a real Indian name
        if category == "Friends (Sent)":
            first = np.random.choice(FRIEND_NAMES)
            last = np.random.choice(LAST_NAMES)
            # 60% include full name, 40% just first name
            name = f"{first} {last}" if np.random.rand() > 0.4 else first
            description = f"{description} {name}"
            amount = round(np.random.choice([100, 200, 500, 1000, 2000, 5000, 10000]) * np.random.uniform(0.5, 3), 2)
            merchant = name
        elif category == "Friends (Received)":
            first = np.random.choice(FRIEND_NAMES)
            last = np.random.choice(LAST_NAMES)
            name = f"{first} {last}" if np.random.rand() > 0.4 else first
            description = f"{description} {name}"
            amount = round(np.random.choice([100, 500, 1000, 2000, 5000]) * np.random.uniform(0.5, 2), 2)
            merchant = name
        elif category == "Food":
            amount = round(np.random.uniform(40, 1500), 2)
            merchant = subcategory
        elif category == "Entertainment":
            amount = round(np.random.uniform(99, 3000), 2)
            merchant = subcategory
        elif category == "Cafes":
            amount = round(np.random.uniform(20, 800), 2)
            merchant = subcategory
        elif category == "Credit Card Payment":
            amount = round(np.random.uniform(2000, 100000), 2)
            merchant = subcategory
        elif category == "Bills & Utilities":
            amount = round(np.random.uniform(100, 8000), 2)
            merchant = subcategory
        elif category == "Travel":
            amount = round(np.random.uniform(30, 25000), 2)
            merchant = subcategory
        elif category == "Investments":
            amount = round(np.random.uniform(500, 50000), 2)
            merchant = subcategory
        elif category == "Shopping":
            amount = round(np.random.uniform(50, 30000), 2)
            merchant = subcategory
        elif category == "Rent":
            amount = round(np.random.uniform(3000, 35000), 2)
            merchant = subcategory
        elif category == "Education":
            amount = round(np.random.uniform(300, 100000), 2)
            merchant = subcategory
        elif category == "Health":
            amount = round(np.random.uniform(50, 20000), 2)
            merchant = subcategory
        elif category == "Pan & Tobacco":
            amount = round(np.random.uniform(10, 500), 2)
            merchant = subcategory
        else:
            amount = round(np.random.uniform(50, 5000), 2)
            merchant = subcategory
        
        data.append({
            "description": description,
            "amount": amount,
            "category": category,
            "subcategory": subcategory,
            "merchant": merchant
        })
    
    return pd.DataFrame(data)


def train_model(df):
    """Train TF-IDF + RandomForest categorization pipeline"""
    print(f"\n📊 Training on {len(df)} transaction samples...")
    
    X = df['description']
    y = df['category']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),  # Unigrams + Bigrams + Trigrams
            lowercase=True,
            strip_accents='unicode',
            analyzer='char_wb',  # Character-level for better fuzzy matching
            min_df=2
        )),
        ('clf', RandomForestClassifier(
            n_estimators=200,
            max_depth=25,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    pipeline.fit(X_train, y_train)
    
    print("\n📈 Model Evaluation:")
    print(classification_report(y_test, pipeline.predict(X_test), zero_division=0))
    
    accuracy = pipeline.score(X_test, y_test)
    print(f"\n✅ Overall Accuracy: {accuracy:.4f}")
    
    return pipeline


if __name__ == "__main__":
    print("="*60)
    print("💸 Smart Spend Analyzer v2 — Massive Pre-Training")
    print("="*60)
    
    # Generate massive dataset
    df = generate_dataset(80000)
    
    # Save
    os.makedirs('data', exist_ok=True)
    csv_path = 'data/spend_categories_training.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Training dataset: {csv_path} ({len(df)} rows)")
    print(f"   Categories: {df['category'].nunique()}")
    print(f"   Unique descriptions: {df['description'].nunique()}")
    
    print("\n📊 Category Distribution:")
    print(df['category'].value_counts().to_string())
    
    # Train category model
    cat_pipeline = train_model(df)
    
    # Train subcategory model
    print("\n📊 Training Subcategory Model...")
    sub_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 3), lowercase=True, analyzer='char_wb', min_df=2)),
        ('clf', RandomForestClassifier(n_estimators=200, max_depth=25, min_samples_leaf=2, random_state=42, n_jobs=-1))
    ])
    X_sub_train, X_sub_test, y_sub_train, y_sub_test = train_test_split(df['description'], df['subcategory'], test_size=0.2, random_state=42)
    sub_pipeline.fit(X_sub_train, y_sub_train)
    sub_acc = sub_pipeline.score(X_sub_test, y_sub_test)
    print(f"✅ Subcategory Accuracy: {sub_acc:.4f}")
    
    # Save models
    os.makedirs('api/models', exist_ok=True)
    with open('api/models/spend_categorizer.pkl', 'wb') as f:
        pickle.dump(cat_pipeline, f)
    with open('api/models/spend_subcategorizer.pkl', 'wb') as f:
        pickle.dump(sub_pipeline, f)
    
    # Create empty learned CSV
    learned_path = 'data/spend_categories_learned.csv'
    if not os.path.exists(learned_path):
        pd.DataFrame(columns=['description', 'amount', 'category', 'subcategory', 'merchant', 'source']).to_csv(learned_path, index=False)
    
    print(f"\n✅ Models saved to api/models/")
    print(f"✅ Self-training CSV ready at {learned_path}")
    print("\n" + "="*60)
    print("🎉 v2 Training Complete — 80K rows, character-level TF-IDF!")
    print("="*60)
