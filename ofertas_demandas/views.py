# -*- encoding: utf-8 -*-
import random
import string
from datetime import datetime


from django.shortcuts import render, redirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.context_processors import csrf
from django.contrib import auth
from django.contrib.auth import logout
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from datetime import *
from ofertas_demandas.models import *
from ofertas_demandas.serializers import *

from usuarios.models import *
from django.db.models import Avg
from usuarios.serializers import UsuarioSerializador


"""
Autor: Jose Velez
Nombre de funcion: verificar_nombre_oferta
Entrada: request GET o POST
Salida: Formulario de generarCodigo
Descripción: Genera un codigo para crear una oferta
"""

def verificar_nombre_oferta(request):  

    if request.method == "POST":
        nombre_oferta = request.POST['nombre_oferta'] 
        try:
            oferta = Oferta.objects.get(nombre=nombre_oferta) 
        except:
            oferta = None
        #print "nombre_oferta",nombre_oferta, "oferta ", oferta
        if oferta is not None: #Error 10, usar palabras en español
            return HttpResponse("usado")
        else:
            return HttpResponse("ok")
    return HttpResponse("no es post")


"""
Autor: Leonel Ramirez
Nombre de funcion: inicio_oferta
Parametros: request
Salida: render 
Descripcion: para llamar la pagina oferta inicio
"""

@login_required
def inicio_oferta(request):

	args = {}
	args['usuario']=request.user
	args['es_admin']=request.session['es_admin']
	return render_to_response('oferta_inicio.html',args)


"""
Autor: FaustoMora y Pedro Iñiguez
Nombre de funcion: inicio_demanda
Parametros: request
Salida: render 
Descripcion: para llamar la pagina demanda inicio
"""

@login_required
def inicio_demanda(request):


	args = {}
	args['usuario']=request.user
	args['es_admin']=request.session['es_admin']

	demandas=Demanda.objects.exclude(publicada=0).all()
	args['demandas'] = demandas

	



	return render_to_response('demanda_inicio.html', args)


"""
Autor: FaustoMora
Nombre de funcion: crear_oferta_copia
Parametros: request
Salida: HttpResponseRedirect
Descripcion: funcion para redireccion a crear_oferta_copia
"""
@login_required
def crear_oferta_copia(request):


	# si existe la variable en el request del get
	if request.GET.get('select_oferta',False):
		args = {}
		args['es_admin']=request.session['es_admin']
		args['usuario']=request.user
		oferta = None
		oferta_id = request.GET['select_oferta']

		# oferta pertenezca al user
		try:
			perfil = Perfil.objects.get(id=request.user.id)
			oferta = perfil.participa_en.all().get(miembroequipo__es_propietario=1,id_oferta=oferta_id)
			palabra_clave = PalabraClave.objects.filter(ofertas_con_esta_palabra=oferta)
			tags = []

			for t in palabra_clave:
				tags.append(t.palabra.encode('utf-8','ignore'))

			tiempo_disponilbe = oferta.tiempo_para_estar_disponible.split(' ',1)
			oferta_tiempo = int(tiempo_disponilbe[0])

			if tiempo_disponilbe[1] == 'Mes/es':
				oferta_duracion = 0
			else:
				oferta_duracion = 1

			etiqueta_json= json.dumps(tags)
			args['oferta_tiempo']=oferta_tiempo
			args['oferta_duracion']=oferta_duracion
			args['oferta']=oferta
			args['tags']=etiqueta_json
			args.update(csrf(request))
			return render(request,'crear_oferta.html',args)

		# caso contrario se redirecciona a crear oferta
		except Oferta.DoesNotExist:
			return redirect('/CrearOferta/')

	#no existe variable se redireeciona a crear oferta
	else:
		return redirect('/CrearOferta/')

"""
Autor: FaustoMora
Nombre de funcion: crear_oferta
Parametros: request
Salida: HttpResponseRedirect
Descripcion: funcion para redireccion a crear_oferta
"""

@login_required
def crear_oferta(request):


	args = {}
	args['usuario']=request.user
	args['es_admin']=request.session['es_admin']
	args['oferta'] = None
	args.update(csrf(request))
	return render(request,'crear_oferta.html',args)


"""
Autor: FaustoMora
Nombre de funcion: cargar_imagen_oferta
Parametros: request
Salida: HttpResponse status
Descripcion: funcion para upload de imagnes en crear oferta
"""

@login_required
def cargar_imagen_oferta(request):


	try:
		imagen = ImagenOferta()
		descripcion = request.POST.get('descripcion',None)
		descripcion = json.loads(descripcion)

		# si existe la descripcion de las imagenes correspondientes
		if descripcion:
			aux = request.POST['flowIdentifier']

			for x in descripcion:
				if x['value'] == aux:
					if 'descripcion' in x:
						imagen.descripcion=x['descripcion']

					#si no existe descripcion en dictionario
					else:
						imagen.descripcion=" "

		# caso contrario se guarda un espacio en blanco
		else:
			imagen.descripcion=" "

		id = request.POST['id_oferta']
		imagen.fk_oferta = Oferta.objects.get(id_oferta=id)
		img = request.FILES['file']
		imagen.imagen = img
		imagen.save()
		response = JsonResponse({'save_estado':True})
		return HttpResponse(response.content)

	except:
		response = JsonResponse({'save_estado':False})
		return HttpResponse(response.content)

"""
Autor: FaustoMora
Nombre de funcion: crear_demanda
Parametros: request
Salida: HttpResponseRedirect
Descripcion: funcion para redirect a crear demanda
"""
@login_required
def crear_demanda(request):


	args = {}
	args['usuario']=request.user
	args['es_admin']=request.session['es_admin']
	args['demanda'] = None
	args.update(csrf(request))
	return render(request,'crear_demanda.html',args)


"""
Autor: FaustoMora
Nombre de funcion: crear_demanda_copia
Parametros: request
Salida: HttpResponseRedirect
Descripcion: funcion para redireccion a crear_demanda_copia
"""
@login_required
def crear_demanda_copia(request):


	# si existe la variable en el request del get
	if request.GET.get('select_demanda',False):
		args = {}
		args['es_admin']=request.session['es_admin']
		args['usuario']=request.user
		demanda_id = request.GET['select_demanda']

		#demanda pertenezca al user
		try:
			perfil = Perfil.objects.get(id=request.user.id)
			demanda = Demanda.objects.get(id_demanda=demanda_id,fk_perfil=perfil)
			palabra_clave = PalabraClave.objects.filter(demandas_con_esta_palabra=demanda)
			tags = []

			for t in palabra_clave:
				tags.append(t.palabra.encode('utf-8','ignore'))

			tiempo_disponilbe = demanda.tiempo_para_estar_disponible.split(' ',1)
			demanda_tiempo = int(tiempo_disponilbe[0])

			if tiempo_disponilbe[1] == 'Mes/es':
				demanda_duracion = 0
			else:
				demanda_duracion = 1

			etiqueta_json= json.dumps(tags)
			args['demanda_tiempo']=demanda_tiempo
			args['demanda_duracion']=demanda_duracion
			args['demanda']=demanda
			args['tags']=etiqueta_json
			args.update(csrf(request))
			return render(request,'crear_demanda.html',args)

		# en caso de no encontrarla redireciona a crear demanda
		except Demanda.DoesNotExist:
			return redirect('/CrearDemanda/')

	# si no existe se redirecciona a crear demanda
	else:
		return redirect('/CrearDemanda/')

"""
Autor: FaustoMora
Nombre de funcion: cargar_imagen_demanda
Parametros: request
Salida: HttpResponse status
Descripcion: funcion para upload de imagnes en crear demanda
"""

