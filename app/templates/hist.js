{% block chart %}
<script>

var histoctx = document.getElementById('histoChart').getContext('2d');
var myHisto = new Chart(histoctx, {
    type: 'bar',
    data: {
        labels: {{ hist|tojson|safe }}.map(histlabels),
        datasets: [{
            data: {{ hist|tojson|safe }}.map(histdata),
            backgroundColor: {{ hist|tojson|safe }}.map(histcolours)
        }]
        
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                grid: {
                    offset: true
                }
            },
        },
        legend: {
            display: false
        },
        animation: {
            duration: 0
        }
    }
});

function histdata(val, i, ele) {
    {% if curtest %}
        if (ele[i][0] > {{pred[0]}}){return val[1];}
        if (ele[i+1][0] < {{pred[0]}}){return val[1]}
        return val[1] + 1;
    {% endif %}
    return val[1];
};

function histlabels(val) {
    //console.log(JSON.stringify((parseInt({{scaler}} * val[0])));
    return parseInt(val[0]);
};

function histcolours(val, i, ele) {
    if (ele[i][0] > {{pred[0]}}){return "grey";}
    if (ele[i+1][0] < {{pred[0]}}){return "grey"}
    return "green"
};

</script>
{% endblock chart %}