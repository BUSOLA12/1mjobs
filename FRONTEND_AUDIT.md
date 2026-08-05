# 1mjobs Frontend Audit

A page-by-page inventory of the user-facing `frontend` app, with a visual-state
rating for each page. Goal: modernize styling and layout only (no logic, routing,
state, or API changes).

- **Stack:** Hireo theme (Bootstrap 5 + `style.css` + `colors/blue.css` + `custom.css`). Brand accent `#2a41e8`.
- **Rating legend:** **Good** (theme-clean or modern-custom) / **Needs minor** (spacing, typography, leftover demo content) / **Needs work** (heavy inline-style, dated patterns, large custom pages).
- Ratings marked (verified) were read in depth; the rest are graded on structural signals and confirmed when each page is opened for work.
- Scope note: this covers the customer-facing `frontend` app. The `adminpanel` staff dashboard (`/site-admin/`, ~25 templates) is a separate surface, not inventoried here.

Last updated: 2026-07-31.

## A. Public & Marketing

| # | Page | Template | Route | Purpose | State |
|---|------|----------|-------|---------|-------|
| 1 | Homepage | frontend/templates/frontend/index.html | `/` | Hero search, categories, featured jobs/cities, freelancers, plans | Needs minor (verified) — reworked, see progress log |
| 2 | Homepage (logged-out) | index-logged-out.html | `/index-logged-out/` | Alt landing for anonymous visitors (1,305 lines) | Needs minor — heavy, likely overlaps #1 |
| 3 | Homepage variant 2 | index-2.html | `/index-2/` | Theme demo homepage variant | Needs review — likely redundant demo |
| 4 | Homepage variant 3 | index-3.html | `/index-3/` | Theme demo homepage variant | Needs review — likely redundant demo |
| 5 | Browse Freelancers | freelancers-grid-layout-full-page.html | `/freelancers/` | Grid of freelancer cards | Needs minor — card component updated (see log) |
| 6 | Browse Jobs | jobs-grid-layout-full-page-map-OpenStreetMap.html | `/jobs/` | Job grid + map | Needs minor — map/filter density |
| 7 | Browse Tasks | tasks-grid-layout-full-page.html | `/tasks/` | Task grid listing | Good (theme) |
| 8 | Job Detail | single-job-page.html | `/job-page/<id>/` | Single job view + apply | Good (theme) |
| 9 | Task Detail | single-task-page.html | `/task-page/<id>/` | Single task view + bid | Good (theme) |
| 10 | Company Profile | single-company-profile.html | `/single/company-profile/<id>/` | Public company page | Good (theme) |
| 11 | Freelancer Profile | single-freelancer-profile.html | `/freelancer-profile/<id>/` | Public freelancer page | Good (theme) |
| 12 | Pricing Plans | pages-pricing-plans.html | `/pricing-plans/` | Subscription plan tiers | Needs minor — cards updated (see log) |
| 13 | Contact | pages-contact.html | `/contact/` | Contact form + map | Good (theme) |
| 14 | Privacy Policy | pages-privacy-policy.html | `/privacy-policy/` | Legal text | Needs minor — long-form typography |
| 15 | Terms of Use | pages-term-of-use.html | `/term-of-use/` | Legal text | Needs minor — long-form typography |
| 16 | 404 | pages-404.html | `/404/` | Not-found page | Good (theme) |

## B. Auth & Account State

| # | Page | Template | Route | Purpose | State |
|---|------|----------|-------|---------|-------|
| 17 | Login | pages-login.html | `/login/` | Email/OAuth sign-in | Needs minor |
| 18 | Register | pages-register.html | `/register/` | Account signup | Needs minor |
| 19 | Request Password Reset | request-reset-password.html | `/reset-password/` | Enter email to reset | Needs minor |
| 20 | Set New Password | reset-password.html | `/reset-password/<uid>/<token>/` | New password form | Needs minor |
| 21 | Unauthorised | unauthorised.html | (invalid reset link) | Error notice | Needs minor — bare 25-line page |
| 22 | Account Suspended | account-suspended.html | `/account-suspended/` | Suspension notice | Needs minor |
| 23 | Verify Identity (KYC) | verify-identity.html | `/dashboard/verify-identity/` | Email + document verification | Needs minor — custom, inline styles |

