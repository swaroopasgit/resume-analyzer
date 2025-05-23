from flask import Flask, request, render_template
import pdfplumber
import re

app = Flask(__name__)

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    file = request.files['resume']
    text = extract_text_from_pdf(file)
    role = request.form.get('role')
    score, feedback = simple_score(text, role)
    keywords = ["Python", "Java", "SQL", "Docker", "AWS", "React", "Kubernetes"]
    highlighted_text = highlight_text(text, keywords, "highlight-good")
    return render_template('result.html', score=score, feedback=feedback, resume_text=highlighted_text)


def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())


def simple_score(text, role=None):
    score = 0
    feedback = {
        "Skills": [],
        "Contact Info": [],
        "Content": [],
        "Structure": [],
    }

    keywords = {
        "Python": 10,
        "Java": 8,
        "SQL": 6,
        "Docker": 5,
        "AWS": 7,
        "React": 6,
        "Kubernetes": 7,
    }

    found_skills = 0
    for skill, pts in keywords.items():
        if re.search(rf"\b{skill}\b", text, re.I):
            score += pts
            found_skills += 1
    if found_skills == len(keywords):
        feedback["Skills"].append({
            "message": "Great! All relevant skills are present.",
            "status": "good"
        })
    else:
        for skill in keywords:
            if not re.search(rf"\b{skill}\b", text, re.I):
                feedback["Skills"].append({
                    "message": f"Consider adding {skill} if applicable.",
                    "status": "improve"
                })

    contact_score = 0
    if re.search(r"\b[\w.-]+@[\w.-]+\.\w{2,4}\b", text):
        contact_score += 3
    else:
        feedback["Contact Info"].append({
            "message": "Missing a valid email address.",
            "status": "improve"
        })
    if re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text):
        contact_score += 3
    else:
        feedback["Contact Info"].append({
            "message": "Missing a valid phone number.",
            "status": "improve"
        })
    if contact_score == 6:
        feedback["Contact Info"].append({
            "message": "Looks good!",
            "status": "good"
        })
    score += contact_score

    word_count = len(text.split())
    if word_count < 300:
        feedback["Content"].append({
            "message": "Resume is short; add more achievements or details.",
            "status": "improve"
        })
    elif word_count > 1000:
        feedback["Content"].append({
            "message": "Too long — consider shortening it.",
            "status": "improve"
        })
    else:
        feedback["Content"].append({
            "message": "Looks good!",
            "status": "good"
        })
        score += 5

    if "Objective" not in text and "Summary" not in text:
        feedback["Structure"].append({
            "message": "Add a short summary or objective section.",
            "status": "improve"
        })
    else:
        feedback["Structure"].append({
            "message": "Looks good!",
            "status": "good"
        })
        score += 5

    return min(score, 100), feedback


def highlight_text(text, keywords, highlight_class="highlight-good"):
    for kw in keywords:
        # Regex pattern to match whole words case-insensitive
        pattern = re.compile(rf"\b({re.escape(kw)})\b", re.IGNORECASE)
        # Replace matched keywords with a span wrapping for highlighting
        text = pattern.sub(rf'<span class="{highlight_class}">\1</span>', text)
    return text


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
