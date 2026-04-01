import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import random
from PyPDF2 import PdfReader, PdfWriter

def create_statement(filename, title, account_name, transactions, password=""):
    os.makedirs('data/sample_statements', exist_ok=True)
    filepath = f"data/sample_statements/unencrypted_{filename}"
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Header helper
    def draw_header():
        c.setFont("Helvetica-Bold", 18)
        c.setFillColorRGB(0.0, 0.2, 0.6) # HDFC Blue
        c.drawString(40, 750, "HDFC BANK")
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 735, "We understand your world")
        c.setFont("Helvetica", 9)
        c.drawString(40, 715, "Statement of account From : 01/04/2025 To : 27/03/2026")
        c.drawString(40, 700, f"Name: {account_name}")
        c.drawString(40, 685, f"Account No: 50100XXXXXXXX839")
        c.drawString(40, 670, f"Branch: ANDHERI WEST, MUMBAI")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 640, title)
        
        # Table Header - Authentic 7-Column Layout
        c.setFont("Helvetica-Bold", 8)
        c.drawString(40, 610, "Date")
        c.drawString(90, 610, "Narration")
        c.drawString(260, 610, "Chq./Ref.No.")
        c.drawString(330, 610, "Value Dt")
        c.drawString(380, 610, "Withdrawal Amt.")
        c.drawString(460, 610, "Deposit Amt.")
        c.drawString(530, 610, "Closing Balance")
        c.line(40, 600, 600, 600)
        return 580

    y = draw_header()
    c.setFont("Helvetica", 8)
    
    balance = 500000.00 # Starting with a 5L baseline to avoid negative debts
    
    # Sort transactions by date (which is in YYYY-MM-DD HH:MM string format so it alphabetizes correctly)
    transactions.sort(key=lambda x: x[0])
    
    for t in transactions:
        # Convert Kaggle-style "YYYY-MM-DD HH:MM" to "DD/MM/YY"
        date_obj = datetime.strptime(t[0], "%Y-%m-%d %H:%M")
        date_str = date_obj.strftime("%d/%m/%y")
        desc = t[1]
        debit = t[2]
        credit = t[3]
        
        # Sequentially modify the closing balance
        if debit: balance -= debit
        if credit: balance += credit
        
        # Add transaction 7-column row mapping
        c.drawString(40, y, f"{date_str}")
        c.drawString(90, y, f"{desc[:30]}")
        c.drawString(260, y, f"0000102{random.randint(10000, 99999)}")
        c.drawString(330, y, f"{date_str}")
        
        if debit:
            c.drawString(380, y, f"{debit:,.2f}")
        if credit:
            c.drawString(460, y, f"{credit:,.2f}")
            
        c.drawString(530, y, f"{balance:,.2f}")
        
        y -= 15
        if y < 50:  # Page break
            c.showPage()
            y = draw_header()
            c.setFont("Helvetica", 8)
            
    # HDFC Authentic Footer
    y -= 10
    c.line(40, y, 600, y)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(330, y - 20, "Total Closing Balance:")
    c.drawString(530, y - 20, f"{balance:,.2f}")
    
    c.save()
    
    # Apply PDF Password Encryption to mimic real banking PDF lock
    final_filepath = f"data/sample_statements/{filename}"
    
    reader = PdfReader(filepath)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
        
    writer.encrypt(password)
    with open(final_filepath, "wb") as f:
        writer.write(f)
        
    # Clean up unencrypted temp file
    os.remove(filepath)
    print(f"Generated Encrypted HDFC Statement: {final_filepath} with {len(transactions)} transactions.")

