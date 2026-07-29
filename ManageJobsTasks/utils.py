# jobs/utils.py

import os
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from .models import Job
from django.contrib.auth import get_user_model

User = get_user_model()


# Allowed upload types and size cap for job files (images, PDF, Word docs).
ALLOWED_FILE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".doc", ".docx",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file


def validate_job_file(uploaded_file):
    """Validate a single uploaded job file.

    Returns an error message string when the file is invalid, or None when it
    passes. Used by the job create view to reject bad uploads server-side.
    """
    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in ALLOWED_FILE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_FILE_EXTENSIONS))
        return f"File type '{extension or uploaded_file.name}' is not allowed. Allowed types: {allowed}."

    if uploaded_file.size > MAX_FILE_SIZE:
        return f"File '{uploaded_file.name}' exceeds the 10 MB size limit."

    return None


def apply_early_access_window(jobs, request):
    """Freelancer Pro perk: hide jobs younger than EARLY_ACCESS_HOURS from
    non-Pro freelancers and anonymous visitors. Employers/admins and Pro
    freelancers (early_access feature) see everything immediately."""
    from pricing.features import EARLY_ACCESS, has_feature

    user = request.user
    if user.is_authenticated:
        if getattr(user, "role", None) in ("employer", "admin"):
            return jobs
        if has_feature(user, EARLY_ACCESS):
            return jobs
    cutoff = timezone.now() - timedelta(hours=settings.EARLY_ACCESS_HOURS)
    return jobs.filter(created_at__lte=cutoff)


