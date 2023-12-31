import React, { useState, useEffect } from 'react';
import { Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import TradeChart from '../components/tradeChart';

const LivePage = () => {
  const [dropdownOptions, setDropdownOptions] = useState([]);
  const [selectedOptionTbl, setSelectedOptionTbl] = useState('');
  const [selectedPxType, setSelectedPxType] = useState('trade');
  const [tableData, setTableData] = useState([]);
  const [eventSource, setEventSource] = useState(null); // New state for SSE connection

  const PxTypeOptions = ['trade', 'bid', 'ask'];
  useEffect(() => {
    // Fetch dropdown options from Flask API
    fetch('http://localhost:8000/pullData_options/trade')
      .then(response => response.json())
      .then(data => {
          setDropdownOptions(data);
      })
      .catch(error => console.error('Error fetching dropdown options:', error));
  }, []);

  useEffect(() => {
    // Cleanup event source when component unmounts
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  const PxTypeChange = (event) => {
      setSelectedPxType(event.target.value);
      establishSSEConnection(selectedOptionTbl, event.target.value);
  };
  
  const handleDropdownChange = (event) => {
    setSelectedOptionTbl(event.target.value);
    establishSSEConnection(event.target.value, selectedPxType);
  };

  const establishSSEConnection = (index, pxType) => {
    // Close existing SSE connection if it exists
    if (eventSource) {
      eventSource.close();
    }
    setTableData([]);
    let tblName = 'trade';
    if (pxType === 'bid' || pxType === 'ask') {
      tblName = 'quote';
    }
    const newEventSource = new EventSource(`http://localhost:8000/live?tbl=${tblName}&index=${index}`);
    setEventSource(newEventSource);

    newEventSource.onmessage = (e) => {
      // Update chart data with each new message
      const newData = JSON.parse(e.data);
      if (pxType === 'bid') {
        newData['price'] = newData['bid'];
      }
      if (pxType === 'ask') {
        newData['price'] = newData['ask'];
      }
      setTableData(previousData => [...previousData, newData]);
    };

    newEventSource.onerror = (e) => {
      // Handle errors here
      console.error('EventSource failed:', e);
    };
  };

    return (
        <div style={{ marginLeft: '20px', paddingTop: '20px' }}>
          <FormControl fullWidth style={{ width: '250px', paddingBottom: '20px' }}>
            <InputLabel id="demo-simple-select-label" style={{ color: '#1E90FF' }}>Select Index</InputLabel>
            <Select
              labelId="demo-simple-select-label"
              id="demo-simple-select"
              value={selectedOptionTbl}
              label="Select Index"
              onChange={handleDropdownChange}
              style={{ color: '#1E90FF'}}
            >
              {dropdownOptions.map((option, index) => (
                <MenuItem key={index} value={option}>{option}</MenuItem>
                ))}
            </Select>
          </FormControl>
          <FormControl fullWidth style={{ width: '250px', paddingBottom: '20px' }}>
            <InputLabel id="demo-simple-select-label" style={{ color: '#1E90FF' }}>Select PxType</InputLabel>
            <Select
              labelId="demo-simple-select-label"
              id="demo-simple-select"
              value={selectedPxType}
              label="Select Option"
              onChange={PxTypeChange}
              style={{ color: '#1E90FF'}}
            >
              {PxTypeOptions.map((option, index) => (
                <MenuItem key={index} value={option}>{option}</MenuItem>
                ))}
            </Select>
          </FormControl>          
          {TradeChart(tableData)}
        </div>
      );
    };

export default LivePage;

