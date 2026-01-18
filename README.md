# SafeCampus  
## A Safe Environment & Gender Support Portal

SafeCampus is a **Django-based, production-ready web application** designed to provide a **secure, anonymous, and trustworthy platform** for reporting harassment, bullying, stalking, and safety-related incidents across **schools, colleges, universities, and workplaces**.

The platform focuses on **privacy, institutional accountability, and gender safety**, and directly aligns with **UN SDG 5 – Gender Equality**.

---

## 🌐 Live Deployment

🚀 **Live Website:** *(Deployed on Render)*  
🔗 **Live Link:** <YOUR_RENDER_LINK_HERE>

> ⚠️ **Important Note:**  
> This application is deployed on **Render (free tier)**.  
> When you click the live link for the first time, **please wait 2–3 minutes** for the Render server to wake up before the website loads.  
> This delay is normal for free deployments.

---

## 📌 Problem Statement

Despite growing awareness around gender equality, incidents of harassment, stalking, bullying, and unsafe environments continue to affect girls and women across educational institutions and corporate offices.

Many victims hesitate to report incidents due to:
- Fear of exposure or retaliation  
- Lack of trust in internal reporting systems  
- Social stigma  
- Unclear reporting and follow-up mechanisms  

Existing systems are often:
- Manual and slow  
- Lacking confidentiality and anonymity  
- Poorly structured for analytics and prevention  
- Reactive rather than preventive  

As a result, victims remain unsupported and institutions fail to identify unsafe locations and recurring risk patterns.

This problem directly aligns with **UN SDG 5 – Gender Equality**, specifically **Target 5.2**, which aims to eliminate all forms of violence and harassment against women and girls in public and private spaces.

---

## 💡 Solution Overview

SafeCampus provides a **secure, digital, and anonymous incident reporting ecosystem** that empowers girls and women while enabling institutions to take **data-driven preventive actions**.

### Core Capabilities:
- Anonymous or identified incident reporting  
- Secure evidence uploads  
- Transparent case tracking  
- In-app communication with counsellors  
- Admin analytics and safety hotspot detection  
- Basic ML-driven insights for prioritization and misuse prevention  

SafeCampus focuses on **trust, privacy, and accountability**, rather than social interaction.

---

## 🎯 Objectives

- Provide a safe and anonymous reporting platform  
- Ensure confidentiality and victim protection  
- Enable structured case management and follow-up  
- Identify unsafe locations and recurring behavioral patterns  
- Support institutional accountability  
- Promote awareness of legal rights and support resources  

---

## 👥 User Roles & Access Control

### 1️⃣ Student / Employee (Primary Focus: Girls & Women)
- Secure authentication  
- Raise complaints (anonymous or non-anonymous)  
- Upload evidence (PDF, DOCX, images, audio, video)  
- Track complaint status  
- In-app communication with counsellors (if non-anonymous)  

### 2️⃣ Counsellor
- View and manage assigned cases  
- Update case status  
- Communicate securely with complainants  
- Add internal resolution notes  

### 3️⃣ Security Staff
- View safety-related and location-based incidents  
- Assist in case resolution (limited access)  

### 4️⃣ Admin
- Full system access  
- Assign cases to counsellors or security staff  
- Manage users, locations, and incident categories  
- View analytics dashboards and ML insights  

---

## 📝 Incident Reporting System

### Step-by-Step Reporting Flow:
1. Incident Type  
2. Location  
3. Date & Time  
4. Title & Detailed Description  
5. Evidence Upload (multiple formats)  
6. Anonymity Toggle  

### 🔐 Anonymity Logic:
- If **anonymous** → reporter identity is not stored  
- If **not anonymous** → identity visible only to authorized staff  
- **Anonymity cannot be overridden**, even by admin  

### After Submission:
- Unique reference code generation  
- Confirmation screen  
- Context-aware helpline numbers displayed with the message:  

> *“If you don’t feel safe at any moment, you can contact these services anytime.”*

---

## 🔄 Case Management & Communication

### Case Status Flow:
- New → Under Review → In Contact → Resolved / Closed  

### Features:
- Secure in-app messaging  
- Internal notes (visible only to counsellor & admin)  
- Complete audit trail of status changes  

---

## 📚 Safety Resources & Awareness

Dedicated **Resources & Support** section includes:
- POSH / ICC policies  
- Legal rights and protections  
- Emergency and counselling contacts  
- Self-help guides and FAQs  

### SDG-5 Awareness Page:
- Gender equality goals  
- Violence prevention  
- How SafeCampus contributes  

---

## 📊 Admin Analytics Dashboard

The dashboard provides insights such as:
- Incident count by type  
- Incident count by location  
- Monthly trend analysis  
- Status distribution  
- Identification of safety hotspots  

These insights help institutions take **preventive and proactive actions**, not just reactive measures.

---

## 🤖 Machine Learning Integration (Basic)

### 1️⃣ Unsafe Location Detection
- Frequency analysis of incidents by location  
- Identification of emerging risk zones  

### 2️⃣ Text Sentiment Analysis
- Emotional tone analysis of complaint descriptions  
- Flagging high-distress or urgent cases  

### 3️⃣ Fake / Spam Complaint Detection
- Detection of repeated patterns or low-content submissions  
- Reduces misuse while protecting genuine complaints  

> ⚠️ *For the current development timeline, ML is implemented using rule-based logic or pre-trained models, with scope for future enhancement.*

---

## 🏗️ System Architecture (High-Level)

- **Frontend:** Django Templates + Tailwind CSS  
- **Backend:** Django (Class-Based Views)  
- **ML Layer:** Python (scikit-learn / NLP utilities)  
- **Database:** PostgreSQL  
- **Media Storage:** Local (scalable to cloud)  
- **Authentication:** Django Auth + Role-Based Access Control  

---

## 🧰 Technology Stack

### Frontend
- HTML5  
- Tailwind CSS  
- Minimal JavaScript  
- Chart.js  

### Backend
- Django 4+  
- Django ORM  
- Django Forms & CBVs  

### Database
- PostgreSQL  

**Why PostgreSQL?**
- Strong relational data handling  
- ACID compliance (critical for safety/legal data)  
- Better analytics and reporting  
- Native Django support  

### ML & Data Processing
- Python  
- scikit-learn  
- NLP utilities  

---

## 🌍 SDG Mapping

### SDG 5 – Gender Equality  
**Target 5.2:** Eliminate all forms of violence and harassment against women and girls in public and private spaces.

### How SafeCampus Supports SDG 5:
- Safe and anonymous reporting  
- Early detection of unsafe environments  
- Institutional accountability  
- Awareness of rights and support systems  

---

## 🚀 Future Scope

- Mobile application (Android / iOS)  
- Real-time emergency alerts  
- Advanced ML-based risk prediction  
- GIS-based safety heatmaps  
- Integration with government and NGO helplines  
- Multi-language support  

---

## 🧑‍💻 Setup & Installation

```bash
# Clone the repository
git clone <repository-url>
cd safecampus

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run the server
python manage.py runserver