## C. Dashboard (shared)

| # | Page | Template | Route | Purpose | State |
|---|------|----------|-------|---------|-------|
| 24 | Dashboard Home | dashboard.html | `/dashboard/` | Stats, charts, notifications, orders | Needs work (verified) — leftover demo "Notes", hardcoded chart data |
| 25 | My Profile | dashboard-my-profile.html | `/dashboard/my-profile/` | Edit profile / skills | Needs minor |
| 26 | Settings | dashboard-settings.html | `/dashboard/settings/` | Account, company, password, onboarding | Needs work (verified) — heavy inline-style soup |
| 27 | Messages | dashboard-messages.html | `/dashboard/messages/` | Real-time chat (1,049 lines) | Needs work — large custom chat UI |
| 28 | Bookmarks | dashboard-bookmarks.html | `/dashboard/bookmarks/` | Saved jobs/tasks | Good (theme) |
| 29 | Reviews | dashboard-reviews.html | `/dashboard/reviews/` | Reviews received/given | Good (theme) |

## D. Applications, Bids, Offers & Contracts

| # | Page | Template | Route | Purpose | State |
|---|------|----------|-------|---------|-------|
| 30 | My Applications | dashboard-my-applications.html | `/dashboard/my-applications/` | Freelancer's job applications | Needs minor |
| 31 | My Active Bids | dashboard-my-active-bids.html | `/dashboard/my-active-bids/` | Freelancer's task bids | Needs minor |
| 32 | Offers | offer.html | `/offers/` | Offers sent/received | Good (verified, theme) |
| 33 | Contracts List | dashboard-contracts.html | `/dashboard/contracts/` | List of contracts | Good (verified, theme + status pills) |
| 34 | Contract Detail (Employer) | dashboard-contract-detail-employer.html | `/dashboard/contracts/<id>/` | Employer-side escrow/deliverables | Needs minor (verified) — ~50 inline styles |
| 35 | Contract Detail (Freelancer) | dashboard-contract-detail-freelancer.html | `/dashboard/contracts/<id>/` | Freelancer-side submit/withdraw | Needs minor — same pattern as #34 |
| 36 | Manage Candidates | dashboard-manage-candidates.html | `/dashboard/manage-candidates/<job_id>/` | Review job applicants | Needs minor |
| 37 | Manage Bidders | dashboard-manage-bidders.html | `/dashboard/manage-bidders/<task_id>/` | Review task bids (932 lines) | Needs work — large custom page |

## E. Jobs & Tasks Management (Employer)

| # | Page | Template | Route | Purpose | State |
|---|------|----------|-------|---------|-------|
| 38 | Manage Jobs | dashboard-manage-jobs.html | `/dashboard/manage-jobs/` | Employer's posted jobs | Needs minor |
| 39 | Manage Tasks | dashboard-manage-tasks.html | `/dashboard/manage-tasks/` | Employer's posted tasks | Needs minor |
| 40 | Post a Job | dashboard-post-a-job.html | `/dashboard/post-job/` | Create job form | Needs minor — form spacing/typography |
| 41 | Post a Task | dashboard-post-a-task.html | `/dashboard/post-task/` | Create task form | Needs minor |
| 42 | Edit Job | dashboard-edit-job.html | `/dashboard/edit-job/<id>/` | Edit job form | Needs minor |
| 43 | Edit Task | dashboard-edit-task.html | `/dashboard/edit-task/<id>/` | Edit task form | Needs minor |
| 44 | Post a Company | dashboard-post-a-company.html | `/dashboard/post-a-company/` | Create company profile | Needs minor |
| 45 | Edit / Resubmit Company | company-edit-resubmit.html | `/dashboard/company/edit-resubmit/` | Fix flagged company fields | Needs minor |

