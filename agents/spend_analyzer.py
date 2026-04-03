"""
SpendAnalyzerAgent v5 — Ultra-Accurate Indian Bank Statement Analyzer.
Architecture: pdfplumber Table Extraction → 1000+ Keyword Rules → ML → Gemini LLM (with smart prompts)
Post-processing: Recurring credit detection for salary, Indian name recognition for friends.
"""
import os
import json
import pickle
import pandas as pd
import numpy as np
import re
import PyPDF2
import io
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv
from collections import defaultdict, Counter

load_dotenv()

# ============================================================
# KEYWORD RULES ENGINE — 1000+ patterns
# Format: (keywords_list, category, subcategory_or_None)
# None subcategory → extract merchant name from description
# ============================================================
KEYWORD_RULES = [
    # ===== CASHBACK / REFUND (credits — check first) =====
    (["cashback", "cash back", "cb cr", "cashbk"], "Cashback / Refund", "Cashback"),
    (["refund", "reversal", "reversed", "refnd"], "Cashback / Refund", "Refund"),

    # ===== CREDIT CARD =====
    (["credit card", "cc payment", "card payment"], "Credit Card Payment", None),
    (["hdfc credit", "hdfc card", "hdfc cc"], "Credit Card Payment", "HDFC Card"),
    (["icici credit", "icici card", "icici cc"], "Credit Card Payment", "ICICI Card"),
    (["sbi credit", "sbi card", "sbi cc"], "Credit Card Payment", "SBI Card"),
    (["axis credit", "axis card", "axis cc"], "Credit Card Payment", "Axis Card"),
    (["kotak credit", "kotak card", "kotak cc"], "Credit Card Payment", "Kotak Card"),
    (["amex", "american express"], "Credit Card Payment", "AMEX"),

    # ===== EMI / LOAN =====
    (["emi ", "loan emi", "emi debit", "emi-", "auto debit emi", "emi/"], "EMI / Loan", "EMI Payment"),
    (["home loan", "housing loan"], "EMI / Loan", "Home Loan"),
    (["car loan", "vehicle loan"], "EMI / Loan", "Car Loan"),
    (["personal loan", "pl emi"], "EMI / Loan", "Personal Loan"),

    # ===== BILLS & UTILITIES (including bill payments) =====
    (["billpay", "bill pay", "bill payment", "billdesk", "lbbillpay", "bbillpay"], "Bills & Utilities", "Bill Payment"),
    (["msedcl", "tata power", "adani electricity", "bescom", "bses", "cesc", "electricity"], "Bills & Utilities", "Electricity"),
    (["mahanagar gas", "hp gas", "bharat gas", "indane gas", "lpg", "gas cylinder"], "Bills & Utilities", "Gas"),
    (["airtel", "jio ", "vodafone", "vi ", "bsnl", "mobile recharge"], "Bills & Utilities", "Mobile / Recharge"),
    (["broadband", "jio fiber", "act fibernet", "hathway", "wifi"], "Bills & Utilities", "Broadband"),
    (["tata play", "airtel dth", "dish tv", "d2h", "dth", "dishtv"], "Bills & Utilities", "DTH"),
    (["lic premium", "lic-", "hdfc life", "icici prudential", "sbi life", "bajaj allianz", "insurance", "lic "], "Bills & Utilities", "Insurance"),
    (["water board", "municipal", "water bill", "water tax"], "Bills & Utilities", "Water Bill"),
    (["recharge"], "Bills & Utilities", "Recharge"),
    (["postpaid", "post paid"], "Bills & Utilities", "Postpaid"),
    (["society", "maintenance charge", "maint charge"], "Bills & Utilities", "Society Maintenance"),

    # ===== FOOD — Major Brands =====
    (["swiggy", "bundl technologies", "bundl tech"], "Food", "Swiggy"),
    (["zomato", "zomato ltd"], "Food", "Zomato"),
    (["domino", "jubilant food"], "Food", "Dominos"),
    (["mcdonald", "mcd ", "hardcastle"], "Food", "McDonalds"),
    (["kfc", "devyani international"], "Food", "KFC"),
    (["pizza hut", "sapphire foods"], "Food", "Pizza Hut"),
    (["burger king"], "Food", "Burger King"),
    (["subway"], "Food", "Subway"),
    (["eatsure", "rebel foods", "faasos"], "Food", "EatSure"),
    (["box8"], "Food", "Box8"),
    (["behrouz"], "Food", "Behrouz Biryani"),
    (["freshmenu"], "Food", "FreshMenu"),
    (["magicpin"], "Food", "MagicPin"),
    (["biryani by kilo"], "Food", "Biryani By Kilo"),
    (["haldiram", "haldirams"], "Food", "Haldirams"),
    (["baskin robbins", "baskin"], "Food", "Baskin Robbins"),
    (["wow momo", "wow momos"], "Food", "Wow Momos"),
    (["barbeque nation", "barbecue nation"], "Food", "Barbeque Nation"),
    (["paradise biryani", "paradise restaurant"], "Food", "Paradise"),
    # Indian Street Food & Local Vendor Keywords
    (["dabeli", "dabelli", "dablewala"], "Food", None),
    (["vada pav", "vadapav", "vada-pav", "vadewala"], "Food", None),
    (["pav bhaji", "pavbhaji", "pav-bhaji"], "Food", None),
    (["samosa", "samosewala"], "Food", None),
    (["biryani", "biriyani"], "Food", None),
    (["dosa", "dosai", "dosewala", "dosa corner"], "Food", None),
    (["idli", "idly", "idli house"], "Food", None),
    (["thali", "rajdhani thali", "thali house"], "Food", None),
    (["paratha", "parantha", "parathe wala", "prathawala"], "Food", None),
    (["chole bhature", "bhature", "chole kulche"], "Food", None),
    (["momos", "momo ", "momowala", "tibetan"], "Food", None),
    (["chaat", "chaatwala", "chaat house", "chaat corner"], "Food", None),
    (["pani puri", "panipuri", "golgappa", "puchka", "gupchup"], "Food", None),
    (["misal", "misal pav", "misalpav"], "Food", None),
    (["poha", "pohewala", "pohe ", "batata poha"], "Food", None),
    (["lassi", "lassi shop", "lassi corner", "lassiwala"], "Food", None),
    (["jalebi", "jalebiwala", "jalebi fafda"], "Food", None),
    (["kulfi", "kulfiwala", "kulfi faluda"], "Food", None),
    (["bhel", "bhelpuri", "bhelwala", "bhel corner"], "Food", None),
    (["kebab", "kabab", "seekh kebab", "galouti"], "Food", None),
    (["tikka", "tikki", "aloo tikki", "paneer tikka"], "Food", None),
    (["naan", "tandoori", "tandoor", "roti "], "Food", None),
    (["dhaba", "highway dhaba", "punjabi dhaba"], "Food", None),
    (["mess ", "tiffin", "tiffin service", "lunch box"], "Food", None),
    (["canteen", "canteen food"], "Food", None),
    (["bakery", "cake shop", "cake house", "cake wala"], "Food", None),
    (["sweet shop", "mithai", "sweet mart", "sweets", "mithaiwala"], "Food", None),
    (["juice", "juice bar", "juice corner", "juice shop", "juice centre"], "Food", None),
    (["restaurant", "bhojnalay", "bhojnalaya", "resto ", "restro"], "Food", None),
    (["chicken", "chickencentre", "chicken centre", "chicken center", "chikencentre", "chiken centre"], "Food", None),
    (["mutton", "fish fry", "prawn", "egg ", "non veg", "nonveg", "meat"], "Food", None),
    (["chinese", "manchurian", "noodles", "chowmein", "chopsuey"], "Food", None),
    (["ice cream", "icecream", "naturals", "amul parlour", "gelato"], "Food", None),
    (["snack", "farsan", "namkeen", "mixture", "chiwda"], "Food", None),
    (["lunch", "dinner", "breakfast", "brunch", "nastha"], "Food", None),
    (["food", "eat ", "khana", "bhojan", "thalassery"], "Food", None),
    (["pizza", "burger", "sandwich", "wrap "], "Food", None),
    (["biryan", "pulao", "pulav"], "Food", None),
    (["paneer", "butter chicken", "butter paneer", "dal makhani", "rajma"], "Food", None),
    (["puri ", "kachori", "bedmi"], "Food", None),
    (["sev puri", "dahi puri", "ragda puri"], "Food", None),
    (["frankie", "roll ", "wrap point"], "Food", None),
    (["shawarma", "falafel", "hummus"], "Food", None),
    (["waffle", "pancake", "crepe"], "Food", None),
    (["smoothie", "shake ", "milkshake"], "Food", None),
    (["kitchen", "rasoi", "khanawal", "bandi"], "Food", None),
    (["pavwala", "pavbhaji stall", "bhaji pav"], "Food", None),
    (["anda ", "egg bhurji", "omelette"], "Food", None),
    (["mughlai", "lucknowi", "awadhi"], "Food", None),
    (["south indian", "udipi", "sagar ", "saravana"], "Food", None),
    (["hotel ", "bhavan", "bhawan"], "Food", None),

    # ===== CAFES =====
    (["starbucks", "tata starbucks"], "Cafes", "Starbucks"),
    (["cafe coffee day", "cafecoffeeday", " ccd "], "Cafes", "CCD"),
    (["third wave coffee", "third wave"], "Cafes", "Third Wave Coffee"),
    (["blue tokai"], "Cafes", "Blue Tokai"),
    (["chaayos"], "Cafes", "Chaayos"),
    (["chai point", "chaipoint"], "Cafes", "Chai Point"),
    (["chai ", "chaiwala", "tapri", "cutting chai", "tea stall"], "Cafes", "Chai / Tea"),
    (["coffee", "cafe", "caffe", "caffeine"], "Cafes", None),

    # ===== LIQUOR / WINE =====
    (["wine", "wines", "wineshop", "wine shop"], "Liquor / Wine", None),
    (["liquor", "beer", "bar ", "theka", "daru", "daaru", "ahata"], "Liquor / Wine", None),
    (["whisky", "whiskey", "vodka", "rum ", "brandy", "gin "], "Liquor / Wine", None),

    # ===== GIFT CARDS / VOUCHERS =====
    (["hubble", "gift card", "gift voucher", "voucher", "gyftr", "woohoo"], "Shopping", "Gift Cards"),
    (["applegift", "apple gift", "itunes"], "Shopping", "Apple Gift Card"),
    (["brandby"], "Shopping", "BrandBy"),

    # ===== SUBSCRIPTIONS / DIGITAL SERVICES =====
    (["googleindia", "google india", "google play", "google one", "google workspace"], "Subscription", "Google Subscription"),
    (["google "], "Subscription", "Google"),
    (["apple.com", "apple music", "icloud"], "Subscription", "Apple"),
    (["kukufm", "kuku fm", "kuku"], "Entertainment", "KukuFM"),
    (["dashreels", "dash reels", "dashreel"], "Entertainment", "Dashreels"),
    (["copylinkimage", "copylink"], "Subscription", "Digital Service"),
    (["lite ", "app subscription"], "Subscription", "App Subscription"),
    (["realmazon", "realmazonindia"], "Shopping", "Amazon"),

    # ===== CREDIT CARD / FINANCIAL APPS =====
    (["cred ", "cred-", "credclub", "dreamplug"], "Credit Card Payment", "CRED"),
    (["uni ", "uni-", "uni card"], "Credit Card Payment", "Uni Card"),

    # ===== INSURANCE =====
    (["acko", "ackogeneral", "acko general"], "Bills & Utilities", "Acko Insurance"),
    (["navi", "navibill", "navi bill", "navi health", "naviinsurance"], "EMI / Loan", "Navi"),
    (["policybazaar", "digit insurance", "godigit"], "Bills & Utilities", "Insurance"),

    # ===== GOVERNMENT / TAX =====
    (["maharashtrastate", "maharashtra state"], "Bills & Utilities", "Maharashtra State Govt"),
    (["mhada", "bmc ", "pmc ", "nmc "], "Bills & Utilities", "Municipal"),
    (["income tax", "gst payment", "epfo", "professional tax"], "Bills & Utilities", "Tax Payment"),

    # ===== TRANSIT / METRO =====
    (["punemetro", "pune metro", "punemtro"], "Travel", "Pune Metro"),
    (["ncmc", "ncmccard", "onepune"], "Travel", "Transit Card (NCMC)"),

    # ===== GROCERY / SUPERMARKET / FRUIT =====
    (["dailybasket", "daily basket"], "Shopping", "DailyBasket"),
    (["fruit", "fruits", "sabzi", "vegetable", "vegitable", "bhaji"], "Shopping", "Fruits / Vegetables"),
    (["gavaran", "organic", "desi "], "Shopping", "Local Organic"),
    (["laxmisuper", "laxmi super"], "Shopping", "Laxmi Supermarket"),
    (["aplasuper", "apla super"], "Shopping", "Apla Supermarket"),
    (["super ", "superstore"], "Shopping", "Supermarket"),
    (["genral", "jenral"], "Shopping", "General Store"),

    # ===== FOOD: Restaurants, Desserts, Bars =====
    (["resto", "restro", "restoand", "restobar"], "Food", None),
    (["dessert", "desserts", "moodsofdessert"], "Food", None),
    (["upahaar", "upahar", "uphar"], "Food", None),
    (["kachi", "kachchi", "kacchi"], "Food", None),
    (["barberry"], "Cafes", "Barberry"),
    (["dockyard"], "Food", None),

    # ===== BAR / LIQUOR (stricter: "barand" = bar and restaurant) =====
    (["barand", "bar and", "bar & ", "bar-and"], "Liquor / Wine", None),
    (["strawberry", "strawberrybar"], "Liquor / Wine", None),

    # ===== SALON / PERSONAL CARE =====
    (["unisex", "unisexsal", "unisex salon", "pineapple"], "Shopping", "Salon / Beauty"),

    # ===== HARDWARE / HOME IMPROVEMENT =====
    (["solidsurface", "solid surface", "shinesolid"], "Shopping", "Hardware / Home Improvement"),
    (["marble", "granite", "tiles", "ply", "plywood"], "Shopping", "Hardware"),

    # ===== BANKING / BANK CHARGES =====
    (["sbimops", "sbi mops"], "Others", "SBI Gateway"),
    (["sbi ", "sbicard"], "Credit Card Payment", "SBI"),

    # ===== REFUND / REVERSAL =====
    (["rev-upi", "reversal", "refund", "rev upi"], "Cashback / Refund", "UPI Reversal"),

    # ===== PAN & TOBACCO =====
    (["pan shop", "pan corner", "pan wala", "paan shop", "paan corner", "paan wala", "panwala"], "Pan & Tobacco", None),
    (["pan bhandar", "pan house", "pan centre", "pan center", "paan bhandar", "pan stall"], "Pan & Tobacco", None),
    (["gutkha", "tambaku", "tobacco", "beedi", "cigarette", "smoke", "sutta"], "Pan & Tobacco", None),
    (["panshop", "pan-shop"], "Pan & Tobacco", None),

    # ===== ENTERTAINMENT =====
    (["bookmyshow", "bigtree entertainment"], "Entertainment", "BookMyShow"),
    (["pvr", "inox", "pvr inox"], "Entertainment", "PVR INOX"),
    (["netflix"], "Entertainment", "Netflix"),
    (["amazon prime video", "primevideo"], "Entertainment", "Amazon Prime"),
    (["hotstar", "disney hotstar", "novi digital"], "Entertainment", "Hotstar"),
    (["spotify"], "Entertainment", "Spotify"),
    (["youtube premium", "google youtube"], "Entertainment", "YouTube Premium"),
    (["jiocinema", "jio cinema"], "Entertainment", "JioCinema"),
    (["sonyliv", "sony liv"], "Entertainment", "SonyLIV"),
    (["zee5"], "Entertainment", "Zee5"),
    (["dream11", "dream 11"], "Entertainment", "Dream11"),
    (["mpl "], "Entertainment", "MPL"),
    (["steam"], "Entertainment", "Steam Gaming"),
    (["paytm first", "paytm insider"], "Entertainment", "Paytm Insider"),

    # ===== SALARY / INCOME (recurring large credits) =====
    (["salary", "payroll", "imprest", "stipend", "remuneration", "wages", "allowance", "perks", "incentive", "bonus"], "Salary / Income", "Salary"),

    # ===== TRAVEL =====
    (["uber", "uberride", "uber india", "uber ride"], "Travel", "Uber"),
    (["ola cab", "ola ride", "ani technologies"], "Travel", "Ola"),
    (["rapido"], "Travel", "Rapido"),
    (["irctc", "indian railway", "railway", "train ticket", "rail ticket"], "Travel", "IRCTC / Railways"),
    (["redbus", "red bus"], "Travel", "RedBus"),
    (["makemytrip", " mmt "], "Travel", "MakeMyTrip"),
    (["goibibo"], "Travel", "Goibibo"),
    (["cleartrip"], "Travel", "Cleartrip"),
    (["ixigo"], "Travel", "Ixigo"),
    (["petrol", "diesel", "fuel", "shell ", "bharat petroleum", "bpcl", "iocl", "hpcl", "indian oil"], "Travel", "Petrol / Fuel"),
    (["metro recharge", "dmrc", "pune metro", "bmrcl", "metro card"], "Travel", "Metro"),
    (["indigo", "interglobe", "6e "], "Travel", "IndiGo Airlines"),
    (["air india", "airindia"], "Travel", "Air India"),
    (["vistara", "tata sia"], "Travel", "Vistara"),
    (["spicejet"], "Travel", "SpiceJet"),
    (["akasa air"], "Travel", "Akasa Air"),
    (["toll ", "fastag", "fast tag", "toll plaza", "netc "], "Travel", "Toll / FASTag"),
    (["parking", "park fee"], "Travel", "Parking"),
    (["bus ticket", "bus booking", "bus pass"], "Travel", "Bus"),
    (["flight", "air ticket"], "Travel", "Flight"),
    (["abhibus"], "Travel", "AbhiBus"),
    (["atlys", "atlysindia", "atlys india"], "Travel", "Atlys (Visa)"),
    (["visa ", "visa fee", "visa service", "visa application"], "Travel", "Visa Services"),
    (["vistjet", "vitjet"], "Travel", "VistJet"),
    (["oyo ", "oyo rooms", "oyorooms"], "Travel", "Hotel / Accommodation"),

    # ===== INVESTMENTS =====
    (["groww", "nextbillion tech"], "Investments", "Groww"),
    (["zerodha", "zerodha kite"], "Investments", "Zerodha"),
    (["sip debit", "mutual fund", "icici mf", "sbi mf", "hdfc amc", "mf purchase", "axis mf", "nippon mf"], "Investments", "Mutual Fund"),
    (["ppf deposit", "public provident"], "Investments", "PPF"),
    (["wazirx", "coindcx", "coinswitch"], "Investments", "Crypto"),
    (["fixed deposit", "fd creation"], "Investments", "Fixed Deposit"),
    (["nps ", "national pension"], "Investments", "NPS"),
    (["smallcase"], "Investments", "Smallcase"),

    # ===== SHOPPING =====
    (["amazon", "amzn", "amazon pay"], "Shopping", "Amazon"),
    (["flipkart", "flip kart"], "Shopping", "Flipkart"),
    (["myntra"], "Shopping", "Myntra"),
    (["ajio"], "Shopping", "Ajio"),
    (["nykaa", "fsn e-commerce"], "Shopping", "Nykaa"),
    (["meesho"], "Shopping", "Meesho"),
    (["bigbasket", "big basket"], "Shopping", "BigBasket"),
    (["blinkit", "blink it", "grofers"], "Shopping", "BlinkIt"),
    (["zepto"], "Shopping", "Zepto"),
    (["dmart", "avenue supermarts", "d mart", "d-mart"], "Shopping", "DMart"),
    (["reliance retail", "reliance fresh", "reliance smart", "jio mart", "jiomart"], "Shopping", "Reliance / JioMart"),
    (["croma"], "Shopping", "Croma"),
    (["decathlon"], "Shopping", "Decathlon"),
    (["pharmacy", "apollo pharmacy", "medplus", "netmeds", "pharmeasy", "1mg", "chemist", "medical"], "Shopping", "Medical / Pharmacy"),
    (["grocery", "kirana", "general store", "provision", "generals", "generalstore"], "Shopping", "Grocery"),
    (["bazar", "bazaar", "market", "bajar", "mandai", "mandi"], "Shopping", "Market / Bazar"),
    (["supermarket", "super market", "hypermarket", "departmental", "variety"], "Shopping", "Supermarket"),
    (["shoppers stop", "lifestyle", "pantaloons", "westside"], "Shopping", "Fashion"),
    (["lenskart"], "Shopping", "Lenskart"),
    (["pepperfry", "urban ladder", "ikea"], "Shopping", "Furniture"),
    (["stationery", "bookstore", "book shop"], "Shopping", "Stationery / Books"),
    (["cloth", "garment", "textile", "saree", "sari", "kurti", "readymade"], "Shopping", "Clothing"),
    (["jewel", "gold", "silver", "diamond", "tanishq"], "Shopping", "Jewellery"),
    (["hardware", "paint", "sanitary", "plumbing", "electric"], "Shopping", "Hardware"),
    (["salon", "beauty", "parlour", "parlor", "spa ", "haircut", "grooming"], "Shopping", "Salon / Beauty"),
    (["laundry", "dry clean", "ironing", "washing"], "Shopping", "Laundry"),

    # ===== RENT =====
    (["rent payment", "house rent", "room rent", "monthly rent"], "Rent", "House Rent"),
    (["pg charge", "hostel fee", "pg rent", "hostel"], "Rent", "PG / Hostel"),

    # ===== EDUCATION =====
    (["college fee", "university fee", "tuition fee", "exam fee", "semester fee"], "Education", "College Fee"),
    (["school fee", "school"], "Education", "School Fee"),
    (["byjus", "byju"], "Education", "Byjus"),
    (["unacademy"], "Education", "Unacademy"),
    (["vedantu"], "Education", "Vedantu"),
    (["coursera"], "Education", "Coursera"),
    (["udemy"], "Education", "Udemy"),

    # ===== HEALTH =====
    (["hospital", "clinic", "doctor"], "Health", "Hospital / Doctor"),
    (["gym fee", "gym membership", "cult fit", "cultfit", "gym "], "Health", "Gym / Fitness"),
    (["thyrocare", "dr lal path", "srl diagnostics", "lab test", "blood test", "pathology"], "Health", "Lab Test"),
    (["dentist", "dental"], "Health", "Dental"),
    (["eye care", "optician", "optical"], "Health", "Eye Care"),

    # ===== OTHERS / BANK / GOVERNMENT =====
    (["atm wdl", "atm cash", "cash withdrawal", "atm/", "atm-"], "Others", "ATM Withdrawal"),
    (["annual maint", "sms charge", "debit card fee", "locker rent", "bank charge", "service charge", "gst on"], "Others", "Bank Charges"),
    (["stamp duty", "rto ", "passport", "challan", "fine "], "Others", "Government"),
    (["donation", "charity", "temple", "mandir", "gurudwara", "church", "mosque"], "Others", "Donation"),
    (["courier", "delhivery", "blue dart", "dtdc", "ecom express"], "Others", "Courier"),
    (["chit fund", "chit ", "plan "], "Investments", "Chit Fund / Plan"),
]