@login_required
def cargar_imagen_demanda(request):


	try:
		imagen = ImagenDemanda()
		descripcion = request.POST.get('descripcion',None)
		descripcion = json.loads(descripcion)

		# si existe la descripcion de las imagenes correspondientes
		if descripcion:
			aux = request.POST['flowIdentifier']

			for x in descripcion:
				if x['value'] == aux:
					if 'descripcion' in x:
						imagen.descripcion=x['descripcion']

					#si no existe descripcion en dictionario
					else:
						imagen.descripcion=" "

		# caso contrario se guarda un espacio en blanco
		else:
			imagen.descripcion=" "

		id = request.POST['id_demanda']
		imagen.fk_demanda = Demanda.objects.get(id_demanda=id)
		img = request.FILES['file']
		imagen.imagen = img
		imagen.save()
		response = JsonResponse({'save_estado':True})
		return HttpResponse(response.content)

	except:
		response = JsonResponse({'save_estado':False})
		return HttpResponse(response.content)

"""
Autor: Rolando Sornoza, Roberto Yoncon, David Vinces, Pedro Iniguez
Nombre de funcion: verCualquierOferta
Parametros: request
Salida: http
Descripcion: funcion para ver una oferta publicada
"""
@login_required
def ver_cualquier_oferta(request, id_oferta):
	usuario = Perfil.objects.get(id=request.session['id_usuario'])
	args = {}
	args['es_admin']=request.session['es_admin']

	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario
		#Obtengo la oferta
		try:
			oferta = Oferta.objects.get(id_oferta = id_oferta)
			print "ofeeerta"
			print oferta.estado
			if oferta.estado == 3:  #la oferta esta censurada
				return HttpResponseRedirect('/NotFound')
			args['oferta'] = oferta
			args['fecha_publicacion_oferta'] = oferta.fecha_publicacion.strftime('%Y-%m-%d %H:%M:%S')
		#Sino la encuentro informo.
		except:
			args['mensaje_error'] = "La oferta no se encuentra en la red, lo sentimos."
			return render_to_response('problema_oferta.html',args)
		#Obtengo la membresia.
		try:
			membresia_oferta = MiembroEquipo.objects.get(fk_participante = usuario.id_perfil,
														fk_oferta_en_que_participa = oferta.id_oferta)
			estado_membresia = membresia_oferta.estado_membresia
			args['estado_membresia'] = estado_membresia
		#Si no tengo la membresia es xq nunca he aplicado. Identificador = 2
		except Exception as e:
			args['estado_membresia'] = 2

		# Sino esta publicada no avanzo.
		if oferta.publicada == 0 :
			args.update(csrf(request))
			args['mensaje_error'] = "La oferta "+oferta.nombre+", no esta actualmente publicada."
			return render_to_response('problema_oferta.html',args)
		#Una vez que esta lista la oferta para presentar cargo todos sus datos.
		else:
			participantes = MiembroEquipo.objects.filter(fk_oferta_en_que_participa=id_oferta,
														 estado_membresia=1)
			propietario = MiembroEquipo.objects.get(fk_oferta_en_que_participa=id_oferta,
													estado_membresia=1,
													es_propietario=1).fk_participante
			comentarios_oferta = ComentarioCalificacion.objects.filter(fk_oferta_id=id_oferta, estado_comentario=1)
			args['mi_comentario'] = ComentarioCalificacion.objects.filter(fk_oferta_id=id_oferta,
																		 fk_usuario_id=usuario).count
			calificacion_oferta = oferta.calificacion_total
			try:
				palabras_claves = oferta.palabras_clave.all()
			except Exception as e:
				palabras_claves =  ["Null", "Null", "Null", "Null"]
			try:
				imagenes = ImagenOferta.objects.filter(fk_oferta = id_oferta)
				imagen_principal = imagenes.first()
				#print hooooooooooooooooooooolaaaaa
				print imagen_principal
				if not imagenes:
					imagenes = False
					imagen_principal = False

			except Exception as e:
				imagenes = False
				imagen_principal = False
		#Envio los args.
		args.update(csrf(request))
		args['participantes'] = participantes
		args['palabras_claves'] = palabras_claves
		args['comentarios_aceptados'] = comentarios_oferta
		args['calificacion_oferta'] = str(calificacion_oferta)
		args['propietario'] = propietario
		args['imagenes_oferta'] = imagenes
		args['imagen_principal'] = imagen_principal
		return render_to_response('oferta_ver_otra.html',args)

	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

"""
Autor: Pedro Iniguez
Nombre de funcion: administrarOferta
Parametros: request
Salida:
Descripcion: funcion para administrar mi oferta publicada.
"""

@login_required
def administrar_Oferta(request, id_oferta):
	session = request.session['id_usuario']
	usuario = Perfil.objects.get(id=session)
	args = {}
	args['es_admin']=request.session['es_admin']
	print 'mi id antes'+id_oferta
	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario
	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	oferta = Oferta.objects.get(id_oferta = id_oferta)
	print oferta.id_oferta

	if (oferta.publicada == 0):
		print 'No publicada'
	#return HttpResponseRedirect('/NotFound/')
	membresiaOferta = MiembroEquipo.objects.all().filter(fk_participante = usuario.id_perfil, fk_oferta_en_que_participa = id_oferta, es_propietario = 1).first()

	if membresiaOferta is None:
		return HttpResponseRedirect('/NotFound/')


	solicitudes=MiembroEquipo.objects.all().filter(fk_oferta_en_que_participa = id_oferta, estado_membresia=0)

	participantes = MiembroEquipo.objects.all().filter(fk_oferta_en_que_participa=oferta.id_oferta,estado_membresia=1,activo =1)

	equipoDueno = MiembroEquipo.objects.all().filter(es_propietario=1, fk_oferta_en_que_participa=oferta.id_oferta).first()
	try:
		palabras_claves = oferta.palabras_clave.all()
	except Exception as e:
		palabras_claves =  ["Null", "Null", "Null", "Null"]

	galeria = ImagenOferta.objects.all().filter(fk_oferta = oferta.id_oferta)
	args['palabras_claves'] = palabras_claves
	args['comentariosPendientes'] = ComentarioCalificacion.objects.filter(fk_oferta = oferta.id_oferta, estado_comentario=0)
	args['comentariosAceptados']=ComentarioCalificacion.objects.filter(fk_oferta = oferta.id_oferta, estado_comentario=1).count
	args.update(csrf(request))
	args['dueno'] = equipoDueno.fk_participante.first_name + ' ' + equipoDueno.fk_participante.last_name
	args['oferta'] = oferta
	args['fecha_publicacion_oferta'] = oferta.fecha_publicacion.strftime('%Y-%m-%d %H:%M:%S')
	calificacionOferta = oferta.calificacion_total
	args['calificacionOferta'] = str(calificacionOferta)
	args['participantes'] = participantes
	args['solicitudes']=solicitudes
	args['galeria'] = galeria
	args['imagen_principal'] = galeria.first()
	return render_to_response('administrar_oferta.html',args)

"""
Autor: Pedro Iniguez
Nombre de funcion: administarBorrador
Parametros: request
Salida:
Descripcion: funcion para administrar mi oferta publicada.
"""

@login_required
def administrar_Borrador(request, id_oferta):
	session = request.session['id_usuario']
	usuario = Perfil.objects.get(id=session)
	args = {}
	args['es_admin']=request.session['es_admin']

	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario

	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	try:
		oferta = Oferta.objects.get(id_oferta = id_oferta)
		#fecha_creacion_oferta = oferta.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
	except:
		return HttpResponseRedirect('/NotFound/')
	if (oferta.publicada == 1):
		return HttpResponseRedirect('/NotFound/')
	membresiaOferta = MiembroEquipo.objects.all().filter(fk_participante = usuario.id_perfil, fk_oferta_en_que_participa = id_oferta, es_propietario = 1).first()

	if membresiaOferta is None:
		return HttpResponseRedirect('/NotFound/')

	equipoDueno = MiembroEquipo.objects.all().filter(es_propietario=1, fk_oferta_en_que_participa=oferta.id_oferta).first()

	galeria = ImagenOferta.objects.all().filter(fk_oferta = oferta.id_oferta)

	args.update(csrf(request))
	args['dueno'] = equipoDueno.fk_participante.first_name + ' ' + equipoDueno.fk_participante.last_name
	args['oferta'] = oferta
	args['fecha_creacion_oferta'] = oferta.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
	args['galeria'] = galeria
	args['imagen_principal'] = galeria.first()
	args['palabras'] = oferta.palabras_clave.all
	return render_to_response('administrar_borrador.html',args)

