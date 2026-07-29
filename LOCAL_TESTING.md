# Local Testing Guide: The Revenue Model

This walks you through testing the whole revenue model in a browser, as a normal
user, using a short story. Payments run through African Money (Flutterwave in
**test mode**), so no real money moves.

> Run everything from `1mjobs/1mjobs/` (the folder with `manage.py`) with the
> virtualenv active.

---

## 1. Setup

### 1a. `.env`

Copy `.env.example` to `.env` and set at least these:

```
SECRET_KEY=any-dev-value-here
DEBUG=True

# IMPORTANT: use localhost so the payment page returns to your LOCAL server
# after paying. If this points at the Fly domain, the redirect won't come back.
DOMAIN=localhost:8000

# African Money (Flutterwave test-mode) credentials:
AFRICANMONEY_API_KEY=your-test-api-key
AFRICANMONEY_SECRET_KEY=your-test-secret-key

# OTP / 2FA codes print to the terminal instead of sending email:
EMAIL_USE_CONSOLE=True
```

### 1b. Migrate, seed, run

```powershell
env\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_plans            # creates the Free + Pro plans
python manage.py seed_test_accounts    # creates the test users + data
python manage.py runserver
```

Then open http://localhost:8000/.

> If your changes don't show up, an old `runserver` may still own port 8000.
> Stop it and restart.

### 1c. Your test logins (password `password123` for all)

| Login | Who | Pro? |
|-------|-----|------|
| free.freelancer@test.local | Freelancer | No |
| pro.freelancer@test.local | Freelancer | **Yes** |
| free.employer@test.local | Employer | No |
| pro.employer@test.local | Employer | **Yes** |

Log in at http://localhost:8000/login/. To switch users, log out and log back in.

---

## 2. The story

> "One Million Jobs has two paying customers: a freelancer and an employer who
> both upgrade to Pro, and a platform that takes 10% of every job payment."

### Scene 1: Pro freelancers stand out (search boost + badge)

Open **http://localhost:8000/freelancers/** (no login needed).
- **See:** `pro.freelancer` shows a gold **PRO** badge and sits at the top; `free.freelancer` has no badge and ranks below.

### Scene 2: Pro freelancers get early access to new jobs

The seed created one "old" job (visible to everyone) and one "fresh" job posted
just now (Pro-only for its first 12 hours).
1. Log in as **free.freelancer** → open **/jobs/**. **See:** "TEST Fresh Job" is **not** listed.
2. Log out, log in as **pro.freelancer** → open **/jobs/**. **See:** "TEST Fresh Job" **is** listed.

### Scene 3: "Who viewed your profile"

As **pro.freelancer**, open **/dashboard/**.
- **See:** a "Who Viewed Your Profile" panel listing the people who viewed you.

Now log in as **free.freelancer**, open **/dashboard/**.
- **See:** the same panel shows an **Upgrade to Pro** prompt instead (this is the 403 turned into an upsell).

### Scene 4: Employers feature a job (Pro)

As **pro.employer**, open **/dashboard/post-job/**.
- **See:** a "**Feature this job** PRO" checkbox. Fill the form, tick it, post.
- **Then** open **/jobs/**: your featured job sits at the top, and it also shows
  in the Featured Jobs section on the home page.

Log in as **free.employer**, open **/dashboard/post-job/**.
- **See:** no "Feature this job" checkbox (free tier).

### Scene 5: Premium employer badge

Open **/jobs/** (any visitor).
- **See:** jobs posted by `pro.employer` show a **PRO** premium badge next to the
  company name.

### Scene 6: Hiring analytics (Pro)

As **pro.employer**, open **/dashboard/**.
- **See:** a "Hiring Analytics" panel (applications / accepted / bids funnel +
  top jobs). As **free.employer**, the same panel shows the Upgrade prompt.

### Scene 7: Direct offers (Pro)

As **pro.employer**, open **/offers/** and send an offer to a freelancer → works.
As **free.employer**, the same action is blocked with a subscription message.

### Scene 8: Buy Pro with a test card (optional)

As **free.freelancer**, open **/pricing-plans/** → choose **Freelancer Pro** →
you're taken to the African Money (Flutterwave **test**) page → pay with a
**Flutterwave test card** → you return to **/order-confirmation/** and your
account becomes Pro (re-check Scenes 1-3).

> Flutterwave test card to start with (confirm against whatever the test
> checkout page shows): `4187 4274 1556 4246`, CVV `828`, expiry `09/32`,
> PIN `3310`, OTP `12345`. Successful-transaction test cards are listed in
> Flutterwave's docs.

### Scene 9: A job payment and the 10% commission (the money story)

**Part A: employer pays the freelancer (money in → escrow).**
1. Log in as **pro.employer**. Open the task's bidders page: **/dashboard/manage-bidders/`<taskId>`/** (the seed printed the task id; it's the "TEST Task to Pay").
2. The freelancer's bid is already **accepted**, so you'll see a **Pay Freelancer** button. Click it.
3. You're sent to the African Money (Flutterwave test) page → pay with a test card.
4. You return to **/payment-confirmation/**, which verifies the payment. Status becomes **ESCROWED**.
5. Log in as **pro.freelancer**, open **/payments/** (My Earnings). **See:** the amount now sits in **Pending balance** (held in escrow).

**Part B: employer releases the funds (the 10% split).**
1. Log back in as **pro.employer**, open **/payments/**.
2. The escrowed payment shows a **Release Funds** button. Click it and confirm.
3. **See:** a message that the platform kept 10% and the rest went to the freelancer.
4. Log in as **pro.freelancer**, open **/payments/**. **See:** the **Available balance**
   rose by **90%** of the payment, and the Transactions list shows a
   "Payment received" (net) row and a "Platform fee" row.

> **Shortcut (no browser payment needed):** the seed also created an already-escrowed
> payment worth ₦10,000. You can release it from **pro.employer**'s `/payments/`
> page (Release Funds), or from the shell:
>
> ```powershell
> python manage.py shell
> ```
> ```python
> from payments.models import Payment
> from payments.services.payment_service import PaymentService
> p = Payment.objects.get(status="ESCROWED", employer__email="pro.employer@test.local")
> PaymentService.release_payment(p); p.refresh_from_db()
> print("gross", p.amount, "commission", p.commission_amount, "net", p.net_amount)
> # -> gross 10000.00 commission 1000.00 net 9000.00
> ```

---

## 3. What "passing" looks like

- [ ] PRO badge + top ranking for the Pro freelancer in the directory.
- [ ] Fresh job hidden from the free freelancer, visible to the Pro freelancer.
- [ ] "Who viewed your profile" list for Pro; upgrade prompt for free.
- [ ] "Feature this job" checkbox for the Pro employer only; featured job tops the list.
- [ ] PRO premium badge on the Pro employer's job cards.
- [ ] Hiring Analytics panel for Pro employer; upgrade prompt for free.
- [ ] Direct offer works for Pro employer, blocked for free.
- [ ] (Optional) Buying Pro with a test card upgrades the account.
- [ ] Paying a freelancer moves money to **pending** (escrow); releasing splits it
      **10% platform / 90% freelancer** and shows the CREDIT + FEE transactions.

---

## 4. Reset

Re-run the seed anytime (it's idempotent):

```powershell
python manage.py seed_test_accounts
```

To remove the test accounts and their data without touching real data:

```python
# python manage.py shell
from django.contrib.auth import get_user_model
get_user_model().objects.filter(email__endswith="@test.local").delete()
```
