# -*- encoding: utf-8 -*-
import random
import string
import re
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
from django.utils.timezone import now, localtime
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
from usuarios.serializers import InstitucionSerializador, PerfilSerializador, UsuarioSerializador
from django.utils import timezone
from incubacion.models import *
from incubacion.serializers import *

from usuarios.models import *
from ofertas_demandas.models import *
from django.db.models import Avg


# Create your views here.

"""
Autor: Kevin Zambrano Cortez
Nombre de funcion: inicio_incubacion
Parametros: request
Salida: render 
Descripcion: para llamar la pagina incubacion desde la barra de navegacion
"""


@login_required
def inicio_incubacion(request):
    args = {}
    args['usuario'] = request.user
    args['es_admin'] = request.session['es_admin']
    # Para el tab incubaciones de la red
    #Verificamos que las incubaciones no esten en estado censuradas
    incubaciones=Incubacion.objects.exclude(estado_incubacion=3).all()
    args['incubaciones'] = incubaciones
    #Para el tab de incubadas
    encontro=False
    incubadas = []
    for incubacion in incubaciones:
        for incubada in Incubada.objects.filter(fk_incubacion=incubacion.id_incubacion):
            for incubada1 in Incubada.objects.filter(fk_incubacion=incubacion.id_ncubacion):

                if incubada.fk_oferta.id_oferta == incubada1.fk_oferta.id_oferta:
                    if encontro == False:
                        encontro=True
                        propietario = MiembroEquipo.objects.all().filter(es_propietario=1,fk_oferta_en_que_participa=incubada.fk_oferta.id_oferta)
                        print propietario
                        if propietario.first().fk_participante == request.user.perfil:
                            consultores = len(IncubadaConsultor.objects.filter(fk_oferta_incubada=incubada.fk_oferta.id_oferta))
                            milestones = len(Incubada.objects.filter(fk_oferta=incubada.fk_oferta.id_oferta))                
                            incubadas.append((incubada, milestones, consultores))
        encontro=False

    args['incubadas'] = incubadas

    #Para el tab de consultores
    encontro=False
    incubadas = []
    for incubacion in incubaciones:
        for incubada in Incubada.objects.filter(fk_incubacion=incubacion.id_incubacion):
            for incubada1 in Incubada.objects.filter(fk_incubacion=incubacion.id_incubacion):

                if incubada.fk_oferta.id_oferta == incubada1.fk_oferta.id_oferta:
                    if encontro == False:
                        encontro=True
                        consultor= Consultor.objects.filter(fk_usuario_consultor=request.user.perfil).first()
                        if consultor:
                            if IncubadaConsultor.objects.filter(fk_consultor=consultor.id_consultor,fk_oferta_incubada=incubada.fk_oferta.id_oferta):
                                consultores = len(IncubadaConsultor.objects.filter(fk_oferta_incubada=incubada.fk_oferta.id_oferta))
                                milestones = len(Incubada.objects.filter(fk_oferta=incubada.fk_oferta.id_oferta))                
                                incubadas.append((incubada, milestones, consultores))
        encontro=False

    args['consultores'] = incubadas


    return render_to_response('inicio_incubacion.html', args)


"""
Autor: Leonel Ramirez
Nombre de funcion: InicioIncubacion
Parametros: request
Salida: pagina de incubacion
Descripcion: para llamar la pagina incubacion inicio
"""
@login_required
def ver_incubaciones(request):
    args = {}
    args['usuario'] = request.user
    request.session['mensajeError'] = None
    request.session['mensajeAlerta'] = None
    args['es_admin'] = request.session['es_admin']
    args['incubaciones'] = Incubacion.objects.filter(fk_perfil=request.user.perfil)
    return render_to_response('admin_incubacion_inicio.html', args)


"""
Autor: FaustoMora
Nombre de funcion: crear_incubacion
Parametros: request
Salida: Muetra el formulario de crear una incubacion
Descripcion: En esta pagina se puede crear incubaciones para las diferentes ofertas
y permite que solo un admin pueda crear incubaciones
"""
@login_required
def crear_incubacion(request):
    args = {}
    args['usuario'] = request.user
    args['es_admin'] = request.session['es_admin']

    # verificar que el creador de una incubacion sea admin de institucion
    if args['es_admin']:
        return render_to_response('admin_crear_incubacion.html', args)

    # caso contrario no es admin y lo redirrecciona al inicio incubacion    
    else:
        return HttpResponseRedirect('InicioIncubaciones')

"""
Autor: Jose Velez
Nombre de funcion: definir_milestone
Parametros: request
Salida: Define un milestone a una incubada
Descripcion: Se define un milestone para que la incubada pueda cumplir con las retroalimentaciones
"""
@login_required
def definir_milestone(request):
    # se recupera el identificador de la sesión actual
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

    #Obtengo todos los datos del formulario para crear un Milestone
    requerimientos = request.GET.get( 'requerimientos' )
    fechaMilestone =  request.GET.get( 'fechaMilestone' )
    fechaRetroalimentacion = request.GET.get( 'fechaRetroalimentacion' )
    importancia =  request.GET.get( 'importancia' )
    otros = request.GET.get( 'otros' )
    idIncubada = request.GET.get( 'idIncubada' )
    fechaactual = datetime.datetime.now()
    #Modifico el formato de las fechas
    listaFM =fechaMilestone.split('/') 
    listaFR=fechaRetroalimentacion.split('/') 
    fechaMilestone = ""+listaFM[2]+"-"+listaFM[0]+"-"+listaFM[1]
    fechaRetroalimentacion = ""+listaFR[2]+"-"+listaFR[0]+"-"+listaFR[1]
    #Obtengo la incubada actual
    incubada_actual = Incubada.objects.get(id_incubada=idIncubada)
    #CLONO la incubada actual para crear un nuevo Milestone
    incubada_clonada = incubada_actual
    #ID OFERTA
    id_oferta= incubada_clonada.fk_oferta.id_oferta

    print "Obtengo los datos para crear Milestone"

    #ID DIAGRAMA DE CANVAS
    id_diagrama_canvas = incubada_actual.fk_diagrama_canvas_id
    #Obtengo el DIAGRAMA DE CANVAS
    canvas_incubada = DiagramaBusinessCanvas.objects.get(id_diagrama_business_canvas=id_diagrama_canvas)
    #CLONAR EL DIAGRAMA CANVAS
    canvas_clonado = canvas_incubada
    canvas_clonado.id_diagrama_business_canvas = None
    canvas_clonado.save()
    nuevo_id_diagrama_canvas = canvas_clonado.id_diagrama_business_canvas 

    print "Diagrama de Canvas"

    #ID DIAGRAMA PORTER
    id_diagrama_porter = incubada_actual.fk_diagrama_competidores_id
    #Obtengo el DIAGRAMA DE PORTER  
    porter_incubada = DiagramaPorter.objects.get(id_diagrama_porter=id_diagrama_porter)
    #CLONAR EL DIAGRAMA DE PORTER
    porter_clonado = porter_incubada
    porter_clonado.id_diagrama_porter = None
    porter_clonado.save()
    nuevo_id_diagrama_porter =  porter_clonado.id_diagrama_porter

    print "Diagrama de porter"

    #Guardo los id de canvas y porter
    incubada_clonada.fk_diagrama_canvas_id = nuevo_id_diagrama_canvas
    incubada_clonada.fk_diagrama_competidores_id = nuevo_id_diagrama_porter
    #Creando el codigo de la incubada con los atributos de idIncubada, idDiagramaCanvas, idDiagramaPorter
    incubada_clonada.codigo = incubada_clonada.id_incubada+nuevo_id_diagrama_canvas+nuevo_id_diagrama_porter
    incubada_clonada.id_incubada = None
    incubada_clonada.save()

    print "Guardo ID canvas y porter"

    #Crea una instancia de Milestone
    milestone = Milestone()
    print "Crear la instancia de milestone"
    milestone.fecha_creacion = fechaactual
    milestone.fecha_maxima_Retroalimentacion = fechaRetroalimentacion
    milestone.fecha_maxima = fechaMilestone
    milestone.requerimientos = requerimientos
    milestone.importancia = importancia
    milestone.num_ediciones=0
    milestone.completado=False
    milestone.otros = otros
    milestone.fk_incubada_id = incubada_clonada.id_incubada
    milestone.num_ediciones=0
    milestone.save()
    print "cree el Mlestone"

