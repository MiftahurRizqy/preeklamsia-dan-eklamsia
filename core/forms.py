# core/forms.py

from allauth.account.forms import LoginForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm

# Form Login kustom untuk menampilkan tombol Google
class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        # Menambahkan kelas form-control bootstrap pada field
        self.fields['login'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

# Form Signup kustom (opsional, bisa digunakan untuk menambah field)
class CustomSocialSignupForm(SocialSignupForm):
    def save(self, request):
        # Tambahkan logika signup sosial khusus jika diperlukan
        user = super(CustomSocialSignupForm, self).save(request)
        return user