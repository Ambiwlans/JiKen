{% block chart %}
<script>

var ctx = document.getElementById('myChart').getContext('2d');
var myLineChart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [{
            type: 'line',
            label: 'Prediction',
            data: makePrediction(),
            pointRadius: 0
        }, {
            type: 'scatter',
            showLine: false,
            data: {{ rightanswers|safe }}.map(rightPoints),
            pointBackgroundColor: '#267f00'
        }, {
            type: 'scatter',
            showLine: false,
            data: {{ wronganswers|safe }}.map(wrongPoints),
            pointBackgroundColor: '#B40020'
        }]
    },
    options: {
        tooltips: {
            enabled: false
        },
        scales: {
            xAxes: [{
                type: 'linear',
                beginAtZero: true,
                ticks: {
                    max: {{config['GRAPH_MAX_X']}}                
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
        }
    }
});

console.log({{ rightanswers|safe }}.forEach(rightPoints))

function makePrediction() {
    var pred = [];
    
    for (var x = 0; x <= {{config['GRAPH_MAX_X']}}; x = x + 50) {
        //y = 1 / (1 + np.exp(t*(x-a)))
        y = 1 / (1 + 2**({{session['t']}} * (x - {{session['a']}})))
        pred.push({x: x, y: y});
    }
    return pred;
};

function rightPoints(val) {
    return {x: val, y: 1};
};

function wrongPoints(val) {
    return {x: val, y: 0};
};

</script>
{% endblock chart %}