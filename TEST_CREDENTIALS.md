# FoodBridge Test Credentials & Chennai Mock Data

## 📍 Chennai Locations Used

All test data uses real Chennai area coordinates for accurate distance testing.

| Area | Latitude | Longitude | Used For |
|------|----------|-----------|----------|
| T.Nagar | 13.0827 | 80.2707 | Anna Daanam Trust (NGO) |
| Mylapore | 13.0339 | 80.2699 | Care & Share Foundation (NGO) |
| Adyar | 13.0012 | 80.2565 | Helping Hands Society (NGO) |
| Anna Nagar | 13.0850 | 80.2101 | Community Kitchen Trust (NGO) |
| Nungambakkam | 13.0418 | 80.2341 | Test NGO |
| Egmore | 13.0792 | 80.2615 | Chennai Grand Hotel (Donor) |
| Besant Nagar | 13.0002 | 80.2668 | South Indian Delights (Donor) |
| Velachery | 12.9815 | 80.2180 | City Bakery (Donor) |
| Marina Beach | 13.0543 | 80.2822 | Marina Restaurant (Donor) |
| Vadapalani | 13.0519 | 80.2121 | Vegetarian Paradise (Donor) |

---

## 🔵 NGO Login Credentials

### Option 1: Test Token (Recommended for testing)
```
Token: fake_token_for_testing
```
This logs you in as "Test NGO" (id=1) for testing purposes.

### Option 2: Verified NGOs (Use with Firebase Auth)

| NGO Name | Email | Location | Distance from T.Nagar |
|----------|-------|----------|----------------------|
| Anna Daanam Trust | anna@example.com | T. Nagar | 0 km |
| Care & Share Foundation | care@example.com | Mylapore | ~4 km |
| Helping Hands Society | helping@example.com | Adyar | ~9 km |
| Community Kitchen Trust | community@example.com | Anna Nagar | ~6 km |
| Test NGO | test@example.com | Nungambakkam | ~5 km |

---

## 🟢 Food Donor Login Credentials

Use **Name + Phone** to login as a food donor:

| Organization Name | Phone | Location | Food Type |
|-------------------|-------|----------|-----------|
| Chennai Grand Hotel | 9876543210 | Egmore | Biryani & Rice (50 servings) |
| South Indian Delights | 9876543211 | Besant Nagar | Idli & Dosa (100 servings) |
| City Bakery | 9876543212 | Velachery | Bread & Pastries (30 loaves) |
| Marina Restaurant | 9876543213 | Marina Beach | Fish Curry & Rice (40 servings) |
| Vegetarian Paradise | 9876543214 | Vadapalani | Sambar & Curd Rice (60 servings) |

---

## 🧪 Testing Flow

### Step 1: Login as Food Donor
1. Go to Food Donor page
2. Enter: `Chennai Grand Hotel` and phone `9876543210`
3. You should see the Donor Dashboard with NGOs sorted by distance

### Step 2: Request an NGO
1. Click "Request NGO" on any NGO card
2. Confirm the popup
3. NGO should move to "Requested NGOs" section

### Step 3: Login as NGO (in another browser/incognito)
1. Go to NGO login page
2. Use test token: `fake_token_for_testing`
3. You should see the pending request from Chennai Grand Hotel

### Step 4: Accept the Request
1. Click "Accept Donation" on the NGO dashboard
2. Request should move to "Accepted Food Donations"
3. Progress tracking steps should appear

### Step 5: Progress Tracking
1. **Step 1 (Donor)**: Donor clicks "Food Packed & Ready"
2. **Step 2-3 (Volunteer)**: Simulated or volunteer clicks
3. **Step 4 (NGO)**: NGO clicks "Confirm Delivery"

---

## 📏 Expected Distances (Chennai)

| From | To | Expected Distance |
|------|-----|-------------------|
| T.Nagar | Mylapore | ~3.8 km |
| T.Nagar | Adyar | ~9.2 km |
| T.Nagar | Anna Nagar | ~6.5 km |
| Egmore | Mylapore | ~4.0 km |
| Egmore | T.Nagar | ~2.5 km |
| Adyar | Anna Nagar | ~10.5 km |

---

## 🔧 Setup Instructions

1. Pull the latest changes:
```bash
git pull origin copilot/fix-foodbridge-project-bugs
```

2. Run the mock data migration (if not already done):
```bash
python add_chennai_mock_data.py
```

3. Start the application:
```bash
python app.py
```

4. Open browser to `http://localhost:5000`

---

## 🧪 Run Automated Tests

```bash
pip install pytest flask flask-cors firebase-admin
python -m pytest tests/test_foodbridge_flow.py -v
```

Expected result: 12 tests passed
