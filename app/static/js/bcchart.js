//
// Prep data for chart
//
var pred = [];
var right_cnt_binned = [];
var wrong_cnt_binned = [];
var binlabels = [];



function makeHistoData(max_x = 7000, bin_cnt = 100) {
    var binsize = Math.floor(Math.ceil((max_x / bin_cnt)/100)*100);
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
                right_cnt_binned[cur_bin] = Math.round(right_cnt_binned[cur_bin]);
                wrong_cnt_binned[cur_bin] = Math.round(wrong_cnt_binned[cur_bin]);
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
            xAxes: [{}],
            yAxes: [{
                type: 'logarithmic',
                ticks: {
                     min: 0,
                     max: 100000,
                     callback: function (value, index, values) {
                         if (value === 100000) return "100K";
                         if (value === 10000) return "10K";
                         if (value === 1000) return "1K";
                         if (value === 100) return "100";
                         if (value === 10) return "10";
                         if (value === 1) return "1";
                         if (value === 0) return "0";
                         return null;
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
