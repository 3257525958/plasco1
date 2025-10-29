from rest_framework import serializers
from django.contrib.auth.models import User
from account_app.models import Product, Branch

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'