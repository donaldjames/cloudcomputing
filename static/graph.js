var trace1 = {
  type: "scatter",
  mode: "lines",
  name: 'Price',
  x: dates,
  y: price,
  line: {color: '#ff0000'}
}

var trace2 = {
  type: "scatter",
  mode: "lines",
  name: 'Moving Average',
  x: dates,
  y: movingavg,
  line: {color: '#0e8e1b'}
}

var data = [trace1,trace2];

var layout = {
  title: company_name,
  plot_bgcolor: "black",
  paper_bgcolor: "#fff3",
  height: 600,
  xaxis: {
    autorange: true,
    rangeselector: {buttons: [
        {
          count: 1,
          label: '1m',
          step: 'month',
          stepmode: 'backward'
        },
        {
          count: 6,
          label: '6m',
          step: 'month',
          stepmode: 'backward'
        },
        {step: 'all'}
      ]},
    type: 'dates'
  },
  yaxis: {
    autorange: true,
    range: [86.8700008333, 138.870004167],
    type: 'linear'
  }
};

Plotly.newPlot('graphDiv', data, layout);

graphDiv.on('plotly_afterplot', function() {
  start_date = layout.xaxis.range[0].substring(0,9);
  end_date = layout.xaxis.range[1].substring(0,9);
  table_content = document.getElementById("mov_avg_data_list");
  tr = table_content.getElementsByTagName("tr");
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[0];
    if(td) {
      txtValue = td.textContent || td.innerText;
      if(txtValue<start_date || txtValue>end_date) {
        tr[i].style.display = "none";
      } else {
        tr[i].style.display = "";
      }
    }
  };
});