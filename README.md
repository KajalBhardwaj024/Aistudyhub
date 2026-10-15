# AI StudyHub

An AI-powered study platform where students upload notes as PDFs and get automatic subject detection, quiz generation, leaderboards, performance analytics and ML-based performance prediction.

Built as an M.Sc. (Data Science & Machine Learning) project at MDU Rohtak.

## Features
- User registration and login with session management
- PDF notes upload with automatic text extraction (PyPDF2)
- Keyword-based subject detection
- Automatic multiple-choice quiz generation from uploaded notes
- Subject-wise leaderboard
- Performance analytics dashboard
- Student performance prediction using Random Forest (scikit-learn)
- Chatbot built on a GPT-2 text-generation pipeline

## Tech Stack
Python, Flask, SQLite, SQLAlchemy, Pandas, scikit-learn, PyPDF2, Hugging Face Transformers, HTML/CSS

## Getting Started
```bash
git clone https://github.com/KajalBhardwaj024/Aistudyhub.git
cd Aistudyhub
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 in your browser. The first run downloads the GPT-2 model, so it may take a few minutes.

## Project Structure
- `app.py`: Flask routes, database models, quiz and ML logic
- `templates/`: HTML pages
- `StudentsPerformance.csv`, `student_courses.csv`: datasets for the prediction module

## Future Scope
Support for DOCX/PPT files, cloud database, improved NLP-based subject detection, adaptive learning and mobile support.