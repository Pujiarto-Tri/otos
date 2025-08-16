from otosapp.models import Test
from django.contrib.auth import get_user_model

# Ganti dengan username/email user yang ingin dicek
def print_user_test_scores(username_or_email):
    User = get_user_model()
    try:
        user = User.objects.get(username=username_or_email)
    except User.DoesNotExist:
        try:
            user = User.objects.get(email=username_or_email)
        except User.DoesNotExist:
            print('User not found')
            return
    tests = Test.objects.filter(student=user, is_submitted=True, tryout_package__isnull=False)
    print(f"Total tests: {tests.count()}")
    for t in tests:
        print(f"Test ID: {t.id}, Score: {t.score}, Submitted: {t.is_submitted}, Tryout: {t.tryout_package}")

# Contoh pemakaian:
# print_user_test_scores('username_atau_email_user')