"""
Autor: Roberto Yoncon - Jose Velez Gomez
Nombre de funcion: editar_borrador
Parametros: request, id de una oferta
Salida: 
Descripcion: funcion para editar un borrador
"""
@login_required
def editar_borrador(request, id_oferta):
	sesion = request.session['id_usuario']
	usuario = Perfil.objects.get(id=sesion)
	args = {}
	args['es_admin']=request.session['es_admin']

	if usuario is not None:
		args['usuario'] = usuario
	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	try:
		oferta = Oferta.objects.get(id_oferta = id_oferta)
	except:
		return HttpResponseRedirect('/NotFound/')

	if (oferta.publicada == 1):
		return HttpResponseRedirect('/NotFound/')

	membresia_oferta = MiembroEquipo.objects.all().filter(fk_participante = usuario.id_perfil, fk_oferta_en_que_participa = id_oferta, es_propietario = 1).first()

	if membresia_oferta is None:
		return HttpResponseRedirect('/NotFound/')

	try:
		tiempo_disponible = oferta.tiempo_para_estar_disponible.split(' ',1)
		oferta_tiempo = int(tiempo_disponible[0])

		#si la duracion es de mes
		if tiempo_disponible[1] == 'Mes/es':
			oferta_duracion = 0
		else:
			oferta_duracion = 1

	#si no se encuentra establecida la duracion
	except:
		oferta_duracion = 1
		#oferta_tiempo = "Año/s"

	if request.method == 'POST':
		#seccion de informacion
		nombre = request.POST['nombre_oferta']
		tipo = request.POST['select_tipo_oferta']
		descripcion = request.POST['descripcion_oferta']
		dominio = request.POST['oferta_dominio']
		subdominio = request.POST['oferta_sub_dominio']
		fecha_actual = datetime.datetime.now()
		#tags = request.POST['oferta_tags'] #Aun no usado
		#seccion de perfiles
		perfil_cliente = request.POST.get('oferta_descripcion_perfil', "No disponible")
		perfil_beneficiario = request.POST.get('oferta_beneficiario_perfil', "No disponible")
		#seccion de business canvas
		canvas_socio_clave = request.POST.get('canvas_socio_clave', "No disponible")
		canvas_actividades_clave = request.POST.get('canvas_actividades_clave', "No disponible")
		canvas_recursos = request.POST.get('canvas_recrusos_clave', "No disponible")
		canvas_propuesta = request.POST.get('canvas_propuesta_valor', "No disponible")
		canvas_relaciones = request.POST.get('canvas_ralaciones_clientes', "No disponible")
		canvas_canales = request.POST.get('canvas_canales_distribucion', "No disponible")
		canvas_segmentos = request.POST.get('canvas_segmentos_clientes', "No disponible")
		canvas_estructura = request.POST.get('canvas_estructura_costos', "No disponible")
		canvas_fuente = request.POST.get('canvas_fuente_ingresos', "No disponible")
		#seccion de industria
		tendencias = request.POST.get('oferta_tendencias', "No disponible")
		soluciones_alternativas = request.POST.get('ofertas_alternativas_soluciones', "No disponible")
		#para Diagrama de Porter
		porter_competidores = request.POST.get('diagramapoter_competidores', "No disponible")
		porter_consumidores = request.POST.get('diagramapoter_consumidores', "No disponible")
		porter_sustitutos = request.POST.get('diagramapoter_sustitutos', "No disponible")
		porter_proveedores = request.POST.get('diagramapoter_proveedores', "No disponible")
		porter_nuevos = request.POST.get('diagramapoter_nuevos_entrantes', "No disponible")
		#seccion de estado/Logros
		tiempo_disponible = request.POST.get('oferta_tiempo_disponibilidad', "No disponible")
		tiempo_unidad = request.POST.get('select_oferta_tiempo', None)
		propiedad_intelectual = request.POST.get('oferta_propiedad_intelectual', "No disponible")
		evidencia_traccion = request.POST.get('oferta_evidencia_traccion', "No disponible")
		#seccion de copia de datos a la oferta a modificar
		#seccion informacion
		oferta_editada = oferta
		oferta_editada.nombre = nombre
		oferta_editada.tipo = tipo
		oferta_editada.descripcion = descripcion
		oferta_editada.dominio = dominio
		oferta_editada.subdominio = subdominio
		oferta_editada.fecha_creacion = fecha_actual
		#seccion perfiles
		oferta_editada.perfil_cliente = perfil_cliente
		oferta_editada.perfil_beneficiario = perfil_beneficiario
		#seccion industria
		oferta_editada.cuadro_tendencias_relevantes = tendencias
		oferta_editada.descripcion_soluciones_existentes = soluciones_alternativas
		#seccion de estado/Logros

		#manejo de la duracion de la oferta
		if tiempo_disponible != "" and tiempo_unidad != "":

			if tiempo_unidad == "0":
				tiempo_unidad = "Mes/es"
			else:
				tiempo_unidad = "Año/s"

			oferta_editada.tiempo_para_estar_disponible = str(tiempo_disponible) + " " + tiempo_unidad
		else:
			oferta_editada.tiempo_para_estar_disponible = "1 Año/s"

		oferta_editada.estado_propieada_intelectual = propiedad_intelectual
		oferta_editada.evidencia_traccion = evidencia_traccion

		#seccion Diagrama canvas
		#se verifica si no existen datos ingresados en los campos. Entonces se dice que no existe el objeto diagrama canvas
		if canvas_socio_clave == "" and canvas_actividades_clave=="" and canvas_recursos=="" and canvas_propuesta=="" and canvas_relaciones=="" and canvas_canales=="" and canvas_segmentos=="" and canvas_estructura=="" and canvas_fuente=="" :
			oferta_editada.fk_diagrama_canvas = None
		#si existen datos ingresados, se los asigna
		else:

			#si anteriormente tuvo canvas, se lo modifica
			try:
				oferta_editada.fk_diagrama_canvas.asociaciones_clave = canvas_socio_clave
				oferta_editada.fk_diagrama_canvas.actividades_clave = canvas_actividades_clave
				oferta_editada.fk_diagrama_canvas.recursos_clave = canvas_recursos
				oferta_editada.fk_diagrama_canvas.propuesta_valor = canvas_propuesta
				oferta_editada.fk_diagrama_canvas.relacion_clientes = canvas_relaciones
				oferta_editada.fk_diagrama_canvas.canales_distribucion = canvas_canales
				oferta_editada.fk_diagrama_canvas.segmento_mercado = canvas_segmentos
				oferta_editada.fk_diagrama_canvas.estructura_costos = canvas_estructura
				oferta_editada.fk_diagrama_canvas.fuente_ingresos = canvas_fuente
				oferta_editada.fk_diagrama_canvas.save()
			#si no tenia, se crea un diagrama canvas nuevo
			except:
				diagrama_canvas = DiagramaBusinessCanvas()
				diagrama_canvas.asociaciones_clave = canvas_socio_clave
				diagrama_canvas.actividades_clave = canvas_actividades_clave
				diagrama_canvas.recursos_clave = canvas_recursos
				diagrama_canvas.propuesta_valor = canvas_propuesta
				diagrama_canvas.relacion_clientes = canvas_relaciones
				diagrama_canvas.canales_distribucion = canvas_canales
				diagrama_canvas.segmento_mercado = canvas_segmentos
				diagrama_canvas.estructura_costos = canvas_estructura
				diagrama_canvas.fuente_ingresos = canvas_fuente
				diagrama_canvas.save()
				oferta_editada.fk_diagrama_canvas = diagrama_canvas

		#print "id_oferta-borrador POST:3:  ",id_oferta
		#seccion Diagrama de Porter
		#se verifica si no existen datos ingresados en los campos. Entonces se dice que no existe el objeto diagrama porter
		if porter_competidores == "" and porter_consumidores=="" and porter_sustitutos=="" and porter_proveedores=="" and porter_nuevos=="":
			oferta_editada.fk_diagrama_competidores = None
		#si existen datos ingresados, se los asigna
		else:

			#si anteriormente tuvo porter, cambiarlo
			try:
				oferta_editada.fk_diagrama_competidores.competidores = porter_competidores
				oferta_editada.fk_diagrama_competidores.consumidores = porter_consumidores
				oferta_editada.fk_diagrama_competidores.sustitutos = porter_sustitutos
				oferta_editada.fk_diagrama_competidores.proveedores = porter_proveedores
				oferta_editada.fk_diagrama_competidores.nuevosMiembros = porter_nuevos
				oferta_editada.fk_diagrama_competidores.save()
			#si no tenia, se crea uno nuevo y se lo asigna
			except:
				diagrama_porter = DiagramaPorter()
				diagrama_porter.competidores = porter_competidores
				diagrama_porter.consumidores = porter_consumidores
				diagrama_porter.sustitutos = porter_sustitutos
				diagrama_porter.proveedores = porter_proveedores
				diagrama_porter.nuevosMiembros = porter_nuevos
				diagrama_porter.save()
				oferta_editada.fk_diagrama_competidores = diagrama_porter

		#print "id_oferta-borrador POST:4:  ",id_oferta
		#manejo de tags
		try:
			palabra_clave = PalabraClave.objects.filter(ofertas_con_esta_palabra=oferta)
			tags = []
			for t in palabra_clave:
				tags.append(t.palabra.encode('utf-8','ignore'))
			etiqueta_json= json.dumps(tags)
			args['tags']=etiqueta_json
		except:
			palabras_claves =  ["Null", "Null", "Null", "Null"]

		galeria = ImagenOferta.objects.all().filter(fk_oferta = oferta.id_oferta)
		oferta_editada.save()
		args.update(csrf(request))

		args['oferta_tiempo']=oferta_tiempo
		args['oferta_duracion']=oferta_duracion
		args['oferta'] = oferta_editada
		args['msg'] = "Borrador de oferta modificada exitosamente"
		args['imagen_principal'] = galeria.first()
		args['palabras'] = oferta.palabras_clave.all
		#return render_to_response('administrar_borrador.html',args)
		return HttpResponseRedirect('/AdministrarBorradorOferta/'+id_oferta)
		
	else:
		args.update(csrf(request))
		args['oferta_tiempo']=oferta_tiempo
		args['oferta_duracion']=oferta_duracion
		args['oferta'] = oferta
		print "DESCRIPCION:::::::::::  ",oferta.descripcion
		return render_to_response('editar_borrador.html',args)


