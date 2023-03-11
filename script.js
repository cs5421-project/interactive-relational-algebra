function insertSymbol(e) {
   var symbol =  e.target.innerHTML.trim();
   var textArea = document.getElementById("editor");
   textArea.value += symbol;
}