{% block bcchart %}
<script>

//
// Prep data for chart
//
var pred = [];
var right_cnt_binned = [];
var wrong_cnt_binned = [];
var binlabels = [];



function makeHistoData(max_x = 7000, bin_cnt = 100) {
    var binsize = parseInt(Math.ceil((max_x / bin_cnt)/100)*100);
    var cur_bin = -1;
    pred = [];
    right_cnt_binned = [];
    wrong_cnt_binned = [];
    binlabels = [];
    
    // calc for every kanji (could be more cost efficient)
    for (var x = 0; x <= max_x + binsize; x++) {
        y = 1 / (1 + 2**(in_t * (x - in_a)));
        pred.push(y);
        // push new bins as needed
        if (!(x % binsize)){
            if (cur_bin >= 0){
                right_cnt_binned[cur_bin] = parseInt(right_cnt_binned[cur_bin]);
                wrong_cnt_binned[cur_bin] = parseInt(wrong_cnt_binned[cur_bin]);
            }
            cur_bin++;
            binlabels[cur_bin] = x;
            right_cnt_binned.push(0);
            wrong_cnt_binned.push(0);
        }
        right_cnt_binned[cur_bin] += y * counts[x];
        wrong_cnt_binned[cur_bin] += (1 - y) * counts[x];
    }
};

//
// Make the chart! (find obj in dom and put a chart there)
//

function makeChart(){
return new Chart(mainctx, {
    type: 'bar',
    data: {
        labels: binlabels,
        datasets: [{
            type: 'bar',
            label: 'Unknown',
            backgroundColor: '#B40020',
            data: wrong_cnt_binned
        },{
            type: 'bar',
            label: 'Known',
            backgroundColor: '#267f00',
            data: right_cnt_binned
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            xAxes: [{
                stacked: true
            }],
            yAxes: [{
                stacked: true
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

/*
//
// Milestone lines
//
var lastVertXPx = 0;
var vert_lines = [[80,"　 　Gr1"],[240,"　 　Gr2"],[440,"　 　Gr3"],[640,"　 　Gr4"],[825,"　 　Gr5"],[1026,"　 　Gr6"],[2136,"　 　常用"]];

const verticalLinePlugin = {
    renderVerticalLine: function (chartInstance, xVal, text) {
        const yscale = chartInstance.scales['y-axis-0'];
        const xscale = chartInstance.scales['x-axis-0'];
        const context = chartInstance.chart.ctx;
        const lineLeftOffset = xscale.getPixelForValue(xVal);
        var linecolour = '#267f00';
        if (xVal > {/{pred[0]}/}){linecolour = '#B40020'}
        
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
//*/

</script>
{% endblock bcchart %}