$(function(){
  $("#tabs").tabs();
  $("input:submit").click(function(){
    $.post("/ajax_post", { text: $("#id_0").val() }, function(data){
       $("#messages").append("<P>" + $("#message", $(data)).text())
    })
  return false
  })
})