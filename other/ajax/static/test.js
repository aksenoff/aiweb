$(function(){
  $("p").each(function(){
    $(this).attr("style", "color:" + $(this).text())
  })
  $("li").click(function(){
    $("p:first").prepend($(this).text())
    $("p:last").append($(this).text())
  }).hover(function(){
    var current_li = this
    $("p").each(function(){
      $(this).attr("prevstyle", $(this).attr("style"))
             .attr("style", $(this).attr("style")+";background-color:"+$(current_li).text())
    })
  }, function(){
    $("p").each(function(){
      $(this).attr("style", $(this).attr("prevstyle"))
    })
  } 
  ) 
})