function anyadirFavorito(id){
    alert("cipote");
   
  if($('#'+id).find('span').hasClass('favorito')){
    //Enviar favorito  
  } else{
      //Eliminar de favorito
  }
    $('#'+id).find('span').toggleClass('favorito');
    
}