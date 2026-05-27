from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count
from django.conf import settings
from django.utils import timezone

def has_collaborated_on_object(reviewer, reviewee, obj):
    """
    Returns True if reviewer and reviewee collaborated on obj (Job or Task).
    Collaboration criteria:
      - Job: JobApplication exists for job=obj with status in ['accepted', 'completed']
             where one user is the job owner and the other is the applicant.
      - Task: TaskBidding exists for task=obj with status in ['accepted', 'completed']
              where one user is the task owner and the other is the bidder.
    """
    model_name = obj.__class__.__name__.lower()
    if model_name == 'job':
        # JobApplication model: jobs.JobApplication
        try:
            JobApplication = apps.get_model('ManageJobsTasks', 'JobApplication')
        except LookupError:
            raise ValidationError("JobApplication model not found in 'ManageJobsTasks' app.")

        valid_status = ['accepted', 'completed']
        # If reviewer is applicant and reviewee is job owner
        if JobApplication.objects.filter(job=obj, user=reviewer, status__in=valid_status).exists() and obj.user == reviewee:
            return True
        # If reviewee is applicant and reviewer is job owner
        if JobApplication.objects.filter(job=obj, user=reviewee, status__in=valid_status).exists() and obj.user == reviewer:
            return True
        return False

    if model_name == 'task':
        try:
            TaskBidding = apps.get_model('ManageJobsTasks', 'TaskBidding')
        except LookupError:
            raise ValidationError("TaskBidding model not found in 'ManageJobsTasks' app.")

        valid_status = ['accepted', 'completed']
        # If reviewer is bidder and reviewee is task owner
        if TaskBidding.objects.filter(task=obj, freelancer=reviewer, status__in=valid_status).exists() and obj.user == reviewee:
            return True
        # If reviewee is bidder and reviewer is task owner
        if TaskBidding.objects.filter(task=obj, freelancer=reviewee, status__in=valid_status).exists() and obj.user == reviewer:
            return True
        return False

    # unsupported object
    raise ValidationError("Unsupported object type for reviews. Only Job and Task are allowed.")


def update_user_aggregate_rating(user):
    """
    Recompute avg_rating and rating_count on the user's profile based on Review entries.
    Assumes UserProfile exists and has avg_rating (FloatField) and rating_count (IntegerField).
    """
    Review = apps.get_model('reviews', 'Review')
    UserProfile = None
    try:
        UserProfile = apps.get_model('users', 'UserProfile')
    except LookupError:
        try:
            UserProfile = apps.get_model('accounts', 'UserProfile')
        except LookupError:
            raise ValidationError("UserProfile model not found in 'users' or 'accounts' app.")

    agg = Review.objects.filter(reviewee=user, rating__isnull=False).aggregate(avg=Avg('rating'), cnt=Count('id'))
    avg = agg.get('avg') or 0.0
    cnt = agg.get('cnt') or 0

    profile = UserProfile.objects.get(user=user)
    # Ensure fields exist on profile
    if not hasattr(profile, 'avg_rating') or not hasattr(profile, 'rating_count'):
        raise ValidationError("UserProfile must have 'avg_rating' and 'rating_count' fields.")
    profile.avg_rating = round(float(avg), 2)
    profile.rating = profile.avg_rating
    profile.rating_count = cnt
    profile.save(update_fields=['avg_rating', 'rating_count', 'rating'])


def get_pending_reviews_for_user(user):
    """
    Returns a list of interactions where the user can still leave a review.
    For each interaction: provide object_type (job/task), object_id, other_user_id, other_username, title/name.
    """
    pending = []
    valid_status = ['accepted', 'completed']

    Job = apps.get_model('ManageJobsTasks', 'Job')
    JobApplication = apps.get_model('ManageJobsTasks', 'JobApplication')
    Task = apps.get_model('ManageJobsTasks', 'Task')
    TaskBidding = apps.get_model('ManageJobsTasks', 'TaskBidding')
    Review = apps.get_model('reviews', 'Review')

    # -----------------------------
    # JOBS
    # -----------------------------

    job_ct = ContentType.objects.get_for_model(Job)

    # As applicant — review job owner
    applicant_apps = JobApplication.objects.filter(
        user=user, status__in=valid_status
    ).select_related('job', 'job__user')

    for app in applicant_apps:
        job = app.job
        owner = job.user
        # Avoid duplicate reviews
        if not Review.objects.filter(reviewer=user, content_type=job_ct, object_id=job.pk).exists():
            pending.append({
                'relation': 'applicant',
                'object_type': 'job',
                'object_id': job.pk,
                'title': job.title,
                'other_user_id': owner.id,
                'other_user_name': f"{owner.first_name} {owner.last_name}",
            })

    # As job owner — review applicant(s)
    owner_apps = JobApplication.objects.filter(
        job__user=user, status__in=valid_status
    ).select_related('job', 'user')

    for app in owner_apps:
        job = app.job
        applicant = app.user
        if not Review.objects.filter(reviewer=user, content_type=job_ct, object_id=job.pk).exists():
            pending.append({
                'relation': 'owner',
                'object_type': 'job',
                'object_id': job.pk,
                'title': job.title,
                'other_user_id': applicant.id,
                'other_user_name': f"{applicant.first_name} {applicant.last_name}",
            })

    # -----------------------------
    # TASKS
    # -----------------------------

    task_ct = ContentType.objects.get_for_model(Task)

    # As bidder — review task owner
    bidder_bids = TaskBidding.objects.filter(
        freelancer=user, status__in=valid_status
    ).select_related('task', 'task__user')

    for bid in bidder_bids:
        task = bid.task
        owner = task.user
        if not Review.objects.filter(reviewer=user, content_type=task_ct, object_id=task.pk).exists():
            pending.append({
                'relation': 'bidder',
                'object_type': 'task',
                'object_id': task.pk,
                'title': task.project_name,
                'other_user_id': owner.id,
                'other_user_name': f"{owner.first_name} {owner.last_name}",
            })

    # As task owner — review bidder(s)
    owner_bids = TaskBidding.objects.filter(
        task__user=user, status__in=valid_status
    ).select_related('task', 'freelancer')

    for bid in owner_bids:
        task = bid.task
        freelancer = bid.freelancer
        if not Review.objects.filter(reviewer=user, content_type=task_ct, object_id=task.pk).exists():
            pending.append({
                'relation': 'owner',
                'object_type': 'task',
                'object_id': task.pk,
                'title': task.project_name,
                'other_user_id': freelancer.id,
                'other_user_name': f"{freelancer.first_name} {freelancer.last_name}",
            })

    return pending