"""
Autor: Roberto Yoncon - Jose Velez Gomez
Nombre de funcion: editar_borrador_demanda
Parametros: request, id de una demanda
Salida: 
Descripcion: funcion para editar un borrador
"""
@login_required
def editar_borrador_demanda(request, id_demanda):
	sesion = request.session['id_usuario']
	usuario = Perfil.objects.get(id=sesion)
	args = {}
	args['es_admin']=request.session['es_admin']

	if usuario is not None:
		args['usuario'] = usuario
	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	try:
		demanda = Demanda.objects.get(id_demanda = id_demanda)
	except:
		return HttpResponseRedirect('/NotFound/')

	if (demanda.publicada == 1):
		return HttpResponseRedirect('/NotFound/')

	try:
		tiempo_disponible = demanda.tiempo_para_estar_disponible.split(' ',1)
		demanda_tiempo = int(tiempo_disponible[0])

		#si la duracion es de mes
		if tiempo_disponible[1] == 'Mes/es':
			demanda_duracion = 0
		else:
			demanda_duracion = 1

	#si no se encuentra establecida la duracion
	except:
		demanda_duracion = -1
		demanda_tiempo = ""

	if request.method == 'POST':
		#seccion de informacion
		nombre = request.POST['nombre_demanda']
		descripcion = request.POST['descripcion_demanda']
		dominio = request.POST['demanda_dominio']
		subdominio = request.POST['demanda_sub_dominio']
		fecha_actual = datetime.datetime.now()
		#tags = request.POST['demanda_tags'] #Aun no usado
		#seccion de perfiles
		perfil_cliente = request.POST.get('demanda_descripcion_perfil', "No disponible")
		perfil_beneficiario = request.POST.get('demanda_beneficiario_perfil', "No disponible")
		#seccion de industria
		importancia_resolver_necesidad = request.POST.get('demanda_importancia_resolver_necesidad', "No disponible")
		alternativas_soluciones_existentes = request.POST.get('demandas_alternativas_soluciones', "No disponible")
		#seccion de estado/Logros
		tiempo_disponible = request.POST.get('demanda_tiempo_disponibilidad', "No disponible")
		tiempo_unidad = request.POST.get('select_demanda_tiempo', None)
		lugar_donde_necesita = request.POST.get('demanda_lugar_donde_necesita', "No disponible")
		#seccion de copia de datos a la demanda a modificar
		#seccion informacion

		if perfil_cliente == "None":
			perfil_cliente =""

		if perfil_beneficiario == "None":
			perfil_beneficiario = ""

		if importancia_resolver_necesidad == "None":
			importancia_resolver_necesidad = ""

		if alternativas_soluciones_existentes== "None":
			alternativas_soluciones_existentes= ""

		if lugar_donde_necesita== "None":
			lugar_donde_necesita= ""

		demanda_editada = demanda
		demanda_editada.nombre = nombre
		demanda_editada.descripcion = descripcion
		demanda_editada.dominio = dominio
		demanda_editada.subdominio = subdominio
		demanda_editada.fecha_creacion = fecha_actual
		#seccion perfiles
		demanda_editada.perfil_cliente = perfil_cliente
		demanda_editada.perfil_beneficiario = perfil_beneficiario
		#seccion industria
		demanda_editada.importancia_resolver_necesidad = importancia_resolver_necesidad
		demanda_editada.alternativas_soluciones_existentes = alternativas_soluciones_existentes
		#seccion de estado
		demanda_editada.lugar_donde_necesita = lugar_donde_necesita

		#manejo de la duracion de la demanda
		if tiempo_disponible != "" and tiempo_unidad != "":

			if tiempo_unidad == "0":
				tiempo_unidad = "Mes/es"
			else:
				tiempo_unidad = "Año/s"

			demanda_editada.tiempo_para_estar_disponible = str(tiempo_disponible) + " " + tiempo_unidad
		else:
			demanda_editada.tiempo_para_estar_disponible = "1 Año/s"

		#manejo de tags
		try:
			palabra_clave = PalabraClave.objects.filter(demandas_con_esta_palabra=demanda)
			tags = []

			for t in palabra_clave:
				tags.append(t.palabra.encode('utf-8','ignore'))

			etiqueta_json= json.dumps(tags)
			args['tags']=etiqueta_json
		except:
			palabras_claves =  ["Null", "Null", "Null", "Null"]

		galeria = ImagenDemanda.objects.all().filter(fk_demanda_id = demanda.id_demanda)
		demanda_editada.save()
		args.update(csrf(request))
		args['demanda_tiempo']=demanda_tiempo
		args['demanda_duracion']=demanda_duracion
		args['demanda'] = demanda_editada
		args['msg'] = "Borrador de demanda modificado exitosamente"
		args['imagen_principal'] = galeria.first()
		args['palabras'] = demanda.palabras_clave.all
		#return render_to_response('administrar_borrador_demanda.html',args)
		return HttpResponseRedirect('/AdministrarBorradorDemanda/'+id_demanda)

	else:
		args.update(csrf(request))
		args['demanda_tiempo']=demanda_tiempo
		args['demanda_duracion']=demanda_duracion
		args['demanda'] = demanda
		print "DESCRIPCION DEMANDA:::::::::::  ",demanda.descripcion
		return render_to_response('editar_borrador_demanda.html',args)



