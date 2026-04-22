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
        return self.customer

class Customer(models.Model):
    name = models.CharField(max_length=140)
    phone_no = models.CharField(max_length=10)
    email = models.CharField(max_length=140)
    address = models.TextField()
    enquiry = models.OneToOneField(Enquiry, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_record')

    class Meta:
        db_table = 'sales_customer'

class Appointment(models.Model):
    name = models.CharField(max_length=140, primary_key=True)
    creation = models.DateTimeField(null=True, blank=True)
    modified = models.DateTimeField(null=True, blank=True)
    modified_by = models.CharField(max_length=140, null=True, blank=True)
    owner = models.CharField(max_length=140, null=True, blank=True)
    docstatus = models.IntegerField(default=0)
    idx = models.IntegerField(default=0)
    date = models.DateField(null=True, blank=True)
    sales_enquiry_id = models.ForeignKey(Enquiry, on_delete=models.SET_NULL, null=True, blank=True, db_column='sales_enquiry_id')
    appoinment_time = models.TimeField(null=True, blank=True)
    appoinment_cancelpost_poned = models.IntegerField(default=0)
    appointment_cancel_reason = models.TextField(null=True, blank=True)
    name1 = models.CharField(max_length=140, null=True, blank=True)
    gender = models.CharField(max_length=140, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    vehicle_name = models.CharField(max_length=140, null=True, blank=True)
    phone_no = models.CharField(max_length=10, null=True, blank=True)
    appoinment_date = models.DateField(null=True, blank=True)
    whatsapp_no = models.CharField(max_length=140, null=True, blank=True)
    amended_from = models.CharField(max_length=140, null=True, blank=True)
    naming_series = models.CharField(max_length=140, null=True, blank=True)
    dupicate_data = models.IntegerField(default=0)
    _user_tags = models.TextField(null=True, blank=True, db_column='_user_tags')
    _comments = models.TextField(null=True, blank=True, db_column='_comments')
    _assign = models.TextField(null=True, blank=True, db_column='_assign')
    _liked_by = models.TextField(null=True, blank=True, db_column='_liked_by')

    class Meta:
        db_table = 'sales_appointment'

class Feedback(models.Model):
    name = models.CharField(max_length=140, primary_key=True)
    creation = models.DateTimeField(null=True, blank=True)
    modified = models.DateTimeField(null=True, blank=True)
    modified_by = models.CharField(max_length=140, null=True, blank=True)
    owner = models.CharField(max_length=140, null=True, blank=True)
    docstatus = models.IntegerField(default=0)
    idx = models.IntegerField(default=0)
    sales_enquiry_id = models.ForeignKey(Enquiry, on_delete=models.SET_NULL, null=True, blank=True, db_column='sales_enquiry_id')
    feed_back_created_date = models.DateField(null=True, blank=True)
    vehicle_name = models.CharField(max_length=140, null=True, blank=True)
    phone_no = models.CharField(max_length=140, null=True, blank=True)
    customer = models.CharField(max_length=140, null=True, blank=True)
    sales_appoinment_id = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, db_column='sales_appoinment_id')
    feed_back_date = models.DateField(null=True, blank=True)
    naming_series = models.CharField(max_length=140, null=True, blank=True)
    amended_from = models.CharField(max_length=140, null=True, blank=True)
    _user_tags = models.TextField(null=True, blank=True, db_column='_user_tags')
    _comments = models.TextField(null=True, blank=True, db_column='_comments')
    _assign = models.TextField(null=True, blank=True, db_column='_assign')
    _liked_by = models.TextField(null=True, blank=True, db_column='_liked_by')

    class Meta:
        db_table = 'sales_feedback'
