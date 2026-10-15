from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.utils import secure_filename
import os
from sqlalchemy import func
from transformers import pipeline
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import random
import re
quiz_questions=[]
current_index=0
total_score=0
notes_text = ""
subject_name="General"
app = Flask(__name__)
app.secret_key = "studyhub_secret"
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studyhub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
chatbot = pipeline(
    "text-generation",
    model="gpt2"
)
# ================= ML Dataset =================

data = pd.read_csv(
    "StudentsPerformance.csv"
)

# Average score create
data["average_score"] = (

    data["math score"] +
    data["reading score"] +
    data["writing score"]

)/3


# Performance label

def performance(x):

    if x >= 80:
        return "Excellent"

    elif x >= 50:
        return "Good"

    else:
        return "Needs Improvement"


data["Performance"] = data[
    "average_score"
].apply(performance)


# Convert labels into numbers

le = LabelEncoder()

data["Performance"] = le.fit_transform(
    data["Performance"]
)


# Inputs and output

X = data[
    [
        "math score",
        "reading score",
        "writing score"
    ]
]

y = data["Performance"]


# Train ML model

model = RandomForestClassifier()

model.fit(X,y)

# User table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Leaderboard(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    email = db.Column(
        db.String(100),
        nullable=False
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    __table_args__ = (

        db.UniqueConstraint(
            'email',
            'subject',
            name='unique_user_subject'
        ),

    )
def detect_subject(text):

    text = text.lower()

    if (
        "machine learning" in text
        or "random forest" in text
        or "algorithm" in text
        or "neural" in text
    ):

        return "Machine Learning"


    elif (

        "photosynthesis" in text
        or "cell" in text
        or "biology" in text
        or "science" in text
    ):

        return "Science"


    elif (

        "database" in text
        or "sql" in text
        or "table" in text
    ):

        return "Database"


    elif (

        "python" in text
        or "flask" in text
        or "programming" in text
    ):

        return "Programming"


    else:

        return "General"
    