# ============================================================
# COMMON INDIAN FIRST NAMES (for friend detection)
# ============================================================
INDIAN_NAMES = {
    "aarav", "aditya", "ajay", "akash", "aman", "amit", "amol", "anil", "ankit", "ankita",
    "arjun", "arya", "ashwin", "bharat", "bhavesh", "chetan", "chirag", "darshan", "deepak", "deepa",
    "devesh", "dhruv", "dinesh", "ganesh", "gaurav", "girish", "gopal", "govind", "harsh", "hemant",
    "indrajeet", "indra", "ishaan", "jatin", "jayesh", "karan", "kartik", "kavita", "kishore", "kunal",
    "lalit", "mahesh", "manish", "manoj", "mayur", "mohit", "mukesh", "naresh", "neha", "nikhil",
    "nilesh", "nitin", "om", "paresh", "pawan", "pooja", "pradeep", "prakash", "pranav", "prashant",
    "pratik", "pravin", "preeti", "priya", "rahul", "raj", "rajesh", "rakesh", "ram", "ramesh",
    "ravi", "rohit", "sachin", "sagar", "sakshi", "sandesh", "sanjay", "sanket", "santosh", "sarthak",
    "satish", "shekhar", "shivam", "shubham", "siddharth", "sneha", "sudhir", "sunil", "suresh", "swapnil",
    "tanmay", "tushar", "umesh", "vaibhav", "vijay", "vikram", "vinay", "vinod", "vishal", "vivek",
    "yash", "yogesh",
    # Common last name patterns
    "kumar", "sharma", "gupta", "singh", "verma", "patel", "joshi", "desai", "patil", "more",
    "jadhav", "pawar", "shinde", "kulkarni", "deshpande", "mane", "shirke", "kokate", "kadam",
    "bhosale", "gaikwad", "chavan", "salunkhe", "wagh", "nikam", "sawant", "thorat", "mahajan",
    "mali", "sonawane", "ingale", "kale", "dhole", "yadav", "mishra", "tiwari", "pandey", "dubey",
    "saxena", "agarwal", "jain", "goyal", "bansal", "mittal", "kapoor", "chopra", "mehra",
    "khanna", "bhatia", "arora", "sethi", "malhotra", "tandon", "sinha", "das", "nair", "menon",
    "iyer", "pillai", "reddy", "naidu", "raju", "rao", "krishna", "swamy", "hegde", "shetty",
    # Marathi names
    "damayanti", "sambhaji", "rajaram", "shantaram", "balkrishna", "dattatray", "eknath",
    "soham", "ananya", "avinash", "shreyas", "swara", "rupesh", "pramod", "dipak", "laxmi", 
    "amir", "sukhadev", "hrushikesh", "uday", "dnyaneswar", "baburao", "rishikesh", "sitaram", 
    "sai", "roopesh", "devendra", "basvaraj", "radhakanta", "dilawar", "mahamood", "farmud", 
    "pandurang", "nitesh", "dattaram", "devarashi", "madan", "suvarna", "bhaskar", "dharmu", 
    "avadhoot", "maruti", "maula", "basha", "samir", "anant", "sameer", "laxmikant",
}