"""
Autor: David Vinces
Nombre de la funcion: lista_comentarios_aceptados
Entrada: request 
Salida: Respuesta html
Descripción: Esta función permite mostrar el listado de comentarios aceptados de una oferta
"""
@login_required
def lista_comentarios_aceptados(request):
	if request.is_ajax():
		args={}



		try:
			#Obtiene la oferta de la base de datos, en base a la oferta obtenida del request
			oferta = Oferta.objects.get(id_oferta=request.GET['oferta'])
			#Obtiene el comentario de la base de datos, en base al id de la oferta obtenida del request
			lista_comentarios = ComentarioCalificacion.objects.filter(fk_oferta = oferta.id_oferta)
			#Guarda variables para la plantilla
			args['lista_comentarios'] = lista_comentarios
			args['oferta']=oferta
			args.update(csrf(request))
			#Renderiza y Envia la plantilla html donde se muestran los comentarios
			return render(request,'comentario_oferta.html',args)

		#Si la oferta no existe, registra un mensaje en el log
		except Oferta.DoesNotExist:
			print '>> Oferta no existe'

		#Si el comentario no existe, registra un mensaje en el log
		except ComentarioCalificacion.DoesNotExist:
			print '>> Comentario no existe'

		#Si un error inesperado ocurre, registra un mensaje en el log
		except:
			print '>> Excepcion no controlada'

	else:
		return redirect('/NotFound')


"""
Autor: Ray Montiel
Nombre de la funcion: equipo_oferta
Entrada: Oferta
Salida: Muestra el equipo de una oferta
Descripción:Esta función permite mostrar el equipo de una oferta
"""
@login_required
def equipo_oferta(request):
	sesion = request.session['id_usuario']
	usuario = Perfil.objects.get(id=sesion)
	args = {}
	args['es_admin']=request.session['es_admin']
	#si el usuario EXISTE asigna un arg para usarlo en el template
	if usuario is not None:
		args['usuario'] = usuario
	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	#si encuentra el ajax del template
	if request.is_ajax():
		#Try para la oferta, si no existe te envia al except y redirecciona la misma página
		try:
			oferta = Oferta.objects.get(id_oferta=request.GET['oferta'])
			lista_equipo= MiembroEquipo.objects.filter(fk_oferta_en_que_participa = oferta.id_oferta)
			args['listaEquipo'] = lista_equipo
			args['oferta']=oferta
			args.update(csrf(request))
			return render(request,'equipo_oferta.html',args)

		except Oferta.DoesNotExist:
			print 'esa oferta no existe '
			return redirect('/')

		except MiembroEquipo.DoesNotExist:
			print 'Este pana no tiene amigos :/'
			return redirect('/')

		except:
			print 'ya me jodi =('
			return redirect('/')

	else:
		return redirect('/NotFound')


"""
Autor: Angel Guale
Nombre de la funcion: equipo_editable_oferta
Entrada: Lista del equipo de una oferta
Salida: None
Descripción:Esta función permite editar el estado del equipo de una oferta
"""
@login_required
def equipo_editable_oferta(request):

	if request.is_ajax():
		args={}

		try:
			oferta = Oferta.objects.get(id_oferta=request.GET['oferta'])
			lista_equipo= MiembroEquipo.objects.filter(fk_oferta_en_que_participa = oferta.id_oferta, estado_membresia=1)
			args['listaEquipo'] = lista_equipo
			args['oferta']=oferta
			args.update(csrf(request))
			return render(request,'equipo_editable.html',args)

		except Oferta.DoesNotExist:
			return redirect('/')

		except MiembroEquipo.DoesNotExist:
			return redirect('/')

		except:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

	else:
		return redirect('/NotFound')



"""
Autor: Ray Montiel
Nombre de la funcion: Autocompletar_Participante
Entrada:
Salida: Muestra los usuarios disponibles para agregarlos a la oferta
Descripción:Esta función permite mostrar los participantes autocompletando sus nombres y usernames
"""
class Autocompletar_Participante(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self,request,*args,**kwargs):
		user = request.query_params.get('term',None)
		usuarios = User.objects.filter(username__icontains=user)[:5]
		serializador = UsuarioSerializador(usuarios,many=True)
		response = Response(serializador.data)
		return response



"""
Autor: Ray Montiel
Nombre de la funcion: solicitar_membresia_oferta
Entrada: Oferta, Comentario
Salida: Usuario asignado a una oferta
Descripción:Envia una solicitud para participar en una Oferta
"""
@login_required
def solicitar_membresia_oferta(request):
	if request.method=="POST":
		args={}

		try:
			oferta = Oferta.objects.get(id_oferta=request.POST['oferta'])
			solicitud_membresia = MiembroEquipo.objects.get(fk_oferta_en_que_participa=oferta.id_oferta,
															fk_participante=request.user.id)

			#Si la membresia ya existe(ya fue solicitada) y fue RECHAZADA(estado = -1), permitira guardar solo los cambios nuevos como comentario y estado
			if solicitud_membresia is not None and solicitud_membresia.estado==-1 :
				solicitud_membresia.rol_participante = "Miembro del Equipo de la Oferta"
				solicitud_membresia.estado_membresia = 0
				solicitud_membresia.fecha_aceptacion = datetime.datetime.now()
				solicitud_membresia.comentario_peticion= request.POST['comentario_peticion']
				solicitud_membresia.save()
				response = JsonResponse({'save_estado':True})
				return HttpResponse(response.content)

		except Oferta.DoesNotExist:
			args['mensaje_error'] = "La oferta no se encuentra en la red, lo sentimos."
			return render_to_response('problema_oferta.html',args)

		except MiembroEquipo.DoesNotExist:
				#si la membresia no existe, entonces procedo a guardar en la base esta solicitud
				solicitud_membresia = MiembroEquipo()
				solicitud_membresia.es_propietario = False
				solicitud_membresia.rol_participante = "Miembro del Equipo de la Oferta"
				solicitud_membresia.estado_membresia = 0
				solicitud_membresia.fk_participante = request.user.perfil
				solicitud_membresia.fk_oferta_en_que_participa = oferta
				solicitud_membresia.fecha_aceptacion = datetime.datetime.now()
				solicitud_membresia.comentario_peticion= request.POST['comentario_peticion']
				solicitud_membresia.save()
				response = JsonResponse({'save_estado':True})
				return HttpResponse(response.content)

		except:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

	else:
		return redirect('/')

"""
Autor: Ray Montiel
Nombre de la funcion: agregar_participante
Entrada: nombre de usuario y rol
Salida: Agrega al participante a la oferta
Descripción:Agrega a un participante a una oferta
"""
def agregar_participante(request):

	if request.method=="POST":
		sesion = request.session['id_usuario']
		usuario = Perfil.objects.get(id=sesion)
		args = {}
		participante = Perfil.objects.get(username = request.POST['particOferta'])
		rol = request.POST['rolNuevoIntegrante']
		oferta_admin = request.POST['ofertaAdmin']

		if usuario is not None:
			#Guardo en la variable de sesion a usuario.
			args['usuario'] = usuario
			print usuario.username
		else:
			args['error'] = "Error al cargar los datos"
			return HttpResponseRedirect('/NotFound/')

		try:#Si encuentra la oferta y la membresia
			oferta = Oferta.objects.get(id_oferta=oferta_admin)
			membresia = MiembroEquipo.objects.get(fk_oferta_en_que_participa=oferta.id_oferta,
												  fk_participante = participante)

			if membresia is not None:
				return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
		#si la oferta no existe redirige a un mensaje de error
		except Oferta.DoesNotExist:
			args['mensaje_error'] = "La oferta no se encuentra en la red, lo sentimos."
			return render_to_response('problema_oferta.html',args)
		#si la membresia no existe, entonces agrega a la persona
		except MiembroEquipo.DoesNotExist:
			print 'Membresia no existe'
			membresia = MiembroEquipo()
			membresia.es_propietario = False
			membresia.rol_participante = rol
			membresia.estado_membresia = 1
			membresia.fk_participante = participante.perfil
			membresia.fk_oferta_en_que_participa = oferta
			membresia.fecha_aceptacion = datetime.datetime.now()
			membresia.save()
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

	else:
		return HttpResponseRedirect('/Not Found')

