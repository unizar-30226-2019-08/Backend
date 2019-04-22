$("#menu-toggle-Filtro").click(function(e) {
    e.preventDefault();
    //comprueba si debe ocultar el otro aside
    if($("#wrapperFilter").hasClass("toggled") && !$("#wrapper").hasClass('toggled')){
    	 $("#wrapper").toggleClass("toggled");
    }
    //muestra/oculta este aside
    $("#wrapperFilter").toggleClass("toggled");


});

$("#menu-toggle").click(function(e) {
    e.preventDefault();
    if($("#wrapper").hasClass("toggled") && !$("#wrapperFilter").hasClass('toggled')){
    	 $("#wrapperFilter").toggleClass("toggled");
    }
   
    $("#wrapper").toggleClass("toggled");
});