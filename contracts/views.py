from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework.parsers import MultiPartParser, FormParser

from ManageJobsTasks.models import JobApplication, TaskBidding
from ManageJobsTasks.utils import validate_job_file
from users.utils import log_user_action

from .models import (
    JobOffer, TaskOffer, Contract, ContractDocument, ProjectSubmission, SubmissionFile,
    Dispute, BillingPeriod, Assignment, AssignmentFile, TerminationRequest,
)
from .serializers import (
    JobOfferSerializer, JobOfferCreateSerializer,
    TaskOfferSerializer, TaskOfferCreateSerializer,
    ContractSerializer, ContractDocumentSerializer, ProjectSubmissionSerializer,
    DisputeSerializer, BillingPeriodSerializer, AssignmentSerializer,
    TerminationRequestSerializer,
)


def _ensure_contract_payment(contract, offer):
    """Create the NOT_INITIATED escrow Payment for a freshly created contract.
    Shared by the Job and Task offer-accept paths. Idempotent."""
    from payments.models import Payment
    Payment.objects.get_or_create(
        contract=contract,
        defaults=dict(
            employer=offer.employer,
            freelancer=offer.freelancer,
            amount=offer.amount,
            status="NOT_INITIATED",
        ),
    )
from .utils import (
    notify_freelancer_of_offer, notify_employer_of_offer_response,
    notify_employer_of_submission, notify_freelancer_work_accepted,
    notify_freelancer_revision_requested, notify_dispute_opened,
    notify_freelancer_of_assignment, notify_employer_of_assignment_submission,
    notify_freelancer_of_assignment_review, notify_termination_requested,
)