"""
Autor: Roberto Yoncon
Nombre de funcion: publicar_borrador
Parametros: request, id de una oferta
Salida: 
Descripcion: cambia el estado de una oferta de 0 a 1, mostrandola como publicada
"""
@login_required
def publicar_borrador(request, id_oferta):
	session = request.session['id_usuario']
	usuario = Perfil.objects.get(id=session)
	args = {}
	args['es_admin']=request.session['es_admin']

	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario

	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	try:
		oferta = Oferta.objects.get(id_oferta = id_oferta)
	except:
		return HttpResponseRedirect('/NotFound/')
	if (oferta.publicada == 1):
		return HttpResponseRedirect('/NotFound/')

	oferta.fecha_publicacion = datetime.datetime.now()
	oferta.publicada = 1
	oferta.es_publica = 1
	oferta.save()
	args['oferta'] = oferta
	args['msg'] = "Oferta publicada exitosamente"
	return render_to_response('oferta_inicio.html',args)



"""
Autor: Roberto Yoncon
Nombre de funcion: publicar_borrador_demanda
Parametros: request, id de una demanda
Salida: 
Descripcion: cambia el estado de una demanda de 0 a 1, mostrandola como publicada
"""
@login_required
def publicar_borrador_demanda(request, id_demanda):
	session = request.session['id_usuario']
	usuario = Perfil.objects.get(id=session)
	args = {}
	args['es_admin']=request.session['es_admin']

	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario

	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	try:
		demanda = Demanda.objects.get(id_demanda = id_demanda)
	except:
		return HttpResponseRedirect('/NotFound/')
	if (demanda.publicada == 1):
		return HttpResponseRedirect('/NotFound/')

	demanda.fecha_publicacion = datetime.datetime.now()
	demanda.publicada = 1
	demanda.es_publica = 1
	demanda.save()
	args['demanda'] = demanda
	args['msg'] = "Demanda publicada exitosamente"
	return render_to_response('demanda_inicio.html',args)



"""
Autor: Roberto Yoncon
Nombre de funcion: eliminar_borrador
Parametros: request, id de una oferta
Salida: 
Descripcion: elimina un borrador de oferta de la base de datos
"""
@login_required
def eliminar_borrador(request, id_oferta):
	sesion = request.session['id_usuario']
	usuario = Perfil.objects.get(id=sesion)
	args = {}
	args['es_admin']=request.session['es_admin']

	#verificar que el usuario exista
	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario
	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	#verificar que la oferta que se quiere eliminar exista
	try:
		oferta = Oferta.objects.get(id_oferta = id_oferta)
	except:
		return HttpResponseRedirect('/NotFound/')

	oferta.delete()
	args['msg'] = "Borrador de oferta eliminado exitosamente"
	return render_to_response('oferta_inicio.html',args)


"""
Autor: Roberto Yoncon
Nombre de funcion: eliminar_borrador_demanda
Parametros: request, id de una demanda
Salida: 
Descripcion: elimina un borrador de demanda de la base de datos
"""
@login_required
def eliminar_borrador_demanda(request, id_demanda):
	sesion = request.session['id_usuario']
	usuario = Perfil.objects.get(id=sesion)
	args = {}
	args['es_admin']=request.session['es_admin']

	#verificar que el usuario exista
	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario
	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	#verificar que la demanda que se quiere eliminar exista
	try:
		demanda = Demanda.objects.get(id_demanda = id_demanda)
	except:
		return HttpResponseRedirect('/NotFound/')

	demanda.delete()
	args['msg'] = "Borrador de demanda eliminado exitosamente"
	return render_to_response('demanda_inicio.html',args)


"""Autor: Angel Guale

"""
def aceptar_peticion(request):
	if request.method=="POST":
		session = request.session['id_usuario']
		usuario = Perfil.objects.get(id=session)
		id_user_peticion=request.POST["id_user_peticion"]
		id_oferta=request.POST["id_oferta"]
		rol_participante=request.POST["rol"]
		args = {}
		oferta=Oferta.objects.get(id_oferta=id_oferta);
		solicitud_membresia = MiembroEquipo.objects.filter(fk_oferta_en_que_participa=id_oferta,fk_participante=id_user_peticion).first()
		if solicitud_membresia is not None:
			solicitud_membresia.estado_membresia=1
			solicitud_membresia.rol_participante=rol_participante
			solicitud_membresia.save()

			return HttpResponse("ok")
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return HttpResponseRedirect('NotFound');

"""Autor: Angel Guale

"""
def rechazar_peticion(request):
	if request.method=="POST":
		session = request.session['id_usuario']
		usuario = Perfil.objects.get(id=session)
		id_user_peticion=request.POST["id_user_peticion"]
		id_oferta=request.POST["id_oferta"]
		#rol_participante=request.POST["rol"]
		args = {}
		oferta=Oferta.objects.get(id_oferta=id_oferta);
		solicitud_membresia = MiembroEquipo.objects.filter(fk_oferta_en_que_participa=id_oferta,fk_participante=id_user_peticion).first()
		if solicitud_membresia is not None:
			solicitud_membresia.estado_membresia=-1
			solicitud_membresia.save()
			#response = JsonResponse({'aceptado':"True"})
			#return HttpResponse(response.content)
			return HttpResponse("ok")
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return HttpResponseRedirect('NotFound');


def editar_rol_membresia(request):
	if request.method=="POST":
		session = request.session['id_usuario']
		usuario = Perfil.objects.get(id=session)
		id_user_peticion=request.POST["id_user_editable"]
		id_oferta=request.POST["id_oferta"]
		rol_participante=request.POST["rol"]
		args = {}
		oferta=Oferta.objects.get(id_oferta=id_oferta);
		solicitud_membresia = MiembroEquipo.objects.filter(fk_oferta_en_que_participa=id_oferta,fk_participante=id_user_peticion).first()
		if solicitud_membresia is not None:
			solicitud_membresia.rol_participante=rol_participante
			solicitud_membresia.save()
			#response = JsonResponse({'aceptado':"True"})
			#return HttpResponse(response.content)
			return HttpResponse("ok")
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return HttpResponseRedirect('NotFound');


def calificacion_resolver_demanda(request):
	if request.method=="POST":
		session = request.session['id_usuario']
		usuario = Perfil.objects.get(id=session)
		id_oferta=request.POST["id_oferta"]
		id_demanda=request.POST["id_demanda"]
		calificacion=request.POST["calificacion"]
		print calificacion
		args = {}
		oferta=Oferta.objects.get(id_oferta=id_oferta)
		demanda=Demanda.objects.get(id_demanda=id_demanda)
		resolucion_demanda = ResolucionDemanda.objects.filter(fk_demanda_que_aplica = id_demanda,fk_oferta_demandante=id_oferta).first()
		if resolucion_demanda is not None:
			resolucion_demanda.calificacion=calificacion
			#print calificacion
			resolucion_demanda.save()
			#response = JsonResponse({'aceptado':"True"})
			#return HttpResponse(response.content)
			return HttpResponse("ok")
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return HttpResponseRedirect('/NotFound');


def editar_estado_membresia(request):
	if request.method=="POST":
		session = request.session['id_usuario']
		usuario = Perfil.objects.get(id=session)
		id_user_peticion=request.POST["id_user_editable"]
		id_oferta=request.POST["id_oferta"]
		estado_str=request.POST["estado"]
		activo=1
		if estado_str=="ACTIVO":
			activo=1
		else:
			activo=0
		args = {}
		oferta=Oferta.objects.get(id_oferta=id_oferta);
		solicitud_membresia = MiembroEquipo.objects.filter(fk_oferta_en_que_participa=id_oferta,fk_participante=id_user_peticion).first()
		if solicitud_membresia is not None:
			solicitud_membresia.activo=activo
			solicitud_membresia.save()
			#response = JsonResponse({'aceptado':"True"})
			#return HttpResponse(response.content)
			return HttpResponse("ok")
		else:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return HttpResponseRedirect('NotFound');


def editar_estado_demanda(request):
	if request.method=="POST":
		session = request.session['id_usuario']
		usuario = Perfil.objects.get(id=session)
		id_demanda=request.POST["id_demanda"]
		estado_str=request.POST["estado"]
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


