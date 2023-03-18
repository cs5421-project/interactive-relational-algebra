var host = "http://127.0.0.1:8000"
url = `${host}/v1/ira/execute_ra_query`; //endpoint of the server

var textArea = document.getElementById("editor");
var form = document.getElementById("query-form");
var resultHeader = document.getElementById("result-header");
var resultInfo = document.getElementById("info-tag");
var resultTable = document.getElementById("result-table");
var sqlQuery = document.getElementById("sql-query");
var resultContainer = document.getElementById("result-container");
form.onsubmit = handleSubmit


function insertSymbol(e) {
   var symbol = e.target.innerHTML.trim();
   textArea.value += symbol;
}

function handleSubmit(event) {
   event.preventDefault();
   var query = textArea.value;

   //post
   fetch(url, {
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
