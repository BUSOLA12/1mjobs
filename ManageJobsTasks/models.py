from django.db import models
from django.core.validators import MinValueValidator
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

# Create your models here.
JOB_TYPES = [
    ('full-time', 'Full Time'),
    ('part-time', 'Part Time'),
    ('freelance', 'Freelance'),
    ('internship', 'Internship'),
    ('temporary', 'Temporary'),
]

JOB_CATEGORIES = [
    ('accounting_and_finance', 'Accounting and Finance'),
    ('clerical_and_data_entry', 'Clerical and Data Entry'),
    ('customer_service', 'Customer Service'),
    ('engineering_and_technical', 'Engineering and Technical'),
    ('healthcare', 'Healthcare'),
    ('hospitality_and_tourism', 'Hospitality and Tourism'),
    ('information_technology', 'Information Technology'),
    ('legal', 'Legal'),
    ('marketing_and_advertising', 'Marketing and Advertising'),
    ('sales_and_business_development', 'Sales and Business Development'),
    ('skilled_trades_and_services', 'Skilled Trades and Services'),
    ('education_and_training', 'Education and Training'),
    ('creative_and_design', 'Creative and Design'),
    ('real_estate_and_property_management', 'Real Estate and Property Management'),
    ('transportation_and_logistics', 'Transportation and Logistics'),
    ('construction_and_maintenance', 'Construction and Maintenance'),
    ('research_and_development', 'Research and Development'),
    ('non_profit_and_volunteering', 'Non-Profit and Volunteering'),
    ('government_and_public_service', 'Government and Public Service'),
    ('media_and_entertainment', 'Media and Entertainment'),
    ('telecommunications', 'Telecommunications'),
    ('energy_and_utilities', 'Energy and Utilities'),
    ('agriculture_and_environment', 'Agriculture and Environment'),
    ('science_and_technology', 'Science and Technology'),
    ('other', 'Other'),
]

JOB_STATUS = [
    ("pending", "Pending"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
]


class JobCategory(models.Model):
    """Admin-managed job categories. `Job.category` stores the slug, so seeding
    this table from JOB_CATEGORIES keeps every existing job valid. The job-post
    form's dropdown is built from the active rows here."""
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Job categories"

    def __str__(self):
        return self.name

class Job(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='name_job')
    title = models.CharField(max_length=255)
    job_type = models.CharField(max_length=50, choices=JOB_TYPES)
    category = models.CharField(max_length=100, choices=JOB_CATEGORIES)
    country = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='pending')
    city = models.CharField(max_length=100, null=True, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    tags = models.TextField(
        blank=True,
        help_text="Optional tags (comma-separated, max 10 tags)"
    )
    description = models.TextField()
    image = models.ImageField(upload_to="job_images/", null=True, blank=True)
    files = models.FileField(upload_to="job_uploads/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    expiration_date = models.DateTimeField(
        blank=True,
        help_text="Project deadline"
    )
    approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            # Set default expiration date based on plan or default to +30 days
            self.expiration_date = timezone.now() + timedelta(days=30)

        if self.expiration_date and self.expiration_date < timezone.now():
            # Optional: handle expired jobs
            self.is_active = False

        super().save(*args, **kwargs)



    def __str__(self):
        return self.title


class JobFile(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="job_files")
    file = models.FileField(upload_to="job_uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.job.title}"


# jobs/models.py (excerpt - JobApplication change)
from django.db import models
from django.conf import settings

APPLICATION_STATUS = [
    ("pending", "Pending"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
    ("cancelled", "Cancelled"),
    ("completed", "Completed"),
]

class JobApplication(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='application', default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applicant')
    name = models.CharField(max_length=255)
    # Platform-internal only. Set server-side from the applicant's account; the
    # employer never sees it (kept private so the platform mediates contact).
    email = models.EmailField()
    # The freelancer's typed pitch and their proposed price for the job.
    proposal = models.TextField(default="")
    bid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    # Optional CV / resume upload.
    files = models.FileField(upload_to="applications/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def applications_count(self):
        return self.job.application.count()
    
    def __str__(self):
        return f"Application for {self.job.title} by {self.name}"




TASK_CATEGORIES = [
    ('admin_support', 'Admin Support'),
    ('customer_service', 'Customer_Service'),
    ('data_analytics', 'Data Analytics'),
    ('design_&_creative', 'Design & Creative'),
    ('legal', 'Legal'),
    ('software_developing', 'Software Development'),
    ('IT_&_networking', 'IT & Networking'),
    ('writing', 'Writing'),
    ('tranlation', 'Translation'),
    ('sales_&_marketing', 'Sales & Marketing'),
]

PROJECT_TYPES = [
    ('fixed', 'Fixed'),
    ('hourly', 'Hourly'),
]


TASK_STATUS = [
    ('draft', 'Draft'),
    ('active', 'Active'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('expired', 'Expired'),
]

class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='name_task')
    project_name = models.CharField(max_length=225)
    category = models.CharField(max_length=100, choices=TASK_CATEGORIES)
    location = models.CharField(max_length=100, blank=True, null=True)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    skills = models.TextField(
        help_text="Required skills (comma-separated, max 5 skills)"
    )
    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS,
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiration_date = models.DateTimeField(
        blank=True,
        help_text="Project deadline"
    )
    is_expired = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    description = models.TextField(
        default="A task",
        help_text="Detailed project description"
    )
    image = models.ImageField(upload_to="task_images/", null=True, blank=True)
    files = models.FileField(
        upload_to="task_uploads/",
        null=True,
        blank=True,
        help_text="Optional project files"
    )
    approved = models.BooleanField(default=False)


    class Meta:
        ordering = ['-created_at']
        # indexes = [
        #     models.Index(fields=['status', 'created_at']),
        #     models.Index(fields=['category', 'status']),
        # ]
    
    

    def __str__(self):
        return self.project_name
    
    @property
    def budget_range(self):
        """Return formatted budget range"""
        return f"${self.budget_min} - ${self.budget_max}"
    
    @property
    def skills_list(self):
        """Return skills as a list"""
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
        return []
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            # Set default expiration date based on plan or default to +30 days
            self.expiration_date = timezone.now() + timedelta(days=30)

        if self.expiration_date and self.expiration_date < timezone.now():
            # Optional: handle expired jobs
            self.is_active = False

        super().save(*args, **kwargs)

STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

class TaskBidding(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="bidding")
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="freelancer_name")
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.CharField(max_length=250)
    status = models.CharField(max_length=250, choices=STATUS_CHOICES, default="pending")
    read_TC = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "freelancer"], name="unique_bid_per_freelancer_per_task"),
        ]

    def __str__(self):
        return f"Bid by {self.freelancer} on {self.task} - {self.status}"