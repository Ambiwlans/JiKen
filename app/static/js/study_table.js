// setup the datatable

function make_table(data=0, type=0, id=0, date=0, lowerbound=0){
    if (screen.width < 500) {hiddencols=[2,3,4,5,7];}
    else {hiddencols=[3,4,5];}
    
    table = $('#study_table').DataTable( {
        dom: 'Brtp',
        "paging":   true,
        "lengthChange": false,
        "pageLength": 10,
        "ordering": true,
        "buttons": true,
        "info":     false,
        "searching": true,
        "order": [[0, "asc" ]],
        columnDefs: [{
            targets: 0,
            render: $.fn.dataTable.render.number(',', '.', 0, '#')
        },
        {
            targets: 3,
            render: function ( data, type, row, meta ) {
              if(data == 14){return '';}
              return data;
            }
        },
        {
            targets: 4,
            render: function ( data, type, row, meta ) {
              if(data == 6){return '';}
              return data;
            }
        },                {
            targets: 2,
            width: "15em"
        },
        {
            targets: hiddencols,
            visible: false
        }],
        buttons: [{
            text: 'Study List Only', 
            action: function(){
                if (this.text() == 'Study List Only'){
                    this.text('All Missed');
                    max_filter = lowerbound;
                    table.draw();
                    }
                else {
                    this.text('Study List Only');
                    max_filter = 100000;
                    table.draw();
                    }
                }
        },
        {
            extend: 'columnsToggle',
            columns: [2,3,4,5,7]
        }]
    } );
    
    // Export button group
    new $.fn.dataTable.Buttons( table, {
        buttons: [
            {
                extend: 'copy',
                text: 'Click to Copy'
            },
            {
                text: 'Anki',
                action: function(){window.location = '/anki_file/'+ id + '/'+ max_filter ;}
            },
            {
                extend: 'csv',
                text: 'CSV',
                charset: 'utf-8'
            },
            {
                text: 'PDF',
                extend: 'pdf',
                charset: 'utf-8',
                title: 'JiKen Study List - ' + id,
                messageTop: 'Test #' + id + '. Saved from Jiken on ' + date + 'GMT.',
                exportOptions: {
                    modifier: {
                        columns: 'visible'
                    }
                },
                customize: function ( doc ) {
                  processDoc(doc);
                }
            }
        ]
    } );
    table.buttons( 1, null ).container().appendTo(
        table.table().container()
    );
}

// Filter
var max_filter = 100000;
$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex ) {
    console.log(data[0]);
        if ( data[0] <= max_filter){return true;}
        return false;
    }
);
        
// PDF Proccessing
function processDoc(doc) {
    alert("Generating PDF may take a few seconds. Please wait.");
    $.getScript("/static/js/vfs_fonts.js");
    
    pdfMake.fonts = {
        Roboto: {
            normal: 'Roboto-Regular.ttf',
            bold: 'Roboto-Medium.ttf',
            italics: 'Roboto-Italic.ttf',
            bolditalics: 'Roboto-MediumItalic.ttf'
        },
        meiryo: {
            normal: 'Meiryo.ttf',
            bold: 'Meiryo.ttf',
            italics: 'Meiryo.ttf',
            bolditalics: 'Meiryo.ttf'
        }
    };
    // modify the PDF to use a custom font:
    doc.defaultStyle.font = "meiryo";
    var i = 1;
}