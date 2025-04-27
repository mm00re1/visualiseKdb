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
        setTableData(data.rows);
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
          <TradeChart data={tableData} />
        </div>
      );
    };
  
  export default SnapshotPage;
