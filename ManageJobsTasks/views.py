from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from users.utils import log_user_action
from .serializers import JobSerializer, TaskSerializer, JobApplicationSerializer, TaskBidsSerializer, get_online_user_ids
from .models import Job, Task, JobApplication, TaskBidding, JobFile
from reviews.models import Review
from .utils import validate_job_file, notify_employer_of_application, notify_employer_of_bid, apply_early_access_window
from pricing.subscription_engine import check_and_consume_feature
from pricing.features import FEATURED_JOB
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.core.cache import cache
from .pagination import JobPagination
import requests

from rest_framework.parsers import MultiPartParser, FormParser


# Task.objects.all().delete()

# Create your views here.
class JobCreateAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        """Assign permissions per HTTP method."""
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [IsAuthenticated()]  # Write operations require a logged-in user
        return [AllowAny()]

    def post(self, request):
        # Only employers and admins may post jobs
        if getattr(request.user, "role", None) not in ("employer", "admin"):
            return Response({"error": "Only employers can post jobs."}, status=status.HTTP_403_FORBIDDEN)

        # Validate every uploaded file before touching the database.
        uploaded_files = request.FILES.getlist("files")
        for uploaded_file in uploaded_files:
            error = validate_job_file(uploaded_file)
            if error:
                return Response({"files": [error]}, status=status.HTTP_400_BAD_REQUEST)

        # Employer Pro perk: feature this job (consumes one featured_job slot).
        want_featured = str(request.data.get("featured", "")).lower() in ("1", "true", "yes")

        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                job = serializer.save(user=request.user)
                if want_featured:
                    # Raises PermissionDenied (403) if the plan lacks or has
                    # exhausted the featured_job quota; the atomic block rolls
                    # the job creation back so nothing is half-saved.
                    check_and_consume_feature(request.user, FEATURED_JOB)
                    job.is_featured = True
                    job.save(update_fields=["is_featured"])
                for uploaded_file in uploaded_files:
                    JobFile.objects.create(job=job, file=uploaded_file)

            log_user_action(request.user, "create_job", metadata={"job_id": job.id})
            return Response(
                {"message": "Job created successfully", "data": JobSerializer(job, context={"request": request}).data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




     

    def get(self, request):

        search = request.GET.get('search', "")
        sort = request.GET.get('sort', "")
        min_salary = request.GET.get('min_salary', "")
        max_salary = request.GET.get('max_salary', "")
        job_type = request.GET.get('job_type', "")
        tags = request.GET.get('tags', "")
        category = request.GET.get('category', "")
        location = request.GET.get('location', "")
        city = request.GET.get('city', "")

        jobs = Job.objects.filter(approved=True)
        jobs = apply_early_access_window(jobs, request)
        query = Q()

        if search:
            query |= (
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(tags__icontains=search)
            )

        if location:
            query |= Q(location__icontains=location)

        if job_type:
            query |= Q(job_type__icontains=job_type)

        if category:
            query |= Q(category__icontains=category)
        if city:
            query |= Q(city__icontains=city)



        if min_salary and max_salary:
            try:
                min_salary = int(min_salary)
                max_salary = int(max_salary)
                query &= Q(salary_min__gte=min_salary) | Q(salary_max__lte=max_salary)
            except ValueError:
                pass

        if query:
            jobs = jobs.filter(query)

        # Featured jobs (Employer Pro perk) float to the top of default/newest.
        sort = sort.lower()
        if sort == "oldest":
            jobs = jobs.order_by("created_at")
        elif sort == "random":
            jobs = jobs.order_by("?")
        else:
            jobs = jobs.order_by("-is_featured", "-created_at")

        paginator = JobPagination()
        paginated_jobs = paginator.paginate_queryset(jobs, request)


        serializer = JobSerializer(paginated_jobs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    
    def put(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)

            if job.user != request.user:
                return Response({"error": "You are not authorized to edit this job"}, status=status.HTTP_403_FORBIDDEN)

            print(f"Received data: {request.data}")
            print(f"Job found: {job.id}")

            serializer = JobSerializer(job, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:
                print(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Job.DoesNotExist:

            print(f"Job with pk={pk} not found")
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)

            if job.user != request.user:
                return Response({"error": "You are not authorized to edit this job"}, status=status.HTTP_403_FORBIDDEN)

            serializer = JobSerializer(job, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    
    def delete(self, request, pk):

        try:
            job = Job.objects.get(pk=pk)
            if job.user != request.user:
                return Response({"error": "You are not authorized to delete this job"}, status=status.HTTP_403_FORBIDDEN)
            
            log_user_action(request.user, "delete_job", metadata={"job_id": job.id})
            
            job.delete()
            
            return Response({"Message": "Job delete successfully"}, status=status.HTTP_200_OK)

        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class JobGetAPIView(APIView):
    TAGS_CACHE_KEY = "job_tags_list"
    TAGS_CACHE_TTL = 60 * 60  # 1 hour

    def _get_all_tags(self):
        """Distinct tags across all approved jobs, cached. Attached to the
        list response so the frontend needs no separate request."""
        tags = cache.get(self.TAGS_CACHE_KEY)
        if tags is None:
            counter = {}
            for raw in Job.objects.filter(approved=True).values_list("tags", flat=True):
                for tag in (raw or "").split(","):
                    tag = tag.strip()
                    if not tag:
                        continue
                    key = tag.lower()  # dedupe case-insensitively
                    if key not in counter:
                        counter[key] = {"tag": tag, "count": 0}  # keep first-seen casing
                    counter[key]["count"] += 1
            tags = sorted(counter.values(), key=lambda t: (-t["count"], t["tag"].lower()))
            cache.set(self.TAGS_CACHE_KEY, tags, self.TAGS_CACHE_TTL)
        return tags

    def get(self, request):

        search = request.GET.get('search', "")
        sort = request.GET.get('sort', "")
        min_salary = request.GET.get('min_salary', "")
        max_salary = request.GET.get('max_salary', "")
        job_type = request.GET.get('job_type', "")
        tags = request.GET.getlist('tags')
        category = request.GET.get('category', "")
        location = request.GET.get('location', "")
        city = request.GET.get('city', "")

        jobs = Job.objects.filter(approved=True)
        jobs = apply_early_access_window(jobs, request)
        query = Q()

        if search:
            query |= (
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(tags__icontains=search)
            )

        if location:
            query |= Q(location__icontains=location)

        if job_type:
            query |= Q(job_type__icontains=job_type)

        if category:
            query |= Q(category__icontains=category)
        if city:
            query |= Q(city__icontains=city)

        if tags:
            tag_q = Q()
            for tag in tags:
                tag = tag.strip()
                if tag:
                    tag_q |= Q(tags__icontains=tag)  # match a job with ANY selected tag
            query |= tag_q


        if min_salary and max_salary:
            try:
                min_salary = int(min_salary)
                max_salary = int(max_salary)
                query &= Q(salary_min__gte=min_salary) | Q(salary_max__lte=max_salary)
            except ValueError:
                pass

        if query:
            jobs = jobs.filter(query)

        # Featured jobs (Employer Pro perk) float to the top of default/newest.
        sort = sort.lower()
        if sort == "oldest":
            jobs = jobs.order_by("created_at")
        elif sort == "random":
            jobs = jobs.order_by("?")
        else:
            jobs = jobs.order_by("-is_featured", "-created_at")

        paginator = JobPagination()
        paginated_jobs = paginator.paginate_queryset(jobs, request)


        serializer = JobSerializer(paginated_jobs, many=True, context={'request': request})
        response = paginator.get_paginated_response(serializer.data)
        response.data["tags"] = self._get_all_tags()  # complete, cached tag list
        return response


class JobDetailAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
            serializer = JobSerializer(job, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)


class FeaturedJobsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            jobs = Job.objects.filter(
                is_featured=True, is_active=True, approved=True
            ).order_by("-created_at")
            serializer = JobSerializer(jobs, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        
class FeaturedJobsCitiesAPIView(APIView):
    permission_classes = [AllowAny]

    DEFAULT_CITY_IMAGE = "/static/images/default-city.png"
    CITY_IMAGE_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days

    def get_city_image(self, city):
        cache_key = f"city_image:{city.strip().lower()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            city_formatted = city.strip().title()
            search_terms = [
                f"{city_formatted}, Nigeria",
                city_formatted,
                f"{city_formatted} (city)",
            ]

            url = "https://en.wikipedia.org/w/api.php"
            headers = {
                "User-Agent": "JobFinderApp/1.0 (contact: web79.tech@gmail.com)"
            }

            for search_term in search_terms:
                params = {
                    "action": "query",
                    "titles": search_term,
                    "prop": "pageimages",
                    "format": "json",
                    "pithumbsize": 400,
                    "redirects": 1,
                }

                r = requests.get(url, params=params, headers=headers, timeout=5)
                r.raise_for_status()

                pages = r.json().get("query", {}).get("pages", {})
                if pages:
                    page = next(iter(pages.values()), {})
                    if "missing" not in page:
                        thumbnail = page.get("thumbnail", {}).get("source")
                        if thumbnail:
                            cache.set(cache_key, thumbnail, self.CITY_IMAGE_CACHE_TTL)
                            return thumbnail

            cache.set(cache_key, self.DEFAULT_CITY_IMAGE, self.CITY_IMAGE_CACHE_TTL)
            return self.DEFAULT_CITY_IMAGE

        except requests.exceptions.RequestException as e:
            print(f"Wikipedia API error for {city}: {str(e)}")
            return self.DEFAULT_CITY_IMAGE
        except Exception as e:
            print(f"Unexpected error getting image for {city}: {str(e)}")
            return self.DEFAULT_CITY_IMAGE

    MIN_JOBS_PER_CITY = 3
    MAX_FEATURED_CITIES = 8

    def get(self, request):
        try:
            city_data = (
                Job.objects
                .filter(
                    is_active=True,
                    approved=True,
                    is_expired=False,
                )
                .exclude(city__isnull=True)
                .exclude(city__exact="")
                .values('city')
                .annotate(job_count=Count('id'))
                .filter(job_count__gte=self.MIN_JOBS_PER_CITY)
                .order_by('-job_count', 'city')
                [:self.MAX_FEATURED_CITIES]
            )

            result = [
                {
                    "city": item["city"],
                    "job_count": item["job_count"],
                    "img": self.get_city_image(item["city"]),
                }
                for item in city_data
            ]

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Featured cities API error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class ManageJobAPIView(APIView):
    def get(self, request):

        jobs = Job.objects.all()
    
        jobs = jobs.filter(user=request.user)
        
        

        paginator = JobPagination()
        paginated_jobs = paginator.paginate_queryset(jobs, request)

                
        serializer = JobSerializer(paginated_jobs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

        


class JobApplicationCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            # The applicant's identity is taken from their account, never the
            # client. The employer must not be able to set or see the email, so
            # we bind user + email server-side and ignore anything posted for them.
            data = request.data.copy()
            data["user"] = request.user.id
            data["email"] = request.user.email

            serializer = JobApplicationSerializer(data=data)
            if serializer.is_valid():
                application = serializer.save(user=request.user, email=request.user.email)

                notify_employer_of_application(application, request=request)

                log_user_action(request.user, "create_job_application", metadata={"application_id": application.id})
                return Response({"message": "Application submitted successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                print(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request, jobId):
        try:
            applications = JobApplication.objects.filter(job=jobId).select_related('user')
            online_user_ids = get_online_user_ids([app.user_id for app in applications])
            serializer = JobApplicationSerializer(
                applications,
                many=True,
                context={'request': request, 'online_user_ids': online_user_ids},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class MyJobApplicationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            applications = JobApplication.objects.filter(user=request.user).select_related('job').order_by('-created_at')
            online_user_ids = get_online_user_ids([app.user_id for app in applications])
            serializer = JobApplicationSerializer(
                applications,
                many=True,
                context={'request': request, 'online_user_ids': online_user_ids},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobApplicationDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            application = JobApplication.objects.get(pk=pk)

            # Only the applicant (withdrawing) or the job owner may delete
            if request.user != application.user and request.user != application.job.user:
                return Response({"error": "You are not authorized to delete this application"}, status=status.HTTP_403_FORBIDDEN)

            log_user_action(request.user, "delete_job_application", metadata={"application_id": application.id})
            application.delete()
            return Response({"message": "Job Application deleted successfully"}, status=status.HTTP_200_OK)
        except JobApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Deletion failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class JobApplicationAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            with transaction.atomic():
                application = (
                    JobApplication.objects.select_related("job")
                    .select_for_update()  # no-op on SQLite, real row lock on Postgres
                    .get(pk=pk)
                )
                job = application.job

                # Only the job owner may accept an application for their job
                if job.user != request.user:
                    return Response(
                        {"message": "You are not allowed to accept applications for this job."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # This specific application is already accepted
                if application.status == "accepted":
                    return Response({"message": "Application Already Accepted"}, status=status.HTTP_409_CONFLICT)

                # A job may have only ONE accepted applicant
                if JobApplication.objects.filter(
                    job=job, status__in=["accepted", "completed"]
                ).exclude(pk=pk).exists():
                    return Response(
                        {"message": "This job already has an accepted applicant."},
                        status=status.HTTP_409_CONFLICT,
                    )

                # Accept this application and reject the remaining pending ones on the same job
                application.status = "accepted"
                application.save(update_fields=["status"])
                JobApplication.objects.filter(job=job, status="pending").exclude(pk=pk).update(status="rejected")

            log_user_action(request.user, "accept_job_application", metadata={"application_id": application.id})
            return Response({"message": "Application accepted", "id": application.id}, status=status.HTTP_200_OK)

        except JobApplication.DoesNotExist:
            return Response({"message": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobApplicationCountAPIView(APIView):
    def get(self, request, pk):
        try:
            applications = JobApplication.objects.filter(job=pk)
            count = applications.count()
            return Response({"count": count}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"An error occured": f"{str(e)}"})





class JobCategoriesGetAPIView(APIView):
    def get(self, request):
        categories = (
            Job.objects.values("category")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        # Map category slugs to human-readable names
        category_name_map = dict(Job._meta.get_field("category").choices)

        data = [
            {
                "category": cat["category"],
                "name": category_name_map.get(cat["category"], cat["category"]),
                "total": cat["total"]
            }
            for cat in categories
        ]
        return Response(data)



class JobSimilarAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            # Try fetching the job
            job = get_object_or_404(Job, pk=pk)

            # Ensure the job has a category
            if not job.category:
                return Response(
                    {"error": "This job does not have an associated category."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get similar jobs within the same category, excluding the current job
            similar_jobs = Job.objects.filter(category=job.category, approved=True).exclude(pk=pk)[:5]

            # Handle case where no similar jobs are found
            if not similar_jobs:
                return Response(
                    {"message": "No similar jobs found."},
                    status=status.HTTP_204_NO_CONTENT
                )

            # Serialize and return data
            serializer = JobSerializer(similar_jobs, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response(
                {"error": "The requested job was not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        except DatabaseError:
            return Response(
                {"error": "A database error occurred while fetching similar jobs."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TaskCreateAPIView(APIView):

    # permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    SKILLS_CACHE_KEY = "task_skills_list"
    SKILLS_CACHE_TTL = 60 * 60  # 1 hour

    def _get_all_skills(self):
        """Distinct skills across all tasks, cached. Attached to the list
        response so the frontend needs no separate request."""
        skills = cache.get(self.SKILLS_CACHE_KEY)
        if skills is None:
            counter = {}
            for raw in Task.objects.filter(approved=True).values_list("skills", flat=True):
                for skill in (raw or "").split(","):
                    skill = skill.strip()
                    if not skill:
                        continue
                    key = skill.lower()  # dedupe case-insensitively
                    if key not in counter:
                        counter[key] = {"tag": skill, "count": 0}  # keep first-seen casing
                    counter[key]["count"] += 1
            skills = sorted(counter.values(), key=lambda s: (-s["count"], s["tag"].lower()))
            cache.set(self.SKILLS_CACHE_KEY, skills, self.SKILLS_CACHE_TTL)
        return skills

    def get_permissions(self):
        """Assign permissions per HTTP method."""
        if self.request.method == "POST":
            return [IsAuthenticated()]  # Only logged-in users can create tasks
        return [AllowAny()] 
    def post(self, request):

        try:
            serializer = TaskSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                task = serializer.save(user=request.user)

                log_user_action(request.user, "create_task", metadata={"task_id": task.id})
                return Response({"message": "Task created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                print(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def get(self, request):

        

        search = request.GET.get('search', "")
        sort = request.GET.get('sort', "")
        min_budget = request.GET.get('min_budget', "")
        max_budget = request.GET.get('max_budget', "")
        skills = request.GET.getlist('skills')
        category = request.GET.get('category', "")
        location = request.GET.get('location', "")

        tasks = Task.objects.filter(approved=True)
        query = Q()

        if search:
            query |= (
                Q(project_name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(skills__icontains=search)
            )

        if skills:
            skill_q = Q()
            for skill in skills:
                skill = skill.strip()
                if skill:
                    skill_q |= Q(skills__icontains=skill)  # match a task with ANY selected skill
            query |= skill_q

        if location:
            query |= Q(location__icontains=location)


        if category:
            query |= Q(category__icontains=category)


        
        if min_budget and max_budget:
            try:
                min_budget = int(min_budget)
                max_budget = int(max_budget)
                query &= Q(budget_min__gte=min_budget) | Q(budget_max__lte=max_budget)
            except ValueError:
                pass

        if query:
            tasks = tasks.filter(query)
        
        sort = sort.lower()
        if sort == "newest":
            tasks = tasks.order_by("-created_at")
        elif sort == "oldest":
            tasks = tasks.order_by("created_at")
        elif sort == "random":
            tasks = tasks.order_by("?")

        paginator = JobPagination()
        paginated_tasks = paginator.paginate_queryset(tasks, request)

        serializer = TaskSerializer(paginated_tasks, many=True, context={'request': request})
        response = paginator.get_paginated_response(serializer.data)
        response.data["skills"] = self._get_all_skills()  # complete, cached skill list
        return response


    def put(self, request, pk):
            try:
                tasks = Task.objects.get(pk=pk)

                print(f"Received data: {request.data}")
                print(f"Task found: {tasks.id}")

                serializer = TaskSerializer(tasks, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)

                else:
                    print(f"Serializer errors: {serializer.errors}")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            except Task.DoesNotExist:

                print(f"Task with pk={pk} not found")
                return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

            except Exception as e:
                print(f"Unexpected error: {e}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    def delete(self, request, pk):

            try:
                task = Task.objects.get(pk=pk)
                log_user_action(request.user, "delete_task", metadata={"task_id": task.id})

                task.delete()

                return Response({"Message": "task delete successfully"}, status=status.HTTP_200_OK)

            except Task.DoesNotExist:
                return Response({"error": "task not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class TaskDetailAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    def get_permissions(self):
        """Assign permissions per HTTP method."""
        if self.request.method == "GET":
            return [AllowAny()]  # Anyone can view task details
        return [IsAuthenticated()]  # Other methods require authentication
    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
            serializer = TaskSerializer(task, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except task.DoesNotExist:
            return Response({"error": "task not found"}, status=status.HTTP_404_NOT_FOUND)

class TaskManageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            tasks = Task.objects.filter(user=request.user)
            serializer = TaskSerializer(tasks, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"Errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class TaskBiddingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:

            task_id = request.data.get("task")
            if TaskBidding.objects.filter(task_id=task_id, freelancer=request.user).exists():
                return Response(
                    {"error": "You have already placed a bid on this task."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = TaskBidsSerializer(data=request.data)
            if serializer.is_valid():
                bid = serializer.save()

                notify_employer_of_bid(bid, request=request)

                log_user_action(request.user, "create_bid", metadata={"task_id": bid.task_id})
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"Errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            
            biddings = TaskBidding.objects.filter(freelancer=request.user)
            serializer = TaskBidsSerializer(biddings, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def put(self, request, pk):
        try:

            taskBidding = TaskBidding.objects.get(pk=pk)
            if taskBidding.status == "accepted":
                return Response({"message": "You Cannot Edit. Bid Already Accepted"}, status=status.HTTP_409_CONFLICT)
            serializer = TaskBidsSerializer(taskBidding, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            taskBidding = TaskBidding.objects.get(pk=pk)
            

            log_user_action(request.user, "delete_bid", metadata={"task_id": taskBidding.task_id})
            
            taskBidding.delete()

            return Response({"message": "Bid Successfully deleted"}, status=status.HTTP_200_OK)

        except TaskBidding.DoesNotExist:
            return Response({"error": "task bid not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TaskBiddingGetAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        try:  
            task = Task.objects.get(pk=pk)
            taskBidding = TaskBidding.objects.filter(task=task, status__in=["pending", "accepted"])
            serializer = TaskBidsSerializer(taskBidding, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OnSJPTaskBiddingGetAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        try:  
            task = Task.objects.get(pk=pk)
            taskBidding = TaskBidding.objects.filter(task=task, status="pending")
            serializer = TaskBidsSerializer(taskBidding, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskBiddingCountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
            taskBidding = TaskBidding.objects.filter(task=task, status__in=["pending", "accepted"])
            taskCount = taskBidding.count()
            return Response({"count": taskCount}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class TaskBiddingAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            with transaction.atomic():
                taskBidding = (
                    TaskBidding.objects.select_related("task")
                    .select_for_update()  # no-op on SQLite, real row lock on Postgres
                    .get(pk=pk)
                )
                task = taskBidding.task

                # Only the task owner may accept a bid on their task
                if task.user != request.user:
                    return Response(
                        {"message": "You are not allowed to accept bids on this task."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # This specific bid is already accepted
                if taskBidding.status == "accepted":
                    return Response({"message": "Bid Already Accepted"}, status=status.HTTP_409_CONFLICT)

                # A task may have only ONE accepted bid
                if TaskBidding.objects.filter(task=task, status="accepted").exclude(pk=pk).exists():
                    return Response(
                        {"message": "This task already has an accepted bid."},
                        status=status.HTTP_409_CONFLICT,
                    )

                # Accept this bid and reject the remaining pending bids on the same task
                taskBidding.status = "accepted"
                taskBidding.save(update_fields=["status", "updated_at"])
                TaskBidding.objects.filter(task=task, status="pending").exclude(pk=pk).update(status="rejected")

            return Response(TaskBidsSerializer(taskBidding).data, status=status.HTTP_200_OK)

        except TaskBidding.DoesNotExist:
            return Response({"message": "Bid not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TaskBiddingRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            taskBidding = TaskBidding.objects.get(pk=pk)
            if taskBidding.status == "rejected":
                return Response({"message": "Bid Already Rejected"}, status=status.HTTP_409_CONFLICT)
            serializer = TaskBidsSerializer(taskBidding, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class TaskBidWonAndJobAppliedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            taskBidWon = TaskBidding.objects.filter(freelancer=request.user, status="accepted")
            taskBidWonCount = taskBidWon.count()

            app = JobApplication.objects.filter(user=request.user)
            JobAppCount = app.count()

            reviewCount = Review.objects.filter(reviewee=request.user).count()

            return Response(
                {"bid_won": taskBidWonCount, "job_app": JobAppCount, "reviews": reviewCount},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





        