$(function(){
  $("input:submit").click(function(){
  $.post("/ajax_post", {text:"fghfghfh"}, function(result){
    $("#messages").append($("#message", result).html());
  })
  return false
  })
})