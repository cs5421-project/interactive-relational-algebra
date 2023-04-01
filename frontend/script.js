var host = "http://127.0.0.1:8000"
submitURL = `${host}/v1/ira/execute_ra_query`; //endpoint of execute ra query
uploadURL = `${host}/v1/ira/load_xml`; //endpoint of upload
downloadURL = `${host}/v1/ira/download_xml`; //endpoint of download

var textArea = document.getElementById("editor");
var form = document.getElementById("query-form");
var resultHeader = document.getElementById("result-header");
var resultInfo = document.getElementById("info-tag");
var resultTable = document.getElementById("result-table");
var sqlQuery = document.getElementById("sql-query");
var resultContainer = document.getElementById("result-container");
const uploadIcon = document.getElementById("upload-icon");
const downloadIcon = document.getElementById("download-icon");
const fileInput = document.getElementById("file-upload");


form.onsubmit = handleSubmit


function insertSymbol(e) {
   var symbol = e.target.innerHTML.trim();
   textArea.value += symbol;
}

function handleSubmit(event) {
   event.preventDefault();
   var query = textArea.value;

   //post
   fetch(submitURL, {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ "raQuery": query })
   })
      .then(response => response.json())
      .then(data => {
         updateResultContainer(data);
      })
      .catch((error) => {
         displayError(error)
      });
}

function updateResultContainer(msg) {

   if (msg.hasOwnProperty('result') && Object.keys(msg.result).length != 0) {
      resultHeader.style.color = "green";
      resultHeader.innerText = "Query Result (Success)";
      displaySQLQuery(msg.sqlQuery);
      buildTable(msg.result);
   }

   else if (msg.hasOwnProperty('message')) {
      resultHeader.style.color = "red";
      displaySQLQuery(msg.sqlQuery);
      resultInfo.innerText = msg.message;
      resultHeader.innerText = "Query Result (SQL ERROR)"
      resultTable.innerHTML = ""
   }

}

function displayError(error) {
   resultHeader.style.color = "red";
   sqlQuery.innerHTML = "";
   resultInfo.innerText = error;
   resultTable.innerHTML = "";
   resultHeader.innerText = "Query Result (POST SYNTAX ERROR)"
}

function buildTable(data) {
   if (data.length == 0) {
      return;
   }

   var columNames = Object.keys(data[0]);
   var cols = columNames.length;
   var rows = data.length;

   var html = "<th>S.No</th>"

   //build table header
   for (let i = 0; i < cols; i++) {
      html += `<th>${columNames[i]}</th>`
   }
   html = `<tr>${html}</tr>`

   //build table rows
   for (let r = 0; r < rows; r++) {
      var rowHTML = `<td>${r + 1}</td>`
      for (let c = 0; c < cols; c++) {
         rowHTML += `<td>${data[r][columNames[c]]}</td>`
      }
      html += `<tr>${rowHTML}</tr>`
   }

   resultInfo.innerText = ""
   resultTable.innerText;
   resultTable.innerHTML = html
}

function displaySQLQuery(data) {
   sqlQuery.innerText = `SQL QUERY: ${data}`
}

uploadIcon.addEventListener("click", () => {
   fileInput.click();
});

downloadIcon.addEventListener("click", () => {
   //write code to call the api end point for RAQ -> XML
   var contents = textArea.value.trim()
   if (!contents.length) {
      alert("no raq provided in the editor")
      return
   }

   fetch(downloadURL, {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ "raQuery": contents })
   })
      .then(response => response.blob())
      .then(data => {
         var a = document.createElement("a");
         a.href = window.URL.createObjectURL(data);
         a.download = "response.xml";
         a.click();
         URL.revokeObjectURL(a.href);
      })
      .catch((error) => {
         console.log("error", error)
      });
});

//read input file
fileInput.addEventListener("change", (event) => {
   const file = event.target.files[0];

   const reader = new FileReader();
   reader.onload = (e) => {
      const contents = e.target.result;
      //write code to call the api end point for XML -> RAQ
      fetch(uploadURL, {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify({ "content": contents })
      })
         .then(response => response.json())
         .then(data => {
            if ('raq' in data) {
               textArea.value = "";
               textArea.value = data.raq
            }
         })
         .catch((error) => {
            console.log("error", error)
         });
   };
   reader.readAsText(file);
   fileInput.value = "";
});


// data = [
//    {
//        "sepal.length": 5.1
//    },
//    {
//        "sepal.length": 4.9
//    },
//    {
//        "sepal.length": 4.7
//    },
//    {
//        "sepal.length": 4.6
//    },
//    {
//        "sepal.length": 5.0
//    },
// ]
// buildTable(data)
