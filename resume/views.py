from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect, HttpResponse
from .models import Profile, Experience
from .forms import ResumeUploadForm
import os
import PyPDF2
import docx
import re
import spacy
from datetime import datetime

nlp = spacy.load('en_core_web_sm')

EMAIL_REGEX = r'[\w\.-]+@[\w\.-]+\.\w+'
PHONE_REGEX = r'(\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
GRADUATION_REGEX = r'(?:Graduation\s+Date|Graduated|Completion)\s*:\s*(\w+\s+\d{4}|\d{4})'
UNIVERSITY_REGEX = r'([A-Z][a-zA-Z]+)\s(University|Institute|College)'
EXPERIENCE_REGEX = r'(?:Professional\s+Experience|Work\s+Experience|Employment\s+History|Experience)(.+?)(?:Skills|Projects|$)'
EXPERIENCE_DETAILS_REGEX = r'•\s*(?P<position>[A-Za-z\s]+)\n(?P<company>[A-Z][a-zA-Z\s]+),?\s*(?P<start_date>\w+\s+\d{4})\s*-\s*(?P<end_date>\w+\s+\d{4}|Present)'


def home(request):
    profile = Profile.objects.first()
    return redirect('upload_resume')


def resume_detail(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    experiences = profile.experience_set.all()

    for exp in experiences:
        exp.description = exp.description.split('\n')

    context = {
        'profile': profile,
        'experiences': experiences,
    }
    return render(request, 'resume/resume_detail.html', context)


def upload_resume(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = request.FILES['resume_file']
            resume_data = process_resume(resume_file)

            profile = Profile.objects.create(
                name=resume_data['name'],
                email=resume_data['email'],
                phone=resume_data['phone'],
                summary=resume_data['summary'],
                university=resume_data['university'],
                graduation_date=resume_data['graduation_date']
            )

            for experience_data in resume_data['experiences']:
                Experience.objects.create(
                    profile=profile,
                    position=experience_data['position'],
                    company=experience_data['company'],
                    start_date=experience_data['start_date'],
                    end_date=experience_data['end_date'],
                    description="\n".join(experience_data['description'])
                )

            return redirect('resume_detail', profile_id=profile.id)
    else:
        form = ResumeUploadForm()

    return render(request, 'resume/upload_resume.html', {'form': form})


def process_resume(resume_file):
    file_ext = os.path.splitext(resume_file.name)[1].lower()

    if file_ext == '.pdf':
        return extract_pdf_info(resume_file)
    elif file_ext == '.docx':
        return extract_docx_info(resume_file)
    else:
        raise ValueError("Unsupported file format")


def extract_pdf_info(resume_file):
    reader = PyPDF2.PdfReader(resume_file)
    text = "".join([page.extract_text() for page in reader.pages])
    return extract_resume_data(text)


def extract_docx_info(resume_file):
    doc = docx.Document(resume_file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return extract_resume_data(text)


def extract_resume_data(text):
    email = re.search(EMAIL_REGEX, text)
    email = email.group(0) if email else "Not found"

    phone = re.search(PHONE_REGEX, text)
    phone = phone.group(0) if phone else "Not found"

    doc = nlp(text)
    name = next((ent.text for ent in doc.ents if ent.label_ == 'PERSON'), "Not found")

    university = re.search(UNIVERSITY_REGEX, text)
    university = university.group(0) if university else "Not found"

    graduation_date = re.search(GRADUATION_REGEX, text)
    graduation_date = graduation_date.group(1) if graduation_date else "Not found"

    experiences = extract_experiences(text)
    summary = text[:500]

    return {
        'name': name,
        'email': email,
        'phone': phone,
        'university': university,
        'graduation_date': graduation_date,
        'experiences': experiences,
        'summary': summary
    }


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%B %Y').strftime('%Y-%m-01')
    except ValueError:
        return None


def extract_experiences(text):
    experience_section = re.search(EXPERIENCE_REGEX, text, re.DOTALL)
    if not experience_section:
        return []

    experience_text = experience_section.group(1).strip()
    experiences = []

    matches = list(re.finditer(EXPERIENCE_DETAILS_REGEX, experience_text, re.MULTILINE))

    for i, match in enumerate(matches):
        position = match.group("position").strip()
        company = match.group("company").strip()
        start_date_str = match.group("start_date").strip()
        end_date_str = match.group("end_date").strip() if match.group("end_date") else "Present"

        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str) if end_date_str != "Present" else None

        description_start = match.end()
        description_end = matches[i + 1].start() if i + 1 < len(matches) else len(experience_text)
        description = experience_text[description_start:description_end].strip()

        description = [line.strip() for line in re.split(r'[•–\n]', description) if line.strip()]

        experiences.append({
            'position': position,
            'company': company,
            'start_date': start_date,
            'end_date': end_date,
            'description': description
        })

    return experiences
