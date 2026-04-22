from django.db import models

class Enquiry(models.Model):
    enquiry_id = models.CharField(max_length=20, unique=True)
    customer = models.CharField(max_length=100)
    vehicle = models.CharField(max_length=100)
    temperature = models.CharField(max_length=10)
    status = models.CharField(max_length=20)
    date = models.DateField()
    source = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.customer} - {self.vehicle}"


class Appointment(models.Model):
    appointment_id = models.CharField(max_length=20, unique=True)
    customer = models.CharField(max_length=100)
    vehicle = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    date = models.DateField()
    time = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.customer} - {self.date} - {self.time}"


class Feedback(models.Model):
    feedback_id = models.CharField(max_length=20, unique=True)
    enquiry_id = models.CharField(max_length=20)
    customer = models.CharField(max_length=100)
    vehicle = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    date = models.DateField()

    def __str__(self):
        return f"{self.customer} - {self.feedback_id}"