## F. Payments & Billing

| # | Page | Template | Route | Purpose | State |
|---|------|----------|-------|---------|-------|
| 46 | Wallet (Freelancer) | wallet.html | `/wallet/` | Balances + transaction history | Good (verified) — modern `wallet-ui.css` |
| 47 | Payments (Employer) | employer-payments.html | `/payments/` | Escrow pipeline + job payments | Good (verified) — modern `wallet-ui.css` |
| 48 | Billing & Subscription | billing-history.html | `/billing/` | Subscription + invoices | Needs minor |
| 49 | Checkout | pages-checkout-page.html | `/checkout/<id>/` | Subscription checkout | Needs minor |
| 50 | Order Confirmation | pages-order-confirmation.html | `/order-confirmation/` | Post-order confirmation | Needs minor |
| 51 | Payment Confirmation | pages-payment-confirmation.html | `/payment-confirmation/` | Escrow payment return page | Needs minor |
| 52 | Invoice | pages-invoice-template.html | `/invoice/<id>/` | Printable invoice | Needs minor |

## G. Admin views (inside the frontend app)

| # | Page | Template | Route | Purpose | State |
|---|------|----------|-------|---------|-------|
| 53 | Admin Dashboard | admin-dashboard.html | `/admin-dashboard/` | Custom admin overview | Needs work — custom, review |
| 54 | Admin Manage Jobs | admin-dashboard-manage-jobs.html | `/admin-manage-job/` | Admin job moderation | Needs minor |

## Housekeeping flags (not blocking)

1. **Dead routes (would 500):** views in `frontend/urls.py` point to templates that do not exist on disk (leftover theme demos): `browse-companies`, `index.htm`, the various `jobs/tasks/freelancers list-layout` and `*-OpenStreetMap` variants, `pages-blog`, `pages-icons-cheatsheet`, `pages-user-interface-elements`.
2. **Unrouted orphan templates:** `employer-payments-details.html`, `freelancer-payments.html` (superseded by Wallet), `pages-pricing-plans(freelancer-employer-version).html`.
3. **Separate admin surface:** the `adminpanel` app (`/site-admin/`) has ~25 of its own templates. Not part of this audit.

## Progress log

### Homepage (`index.html`) — in progress
- **Empty states:** unified all five section empty states into one on-brand component (`.home-empty`) with consistent spacing, brand-blue circular icon, and a real call-to-action per section.
- **Hero:** replaced the three hardcoded fake stat counters with honest, no-data trust points (Secure escrow, Verified members, Post in minutes); tightened headline type and softened the search-card shadow.
- **Footer** (shared partial `partials/footer.html`): rebuilt into a light, freelancer.com-style multi-column layout (brand + social, link columns, newsletter, bottom legal bar). Language toggle removed on request.
- **Pricing / Membership cards** (shared `.pricing-plan`, also on the Pricing page): separated cards with modern price typography, check-marked features, and a deep-blue "recommended" standout.
- **Freelancer cards** (shared `.freelancer`, also on `/freelancers/`): modern card shell (rounded, hairline border, soft shadow, hover lift), squared avatar crop, cleaner stat row, full-width button. Equal-height cards across the carousel (verified: all 482px, buttons full width). PRO members shown as a gold star instead of the text badge.

### Technical notes
- All changes are CSS/markup only; no logic, routes, or API calls touched.
- Shared CSS lives in `frontend/static/css/custom.css`. The stylesheet link in `partials/css_links.html` carries a `?v=N` cache-buster (bump on each CSS change during this work).
- Run `python manage.py collectstatic --noinput` after CSS edits so `staticfiles/` (served by WhiteNoise) stays in sync.