"""
Autor: David Vinces
Nombre de funcion: aceptar_comentario
Parametros: request, id de un comentario
Salida: Redireccion a Administrar Oferta
Descripcion: Cambia el estado de un comentario de una oferta para que sea visible
"""
@login_required
def aceptar_comentario(request, id_comentario):
	try:
		#Obtenemos el comentario de la base a la que hace referencia el id_comentario
		comentario = ComentarioCalificacion.objects.get(id_comentario_calificacion = id_comentario)
		#Seteamos el comentario a 1, que significa Aceptado y guardamos en la base
		comentario.estado_comentario = 1
		oferta_id = comentario.fk_oferta.id_oferta
		comentario.save()

	#Si algo no funciona se redirecciona No Encontrado
	except:
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

	return HttpResponseRedirect('/administrarOferta/'+str(oferta_id))


"""
Autor: David Vinces
Nombre de funcion: rechazar_comentario
Parametros: request, id de un comentario
Salida: Redireccion a Administrar Oferta
Descripcion: Cambia el estado de un comentario de una oferta para rechazarlo
"""
@login_required
def rechazar_comentario(request, id_comentario):
	try:
		#Obtenemos el comentario de la base a la que hace referencia el id_comentario
		comentario = ComentarioCalificacion.objects.get(id_comentario_calificacion = id_comentario)
		#Seteamos el comentario a -1, que significa Rechazado y guardamos en la base
		comentario.estado_comentario=-1
		oferta_id = comentario.fk_oferta.id_oferta
		comentario.save()

	#Si algo no funciona se redirecciona No Encontrado
	except:
		return HttpResponseRedirect('/NotFound/')

	return HttpResponseRedirect('/administrarOferta/'+str(oferta_id))


"""
Autor: David Vinces
Nombre de funcion: enviar_comentario
Parametros: request
Salida: Respuesta json
Descripcion: Crea un comentario de una oferta con estado_comentario=0, es decir pendiente
"""
@login_required
def enviar_comentario(request):
	if request.method=="POST":

		try:
			#Obtenemos la oferta, el usario, la calificacion y el mensaje del comentario
			oferta = Oferta.objects.get(id_oferta=request.POST['oferta'])
			usuario = Perfil.objects.get(id=request.user.id)
			calificacion = request.POST['calificacion']
			mensaje = request.POST['comentario_peticion']
			#Creamos un Objeto Comentario y guardamos los datos
			comentario = ComentarioCalificacion()
			comentario.calificacion = calificacion
			comentario.comentario = mensaje
			comentario.estado_comentario=0
			comentario.fecha_comentario = datetime.datetime.now()
			comentario.fk_oferta = oferta
			comentario.fk_usuario = usuario
			comentario.save()

			#Se calcula el promedio total de la calificacion del comentario y se actualiza la oferta
			#Solo si el comentario es el primero, es decir que tiene calificacion (diferente -1)
			if not comentario.calificacion == -1 :
				promedio_calificacion = ComentarioCalificacion.objects.filter(fk_oferta=request.POST['oferta']).aggregate(average_cal=Avg('calificacion'))
				oferta.calificacion_total = promedio_calificacion["average_cal"]
				oferta.save()

			#Se retorna la respuesta en Json
			response = JsonResponse({})
			return HttpResponse(response.content)

		#Si algo no funciona se envia el codigo Http correspondiente
		except Exception as e:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

	else:
		return redirect('/')


"""
Autor: Rolando Sornoza
Nombre de funcion: verCualquierDemaanda
Parametros: request
Salida: http
Descripcion: funcion para ver una demanda publicada
"""
@login_required
def ver_cualquier_demanda(request, id_demanda):
	usuario = Perfil.objects.get(id=request.session['id_usuario'])
	args = {}
	args['es_admin']=request.session['es_admin']
	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario
		#Obtengo las ofertas de las que soy dueño
		ofertas = MiembroEquipo.objects.filter(fk_participante=usuario.id_perfil,es_propietario=1)
		args['ofertas']=ofertas

		#Obtengo la demanda
		try:
			demanda = Demanda.objects.get(id_demanda = id_demanda)
			estado = demanda.estado
			if estado==4:
				args['mensaje_error'] = "La Demanda no se encuentra disponible, lo sentimos."
				return render_to_response('problema_oferta.html',args)
			args['demanda'] = demanda
			args['fecha_publicacion_demanda'] = demanda.fecha_publicacion.strftime('%Y-%m-%d')
			args['estado'] = estado
		#Si algo sale mal entonces la demanda no existe.
		except:
			args['mensaje_error'] = "La Demanda no se encuentra en la red, lo sentimos."
			return render_to_response('problema_oferta.html',args)

		#Si no esta publicada, retorno mensaje correspondiente.
		if demanda.publicada == 0 :
			args.update(csrf(request))
			args['mensaje_error'] = "La demanda "+demanda.nombre+", no esta actualmente publicada."
			return render_to_response('problema_oferta.html',args)

		#Si llego hasta este punto, la demanda es viable de presentar
		else:
			propietario = demanda.fk_perfil
			comentariosDemanda = ComentarioDemanda.objects.filter(fk_demanda =id_demanda)
			args['num_comentarios'] = ComentarioDemanda.objects.filter(fk_demanda=id_demanda,
																	  fk_usuario=usuario).count
			#Intento obtener las palabras claves, sino relleno un arreglo vacio.
			try:
				palabras_claves = demanda.palabras_clave.all()
			except Exception as e:
				palabras_claves =  ["Null", "Null", "Null", "Null"]
			#Intento obtener las imagenes, sino retorno false, para manejarlas en el template.
			try:
				imagenes = ImagenDemanda.objects.filter(fk_demanda = id_demanda)
				imagenPrincipal = ImagenDemanda.objects.filter(fk_demanda = id_demanda).first()
				if not imagenes:
					imagenes =  False
					imagenPrincipal =  False

			except Exception as e:
				imagenes = False
				imagenPrincipal = False
			#Lista de comentarios aceptados.
			aceptados = ComentarioDemanda.objects.filter(fk_demanda = id_demanda,
														 estado_comentario=1).count
		#Envio de parametros.
		args.update(csrf(request))
		args['imagenes_demanda'] = imagenes
		args['imagen_principal'] = imagenPrincipal
		args['palabras_claves'] = palabras_claves
		args['comentarios_demanda'] = comentariosDemanda
		args['comentarios_aceptados'] = aceptados
		args['propietario'] = propietario
		return render_to_response('demanda_ver_otra.html',args)
	# Si algo sale mal.
	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')
"""
Autor: Andres Sornoza, David Vinces
Nombre de funcion: enviarComentarioDemanda
Parametros: request
Salida:
Descripcion: crea un comentario de una demanda con estado_comentario=0, es decir pendiente
"""
@login_required
def enviar_comentario_demanda(request):
	if request.method=="POST":
		args={}
		try:
			print "entro al try"
			demanda = Demanda.objects.get(id_demanda=request.POST['demanda'])
			usuario = Perfil.objects.get(id=request.user.id)
			mensaje = request.POST['comentario_peticion']
			comentario = ComentarioDemanda()
			comentario.comentario = mensaje
			comentario.estado_comentario=0
			comentario.fecha_comentario = datetime.datetime.now()
			comentario.fk_demanda = demanda
			comentario.fk_usuario = usuario
			comentario.save()
			response = JsonResponse({})
			return HttpResponse(response.content)
		except Exception as e:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return redirect('/')

"""
Autor: Andres Sornoza, David Vinces
Nombre de la funcion: listaComentariosAceptadosDemandas
Entrada:
Salida: Muestra la lista de Comentarios Aceptados de una demanda
Descripción:Esta función permite mostrar el listado de comentarios aceptados de una Demanda
"""
@login_required
def lista_comentarios_aceptados_demandas(request):
	"""print 'listaComentariosAceptadosDemandas :: ajax con id '+ request.GET['oferta']"""
	if request.is_ajax():
		args={}
		try:
			demanda = Demanda.objects.get(id_demanda=request.GET['demanda'])
			listaComentarios= ComentarioDemanda.objects.filter(fk_demanda = demanda.id_demanda)
			args['lista_comentarios'] = listaComentarios
			args['demanda']=demanda
			args.update(csrf(request))
			return render(request,'comentario_demanda.html',args)
		except Demanda.DoesNotExist:
			print '>> Demanda no existe'
		except ComentarioDemanda.DoesNotExist:
			print '>> Comentario de Demanda no existe'
		except:
			print '>> Excepcion no controlada'
	else:
		return redirect('/NotFound')


