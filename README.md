# 📊 Automatic Sales Report System

Yeh ek Streamlit web app hai jo automatically sales reports generate karti hai.

## Features
- 🏠 Dashboard with charts
- 📝 Data Entry (CSV upload + manual entry)
- 📊 PDF Report generation with charts
- 📥 Download report directly from browser

## Streamlit Cloud pe Deploy Karne ke Steps

### Step 1 – GitHub pe upload karein
```
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/AAPKA_USERNAME/sales-report-system.git
git push -u origin main
```

### Step 2 – Streamlit Cloud pe jayein
1. **https://share.streamlit.io** pe jaayein
2. Google/GitHub se login karein
3. **"New app"** button dabaayein
4. Apna GitHub repo select karein
5. **Main file path:** `app.py`
6. **Deploy!** click karein

App kuch minutes mein live ho jaayegi! 🎉

## Local chalane ke liye
```bash
pip install -r requirements.txt
streamlit run app.py
```
