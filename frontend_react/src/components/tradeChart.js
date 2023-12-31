import React from 'react';
import ApexCharts from 'react-apexcharts';

const TradeChart = (data) => {
  if (data === undefined) {
        return <div></div>;
  }

  const series = [{
    name: 'Price',
    data: data.map(item => ({
      x: item.time,
      y: item.price
    }))
  }];

  // Define chart options
  const options = {
    chart: {
      type: 'line',
      height: 350
    },
    xaxis: {
      type: 'datetime', // Change to 'datetime' to handle date-time values
      tickAmount: 10, // de-clutter the x axis
      labels: {
        formatter: function(value) {
          return new Date(value).toLocaleTimeString(); // Formats the x-axis labels as time strings
        }
      }
    },
    yaxis: {
        labels: {
          formatter: function(value) {
            return value.toFixed(2); // Round to 2 decimal places
          }
        },
    },

    tooltip: {
      x: {
        format: 'HH:mm:ss'
      }
    },
    stroke: {
      curve: 'straight'
    },
  };

  return (
    <div style={{marginLeft: '5%', marginRight: '20%'}}>
      <ApexCharts options={options} series={series} type="line" height={350} />
    </div>
  );
};

export default TradeChart;
