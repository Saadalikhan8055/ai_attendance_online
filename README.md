
# AI Attendance Online

AI Attendance Online is a **web-based student attendance management system** that uses **face recognition** to automatically mark attendance.  
The project is built with a **Flask backend** and a **simple, modern frontend**, making it easy to use for students, teachers, and administrators.


## 🚀 Features
- 🔐 **Face Recognition** – Secure and automatic student identification  
- 📊 **Attendance Reports** – View and export daily/monthly attendance  
- 👨‍🏫 **Role Management** – Admin, Teacher, and Student dashboards  
- 🖥️ **Web-Based** – Access from any device with internet  
- ⚡ **Fast & Lightweight** – Built with Flask for smooth performance  


## 🛠️ Tech Stack
- **Backend:** Flask (Python)  
- **Frontend:** HTML, CSS, JavaScript (can extend with React/Bootstrap)  
- **Database:** SQLite / MySQL  
- **AI/ML:** OpenCV, face-recognition library  


## 📂 Project Structure

ai_attendance_online/ 
│── app/                # Flask application │  
├── static/         # CSS, JS, Images │
├── templates/      # HTML templates │ 
├── routes.py       # Flask routes │  
├── models.py       # Database models │ 
└──  │── dataset/     # Training images 
      │── requirements.txt    # Dependencies 
│── run.py              # Main entry point 
│── README.md           # Documentation


## ⚙️ Installation & Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/Saadalikhan8055/ai_attendance_online.git
   cd ai_attendance_online

2. Create virtual environment (optional but recommended)

python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows


3. Install dependencies

pip install -r requirements.txt


4. Run the application

python run.py

Open your browser at http://127.0.0.1:5000/




---

📸 How It Works

1. Admin/Teacher uploads student images for training


2. System trains face recognition model


3. Students are recognized via webcam/live feed


4. Attendance is marked automatically and stored in the database




---

📊 Future Enhancements

📱 Mobile app integration

📧 Email/SMS notifications for absentees

📈 Advanced analytics with charts & insights

🔗 Integration with LMS/ERP systems



---

🤝 Contributing

Contributions are welcome! Feel free to fork this repo, raise issues, or submit PRs.


---

📜 License

This project is licensed under the MIT License.


---

👨‍💻 Author

Saad Ali Khan
AI & ML Engineer | Passionate about building intelligent systems 🚀