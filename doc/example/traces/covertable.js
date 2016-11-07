/*
 * A popup is as follow:
 *
 * <span class="popup">
 *   ... data to click on to show the popup ...
 *   <span class="popuptext">Content of the popup</span>
 * </span>
 *
 * The function just makes the popup visible, and hide the other popups
 *
 */
function show_popup(popup) {
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

/*
 * The HTML stores a list of 'popuptext' class elements outside
 * the table data. The principle is to clone all of the 'popuptext's and insert
 * them into the 'covered' lines one by one, and add to the lines the 'popup'
 * class, so that clicking on the line will show up the popup content.
 *
 * Once done, the document has elements like this:
 *
 * <span class="covered popup"> ... <span class="popuptext">...</span></span>
 *
 */
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
      show_popup(k);
    }
  }
}

