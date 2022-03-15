{% block chart %}
<script>

const verticalLinePlugin = {
    renderVerticalLine: function (chartInstance, xVal, text) {
        const yscale = chartInstance.scales['y-axis-0'];
        const xscale = chartInstance.scales['x-axis-0'];
        const context = chartInstance.chart.ctx;
        const lineLeftOffset = xscale.getPixelForValue(xVal);
        var linecolour = '#267f00';
        if (xVal > {{pred[0]}}){linecolour = '#B40020'}
        
        // Draw another line if last one was over 20px away and not within 20px of the edge
        if (lineLeftOffset > lastVertXPx + 25 && lineLeftOffset < xscale.right - 20){
            // render vertical line
            context.beginPath();
            
            context.strokeStyle = linecolour;
            context.moveTo(lineLeftOffset, yscale.top);
            context.lineTo(lineLeftOffset, yscale.bottom);
            context.stroke();
            
            lastVertXPx = lineLeftOffset;
            
            // write label
            context.fillStyle = linecolour;
            context.textAlign = 'center';
            context.fillText(text, lineLeftOffset, (yscale.bottom - yscale.top) / 2 + yscale.top);        
        }
    },
    
    afterDatasetsDraw: function (chart, easing) {
        if (chart.config.lineAtxVal) {
            chart.config.lineAtxVal.forEach(item => this.renderVerticalLine(chart, item[0], item[1]));
        }
    }
};

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

function update_vert_lines(achievement_type){
    // select the set of vert lines
    switch(achievement_type){
    case 'kyouiku':    // default
        vert_lines = [[80,"　 　Gr1"],[240,"　 　Gr2"],[440,"　 　Gr3"],[640,"　 　Gr4"],[825,"　 　Gr5"],[1026,"　 　Gr6"],[2136,"　 　常用"]];
        break;
    case 'jlpt':    
        vert_lines = [[80,"　 　N5"],[250,"　 　N4"],[620,"　 　N3"],[1000,"　 　N2"],[2136,"　 　N1"]];
        break;
    case 'kanken':   
        vert_lines = [[80,"　 　漢10"],[240,"　 　漢9"],[440,"　 　漢8"],[642,"　 　漢7"],[835,"　 　漢6"],[1026,"　 　漢5"],[1300,"　 　漢4"],[1600,"　 　漢3"],[1951,"　 　Pre-2"],[2136,"　 　漢2"],[2965,"　 　Pre-1"],[6300,"　 　漢1"]];
        break;
    case 'none':    
    default:
        vert_lines = []
        break;        
    }
    lastVertXPx = 0;
    mainChart.destroy();
    mainctx = document.getElementById('predChart').getContext('2d');
    mainChart = makeChart();
};


// find the chart in dom and make it ... or remake it
var prediction =  makePrediction();
var lastVertXPx = 0;
var vert_lines = [[80,"　 　Gr1"],[240,"　 　Gr2"],[440,"　 　Gr3"],[640,"　 　Gr4"],[825,"　 　Gr5"],[1026,"　 　Gr6"],[2136,"　 　常用"]];

var mainctx = document.getElementById('predChart').getContext('2d');
var mainChart = makeChart();

function makeChart(){
return new Chart(mainctx, {
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
    plugins: [verticalLinePlugin],
    lineAtxVal: vert_lines,
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
});};

</script>
{% endblock chart %}