def notify_employer_of_application(application, request=None):
    """Email the employer (HTML) that someone applied to their job.

    Called after a JobApplication is created. Sends a plain-text body with an
    HTML alternative. Failures are swallowed so a mail outage never breaks the
    application flow.

    Links are built from the incoming ``request`` so they point at whatever
    host the app is served from (local, staging, production). The "Review
    application" button deep-links to this job's manage-candidates page. Falls
    back to ``settings.FRONTEND_URL`` when no request is available.
    """
    job = application.job
    employer = job.user
    employer_email = getattr(employer, "email", None)
    if not employer_email:
        return

    subject = f"New application for your job: {job.title}"

    # Path to the employer's candidate-review page for this specific job.
    review_path = reverse("dashboard_manage_candidates", args=[job.id])
    if request is not None:
        site_url = request.build_absolute_uri("/")
        review_url = request.build_absolute_uri(review_path)
    else:
        site_url = settings.FRONTEND_URL
        review_url = settings.FRONTEND_URL.rstrip("/") + review_path

    # Note: the applicant's email is deliberately omitted. It is platform-internal
    # and must never be surfaced to the employer.
    context = {
        "applicant_name": application.name,
        "bid_amount": application.bid_amount,
        "job_title": job.title,
        "applications_count": application.applications_count,
        "link": review_url,
        "site_url": site_url,
    }

    price_line = (
        f"Proposed price: NGN {application.bid_amount}\n"
        if application.bid_amount is not None else ""
    )

    # Plain-text fallback for clients that don't render HTML.
    text_body = (
        f"{application.name} has applied for your job posting \"{job.title}\".\n\n"
        f"Applicant name: {application.name}\n"
        f"{price_line}"
        f"Total applications so far: {application.applications_count}\n\n"
        f"Review the application here: {review_url}\n\n"
        f"One Million Jobs"
    )

    try:
        html_body = render_to_string("emails/job_application_notification.html", context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[employer_email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=True)
    except Exception as e:
        # Don't let an email error surface to the applicant.
        print(f"Failed to send employer application email: {e}")


def notify_employer_of_bid(bid, request=None):
    """Email the employer (HTML) that a freelancer bid on their task.

    Called after a TaskBidding is created. Failures are swallowed so a mail
    outage never breaks the bidding flow. Links are built from the incoming
    ``request``; falls back to ``settings.FRONTEND_URL``.
    """
    task = bid.task
    employer = task.user
    employer_email = getattr(employer, "email", None)
    if not employer_email:
        return

    freelancer = bid.freelancer
    freelancer_name = f"{freelancer.first_name} {freelancer.last_name}".strip() or freelancer.email

    subject = f"New bid on your task: {task.project_name}"

    review_path = reverse("dashboard_manage_bidders", args=[task.id])
    if request is not None:
        site_url = request.build_absolute_uri("/")
        review_url = request.build_absolute_uri(review_path)
    else:
        site_url = settings.FRONTEND_URL
        review_url = settings.FRONTEND_URL.rstrip("/") + review_path

    context = {
        "freelancer_name": freelancer_name,
        "task_name": task.project_name,
        "bid_amount": bid.bid_amount,
        "delivery_time": bid.delivery_time,
        "bids_count": task.bidding.count(),
        "link": review_url,
        "site_url": site_url,
    }

    text_body = (
        f"{freelancer_name} has placed a bid on your task \"{task.project_name}\".\n\n"
        f"Bid amount: NGN {bid.bid_amount}\n"
        f"Delivery time: {bid.delivery_time}\n"
        f"Total bids so far: {context['bids_count']}\n\n"
        f"Review the bid here: {review_url}\n\n"
        f"One Million Jobs"
    )

    try:
        html_body = render_to_string("emails/task_bid_notification.html", context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[employer_email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=True)
    except Exception as e:
        # Don't let an email error surface to the bidder.
        print(f"Failed to send employer bid email: {e}")


SAMPLE_JOBS = [
    {
        "title": "Senior Software Engineer",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Lagos",
        "salary_min": 350000,
        "salary_max": 600000,
        "tags": "Python, Django, PostgreSQL",
        "description": "Develop scalable backend services using Django.",
    },
    {
        "title": "Customer Support Representative",
        "job_type": "full-time",
        "category": "customer_service",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Abuja",
        "salary_min": 80000,
        "salary_max": 120000,
        "tags": "Communication, Email Support, Problem Solving",
        "description": "Assist customers with product-related queries.",
    },
    {
        "title": "Graphic Designer",
        "job_type": "freelance",
        "category": "creative_and_design",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Lagos",
        "salary_min": 50000,
        "salary_max": 150000,
        "tags": "Photoshop, Illustrator, Figma",
        "description": "Create modern visual content for branding.",
    },
    {
        "title": "Marketing Coordinator",
        "job_type": "full-time",
        "category": "marketing_and_advertising",
        "country": "Nigeria",
        "location": "Ikeja",
        "city": "Lagos",
        "salary_min": 150000,
        "salary_max": 250000,
        "tags": "SEO, Social Media, Campaigns",
        "description": "Manage and optimize marketing campaigns.",
    },
    {
        "title": "Data Entry Clerk",
        "job_type": "part-time",
        "category": "clerical_and_data_entry",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Ibadan",
        "salary_min": 40000,
        "salary_max": 60000,
        "tags": "Typing, Accuracy, Excel",
        "description": "Enter large volumes of data into company systems.",
    },
    {
        "title": "Frontend Developer",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Lagos",
        "salary_min": 250000,
        "salary_max": 400000,
        "tags": "React, JavaScript, CSS",
        "description": "Implement high-quality user interfaces.",
    },
    {
        "title": "Backend Developer",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Abuja",
        "salary_min": 300000,
        "salary_max": 500000,
        "tags": "Node.js, Express, MongoDB",
        "description": "Build and maintain backend APIs.",
    },
    {
        "title": "Mobile App Developer",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Calabar",
        "salary_min": 200000,
        "salary_max": 350000,
        "tags": "Flutter, Dart, REST APIs",
        "description": "Develop cross-platform mobile apps.",
    },
    {
        "title": "Research Assistant",
        "job_type": "temporary",
        "category": "research_and_development",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Lagos",
        "salary_min": 70000,
        "salary_max": 100000,
        "tags": "Research, Data Collection, Reporting",
        "description": "Assist in collecting and analyzing research data.",
    },
    {
        "title": "Sales Representative",
        "job_type": "full-time",
        "category": "sales_and_business_development",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Port Harcourt",
        "salary_min": 100000,
        "salary_max": 200000,
        "tags": "Sales, Negotiation, CRM",
        "description": "Sell company products and manage customer leads.",
    },
    {
        "title": "IT Support Technician",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Lagos",
        "salary_min": 120000,
        "salary_max": 180000,
        "tags": "Troubleshooting, Networking, Hardware",
        "description": "Provide technical support to staff and clients.",
    },
    {
        "title": "Content Writer",
        "job_type": "freelance",
        "category": "media_and_entertainment",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Lagos",
        "salary_min": 30000,
        "salary_max": 70000,
        "tags": "Writing, SEO, Blogging",
        "description": "Write SEO-friendly content for blogs.",
    },
    {
        "title": "HR Assistant",
        "job_type": "full-time",
        "category": "other",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Ibadan",
        "salary_min": 80000,
        "salary_max": 120000,
        "tags": "HR, Payroll, Recruitment",
        "description": "Assist HR in recruitment and employee management.",
    },
    {
        "title": "Project Manager",
        "job_type": "full-time",
        "category": "science_and_technology",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Abuja",
        "salary_min": 250000,
        "salary_max": 450000,
        "tags": "PM, Agile, Scrum",
        "description": "Lead teams to achieve project goals.",
    },
    {
        "title": "Accountant",
        "job_type": "full-time",
        "category": "accounting_and_finance",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Lagos",
        "salary_min": 200000,
        "salary_max": 300000,
        "tags": "Accounting, Excel, Reporting",
        "description": "Handle company financials and prepare reports.",
    },
    {
        "title": "Video Editor",
        "job_type": "freelance",
        "category": "media_and_entertainment",
        "country": "Nigeria",
        "location": "Remote",
        "city": "Lagos",
        "salary_min": 60000,
        "salary_max": 150000,
        "tags": "Premiere Pro, Editing, Filmmaking",
        "description": "Edit video content for social media and ads.",
    },
    {
        "title": "Teacher",
        "job_type": "full-time",
        "category": "education_and_training",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Benin City",
        "salary_min": 50000,
        "salary_max": 90000,
        "tags": "Teaching, Communication, Leadership",
        "description": "Teach students based on provided curriculum.",
    },
    {
        "title": "Logistics Coordinator",
        "job_type": "full-time",
        "category": "transportation_and_logistics",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Lagos",
        "salary_min": 90000,
        "salary_max": 150000,
        "tags": "Logistics, Planning, Dispatch",
        "description": "Coordinate deliveries and manage operations.",
    },
    {
        "title": "Electrician",
        "job_type": "full-time",
        "category": "construction_and_maintenance",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Abeokuta",
        "salary_min": 70000,
        "salary_max": 130000,
        "tags": "Electrical Wiring, Repair, Safety",
        "description": "Handle electrical maintenance tasks.",
    },
    {
        "title": "Environmental Officer",
        "job_type": "full-time",
        "category": "agriculture_and_environment",
        "country": "Nigeria",
        "location": "Onsite",
        "city": "Enugu",
        "salary_min": 100000,
        "salary_max": 160000,
        "tags": "Environment, Field Work, Reporting",
        "description": "Monitor and evaluate environmental compliance.",
    },
]



def create_sample_jobs(user_id):
    """
    Bulk create 20 sample jobs for testing.
    """
    user = User.objects.get(id=user_id)

    created_jobs = []

    for job in SAMPLE_JOBS:
        created = Job.objects.create(
            user=user,
            title=job["title"],
            job_type=job["job_type"],
            category=job["category"],
            country=job["country"],
            location=job["location"],
            city=job["city"],
            salary_min=job["salary_min"],
            salary_max=job["salary_max"],
            tags=job["tags"],
            description=job["description"],
            expiration_date=timezone.now() + timedelta(days=30),
            approved=True,
        )
        created_jobs.append(created)

    return created_jobs



SAMPLE_JOBS_USA = [
    {
        "title": "Software QA Tester",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "United States",
        "location": "Remote",
        "city": "New York",
        "salary_min": 5500,
        "salary_max": 7500,
        "tags": "Testing, QA, Selenium",
        "description": "Test software features and report bugs.",
    },
    {
        "title": "Administrative Assistant",
        "job_type": "full-time",
        "category": "clerical_and_data_entry",
        "country": "United States",
        "location": "Onsite",
        "city": "Chicago",
        "salary_min": 3500,
        "salary_max": 5000,
        "tags": "Clerical, Data Entry, Scheduling",
        "description": "Support administrative operations and documentation.",
    },
    {
        "title": "Digital Marketing Specialist",
        "job_type": "full-time",
        "category": "marketing_and_advertising",
        "country": "United States",
        "location": "Hybrid",
        "city": "Austin",
        "salary_min": 6000,
        "salary_max": 9000,
        "tags": "SEO, PPC, Social Media",
        "description": "Plan and implement marketing strategies.",
    },
    {
        "title": "Customer Support Technician",
        "job_type": "full-time",
        "category": "customer_service",
        "country": "United States",
        "location": "Remote",
        "city": "Los Angeles",
        "salary_min": 4000,
        "salary_max": 6500,
        "tags": "Customer Support, Technical Support, Chat Support",
        "description": "Assist customers with technical issues.",
    },
    {
        "title": "Data Analyst",
        "job_type": "full-time",
        "category": "science_and_technology",
        "country": "United States",
        "location": "Remote",
        "city": "Seattle",
        "salary_min": 7000,
        "salary_max": 11000,
        "tags": "Python, SQL, Dashboarding",
        "description": "Analyze business data to support decisions.",
    },
    {
        "title": "Full-Stack Developer",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "United States",
        "location": "Hybrid",
        "city": "San Francisco",
        "salary_min": 9000,
        "salary_max": 14000,
        "tags": "Node.js, React.js, APIs",
        "description": "Build scalable full-stack web applications.",
    },
    {
        "title": "Warehouse Supervisor",
        "job_type": "full-time",
        "category": "transportation_and_logistics",
        "country": "United States",
        "location": "Onsite",
        "city": "Dallas",
        "salary_min": 3500,
        "salary_max": 6000,
        "tags": "Supervision, Logistics, Inventory",
        "description": "Manage warehouse operations and staff.",
    },
    {
        "title": "Project Coordinator",
        "job_type": "full-time",
        "category": "science_and_technology",
        "country": "United States",
        "location": "Remote",
        "city": "Denver",
        "salary_min": 5000,
        "salary_max": 8000,
        "tags": "Project Management, Reporting, Communication",
        "description": "Assist in managing ongoing technical projects.",
    },
    {
        "title": "Nurse Assistant",
        "job_type": "full-time",
        "category": "healthcare",
        "country": "United States",
        "location": "Onsite",
        "city": "Houston",
        "salary_min": 4000,
        "salary_max": 6000,
        "tags": "Nursing, Patient Care, Health",
        "description": "Provide support care to patients.",
    },
    {
        "title": "Content Creator",
        "job_type": "freelance",
        "category": "media_and_entertainment",
        "country": "United States",
        "location": "Remote",
        "city": "Miami",
        "salary_min": 2000,
        "salary_max": 4500,
        "tags": "Content Writing, Video Scripts, Social Media",
        "description": "Produce content for brand marketing campaigns.",
    },
    {
        "title": "Real Estate Agent",
        "job_type": "full-time",
        "category": "real_estate_and_property_management",
        "country": "United States",
        "location": "Onsite",
        "city": "Orlando",
        "salary_min": 5000,
        "salary_max": 12000,
        "tags": "Sales, Real Estate, Negotiation",
        "description": "Sell and manage residential properties.",
    },
    {
        "title": "Mechanical Engineer",
        "job_type": "full-time",
        "category": "engineering_and_technical",
        "country": "United States",
        "location": "Hybrid",
        "city": "Detroit",
        "salary_min": 8000,
        "salary_max": 13000,
        "tags": "CAD, Engineering Design, Manufacturing",
        "description": "Design mechanical systems and components.",
    },
    {
        "title": "Cybersecurity Analyst",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "United States",
        "location": "Remote",
        "city": "Virginia",
        "salary_min": 9500,
        "salary_max": 15000,
        "tags": "Security, SOC, Threat Monitoring",
        "description": "Monitor and analyze cybersecurity threats.",
    },
    {
        "title": "Barista",
        "job_type": "part-time",
        "category": "hospitality_and_tourism",
        "country": "United States",
        "location": "Onsite",
        "city": "Phoenix",
        "salary_min": 1800,
        "salary_max": 3000,
        "tags": "Coffee Making, Customer Service, Cashier",
        "description": "Prepare coffee and serve customers.",
    },
    {
        "title": "Construction Worker",
        "job_type": "full-time",
        "category": "construction_and_maintenance",
        "country": "United States",
        "location": "Onsite",
        "city": "Las Vegas",
        "salary_min": 3500,
        "salary_max": 5500,
        "tags": "Construction, Tools, Safety",
        "description": "Perform on-site construction labor.",
    },
    {
        "title": "Research Scientist",
        "job_type": "full-time",
        "category": "research_and_development",
        "country": "United States",
        "location": "Hybrid",
        "city": "Boston",
        "salary_min": 10000,
        "salary_max": 16000,
        "tags": "Research, Lab Work, Reporting",
        "description": "Conduct experiments and publish findings.",
    },
    {
        "title": "Electric Vehicle Technician",
        "job_type": "full-time",
        "category": "engineering_and_technical",
        "country": "United States",
        "location": "Onsite",
        "city": "San Jose",
        "salary_min": 4500,
        "salary_max": 7000,
        "tags": "EV Repair, Diagnostics, Tools",
        "description": "Repair and maintain electric vehicles.",
    },
    {
        "title": "Tutor (Math & Science)",
        "job_type": "part-time",
        "category": "education_and_training",
        "country": "United States",
        "location": "Remote",
        "city": "Atlanta",
        "salary_min": 2000,
        "salary_max": 3500,
        "tags": "Teaching, STEM, Online Tutoring",
        "description": "Teach students online in math and science.",
    },
    {
        "title": "Chef Assistant",
        "job_type": "full-time",
        "category": "hospitality_and_tourism",
        "country": "United States",
        "location": "Onsite",
        "city": "San Diego",
        "salary_min": 3500,
        "salary_max": 5000,
        "tags": "Cooking, Food Prep, Kitchen Skills",
        "description": "Assist the head chef in meal preparation.",
    },
    {
        "title": "IT Help Desk Specialist",
        "job_type": "full-time",
        "category": "information_technology",
        "country": "United States",
        "location": "Hybrid",
        "city": "Portland",
        "salary_min": 4500,
        "salary_max": 6500,
        "tags": "IT Support, Troubleshooting, Windows",
        "description": "Provide support for company IT systems.",
    },
]

def create_sample_jobs_usa(user_id):
    """
    Bulk create 20 U.S.-based sample jobs.
    """
    user = User.objects.get(id=user_id)
    created_jobs = []

    for job in SAMPLE_JOBS_USA:
        created = Job.objects.create(
            user=user,
            title=job["title"],
            job_type=job["job_type"],
            category=job["category"],
            country=job["country"],
            location=job["location"],
            city=job["city"],
            salary_min=job["salary_min"],
            salary_max=job["salary_max"],
            tags=job["tags"],
            description=job["description"],
            expiration_date=timezone.now() + timedelta(days=30),
            approved=True,
        )
        created_jobs.append(created)

    return created_jobs


SAMPLE_TASKS_NIGERIA = [
    {
        "project_name": "Design a Modern Logo for Tech Startup",
        "category": "design_&_creative",
        "location": "Lagos, Nigeria",
        "budget_min": 20000,
        "budget_max": 45000,
        "project_type": "fixed",
        "skills": "Logo Design, Branding, Illustrator",
        "description": "Create a clean and modern logo for a Nigerian tech brand."
    },
    {
        "project_name": "Customer Support Agent Needed",
        "category": "customer_service",
        "location": "Remote (Nigeria)",
        "budget_min": 30000,
        "budget_max": 60000,
        "project_type": "hourly",
        "skills": "Communication, CRM, Problem Solving",
        "description": "Provide daily customer chat and call support."
    },
    {
        "project_name": "Build a Small Django Web App",
        "category": "software_developing",
        "location": "Abuja, Nigeria",
        "budget_min": 120000,
        "budget_max": 250000,
        "project_type": "fixed",
        "skills": "Python, Django, APIs",
        "description": "Develop a basic CRUD Django application."
    },
    {
        "project_name": "Facebook Ads Manager",
        "category": "sales_&_marketing",
        "location": "Remote",
        "budget_min": 50000,
        "budget_max": 80000,
        "project_type": "hourly",
        "skills": "Facebook Ads, Marketing Strategy, Analytics",
        "description": "Run and optimize ad campaigns for a local brand."
    },
    {
        "project_name": "Write SEO-Optimized Blog Articles",
        "category": "writing",
        "location": "Remote (Nigeria)",
        "budget_min": 15000,
        "budget_max": 35000,
        "project_type": "fixed",
        "skills": "SEO Writing, Research, Editing",
        "description": "Write 5 SEO-optimized articles for a finance blog."
    },
    {
        "project_name": "Translate English Text to Yoruba",
        "category": "tranlation",
        "location": "Ibadan, Nigeria",
        "budget_min": 10000,
        "budget_max": 20000,
        "project_type": "fixed",
        "skills": "Translation, Yoruba, English",
        "description": "Translate a 20-page document from English to Yoruba."
    },
    {
        "project_name": "Data Cleaning for Excel Sheet",
        "category": "data_analytics",
        "location": "Remote",
        "budget_min": 20000,
        "budget_max": 50000,
        "project_type": "fixed",
        "skills": "Excel, Data Cleaning, Analysis",
        "description": "Clean and format 5,000-row dataset."
    },
    {
        "project_name": "IT Support Technician Needed",
        "category": "IT_&_networking",
        "location": "Lagos",
        "budget_min": 40000,
        "budget_max": 70000,
        "project_type": "hourly",
        "skills": "Networking, Troubleshooting, Hardware Repair",
        "description": "Provide office IT support for small business."
    },
    {
        "project_name": "Contract Draft Review",
        "category": "legal",
        "location": "Remote (Nigeria)",
        "budget_min": 25000,
        "budget_max": 60000,
        "project_type": "fixed",
        "skills": "Legal Writing, Contract Review, Research",
        "description": "Review a business partnership contract."
    },
    {
        "project_name": "Admin Support for E-commerce Store",
        "category": "admin_support",
        "location": "Port Harcourt",
        "budget_min": 20000,
        "budget_max": 45000,
        "project_type": "hourly",
        "skills": "Data Entry, Email Handling, MS Office",
        "description": "Assist with order processing and customer messages."
    },
]

from django.utils import timezone
from datetime import timedelta
from .models import Task
from django.contrib.auth import get_user_model

User = get_user_model()


def create_sample_tasks_nigeria(user_id):
    user = User.objects.get(id=user_id)
    created = []

    for task in SAMPLE_TASKS_NIGERIA:
        t = Task.objects.create(
            user=user,
            project_name=task["project_name"],
            category=task["category"],
            location=task["location"],
            budget_min=task["budget_min"],
            budget_max=task["budget_max"],
            project_type=task["project_type"],
            skills=task["skills"],
            description=task["description"],
            expiration_date=timezone.now() + timedelta(days=30),
            status="active",
        )
        created.append(t)

    return created

SAMPLE_TASKS_USA = [
    {
        "project_name": "Full Website Redesign (Figma + Webflow)",
        "category": "design_&_creative",
        "location": "New York, USA",
        "budget_min": 800,
        "budget_max": 1500,
        "project_type": "fixed",
        "skills": "Figma, Web Design, UI/UX",
        "description": "Redesign corporate website for a U.S. startup."
    },
    {
        "project_name": "Virtual Customer Service Agent",
        "category": "customer_service",
        "location": "Remote (USA)",
        "budget_min": 15,
        "budget_max": 25,
        "project_type": "hourly",
        "skills": "Customer Support, Live Chat, CRM",
        "description": "Provide professional customer service for e-commerce brand."
    },
    {
        "project_name": "Python Script for Automation",
        "category": "software_developing",
        "location": "San Francisco, USA",
        "budget_min": 500,
        "budget_max": 1200,
        "project_type": "fixed",
        "skills": "Python, Automation, APIs",
        "description": "Write automation script to integrate multiple APIs."
    },
    {
        "project_name": "Legal Research Assistant",
        "category": "legal",
        "location": "Remote",
        "budget_min": 20,
        "budget_max": 40,
        "project_type": "hourly",
        "skills": "Legal Research, Documentation",
        "description": "Assist with U.S. federal case research."
    },
    {
        "project_name": "SEO Optimized Content Writing",
        "category": "writing",
        "location": "Chicago, USA",
        "budget_min": 100,
        "budget_max": 250,
        "project_type": "fixed",
        "skills": "Content Writing, SEO, Editing",
        "description": "Write 3 high-quality SEO articles."
    },
    {
        "project_name": "IT Network Setup for Office",
        "category": "IT_&_networking",
        "location": "Los Angeles, USA",
        "budget_min": 600,
        "budget_max": 1000,
        "project_type": "fixed",
        "skills": "Networking, Routers, Server Setup",
        "description": "Setup office networking and security tools."
    },
    {
        "project_name": "Data Visualization Dashboard",
        "category": "data_analytics",
        "location": "Boston, USA",
        "budget_min": 700,
        "budget_max": 1500,
        "project_type": "fixed",
        "skills": "Python, Power BI, Data Visualization",
        "description": "Build a full analytics dashboard for U.S. client."
    },
    {
        "project_name": "Sales Funnel Creation",
        "category": "sales_&_marketing",
        "location": "Dallas, USA",
        "budget_min": 400,
        "budget_max": 900,
        "project_type": "fixed",
        "skills": "Marketing, Funnels, CRM",
        "description": "Create a lead funnel for a U.S. consulting firm."
    },
    {
        "project_name": "Translate Spanish to English",
        "category": "tranlation",
        "location": "Miami, USA",
        "budget_min": 120,
        "budget_max": 250,
        "project_type": "fixed",
        "skills": "Translation, Spanish, English",
        "description": "Translate business proposal from Spanish to English."
    },
    {
        "project_name": "Admin Assistant for U.S. Business",
        "category": "admin_support",
        "location": "Houston, USA",
        "budget_min": 15,
        "budget_max": 30,
        "project_type": "hourly",
        "skills": "Admin, Email Handling, Scheduling",
        "description": "Provide administrative support and schedule management."
    },
]

def create_sample_tasks_usa(user_id):
    user = User.objects.get(id=user_id)
    created = []

    for task in SAMPLE_TASKS_USA:
        t = Task.objects.create(
            user=user,
            project_name=task["project_name"],
            category=task["category"],
            location=task["location"],
            budget_min=task["budget_min"],
            budget_max=task["budget_max"],
            project_type=task["project_type"],
            skills=task["skills"],
            description=task["description"],
            expiration_date=timezone.now() + timedelta(days=30),
            status="active",
        )
        created.append(t)

    return created
