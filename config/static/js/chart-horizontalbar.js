// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#292b2c';

// Bar Chart Example
var ctx = document.getElementById("myHorizontalChart");
var myHorizontalChart = new Chart(document.getElementById("myHorizontalChart"), {
    "type": "horizontalBar",
    "data": {
      "labels": labels,
      "datasets": [{
        "label": "Etudiant",
        "data": data,
        "fill": false,
        "backgroundColor": (["rgba(255, 99, 132, 0.6)", "rgba(255, 159, 64, 0.6)",
                  "rgba(255, 205, 86, 0.6)", "rgba(75, 192, 192, 0.6)", "rgba(154, 80, 235, 0.6)"
                ].join('@')+'@').repeat(data.length).split('@').splice(0,data.length*5), 
        "borderColor": (["rgba(255, 99, 132, 0.6)", "rgba(255, 159, 64, 0.6)",
                  "rgba(255, 205, 86, 0.6)", "rgba(75, 192, 192, 0.6)", "rgba(154, 80, 235, 0.6)"
                ].join('@')+'@').repeat(data.length).split('@').splice(0,data.length*5), 
        "borderWidth": 1
      }]
    },
    "options": {
      "scales": {
        "xAxes": [{
          "ticks": {
            "beginAtZero": true
          }
        }]
      }
    }
  });
