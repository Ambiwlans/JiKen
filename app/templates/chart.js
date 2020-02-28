{% block chart %}
<script>

var prediction =  makePrediction();
var ctx = document.getElementById('predChart').getContext('2d');
var myLineChart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [{
            type: 'scatter',
            showLine: false,
            data: {{ rightanswers|tojson|safe }}.map(rightPoints),
            pointBackgroundColor: '#267f00'
        }, {
            type: 'scatter',
            showLine: false,
            data: {{ wronganswers|tojson|safe }}.map(wrongPoints),
            pointBackgroundColor: '#B40020'
        }, {
            type: 'line',
            label: 'Prediction',
            backgroundColor: '#267f0020',
            fill: 'origin',
            data: prediction,
            pointRadius: 0
        }, {
            type: 'line',
            label: 'Prediction',
            backgroundColor: '#B4002020',
            fill: 'end',
            data: prediction,
            pointRadius: 0
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        tooltips: {
            enabled: true,
            mode: 'single',
            bodyFontSize: 18,
            callbacks: {
                custom: function(tooltip) {
    		        if (!tooltip) return;
    		        // disable displaying the color box;
    		        tooltip.displayColors = false;
		        },
                label: function(tooltipItems, data) { 
                    return (data.datasets[tooltipItems.datasetIndex].data[tooltipItems.index].kanji);
                },
                title: function(tooltipItem, data) {
		          return;
		        }
            }
        },
        scales: {
            xAxes: [{
                type: 'linear',
                beginAtZero: true,
                ticks: {
                    max: {{xmax}}
                }
            }],
            yAxes: [{
                ticks: {
                    beginAtZero: true,
                    callback: function(value, index, values) {
                        if (value == 0 || value == .5 || value == 1){
                            return (value * 100) + '%';
                        }
                        return '';
                    }
                }
            }]
        },
        legend: {
            display: false
        },
        layout: {
            padding: {
                top: 30
            }
        },
        animation: {
            duration: 0
        }
    }
});

//console.log({{ rightanswers|safe }}.forEach(rightPoints))

function makePrediction() {
    var pred = []; 
    for (var x = 0; x <= {{config['MAX_X']}} + 50; x = x + 50) {
        y = 1 / (1 + 2**({{t}} * (x - {{a}})))
        pred.push({x: x, y: y});
    }
    return pred;
};

function rightPoints(val) {
    return {x: val[0], y: 1, kanji: val[1]};
};

function wrongPoints(val) {
    return {x: val[0], y: 0, kanji: val[1]};
};

</script>
{% endblock chart %}