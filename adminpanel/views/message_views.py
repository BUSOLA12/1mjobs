from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from admins.models import MessageContact


@staff_member_required
def admin_contact_message_list(request):
    messages_qs = MessageContact.objects.all().order_by("-id")

    q = request.GET.get("q")
    if q:
        messages_qs = messages_qs.filter(
            Q(name__icontains=q)
            | Q(email__icontains=q)
            | Q(subject__icontains=q)
            | Q(message__icontains=q)
        )

    paginator = Paginator(messages_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "adminpanel/messages/list.html",
        {"page_obj": page_obj, "q": q or ""},
    )


@staff_member_required
def admin_contact_message_detail(request, pk):
    message = get_object_or_404(MessageContact, pk=pk)
    return render(
        request,
        "adminpanel/messages/detail.html",
        {"message": message},
    )