class SpendAnalyzerAgent:
    def __init__(self):
        from agents.genai_client import get_genai_client, get_model_name, safe_generate
        self.client = get_genai_client()
        self.model_name = get_model_name()
        self._safe_generate = safe_generate
        
        base = os.path.dirname(__file__)
        cat_path = os.path.join(base, '..', 'api', 'models', 'spend_categorizer.pkl')
        sub_path = os.path.join(base, '..', 'api', 'models', 'spend_subcategorizer.pkl')
        try:
            with open(cat_path, 'rb') as f:
                self.category_model = pickle.load(f)
            with open(sub_path, 'rb') as f:
                self.subcategory_model = pickle.load(f)
            print("✓ SpendAnalyzerAgent v5: ML models loaded")
        except Exception as e:
            print(f"⚠️ ML models not loaded: {e}")
            self.category_model = None
            self.subcategory_model = None
            
        # Load Self-Learned Cache
        self.learned_cache = {}
        learned_path = os.path.join(base, '..', 'data', 'spend_categories_learned.csv')
        try:
            if os.path.exists(learned_path):
                df_learned = pd.read_csv(learned_path)
                for _, row in df_learned.iterrows():
                    desc = str(row.get('description', '')).strip().lower()
                    if desc:
                        self.learned_cache[desc] = {
                            'category': row['category'],
                            'subcategory': row['subcategory'],
                            'merchant': row['merchant']
                        }
                print(f"✓ Loaded {len(self.learned_cache)} self-learned patterns into cache")
        except Exception as e:
            print(f"⚠️ Could not load learned cache: {e}")

    def _apply_chronology_fix(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < 5 or 'source_math' not in df.columns:
            return df
            
        parsed_dates = []
        for i, row in df.iterrows():
            d_str = str(row['date'])
            match = re.search(r'(\d{1,4}[/.-]\d{2}[/.-]\d{1,4})', d_str)
            if match:
                s = match.group(1)
                dt = None
                for fmt in ('%d/%m/%y', '%y/%m/%d', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y'):
                    try:
                        dt = datetime.strptime(s, fmt)
                        break
                    except: pass
                if dt:
                    parsed_dates.append((i, dt.timestamp()))
                    
        if len(parsed_dates) < 5:
            return df
            
        front = parsed_dates[:min(5, len(parsed_dates))]
        back = parsed_dates[-min(5, len(parsed_dates)):]
        avg_front = sum(x[1] for x in front) / len(front)
        
        # EXCLUSIVELY Strict Banking Syntax (To avoid "Charges/Fee" masking Merchant Names)
        STRONG_CREDIT = ['UPI/CR', 'NEFTCR', 'NEFT-CR', 'INWARD', 'BY CASH', 'IMPS-CR']
        STRONG_DEBIT = ['UPI/DR', 'NEFTDR', 'NEFT-DR', 'POS ', 'ATM WDL', 'CASH WDL', 'IMPS-DR']
        
        forward_votes = 0
        reverse_votes = 0
        
        for i, row in df.iterrows():
            if not row.get('source_math', False):
                continue
                
            desc = str(row['description']).upper()
            is_credit_calc = bool(row['is_credit'])
            
            is_sem_credit = any(kw in desc for kw in STRONG_CREDIT)
            is_sem_debit = any(kw in desc for kw in STRONG_DEBIT)
            
            if is_sem_credit and not is_sem_debit:
                if is_credit_calc: forward_votes += 1
                else: reverse_votes += 1
            elif is_sem_debit and not is_sem_credit:
                if not is_credit_calc: forward_votes += 1
                else: reverse_votes += 1
                
        if reverse_votes > forward_votes and reverse_votes >= 1:
            print(f"⏳ Semantic Calibration TRIGGERED: {reverse_votes} REVERSE vs {forward_votes} FORWARD. Inverting Math!")
            df.loc[df['source_math'] == True, 'is_credit'] = ~df.loc[df['source_math'] == True, 'is_credit']
        else:
            print(f"🔄 Semantic Calibration OK: {forward_votes} FORWARD vs {reverse_votes} REVERSE.")
            
        return df

    def extract_transactions_from_pdf(self, pdf_bytes: bytes, password: str = None) -> pd.DataFrame:
        full_text = ""
        
        try:
            import pdfplumber
            pdf = pdfplumber.open(io.BytesIO(pdf_bytes), password=password or None)
            tables_found = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        tables_found.append(table)
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            pdf.close()
            if tables_found:
                result = self._parse_tables(tables_found)
                if not result.empty and len(result) > 3:
                    print(f"✓ Table extraction: {len(result)} transactions")
                    return result
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️ pdfplumber: {e}")
        
        if not full_text:
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                if reader.is_encrypted:
                    reader.decrypt(password or "")
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            except Exception as e:
                print(f"⚠️ PyPDF2: {e}")
        
        if not full_text.strip():
            return pd.DataFrame(columns=['date', 'description', 'amount', 'is_credit', 'source_math'])
        
        result = self._parse_text_transactions(full_text)
        if not result.empty and len(result) > 3:
            return result
        
        print("⚠️ Regex failed, using LLM extraction...")
        return self._llm_extract_transactions(full_text)

    def _parse_tables(self, tables: list) -> pd.DataFrame:
        rows = []
        seen = set()
        prev_balance = None
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            for row_data in table[1:]:
                if not row_data: continue
                
                cells = [str(x).replace('\n', ' ').strip() if x is not None else '' for x in row_data]
                if not any(cells): continue
                
                date = cells[0]
                if not re.search(r'\d', date) and len(cells) > 1:
                    date = cells[1]
                if not re.search(r'\d', date): continue
                
                desc = max(cells[:4], key=len, default='')
                if len(desc) < 3 or any(k in desc.lower() for k in ['opening balance', 'closing balance', 'brought forward']):
                    continue
                
                amt_cols = []
                for cell in cells:
                    val = self._parse_amount(cell)
                    if val != 0: amt_cols.append(val)
                
                if not amt_cols: continue
                
                amount = 0
                is_credit = False
                source_math = False
                CREDIT_KW = ['SALARY', 'NEFTCR', 'NEFT CR', 'UPI/CR', 'RECEIVED', 'REFUND', 'CASHBACK', 'CREDIT', 'INTEREST', 'DIVIDEND', 'INWARD']
                
                if len(amt_cols) >= 2:
                    current_balance = amt_cols[-1]
                    amount_candidates = amt_cols[:-1]
                    
                    valid_cands = [x for x in amount_candidates if x < 100000000]
                    fallback_amt = valid_cands[-1] if valid_cands else amount_candidates[-1]
                    
                    if prev_balance is not None:
                        delta = round(current_balance - prev_balance, 2)
                        
                        if delta > 0:
                            amount = delta
                            is_credit = True
                        elif delta < 0:
                            amount = abs(delta)
                            is_credit = False
                        else:
                            amount = fallback_amt
                            is_credit = any(kw in desc.upper() for kw in CREDIT_KW)
                        
                        source_math = True
                    else:
                        amount = abs(fallback_amt)
                        is_credit = any(kw in desc.upper() for kw in CREDIT_KW)
                        source_math = False
                        
                    prev_balance = current_balance
                elif len(amt_cols) == 1:
                    amount = abs(amt_cols[0])
                    if amount > 100000000: amount = 0 
                    is_credit = any(kw in desc.upper() for kw in CREDIT_KW)
                    source_math = False
                    prev_balance = None
                
                if amount > 0:
                    txn_hash = f"{date}_{desc[:20]}_{amount}_{is_credit}"
                    if txn_hash not in seen:
                        seen.add(txn_hash)
                        rows.append({'date': date, 'description': desc, 'amount': amount, 'is_credit': is_credit, 'source_math': source_math})
        
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=['date', 'description', 'amount', 'is_credit', 'source_math'])

    def _parse_amount(self, val) -> float:
        if val is None:
            return 0
        s = str(val).strip()
        if not s or s in ['-', '0', '0.00'] or s.lower() in ['none', 'nan']:
            return 0
        is_neg = s.startswith('-') or ('-' in s) or s.lower().endswith('dr')
        # Remove Rs., INR, ₹, spaces, and commas. Leave the decimal intact!
        s = re.sub(r'(?i)rs\.?|inr|₹|\s|,|dr|cr', '', s).strip()
        try:
            parsed = float(s)
            return -abs(parsed) if is_neg else abs(parsed)
        except ValueError:
            return 0

    def _parse_text_transactions(self, raw_text: str) -> pd.DataFrame:
        rows = []
        lines = raw_text.split('\n')
        CREDIT_KW = ['SALARY', 'SAL CR', 'NEFTCR', 'NEFT CR', 'UPI/CR', 'DEPOSIT', 'RECEIVED', 'REFUND', 'CASHBACK', 'INTEREST', 'DIVIDEND', 'CREDITED', 'CR-', '/CR/', 'CR ', 'INWARD']
        prev_balance = None
        
        # Look for Date + Text + [1 or more amounts]
        for line in lines:
            line = line.strip()
            # Match start with date like 12/04/2024 or 2024-04-12 or 12-04-2024
            date_match = re.match(r'^(\d{1,4}[/.-]\d{2}[/.-]\d{1,4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)', line)
            if not date_match:
                continue
                
            dt = date_match.group(1)
            rest = line[len(dt):].strip()
            
            # Strategy: split string safely
            parts = rest.split()
            amounts = []
            desc_parts = []
            
            for p in parts:
                cleaned = re.sub(r'(?i)rs\.?|inr|₹|,', '', p)
                try:
                    # Allow negative parsing for text too
                    is_neg = p.startswith('-') or ('-' in p) or p.lower().endswith('dr')
                    cleaned_num = re.sub(r'(?i)dr|cr', '', cleaned).strip()
                    if cleaned_num.startswith('-'): cleaned_num = cleaned_num[1:]
                    val = float(cleaned_num)
                    if is_neg: val = -val
                    
                    if re.match(r'^-?\d+(\.\d{1,2})?$', '-'+cleaned_num if is_neg else cleaned_num):
                        amounts.append(val)
                    else:
                        desc_parts.append(p)
                except ValueError:
                    desc_parts.append(p)
            
            if not amounts:
                continue
                
            desc = " ".join(desc_parts)
            if len(desc) < 3: continue
            
            amount = 0
            is_credit = False
            source_math = False
            
            if len(amounts) >= 2:
                # E.g. [Withdrawal, Deposit, Balance]
                current_balance = amounts[-1]
                amount_candidates = amounts[:-1]
                
                valid_cands = [x for x in amount_candidates if x < 100000000]
                fallback_amt = valid_cands[-1] if valid_cands else amount_candidates[-1]
                
                # ALGEBRAIC SEQUENCE Tracker
                if prev_balance is not None:
                    delta = round(abs(current_balance - prev_balance), 2)
                    
                    if delta > 0:
                        amount = delta
                        is_credit = (current_balance > prev_balance)
                        source_math = True
                    else:
                        amount = fallback_amt
                        is_credit = any(kw in desc.upper() for kw in CREDIT_KW)
                        source_math = False
                else:
                    amount = fallback_amt
                    is_credit = any(kw in desc.upper() for kw in CREDIT_KW)
                    source_math = False
                    
                prev_balance = current_balance
            else:
                amount = amounts[0]
                if amount > 100000000: amount = 0
                is_credit = any(kw in desc.upper() for kw in CREDIT_KW)
                source_math = False
                prev_balance = None
            
            if amount > 0:
                rows.append({'date': dt[:10], 'description': desc, 'amount': amount, 'is_credit': is_credit, 'source_math': source_math})
                
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=['date', 'description', 'amount', 'is_credit', 'source_math'])

    def _llm_extract_transactions(self, raw_text: str) -> pd.DataFrame:
        if not self.client:
            return pd.DataFrame(columns=['date', 'description', 'amount', 'is_credit'])
        from google.genai import types
        
        all_txns = []
        chunk_size = 12000
        
        for start in range(0, min(len(raw_text), 60000), chunk_size):
            chunk = raw_text[start:start + chunk_size]
            if not chunk.strip():
                break
            
            prompt = f"""Extract ALL financial transactions from this Indian bank statement text.
For each transaction return: date, description (FULL narration text), amount (number), is_credit (boolean — true ONLY if money was RECEIVED/CREDITED into account, false if DEBITED/SPENT).

CRITICAL EXTRACTION RULES:
1. NEVER confuse the trailing 'Balance' column for the transaction amount. The transaction amount will be listed BEFORE the running balance!
2. If there are separate Debit and Credit columns, use those to determine is_credit.
3. If an unusually massive credit (₹15,000+) arrives on a recurring date from a corporate entity, it is highly likely SALARY!
4. Do NOT classify a transaction as DEBIT if it is clearly Salary, a Refund, or a Credit.

Return JSON array only. Be exhaustive — extract EVERY single transaction.

Text:
{chunk}"""
            
            try:
                resp = self._safe_generate(
                    self.client, self.model_name, prompt,
                    types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1))
                txns = json.loads(resp.text)
                if isinstance(txns, list):
                    all_txns.extend(txns)
            except Exception as e:
                print(f"LLM extract chunk error: {e}")
        
        if all_txns:
            df = pd.DataFrame(all_txns)
            df.columns = [c.lower().strip() for c in df.columns]
            if 'amount' in df.columns:
                df['amount'] = df['amount'].apply(lambda x: abs(float(x)) if x else 0)
            if 'is_credit' not in df.columns:
                df['is_credit'] = False
            if 'description' not in df.columns and 'narration' in df.columns:
                df['description'] = df['narration']
            required = ['date', 'description', 'amount', 'is_credit']
            for c in required:
                if c not in df.columns:
                    df[c] = '' if c in ['date', 'description'] else (False if c == 'is_credit' else 0)
            return df[required]
        
        return pd.DataFrame(columns=['date', 'description', 'amount', 'is_credit'])

    # ============================================================
    # TWO-PASS CATEGORIZATION
    # Pass 1: Keywords → Indian Name → ML (offline, instant)
    # Pass 2: AI reviews Friends + Others (corrects misclassifications, self-trains)
    # ============================================================
    def categorize_transactions(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {"error": "No transactions found"}
        
        results = []
        kw_hits = ml_hits = llm_hits = 0
                
        # ===== PASS 1: Offline Classification (Keywords + ML + Learned Cache) =====
        print("═══ PASS 1: Offline Classification (Learned Cache + Keywords + ML) ═══")
        for i, row in df.iterrows():
            desc = str(row.get('description', ''))
            amt = float(row.get('amount', 0))
            is_credit = bool(row.get('is_credit', False))
            date = str(row.get('date', ''))
            merchant = self._extract_merchant_name(desc)
            desc_lower = desc.strip().lower()

            # Layer 0: Instant match from Self-Learned Cache (from previous AI reviews)
            if desc_lower in self.learned_cache:
                cached = self.learned_cache[desc_lower]
                kw_hits += 1
                results.append(self._make_result(date, desc, amt, is_credit, 
                    cached['category'], cached['subcategory'], cached['merchant'], 'LearnedCache', 99.0))
                continue
            
            # Layer 1: Keyword Rules (1500+ patterns)
            cat, subcat = self._keyword_classify(desc, amt, is_credit)
            if cat:
                kw_hits += 1
                results.append(self._make_result(date, desc, amt, is_credit, cat, subcat or merchant, subcat or merchant, 'Keywords', 95.0))
                continue
            
            # Layer 1.5: Indian Name → Friends
            if self._looks_like_indian_name(desc, merchant):
                cat = "Friends (Received)" if is_credit else "Friends (Sent)"
                kw_hits += 1
                results.append(self._make_result(date, desc, amt, is_credit, cat, merchant, merchant, 'NameMatch', 90.0))
                continue
            
            # Layer 2: ML Model
            if self.category_model:
                try:
                    proba = self.category_model.predict_proba([desc])[0]
                    if proba.max() >= 0.55:
                        ml_hits += 1
                        results.append(self._make_result(date, desc, amt, is_credit,
                            self.category_model.predict([desc])[0],
                            self.subcategory_model.predict([desc])[0] if self.subcategory_model else merchant,
                            merchant, 'ML', round(float(proba.max()) * 100, 1)))
                        continue
                except:
                    pass
            
            # Layer 3: Unclassified → mark as "Others" for now
            results.append(self._make_result(date, desc, amt, is_credit, 'Others', merchant, merchant, 'Pending', 0))
        
        print(f"  ✓ Pass 1 complete: {kw_hits} Keywords, {ml_hits} ML, {len([r for r in results if r['source'] == 'Pending'])} unclassified")
        
        # ===== PASS 2: AI Review of Friends + Others =====
        # Collect all "suspicious" items: ALWAYS review Friends + Others
        review_queue = []
        for i, r in enumerate(results):
            if r['category'] in ('Others', 'Friends (Sent)', 'Friends (Received)'):
                review_queue.append({
                    'index': i, 'date': r['date'], 'description': r['description'],
                    'amount': r['amount'], 'is_credit': r['is_credit'],
                    'merchant': r['merchant'], 'current_category': r['category'],
                    'original_source': r['source'] # Track original source
                })
        
        if review_queue and self.client:
            print(f"═══ PASS 2: AI Review of {len(review_queue)} items (Friends + Others) ═══")
            ai_corrections = self._ai_review_pass(review_queue)
            
            for correction in ai_corrections:
                idx = correction.get('_idx')
                if idx is not None and idx < len(results):
                    old_cat = results[idx]['category']
                    new_cat = correction.get('category', old_cat)
                    if new_cat != old_cat:
                        print(f"  🔄 AI corrected: '{results[idx]['merchant']}' from [{old_cat}] → [{new_cat}]")
                        results[idx]['category'] = new_cat
                        results[idx]['subcategory'] = correction.get('subcategory', results[idx]['subcategory'])
                        results[idx]['merchant'] = correction.get('merchant', results[idx]['merchant'])
                        results[idx]['source'] = 'AI-Review'
                        results[idx]['confidence'] = 88.0
                        llm_hits += 1
            
            # Self-train: save ALL AI-reviewed corrections to training data
            self._save_learned_data([r for r in results if r.get('source') == 'AI-Review'])
            print(f"  ✓ Pass 2 complete: {llm_hits} AI corrections saved to training data")
        elif review_queue:
            # No AI available — keep them as they were
            pass
        
        # Post-processing: Detect salary from recurring credits
        results = self._detect_salary(results)
        
        return self._build_report(results, kw_hits, ml_hits, llm_hits)
    
    def _make_result(self, date, desc, amt, is_credit, cat, subcat, merchant, source, conf):
        return {'date': date, 'description': desc, 'amount': amt, 'is_credit': is_credit,
                'category': cat, 'subcategory': subcat, 'merchant': merchant,
                'source': source, 'confidence': conf}

    # ============================================================
    # KEYWORD CLASSIFICATION
    # ============================================================
    def _keyword_classify(self, desc: str, amount: float, is_credit: bool) -> Tuple[Optional[str], Optional[str]]:
        desc_lower = desc.lower()
        # Clean GPay/Paytm/PayU suffixes for better matching
        desc_clean = re.sub(r'[-/](?:gpay|paytm|phonepe|googlepay|bhim|payu)\b', '', desc_lower)
        desc_clean = re.sub(r'-(?:gpay|paytmqr|paytm)\b', '', desc_clean)
        
        # Pan shop special detection (before keyword matching)
        if self._is_pan_shop(desc_lower) or self._is_pan_shop(desc_clean):
            return ("Pan & Tobacco", self._extract_merchant_name(desc))
        
        # Bill payment special detection
        if 'billpay' in desc_lower or 'bill pay' in desc_lower or 'lbbillpay' in desc_lower:
            return ("Bills & Utilities", "Bill Payment")
        
        # Keyword matching against BOTH original AND cleaned descriptions
        for keywords, category, subcategory in KEYWORD_RULES:
            for kw in keywords:
                if kw in desc_lower or kw in desc_clean:
                    return (category, subcategory if subcategory else self._extract_merchant_name(desc))
        
        # Credit from non-merchant → ONLY Friends if name looks like a person
        if is_credit and not self._has_merchant_keyword(desc_lower):
            merchant = self._extract_merchant_name(desc)
            if self._looks_like_indian_name(desc, merchant):
                return ("Friends (Received)", merchant)
            # If name has business indicators, let it fall to LLM
            if self._looks_like_business(merchant):
                return (None, None)  # Send to LLM
            # Default: still classify as Friends for credits with clean person-like names
            return ("Friends (Received)", merchant)
        
        return (None, None)

    def _has_merchant_keyword(self, desc_lower: str) -> bool:
        for keywords, category, subcategory in KEYWORD_RULES:
            for kw in keywords:
                if kw in desc_lower:
                    return True
        return False

    def _is_pan_shop(self, desc_lower: str) -> bool:
        if any(kw in desc_lower for kw in ['pan shop', 'paan shop', 'pan corner', 'paan corner', 'pan wala', 'paan wala', 'panwala', 'pan bhandar', 'paan bhandar', 'panshop', 'pan stall']):
            return True
        # Word-boundary "pan" detection — matches " pan-", " pan ", "pan " at start, "XXX pan" names
        if 'pan card' not in desc_lower and 'pan number' not in desc_lower:
            if re.search(r'\bpan\b', desc_lower) and any(p in desc_lower for p in ['upi', 'paytm', 'gpay', 'phonepe', 'qr']):
                return True
            # Match merchant names ending with " pan" like "mahesh shantaram pan"
            if re.search(r'\w+\s+pan$', desc_lower.split('-')[0] if '-' in desc_lower else desc_lower):
                return True
        return False

    # Business indicator words — if ANY of these appear in a name, it's NOT a person
    BUSINESS_WORDS = {
        'shop', 'store', 'mart', 'enterprise', 'trader', 'service', 'centre', 'center',
        'hotel', 'cafe', 'caffe', 'restaurant', 'pvt', 'ltd', 'corp', 'tech', 'info', 'solution',
        'digital', 'mobile', 'pharma', 'medical', 'hospital', 'clinic', 'garage',
        'industries', 'trading', 'agency', 'works', 'hardware', 'electric', 'auto',
        'motors', 'sales', 'telecom', 'finance', 'bank', 'insurance', 'academy',
        'institute', 'college', 'university', 'school', 'studio', 'salon', 'beauty',
        'wine', 'wines', 'liquor', 'beer', 'bar', 'general', 'generals', 'grocery',
        'kirana', 'provision', 'bazar', 'bazaar', 'market', 'mandi', 'mandai',
        'chicken', 'bakery', 'sweet', 'juice', 'pan', 'paan', 'tobacco',
        'private', 'limited', 'pvtlt', 'pvtltd', 'ventures', 'startup',
        'foods', 'food', 'kitchen', 'hubble', 'gift', 'voucher', 'card',
        'omega', 'alpha', 'beta', 'global', 'international', 'national',
        'express', 'logistics', 'transport', 'cargo', 'courier',
        'online', 'web', 'app', 'software', 'systems', 'network',
        'labs', 'lab', 'research', 'consulting', 'consultancy',
        'builders', 'construction', 'realty', 'properties', 'estate',
        'jewel', 'gold', 'silver', 'diamond', 'cloth', 'textile', 'fabric',
        'laundry', 'tailor', 'stationery', 'print', 'photo',
        'petrol', 'fuel', 'gas', 'oil', 'tyre', 'tire', 'spare',
        'rent', 'subscription', 'premium', 'membership',
        # Merchant platforms — names with these are LOCAL MERCHANTS, not friends
        'bharatpe', 'bharat pe', 'bajajpay', 'bajaj pay', 'paytmqr', 'phonepeqr',
        # Food/restaurant indicators
        'resto', 'restro', 'restobar', 'dockyard', 'dessert', 'upahaar', 'uphar',
        'barberry', 'basket', 'dailybasket', 'gavaran',
        # Supermarket/grocery indicators  
        'super', 'supermarket', 'fruit', 'sabzi', 'vegetable',
        # Salon/beauty
        'unisex', 'parlour', 'parlor', 'haircut',
        # Other business indicators
        'surface', 'marble', 'granite', 'tiles',
        'metro', 'ncmc', 'transit',
        'acko', 'navi', 'cred', 'kukufm', 'dashreels',
    }

    def _looks_like_business(self, merchant: str) -> bool:
        """Check if merchant name contains business indicator words."""
        name = merchant.lower().strip()
        for bw in self.BUSINESS_WORDS:
            if bw in name and len(bw) >= 3:
                return True
        return False

    def _looks_like_indian_name(self, desc: str, merchant: str) -> bool:
        """Check if the extracted merchant name looks like an Indian personal name."""
        name = merchant.lower().strip()
        
        # If it has business words, it's NOT a person
        if self._looks_like_business(merchant):
            return False
        
        # Check if any known Indian name is a substring
        for indian_name in INDIAN_NAMES:
            if indian_name in name and len(indian_name) >= 4:
                return True
        
        # Check if the name is 2-3 words, all alphabetic, looks like a person
        words = name.split()
        if 1 <= len(words) <= 4:
            all_alpha = all(w.isalpha() for w in words)
            if all_alpha and 3 <= len(name) <= 30:
                desc_lower = desc.lower()
                if any(p in desc_lower for p in ['upi', 'neft', 'imps', 'rtgs']):
                    return True
        
        return False

    # ============================================================
    # POST-PROCESSING: Dynamic Employer Discovery (Salary)
    # 0-100 Mathematical Score Matrix
    # ============================================================
    def _detect_salary(self, results: list) -> list:
        unique_months = set()
        for r in results:
            match = re.search(r'(\d{2}[/.-]\d{4}|\d{4}[/.-]\d{2})', str(r.get('date', '')))
            if match:
                unique_months.add(match.group(1))
        
        statement_months = max(1, len(unique_months))
        dynamic_threshold = max(2, int(statement_months * 0.5))

        # 1. Cluster all significant Incomes purely by mathematical amounts (±20% variance)
        # This completely bypasses the 'Vadiniinfocenter' vs 'Icic0' Name-Change bug!
        amount_clusters = []
        for i, r in enumerate(results):
            if r['is_credit'] and r['amount'] >= 10000:
                amount = r['amount']
                placed = False
                for cluster_idx, indices in amount_clusters:
                    center_amt = sum([results[idx]['amount'] for idx in indices]) / len(indices)
                    if 0.8 * center_amt <= amount <= 1.2 * center_amt:
                        indices.append(i)
                        placed = True
                        break
                if not placed:
                    amount_clusters.append((amount, [i]))

        # 2. Evaluate Matrix Scoring System per Cluster
        SALARY_KW = ['SALARY', 'PAYROLL', 'SAL', 'STIPEND', 'REMUNERATION']
        NEFT_KW = ['NEFT', 'IMPS', 'ACH', 'RTGS']
        
        for base_amt, indices in amount_clusters:
            if len(indices) >= dynamic_threshold:
                # Calculate absolute Base conditions
                score = 0
                
                # Condition 1: Consistent Amount (+20) -> inherently true due to 0.8-1.2 cluster rules
                amounts = [results[idx]['amount'] for idx in indices]
                score += 20
                
                # Analyze descriptors within the matched cluster
                names = [str(results[idx]['merchant']).lower() for idx in indices]
                raw_descs = [str(results[idx]['description']).lower() for idx in indices]
                
                # Condition 2: Frequent Monthly Recurrence (+30)
                if len(indices) >= statement_months * 0.7:
                    score += 30
                    
                # Condition 3: Exact Identical Match vs Fuzzy (+20)
                if len(set(names)) == 1:
                    score += 20
                else:
                    # Fuzzy Sender Check (Vadiniinfocenter vs Icic0Sf0002-Vadini...)
                    sub_lengths = [len(n) for n in names]
                    shortest_name = names[sub_lengths.index(min(sub_lengths))]
                    if len(shortest_name) > 4 and all(shortest_name[:5] in n for n in names):
                        score += 20 # Passed Fuzzy String
                        
                # Condition 4: Keywords (+40)
                if any(kw in raw.upper() for raw in raw_descs for kw in SALARY_KW):
                    score += 40
                    
                # Condition 5: Valid Corporate Credit Setup (+10) 
                # (Prevents standard random UPIs from being declared Salaries)
                if any(kw in raw.upper() for raw in raw_descs for kw in NEFT_KW) or not any('UPI' in raw.upper() for raw in raw_descs):
                    score += 10
                
                # Final Determination!
                if score >= 60:
                    for idx in indices:
                        results[idx]['category'] = 'Salary / Income'
                        results[idx]['subcategory'] = 'Salary'
                        results[idx]['source'] = f'Score Rule ({score}/120)'
        
        return results

    # ============================================================
    # MERCHANT NAME EXTRACTION
    # ============================================================
    def _extract_merchant_name(self, desc: str) -> str:
        desc_clean = desc.strip()
        
        # NPCI: "UPI-ASHAPURA DABELI CEN-ASHAPURADABELI@..."
        m = re.match(
            r'(?:UPI|NEFT|IMPS|NEFTCR|NEFTDR)[-/](.+?)(?:\s*(?:CEN|TYS|YBL|JSB|SBI|HDFC|ICICI|AXIS|PAYTM|CENT|KVBL|MAHB|UCBA|UTIB|BKID|PUNB|SBIN|CNRB|IOBA|BARB)[-\s@]|[-/][A-Za-z0-9]+@|\s*$)',
            desc_clean, re.IGNORECASE
        )
        if m:
            name = m.group(1).strip()
            name = re.sub(r'^[A-Z]{4}\d{5,}[-\s]*', '', name).strip()  # Remove bank codes
            name = re.sub(r'[-\s]\d{5,}.*$', '', name).strip()  # Remove trailing refs
            name = re.sub(r'\s+', ' ', name).strip()
            if len(name) > 2:
                # Try to add spaces to concatenated names
                name = self._humanize_name(name)
                return name.title()
        
        # POS format
        m2 = re.match(r'POS[:]\s*(.+?)(?:\s*$|\s+Rs)', desc_clean, re.IGNORECASE)
        if m2:
            return m2.group(1).strip().title()
        
        # UPI: format
        m3 = re.match(r'UPI[:]\s*(.+?)(?:\s*$|\s+Rs)', desc_clean, re.IGNORECASE)
        if m3:
            return m3.group(1).strip().title()
        
        # NEFT credit: "NEFTCR-ICIC0099999-VADINIINFOCENTER-..."
        m4 = re.match(r'(?:NEFTCR|NEFTDR|NEFT)[-/](?:[A-Z]{4}\d+[-/])?(.+?)(?:[-/]\d|[-/][A-Z]{4}\d|\s*$)', desc_clean, re.IGNORECASE)
        if m4:
            name = m4.group(1).strip()
            name = re.sub(r'[-/].*$', '', name).strip()
            if len(name) > 2:
                name = self._humanize_name(name)
                return name.title()
        
        # "lbbillpaydr-Hdfc97-361010Xxxx6334 176961"
        m5 = re.match(r'(?:lbbillpay|billpay)\w*[-/](.+?)[-/\s]\d', desc_clean, re.IGNORECASE)
        if m5:
            return "Bill Payment - " + m5.group(1).strip().title()
        
        return desc_clean[:40].strip().title()

    def _humanize_name(self, name: str) -> str:
        """Try to add spaces to concatenated names like 'INDRAJEETRAJARAM' → 'INDRAJEET RAJARAM'."""
        name_lower = name.lower()
        
        # Check if it's already properly spaced
        if ' ' in name:
            return name
        
        # Try to find known Indian name boundaries
        best_split = name
        for indian_name in sorted(INDIAN_NAMES, key=len, reverse=True):
            if len(indian_name) < 4:
                continue
            idx = name_lower.find(indian_name)
            if idx >= 0:
                end = idx + len(indian_name)
                if idx > 0 and end < len(name):
                    best_split = name[:idx] + ' ' + name[idx:end] + ' ' + name[end:]
                elif idx == 0 and end < len(name):
                    best_split = name[:end] + ' ' + name[end:]
                elif idx > 0 and end >= len(name):
                    best_split = name[:idx] + ' ' + name[idx:]
                best_split = re.sub(r'\s+', ' ', best_split).strip()
                break
        
        return best_split

    # ============================================================
    # PASS 2: AI REVIEW — Reviews Friends + Others for misclassifications
    # ============================================================
    def _ai_review_pass(self, review_queue: list) -> list:
        """AI reviews items classified as Friends or Others.
        Returns corrected classifications that get saved to training data."""
        if not review_queue or not self.client:
            return []
        
        from google.genai import types
        all_corrections = []
        
        # Vertex AI Free Tier limits gemini-2.5-flash to 128k input tokens.
        # Batching 1000 items per request keeps processing fast while strictly
        # avoiding both the 15 RPM limit and silent Vertex AI payload hanging bugs.
        batch_size = 1000
        for i in range(0, len(review_queue), batch_size):
            batch = review_queue[i:i + batch_size]
            
            txn_list = "\n".join([
                f'{j+1}. [{r["current_category"]}] "{r["description"]}" — ₹{r["amount"]} ({"CREDITED" if r.get("is_credit") else "DEBITED"})'
                for j, r in enumerate(batch)
            ])
            
            prompt = f"""You are an expert Indian financial transaction reviewer. Our offline ML system already classified these transactions, but we need you to VERIFY and CORRECT them.

Each transaction below shows its CURRENT classification in [brackets]. Your job:
1. If the current category is CORRECT → keep it
2. If it is WRONG → provide the correct category

CATEGORIES (use exactly one):
Food, Cafes, Pan & Tobacco, Liquor / Wine, Entertainment, Credit Card Payment, Bills & Utilities, Travel, Investments, Shopping, Friends (Sent), Friends (Received), Rent, Education, Health, Salary / Income, Cashback / Refund, EMI / Loan, Grocery, Government / Tax, Subscription, Others

CRITICAL VERIFICATION RULES:
- HUMAN NAMES ARE ALWAYS FRIENDS: If the merchant name is a purely human name (e.g., 'ARYA SANJAY', 'ADESH RAVINDRA', 'JAIN LEESH', 'SAKSHI', etc.), it MUST be assigned to "Friends (Sent)" or "Friends (Received)" based on DEBIT/CREDIT.
- DO NOT PUT HUMAN NAMES IN 'Food' or 'Shopping' under any circumstances unless followed by 'Store', 'Cafe', 'Restaurant', etc.
- If it says "Friends" but the name is clearly a BUSINESS (e.g. "Omegawine", "A1ChickenCentre") → RECLASSIFY to Liquor / Wine, Food, etc.!
- SALARY RECOGNITION: If the transaction is an unusually large CREDIT (e.g., ₹20,000 to ₹5,00,000) from a corporate entity, IT IS LIKELY SALARY. Classify as "Salary / Income"! Do NOT call it "Others".
- "Others" should be LAST RESORT (<2%). Analyze the corporate name intelligently.

Transactions to review:
{txn_list}

Return JSON array:
[{{"index": 1, "category": "Salary / Income", "subcategory": "Vadini Infocenter", "merchant": "Vadini Infocenter"}}]"""
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    resp = self._safe_generate(
                        self.client, self.model_name, prompt,
                        types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1),
                        max_retries=3)
                    llm_data = json.loads(resp.text)
                    for item in llm_data:
                        idx = item.get('index', 1) - 1
                        if 0 <= idx < len(batch):
                            r = batch[idx]
                            all_corrections.append({
                                '_idx': r['index'],
                                'category': item.get('category', r.get('current_category', 'Others')),
                                'subcategory': item.get('subcategory', r.get('merchant', 'Unknown')),
                                'merchant': item.get('merchant', r.get('merchant', 'Unknown')),
                            })
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    import time
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        wait_time = 15 * (attempt + 1)
                        print(f"  ⏳ Gemini API Rate Limited (429). Waiting {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                        continue # Retry
                    else:
                        print(f"  ⚠️ AI Review error: {e}")
                        # If it's not a rate limit, or we exhausted retries, log failure and break
                        for r in batch:
                            all_corrections.append({
                                '_idx': r['index'],
                                'category': r.get('current_category', 'Others'),
                                'subcategory': r.get('merchant', 'Unknown'),
                                'merchant': r.get('merchant', 'Unknown'),
                            })
                        break
            else:
                # If we exhausted all retries
                print(f"  ❌ AI Review Failed after {max_retries} attempts.")
                for r in batch:
                    all_corrections.append({
                        '_idx': r['index'],
                        'category': r.get('current_category', 'Others'),
                        'subcategory': r.get('merchant', 'Unknown'),
                        'merchant': r.get('merchant', 'Unknown'),
                    })
        
        return all_corrections

    # ============================================================
    # LEGACY: LLM BATCH CATEGORIZATION (kept for compatibility)
    # ============================================================
    def _llm_batch_categorize(self, rows: list) -> list:
        if not rows or not self.client:
            return [{'_idx': r['index'], 'date': r['date'], 'description': r['description'],
                     'amount': r['amount'], 'is_credit': r.get('is_credit', False),
                     'category': 'Others', 'subcategory': r.get('merchant', 'Unknown'),
                     'merchant': r.get('merchant', 'Unknown'), 'source': 'Fallback', 'confidence': 0}
                    for r in rows]
        
        from google.genai import types
        all_results = []
        
        for batch_start in range(0, len(rows), 40):
            batch = rows[batch_start:batch_start + 40]
            txn_list = "\n".join([
                f'{i+1}. "{r["description"]}" — ₹{r["amount"]} ({"CREDITED" if r.get("is_credit") else "DEBITED"})'
                for i, r in enumerate(batch)])
            
            prompt = f"""You are an expert Indian bank transaction categorizer specializing in NPCI UPI, NEFT, IMPS, and Indian financial patterns.

CATEGORIES (use EXACTLY one):
Food, Cafes, Pan & Tobacco, Entertainment, Credit Card Payment, Bills & Utilities, Travel, Investments, Shopping, Friends (Sent), Friends (Received), Rent, Education, Health, Salary / Income, Cashback / Refund, EMI / Loan, Grocery, Others

ABSOLUTELY CRITICAL — MINIMIZE "Others":
- "Others" should be used for LESS THAN 5% of transactions
- ALWAYS try to categorize. Guess intelligently from the name.
- If a name has "pvt ltd" or "private limited" → research what company it is and pick the right category
- If a name sounds like food (any cuisine word, meat, restaurant) → Food
- If a name sounds like a market/bazar/shop → Shopping
- If a name is clearly a person → Friends (Sent/Received based on DEBIT/CREDIT)
- "AtlysIndiaPvtLt" = Atlys India = VISA processing company → Travel
- "ChickenCentre", "A1Chicken" = non-veg food shop → Food
- "ChiplunBazar" = local market/bazar → Shopping
- Names ending in "-Gpay" or "-Paytm" → strip the suffix, categorize the actual merchant
- "Pan" in a vendor name with UPI/Paytm = Pan/Tobacco shop → Pan & Tobacco

RULES:
1. CREDITED from a person → "Friends (Received)"
2. DEBITED to a person → "Friends (Sent)"
3. Indian personal names (2-3 words, all alphabetic, Marathi/Hindi names) → Friends
4. "NEFTCR" = money CREDITED (received)
5. "billpay"/"lbbillpay" = Bill Payment → Bills & Utilities
6. Salary = only recurring monthly CREDITED ≥₹15,000 from a company
7. Clean merchant names: strip bank codes, UPI refs, @addresses
8. If unsure between two categories, pick the MORE SPECIFIC one (never default to Others)

Transactions:
{txn_list}

Return JSON array ONLY:
[{{"index": 1, "category": "Food", "subcategory": "Ashapura Dabeli", "merchant": "Ashapura Dabeli"}}]"""

            try:
                resp = self._safe_generate(
                    self.client, self.model_name, prompt,
                    types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1),
                    max_retries=3)
                llm_data = json.loads(resp.text)
                for item in llm_data:
                    idx = item.get('index', 1) - 1
                    if 0 <= idx < len(batch):
                        r = batch[idx]
                        all_results.append({
                            '_idx': r['index'], 'date': r['date'], 'description': r['description'],
                            'amount': r['amount'], 'is_credit': r.get('is_credit', False),
                            'category': item.get('category', 'Others'),
                            'subcategory': item.get('subcategory', r.get('merchant', 'Unknown')),
                            'merchant': item.get('merchant', r.get('merchant', 'Unknown')),
                            'source': 'LLM', 'confidence': 85.0})
            except Exception as e:
                print(f"LLM batch error: {e}")
                for r in batch:
                    all_results.append({
                        '_idx': r['index'], 'date': r['date'], 'description': r['description'],
                        'amount': r['amount'], 'is_credit': r.get('is_credit', False),
                        'category': 'Others', 'subcategory': r.get('merchant', 'Unknown'),
                        'merchant': r.get('merchant', 'Unknown'), 'source': 'Fallback', 'confidence': 0})
        
        return all_results

    # ============================================================
    # SELF-TRAINING
    # ============================================================
    def _save_learned_data(self, llm_results: list):
        if not llm_results:
            return
        base = os.path.dirname(__file__)
        learned_path = os.path.join(base, '..', 'data', 'spend_categories_learned.csv')
        training_path = os.path.join(base, '..', 'data', 'spend_categories_training.csv')
        
        new_rows = pd.DataFrame([{
            'description': r['description'], 'amount': r['amount'],
            'category': r['category'], 'subcategory': r['subcategory'],
            'merchant': r['merchant'], 'source': 'LLM_SelfLearned'
        } for r in llm_results if r.get('category') != 'Others'])
        
        if new_rows.empty:
            return
        try:
            existing = pd.read_csv(learned_path) if os.path.exists(learned_path) else pd.DataFrame()
            combined = pd.concat([existing, new_rows], ignore_index=True)
            combined.to_csv(learned_path, index=False)
            print(f"✅ Self-Training: {len(new_rows)} rows → {learned_path}")
        except Exception as e:
            print(f"⚠️ Save error: {e}")
        
        try:
            if os.path.exists(training_path):
                master = pd.read_csv(training_path)
                master = pd.concat([master, new_rows[['description', 'amount', 'category', 'subcategory', 'merchant']]], ignore_index=True)
                master.to_csv(training_path, index=False)
        except:
            pass

    # ============================================================
    # REPORT BUILDER
    # ============================================================
    def _build_report(self, results: list, kw_count: int, ml_count: int, llm_count: int) -> Dict[str, Any]:
        if not results:
            return {"error": "No transactions categorized"}
        
        df = pd.DataFrame(results)
        
        categories = {}
        for cat in sorted(df['category'].unique()):
            cat_df = df[df['category'] == cat]
            subcategories = {}
            for sub in cat_df['subcategory'].unique():
                sub_df = cat_df[cat_df['subcategory'] == sub]
                merchants = {}
                for merch in sub_df['merchant'].unique():
                    merch_df = sub_df[sub_df['merchant'] == merch]
                    merchants[merch] = {
                        'total': round(float(merch_df['amount'].sum()), 2),
                        'count': int(len(merch_df)),
                        'avg': round(float(merch_df['amount'].mean()), 2),
                        'is_credit': bool(merch_df['is_credit'].any())
                    }
                subcategories[sub] = {
                    'total': round(float(sub_df['amount'].sum()), 2),
                    'count': int(len(sub_df)),
                    'merchants': dict(sorted(merchants.items(), key=lambda x: x[1]['total'], reverse=True)),
                    'is_credit': bool(sub_df['is_credit'].any())
                }
            
            total = float(cat_df['amount'].sum())
            grand_total = float(df['amount'].sum()) or 1
            categories[cat] = {
                'total': round(total, 2),
                'count': int(len(cat_df)),
                'percentage': round(total / grand_total * 100, 1),
                'subcategories': dict(sorted(subcategories.items(), key=lambda x: x[1]['total'], reverse=True)),
                'is_credit': bool(cat_df['is_credit'].any())
            }
        
        categories = dict(sorted(categories.items(), key=lambda x: x[1]['total'], reverse=True))
        
        friends_sent = {}
        friends_received = {}
        for _, row in df.iterrows():
            if row['category'] == 'Friends (Sent)':
                friends_sent[row['merchant']] = friends_sent.get(row['merchant'], 0) + row['amount']
            elif row['category'] == 'Friends (Received)':
                friends_received[row['merchant']] = friends_received.get(row['merchant'], 0) + row['amount']
        friends_sent = {k: round(v, 2) for k, v in sorted(friends_sent.items(), key=lambda x: x[1], reverse=True)}
        friends_received = {k: round(v, 2) for k, v in sorted(friends_received.items(), key=lambda x: x[1], reverse=True)}
        
        merchant_totals = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(20)
        top_merchants = [{'name': n, 'total': round(float(t), 2)} for n, t in merchant_totals.items()]
        
        total_count = kw_count + ml_count + llm_count or 1
        
        return {
            'total_transactions': int(len(df)),
            'total_spent': round(float(df[~df['is_credit']]['amount'].sum()), 2),
            'total_received': round(float(df[df['is_credit']]['amount'].sum()), 2),
            'categories': categories,
            'friends_sent': friends_sent,
            'friends_received': friends_received,
            'top_merchants': top_merchants,
            'ml_stats': {
                'keyword_classified': kw_count,
                'ml_classified': ml_count,
                'llm_classified': llm_count,
                'total': total_count,
                'keyword_percentage': round(kw_count / total_count * 100, 1),
                'ml_percentage': round(ml_count / total_count * 100, 1),
                'llm_percentage': round(llm_count / total_count * 100, 1),
            },
            'transaction_count': int(len(results))
        }
