from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from users.utils import log_user_action
from .serializers import JobSerializer, TaskSerializer, JobApplicationSerializer, TaskBidsSerializer
from .models import Job, Task, JobApplication, TaskBidding
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
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
        if self.request.method == "POST":
            return [IsAuthenticated()]  # Only logged-in users can create Jobs
        return [AllowAny()] 

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save(user=request.user)

            log_user_action(request.user, "create_job", metadata={"job_id": job.id})
            return Response({"message": "Job created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
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

        jobs = Job.objects.all()
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

        if sort == "Newest":
            jobs = jobs.order_by("-created_at")
        elif sort == "Oldest":
            jobs = jobs.order_by("created_at")
        elif sort == "Random":
            jobs = jobs.order_by("?")

        paginator = JobPagination()
        paginated_jobs = paginator.paginate_queryset(jobs, request)

                
        serializer = JobSerializer(paginated_jobs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    
    def put(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)

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

        jobs = Job.objects.all()
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
        
        if sort == "Newest":
            jobs = jobs.order_by("-created_at")
        elif sort == "Oldest":
            jobs = jobs.order_by("created_at")
        elif sort == "Random":
            jobs = jobs.order_by("?")

        paginator = JobPagination()
        paginated_jobs = paginator.paginate_queryset(jobs, request)

                
        serializer = JobSerializer(paginated_jobs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


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
            serializer = JobApplicationSerializer(data=request.data)
            if serializer.is_valid():
                application = serializer.save()

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
            applications = JobApplication.objects.filter(job=jobId)
            serializer = JobApplicationSerializer(applications, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class JobApplicationDeleteAPIView(APIView):
    def delete(self, request, pk):
        try:
            application = JobApplication.objects.get(pk=pk)

            log_user_action(request.user, "delete_job_application", metadata={"application_id": application.id})
            application.delete()
            return Response({"message": "Job Application deleted successfully"}, status=status.HTTP_200_OK)
        except JobApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Deletion failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
            similar_jobs = Job.objects.filter(category=job.category).exclude(pk=pk)[:5]

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

    def get_permissions(self):
        """Assign permissions per HTTP method."""
        if self.request.method == "POST":
            return [IsAuthenticated()]  # Only logged-in users can create tasks
        return [AllowAny()] 
    def post(self, request):

        try:
            serializer = TaskSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                task = serializer.save()

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
        skills = request.GET.get('skills', "")
        category = request.GET.get('category', "")
        location = request.GET.get('location', "")

        tasks = Task.objects.all()
        query = Q()

        if search:
            query |= (
                Q(project_name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(skills__icontains=search)
            )

        if skills:
            query |= Q(skills__icontains=skills)

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
        
        if sort == "Newest":
            tasks = tasks.order_by("-created_at")
        elif sort == "Oldest":
            tasks = tasks.order_by("created_at")
        elif sort == "Random":
            tasks = tasks.order_by("?")

        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


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

            serializer = TaskBidsSerializer(data=request.data)
            if serializer.is_valid():
                task = serializer.save()

                log_user_action(request.user, "create_bid", metadata={"task_id": task.id})
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
            taskBidding = TaskBidding.objects.get(pk=pk)
            if taskBidding.status == "accepted":
                return Response({"message": "Bid Already Accepted"}, status=status.HTTP_409_CONFLICT)
            serializer = TaskBidsSerializer(taskBidding, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

            return Response({"bid_won": taskBidWonCount, "job_app": JobAppCount}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





        