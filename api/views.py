from django.shortcuts import render
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from django.db import transaction
from .serializers import *
from .models import *
from datetime import datetime, timedelta
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Sum


class TokenPairView(TokenObtainPairView):
	serializer_class = TokenPairSerializer


class GroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
	authentication_classes = [JWTAuthentication, SessionAuthentication]
	permission_classes = IsAuthenticated,
	queryset = Group.objects.all()
	serializer_class = GroupSerializer


class UserViewSet(viewsets.ModelViewSet):
	serializer_class = UserSerializer
	queryset = User.objects.all().order_by('-id')
	authentication_classes = [JWTAuthentication, SessionAuthentication]
	permission_classes = IsAuthenticated,
	# modification mot de passe

	@transaction.atomic()
	def update(self, request, pk):
		user = self.get_object()
		print(user)
		data = request.data
		username = data.get('username')
		first_name = data.get('first_name')
		last_name = data.get('last_name')
		nouv_password = data.get('nouv_password')
		anc_password = data.get('anc_password')
		if user.check_password(anc_password):
			print("checked")
			user.username = username
			user.first_name = first_name
			user.last_name = last_name
			user.set_password(nouv_password)
			user.save()
			return Response({"status": "Utilisateur modifié avec success"}, 201)
		return Response({"status": "Ancien mot de passe incorrect"}, 400)

class PersonnelViewSet(viewsets.ModelViewSet):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	serializer_class = PersonnelSerializer
	queryset = Personnel.objects.all().order_by('-id')
	filter_backends = [DjangoFilterBackend, filters.SearchFilter]
	filterset_fields = []
	search_fields = []

	@transaction.atomic()
	def create(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		telephone = data['telephone']
		genre = data['genre']
		user_serial = data['user']
		user = User(
			username=user_serial['username'],
			first_name=user_serial['first_name'],
			last_name=user_serial['last_name'],
		)
		user.set_password(request.data['user']['password'])
		professeur:Personnel = Personnel(
			user = user,
			telephone = telephone,
			genre = genre
			)
		user.save()
		group = Group.objects.get_or_create(name='Professeur')
		user.groups.add(group[0])
		user.save()
		professeur.save()
		serializer = PersonnelSerializer(
			professeur, many=False, context={"request": request})
		return Response(serializer.data, 201)

class EleveViewSet(viewsets.ModelViewSet):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	serializer_class = EleveSerializer
	queryset = Eleve.objects.all().order_by('-id')
	filter_backends = [DjangoFilterBackend, filters.SearchFilter]
	filterset_fields = {"classe":['exact'],}
	search_fields = ["classe"]

	@transaction.atomic()
	def create(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		nom = serializer.validated_data['nom']
		prenom = serializer.validated_data['prenom']
		genre = serializer.validated_data['genre']
		classe:Classe = serializer.validated_data['classe']
		date_naissance = serializer.validated_data['date_naissance']
		
		eleve:Eleve = Eleve(
			nom=nom,
			prenom=prenom,
			genre=genre,
			classe=classe,
			date_naissance=date_naissance,
			)
		eleve.save()
		serializer = EleveSerializer(
			eleve, many=False, context={"request": request})
		return Response(serializer.data, 201)


class NiveauViewSet(viewsets.ModelViewSet):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	serializer_class = NiveauSerializer
	queryset = Niveau.objects.all().order_by('id')
	filter_backends = [DjangoFilterBackend, filters.SearchFilter]
	filterset_fields = [
		'nom'
	]
	search_fields = [
		'nom'
	]

	@transaction.atomic()
	def create(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		nom = data['nom']
		user = request.user
		niveau: Niveau = Niveau(
			nom=nom,
			user=user
		)
		niveau.save()
		serializer = NiveauSerializer(
			niveau, many=False, context={"request": request})
		return Response(serializer.data, 201)


class SectionViewSet(viewsets.ModelViewSet):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	serializer_class = SectionSerializer
	queryset = Section.objects.all().order_by('-id')
	filter_backends = [DjangoFilterBackend, filters.SearchFilter]
	filterset_fields = [
		'nom',
		'niveau__nom'
	]
	search_fields = [
		'nom',
		'niveau__nom'
	]

	@transaction.atomic()
	def create(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		nom = data['nom']
		niveau: Niveau = data['niveau']
		user = request.user
		section: Section = Section(
			nom=nom,
			niveau=niveau,
			user=user
		)
		section.save()
		serializer = SectionSerializer(
			section, many=False, context={"request": request})
		return Response(serializer.data, 201)


class ClasseViewSet(viewsets.ModelViewSet):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	serializer_class = ClasseSerializer
	queryset = Classe.objects.all().order_by('id')
	filter_backends = [DjangoFilterBackend, filters.SearchFilter]
	filterset_fields = [
		'niveau',
		'section',
		'id'
	]
	search_fields = [
		'niveau__nom',
		'section__nom',
		'nom'
	]

class EntreeViewSet(viewsets.ModelViewSet):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	serializer_class = EntreeSerializer
	queryset = Entree.objects.all().order_by('id')
	filter_backends = [DjangoFilterBackend,]
	filterset_fields = {
		'type_entree':['exact'],
		'date': ['gte', 'lte'],
		'user':['exact']
	}

	@transaction.atomic()
	def create(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		type_entree = int(data['type_entree'])
		montant = data['montant']
		details = data['details']
		user = request.user
		entree: Entree = Entree(
			user=user,
			type_entree=type_entree,
			montant=montant,
			details=details
		)
		entree.save()

		if(type_entree in range(2,6)):
			extra_data = request.data
			nom = extra_data.get('nom')
			prenom = extra_data.get('prenom')
			telephone = extra_data.get('telephone')
			adresse = extra_data.get('adresse')
			cni = extra_data.get('cni')
			date_debut = extra_data.get('date_debut')
			date_fin = extra_data.get('date_fin')

			DetailsEntreeLocation(
				entree = entree,
				nom = nom,
				prenom = prenom,
				telephone = telephone,
				adresse = adresse,
				cni = cni,
				date_debut = date_debut,
				date_fin = date_fin,
				).save()
		serializer = EntreeSerializer(
			entree, many=False, context={"request": request})
		return Response(serializer.data, 201)	

class DetailsEntreeLocationViewSet(viewsets.ModelViewSet):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	serializer_class = DetailsEntreeLocationSerializer
	queryset = DetailsEntreeLocation.objects.all().order_by('id')
	filter_backends = [DjangoFilterBackend,]
	filterset_fields = {
		'entree':['exact'],
		'date': ['gte', 'lte']
	}

class SortieViewSet(viewsets.ModelViewSet):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	serializer_class = SortieSerializer
	queryset = Sortie.objects.all().order_by('id')
	filter_backends = [DjangoFilterBackend,]
	filterset_fields = {
		'type_sortie':['exact'],
		'date': ['gte', 'lte'],
		'user':['exact']
	}

	@transaction.atomic()
	def create(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		type_sortie = int(data['type_sortie'])
		montant = data['montant']
		details = data['details']
		user = request.user
		sortie: Sortie = Sortie(
			user=user,
			type_sortie=type_sortie,
			montant=montant,
			details=details
		)
		sortie.save()
		serializer = SortieSerializer(
			sortie, many=False, context={"request": request})
		return Response(serializer.data, 201)	