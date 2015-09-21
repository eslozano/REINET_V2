from django.shortcuts import render
from django.shortcuts import render, redirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.context_processors import csrf
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.http import JsonResponse
#from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from usuarios.models import *
from ofertas_demandas.models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import *

# Create your views here.


def administrar_usuarios(request):
	if request.method == "POST":
		pass
	else:
		args={}
		return render_to_response('administrar_usuarios.html', args,context_instance=RequestContext(request))

"""
def usuarios_render(request):
	if request.method == "POST":
		print "entre"
		apellido=request.POST['apellido']
		print apellido
		usuarios=Perfil.objects.filter(last_name_icontains=apellido)
		print usuarios
		args={}
		args['usuarios']=usuarios
		return render_to_response('usuarios_render.html', args)
	else:
		print "else.."
		args={}
		return render_to_response('usuarios_render.html', args)
"""

def usuarios_render(request):
	try:
		print "entre"
		apellido=request.GET['apellido']
		print apellido
		usuarios_query=Perfil.objects.filter(last_name__icontains=apellido)
		paginator = Paginator(usuarios_query, 5) # Show 25 contacts per page
		page = request.GET.get('page')
		try:
			usuarios = paginator.page(page)
		except PageNotAnInteger:
			# If page is not an integer, deliver first page.
			usuarios = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			usuarios = paginator.page(paginator.num_pages)
		args={}
		args['usuarios']=usuarios
		return render_to_response('usuarios_render.html', args)
	except Exception as e:
		print e
		args={}
		return render_to_response('usuarios_render.html', args)

def ofertas_render(request):
	try:
		print "entre"
		input_query=request.GET['input']
		print input_query
		usuarios_query=Oferta.objects.filter(nombre__icontains=input_query)
		paginator = Paginator(usuarios_query, 5) # Show 25 contacts per page
		page = request.GET.get('page')
		try:
			ofertas = paginator.page(page)
		except PageNotAnInteger:
			# If page is not an integer, deliver first page.
			ofertas = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			ofertas = paginator.page(paginator.num_pages)
		args={}
		args['ofertas']=ofertas
		return render_to_response('ofertas_render.html', args)
	except Exception as e:
		print e
		args={}
		return render_to_response('ofertas_render.html', args)


def administrar_ofertas(request):
	if request.method == "POST":
		pass
	else:
		args={}
		return render_to_response('admin_administrar_ofertas.html', args,context_instance=RequestContext(request))


def demandas_render(request):
	try:
		print "entre"
		input_query=request.GET['input']
		print input_query
		usuarios_query=Demanda.objects.filter(nombre__icontains=input_query)
		paginator = Paginator(usuarios_query, 5) # Show 25 contacts per page
		page = request.GET.get('page')
		try:
			demandas = paginator.page(page)
		except PageNotAnInteger:
			# If page is not an integer, deliver first page.
			demandas = paginator.page(1)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			demandas = paginator.page(paginator.num_pages)
		args={}
		args['demandas']=demandas
		return render_to_response('demandas_render.html', args)
	except Exception as e:
		print e
		args={}
		return render_to_response('demandas_render.html', args)


def administrar_demandas(request):
	if request.method == "POST":
		pass
	else:
		args={}
		return render_to_response('admin_administrar_demandas.html', args,context_instance=RequestContext(request))


def admin_editar_estado_demanda(request):
	if request.method=="GET":
		id_demanda=request.GET["id_demanda"]
		estado_str=request.GET["estado"]
		print "estado "+ estado_str
		args = {}
		demanda=Demanda.objects.get(id_demanda=id_demanda);
		if demanda is not None:
			demanda.estado=estado_str
			demanda.save()
			return HttpResponse("ok")
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		print "not found en editar estado"
		return HttpResponseRedirect('NotFound');


def admin_editar_estado_oferta(request):
	if request.method=="GET":
		id_oferta=request.GET["id_oferta"]
		estado_str=request.GET["estado"]
		print "estado "+ estado_str
		args = {}
		oferta=Oferta.objects.get(id_oferta=id_oferta);
		if oferta is not None:
			oferta.estado=estado_str
			oferta.save()
			return HttpResponse("ok")
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		print "not found en editar estado"
		return HttpResponseRedirect('NotFound');

def admin_editar_estado_usuario(request):
	if request.method=="GET":
		id_usuario=request.GET["id_usuario"]
		estado_str=request.GET["estado"]
		print "estado "+ estado_str
		args = {}
		usuario=Perfil.objects.get(id_perfil=id_usuario);
		if usuario is not None:
			usuario.estado=estado_str
			usuario.save()
			return HttpResponse("ok")
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		print "not found en editar estado"
		return HttpResponseRedirect('NotFound');


def verPeticiones(request):
    try:
        args = {}
        args['peticiones'] = Peticion.objects.all().filter(codigo='000000')
        args['peticiones_aceptadas'] = Peticion.objects.all().exclude(codigo='000000')
        args.update(csrf(request))
        return render_to_response('verPeticiones.html', args,context_instance=RequestContext(request))
    except:
        return HttpResponseRedirect('/NotFound')

def aceptarPeticiones(request):
    args={}
    try:
        peticion = Peticion.objects.get(id_peticion = request.GET['id_peticion'])
        usuario = Perfil.objects.get(id=peticion.fk_usuario.id)
        destinatario = usuario.email
        codigo = "12341234"+usuario.username
        peticion.codigo = codigo
        peticion.save()
        print codigo
        #html_content = "<p><h2>Hola... puedes crear tu institucion desde el siguiente link: http://www.reinet.org/registro_institucion/" + codigo
        #msg = EmailMultiAlternatives('Registra tu institucion en REINET', html_content,
        #                             'REINET <from@server.com>', [destinatario])
        #msg.attach_alternative(html_content, 'text/html')
        #msg.send()
        #args['esAlerta'] = 0
        #args['msj'] = 'Aceptada la institucion ' + peticion.nombre_institucion
        return HttpResponse("ok")
    except Exception as e:
    	print e
        args['esAlerta'] = 1
        #args['msj'] = 'Refresque la pagina, error al aceptar ' + peticion.nombre_institucion
        return HttpResponse("error")
