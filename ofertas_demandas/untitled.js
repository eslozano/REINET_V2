
appoferta.directive('uniqueNombre', function($http){
    var toId;
    return {
        require: 'ngModel',
        ink: function(scope, elem, attr, ctrl) {
            //when the scope changes, revisar las siglas.
            scope.$watch(attr.ngModel, function(value) {
                // if there was a previous attempt, stop it.
                if(toId) clearTimeout(toId);
                if(value!= undefined){
                    console.log("Estamos adentro del directive para Nombre Oferta");
                    toId = setTimeout(function(){
                        $http(
                        {
                            method: 'POST',
                            url: '/verificar_nombre_oferta',
                            data: 'nombre_oferta='+value,
                            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                        })
                        .success(function(data, status, headers, config) {
                            if (data == "usado") {
                                ctrl.$setValidity('uniqueNombre', false);
                                $("#nombre_oferta_usado").html("Nombre de Oferta no disponible");
                                $("#nombre_oferta_usado").attr("style", "display: block; color: red; text-align:center");
                                $("#nombre_oferta_usado").attr("class", "info-board-red");
                            }
                            else if (data == "ok"){
                                ctrl.$setValidity('uniqueNombre', true);
                                $("#nombre_oferta_usado").html("Nombre de Oferta disponible");
                                $("#nombre_oferta_usado").attr("style", "display: block; color: green; text-align:center");
                                $("#nombre_oferta_usado").attr("class", "info-board-green");
                            }
                            else {
                                ctrl.$setValidity('uniqueNombre', false);
                                $("#nombre_oferta_usado").html("Ingrese nombre Oferta");
                                $("#nombre_oferta_usado").attr("style", "display: block; color: blue; text-align:center");
                                $("#nombre_oferta_usado").attr("class", "info-board-blue");
                            }
                        })
                        .error(function(data, status, headers, config) {
                            console.log("error")
                        });
                    }, 200);
                }
            })
        }
            
});