"""
Autor: Leonel Ramirez 
Nombre de funcion: participar_incubacion
Parametros: request
Salida: Muetra al usuario que sus ofertas
Descripcion: En esta funcion mostrara las ofertas de un usuario para 
        participar a una incubacion
"""
@login_required
def participar_incubacion(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin'] = request.session['es_admin']
    # si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if request.is_ajax():
        try:
            ofertaParticipar = Oferta.objects.filter(publicada=1).filter(
                miembroequipo=MiembroEquipo.objects.filter(fk_participante=usuario.id_perfil, es_propietario=1))
            args['incubacion'] = request.GET['incubacion']
            args['pariciparIncubacion'] = ofertaParticipar
            return render_to_response('usuario_participar_incubacion.html', args)

        except Oferta.DoesNotExist:
            print '>> Oferta no existe'
            return redirect('/')
        except Exception as e:
            print e
            print '>> Excepcion no controlada PARTICIPAR INCUBACION'
            return redirect('/')
    else:
        return redirect('/NotFound')

"""
Autor: Leonel Ramirez
Nombre de funcion: contenido_milestone
Parametros: request
Salida: 
Descripcion: llama una funcion ajax para setear el contenido de cada milestone
"""

@login_required
def contenido_milestone(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin'] = request.session['es_admin']    
    #si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #si encuentra el ajax del template
    if request.is_ajax():
        try:
            #args['milestone'] = milestoneObjeto
            
            idMilestone = request.GET['milestoneId']
            milestone = Milestone.objects.get(id_milestone=idMilestone)
            incubada = milestone.fk_incubada

    
            if incubada:
                # Tengo que verificar que el administrador de la incubada es el usuario en sesion
                consultores = Consultor.objects.filter(fk_usuario_consultor=usuario.id_perfil)
                propietario = MiembroEquipo.objects.get(fk_oferta_en_que_participa=incubada.fk_oferta, es_propietario=1)
                
                if milestone:

                    #Validar que sea un administrador
                    if incubada.fk_incubacion.fk_perfil == usuario:
                                
                            #Ahora voy a buscar las palabras claves
                            palabras_Claves = incubada.palabras_clave.all()
                            if palabras_Claves.count() == 0:
                               palabras_Claves = False
                               args['palabras_clave'] = palabras_Claves

                            args['incubada'] = incubada
                            args['propietario'] = propietario
                            args['milestone'] = milestone
                            return render_to_response('contenido_historial_milestone.html', args)
                    
                    #Validar que sea un consultor                    
                    elif consultores:
                        consultor = Consultor.objects.get(fk_usuario_consultor=usuario.id_perfil)
                        incubadaCons=IncubadaConsultor.objects.filter(fk_consultor=consultor.id_consultor,fk_incubada=incubada.id_incubada)
                        if incubadaCons:
                            #Ahora voy a buscar las palabras claves
                            palabras_Claves = incubada.palabras_clave.all()
                            if palabras_Claves.count() == 0:
                               palabras_Claves = False
                               args['palabras_clave'] = palabras_Claves

                            args['incubada'] = incubada
                            args['propietario'] = propietario
                            args['milestone'] = milestone
                            return render_to_response('contenido_historial_milestone.html', args)


                    #Validar que sea un propietario
                    elif propietario.fk_participante.id_perfil==usuario.id_perfil:
                        #Ahora voy a buscar las palabras claves
                            palabras_Claves = incubada.palabras_clave.all()
                            if palabras_Claves.count() == 0:
                               palabras_Claves = False
                               args['palabras_clave'] = palabras_Claves

                            args['incubada'] = incubada
                            args['propietario'] = propietario
                            args['milestone'] = milestone
                            return render_to_response('contenido_historial_milestone.html', args)
                    else:
                        args['error'] = "Esta incubada no se encuentra bajo su administración"
                        return HttpResponseRedirect('/NotFound/')

                else:
                    args['error'] = "Esta incubada no se encuentra bajo su administración"
                    return HttpResponseRedirect('/NotFound/')
            else:
                args['error'] = "Esta incubada no se encuentra bajo su administración"
                return HttpResponseRedirect('/NotFound/')

        except Milestone.DoesNotExist:
            return redirect('/')
        except Incubada.DoesNotExist:
            return redirect('/')
        except:
            return redirect('/')
    else:
        print "NO INGRESO A INVITAR"
        return redirect('/NotFound')



"""
Autor: Leonel Ramirez
Nombre de funcion: inviar_oferta_incubacion
Parametros: request
Salida: envia id_oferta y id_incubacion
Descripcion: Solictud para pertenecer a una incubacion
"""

@login_required
def enviar_oferta_incubacion(request):
    session = request.session['id_usuario']
    usuario = Perfil.objects.get(id=session)
    args = {}
    args['es_admin']=request.session['es_admin']
    #si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if request.is_ajax():
            idIncubacion = request.GET['incubacion']
            idOferta = request.GET['oferta']
            idConvocatoria = request.GET['convocatoria']
            solicitudDatos = SolicitudOfertasConvocatoria()
            #enviar datos a la tabla solicitud convocatoria
            solicitudDatos.estado_solicitud = 0
            solicitudDatos.fk_convocatoria_id = idConvocatoria
            solicitudDatos.fk_oferta_id = idOferta
            solicitudDatos.fk_incubacion_id = idIncubacion
            solicitudDatos.fecha_creacion = datetime.datetime.now()
            solicitudDatos.save()
            return render_to_response('enviar_oferta_incubacion.html',args)
    else:
        return redirect('/NotFound')



"""
Autor: Jose Velez
Nombre de funcion: invitar_consultor
Parametros: request
Salida: Muetra al usuario que desea invitar como consultor
Descripcion: En esta funcion mostrara los usuario que pueden ser consultor
"""


@login_required
def invitar_consultor(request):
    try:

        # se recupera el identificador de la sesión actual
        sesion = request.session['id_usuario']
        #se obtiene el usuario de la sesión actual
        usuario = Perfil.objects.get(id=sesion)

        args = {}
        args['es_admin'] = request.session['es_admin']

        # si el usuario EXISTE asigna un arg para usarlo en el template
        if usuario is not None:
            args['usuario'] = usuario
        else:
            args['error'] = "Error al cargar los datos"
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        consultor = request.GET.get( 'consultor' )
        consultor = request.GET.get('consultor')
        usuarioconsultor = consultor.split('-')

        if usuario.username == usuarioconsultor[1]:
            args['mismousuario'] = "NO SE PUEDE SELECCIONAR EL MISMO USUARIO"
        else:

            #si encuentra el ajax del template
            if request.is_ajax():
                try:
                    invitarconsultor = Perfil.objects.get(username=usuarioconsultor[1])
                    args['invitarconsultor'] = invitarconsultor

                    return render_to_response('admin_invitar_consultor.html', args)
                except User.DoesNotExist:
                    return redirect('/')
                except:
                    return redirect('/')
            else:
                return redirect('/NotFound')

            return render_to_response('admin_invitar_consultor.html', args)
    except:
        return redirect('/')

"""
Autor: Jose Velez
Nombre de funcion: enviar_invitaciones
Parametros: request
Salida: Se envia a solicitud a todos los usuario
Descripcion: En esta funcion se guarda en la base todos los usuario que seran consultor
"""


@login_required
def enviar_invitaciones(request):
    try:
        # se recupera el identificador de la sesión actual
        sesion = request.session['id_usuario']
        #se obtiene el usuario de la sesión actual
        usuario = Perfil.objects.get(id=sesion)
        #Se inicializa la variable que va a contener los parametros del vista
        args = {}
        #Enviar como parametro si el usuario es administrador
        args['es_admin']=request.session['es_admin']
        
        #si el usuario EXISTE asigna un arg para usarlo en el template
        if usuario is not None:
            args['usuario'] = usuario
        else:
            args['error'] = "Error al cargar los datos"
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        #Se obtiene el usuario del Perfil
        usuarioPerfil = request.GET.get( 'usuarioperfil' )
        #Se obtiene el arametro por el Metodo GET
        idIncubada =  request.GET.get( 'idincubada' )
        #Se obtiene el objeto de la incuabada
        incubada = Incubada.objects.get(id_incubada=idIncubada)
        #Por medio del objeto de la incubada, se obtiene el id_incubacion
        idIncubacion = incubada.fk_incubacion.id_incubacion
        #Por medio del objeto de la incubada, de obtiene el id_oferta
        idoferta = incubada.fk_oferta.id_oferta
        fechaactual = datetime.datetime.now()

        #Se obtiene los consultores usuarios que son consultores y estan relacionado a una incubada.
        consultor = Consultor.objects.filter(fk_usuario_consultor=usuarioPerfil).filter(
            incubadaconsultor=IncubadaConsultor.objects.filter(fk_oferta_incubada_id=idoferta))

        #Se verifica si la lista de objeto de las incubadas es mayor a 0, para saber si el
        #usuario no es consultor. 
        if len(consultor) > 0:
            args['no_consultor'] = "EL USUARIO NO PUEDE SER CONSULTOR"
            print "EL USUARIO NO PUEDE SER CONSULTOR"
        elif len(consultor) == 0:

            #Verifica que el usuario exista
            consultorExiste = Consultor.objects.filter(fk_usuario_consultor=usuarioPerfil)

            if len(consultorExiste)==0:
                #Guardar en la tabla Consultor
                consultorTabla = Consultor()
                consultorTabla.fk_usuario_consultor_id = usuarioPerfil
                consultorTabla.fecha_creacion = fechaactual
                #se guardan los cambios
                consultorTabla.save()
                consultorExiste=consultorTabla
            else:
                consultorExiste=consultorExiste.first()
            #Guardar en la tabla Consultor
            incubadaconsultor = IncubadaConsultor()
            incubadaconsultor.fk_consultor_id = consultorExiste.id_consultor
            incubadaconsultor.fk_incubada_id = idIncubada
            incubadaconsultor.fecha_creacion = fechaactual
            incubadaconsultor.fk_oferta_incubada_id=idoferta
            incubadaconsultor.fk_incubacion_id=idIncubacion
            #se guardan los cambios
            incubadaconsultor.save()
    except:
        return redirect('/')


"""
Autor: Dimitri Laaz
Nombre de funcion: editar_mi_incubacion
Parametros: 
request-> petición http
id -> identificador de la incubación a editar
Salida: Vista con formulario de edición
Descripcion: Carga los datos de una incubación para psoteriormente ser editada
"""


@login_required
def editar_mi_incubacion(request, incubacionid):
    try:
        args = {}
        # se recupera el identificador de la sesión actual
        sesion = request.session['id_usuario']
        #se obtiene el usuario de la sesión actual
        usuario = Perfil.objects.get(id=sesion)
        #se actualiza el token contra ataques de Cross Site Request Forgery(CSRF)
        args.update(csrf(request))

        #se envia el usuario y la bandera de administrador como argumentos de la vista
        args['usuario'] = request.user
        args['es_admin'] = request.session['es_admin']

        #se comprueba si la incubación solicitada existe
        try:
            incubacion_editar = Incubacion.objects.get(id_incubacion=incubacionid)
            if incubacion_editar.fk_perfil.id_perfil != usuario.id_perfil:
                return HttpResponseRedirect('/VerIncubacion/' + str(incubacion_editar.id_incubacion))
        except ObjectDoesNotExist:
            return HttpResponseRedirect('/NotFound/')

        if request.method == 'POST':
            # se recuperan los datos enviados por medio de la peticion http POST
            nombreIncubacion = request.POST.get("nombre_incubacion")
            descripcionIncubacion = request.POST.get("descripcion_incubacion")
            perfilIncubacion = request.POST.get("perfil_incubacion")
            condicionesIncubacion = request.POST.get("condiciones_incubacion")
            tipoIncubacion = request.POST.get("select_tipo_incubacion")

            #validación de los campos por medio de expresiones regulares
            nombreValido = re.search(u'^([áéíóúÁÉÍÓÚñÑ\w]\s?){10,300}$', nombreIncubacion)
            descripcionValido = re.search(u'^([áéíóúÁÉÍÓÚñÑ\w]\s?[,;.:]?\s?)+$', descripcionIncubacion)
            perfilValido = re.search(u'^([áéíóúÁÉÍÓÚñÑ\w]\s?[,;.:]?\s?)+$', perfilIncubacion)
            condicionesValido = re.search(u'^([áéíóúÁÉÍÓÚñÑ\w]\s?[,;.:]?\s?)+$', condicionesIncubacion)
            tipoValido = re.search(u'^[012]$', tipoIncubacion)

            #se cambian los datos de la incubacion
            incubacion_editar.nombre = nombreIncubacion
            incubacion_editar.descripcion = descripcionIncubacion
            incubacion_editar.perfil_oferta = perfilIncubacion
            incubacion_editar.condiciones = condicionesIncubacion
            incubacion_editar.tipos_oferta = int(tipoIncubacion)

            #condicíon en caso de que un campo no este correcto
            if nombreValido is None or \
                            descripcionValido is None or \
                            perfilValido is None or \
                            condicionesValido is None or \
                            tipoValido is None:
                #se establece el mensaje de error de la operación
                args['errmsg'] = 1
                args['incubacion'] = incubacion_editar

                #se reenvia el formulario con los datos cambiados
                return render_to_response('admin_editar_mi_incubacion.html', args)


            #se guardan los cambios
            incubacion_editar.save()

            #Se establece el mensaje de éxito de la operación
            args['errmsg'] = 0

        #se envia la información de la incubación a la vista
        args['incubacion'] = incubacion_editar

        #se renderiza la vista
        return render_to_response('admin_editar_mi_incubacion.html', args)
    except:
        return redirect('/')


"""
Autor: Dimitri Laaz
Nombre de funcion: editar_estado_incubacion
Parametros: 
request-> petición http
Salida: Codigo de exito de la operación
Descripcion: Cambia el estado de una incubacion por medio de Ajax
"""
@login_required
def editar_estado_incubacion(request):
    if request.is_ajax():
        try:
            args = {}
            # se recupera el identificador de la sesión actual
            sesion = request.session['id_usuario']
            #se obtiene el usuario de la sesión actual
            usuario = Perfil.objects.get(id=sesion)
            #se recupera el id de la incubacion a cambiarle el estado
            incubacionid = request.GET.get("incubacion")
            #se recupera el nuevo estado a ser fijado
            estado_nuevo = request.GET.get("estado")
            # se valida que que el estado enviado tengo un valor valido
            estadoValido = re.search(u'^[12]$', estado_nuevo)
            if estadoValido is not None:
                try:
                    incubacion_cambiar = Incubacion.objects.get(id_incubacion=incubacionid)
                    #se valida que el usuario que solicita el cambio sea el dueño de la incubacion
                    if incubacion_cambiar.fk_perfil.id_perfil != usuario.id_perfil:
                        return HttpResponse(0)
                    #se valida que el estado actual sea activo para realizar el cambio
                    if incubacion_cambiar.estado_incubacion != 0:
                        return HttpResponse(1)
                    if incubacion_cambiar.estado_incubacion == 0:
                        #se realiza el cambio de estado si la condiciones son correctas
                        incubacion_cambiar.estado_incubacion = int(estado_nuevo)
                        incubacion_cambiar.save()
                        #se devuelve el codigo 2 de exito de la operacion
                        return HttpResponse(2)
                except ObjectDoesNotExist:
                    return HttpResponse(0)           
            else:
                return HttpResponse(3)         
        except:
            return HttpResponse(0)    
    return HttpResponseRedirect('/NotFound/')


"""
Autor: Henry Lasso
Nombre de funcion: admin_ver_incubacion
Parametros: request y id_incubacion
Salida: 
Descripcion: Mostar template ver mi incubacion desde administrador
"""

@login_required
def admin_ver_incubacion(request, id_incubacion):
    session = request.session['id_usuario']
    usuario = Perfil.objects.get(id=session)
    args = {}
    args.update(csrf(request))
    args['es_admin'] = request.session['es_admin']


    # Para que las variables de session sena colocadas en args[]
    if usuario is not None:
        args['usuario'] = usuario
        try:
            #obtengo la incubacion por medio del id enviado por la url
            incubacion = Incubacion.objects.get(id_incubacion=id_incubacion)
            #valido que el usuario sea dueño de la incubacion
            if incubacion.fk_perfil == usuario:    
                if incubacion:
                    #listo las convocatorias de la incubación
                    convocatorias_incubacion = Convocatoria.objects.all().filter(fk_incubacion_id=id_incubacion).last()
                    if convocatorias_incubacion is not None:
                        hoy = datetime.datetime.now(timezone.utc)
                        fecha_maxima = convocatorias_incubacion.fecha_maxima
                        # si la fecha maxima es menor a hoy no hay una convocatoria abierta
                        if fecha_maxima <= hoy:
                            args['convocatoria'] = False
                        else:
                            args['convocatoria'] = convocatorias_incubacion

                    else:
                        args['convocatoria'] = False

                    args['incubacion'] = incubacion
                    return render_to_response('admin_ver_incubacion.html', args)
                else:
                    args['error'] = "Esta incubada no se encuentra bajo su administración"
                    return HttpResponseRedirect('/NotFound/')
            else:
                args['error'] = "Esta incubacion no se encuentra bajo su administración"
                return HttpResponseRedirect('/NotFound/')
        except Incubacion.DoesNotExist:
            args['error'] = "La incubación no se encuentra en la red, lo sentimos."
            return HttpResponseRedirect('/NotFound/')
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect('/NotFound/')

"""
Autor: Henry Lasso
Nombre de funcion: usuario_ver_incubacion
Parametros: request y id de incubacion
Salida: render template ver incubacion desde usuario 
Descripcion: Mostar template ver mi incubacion
"""

@login_required
def usuario_ver_incubacion(request, id_incubacion):
    session = request.session['id_usuario']
    usuario = Perfil.objects.get(id=session)
    args = {}
    args['es_admin'] = request.session['es_admin']
    if usuario is not None:
        # Guardo en la variable de sesion a usuario.
        args['usuario'] = usuario
        try:
            #obtengo la incubacion por medio del id 
            incubacion = Incubacion.objects.get(id_incubacion=id_incubacion)
            

            if incubacion :
                #Lo siguiente es para poder mostrar las incubadas de la incubacion               
                incubadas = []
                incubadasIncubacion=Incubada.objects.filter(fk_incubacion=incubacion.id_incubacion)                
                #Si es que tengo incubadas puedo recorrer la lista
                idofertas =[]
                if incubadasIncubacion.first():                    
                    idofertas.append(incubadasIncubacion.first().fk_oferta.id_oferta)
                    ofertaEncontrada=False
                    for inc in incubadasIncubacion:
                        for ofe in idofertas:
                            if inc.fk_oferta.id_oferta == ofe:
                                ofertaEncontrada=True
                        if ofertaEncontrada!=True:
                            idofertas.append((inc.fk_oferta.id_oferta))
                        else:
                            ofertaEncontrada=False

                    for idofert in idofertas:
                        ultimaIncubada=Incubada.objects.filter(fk_oferta=idofert).last()
                        if ultimaIncubada:
                            propietario = MiembroEquipo.objects.all().filter(es_propietario=1,fk_oferta_en_que_participa=ultimaIncubada.fk_oferta.id_oferta).first()
                            fechapublicacion=ultimaIncubada.fecha_publicacion
                            foto=ImagenIncubada.objects.filter(fk_incubada=ultimaIncubada.id_incubada).first()
                            incubadas.append((ultimaIncubada, propietario, fechapublicacion,foto))
                    
                    args['incubadas'] = incubadas

                #Lo siguiente es para mostrar la convocatoriaa actual
                convocatorias_incubacion = Convocatoria.objects.all().filter(fk_incubacion_id=id_incubacion).last()
                if convocatorias_incubacion is not None:
                    hoy = datetime.datetime.now(timezone.utc)
                    fecha_maxima = convocatorias_incubacion.fecha_maxima
                    # verifico si hay un convocatoria abierta por medio de las fechas
                    if fecha_maxima <= hoy:
                        args['convocatoria'] = False
                    else:
                        args['convocatoria'] = convocatorias_incubacion
                else:
                    args['convocatoria'] = False

                
                #Lo siguiente es para la presentacion del boton participar
                #Primero verificaremos si el usuario es administrador de la incubacion
                if incubacion.fk_perfil == usuario:
                    administrador=True
                else:
                    administrador=False
                #Ahora debemos verificar si es un consultor de la incubacioin
                consultor=False

                for id in idofertas:
                    consultorExiste= Consultor.objects.filter(fk_usuario_consultor=usuario.id_perfil).first()
                    if consultorExiste:
                        incubada_consultor=IncubadaConsultor.objects.filter(fk_oferta_incubada=id,fk_consultor=consultorExiste.id_consultor,fk_incubacion=incubacion.id_incubacion)
                        for ic in incubada_consultor:
                            if len(incubada_consultor)>0:
                                consultor=True
                                args['idOfertaConsultor']=id

                #y ahora verificaremos si es un participante de la incubacion
                participante=False
                for id in idofertas:
                    propietario = MiembroEquipo.objects.all().filter(es_propietario=1,fk_oferta_en_que_participa=id,fk_participante=usuario.id_perfil).first()
                    if propietario:
                        participante=True

                #y ahora verificaremos si es un solicitante pendiente de la incubacion
                solicitud=False
                solicitudes=SolicitudOfertasConvocatoria.objects.all().filter(fk_incubacion=incubacion.id_incubacion,estado_solicitud=0)
                if len(solicitudes)>0:
                    for solicitud in solicitudes:
                        propietario = MiembroEquipo.objects.all().filter(es_propietario=1,fk_oferta_en_que_participa=solicitud.fk_oferta.id_oferta,fk_participante=usuario.id_perfil).first()
                        if propietario:
                            solicitud=True             


                args['administrador']=administrador
                args['consultor']=consultor
                args['participante']=participante
                args['solicitud']=solicitud


                #Necesitamos tambien mostrar la incubacion 
                args['incubacion'] = incubacion
                args.update(csrf(request))
                return render_to_response('usuario_ver_incubacion.html', args)
            else:
                args['error'] = "Esta incubacion no se encuentra en la red"
                return HttpResponseRedirect('/NotFound/')
        except Incubacion.DoesNotExist:
            args['error'] = "La incubacion no se encuentra en la red, lo sentimos."
            return HttpResponseRedirect('/NotFound/')
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect('/NotFound/')

"""
Autor: Henry Lasso
Nombre de funcion: admin_incubadas_incubacion
Parametros: request
Salida: admin_lista_incubadas desde administrador
Descripcion: Esta funcion es para la peticion Ajax que pide mostrar la lista de incubadas de la incubacion
"""

@login_required
def admin_incubadas_incubacion(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin'] = request.session['es_admin']
    # si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #si encuentra el ajax del template
    if request.is_ajax():
        try:
            incubacion = Incubacion.objects.get(id_incubacion=request.GET['incubacion'])
            if incubacion:
                #Lo siguiente es para poder mostrar las incubadas de la incubacion               
                incubadas = []
                incubadasIncubacion=Incubada.objects.filter(fk_incubacion=incubacion.id_incubacion)                
                #Si es que tengo incubadas puedo recorrer la lista
                idofertas =[]
                if incubadasIncubacion.first():                    
                    idofertas.append(incubadasIncubacion.first().fk_oferta.id_oferta)
                    ofertaEncontrada=False
                    for inc in incubadasIncubacion:
                        for ofe in idofertas:
                            if inc.fk_oferta.id_oferta == ofe:
                                ofertaEncontrada=True
                        if ofertaEncontrada!=True:
                            idofertas.append((inc.fk_oferta.id_oferta))
                        else:
                            ofertaEncontrada=False

                    for idofert in idofertas:
                        ultimaIncubada=Incubada.objects.filter(fk_oferta=idofert).last()
                        if ultimaIncubada:
                            propietario = MiembroEquipo.objects.all().filter(es_propietario=1,fk_oferta_en_que_participa=ultimaIncubada.fk_oferta.id_oferta).first()
                            fechapublicacion=ultimaIncubada.fecha_publicacion
                            foto=ImagenIncubada.objects.filter(fk_incubada=ultimaIncubada.id_incubada).first()
                            incubadas.append((ultimaIncubada, propietario, fechapublicacion,foto))
                    
                    args['incubadas'] = incubadas
            return render_to_response('admin_incubadas_de_incubacion.html',args)
        except Incubada.DoesNotExist:
            return redirect('/')
        except IncubadaConsultor.DoesNotExist:
            return redirect('/')
        except:
            return redirect('/')
    else:
        return redirect('/NotFound')


"""
Autor: Henry Lasso
Nombre de funcion: admin_solicitudes_incubacion
Parametros: request
Salida: admin_lista_solicitudes_incubacion
Descripcion: Esta funcion es para la peticion Ajax que pide mostrar la lista de ofertas aplicantes  a la incubacion
"""

@login_required
def admin_solicitudes_incubacion(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin']=request.session['es_admin']
    #si el usuario EXISTE asigna un arg para usarlo en el template
    # si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #si encuentra el ajax del template
    if request.is_ajax():
        try:
            #obtengo todas las solicitudes de las convocatorias de la incubacion
            solicitudes = SolicitudOfertasConvocatoria.objects.all().filter(fk_incubacion = request.GET['incubacion'],estado_solicitud=0) 
            
            solicitudesLista = []
            #Si es que tengo incubadas puedo recorrer la lista
            if solicitudes.first():
                for solicitud in solicitudes:
                        propietario = MiembroEquipo.objects.all().filter(es_propietario=1,fk_oferta_en_que_participa=solicitud.fk_oferta.id_oferta).first()
                        fechasolicitud=solicitud.fecha_creacion
                        foto=ImagenOferta.objects.filter(fk_oferta=solicitud.fk_oferta.id_oferta).first()
                        solicitudesLista.append((solicitud, propietario, fechasolicitud,foto))
                
                args['solicitudes'] = solicitudesLista

            return render_to_response('admin_incubacion_solicitudes.html',args)
        except Incubada.DoesNotExist:
            return redirect('/')
        except IncubadaConsultor.DoesNotExist:
            return redirect('/')
        except:
            return redirect('/')
    else:
        return redirect('/NotFound')

"""
Autor: Henry Lasso
Nombre de funcion: admin_rechazar_solicitud
Parametros: request
Salida: actualiza la solicitud con estado rechazada
Descripcion: Esta funcion es para la peticion Ajax que actualiza el estado de la solictud a rechazada
"""
@login_required
def admin_rechazar_solicitud(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin']=request.session['es_admin']
    #si el usuario EXISTE asigna un arg para usarlo en el template
    # si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #si encuentra el ajax del template
    if request.is_ajax():
        try:
            #obtengo las solicitudes pendientes de la incubacion
            solicitud= SolicitudOfertasConvocatoria.objects.get(id_solicitud_ofertas_convocatoria=request.GET['id_solicitud'])
            solicitud.estado_solicitud=2
            solicitud.save() 
        except:
            return redirect('/NotFound')
    else:
        return redirect('/NotFound')


"""
Autor: David Vinces
Nombre de funcion: admin_aceptar_solicitud
Parametros: request
Salida: actualiza la solicitud con estado aceptada
Descripcion: Esta funcion es para la peticion Ajax que actualiza el estado de la solicitud a aceptada
"""
@login_required
def admin_aceptar_solicitud(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin']=request.session['es_admin']

    #si el usuario EXISTE asigna un arg para usarlo en el template
    # si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    #si encuentra el ajax del template
    if request.is_ajax():
        try:
            print'222222222222222222222222222'
            solicitud= SolicitudOfertasConvocatoria.objects.get(id_solicitud_ofertas_convocatoria=request.GET['id_solicitud'])
            #Se crea una nueva incubada en base a la oferta dada en la solicitud
            oferta = Oferta.objects.get(id_oferta = solicitud.fk_oferta.id_oferta)
            incubada = Incubada()
            print'1111'
            #---Seccion Informacion General
            incubada.nombre = oferta.nombre
            incubada.codigo = oferta.codigo
            incubada.tipo = oferta.tipo
            incubada.descripcion = oferta.descripcion
            incubada.dominio = oferta.dominio
            incubada.subdominio = oferta.subdominio

            #---Seccion Perfiles
            incubada.perfil_cliente = oferta.perfil_cliente
            incubada.perfil_beneficiario = oferta.perfil_beneficiario

            #---Seccion Industria
            incubada.cuadro_tendencias_relevantes = oferta.cuadro_tendencias_relevantes
            incubada.descripcion_soluciones_existentes = oferta.descripcion_soluciones_existentes

            #---Seccion de Estado/Logros
            incubada.tiempo_para_estar_disponible = oferta.tiempo_para_estar_disponible
            incubada.estado_propiedad_intelectual = oferta.estado_propieada_intelectual
            incubada.evidencia_traccion = oferta.evidencia_traccion

            #---Diagrama Canvas
            diagrama_canvas = DiagramaBusinessCanvas()
            if oferta.fk_diagrama_canvas:
                diagrama_canvas.asociaciones_clave = oferta.fk_diagrama_canvas.asociaciones_clave
                diagrama_canvas.actividades_clave = oferta.fk_diagrama_canvas.actividades_clave
                diagrama_canvas.recursos_clave = oferta.fk_diagrama_canvas.recursos_clave
                diagrama_canvas.propuesta_valor = oferta.fk_diagrama_canvas.propuesta_valor
                diagrama_canvas.relacion_clientes = oferta.fk_diagrama_canvas.relacion_clientes
                diagrama_canvas.canales_distribucion = oferta.fk_diagrama_canvas.canales_distribucion
                diagrama_canvas.segmento_mercado = oferta.fk_diagrama_canvas.segmento_mercado
                diagrama_canvas.estructura_costos = oferta.fk_diagrama_canvas.estructura_costos
                diagrama_canvas.fuente_ingresos = oferta.fk_diagrama_canvas.fuente_ingresos
                
            diagrama_canvas.save()
            incubada.fk_diagrama_canvas = diagrama_canvas
            print'2222222'
            #---Diagrama Porter
            diagrama_porter = DiagramaPorter()
            if oferta.fk_diagrama_competidores:                
                diagrama_porter.competidores = oferta.fk_diagrama_competidores.competidores
                diagrama_porter.consumidores = oferta.fk_diagrama_competidores.consumidores
                diagrama_porter.sustitutos = oferta.fk_diagrama_competidores.sustitutos
                diagrama_porter.proveedores = oferta.fk_diagrama_competidores.proveedores
                diagrama_porter.nuevosMiembros = oferta.fk_diagrama_competidores.nuevosMiembros
            diagrama_porter.save()
            incubada.fk_diagrama_competidores = diagrama_porter

            #---Otras Relaciones
            equipo=MiembroEquipo.objects.filter(fk_oferta_en_que_participa=oferta.id_oferta).first()
            incubada.equipo = MiembroEquipo.objects.get(id_equipo = equipo.id_equipo)
            #incubada.palabras_clave = oferta.palabras_clave
            incubada.fk_oferta = oferta
            incubada.fk_incubacion = solicitud.fk_incubacion
            #Guardar la incubada creada
            incubada.save()
            #Copiar las imagenes de la oferta a la incubacion

            imagenes_oferta = ImagenOferta.objects.filter(fk_oferta = oferta.id_oferta)
            for o in imagenes_oferta:
                imagen_incubada = ImagenIncubada()
                imagen_incubada.imagen = o.imagen
                imagen_incubada.descripcion = o.descripcion
                imagen_incubada.fk_incubada = incubada
                imagen_incubada.save()                


            #Se crea un milestone vencido (con fecha actual)
            milestone = Milestone()
            milestone.fecha_creacion = datetime.datetime.now(timezone.utc)
            milestone.fecha_maxima_Retroalimentacion = datetime.datetime.now(timezone.utc)
            milestone.fecha_maxima = datetime.datetime.now(timezone.utc)
            milestone.requerimientos = "Primera versión de la incubada"
            milestone.importancia = "Primera version de la incubada"

            milestone.num_ediciones=milestone.num_ediciones+1
            milestone.completado=True

            milestone.otros = "Ninguno"
            #Se enlaza el milestone creado a la incubada creada
            milestone.fk_incubada = incubada
            milestone.save()         

            #Se actualiza la solicitud al estado Aceptada(estado=1)
            solicitud.estado_solicitud=1
            solicitud.save() 

        except:
            return redirect('/NotFound')

    else:
        return redirect('/NotFound')


"""
Autor: Estefania Lozano
Nombre de funcion: admin_ver_incubada
Parametros: request, id_incubada
Salida: Template admin_ver_incubada
Descripcion: Administrar una incubada de una incubacion de la cual soy dueño
"""
@login_required
def admin_ver_incubada(request, id_oferta):
    session = request.session['id_usuario']
    usuario = Perfil.objects.get(id=request.session['id_usuario'])
    args = {}
    args['es_admin'] = request.session['es_admin']
    if usuario is not None:
        args['usuario'] = usuario
        try:
            incubada = Incubada.objects.filter(fk_oferta=id_oferta).last()
            # Tengo que verificar que el administrador de la incubada es el usuario en sesion

            # Ahora tengo que indicarle al administrador que no puede ver la incubada si su incubacion esta censurada
            id_incubacion=incubada.fk_incubacion.id_incubacion
            incubacion=Incubacion.objects.filter(id_incubacion=id_incubacion).first()
            if incubacion.estado_incubacion!=2 and incubacion.estado_incubacion!=3:
                if incubada:
                    if incubada.fk_incubacion.fk_perfil == usuario:
                        propietario = MiembroEquipo.objects.get(fk_oferta_en_que_participa=incubada.fk_oferta, es_propietario=1)
                        equipo = MiembroEquipo.objects.filter(fk_oferta_en_que_participa=incubada.fk_oferta)
                        if len(equipo)>0:
                            args['equipo'] = equipo
                        fotos = ImagenIncubada.objects.filter(fk_incubada=incubada.id_incubada)
                        if fotos:
                            imagen_principal = fotos.first()
                        else:
                            fotos = False
                            imagen_principal = False

                        #Tenemos que validar si hay un mmilestone vigente
                        primer_Incubada = Incubada.objects.filter(fk_oferta=incubada.fk_oferta).first()
                        primer_milestone=Milestone.objects.filter(fk_incubada=primer_Incubada.id_incubada).first()
                        args['milestone']=primer_milestone
                        milestone = Milestone.objects.filter(fk_incubada=incubada.id_incubada).last()
                        if milestone:
                            hoy = datetime.datetime.now(timezone.utc)
                            fecha_maxima_milestone = milestone.fecha_maxima_Retroalimentacion
                            if fecha_maxima_milestone < hoy:
                                args['milestoneVigente'] = False
                            else:
                                args['milestoneVigente'] = True

                        #Ahora voy a buscar las palabras claves
                        palabras_Claves = incubada.palabras_clave.all()
                        if palabras_Claves.count() == 0:
                            palabras_Claves = False
                        args['palabras_clave'] = palabras_Claves

                        args['fotos'] = fotos
                        args['imagen_principal'] = imagen_principal
                        args['incubada'] = incubada
                        args['propietario'] = propietario
                        return render_to_response('admin_incubada.html', args)
                    else:
                        args['error'] = "Esta incubada no se encuentra bajo su administración"
                        return HttpResponseRedirect('/NotFound/')
                else:
                    args['error'] = "Esta incubada no se encuentra bajo su administración"
                    return HttpResponseRedirect('/NotFound/')
            else:
                args['error'] = "Esta incubada se encuentra en una incubación desactivada o censurada de la red."
                return HttpResponseRedirect('/NotFound/')
        # si la oferta no existe redirige a un mensaje de error
        except Incubada.DoesNotExist:
            args['error'] = "La incubada no se encuentra en la red, lo sentimos."
            return HttpResponseRedirect('/NotFound/')
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect('/NotFound/')


"""
Autor: Estefania Lozano
Nombre de funcion: admin_consultores
Parametros: request
Salida: admin_lista_consultores
Descripcion: Esta funcion es para la peticion Ajax que pide mostrar la lista de consultores de la incubada
"""

@login_required
def admin_incubada_consultores(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin'] = request.session['es_admin']
    # si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #si encuentra el ajax del template
    if request.is_ajax():
        try:
            #Debo obtener todos los consultores relacionados con la incubada, esto lo encuentro en la tabla incubadaConsultor
            incubada = Incubada.objects.get(id_incubada=request.GET['incubada'])
            consultores=IncubadaConsultor.objects.filter(fk_incubacion=incubada.fk_incubacion,fk_oferta_incubada=incubada.fk_oferta)
            #for c in incubConsult:
            #    try:
            #        print c.fk_consultor.fk_usuario_consultor.foto.url
            #    except Exception as e:
            #        print e
            args['consultores'] = consultores
            return render_to_response('consultores.html',args)

        except Incubada.DoesNotExist:
            return redirect('/')
        except IncubadaConsultor.DoesNotExist:
            return redirect('/')
        except:
            return redirect('/')
    else:
        return redirect('/NotFound')


"""
Autor: Estefania Lozano
Nombre de funcion: admin_incubada_milestone_actual
Parametros: request
Salida: ver admin_incubada_milestone_actual
Descripcion: Esta funcion es para la peticion Ajax que pide mostrar el milestone vigente en
    la vista de incubada para el administrador
"""

@login_required
def admin_incubada_milestone_actual(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin'] = request.session['es_admin']
    # si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #si encuentra el ajax del template
    if request.is_ajax():
        try:
            milestone = Milestone.objects.filter(fk_incubada=request.GET['incubada']).last()

            hoy = datetime.datetime.now(timezone.utc)
            fecha_maxima_retroal = milestone.fecha_maxima_Retroalimentacion
            fecha_maxima_completar = milestone.fecha_maxima

            print hoy
            if fecha_maxima_retroal < hoy :
                print 'fecha maxima lalalalalalalar'
                print fecha_maxima_retroal
                args['retroalimentar']=False
                args['completar'] = False
                args['milestone'] = False
                
            elif fecha_maxima_completar <hoy and hoy<= fecha_maxima_retroal:
                print fecha_maxima_retroal,'fecha maxima retroalimentar'
                args['retroalimentar']=True
                args['completar'] = False
                args['milestone'] = milestone
            else:
                print fecha_maxima_completar,'fecha maxima completar'
                args['retroalimentar']=False
                args['completar'] = True
                args['milestone'] = milestone

            
            return render_to_response('milestone_actual.html',args)


        except Incubada.DoesNotExist:
            return redirect('/')
        except IncubadaConsultor.DoesNotExist:
            return redirect('/')
        except:
            return redirect('/')
    else:
        return redirect('/NotFound')


"""
Autor: Estefania Lozano
Nombre de funcion: ver_retroalimentaciones
Parametros: request
Salida: ver la lista de retroalimentaciones de cada tab de la incubada
Descripcion: Esta funcion es para la peticion Ajax que pide mostrar todas las retroalimentaciones 
    de cada tab
"""

@login_required
def ver_retroalimentaciones(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin'] = request.session['es_admin']
    # si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #si encuentra el ajax del template
    if request.is_ajax():
        try:
            id_incubada = request.GET['incubada']
            milestone = Milestone.objects.get(fk_incubada=id_incubada)
            numRetroal = 0
            if milestone:
                retroalimentaciones = Retroalimentacion.objects.filter(fk_milestone=milestone.id_milestone,
                                                                       num_tab=request.GET['numTab'])
                if retroalimentaciones:
                    numRetroal = retroalimentaciones.count()
            numTabVar = request.GET['numTab']

            args['idMilestone'] = milestone.id_milestone
            args['idIncubada'] = id_incubada
            args['numTabIncubada'] = numTabVar
            args['num_Retroal'] = numRetroal
            args['retroalimentaciones'] = retroalimentaciones
            return render_to_response('retroalimentaciones.html', args)

        except Incubada.DoesNotExist:
            return redirect('/')
        except:
            return redirect('/')
    else:
        return redirect('/NotFound')

"""
Autor: Sixto Castro
Nombre de funcion: guardar_retroalimentaciones
Parametros: request
Salida: Template admin_ver_incubada
Descripcion: Esta funcion guarda todas las retroalimentaciones hechas en cada tab de una incubada
"""


@login_required
def guardar_retroalimentaciones(request):
    sesion = request.session['id_usuario']
    usuario = Perfil.objects.get(id=sesion)
    args = {}
    args['es_admin'] = request.session['es_admin']
    if args['es_admin']:
        if request.method == 'GET':
            num_tab = request.GET['numTab']
            id_incubada = request.GET['idIncubada']
            id_milestone = request.GET['idMilestone']
            contenido = request.GET['contenido']
            try:
                #print id_usuario
                hoy = datetime.datetime.now()
                retroalimentacion = Retroalimentacion()
                retroalimentacion.fecha_creacion = hoy
                milestone = Milestone.objects.get(id_milestone=id_milestone)
                retroalimentacion.fk_milestone = milestone
                consultor = Consultor.objects.get(fk_usuario_consultor_id = usuario.id_perfil)
                retroalimentacion.fk_consultor = consultor
                retroalimentacion.contenido = contenido
                retroalimentacion.num_tab = num_tab
                retroalimentacion.save()
            except:
                print 'Error desconocido'

        return HttpResponseRedirect('AdminIncubada/' + id_incubada)
    else:
        return HttpResponseRedirect('InicioIncubaciones')


"""
Autor: Estefania Lozano
Nombre de funcion: consultor_ver_incubada
Parametros: request
Salida: 
Descripcion: Mostar template de la incubada para el consultor de la incubada
"""


@login_required
def consultor_ver_incubada(request,id_oferta):
    session = request.session['id_usuario']
    usuario = Perfil.objects.get(id=request.session['id_usuario'])
    args = {}
    args['es_admin']=request.session['es_admin']

    if usuario is not None:
        args['usuario'] = usuario
        try:
            incubada = Incubada.objects.filter(fk_oferta=id_oferta).last()
            
            #Tengo que verificar que la incubacion no se encuentra censurada
            id_incubacion=incubada.fk_incubacion.id_incubacion
            incubacion=Incubacion.objects.filter(id_incubacion=id_incubacion).first()
            if incubacion.estado_incubacion!=2 and incubacion.estado_incubacion!=3:
                if incubada:
                    consultores = Consultor.objects.filter(fk_usuario_consultor=usuario.id_perfil)
                    if consultores:
                        consultor = Consultor.objects.filter(fk_usuario_consultor=usuario.id_perfil).first()
                        print 'datos importantes'
                        print consultor
                        print consultor.id_consultor
                        print incubada.id_incubada
                        incubadaCons=IncubadaConsultor.objects.filter(fk_consultor=consultor.id_consultor,fk_oferta_incubada=id_oferta)
                        print incubadaCons
                        print 'me caigo 1'

                        if len(incubadaCons)>0:
                            print 'me caigo 5'
                            args['consultor']=usuario
                            propietario = MiembroEquipo.objects.get(fk_oferta_en_que_participa=incubada.fk_oferta, es_propietario=1)
                            equipo = MiembroEquipo.objects.filter(fk_oferta_en_que_participa=incubada.fk_oferta)
                            if len(equipo)>0:
                                args['equipo'] = equipo
                            fotos= ImagenIncubada.objects.filter(fk_incubada=incubada.id_incubada)
                            if fotos:
                                imagen_principal = fotos.first()
                            else:
                                fotos = False
                                imagen_principal = False

                            #Tenemos que encontrar el primer milestone que tuvo la oferta
                            primer_Incubada = Incubada.objects.filter(fk_oferta=incubada.fk_oferta).first()
                            primer_milestone=Milestone.objects.filter(fk_incubada=primer_Incubada.id_incubada).first()
                            args['milestone']=primer_milestone

                            #Ahora encontramos el milestone actual
                            milestone = Milestone.objects.filter(fk_incubada=incubada.id_incubada).last()
                            if milestone:
                                #lo siguiente es para validar que el consultor pueda retroalimentar
                                #Si es que el milestone ya fue completado pero no ha acabado el tiempo de retroalimentar
                                hoy = datetime.datetime.now(timezone.utc)
                                fecha_maxima_retro = milestone.fecha_maxima_Retroalimentacion
                                fecha_maxima_completar=milestone.fecha_maxima

                                if fecha_maxima_completar < hoy and hoy<=fecha_maxima_retro:
                                    args['retroalimentar'] = True
                                else:
                                    args['retroalimentar'] = False
                                args['milestone_actual']=milestone

                            #Ahora voy a buscar las palabras claves
                            palabras_Claves = incubada.palabras_clave.all()
                            if palabras_Claves.count()==0:
                                palabras_Claves=False
                            args['palabras_clave']=palabras_Claves

                            args['fotos'] = fotos
                            args['imagen_principal'] = imagen_principal
                            args['incubada'] = incubada
                            args['propietario'] = propietario
                            return render_to_response('consultor_ver_incubada.html', args)
                        else:
                            args['error'] = "El usuario no es consultor en esta incubada"
                            return HttpResponseRedirect('/NotFound/')  
                    else:
                        args['error'] = "El usuario no es consultor en esta incubada"
                        return HttpResponseRedirect('/NotFound/')  
                else:
                    args['error'] = "Esta incubada no se encuentra bajo su administración"
                    return HttpResponseRedirect('/NotFound/')
            else:
                args['error'] = "Esta incubada se encuentra en una incubación desactivada o censurada de la red."
                return HttpResponseRedirect('/NotFound/')
        #si la oferta no existe redirige a un mensaje de error
        except Incubada.DoesNotExist:
            args['error'] = "La incubada no se encuentra en la red, lo sentimos."
            return HttpResponseRedirect('/NotFound/')
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect('/NotFound/')

"""
Autor: Estefania Lozano
Nombre de funcion: ver_incubada
Parametros: request
Salida: 
Descripcion: Mostar template de la incubada para el duenio de la incubada
"""

@login_required
def usuario_ver_incubada(request,id_oferta,mostrar):
    session = request.session['id_usuario']
    usuario = Perfil.objects.get(id=request.session['id_usuario'])    
    args = {}
    args['mostrar_actualizado'] = mostrar
    args['es_admin']=request.session['es_admin']

    if usuario is not None:
        args['usuario'] = usuario
        try:
            incubada = Incubada.objects.filter(fk_oferta=id_oferta).last()
            
            id_incubacion=incubada.fk_incubacion.id_incubacion
            incubacion=Incubacion.objects.filter(id_incubacion=id_incubacion).first()
            if incubacion.estado_incubacion!=2 and incubacion.estado_incubacion!=3:
            #Tengo que verificar que el usuario es consultor de la incubada
                if incubada:
                    print incubada.equipo.id_equipo
                    propietario = MiembroEquipo.objects.get(fk_oferta_en_que_participa=incubada.fk_oferta, es_propietario=1)
                    if propietario.fk_participante.id_perfil==usuario.id_perfil:

                        fotos= ImagenIncubada.objects.filter(fk_incubada=incubada.id_incubada)
                        if fotos:
                            imagen_principal = fotos.first()
                        else:
                            fotos = False
                            imagen_principal = False

                        equipo = MiembroEquipo.objects.filter(fk_oferta_en_que_participa=incubada.fk_oferta)
                        if len(equipo)>0:
                            args['equipo'] = equipo

                        #Tenemos que encontrar el primer milestone que tuvo la oferta
                        primer_Incubada = Incubada.objects.filter(fk_oferta=incubada.fk_oferta).first()
                        primer_milestone=Milestone.objects.filter(fk_incubada=primer_Incubada.id_incubada).first()
                        args['milestone']=primer_milestone

                        #Ahora encontramos el milestone actual
                        milestone = Milestone.objects.filter(fk_incubada=incubada.id_incubada).last()
                        if milestone:
                            #lo siguiente es para validar que el consultor pueda retroalimentar
                            #Si es que el milestone ya fue completado pero no ha acabado el tiempo de retroalimentar
                            hoy = datetime.datetime.now(timezone.utc)
                            fecha_maxima_retro = milestone.fecha_maxima_Retroalimentacion
                            fecha_maxima_completar=milestone.fecha_maxima

                            if fecha_maxima_completar < hoy and hoy<=fecha_maxima_retro:
                                args['completar'] = False
                                args['retroalimentar'] = True                            
                            elif fecha_maxima_completar > hoy:
                                args['completar'] = True
                                args['retroalimentar'] = False                            
                            else:
                                args['completar'] = False
                                args['retroalimentar'] = False 


                        #Ahora voy a buscar las palabras claves
                        palabras_Claves = incubada.palabras_clave.all()
                        if palabras_Claves.count()==0:
                            palabras_Claves=False
                        args['palabras_clave']=palabras_Claves

                        args['fotos'] = fotos
                        args['imagen_principal'] = imagen_principal
                        args['incubada'] = incubada
                        args['propietario'] = propietario
                        return render_to_response('usuario_ver_incubada.html', args)

                    else:
                        args['error'] = "El usuario no es consultor en esta incubada"
                        return HttpResponseRedirect('/NotFound/')  
                else:
                    args['error'] = "Esta incubada no se encuentra bajo su administración"
                    return HttpResponseRedirect('/NotFound/')
            else:
                args['error'] = "Esta incubada se encuentra en una incubación desactivada o censurada de la red."
                return HttpResponseRedirect('/NotFound/')
        #si la oferta no existe redirige a un mensaje de error
        except Incubada.DoesNotExist:
            args['error'] = "La incubada no se encuentra en la red, lo sentimos."
            return HttpResponseRedirect('/NotFound/')
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect('/NotFound/')



"""
Autor: Jose Velez
Nombre de funcion: buscar_usuario
Parametros: request
Salida: Muetra el formulario de crear una incubacion
Descripcion: En esta pagina se puede crear incubaciones para las diferentes ofertas
"""

@login_required
def buscar_usuario(request):
    try:
        # se recupera el identificador de la sesión actual
        sesion = request.session['id_usuario']
        #se obtiene el usuario de la sesión actual
        usuario = User.objects.get(id=sesion)
        #Se inicializa la variable que va a contener los parametros del vista
        args = {}

        #Se obtiene los parametros del Metodo 
        if request.method == 'POST':
             #Se obtiene el objeto de la incuabada
            consultor = request.POST['consultor']
            emisor = User.objects.get(id=sesion)
            
            #Seteando los  consultor
            if consultor == emisor:
                args['mensaje_alerta'] = "No te puedes auto-aisgnarte consultor"
            else:
                try:
                    receptor_aux = User.objects.get(username=consultor)
                    receptor = receptor_aux
                    tipo_mensaje = 'usuario-usuario'
                except User.DoesNotExist:
                    print 'No existe usuario'

        else:
            #Se enviara los parametros a la vista
            args['usuario'] = usuario
            args['es_admin'] = request.session['es_admin']
            args.update(csrf(request))
    except:
        return redirect('/')


"""
Autor: Leonel Ramirez
Nombre de funcion: VerMilestone
Parametros: request
Salida: pagian ver milestone
Descripcion: para llamar la pagina ver milestone
"""



@login_required
def admin_ver_milestone(request,id_incubada):
    args = {}
    args['usuario'] = request.user
    args['es_admin'] = request.session['es_admin']
    try:
        incubada=Incubada.objects.get(id_incubada=id_incubada)
        print incubada.fk_oferta
        args['incubada'] = incubada
        listaMilestone = Milestone.objects.all().filter()
        args['listaMilestone'] = listaMilestone
        return render_to_response('admin_ver_milestone.html', args)
    except Incubada.DoesNotExist:
        print '>> incubada no existe'
        return redirect('/NotFound/')
    except Exception as e:
        print e
        print '>> Excepcion no controlada ver milestone'
        return redirect('/NotFound/')


"""
Autor: Jose Velez
Nombre de funcion: Autocompletar_Consultor
Parametros: APIView
Salida: Hace la busqueda por nombre del usuario
Descripcion: En esta funcion se realiza el autocompletado de la busqueda por usuario
"""


class Autocompletar_Consultor(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.query_params.get('term', None)
        usuarios = User.objects.filter(first_name__icontains=user)[:10]
        serializador = UsuarioSerializador(usuarios, many=True)
        response = Response(serializador.data)
        return response



"""
Autor: Sixto Castro
Nombre de funcion: GuardarConvocatoria
Parametros: request
Salida: Se crea convocatoria exitosamente. Caso contrario se muestra el mensaje de error respectivo
Descripcion: Funcion para crear convocatoria a la incubacion respectiva
"""
@login_required
def guardar_convocatoria(request):
    session = request.session['id_usuario']
    usuario = Perfil.objects.get(id=session)
    args = {}
    args['es_admin']=request.session['es_admin']
    #si el usuario EXISTE asigna un arg para usarlo en el template
    if usuario is not None:
        args['usuario'] = usuario
    else:
        args['error'] = "Error al cargar los datos"
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if request.is_ajax():
        fecha_max = request.GET['fecMaxima']
        id_incubacion = request.GET['idIncubacion']
        incubacion = Incubacion.objects.get(id_incubacion=id_incubacion)
        convocatoria = Convocatoria()
        print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        convocatoria.fecha_creacion = datetime.datetime.now()
        print "ttttttttttttttttttttttttttttttttttttttttt"
        convocatoria.fk_incubacion = incubacion
        print "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"
        convocatoria.fecha_maxima = datetime.datetime.strptime(fecha_max, '%m/%d/%Y')
        print "ssssssssssssssssssssssssssssssssssssssssss"
        convocatoria.save()
        print "mmmmmmmmmmmmmmmmmmmmmmmmmmmm"
    else:
        return redirect('/NotFound')

    

"""
Autor: David Vinces
Nombre de funcion: editar_incubada
Parametros: request, id de una incubada
Salida: 
Descripcion: funcion para editar una incubada
"""
@login_required
def editar_incubada(request, id_incubada):
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
        incubada = Incubada.objects.get(id_incubada = id_incubada)
    except:        
        return HttpResponseRedirect('/NotFound/')


    try:
        tiempo_disponible = incubada.tiempo_para_estar_disponible.split(' ',1)
        incubada_tiempo = int(tiempo_disponible[0])

        #si la duracion es de mes
        if tiempo_disponible[1] == 'Mes/es':
            incubada_duracion = 0
        else:
            incubada_duracion = 1

    #si no se encuentra establecida la duracion
    except:
        incubada_duracion = 1
        incubada_tiempo = "Año/s"

    if request.method == 'POST':
        #seccion de informacion
        nombre = request.POST['nombre_oferta']
        tipo = request.POST['select_tipo_oferta']
        descripcion = request.POST['descripcion_oferta']
        dominio = request.POST['oferta_dominio']
        subdominio = request.POST['oferta_sub_dominio']
        
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

        #seccion de copia de datos a la incubada a modificar
        #seccion informacion
        incubada_editada = incubada
        incubada_editada.nombre = nombre
        incubada_editada.tipo = tipo
        incubada_editada.descripcion = descripcion
        incubada_editada.dominio = dominio
        incubada_editada.subdominio = subdominio

        #seccion perfiles
        incubada_editada.perfil_cliente = perfil_cliente
        incubada_editada.perfil_beneficiario = perfil_beneficiario

        #seccion industria
        incubada_editada.cuadro_tendencias_relevantes = tendencias
        incubada_editada.descripcion_soluciones_existentes = soluciones_alternativas

        #seccion de estado/Logros
        #manejo de la duracion de la oferta
        if tiempo_disponible != "" and tiempo_unidad != "":
            if tiempo_unidad == "0":
                tiempo_unidad = "Mes/es"
            else:
                tiempo_unidad = "Año/s"

            incubada_editada.tiempo_para_estar_disponible = str(tiempo_disponible) + " " + tiempo_unidad
        else:
            incubada_editada.tiempo_para_estar_disponible = "1 Año/s"

        incubada_editada.estado_propiedad_intelectual = propiedad_intelectual
        incubada_editada.evidencia_traccion = evidencia_traccion

        #seccion Diagrama canvas
        #se verifica si no existen datos ingresados en los campos. Entonces se dice que no existe el objeto diagrama canvas
        if canvas_socio_clave == "" and canvas_actividades_clave=="" and canvas_recursos=="" and canvas_propuesta=="" and canvas_relaciones=="" and canvas_canales=="" and canvas_segmentos=="" and canvas_estructura=="" and canvas_fuente=="" :
            incubada_editada.fk_diagrama_canvas = None
        #si existen datos ingresados, se los asigna
        else:

            #si anteriormente tuvo canvas, se lo modifica
            try:
                incubada_editada.fk_diagrama_canvas.asociaciones_clave = canvas_socio_clave
                incubada_editada.fk_diagrama_canvas.actividades_clave = canvas_actividades_clave
                incubada_editada.fk_diagrama_canvas.recursos_clave = canvas_recursos
                incubada_editada.fk_diagrama_canvas.propuesta_valor = canvas_propuesta
                incubada_editada.fk_diagrama_canvas.relacion_clientes = canvas_relaciones
                incubada_editada.fk_diagrama_canvas.canales_distribucion = canvas_canales
                incubada_editada.fk_diagrama_canvas.segmento_mercado = canvas_segmentos
                incubada_editada.fk_diagrama_canvas.estructura_costos = canvas_estructura
                incubada_editada.fk_diagrama_canvas.fuente_ingresos = canvas_fuente
                incubada_editada.fk_diagrama_canvas.save()
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
                incubada_editada.fk_diagrama_canvas = diagrama_canvas

        #seccion Diagrama de Porter
        #se verifica si no existen datos ingresados en los campos. Entonces se dice que no existe el objeto diagrama porter
        if porter_competidores == "" and porter_consumidores=="" and porter_sustitutos=="" and porter_proveedores=="" and porter_nuevos=="":
            incubada_editada.fk_diagrama_competidores = None
        #si existen datos ingresados, se los asigna
        else:

            #si anteriormente tuvo porter, cambiarlo
            try:
                incubada_editada.fk_diagrama_competidores.competidores = porter_competidores
                incubada_editada.fk_diagrama_competidores.consumidores = porter_consumidores
                incubada_editada.fk_diagrama_competidores.sustitutos = porter_sustitutos
                incubada_editada.fk_diagrama_competidores.proveedores = porter_proveedores
                incubada_editada.fk_diagrama_competidores.nuevosMiembros = porter_nuevos
                incubada_editada.fk_diagrama_competidores.save()
            #si no tenia, se crea uno nuevo y se lo asigna
            except:
                diagrama_porter = DiagramaPorter()
                diagrama_porter.competidores = porter_competidores
                diagrama_porter.consumidores = porter_consumidores
                diagrama_porter.sustitutos = porter_sustitutos
                diagrama_porter.proveedores = porter_proveedores
                diagrama_porter.nuevosMiembros = porter_nuevos
                diagrama_porter.save()
                incubada_editada.fk_diagrama_competidores = diagrama_porter

        
        incubada_editada.save()
        args.update(csrf(request))
        return redirect('/Incubada/'+str(incubada_editada.fk_oferta.id_oferta)+'/'+str(1))

    else:
        args.update(csrf(request))
        args['incubada_tiempo'] = incubada_tiempo
        args['incubada_duracion'] = incubada_duracion
        args['incubada'] = incubada
        return render_to_response('editar_incubada.html',args)