class Notes(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_email = db.Column(
        db.String(100)
    )

    file_name = db.Column(
        db.String(200)
    )

    subject = db.Column(
        db.String(100)
    )

    file_path = db.Column(
        db.String(300)
    )
class Score(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_email = db.Column(
        db.String(100)
    )

    marks = db.Column(
        db.Integer
    )

# Login page
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        if user:

            session["email"]=email

            return redirect(

                url_for(
                    "dashboard"
                )

    )
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    user_notes = Notes.query.filter_by(

        user_email=session["email"]

    ).group_by(

    Notes.file_name
    ).all()

    return render_template(

        "dashboard.html",

        email=session["email"],

        notes=user_notes

    )
# Signup page
@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        new_user = User(
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/upload", methods=["GET","POST"])
def upload():

    global notes_text
    if request.method=="GET":

        if session.get(
            "opened_note",
            False
        ):

            session.pop(
                "opened_note"
            )

        else:

            notes_text=""

    extracted_text=""

    if request.method=="POST":

        file=request.files["note"]

        if file:

            filename=secure_filename(
                file.filename
            )

            filepath=os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            import PyPDF2

            with open(filepath,"rb") as pdf_file:

                reader=PyPDF2.PdfReader(pdf_file)

                for page in reader.pages:

                    text = page.extract_text()

                    if text:
                        extracted_text += text

            notes_text = extracted_text
            global subject_name

            subject_name = detect_subject(
                notes_text
            )

            print(
                "Detected Subject:",
                subject_name
            )
            existing_note = Notes.query.filter_by(

                user_email=session["email"],
                file_name=filename

            ).first()


            if not existing_note:

                saved_note = Notes(

                user_email=session["email"],
                file_name=filename,
                subject=subject_name,
                file_path=filepath

            )

                db.session.add(
                    saved_note
                )

                db.session.commit()
            
    return render_template(

        "upload.html",

        email=session["email"],

        subject=subject_name,

        extracted_text=notes_text[:1000]

    )
@app.route("/quiz", methods=["GET","POST"])
def quiz():

    global notes_text
    global quiz_questions
    global current_index
    global total_score

    # Generate quiz only once
    if not quiz_questions:

        import re
        quiz_questions=[]

        # Split notes into sentences
        sentences = re.split(r'[.!?]', notes_text)

        # Extract meaningful words
        keywords=[]

        for s in sentences:

            words=s.split()

            for w in words:

                w=w.strip(".,()[]{}:;")

                if len(w)>4 and w.isalpha():

                    keywords.append(
                        w
                    )

        # remove duplicates
        keywords=list(
            set(keywords)
        )

        for sentence in sentences:

            sentence=sentence.strip()

            words=sentence.split()

            if len(words)>6:

                # find candidate words from this sentence
                candidates=[]

                for w in words:

                    clean=w.strip(
                        ".,()[]{}:;"
                    )

                    if clean in keywords:

                        candidates.append(
                            clean
                        )

                if len(candidates)>0:

                    # correct answer
                    correct=random.choice(
                        candidates
                    )

                    question=sentence.replace(
                        correct,
                        "_____",
                        1
                    )

                    # wrong options
                    wrong_pool=[
                        x for x in keywords
                        if x!=correct
                    ]

                    if len(wrong_pool)>=3:

                        wrong=random.sample(
                            wrong_pool,
                            3
                        )

                    else:
                        continue

                    options=[
                        correct
                    ] + wrong

                    random.shuffle(
                        options
                    )

                    quiz_questions.append({

                        "question":question,
                        "answer":correct,
                        "options":options
                    })

            if len(
                quiz_questions
            )>=10:

                break

    # Check answer
    if request.method=="POST":

        if current_index < len(
            quiz_questions
        ):

            user_answer=request.form.get(
                "answer"
            )

            if user_answer:

                correct=quiz_questions[
                    current_index
                ]["answer"]

                if user_answer==correct:

                    total_score+=1

            current_index+=1
    # Final result
    if current_index >= len(
        quiz_questions
    ):
  
        score = total_score


        existing = Leaderboard.query.filter_by(

            email=session["email"],
            subject=subject_name

        ).first()


        if existing:

            existing.score = score

        else:

            db.session.add(

                Leaderboard(

                    email=session["email"],
                    subject=subject_name,
                    score=score

                )

            )


        score_entry = Score(

            user_email=session["email"],
            marks=score

        )

        db.session.add(
            score_entry
        )

        db.session.commit()


        quiz_questions = []
        current_index = 0
        total_score = 0


        return render_template(
            "result.html",
            score=score
        )


    current=quiz_questions[
        current_index
    ]

    return render_template(
        "quiz.html",
        question=current[
            "question"
        ],
        options=current[
            "options"
        ]
    )
   

@app.route("/open_note/<int:id>")
def open_note(id):

    global notes_text
    global subject_name

    note = Notes.query.get(id)

    if note:

        import PyPDF2

        with open(
            note.file_path,
            "rb"
        ) as pdf_file:

            reader = PyPDF2.PdfReader(
                pdf_file
            )

            extracted=""

            for page in reader.pages:

                text=page.extract_text()

                if text:

                    extracted += text

        notes_text = extracted

        subject_name = note.subject
    session["opened_note"] = True
    return redirect(
          "/upload"
    )
@app.route("/leaderboard")
def leaderboard():

    subject = globals().get(
        "subject_name",
        "General"
    )

    data = Leaderboard.query.filter_by(

        subject=subject

    ).order_by(

        Leaderboard.score.desc()

    ).all()

    return render_template(

        "leaderboard.html",

        leaderboard=data,

        subject=subject

    )
@app.route("/analytics")
def analytics():

    total_quizzes = Score.query.count()

    total_score = db.session.query(
        func.sum(Score.marks)
    ).scalar()

    if total_score is None:
        total_score = 0

    if total_quizzes > 0:
        average_score = total_score / total_quizzes
    else:
        average_score = 0

    return render_template(
        "analytics.html",
        total_quizzes=total_quizzes,
        total_score=total_score,
        average_score=round(average_score,2)
    )
@app.route("/chatbot", methods=["GET","POST"])
def chatbot_page():

    global notes_text

    answer=""

    if request.method=="POST":

        question=request.form["question"]

        question_words = question.lower().split()

        matching_lines=[]

        lines = notes_text.split("\n")

        for line in lines:

            for word in question_words:

                if word in line.lower():

                    matching_lines.append(line)

        if matching_lines:

            answer = matching_lines[0]

        else:

            answer = "Question not found in uploaded notes."

    return render_template(
        "chatbot.html",
        answer=answer
    )
@app.route("/logout")
def logout():

    session.pop("email",None)

    return redirect(url_for("login"))
@app.route("/profile")
def profile():

    email = session.get("email")

    user = User.query.filter_by(
        email=email
    ).first()

    return render_template(
        "profile.html",
        email=user.email
    )
@app.route(
    "/prediction",
    methods=["GET","POST"]
)
def prediction():

    result=""

    recommendation=""

    if request.method=="POST":

        math = int(
            request.form["math"]
        )

        reading = int(
            request.form["reading"]
        )

        writing = int(
            request.form["writing"]
        )

        prediction = model.predict(
            [[math,reading,writing]]
        )

        result = le.inverse_transform(
            prediction
        )[0]

        if result=="Excellent":

            recommendation="Advanced ML"

        elif result=="Good":

            recommendation="Machine Learning"

        else:

            recommendation="Python Basics"

    return render_template(
        "prediction.html",
        result=result,
        recommendation=recommendation
    )
with app.app_context():

    db.create_all()


if __name__=="__main__":

    app.run(
        debug=True,
        use_reloader=False
    )