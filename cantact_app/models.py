from django.db import models


class accuntmodel(models.Model):
    firstname = models.CharField(max_length=100 ,null=True)
    lastname = models.CharField(max_length=100 ,null=True)
    melicode = models.CharField(max_length=15 , default='0',null=True)
    phonnumber = models.CharField(max_length=11 ,null=True, default='0')
    savesabt = models.CharField(max_length=100,null=True)
    pasword = models.CharField(max_length=100,null=True)
    level = models.CharField(max_length=50,default='دسترسی معمولی' ,null=True)
    dayb = models.CharField(max_length=3 , default='0',null=True)
    mountb = models.CharField(max_length=20 , default='0',null=True)
    yearb = models.CharField(max_length=5, default='0',null=True)
    profile_picture = models.ImageField(upload_to='profilepics/', null=True, blank=True,)


    def __str__(self):
        return f"{self.melicode}"
class savecodphon(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    melicode = models.CharField(max_length=20 , default="0")
    phonnumber = models.CharField(max_length=20 , default="0")
    berthdayyear = models.CharField(max_length=100)
    berthdayday = models.CharField(max_length=100)
    berthdaymounth = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    expaiercode = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to='profilepicstest/', null=True, blank=True)
    def __str__(self):
        return f"{self.melicode}"



class dataacont(models.Model):
    firstname = models.CharField(max_length=100,null=True)
    lastname = models.CharField(max_length=100,null=True)
    melicode = models.CharField(max_length=20 , default="0")
    phonnumber = models.CharField(max_length=20 , default="0")
    berthday = models.CharField(max_length=100,null=True)
    miladiarray = models.CharField(max_length=5000 , default="0")
    shamsiarray = models.CharField(max_length=5000 , default="0")
    showclandarray = models.CharField(max_length=5000 , default="0")
    def __str__(self):
        return f"{self.melicode}"


class phonnambermodel(models.Model):
    name = models.CharField(max_length=100,default="0")
    lastname = models.CharField(max_length=100, default="0")
    phonnumber = models.CharField(max_length=20 , default="0")
    saver = models.CharField(max_length=20 , default="0")
    def __str__(self):
        return f"{self.phonnumber}"