"""
Autor: David Vinces
Nombre de funcion: aceptarComentarioDemanda
Parametros: request, id de un comentario
Salida: 
Descripcion: cambia el estado de un comentario de una demanda para que sea visible
"""
@login_required
def aceptar_comentario_demanda(request, id_comentario):
	try:
		comentario = ComentarioDemanda.objects.get(id_comentario_calificacion = id_comentario)
		comentario.estado_comentario = 1
		demanda_id = comentario.fk_demanda.id_demanda
		comentario.save()
	except:
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

	return HttpResponseRedirect('/administrarDemanda/'+str(demanda_id))

"""
Autor: David Vinces
Nombre de funcion: rechazarComentarioDemanda
Parametros: request, id de un comentario
Salida: 
Descripcion: cambia el estado de un comentario de una demanda para eliminarlo
"""
@login_required
def rechazar_comentario_demanda(request, id_comentario):
	try:
		comentario = ComentarioDemanda.objects.get(id_comentario_calificacion = id_comentario)
		comentario.estado_comentario=-1
		demanda_id = comentario.fk_demanda.id_demanda
		comentario.save()
	except:
		return HttpResponseRedirect('/NotFound/')

	return HttpResponseRedirect('/administrarDemanda/'+str(demanda_id))

"""
Autor: Pedro Iniguez
Nombre de funcion: administarBorrador
Parametros: request
Salida:
Descripcion: funcion para administrar mi oferta publicada.
"""

@login_required
def administrar_Borrador_Demanda(request, id_demanda):
	session = request.session['id_usuario']
	usuario = Perfil.objects.get(id=session)
	args = {}
	args['es_admin']=request.session['es_admin']

	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario

	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')

	try:
		demanda = Demanda.objects.get(id_demanda = id_demanda)
	except:
		return HttpResponseRedirect('/NotFound/')

	if (demanda.publicada == 1 or demanda.fk_perfil_id!=usuario.id_perfil):
		return HttpResponseRedirect('/NotFound/')

	galeria = ImagenDemanda.objects.all().filter(fk_demanda_id = demanda.id_demanda)

	args.update(csrf(request))
	args['dueno'] = usuario.first_name + ' ' + usuario.last_name
	args['demanda'] = demanda
	args['fecha_creacion_demanda'] = demanda.fecha_creacion.strftime('%Y-%m-%d')
	args['galeria'] = galeria
	args['imagen_principal'] = galeria.first()
	args['palabras'] = demanda.palabras_clave.all
	return render_to_response('administrar_borrador_demanda.html',args)




"""
Autor: Rolando Sornoza
Nombre de funcion: administrarDemanda
Parametros: request
Salida:
Descripcion: funcion para administrar mi demanda publicada.
"""

@login_required
def administrar_demanda(request, id_demanda):
	session = request.session['id_usuario']
	usuario = Perfil.objects.get(id=session)
	args = {}
	args['es_admin']=request.session['es_admin']
	if usuario is not None:
		#Guardo en la variable de sesion a usuario.
		args['usuario'] = usuario
		try:
			demanda = Demanda.objects.get(id_demanda = id_demanda)
			args['demanda'] = demanda
			args['fecha_publicacion_demanda'] = demanda.fecha_publicacion.strftime('%Y-%m-%d')
			solicitudes = ResolucionDemanda.objects.filter(fk_demanda_que_aplica = demanda)
			args['solicitudes'] = solicitudes
		except:
			args['mensaje_error'] = "La Demanda no se encuentra en la red, lo sentimos."
			return render_to_response('problema_oferta.html',args)


		if demanda.publicada == 0 :
			args.update(csrf(request))
			args['mensaje_error'] = "La demanda "+demanda.nombre+", no esta actualmente publicada."
			return render_to_response('problema_oferta.html',args)

		elif demanda.fk_perfil_id!=usuario.id_perfil:
			args.update(csrf(request))
			args['mensaje_error'] = "Usted no es el dueño de la demanda, por favor no moleste."
			return render_to_response('problema_oferta.html',args)

		else:
			propietario = demanda.fk_perfil
			comentarios_demanda = ComentarioDemanda.objects.filter(fk_demanda =id_demanda)
			args['num_comentarios'] = ComentarioDemanda.objects.filter(fk_demanda=id_demanda,
																	   fk_usuario=usuario).count
			try:
				palabras_claves = demanda.palabras_clave.all()
			except Exception as e:
				palabras_claves =  ["Null", "Null", "Null", "Null"]
			try:
				imagenes = ImagenDemanda.objects.filter(fk_demanda = id_demanda)
				imagen_principal = ImagenDemanda.objects.filter(fk_demanda = id_demanda).first()
				if not imagenes:
					imagenes =  False
					imagen_principal =  False
			except Exception as e:
				imagenes = False
				imagen_principal = False
			pendientes = ComentarioDemanda.objects.filter(fk_demanda = id_demanda,
														  estado_comentario=0)
			aceptados = ComentarioDemanda.objects.filter(fk_demanda = id_demanda,
														 estado_comentario=1).count

		args.update(csrf(request))
		args['imagenes_demanda'] = imagenes
		args['imagen_principal'] = imagen_principal
		args['palabras_claves'] = palabras_claves
		args['comentarios_demanda'] = comentarios_demanda
		args['propietario'] = propietario
		args['comentarios_pendientes'] = pendientes
		args['comentarios_aceptados']= aceptados
		return render_to_response('administrar_demanda.html',args)

	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect('/NotFound/')
"""
Autor: Ray Montiel
Nombre de la funcion: resolver_demanda
Entrada: request
Salida:HttpResponse
Descripción:Envia una solicitud para resolver en una Demanda
"""
@login_required
def resolver_demanda(request):
	if request.method=="POST":
		args={}
		try:
			demanda = Demanda.objects.get(id_demanda=request.POST['demanda'])
			ofertaSel = Oferta.objects.get(id_oferta = request.POST['oferta_escogida'])
			resolucion= ResolucionDemanda.objects.filter(fk_demanda_que_aplica = demanda.id_demanda,fk_oferta_demandante=ofertaSel.id_oferta).first()
			if resolucion is not None:
				response = JsonResponse({'save_estado':False})
				return HttpResponse(response.content)
			else:
				resolucion = ResolucionDemanda()
				resolucion.fk_oferta_demandante = ofertaSel
				resolucion.fk_demanda_que_aplica = demanda
				resolucion.resuelve = 0
				resolucion.motivo= request.POST['comentario_resolucion']
				resolucion.save()
				response = JsonResponse({'save_estado':True})
				return HttpResponse(response.content)

		except Demanda.DoesNotExist:
			args['mensaje_error'] = "La demanda no se encuentra en la red, lo sentimos."
			return render_to_response('problema_demanda.html',args)

		except:
			return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return redirect('/')


"""
Autor: Ray Montiel
Nombre de la funcion: oferta_resuelve_demanda
Entrada:
Salida: Muestra las ofertas que resuelven la demanda
Descripción:Esta función permite mostrar las ofertas que resolvieron la demanda
"""
@login_required
def oferta_resuelve_demanda(request):
	session = request.session['id_usuario']
	usuario = Perfil.objects.get(id=session)
	args = {}
	args['es_admin']=request.session['es_admin']

	if usuario is not None:
		args['usuario'] = usuario

	else:
		args['error'] = "Error al cargar los datos"
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	#obtencion del ajax
	if request.is_ajax():

		try:
			demanda = Demanda.objects.get(id_demanda=request.GET['demanda'])
			ofertas= ResolucionDemanda.objects.filter(fk_demanda_que_aplica = demanda.id_demanda)
			imagenes = ImagenOferta.objects.all()
			args['ofertas'] = ofertas
			args['imagenes'] = imagenes
			args['demanda']=demanda
			args.update(csrf(request))
			return render(request,'resuelve_demanda.html',args)

		except Oferta.DoesNotExist:
			return redirect('/')

		except Demanda.DoesNotExist:
			return redirect('/')

		except:
			return redirect('/')
	else:
		return redirect('/NotFound')