class SendJobOfferAPIView(APIView):
    """Employer sends a formal offer to one of their job's candidates.

    Replaces the old bare "accept". The application is NOT accepted here: it is
    accepted only when the freelancer accepts the offer (RespondJobOfferAPIView).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = JobOfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        application = get_object_or_404(
            JobApplication.objects.select_related("job", "user"),
            pk=data["application"],
        )
        job = application.job

        # Only the job owner may send an offer for their job.
        if job.user_id != request.user.id:
            return Response(
                {"message": "You are not allowed to send offers for this job."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Cannot offer on an application that is already resolved.
        if application.status in ("accepted", "completed", "rejected", "cancelled"):
            return Response(
                {"message": f"This application is already {application.status}."},
                status=status.HTTP_409_CONFLICT,
            )

        # At most one live offer per application.
        if JobOffer.objects.filter(
            application=application, status__in=["pending", "accepted"]
        ).exists():
            return Response(
                {"message": "An active offer already exists for this candidate."},
                status=status.HTTP_409_CONFLICT,
            )

        offer = JobOffer.objects.create(
            job=job,
            application=application,
            employer=request.user,
            freelancer=application.user,
            amount=data["amount"],  # monthly rate
            payment_day=data["payment_day"],
            cadence=data.get("cadence") or "monthly",
            meeting_terms=data.get("meeting_terms", ""),
            note=data.get("note", ""),
        )

        notify_freelancer_of_offer(offer, request=request)
        log_user_action(request.user, "send_job_offer", metadata={"offer_id": offer.id})

        return Response(
            {"message": "Offer sent", "offer": JobOfferSerializer(offer).data},
            status=status.HTTP_201_CREATED,
        )


class RespondJobOfferAPIView(APIView):
    """Freelancer accepts or rejects an offer they received.

    On accept, the underlying application is marked accepted and the other
    pending applications / offers on the same job are rejected. (A Contract is
    created here in Phase 3.)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from django.utils import timezone

        action = (request.data.get("action") or "").lower()
        if action not in ("accept", "reject"):
            return Response(
                {"message": "action must be 'accept' or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Accepting a Job offer requires signing the agreement.
        agreed = bool(request.data.get("agreed"))
        if action == "accept" and not agreed:
            return Response(
                {"message": "You must agree to the terms to accept this offer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                offer = (
                    JobOffer.objects.select_related("job", "application")
                    .select_for_update()
                    .get(pk=pk)
                )

                # Only the recipient freelancer may respond.
                if offer.freelancer_id != request.user.id:
                    return Response(
                        {"message": "This offer is not addressed to you."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if offer.status != "pending":
                    return Response(
                        {"message": f"This offer was already {offer.status}."},
                        status=status.HTTP_409_CONFLICT,
                    )

                job = offer.job
                application = offer.application

                if action == "reject":
                    offer.status = "rejected"
                    offer.save(update_fields=["status", "updated_at"])
                else:
                    # A job may have only one accepted applicant.
                    if JobApplication.objects.filter(
                        job=job, status__in=["accepted", "completed"]
                    ).exclude(pk=application.pk).exists():
                        return Response(
                            {"message": "This job already has an accepted applicant."},
                            status=status.HTTP_409_CONFLICT,
                        )

                    # Freelancer signs the agreement at accept time.
                    offer.status = "accepted"
                    offer.agreement_signed_at = timezone.now()
                    offer.save(update_fields=["status", "agreement_signed_at", "updated_at"])

                    application.status = "accepted"
                    application.save(update_fields=["status"])

                    # Reject the remaining pending applications and offers on this job.
                    JobApplication.objects.filter(
                        job=job, status="pending"
                    ).exclude(pk=application.pk).update(status="rejected")
                    JobOffer.objects.filter(
                        job=job, status="pending"
                    ).exclude(pk=offer.pk).update(status="withdrawn")

                    # Create the long-term recurring contract (active) and its
                    # first billing period (awaiting funding).
                    from .billing import create_first_period

                    contract, created = Contract.objects.get_or_create(
                        offer=offer,
                        defaults=dict(
                            job=job,
                            application=application,
                            employer=offer.employer,
                            freelancer=offer.freelancer,
                            amount=offer.amount,
                            terms=offer.note,
                            status="active",
                            is_recurring=True,
                            monthly_rate=offer.amount,
                            payment_day=offer.payment_day,
                            cadence=offer.cadence or "monthly",
                            meeting_terms=offer.meeting_terms,
                            agreement_signed_at=offer.agreement_signed_at,
                        ),
                    )
                    if created:
                        create_first_period(contract)

            notify_employer_of_offer_response(offer, request=request)
            log_user_action(
                request.user, "respond_job_offer",
                metadata={"offer_id": offer.id, "action": action},
            )
            return Response(
                {"message": f"Offer {offer.status}", "offer": JobOfferSerializer(offer).data},
                status=status.HTTP_200_OK,
            )

        except JobOffer.DoesNotExist:
            return Response({"message": "Offer not found"}, status=status.HTTP_404_NOT_FOUND)


class OffersReceivedListAPIView(APIView):
    """Offers the logged-in freelancer has received."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = JobOffer.objects.filter(freelancer=request.user).select_related("job")
        return Response(JobOfferSerializer(offers, many=True).data)


class OffersSentListAPIView(APIView):
    """Offers the logged-in employer has sent."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = JobOffer.objects.filter(employer=request.user).select_related("job")
        return Response(JobOfferSerializer(offers, many=True).data)


# ---------------------------------------------------------------------------
# Task offers (task-side twin of the Job offer flow)
# ---------------------------------------------------------------------------

class SendTaskOfferAPIView(APIView):
    """Employer sends a formal offer to one of their task's bidders."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TaskOfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        bidding = get_object_or_404(
            TaskBidding.objects.select_related("task", "freelancer"),
            pk=data["bidding"],
        )
        task = bidding.task

        if task.user_id != request.user.id:
            return Response(
                {"message": "You are not allowed to send offers for this task."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if bidding.status in ("accepted", "rejected", "cancelled"):
            return Response(
                {"message": f"This bid is already {bidding.status}."},
                status=status.HTTP_409_CONFLICT,
            )
        if TaskOffer.objects.filter(bidding=bidding, status__in=["pending", "accepted"]).exists():
            return Response(
                {"message": "An active offer already exists for this bidder."},
                status=status.HTTP_409_CONFLICT,
            )

        offer = TaskOffer.objects.create(
            task=task,
            bidding=bidding,
            employer=request.user,
            freelancer=bidding.freelancer,
            amount=data["amount"],
            delivery_days=data["delivery_days"],
            note=data.get("note", ""),
        )

        notify_freelancer_of_offer(offer, request=request)
        log_user_action(request.user, "send_task_offer", metadata={"offer_id": offer.id})

        return Response(
            {"message": "Offer sent", "offer": TaskOfferSerializer(offer).data},
            status=status.HTTP_201_CREATED,
        )


class RespondTaskOfferAPIView(APIView):
    """Freelancer accepts or rejects a task offer. On accept, the bidding is
    marked accepted, the task's other pending bids/offers are rejected, and a
    Contract (task-origin) + escrow Payment are created."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        action = (request.data.get("action") or "").lower()
        if action not in ("accept", "reject"):
            return Response(
                {"message": "action must be 'accept' or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                offer = (
                    TaskOffer.objects.select_related("task", "bidding")
                    .select_for_update()
                    .get(pk=pk)
                )

                if offer.freelancer_id != request.user.id:
                    return Response(
                        {"message": "This offer is not addressed to you."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                if offer.status != "pending":
                    return Response(
                        {"message": f"This offer was already {offer.status}."},
                        status=status.HTTP_409_CONFLICT,
                    )

                task = offer.task
                bidding = offer.bidding

                if action == "reject":
                    offer.status = "rejected"
                    offer.save(update_fields=["status", "updated_at"])
                else:
                    if TaskBidding.objects.filter(
                        task=task, status="accepted"
                    ).exclude(pk=bidding.pk).exists():
                        return Response(
                            {"message": "This task already has an accepted bid."},
                            status=status.HTTP_409_CONFLICT,
                        )

                    offer.status = "accepted"
                    offer.save(update_fields=["status", "updated_at"])

                    bidding.status = "accepted"
                    bidding.save(update_fields=["status"])

                    TaskBidding.objects.filter(
                        task=task, status="pending"
                    ).exclude(pk=bidding.pk).update(status="rejected")
                    TaskOffer.objects.filter(
                        task=task, status="pending"
                    ).exclude(pk=offer.pk).update(status="withdrawn")

                    contract, _ = Contract.objects.get_or_create(
                        task_offer=offer,
                        defaults=dict(
                            task=task,
                            task_bidding=bidding,
                            employer=offer.employer,
                            freelancer=offer.freelancer,
                            amount=offer.amount,
                            delivery_days=offer.delivery_days,
                            terms=offer.note,
                        ),
                    )
                    _ensure_contract_payment(contract, offer)

            notify_employer_of_offer_response(offer, request=request)
            log_user_action(
                request.user, "respond_task_offer",
                metadata={"offer_id": offer.id, "action": action},
            )
            return Response(
                {"message": f"Offer {offer.status}", "offer": TaskOfferSerializer(offer).data},
                status=status.HTTP_200_OK,
            )

        except TaskOffer.DoesNotExist:
            return Response({"message": "Offer not found"}, status=status.HTTP_404_NOT_FOUND)


class TaskOffersReceivedListAPIView(APIView):
    """Task offers the logged-in freelancer has received."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = TaskOffer.objects.filter(freelancer=request.user).select_related("task")
        return Response(TaskOfferSerializer(offers, many=True).data)


class TaskOffersSentListAPIView(APIView):
    """Task offers the logged-in employer has sent."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = TaskOffer.objects.filter(employer=request.user).select_related("task")
        return Response(TaskOfferSerializer(offers, many=True).data)


def _contract_for_party_or_403(pk, user):
    """Fetch a contract only if `user` is the employer or freelancer on it.
    Returns (contract, None) or (None, Response)."""
    contract = (
        Contract.objects.select_related("job", "employer", "freelancer")
        .filter(pk=pk).first()
    )
    if contract is None:
        return None, Response({"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
    if user.id not in (contract.employer_id, contract.freelancer_id):
        return None, Response({"message": "This is not your contract."}, status=status.HTTP_403_FORBIDDEN)
    return contract, None


class ContractListAPIView(APIView):
    """All contracts the logged-in user is a party to (either side)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        contracts = (
            Contract.objects.filter(Q(employer=request.user) | Q(freelancer=request.user))
            .select_related("job", "employer", "freelancer")
            .prefetch_related("documents", "payments")
        )
        return Response(ContractSerializer(contracts, many=True, context={"request": request}).data)


class ContractDetailAPIView(APIView):
    """A single contract (parties only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        contract, err = _contract_for_party_or_403(pk, request.user)
        if err:
            return err
        return Response(ContractSerializer(contract, context={"request": request}).data)


class FundContractAPIView(APIView):
    """Employer funds the contract escrow. Reuses the shared PaymentService +
    African Money, returning the hosted payment URL. Idempotent: reuses the
    contract's not-yet-released payment instead of creating duplicates."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from payments.models import Payment
        from payments.services.payment_service import PaymentService
        from payments.services.africanmoney_service import AfricanMoneyError

        contract, err = _contract_for_party_or_403(pk, request.user)
        if err:
            return err

        if contract.employer_id != request.user.id:
            return Response({"message": "Only the employer funds escrow."}, status=status.HTTP_403_FORBIDDEN)
        if contract.status not in ("awaiting_funding",):
            return Response({"message": f"Contract is already {contract.status}."}, status=status.HTTP_409_CONFLICT)

        payment = contract.payments.exclude(status="RELEASED").order_by("-created_at").first()
        if not payment:
            payment = Payment.objects.create(
                employer=contract.employer, freelancer=contract.freelancer,
                contract=contract, amount=contract.amount, status="NOT_INITIATED",
            )

        if payment.status in ("NOT_INITIATED", "FAILED"):
            try:
                payment = PaymentService.initiate_payment(payment)
            except (AfricanMoneyError, ValueError) as e:
                return Response({"message": f"Could not start payment: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "payment_id": payment.id,
            "payment_url": payment.payment_url,
            "status": payment.status,
        })


class FundPeriodAPIView(APIView):
    """Employer funds a single billing period's escrow (recurring Job contracts).
    Mirrors FundContractAPIView but targets a BillingPeriod. Idempotent."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from payments.models import Payment
        from payments.services.payment_service import PaymentService
        from payments.services.africanmoney_service import AfricanMoneyError

        period = get_object_or_404(BillingPeriod.objects.select_related("contract"), pk=pk)
        contract = period.contract

        if contract.employer_id != request.user.id:
            return Response({"message": "Only the employer funds escrow."}, status=status.HTTP_403_FORBIDDEN)
        if period.status != "awaiting_funding":
            return Response({"message": f"This period is already {period.status}."}, status=status.HTTP_409_CONFLICT)

        payment = period.payments.exclude(status="RELEASED").order_by("-created_at").first()
        if not payment:
            payment = Payment.objects.create(
                employer=contract.employer, freelancer=contract.freelancer,
                contract=contract, period=period, amount=period.amount, status="NOT_INITIATED",
            )

        if payment.status in ("NOT_INITIATED", "FAILED"):
            try:
                payment = PaymentService.initiate_payment(payment)
            except (AfricanMoneyError, ValueError) as e:
                return Response({"message": f"Could not start payment: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "payment_id": payment.id,
            "payment_url": payment.payment_url,
            "status": payment.status,
            "period_id": period.id,
        })


class ContractDocumentUploadAPIView(APIView):
    """Attach a document to a contract. Either party may upload; both can view."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        contract, err = _contract_for_party_or_403(pk, request.user)
        if err:
            return err

        files = request.FILES.getlist("file")
        if not files:
            return Response({"message": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate every file first so a single bad file rejects the whole batch
        # (nothing is saved unless all files pass).
        for uploaded in files:
            error = validate_job_file(uploaded)
            if error:
                return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)

        label = request.data.get("label", "")
        docs = [
            ContractDocument.objects.create(
                contract=contract, uploaded_by=request.user, file=uploaded, label=label,
            )
            for uploaded in files
        ]
        return Response(
            ContractDocumentSerializer(docs, many=True, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class SubmitProjectAPIView(APIView):
    """Freelancer submits (or resubmits) their work on a funded contract."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        contract, err = _contract_for_party_or_403(pk, request.user)
        if err:
            return err

        if contract.freelancer_id != request.user.id:
            return Response({"message": "Only the freelancer can submit work."}, status=status.HTTP_403_FORBIDDEN)
        if contract.status not in ("funded", "revision_requested"):
            return Response(
                {"message": f"You can't submit work while the contract is {contract.status}."},
                status=status.HTTP_409_CONFLICT,
            )

        message = (request.data.get("message") or "").strip()
        files = request.FILES.getlist("file")
        if not files and not message:
            return Response({"message": "Add a message or at least one file."}, status=status.HTTP_400_BAD_REQUEST)
        for f in files:
            error = validate_job_file(f)
            if error:
                return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            last = contract.submissions.order_by("-version").first()
            version = (last.version + 1) if last else 1
            submission = ProjectSubmission.objects.create(
                contract=contract, message=message, version=version,
            )
            for f in files:
                SubmissionFile.objects.create(submission=submission, file=f)
            contract.status = "submitted"
            contract.save(update_fields=["status", "updated_at"])

        notify_employer_of_submission(contract, submission, request=request)
        log_user_action(request.user, "submit_project", metadata={"contract_id": contract.id, "version": version})
        return Response(
            {"message": "Work submitted", "submission": ProjectSubmissionSerializer(submission, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )


class ReviewSubmissionAPIView(APIView):
    """Employer reviews the submitted work: accept (release escrow),
    request_change (send back), or reject (open a dispute)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from payments.models import Payment
        from payments.services.payment_service import PaymentService

        action = (request.data.get("action") or "").lower()
        if action not in ("accept", "request_change", "reject"):
            return Response(
                {"message": "action must be 'accept', 'request_change', or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract, err = _contract_for_party_or_403(pk, request.user)
        if err:
            return err
        if contract.employer_id != request.user.id:
            return Response({"message": "Only the employer can review the work."}, status=status.HTTP_403_FORBIDDEN)
        if contract.status not in ("submitted", "in_review"):
            return Response(
                {"message": f"Nothing to review while the contract is {contract.status}."},
                status=status.HTTP_409_CONFLICT,
            )

        if action == "request_change":
            note = (request.data.get("note") or "").strip()
            files = request.FILES.getlist("file")
            for f in files:
                error = validate_job_file(f)
                if error:
                    return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                contract.status = "revision_requested"
                contract.review_note = note
                contract.save(update_fields=["status", "review_note", "updated_at"])
                # Any screenshots/docs the employer attaches are stored as contract
                # documents so the freelancer can download them (labelled clearly).
                for f in files:
                    ContractDocument.objects.create(
                        contract=contract, uploaded_by=request.user, file=f, label="Change request",
                    )
            notify_freelancer_revision_requested(contract, note, request=request)
            log_user_action(request.user, "request_change", metadata={"contract_id": contract.id})
            return Response({"message": "Change requested", "status": contract.status})

        if action == "reject":
            reason = (request.data.get("reason") or "").strip()
            if not reason:
                return Response({"message": "A reason is required to reject."}, status=status.HTTP_400_BAD_REQUEST)
            files = request.FILES.getlist("file")
            for f in files:
                error = validate_job_file(f)
                if error:
                    return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                dispute = Dispute.objects.create(contract=contract, raised_by=request.user, reason=reason)
                contract.status = "disputed"
                contract.save(update_fields=["status", "updated_at"])
                for f in files:
                    ContractDocument.objects.create(
                        contract=contract, uploaded_by=request.user, file=f, label="Dispute evidence",
                    )
            notify_dispute_opened(dispute, request=request)
            log_user_action(request.user, "reject_submission", metadata={"contract_id": contract.id, "dispute_id": dispute.id})
            return Response({"message": "Work rejected, dispute opened", "status": contract.status}, status=status.HTTP_201_CREATED)

        # accept -> release escrow to the freelancer
        with transaction.atomic():
            payment = contract.payments.select_for_update().filter(status="ESCROWED").order_by("-created_at").first()
            if not payment:
                return Response({"message": "No escrowed payment to release."}, status=status.HTTP_409_CONFLICT)
            payment = PaymentService.release_payment(payment)

            contract.status = "completed"
            contract.save(update_fields=["status", "updated_at"])
            if contract.application_id:
                type(contract.application).objects.filter(pk=contract.application_id).update(status="completed")

        notify_freelancer_work_accepted(contract, payment.net_amount, request=request)
        log_user_action(request.user, "accept_submission", metadata={"contract_id": contract.id, "payment_id": payment.id})
        return Response({
            "message": "Work accepted, payment released",
            "status": contract.status,
            "gross": payment.amount,
            "commission": payment.commission_amount,
            "vat": payment.vat_amount,
            "net": payment.net_amount,
        })


class RaiseDisputeAPIView(APIView):
    """Either party opens a dispute on a contract (e.g. the freelancer contests
    a revision request). Resolved manually by an admin."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        contract, err = _contract_for_party_or_403(pk, request.user)
        if err:
            return err
        if contract.status in ("completed", "cancelled"):
            return Response({"message": f"Can't dispute a {contract.status} contract."}, status=status.HTTP_409_CONFLICT)

        reason = (request.data.get("reason") or "").strip()
        if not reason:
            return Response({"message": "A reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist("file")
        for f in files:
            error = validate_job_file(f)
            if error:
                return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            dispute = Dispute.objects.create(contract=contract, raised_by=request.user, reason=reason)
            contract.status = "disputed"
            contract.save(update_fields=["status", "updated_at"])
            # Optional evidence is stored as contract documents so both parties
            # and the admin reviewing the dispute can see it.
            for f in files:
                ContractDocument.objects.create(
                    contract=contract, uploaded_by=request.user, file=f, label="Dispute evidence",
                )
        notify_dispute_opened(dispute, request=request)
        log_user_action(request.user, "raise_dispute", metadata={"contract_id": contract.id, "dispute_id": dispute.id})
        return Response(
            {"message": "Dispute opened", "dispute": DisputeSerializer(dispute).data},
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Assignments (recurring Job contracts): employer hands out work units, the
# freelancer submits, the employer accepts or requests changes. Payment stays
# period-based, so these do not move money.
# ---------------------------------------------------------------------------

class CreateAssignmentAPIView(APIView):
    """Employer creates an assignment on a recurring contract (optional brief files)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        contract, err = _contract_for_party_or_403(pk, request.user)
        if err:
            return err
        if contract.employer_id != request.user.id:
            return Response({"message": "Only the employer can create assignments."}, status=status.HTTP_403_FORBIDDEN)
        if not contract.is_recurring:
            return Response({"message": "Assignments are only for long-term job contracts."}, status=status.HTTP_400_BAD_REQUEST)
        if contract.status in ("terminated", "ended", "cancelled"):
            return Response({"message": f"Contract is {contract.status}."}, status=status.HTTP_409_CONFLICT)

        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"message": "A title is required."}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist("file")
        for f in files:
            error = validate_job_file(f)
            if error:
                return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)

        # Attach to the current active period, if any.
        period = contract.periods.filter(status__in=["funded", "in_review"]).order_by("-period_number").first()

        with transaction.atomic():
            assignment = Assignment.objects.create(
                contract=contract, period=period, title=title,
                description=request.data.get("description", ""), created_by=request.user,
            )
            for f in files:
                AssignmentFile.objects.create(assignment=assignment, file=f)

        notify_freelancer_of_assignment(assignment, request=request)
        log_user_action(request.user, "create_assignment", metadata={"assignment_id": assignment.id})
        return Response(
            AssignmentSerializer(assignment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


def _assignment_for_party_or_403(pk, user):
    assignment = (
        Assignment.objects.select_related("contract", "contract__employer", "contract__freelancer")
        .filter(pk=pk).first()
    )
    if assignment is None:
        return None, Response({"message": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
    c = assignment.contract
    if user.id not in (c.employer_id, c.freelancer_id):
        return None, Response({"message": "This is not your contract."}, status=status.HTTP_403_FORBIDDEN)
    return assignment, None


class SubmitAssignmentAPIView(APIView):
    """Freelancer submits (or resubmits) deliverables for an assignment."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        assignment, err = _assignment_for_party_or_403(pk, request.user)
        if err:
            return err
        contract = assignment.contract
        if contract.freelancer_id != request.user.id:
            return Response({"message": "Only the freelancer can submit."}, status=status.HTTP_403_FORBIDDEN)
        if assignment.status == "accepted":
            return Response({"message": "This assignment is already accepted."}, status=status.HTTP_409_CONFLICT)

        message = (request.data.get("message") or "").strip()
        files = request.FILES.getlist("file")
        if not message and not files:
            return Response({"message": "Add a message or at least one file."}, status=status.HTTP_400_BAD_REQUEST)
        for f in files:
            error = validate_job_file(f)
            if error:
                return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            version = assignment.submissions.count() + 1
            submission = ProjectSubmission.objects.create(
                contract=contract, assignment=assignment, message=message, version=version,
            )
            for f in files:
                SubmissionFile.objects.create(submission=submission, file=f)
            assignment.status = "submitted"
            assignment.save(update_fields=["status", "updated_at"])

        notify_employer_of_assignment_submission(assignment, request=request)
        log_user_action(request.user, "submit_assignment", metadata={"assignment_id": assignment.id, "version": version})
        return Response(
            AssignmentSerializer(assignment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ReviewAssignmentAPIView(APIView):
    """Employer accepts an assignment or requests changes."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        action = (request.data.get("action") or "").lower()
        if action not in ("accept", "request_change"):
            return Response({"message": "action must be 'accept' or 'request_change'."}, status=status.HTTP_400_BAD_REQUEST)

        assignment, err = _assignment_for_party_or_403(pk, request.user)
        if err:
            return err
        if assignment.contract.employer_id != request.user.id:
            return Response({"message": "Only the employer can review assignments."}, status=status.HTTP_403_FORBIDDEN)
        if assignment.status != "submitted":
            return Response({"message": f"Nothing to review (assignment is {assignment.status})."}, status=status.HTTP_409_CONFLICT)

        if action == "accept":
            assignment.status = "accepted"
            assignment.save(update_fields=["status", "updated_at"])
        else:
            assignment.review_note = (request.data.get("note") or "").strip()
            assignment.status = "changes_requested"
            assignment.save(update_fields=["status", "review_note", "updated_at"])

        notify_freelancer_of_assignment_review(assignment, action, request=request)
        log_user_action(request.user, "review_assignment", metadata={"assignment_id": assignment.id, "action": action})
        return Response(
            AssignmentSerializer(assignment, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class RequestTerminationAPIView(APIView):
    """Either party requests to end a recurring contract. This never ends the
    contract directly: it records a pending TerminationRequest and flags the
    contract 'pending_termination' for an admin to review and execute."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        contract, err = _contract_for_party_or_403(pk, request.user)
        if err:
            return err
        if not contract.is_recurring:
            return Response({"message": "Only long-term job contracts can be terminated this way."}, status=status.HTTP_400_BAD_REQUEST)
        if contract.status in ("terminated", "ended", "cancelled", "pending_termination"):
            return Response({"message": f"Contract is {contract.status}."}, status=status.HTTP_409_CONFLICT)

        reason = (request.data.get("reason") or "").strip()
        if not reason:
            return Response({"message": "A reason is required to request termination."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            termination = TerminationRequest.objects.create(
                contract=contract, requested_by=request.user, reason=reason,
            )
            contract.status = "pending_termination"
            contract.save(update_fields=["status", "updated_at"])

        notify_termination_requested(termination, request=request)
        log_user_action(request.user, "request_termination", metadata={"contract_id": contract.id, "termination_id": termination.id})
        return Response(
            {"message": "Termination requested; our team will review it.",
             "termination": TerminationRequestSerializer(termination).data},
            status=status.HTTP_201_CREATED,
        )
