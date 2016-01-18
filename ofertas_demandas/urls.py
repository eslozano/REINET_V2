from ofertas_demandas import routers
from views import *
from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('',
                       url(r'^InicioOferta[/]?$','ofertas_demandas.views.inicio_oferta', name='InicioOferta'),
                       url(r'^verificar_nombre_oferta[/]?$',verificar_nombre_oferta, name="verificar_nombre_oferta"),
                       url(r'^CrearOferta[/]?$','ofertas_demandas.views.crear_oferta', name='CrearOferta'),
                       url(r'^CrearOfertaCopia[/]?$','ofertas_demandas.views.crear_oferta_copia', name='CrearOfertaCopia'),
                       url(r'^CargarImagenOferta[/]?$','ofertas_demandas.views.cargar_imagen_oferta', name='CargarImagenOferta'),

                       url(r'^oferta/(?P<id_oferta>\w{0,250})[/]?$','ofertas_demandas.views.ver_cualquier_oferta', name='verOferta'),
                       url(r'^administrarOferta/(?P<id_oferta>\w{0,250})[/]?$','ofertas_demandas.views.administrar_Oferta', name='AdministrarOferta'),
                       url(r'^AdministrarBorradorOferta/(?P<id_oferta>\w{0,250})[/]?$','ofertas_demandas.views.administrar_Borrador', name='AdministrarBorradorOferta'),
                       url(r'^EditarBorradorOferta/(?P<id_oferta>\w{0,250})[/]?$','ofertas_demandas.views.editar_borrador', name='EditarBorradorOferta'),

                       url(r'^equipoOferta[/]?$', 'ofertas_demandas.views.equipo_oferta', name='equipoOferta'),
                       url(r'^equipoEditableOferta[/]?$', 'ofertas_demandas.views.equipo_editable_oferta', name='equipoOferta'),
                       url(r'^listaComentariosAceptados[/]?$', 'ofertas_demandas.views.lista_comentarios_aceptados', name='lista_comentarios_aceptados'),
                       #url(r'^editarEquipoOferta[/]?$', 'ofertas_demandas.views.editarEquipoOferta', name='editarEquipoOferta'),
                       url(r'^agregarParticipante[/]?$', 'ofertas_demandas.views.agregar_participante', name='agregarParticipante'),
                       url(r'^AutocompletarParticipante[/]?$', Autocompletar_Participante.as_view() , name='AutocompletarParticipante'),

                       url(r'^solicitarMembresiaOferta[/]?$', 'ofertas_demandas.views.solicitar_membresia_oferta', name='solicitarMembresiaOferta'),
                       url(r'^publicarBorrador/(?P<id_oferta>\w{0,250})[/]?$','ofertas_demandas.views.publicar_borrador', name='publicarBorrador'),
                       url(r'^eliminarBorrador/(?P<id_oferta>\w{0,250})[/]?$','ofertas_demandas.views.eliminar_borrador', name='eliminarBorrador'),
                       url(r'^aceptarPeticionMiembro[/]?$','ofertas_demandas.views.aceptar_peticion', name='aceptar_peticion'),
                       url(r'^rechazarPeticionMiembro[/]?$','ofertas_demandas.views.rechazar_peticion', name='rechazar_peticion'),

                       url(r'^editarEstadoMembresia[/]?$','ofertas_demandas.views.editar_estado_membresia', name='editarEstadoMembresia'),
                      url(r'^calificacionResolverDemanda[/]?$','ofertas_demandas.views.calificacion_resolver_demanda', name='calificacion_resolver_demanda'),
                    
                       url(r'^editarRolMembresia[/]?$','ofertas_demandas.views.editar_rol_membresia', name='editarRolMembresia'),
                       url(r'^aceptarPeticionMiembro[/]?$','ofertas_demandas.views.aceptar_peticion', name='aceptar_peticion'),
                       url(r'^editarEstadoMembresia[/]?$','ofertas_demandas.views.editar_estado_membresia', name='editarEstadoMembresia'),
                       url(r'^editarRolMembresia[/]?$','ofertas_demandas.views.editar_rol_membresia', name='editarRolMembresia'),
                       url(r'^editarEstadoDemanda[/]?$','ofertas_demandas.views.editar_estado_demanda', name='editarEstadoDemanda'),

                       url(r'^enviarComentario[/]?$', 'ofertas_demandas.views.enviar_comentario', name='enviar_comentario'),
                       url(r'^aceptarComentario/(?P<id_comentario>\w{0,250})[/]?$','ofertas_demandas.views.aceptar_comentario', name='aceptar_comentario'),
                       url(r'^rechazarComentario/(?P<id_comentario>\w{0,250})[/]?$','ofertas_demandas.views.rechazar_comentario', name='rechazar_comentario'),

                       url(r'^InicioDemanda[/]?$','ofertas_demandas.views.inicio_demanda', name='InicioDemanda'),
                       url(r'^CrearDemanda[/]?$','ofertas_demandas.views.crear_demanda', name='CrearDemanda'),
                       url(r'^CrearDemandaCopia[/]?$','ofertas_demandas.views.crear_demanda_copia', name='CrearDemandaCopia'),
                       url(r'^CargarImagenDemanda[/]?$','ofertas_demandas.views.cargar_imagen_demanda', name='CargarImagenDemanda'),
                       url(r'^EliminarBorradorDemanda/(?P<id_demanda>\w{0,250})[/]?$','ofertas_demandas.views.eliminar_borrador_demanda', name='EliminarBorradorDemanda'),

                       url(r'^demanda/(?P<id_demanda>\w{0,250})[/]?$','ofertas_demandas.views.ver_cualquier_demanda', name='verDemanda'),
                       url(r'^administrarDemanda/(?P<id_demanda>\w{0,250})[/]?$','ofertas_demandas.views.administrar_demanda', name='AdministrarDemanda'),
                       url(r'^lista_comentarios_aceptados_demandas[/]?$', 'ofertas_demandas.views.lista_comentarios_aceptados_demandas', name='lista_comentarios_aceptados_demandas'),
                       url(r'^enviar_comentario_demanda[/]?$', 'ofertas_demandas.views.enviar_comentario_demanda', name='enviar_comentario_demanda'),
                       url(r'^aceptar_comentario_demanda/(?P<id_comentario>\w{0,250})[/]?$','ofertas_demandas.views.aceptar_comentario_demanda', name='aceptar_comentario_demanda'),
                       url(r'^rechazar_comentario_demanda/(?P<id_comentario>\w{0,250})[/]?$','ofertas_demandas.views.rechazar_comentario_demanda', name='rechazar_comentario_demanda'),
                       url(r'^AdministrarBorradorDemanda/(?P<id_demanda>\w{0,250})[/]?$','ofertas_demandas.views.administrar_Borrador_Demanda', name='AdministrarBorradorDemanda'),
                       url(r'^EditarBorradorDemanda/(?P<id_demanda>\w{0,250})[/]?$','ofertas_demandas.views.editar_borrador_demanda', name='EditarBorradorDemanda'),
                       url(r'^PublicarBorradorDemanda/(?P<id_demanda>\w{0,250})[/]?$','ofertas_demandas.views.publicar_borrador_demanda', name='PublicarBorradorDemanda'),
                       url(r'^resolverDemanda[/]?$', 'ofertas_demandas.views.resolver_demanda', name='resolverDemanda'),
                       url(r'^ofertaResuelveDemanda[/]?$', 'ofertas_demandas.views.oferta_resuelve_demanda', name='ofertaResuelveDemanda'),
                       )

urlpatterns += routers.ofertas_routers
