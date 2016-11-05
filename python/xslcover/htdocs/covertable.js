
function myFunction(popup) {
  var popuptext = popup.getElementsByClassName("popuptext")[0];
  popuptext.style.visibility = "visible";
  popuptext.style.animation = "fadeIn 1s";

  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function(event) {
    var popups = document.getElementsByClassName("popup");
    for (var i=0; i < popups.length; i++) {
      var p = popups[i];
      var text = p.getElementsByClassName("popuptext")[0];
      if (p != popup || event.target.parentElement != popup){
        text.style.visibility = "hidden";
      }
    }
  }
}

//var toto = document.getElementsByTagName("body");

//document.getElementsByTagName("body")[0].onload =

function fill_popups() {
  var popuptexts = document.getElementsByClassName("popuptext");
  var popups_to_fill =  document.getElementsByClassName("covered")

  var popup_count = Math.min(popups_to_fill.length,popuptexts.length);

  for (var i=0; i < popup_count; i++) {
    var itm = popuptexts[i]
    var cln = itm.cloneNode(true);

    popups_to_fill[i].appendChild(cln)
    popups_to_fill[i].classList.add("popup")
    popups_to_fill[i].onclick = function(e){
      var k = this;
      myFunction(k);
    }
  }
}

