import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";
import axios from "axios";

const API = "http://localhost:8000/api/v1";

export default function Dashboard() {
  const [topCoins, setTopCoins] = useState([]);
  useEffect(() => {
    axios.get(`${API}/market/top`).then(r => setTopCoins(r.data));
  }, []);
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      {topCoins.map((c: any) => (
        <div key={c.symbol}>{c.symbol}: ${c.price}</div>
      ))}
    </div>
  );
}