def generate_noise(start_date, num_tx):
    noise = []
    vendors = [
        ("UPI: Swiggy Instamart", 50, 300),
        ("UPI: Zomato Limited", 100, 400),
        ("UPI: Amazon Pay", 100, 1000),
        ("UPI: Local Chaiwala", 20, 50),
        ("POS: Shell Petrol", 500, 1500),
        ("UPI: Jio Recharge", 299, 999),
        ("POS: Starbucks", 200, 600),
        ("POS: Apollo Pharmacy", 100, 800),
        ("UPI: UberRides", 100, 500),
        ("UPI: BlinkIt Groceries", 200, 800)
    ]
    curr = start_date
    for i in range(num_tx):
        v = random.choice(vendors)
        amt = random.randint(v[1], v[2])
        # Randomly advance time by 10 to 60 minutes
        curr += timedelta(minutes=random.randint(10, 60))
        # Ensure we don't go way past the FY by doing this, but with 10k transactions * 35 mins approx = roughly 240 days, fits in 1 year.
        noise.append((curr.strftime("%Y-%m-%d %H:%M"), v[0], amt, None))
    return noise

def generate_all():
    start_date = datetime(2025, 4, 1, 8, 0)
    
    print("Generating 10,000+ transactions per file. This will take ~20 seconds...")

    # 1. LOW RISK (10,000 tx)
    tx_low = generate_noise(start_date, 10000)
    # Inject salary on 2nd of each month
    curr_month = 4
    curr_year = 2025
    for _ in range(12):
        tx_low.append((datetime(curr_year, curr_month, 2, 8, 0).strftime("%Y-%m-%d %H:%M"), "NEFT: TECHCORP SOLUTIONS (SALARY)", None, 250000))
        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1
    create_statement("HDFC_stmt_01_low_risk.pdf", "LOW RISK PROFILE", "Rahul Sharma", tx_low, "294927964")
    
    # 2. MEDIUM RISK
    tx_med = generate_noise(start_date, 10000)
    curr_month = 4
    curr_year = 2025
    for _ in range(12):
        tx_med.append((datetime(curr_year, curr_month, 2, 8, 0).strftime("%Y-%m-%d %H:%M"), "NEFT: TECHCORP SOLUTIONS (SALARY)", None, 250000))
        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1
    tx_med.append(("2025-06-15 14:30", "CASH DEPOSIT - BRANCH 492", None, 350000))
    tx_med.append(("2025-09-22 10:15", "CASH DEPOSIT - ATM", None, 450000))
    create_statement("HDFC_stmt_02_medium_risk.pdf", "MEDIUM RISK PROFILE", "Priya Patel", tx_med, "294927964")
    
    # 3. HIGH RISK (Smurfing pattern deeply hidden in 10k noise)
    tx_high = generate_noise(start_date, 10000)
    smurf_date = datetime(2025, 5, 1, 10, 0)
    for _ in range(25): # 25 days of 49.9k cash randomly seeded
        tx_high.append((smurf_date.strftime("%Y-%m-%d %H:%M"), "CASH DEPOSIT - SELF", None, 49900))
        smurf_date += timedelta(days=1, hours=3)
    tx_high.append(("2025-06-05 11:00", "IMPS: WAZIRX CRYPTO EXCHANGE", 800000, None))
    tx_high.append(("2025-06-15 13:00", "IMPS: WAZIRX CRYPTO EXCHANGE", 300000, None))
    create_statement("HDFC_stmt_03_high_risk.pdf", "HIGH RISK (SMURFING)", "Amit Kumar", tx_high, "294927964")
    
    # 4. CRITICAL RISK 
    tx_crit = generate_noise(start_date, 10000)
    tx_crit.extend([
        ("2025-04-10 09:00", "SWIFT IN: OFFSHORE HOLDINGS CAYMAN", None, 85000000), # 8.5 Cr
        ("2025-04-12 11:30", "RTGS: LUXURY MOTORS DUBAI", 65000000, None), # Out
        ("2025-05-01 14:00", "CASH WITHDRAWAL - SELF", 5000000, None),
        ("2025-06-01 15:45", "CASH WITHDRAWAL - SELF", 2500000, None),
        ("2025-07-01 10:10", "NEFT: SHELL CORP SERVICES LTD", 400000, None)
    ])
    create_statement("HDFC_stmt_04_critical_risk.pdf", "CRITICAL RISK (LAUNDERING)", "Vikram Singh (HUF)", tx_crit, "294927964")

if __name__ == "__main__":
    generate_all()
