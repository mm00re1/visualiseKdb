import React, { useState, useEffect } from 'react';
import { Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import TradeChart from '../components/tradeChart';

const LivePage = () => {
  const [dropdownOptions, setDropdownOptions] = useState([]);
  const [selectedOptionTbl, setSelectedOptionTbl] = useState('');
  const [selectedPxType, setSelectedPxType] = useState('trade');
  const [tableData, setTableData] = useState([]);
  const [ws, setWs] = useState(null);  // Track the WebSocket connection

  const PxTypeOptions = ['trade', 'bid', 'ask'];

  useEffect(() => {
    // Fetch initial dropdown options
    fetch('http://localhost:8000/pullData_options/trade')
      .then(response => response.json())
      .then(data => setDropdownOptions(data))
      .catch(error => console.error('Error fetching dropdown options:', error));
  }, []);

  // Cleanup the WebSocket on unmount
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  const PxTypeChange = (event) => {
    setSelectedPxType(event.target.value);
    establishWebSocketConnection(selectedOptionTbl, event.target.value);
  };

  const handleDropdownChange = (event) => {
    setSelectedOptionTbl(event.target.value);
    establishWebSocketConnection(event.target.value, selectedPxType);
  };

  const establishWebSocketConnection = (index, pxType) => {
    // Close existing WebSocket if needed
    if (ws) {
      ws.close();
    }
    setTableData([]);

    let tblName = 'trade';
    if (pxType === 'bid' || pxType === 'ask') {
      tblName = 'quote';
    }

    // Create a new WebSocket. The query string includes tbl & index
    const newSocket = new WebSocket(`ws://localhost:8000/live?tbl=${tblName}&index=${index}`);

    newSocket.onopen = () => {
      console.log('WebSocket connected');
    };

    newSocket.onmessage = (e) => {
      const newData = JSON.parse(e.data);
      // If pxType is 'bid' or 'ask', set the displayed "price" from that field
      if (pxType === 'bid') {
        newData['price'] = newData['bid'];
      } else if (pxType === 'ask') {
        newData['price'] = newData['ask'];
      }
      setTableData(prev => [...prev, newData]);
    };

    newSocket.onclose = () => {
      console.log('WebSocket closed');
    };

    newSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(newSocket);
  };

  return (
    <div style={{ marginLeft: '20px', paddingTop: '20px' }}>
      <FormControl fullWidth style={{ width: '250px', paddingBottom: '20px' }}>
        <InputLabel id="index-select-label" style={{ color: '#1E90FF' }}>Select Index</InputLabel>
        <Select
          labelId="index-select-label"
          id="index-select"
          value={selectedOptionTbl}
          label="Select Index"
          onChange={handleDropdownChange}
          style={{ color: '#1E90FF'}}
        >
          {dropdownOptions.map((option, idx) => (
            <MenuItem key={idx} value={option}>{option}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl fullWidth style={{ width: '250px', paddingBottom: '20px' }}>
        <InputLabel id="pxType-select-label" style={{ color: '#1E90FF' }}>Select PxType</InputLabel>
        <Select
          labelId="pxType-select-label"
          id="pxType-select"
          value={selectedPxType}
          label="Select Option"
          onChange={PxTypeChange}
          style={{ color: '#1E90FF'}}
        >
          {PxTypeOptions.map((option, idx) => (
            <MenuItem key={idx} value={option}>{option}</MenuItem>
          ))}
        </Select>
      </FormControl>          

      {TradeChart(tableData)}
    </div>
  );
};

export default LivePage;
