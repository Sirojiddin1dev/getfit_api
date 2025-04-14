from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    STATUS = (
        ('Active', 'Active'),
        ('Block', 'Block')
    )
    COURSE_MONTH = (
        (0, "1 Oy"),
        (1, "3 Oy"),
        (2, "6 Oy"),
        (3, "12 Oy")
    )
    course_month = models.IntegerField(choices=COURSE_MONTH, null=True, blank=True)
    course_expire_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS, default='Active')
    phone_number = models.CharField(
        null=True,
        blank=True,
        max_length=13,
        unique=True,
        verbose_name='Telefon raqam',
        validators=[
            RegexValidator(
                regex=r'^\+998\d{9}$',
                message='Invalid phone number. Format should be +998XXXXXXXXX',
                code='invalid_number'
            )
        ]
    )

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)
    device_name = models.CharField(max_length=255)
    last_login = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"


class Video(models.Model):
    video_name = models.CharField(max_length=555)
    video_id = models.CharField(max_length=500)
    CATEGORY_CHOICES = (
        ("Kokrakvatriceps", "Ko'krak va triceps"),
        ("QanotmashqlarivaBiceps", "Qanot mashqlari va Biceps"),
        ("Qanotmashqlari", "Qanot mashqlari"),
        ("Yelkamashqlari", "Yelka mashqlari"),
        ("Oyoqmashqlari", "Oyoq mashqlari"),
        ("Uysharoitidamashqlar(Erkaklaruchun)", "Uy sharoitida mashqlar (Erkaklar uchun)"),
        ("Uysharoitidamashqlar(Ayollaruchun)", "Uy sharoitida mashqlar (Ayollar uchun)"),
        ("Kardiovajismoniymashqlar", "Kardio va jismoniy mashqlar"),
        ("Pressmashqlari", "Press mashqlari"),
        ("Dietavatogriovqatlanish:ErkeklarvaAyollaruchun", "Dieta va to'g'ri ovqatlanish: Erkeklar va Ayollar uchun"),
        ("Sportqoshimchalari", "Sport qo'shimchalari"),
        ("Farmakalogiya(Ximiya)", "Farmakalogiya (Ximiya)"),
    )
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.video_name


class Book(models.Model):
    name = models.CharField(max_length=255)
    book = models.FileField(upload_to='book/')

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField(max_length=500)
    text = models.TextField()
    img = models.ImageField(upload_to='news/')

    def __str__(self):
        return self.title



