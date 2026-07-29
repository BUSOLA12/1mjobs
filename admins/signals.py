# Contact-message admin notifications are sent from `admins.views.message_contact_view`
# (see `_notify_admin_of_message`), where the request is available so the "view
# message" link can be built from the actual host. This module is intentionally
# left without a post_save email receiver to avoid sending the email twice.
