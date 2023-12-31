import React, { useState, useEffect } from 'react';
import { Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import TradeChart from '../components/tradeChart';

const SnapshotPage = () => {
  const [dropdownOptions, setDropdownOptions] = useState([]);
  const [selectedOption, setSelectedOption] = useState('');
  const [tableData, setTableData] = useState([]);

  useEffect(() => {
    // Fetch dropdown options from Flask API
    fetch('http://localhost:8000/pullData_options/trade')
      .then(response => response.json())
      .then(data => {
          setDropdownOptions(data);
      })
      .catch(error => console.error('Error fetching dropdown options:', error));
  }, []);

  const handleDropdownChange = (event) => {
    setSelectedOption(event.target.value);
    // Fetch table data based on selected option
    fetch(`http://localhost:8000/pullData/trade/${event.target.value}`)
      .then(response => response.json())
      .then(data => {
          const columns = Object.keys(data);
          // construct a list of dictionaries from the data
          const transformedData = [];
          for (let i = 0; i < data[columns[0]].length; i++) {
              const row = {};
              // time comes in format ms e.g. '61584022', convert to datetime
              row['time'] = new Date(data['time'][i]);
              row['price'] = data['price'][i];
              transformedData.push(row);
          }
          setTableData(transformedData);
      })
      .catch(error => console.error('Error fetching table data:', error));
  };
  
    return (
        <div style={{
            marginLeft: '20px',
            paddingTop: '20px'
            }}>
          <FormControl fullWidth style={{ width: '250px', paddingBottom: '20px' }}>
            <InputLabel id="demo-simple-select-label" style={{ color: '#1E90FF' }}>Select Index</InputLabel>
            <Select
              labelId="demo-simple-select-label"
              id="demo-simple-select"
              value={selectedOption}
              label="Select Index"
              onChange={handleDropdownChange}
              style={{ color: '#1E90FF'}}
            >
              {dropdownOptions.map((option, index) => (
                <MenuItem key={index} value={option}>{option}</MenuItem>
                ))}
            </Select>
          </FormControl>          
          {TradeChart(tableData)}
        </div>
      );
    };
  
  export default SnapshotPage;
