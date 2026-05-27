
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Bookmark
from .serializers import BookmarkCreateSerializer, BookmarkListSerializer

class BookmarkCreateView(generics.CreateAPIView):
    serializer_class = BookmarkCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

class BookmarkListView(generics.RetrieveAPIView):
    serializer_class = BookmarkListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class BookmarkDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Bookmark.objects.all()

    def delete(self, request, *args, **kwargs):
        bookmark_id = kwargs.get("id")
        bookmark = Bookmark.objects.filter(id=bookmark_id, user=request.user).first()
        if not bookmark:
            return Response({"detail": "Bookmark not found."}, status=status.HTTP_404_NOT_FOUND)
        bookmark.delete()
        return Response({"detail": "Bookmark deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
